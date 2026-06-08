"""
H10 — Network resilience: targeted vs random contractor removal
Bipartite simple graph (collapsed multigraph); neighbor-set iteration (no graph copies).
"""

# ---------------------------------------------------------------------------
# Pre-flight spec — must match docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H10"
HYPOTHESIS_STATEMENT = "Removing the highest-value contractors strands significantly more public institutions than random removal"
GRAPH_FORM           = "bipartite simple graph (collapsed multigraph — one edge per CA–contractor pair; IsUponFA=false)"
NULL_MODEL           = "Random contractor removal curve — 1,000 permutations of random removal order; null envelope of isolated CA counts at each step k"
DATA_CONSTRAINT      = "none"
# ---------------------------------------------------------------------------

import sys
import textwrap

import numpy as np
import pandas as pd

DATA_PATH      = "data/contracts_clean.csv"
NULL_PERMS     = 1_000
PRIMARY_K      = 10          # top k contractors by total TotalValue
ISOLATION_PCT  = 0.10        # threshold for "10% of CAs isolated" secondary report
EFFECT_PCT_CAS = 0.05        # effect threshold: excess ≥ 5% of all CAs
ALPHA          = 0.05
MAX_CURVE_K    = 50          # print isolation curve up to this k


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(include_calloffs: bool = False):
    df = pd.read_csv(DATA_PATH, low_memory=False)
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
    )
    if include_calloffs:
        # sensitivity: drop the calloff filter
        mask = df["in_analysis_window"].eq(True) & df["is_eur"].eq(True)
    return df, df[mask].copy()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def print_header(df_full, df_analysis, *, include_calloffs: bool = False):
    foreign_n   = df_full["is_foreign_contractor"].sum()
    foreign_pct = 100.0 * foreign_n / len(df_full)
    calloff_tag = " [SENSITIVITY: call-offs included]" if include_calloffs else ""
    print(textwrap.dedent(f"""
    ============================================================
    Hypothesis  : {HYPOTHESIS_ID} — {HYPOTHESIS_STATEMENT}
    Graph form  : {GRAPH_FORM}
    Null model  : {NULL_MODEL}
    Constraint  : {DATA_CONSTRAINT}{calloff_tag}
    ------------------------------------------------------------
    Rows loaded      : {len(df_full):,}
    Analysis subset  : {len(df_analysis):,}
    Foreign excluded : {foreign_n:,} ({foreign_pct:.1f}%)
    ============================================================
    """).strip())


# ---------------------------------------------------------------------------
# Graph construction (neighbor-set representation)
# ---------------------------------------------------------------------------

def build_neighbor_sets(df):
    """
    Returns:
        ca_neighbors   : dict { ca_id  -> set of contractor_ids } (mutable sets)
        contractor_value: dict { contractor_id -> total TotalValue }
        n_cas          : int  (total unique CAs in the bipartite simple graph)
    """
    # Collapse multigraph: one edge per (CA, contractor) pair
    edges = (
        df.groupby(["CAIdentificationNumber", "ContractorIdentificationNumber"])["TotalValue"]
        .sum()
        .reset_index()
    )
    ca_neighbors: dict[object, set] = {}
    contractor_value: dict[object, float] = {}

    for row in edges.itertuples(index=False):
        ca  = row.CAIdentificationNumber
        con = row.ContractorIdentificationNumber
        val = row.TotalValue

        ca_neighbors.setdefault(ca, set()).add(con)
        contractor_value[con] = contractor_value.get(con, 0.0) + val

    return ca_neighbors, contractor_value


# ---------------------------------------------------------------------------
# Targeted removal curve
# ---------------------------------------------------------------------------

def targeted_removal_curve(ca_neighbors_init, contractor_order, max_k: int):
    """
    Remove contractors in `contractor_order` one at a time.
    After each removal, count CAs whose neighbor set is now empty.

    Uses a copy of the neighbor sets so the original is preserved.
    Returns array of length min(max_k, len(contractor_order)).
    """
    # Work on mutable copies
    ca_nb = {ca: set(nbrs) for ca, nbrs in ca_neighbors_init.items()}

    curve = []
    for k, con in enumerate(contractor_order):
        if k >= max_k:
            break
        # Remove this contractor from every CA that had it
        for ca in list(ca_nb.keys()):
            ca_nb[ca].discard(con)
        isolated = sum(1 for nbrs in ca_nb.values() if len(nbrs) == 0)
        curve.append(isolated)

    return np.array(curve, dtype=np.int32)


# ---------------------------------------------------------------------------
# Null model: vectorised over permutations using neighbor-set approach
# ---------------------------------------------------------------------------

def random_removal_null(ca_neighbors_init, all_contractors, max_k: int, n_perms: int = NULL_PERMS, rng=None):
    """
    For each of n_perms permutations, shuffle contractor order and compute
    the isolation curve up to max_k steps.

    Returns null_array of shape (n_perms, max_k):
        null_array[perm, k] = isolated CA count after removing k+1 contractors.

    Strategy: represent each CA as a set index into a contractor index array,
    then use numpy operations per step.
    """
    if rng is None:
        rng = np.random.default_rng(seed=42)

    contractors_arr = np.array(all_contractors)
    n_contractors   = len(contractors_arr)
    actual_k        = min(max_k, n_contractors)

    # Map contractor → integer index
    con_to_idx = {c: i for i, c in enumerate(contractors_arr)}

    # Represent each CA's neighbor set as a boolean array (n_contractors,)
    # Then "remove" = set that column to False across all CAs.
    # For n_cas * n_contractors this may be large; use a per-CA set of indices instead
    # to keep memory reasonable.
    cas         = list(ca_neighbors_init.keys())
    n_cas       = len(cas)
    # ca_idx_sets[i] = set of contractor integer indices for cas[i]
    ca_idx_sets = [
        {con_to_idx[c] for c in ca_neighbors_init[cas[i]] if c in con_to_idx}
        for i in range(n_cas)
    ]

    null_array = np.zeros((n_perms, actual_k), dtype=np.int32)

    for perm in range(n_perms):
        order = rng.permutation(n_contractors)  # shuffled indices into contractors_arr

        # Working copy: for each CA a set of remaining contractor indices
        remaining = [s.copy() for s in ca_idx_sets]

        for k, con_idx in enumerate(order[:actual_k]):
            # Remove con_idx from every CA
            for ca_set in remaining:
                ca_set.discard(con_idx)
            isolated = sum(1 for s in remaining if len(s) == 0)
            null_array[perm, k] = isolated

        if (perm + 1) % 100 == 0:
            print(f"  Null permutations completed: {perm + 1}/{n_perms}", flush=True)

    return null_array


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(targeted_curve, null_array, n_cas: int, primary_k: int = PRIMARY_K):
    k_obs   = primary_k - 1      # 0-indexed
    obs_k10 = int(targeted_curve[k_obs])

    null_at_k10        = null_array[:, k_obs]
    null_median_k10    = float(np.median(null_at_k10))
    null_p95_k10       = float(np.percentile(null_at_k10, 95))
    excess_k10         = obs_k10 - null_median_k10
    # One-tailed p-value: fraction of null permutations ≥ observed
    p_value            = (np.sum(null_at_k10 >= obs_k10) + 1) / (len(null_at_k10) + 1)

    effect_floor       = EFFECT_PCT_CAS * n_cas
    effect_floor_int   = int(np.ceil(effect_floor))

    print()
    print("=" * 60)
    print(f"PRIMARY TEST — targeted removal at k={primary_k}")
    print("=" * 60)
    print(f"Total CAs              : {n_cas:,}")
    print(f"5% effect floor        : {effect_floor_int:,} CAs (= 5% × {n_cas:,})")
    print(f"Null median @ k={primary_k}     : {null_median_k10:.1f}")
    print(f"Null 95th pct @ k={primary_k}  : {null_p95_k10:.1f}")
    print(f"Observed @ k={primary_k}       : {obs_k10:,}")
    print(f"Excess (obs − null med) : {excess_k10:+.1f}")
    print(f"p-value (one-tailed)    : {p_value:.4f}  (n={len(null_at_k10):,} perms)")
    print()

    stat_sig   = p_value <= ALPHA
    above_eff  = excess_k10 >= effect_floor_int

    if stat_sig and above_eff:
        print("RESULT: reject null — targeted removal isolates significantly more CAs; excess above 5% effect threshold")
    elif stat_sig:
        print("RESULT: reject null — statistically significant, but excess below 5% effect threshold (not substantively meaningful)")
    else:
        print("RESULT: fail to reject null — targeted removal not significantly worse than random")

    # -----------------------------------------------------------------------
    # Secondary: full isolation curve table (k=1..MAX_CURVE_K)
    # -----------------------------------------------------------------------
    actual_curve_len = len(targeted_curve)
    max_display      = min(MAX_CURVE_K, actual_curve_len)

    print()
    print("=" * 60)
    print("SECONDARY — isolation curve (k contractors removed)")
    print("=" * 60)
    print(f"{'k':>4}  {'targeted':>10}  {'null_median':>11}  {'null_p95':>9}  {'excess':>8}")
    print("-" * 52)
    for k in range(max_display):
        t_iso      = int(targeted_curve[k])
        n_med      = float(np.median(null_array[:, k]))
        n_p95      = float(np.percentile(null_array[:, k], 95))
        exc        = t_iso - n_med
        print(f"{k+1:>4}  {t_iso:>10,}  {n_med:>11.1f}  {n_p95:>9.1f}  {exc:>+8.1f}")

    # k at which 10% of CAs become isolated under targeted vs null median
    target_10pct = int(np.ceil(ISOLATION_PCT * n_cas))
    k_targeted_10pct = None
    k_null_10pct     = None

    for k in range(actual_curve_len):
        if k_targeted_10pct is None and int(targeted_curve[k]) >= target_10pct:
            k_targeted_10pct = k + 1  # 1-indexed
        null_med_k = float(np.median(null_array[:, k]))
        if k_null_10pct is None and null_med_k >= target_10pct:
            k_null_10pct = k + 1

    print()
    print(f"10% isolation threshold : {target_10pct:,} CAs")
    if k_targeted_10pct is not None:
        print(f"Targeted reaches 10%   : k = {k_targeted_10pct}")
    else:
        print(f"Targeted reaches 10%   : not reached within k={actual_curve_len}")
    if k_null_10pct is not None:
        print(f"Null median reaches 10%: k = {k_null_10pct}")
    else:
        print(f"Null median reaches 10%: not reached within k={actual_curve_len}")

    if k_targeted_10pct is not None and k_null_10pct is not None:
        gap = k_null_10pct - k_targeted_10pct
        if gap > 0:
            print(f"Fragility gap          : targeted isolates 10% of CAs {gap} steps earlier than random removal")
        elif gap == 0:
            print(f"Fragility gap          : 0 — targeted and random reach 10% isolation at the same k")
        else:
            print(f"Fragility gap          : targeted reaches 10% *later* than random by {abs(gap)} steps")


# ---------------------------------------------------------------------------
# Sensitivity check wrapper
# ---------------------------------------------------------------------------

def run_analysis(include_calloffs: bool = False, tag: str = ""):
    df_full, df = load_data(include_calloffs=include_calloffs)
    print_header(df_full, df, include_calloffs=include_calloffs)

    if tag:
        print(f"\n[{tag}]")

    # Build neighbor-set representation
    print("\nBuilding bipartite simple graph (neighbor sets)...")
    ca_neighbors, contractor_value = build_neighbor_sets(df)

    n_cas        = len(ca_neighbors)
    n_contractors = len(contractor_value)
    total_edges  = sum(len(v) for v in ca_neighbors.values())

    print(f"Unique CAs         : {n_cas:,}")
    print(f"Unique contractors : {n_contractors:,}")
    print(f"Edges (CA–con)     : {total_edges:,}")

    # Targeted order: descending total TotalValue
    targeted_order = sorted(
        contractor_value.keys(),
        key=lambda c: contractor_value[c],
        reverse=True
    )

    max_k = min(MAX_CURVE_K, n_contractors)

    # Targeted removal curve
    print(f"\nComputing targeted removal curve (k=1..{max_k})...")
    targeted_curve = targeted_removal_curve(ca_neighbors, targeted_order, max_k)

    # Null model
    print(f"\nRunning null model ({NULL_PERMS:,} random permutations)...")
    rng = np.random.default_rng(seed=42)
    null_array = random_removal_null(
        ca_neighbors,
        list(contractor_value.keys()),
        max_k=max_k,
        n_perms=NULL_PERMS,
        rng=rng,
    )

    # Report
    report(targeted_curve, null_array, n_cas=n_cas, primary_k=PRIMARY_K)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    # Primary analysis: IsUponFA = false (call-offs excluded)
    run_analysis(include_calloffs=False, tag="")

    print()
    print()
    print("=" * 60)
    print("SENSITIVITY CHECK — including framework call-offs")
    print("=" * 60)
    run_analysis(include_calloffs=True, tag="SENSITIVITY: is_framework_calloff filter removed")


if __name__ == "__main__":
    main()
