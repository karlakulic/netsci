# ---------------------------------------------------------------------------
# Pre-flight spec — must match docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H11"
HYPOTHESIS_STATEMENT = "Public institutions in the same procurement domain share vendor portfolios at above-chance rates"
GRAPH_FORM           = "bipartite multigraph (IsUponFA=false; analysis window only)"
NULL_MODEL           = "Bipartite configuration model — degree-preserving rewiring; group labels held fixed; within-group mean pairwise CA Jaccard compared to null ensemble"
DATA_CONSTRAINT      = "Restrict to CAs with degree ≥ 2; group minimum ≥ 5 CAs per modal CPV group"
# ---------------------------------------------------------------------------

import sys
import textwrap
import random
import numpy as np
import pandas as pd
from itertools import combinations

DATA_PATH        = "data/contracts_clean.csv"
NULL_ITERATIONS  = 500
ALPHA            = 0.05
EFFECT_THRESHOLD = 0.05
MIN_CA_DEGREE    = 2     # minimum distinct contractors per CA
MIN_GROUP_SIZE   = 5     # minimum CAs per CPV group to be testable
TOP_N_GROUPS     = 5     # groups reported in secondary analysis


def print_header(df_full, df_analysis):
    foreign_n   = df_full["is_foreign_contractor"].sum()
    foreign_pct = 100 * foreign_n / len(df_full)
    print(textwrap.dedent(f"""
    ============================================================
    Hypothesis  : {HYPOTHESIS_ID} — {HYPOTHESIS_STATEMENT}
    Graph form  : {GRAPH_FORM}
    Null model  : {NULL_MODEL}
    Constraint  : {DATA_CONSTRAINT}
    ------------------------------------------------------------
    Rows loaded      : {len(df_full):,}
    Analysis subset  : {len(df_analysis):,}
    Foreign excluded : {foreign_n:,} ({foreign_pct:.1f}%)
    ============================================================
    """).strip())


def load_data():
    df = pd.read_csv(DATA_PATH, low_memory=False)
    # Modal CPV group label must be computed over the full post-cleaning dataset
    # (all rows, not just analysis window). df_full is used for that.
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
    )
    return df, df[mask].copy()


def ca_modal_cpv(df_full):
    """
    Per CA: modal cpv_division by contract count across the full post-cleaning dataset.
    Tie-break by sum TotalValue.
    Returns dict {ca_id: '2d_prefix'}.
    """
    counts = (
        df_full.groupby(["CAIdentificationNumber", "cpv_division"])
        .agg(n_contracts=("Id", "count"), total_value=("TotalValue", "sum"))
        .reset_index()
    )
    counts = counts.sort_values(
        ["CAIdentificationNumber", "n_contracts", "total_value"],
        ascending=[True, False, False],
    )
    modal = counts.groupby("CAIdentificationNumber")["cpv_division"].first()
    return modal.to_dict()


def build_contractor_sets(df):
    """
    Per CA: frozenset of distinct ContractorIdentificationNumber values
    in the analysis window.
    Returns dict {ca_id: frozenset}.
    """
    result = {}
    for ca, grp in df.groupby("CAIdentificationNumber"):
        result[ca] = frozenset(grp["ContractorIdentificationNumber"].unique())
    return result


def jaccard(set_a, set_b):
    """|A ∩ B| / |A ∪ B|; return 0.0 if both empty."""
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


MAX_PAIRS_PER_GROUP = 5_000   # per-group sampling limit (groups 45/15 each have 300K+ pairs)
MAX_BETWEEN_PAIRS   = 50_000  # between-group sampling limit (~7M possible pairs)


def within_group_mean_jaccard(ca_groups, contractor_set_map):
    """
    For each group with ≥ MIN_GROUP_SIZE CAs: compute pairwise Jaccard;
    sample MAX_PAIRS_PER_GROUP random pairs if the group exceeds that count.

    Returns:
      group_means: dict {group_label: float}   (only powered groups)
      aggregate_mean: float
    """
    group_means = {}
    all_jaccards = []

    for group_label, ca_list in ca_groups.items():
        present = [c for c in ca_list if c in contractor_set_map]
        if len(present) < MIN_GROUP_SIZE:
            continue
        n = len(present)
        n_pairs = n * (n - 1) // 2
        jaccards = []
        if n_pairs <= MAX_PAIRS_PER_GROUP:
            for ca_i, ca_j in combinations(present, 2):
                jaccards.append(jaccard(contractor_set_map[ca_i], contractor_set_map[ca_j]))
        else:
            for _ in range(MAX_PAIRS_PER_GROUP):
                i, j = random.sample(range(n), 2)
                jaccards.append(jaccard(contractor_set_map[present[i]], contractor_set_map[present[j]]))
        if jaccards:
            group_means[group_label] = float(np.mean(jaccards))
            all_jaccards.extend(jaccards)

    aggregate = float(np.mean(all_jaccards)) if all_jaccards else 0.0
    return group_means, aggregate


def between_group_mean_jaccard(ca_groups, contractor_set_map):
    """
    Compute mean pairwise Jaccard across CA pairs from *different* groups.
    Samples MAX_BETWEEN_PAIRS random between-group pairs to keep runtime feasible.
    """
    powered_cas = []
    for group_label, ca_list in ca_groups.items():
        present = [c for c in ca_list if c in contractor_set_map]
        if len(present) >= MIN_GROUP_SIZE:
            for ca in present:
                powered_cas.append((ca, group_label))

    n = len(powered_cas)
    if n < 2:
        return 0.0

    between_jaccards = []
    attempts = 0
    max_attempts = MAX_BETWEEN_PAIRS * 5
    while len(between_jaccards) < MAX_BETWEEN_PAIRS and attempts < max_attempts:
        attempts += 1
        i, j = random.sample(range(n), 2)
        ca_i, g_i = powered_cas[i]
        ca_j, g_j = powered_cas[j]
        if g_i != g_j:
            between_jaccards.append(jaccard(contractor_set_map[ca_i], contractor_set_map[ca_j]))

    return float(np.mean(between_jaccards)) if between_jaccards else 0.0


# ---------------------------------------------------------------------------
# Degree-preserving edge switching (bipartite configuration model)
# ---------------------------------------------------------------------------

def rewire_edge_list(edges, n_swaps):
    """
    Degree-preserving bipartite edge switching.

    edges: list of (ca, contractor) tuples
    n_swaps: number of *successful* swaps to perform

    Accepts a swap only if:
      - the two new edges don't already exist in the edge set, and
      - no self-loop is created (not possible in bipartite, but guarded anyway).

    Returns a new list of (ca, contractor) edges.
    """
    edge_list = list(edges)
    edge_set  = set(edge_list)
    n         = len(edge_list)
    successful = 0
    max_attempts = n_swaps * 20   # cap to avoid infinite loop on dense graphs

    attempts = 0
    while successful < n_swaps and attempts < max_attempts:
        attempts += 1
        i = random.randrange(n)
        j = random.randrange(n)
        if i == j:
            continue
        ca_i, con_i = edge_list[i]
        ca_j, con_j = edge_list[j]
        # Must swap contractors between two different CA rows (bipartite constraint
        # is automatically preserved since both sides stay in their respective sets).
        if con_i == con_j or ca_i == ca_j:
            continue
        new_e1 = (ca_i, con_j)
        new_e2 = (ca_j, con_i)
        if new_e1 in edge_set or new_e2 in edge_set:
            continue
        # Accept swap
        edge_set.discard((ca_i, con_i))
        edge_set.discard((ca_j, con_j))
        edge_set.add(new_e1)
        edge_set.add(new_e2)
        edge_list[i] = new_e1
        edge_list[j] = new_e2
        successful += 1

    return edge_list


def null_ensemble(df, ca_groups, n=NULL_ITERATIONS):
    """
    Bipartite configuration model null for H11.
    Single pass: computes both aggregate and per-group null series in one rewiring loop.

    Returns:
      null_aggregates: list of n aggregate means
      null_group_series: dict {group_label: list of n floats}
    """
    edges       = list(zip(df["CAIdentificationNumber"], df["ContractorIdentificationNumber"]))
    n_edges     = len(edges)
    n_swaps     = 10 * n_edges

    relevant_cas = set()
    for ca_list in ca_groups.values():
        relevant_cas.update(ca_list)

    null_aggregates   = []
    null_group_series = {g: [] for g in ca_groups}

    for it in range(n):
        rewired = rewire_edge_list(edges, n_swaps)

        null_contractor_sets = {}
        for ca, con in rewired:
            if ca in relevant_cas:
                null_contractor_sets.setdefault(ca, set()).add(con)

        filtered_sets = {
            ca: frozenset(s)
            for ca, s in null_contractor_sets.items()
            if len(s) >= MIN_CA_DEGREE
        }

        g_means, agg = within_group_mean_jaccard(ca_groups, filtered_sets)
        null_aggregates.append(agg)
        for g in null_group_series:
            if g in g_means:
                null_group_series[g].append(g_means[g])

        if (it + 1) % 100 == 0:
            print(f"  null iteration {it+1}/{n} done …", flush=True)

    return null_aggregates, null_group_series


def per_group_test(group_means_obs, null_group_series, n_testable_groups):
    """
    Bonferroni-corrected per-group test.

    group_means_obs: dict {group_label: float}
    null_group_series: dict {group_label: list of null floats}
    n_testable_groups: int  — used for Bonferroni denominator

    Prints per-group results.
    """
    alpha_star = ALPHA / max(n_testable_groups, 1)
    pct_corrected = 100 * (1 - alpha_star)
    print(f"\nPer-group Bonferroni correction: α* = {ALPHA}/{n_testable_groups} = {alpha_star:.5f}")
    print(f"Rejection threshold: observed > {pct_corrected:.2f}th percentile of null\n")
    print(f"  {'Group':>6}  {'Obs':>8}  {'Null med':>9}  {'Null p95':>9}  {'Null p_corr':>11}  {'Excess':>8}  {'p-value':>8}  Result")
    print(f"  {'------':>6}  {'--------':>8}  {'---------':>9}  {'---------':>9}  {'-----------':>11}  {'--------':>8}  {'-------':>8}  ------")

    for group_label in sorted(group_means_obs.keys()):
        obs   = group_means_obs[group_label]
        nulls = np.array(null_group_series.get(group_label, []))
        if len(nulls) == 0:
            continue
        null_med  = float(np.median(nulls))
        null_p95  = float(np.percentile(nulls, 95))
        null_pcor = float(np.percentile(nulls, pct_corrected))
        excess    = obs - null_med
        p_val     = (np.sum(nulls >= obs) + 1) / (len(nulls) + 1)
        sig_corr  = "*" if obs > null_pcor else ""
        print(f"  {group_label:>6}  {obs:>8.4f}  {null_med:>9.4f}  {null_p95:>9.4f}  {null_pcor:>11.4f}  {excess:>+8.4f}  {p_val:>8.4f}  {sig_corr}")


def report(observed, null_values):
    null_arr    = np.array(null_values)
    null_median = float(np.median(null_arr))
    null_p95    = float(np.percentile(null_arr, 95))
    excess      = observed - null_median
    p_value     = (np.sum(null_arr >= observed) + 1) / (len(null_arr) + 1)

    print(f"Null median : {null_median:.4f}")
    print(f"Null 95th % : {null_p95:.4f}")
    print(f"Observed    : {observed:.4f}")
    print(f"Excess      : {excess:+.4f}")
    print(f"p-value     : {p_value:.4f}  (one-tailed, n={len(null_values)} iterations)")
    print()
    if p_value <= ALPHA and excess >= EFFECT_THRESHOLD:
        print("RESULT: reject null — effect above threshold")
        print("        Consistent with institutional convergence: CAs in the same CPV domain")
        print("        share vendor portfolios at rates above what shared market structure predicts.")
    elif p_value <= ALPHA:
        print("RESULT: reject null — excess below effect threshold (statistically significant, not substantively meaningful)")
    else:
        print("RESULT: fail to reject null")
        print("        Within-group CA portfolio overlap is consistent with shared market structure;")
        print("        no additional convergence beyond what degree sequence alone produces.")


def main():
    df_full, df = load_data()
    print_header(df_full, df)

    # --- Compute CA group labels from full dataset (not filtered subset) ---
    print("Computing CA modal CPV division (over full post-cleaning dataset) …")
    modal_cpv_map = ca_modal_cpv(df_full)
    print(f"  CAs with a modal CPV label: {len(modal_cpv_map):,}\n")

    # --- Build contractor sets from analysis window ---
    print("Building contractor sets from analysis window …")
    # Apply degree ≥ MIN_CA_DEGREE filter
    raw_contractor_sets = build_contractor_sets(df)
    contractor_set_map  = {
        ca: s for ca, s in raw_contractor_sets.items() if len(s) >= MIN_CA_DEGREE
    }
    print(f"  CAs in analysis window (all)          : {len(raw_contractor_sets):,}")
    print(f"  CAs with ≥ {MIN_CA_DEGREE} distinct contractors    : {len(contractor_set_map):,}\n")

    # --- Build group → CA list mapping ---
    # Only CAs that have a group label AND meet degree constraint
    ca_groups = {}
    for ca, group_label in modal_cpv_map.items():
        if ca in contractor_set_map:
            ca_groups.setdefault(group_label, []).append(ca)

    # Identify powered vs underpowered groups
    powered_groups    = {g: lst for g, lst in ca_groups.items() if len(lst) >= MIN_GROUP_SIZE}
    underpowered_groups = {g: lst for g, lst in ca_groups.items() if len(lst) < MIN_GROUP_SIZE}

    print(f"CPV groups with ≥ {MIN_GROUP_SIZE} CAs (testable)  : {len(powered_groups):,}")
    print(f"CPV groups with < {MIN_GROUP_SIZE} CAs (underpowered): {len(underpowered_groups):,}")
    total_cas_powered = sum(len(v) for v in powered_groups.values())
    print(f"CAs in powered groups                  : {total_cas_powered:,}\n")

    if not powered_groups:
        print("ERROR: No adequately-powered groups. Cannot proceed with test.")
        sys.exit(1)

    # --- Observed metric ---
    print("Computing observed within-group mean pairwise Jaccard …")
    obs_group_means, obs_aggregate = within_group_mean_jaccard(powered_groups, contractor_set_map)
    print(f"  Aggregate mean within-group Jaccard : {obs_aggregate:.4f}")
    print(f"  Groups contributing to aggregate   : {len(obs_group_means):,}\n")

    # --- Between-group Jaccard (secondary) ---
    print("Computing between-group mean Jaccard (secondary) …")
    between_jaccard = between_group_mean_jaccard(powered_groups, contractor_set_map)
    ratio = obs_aggregate / between_jaccard if between_jaccard > 0 else float("inf")
    print(f"  Between-group mean Jaccard         : {between_jaccard:.4f}")
    print(f"  Within / between ratio             : {ratio:.3f}\n")

    # --- Top-5 largest groups (by number of CAs) ---
    sorted_groups = sorted(obs_group_means.items(), key=lambda kv: -len(powered_groups[kv[0]]))
    top5 = sorted_groups[:TOP_N_GROUPS]
    print(f"Per-group mean Jaccard — {TOP_N_GROUPS} largest adequately-powered groups:")
    print(f"  {'Group':>6}  {'n_CAs':>6}  {'Obs Jaccard':>11}")
    print(f"  {'------':>6}  {'------':>6}  {'-----------':>11}")
    for g, jval in top5:
        n_cas = len(powered_groups[g])
        print(f"  {g:>6}  {n_cas:>6}  {jval:>11.4f}")
    print()

    # --- Null ensemble (single pass: aggregate + per-group) ---
    n_testable_groups = len(obs_group_means)
    print(f"Running null ensemble ({NULL_ITERATIONS} iterations, 10×|E| swaps each) …")
    print(f"  |E| = {len(df):,} edges  →  {10*len(df):,} target swaps per iteration")
    print(f"  Pair sampling: max {MAX_PAIRS_PER_GROUP:,}/group (groups 45/15 have 300K+ pairs)")

    null_aggregates, null_group_series = null_ensemble(df, powered_groups, n=NULL_ITERATIONS)

    print(f"\n{'='*60}")
    print("AGGREGATE TEST (one-tailed)")
    print(f"{'='*60}")
    report(obs_aggregate, null_aggregates)

    print()
    print(f"{'='*60}")
    print("PER-GROUP TEST (Bonferroni-corrected)")
    print(f"{'='*60}")
    per_group_test(obs_group_means, null_group_series, n_testable_groups)

    print(f"\n{'='*60}")
    print("SECONDARY: Within-group vs. between-group Jaccard")
    print(f"{'='*60}")
    print(f"  Within-group mean Jaccard  : {obs_aggregate:.4f}")
    print(f"  Between-group mean Jaccard : {between_jaccard:.4f}")
    print(f"  Ratio (within/between)     : {ratio:.3f}")
    if ratio > 1.0:
        print("  Within-group overlap exceeds between-group — group structure mirrors CPV domain.")
    else:
        print("  Within-group overlap does not exceed between-group — no CPV-aligned portfolio clustering.")


if __name__ == "__main__":
    main()
