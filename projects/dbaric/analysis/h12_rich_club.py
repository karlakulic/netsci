"""
H12 — Rich club: high-value contractors share client bases at above-chance rates.
Bipartite configuration model null via edge-count-preserving rewiring.
"""

# ---------------------------------------------------------------------------
# Pre-flight spec — must match docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H12"
HYPOTHESIS_STATEMENT = "The highest-value contractors share client bases with each other at above-chance rates (rich club)"
GRAPH_FORM           = "bipartite simple graph (collapse multigraph; CA–contractor edge if ≥1 contract; IsUponFA=false)"
NULL_MODEL           = "Bipartite configuration model — edge-count-preserving rewiring; null distribution of mean pairwise Jaccard among top-1% contractors by strength"
DATA_CONSTRAINT      = "none"
# ---------------------------------------------------------------------------

import random
import sys
import textwrap
from itertools import combinations

import numpy as np
import pandas as pd

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
EFFECT_THRESHOLD = 0.05

# Rich-club curve thresholds
CURVE_THRESHOLDS = (0.01, 0.05, 0.10, 0.25)

# Target successful swaps per null instance (10 × |E|)
SWAP_MULTIPLIER = 10


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(include_calloffs=False):
    df = pd.read_csv(DATA_PATH, low_memory=False)
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_foreign_contractor"].eq(False)
    )
    if not include_calloffs:
        mask = mask & df["is_framework_calloff"].eq(False)
    return df, df[mask].copy()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def print_header(df_full, df_analysis):
    foreign_n = int(df_full["is_foreign_contractor"].sum())
    foreign_pct = 100.0 * foreign_n / len(df_full)
    print(textwrap.dedent(f"""
    ============================================================
    Hypothesis  : {HYPOTHESIS_ID} — {HYPOTHESIS_STATEMENT}
    Graph form  : {GRAPH_FORM}
    Null model  : {NULL_MODEL}
    Constraint  : {DATA_CONSTRAINT}
    NULL_ITERATIONS = {NULL_ITERATIONS} (graph-level null); edge-count-preserving variant
    ------------------------------------------------------------
    Rows loaded      : {len(df_full):,}
    Analysis subset  : {len(df_analysis):,}
    Foreign excluded : {foreign_n:,} ({foreign_pct:.1f}%)
    ============================================================
    """).strip())


# ---------------------------------------------------------------------------
# Graph construction — bipartite simple graph (collapsed multigraph)
# ---------------------------------------------------------------------------

def build_edge_list(df):
    """
    Return a list of unique (ca, contractor) tuples — one entry per CA–contractor
    pair regardless of how many contracts they share.  This is the simple bipartite
    graph edge set.
    """
    pairs = (
        df[["CAIdentificationNumber", "ContractorIdentificationNumber"]]
        .drop_duplicates()
    )
    return list(zip(pairs["CAIdentificationNumber"], pairs["ContractorIdentificationNumber"]))


# ---------------------------------------------------------------------------
# Contractor strength and rank
# ---------------------------------------------------------------------------

def contractor_strength_rank(df):
    """
    Return a list of contractor IDs sorted descending by total TotalValue.
    Uses all contracts in df (already filtered to analysis subset).
    """
    strength = (
        df.groupby("ContractorIdentificationNumber")["TotalValue"]
        .sum()
        .sort_values(ascending=False)
    )
    return list(strength.index)


def top_k_contractors(ranked_contractors, fraction):
    """Return the top fraction (e.g. 0.01) of contractors by strength rank."""
    k = max(1, round(len(ranked_contractors) * fraction))
    return ranked_contractors[:k]


# ---------------------------------------------------------------------------
# CA sets and Jaccard
# ---------------------------------------------------------------------------

def build_ca_sets(edges):
    """
    Given an edge list of (ca, contractor) tuples, return a dict
    {contractor_id: frozenset of ca_ids}.
    """
    ca_map = {}
    for ca, con in edges:
        if con not in ca_map:
            ca_map[con] = set()
        ca_map[con].add(ca)
    return {k: frozenset(v) for k, v in ca_map.items()}


def jaccard(set_a, set_b):
    """Jaccard similarity between two frozensets. Returns 0.0 if both empty."""
    if not set_a and not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


MAX_PAIRS = 50_000  # for large clubs, sample this many pairs to keep runtime feasible

def mean_pairwise_jaccard(contractor_ids, ca_set_map, max_pairs=MAX_PAIRS):
    """
    Compute mean pairwise Jaccard among all pairs in contractor_ids.
    If n_pairs > max_pairs, randomly sample max_pairs pairs (unbiased estimator).
    contractor_ids: list of contractor IDs in the rich-club set.
    ca_set_map: dict {contractor_id: frozenset of CA IDs}.
    Returns 0.0 if fewer than 2 contractors (no pairs).
    """
    ids = [c for c in contractor_ids if c in ca_set_map]
    n = len(ids)
    if n < 2:
        return 0.0
    n_pairs = n * (n - 1) // 2
    if n_pairs <= max_pairs:
        total = 0.0
        for i, j in combinations(range(n), 2):
            total += jaccard(ca_set_map[ids[i]], ca_set_map[ids[j]])
        return total / n_pairs
    else:
        # Random pair sampling — unbiased estimate of mean Jaccard
        total = 0.0
        for _ in range(max_pairs):
            i, j = random.sample(range(n), 2)
            total += jaccard(ca_set_map[ids[i]], ca_set_map[ids[j]])
        return total / max_pairs


# ---------------------------------------------------------------------------
# Edge-count-preserving rewiring (degree-preserving swap)
# ---------------------------------------------------------------------------

def rewire_edges(edges, n_swaps_target):
    """
    Degree-preserving edge switching on a bipartite edge list.
    edges: list of (ca, contractor) tuples (no duplicates — simple graph).
    n_swaps_target: number of *successful* swaps to perform.

    Swap: pick edges (a, b) and (c, d).
    Try (a, d) and (c, b).  Accept if neither is a self-loop (not possible in bipartite,
    since a and c are both CA nodes, b and d are both contractor nodes) and neither
    already exists in the current edge set.
    Fall back to swap (a, c) and (b, d) — but both a,c are CAs and b,d are contractors,
    so (a,c) would be CA–CA: invalid in bipartite.  Only (a,d)/(c,b) is valid here.

    Returns a NEW list of edges (does not mutate input).
    """
    edge_set = set(edges)
    edge_list = list(edges)
    m = len(edge_list)
    if m < 2:
        return edge_list

    successful = 0
    max_attempts = n_swaps_target * 10  # bound total loop iterations
    attempts = 0

    while successful < n_swaps_target and attempts < max_attempts:
        attempts += 1
        i, j = random.sample(range(m), 2)
        a, b = edge_list[i]   # a = CA, b = contractor
        c, d = edge_list[j]   # c = CA, d = contractor

        # Skip if endpoints already overlap (swap would be trivial)
        if b == d or a == c:
            continue

        # Proposed swap: (a, d) and (c, b)
        new1 = (a, d)
        new2 = (c, b)

        if new1 in edge_set or new2 in edge_set:
            continue

        # Accept swap
        edge_set.discard((a, b))
        edge_set.discard((c, d))
        edge_set.add(new1)
        edge_set.add(new2)
        edge_list[i] = new1
        edge_list[j] = new2
        successful += 1

    return list(edge_set)


# ---------------------------------------------------------------------------
# Null ensemble
# ---------------------------------------------------------------------------

def compute_null_ca_maps(edges, n=NULL_ITERATIONS):
    """Pre-compute n rewired CA-set maps. Done ONCE and reused across all thresholds."""
    m = len(edges)
    n_swaps = SWAP_MULTIPLIER * m
    maps = []
    for i in range(n):
        rewired = rewire_edges(edges, n_swaps)
        maps.append(build_ca_sets(rewired))
        if (i + 1) % 100 == 0:
            print(f"  rewiring {i + 1}/{n} done ...", flush=True)
    return maps


def null_jaccard_from_maps(null_ca_maps, top_contractors):
    """Compute null Jaccard values from pre-computed rewired CA-set maps."""
    return [mean_pairwise_jaccard(top_contractors, m) for m in null_ca_maps]


# ---------------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------------

def report_metric(label, observed, null_values, effect_threshold=EFFECT_THRESHOLD):
    null_arr = np.array(null_values)
    null_median = float(np.median(null_arr))
    null_p95 = float(np.percentile(null_arr, 95))
    excess = observed - null_median
    p_value = (np.sum(null_arr >= observed) + 1) / (len(null_arr) + 1)

    print(f"  {label}")
    print(f"    Null median : {null_median:.6f}")
    print(f"    Null 95th % : {null_p95:.6f}")
    print(f"    Observed    : {observed:.6f}")
    print(f"    Excess      : {excess:+.6f}")
    print(f"    p-value     : {p_value:.4f}  (one-tailed, n={len(null_arr)} iterations)")
    if p_value <= ALPHA and excess >= effect_threshold:
        verdict = "REJECT NULL — effect above threshold"
    elif p_value <= ALPHA:
        verdict = "REJECT NULL — but excess below effect threshold (significant, not substantive)"
    else:
        verdict = "FAIL TO REJECT NULL"
    print(f"    Result      : {verdict}")
    print()
    return {
        "observed": observed,
        "null_median": null_median,
        "null_p95": null_p95,
        "excess": excess,
        "p_value": p_value,
        "reject": p_value <= ALPHA and excess >= effect_threshold,
    }


# ---------------------------------------------------------------------------
# Rich-club curve
# ---------------------------------------------------------------------------

def rich_club_curve(ranked_contractors, edges, null_ca_maps, thresholds=CURVE_THRESHOLDS):
    """
    For each threshold, compute observed Jaccard and null Jaccard from pre-computed
    rewired CA-set maps (shared across thresholds — no extra rewiring done here).
    Pair sampling applied automatically by mean_pairwise_jaccard for large clubs.
    """
    print("=== RICH-CLUB CURVE ===")
    print(f"  (null CA-set maps pre-computed and shared; pair sampling at >{MAX_PAIRS:,} pairs)\n")
    header = (
        f"{'threshold':>10}  {'n_con':>7}  {'n_pairs':>12}  {'sampled':>8}  {'observed':>10}  "
        f"{'null_med':>10}  {'null_p95':>10}  "
        f"{'excess':>10}  {'p-value':>8}  {'reject?':>8}"
    )
    print(header)
    print("-" * len(header))

    ca_map_obs = build_ca_sets(edges)

    for thr in thresholds:
        top_cons = top_k_contractors(ranked_contractors, thr)
        n_con = len(top_cons)
        n_pairs_full = n_con * (n_con - 1) // 2
        sampled = "yes" if n_pairs_full > MAX_PAIRS else "no"
        obs = mean_pairwise_jaccard(top_cons, ca_map_obs)

        null_vals = null_jaccard_from_maps(null_ca_maps, top_cons)

        null_arr = np.array(null_vals)
        null_med = float(np.median(null_arr))
        null_p95 = float(np.percentile(null_arr, 95))
        excess = obs - null_med
        p_val = (np.sum(null_arr >= obs) + 1) / (len(null_arr) + 1)
        reject = "YES" if (p_val <= ALPHA and excess >= EFFECT_THRESHOLD) else "no"

        print(
            f"{thr:>10.2%}  {n_con:>7,}  {n_pairs_full:>12,}  {sampled:>8}  {obs:>10.6f}  "
            f"{null_med:>10.6f}  {null_p95:>10.6f}  "
            f"{excess:>+10.6f}  {p_val:>8.4f}  {reject:>8}"
        )
    print()


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run_primary_analysis(df, label="PRIMARY (IsUponFA=False)", n_null=NULL_ITERATIONS):
    """Build graph, rank contractors, pre-compute null rewirings once, run all thresholds."""
    print(f"\n=== {label} ===\n")

    edges = build_edge_list(df)
    n_ca = df["CAIdentificationNumber"].nunique()
    n_con = df["ContractorIdentificationNumber"].nunique()
    print(f"  Nodes (CA)          : {n_ca:,}")
    print(f"  Nodes (contractor)  : {n_con:,}")
    print(f"  Edges (unique pairs): {len(edges):,}")

    ranked = contractor_strength_rank(df)

    # Primary: top-1%
    top1 = top_k_contractors(ranked, 0.01)
    print(f"  Top-1% club size    : {len(top1):,}  (n_contractors × 0.01 = {round(n_con * 0.01)})")
    n_pairs_1pct = len(top1) * (len(top1) - 1) // 2
    print(f"  Pairs in top-1% set : {n_pairs_1pct:,}")

    ca_map = build_ca_sets(edges)
    obs = mean_pairwise_jaccard(top1, ca_map)

    # Pre-compute null CA-set maps ONCE — reused for all thresholds
    print(f"\n  Pre-computing {n_null} rewired CA-set maps (target swaps = 10×|E| = {10*len(edges):,})...")
    null_ca_maps = compute_null_ca_maps(edges, n=n_null)

    # Primary test: top-1%
    null_vals = null_jaccard_from_maps(null_ca_maps, top1)
    print(f"\n--- Primary metric: mean pairwise Jaccard, top-1% contractors ---")
    result = report_metric("Mean pairwise Jaccard (top-1%)", obs, null_vals)

    print()
    rich_club_curve(ranked, edges, null_ca_maps, thresholds=CURVE_THRESHOLDS)

    return result


def main():
    # --- Primary run (IsUponFA=False, call-offs excluded) ---
    df_full, df = load_data(include_calloffs=False)
    print_header(df_full, df)

    primary_result = run_primary_analysis(df, label="PRIMARY ANALYSIS (IsUponFA=False)", n_null=NULL_ITERATIONS)

    # --- Sensitivity check (call-offs included) ---
    print("\n=== SENSITIVITY CHECK (is_framework_calloff=True included) ===\n")
    print("NOTE: This rerun includes framework call-off contracts (IsUponFA=True).")
    print("      Results annotated as sensitivity only; primary finding is above.\n")
    _, df_sens = load_data(include_calloffs=True)
    print(f"  Sensitivity subset rows: {len(df_sens):,}")
    run_primary_analysis(df_sens, label="SENSITIVITY (incl. call-offs)", n_null=NULL_ITERATIONS)


if __name__ == "__main__":
    main()
