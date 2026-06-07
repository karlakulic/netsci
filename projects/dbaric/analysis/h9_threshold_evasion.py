"""
H9 — Value threshold evasion (contract splitting).
One script per hypothesis.
"""

# ---------------------------------------------------------------------------
# Pre-flight spec — matches docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H9"
HYPOTHESIS_STATEMENT = "Authorities cluster below-threshold contracts with the same vendor within short time windows at rates consistent with deliberate threshold evasion"
GRAPH_FORM           = "bipartite multigraph; 90-day rolling window; T applied by ContractTypeId separately"
NULL_MODEL           = "within-pair temporal permutation (1,000 permutations per pair; shuffle ContractDate values)"
DATA_CONSTRAINT      = "T_goods_services=26540 (ContractTypeId 1,2); T_works=66360 (ContractTypeId 3); McCrary discontinuity test required as preliminary step"
# ---------------------------------------------------------------------------

import random
import textwrap

import numpy as np
import pandas as pd
from scipy.stats import binom

DATA_PATH        = "data/contracts_clean.csv"
ALPHA            = 0.05
PAIR_NULL_ITERS  = 1000
WINDOW_DAYS      = 90
EFFECT_THRESHOLD = 0.10       # 10pp above 5% baseline
MAX_PAIRS        = 50_000

T_GOODS_SERVICES = 26_540.0
T_WORKS          = 66_360.0

CONTRACT_TYPE_T = {
    1: T_GOODS_SERVICES,
    2: T_GOODS_SERVICES,
    3: T_WORKS,
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    df = pd.read_csv(DATA_PATH, low_memory=False, parse_dates=["ContractDate"])
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
        & df["is_foreign_contractor"].eq(False)
    )
    return df, df[mask].copy()


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
    Thresholds       : goods/services T={T_GOODS_SERVICES:,.0f} EUR; works T={T_WORKS:,.0f} EUR
    ============================================================
    """).strip())


# ---------------------------------------------------------------------------
# McCrary-style density test
# ---------------------------------------------------------------------------

def mccrary_density_test(df, contract_type_ids, T_primary, label):
    print(f"\n  McCrary density check — {label} (T={T_primary:,.0f})")
    subset = df[df["ContractTypeId"].isin(contract_type_ids)].copy()
    subset = subset[(subset["TotalValue"] > 0) & subset["TotalValue"].notna()]

    below = subset[(subset["TotalValue"] >= T_primary * 0.5) & (subset["TotalValue"] < T_primary)]
    above = subset[(subset["TotalValue"] > T_primary) & (subset["TotalValue"] <= T_primary * 2.0)]

    ratio = len(below) / max(len(above), 1)
    print(f"  Contracts in [T/2, T) : {len(below):,}")
    print(f"  Contracts in (T, 2T]  : {len(above):,}")
    print(f"  Density ratio below/above T={T_primary:,.0f}: {ratio:.2f}")
    if ratio > 2.0:
        print(f"  SIGNAL: Excess mass below threshold — consistent with bunching at T={T_primary:,.0f}")
    else:
        print(f"  No strong density discontinuity signal at T={T_primary:,.0f}")
    return ratio


# ---------------------------------------------------------------------------
# Cluster counting
# ---------------------------------------------------------------------------

def count_splitting_clusters(pair_df, T, window_days=WINDOW_DAYS):
    """Count distinct windows where k>=2 below-T contracts aggregate to >= T."""
    pair_df = pair_df[pair_df["TotalValue"] < T].sort_values("ContractDate").reset_index(drop=True)
    if len(pair_df) < 2:
        return 0

    dates  = pair_df["ContractDate"].values
    values = pair_df["TotalValue"].values
    window = pd.Timedelta(days=window_days)

    clusters = 0
    used     = set()
    for i in range(len(dates)):
        if i in used:
            continue
        in_window = [
            j for j in range(i, len(dates))
            if (dates[j] - dates[i]) <= window and j not in used
        ]
        if len(in_window) >= 2 and sum(values[j] for j in in_window) >= T:
            clusters += 1
            for j in in_window:
                used.add(j)
    return clusters


# ---------------------------------------------------------------------------
# Null model for a single pair
# ---------------------------------------------------------------------------

def pair_temporal_null(pair_df, T, n=PAIR_NULL_ITERS):
    dates    = pair_df["ContractDate"].tolist()
    shuffled = pair_df.copy()
    results  = []
    for _ in range(n):
        random.shuffle(dates)
        shuffled = pair_df.copy()
        shuffled["ContractDate"] = dates
        results.append(count_splitting_clusters(shuffled, T))
    return results


# ---------------------------------------------------------------------------
# Market-level binomial test
# ---------------------------------------------------------------------------

def binomial_market_test(n_significant, n_pairs, alpha=ALPHA):
    if n_pairs == 0:
        return 0.0, 0.0, 1.0
    fraction    = n_significant / n_pairs
    p_value     = 1 - binom.cdf(n_significant - 1, n_pairs, 0.05)
    threshold   = binom.ppf(1 - alpha, n_pairs, 0.05) / n_pairs
    return fraction, threshold, p_value


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df_full, df = load_data()
    print_header(df_full, df)

    # Preliminary: McCrary density tests
    print("\n" + "="*60)
    print("PRELIMINARY: McCrary-style density discontinuity test")
    mccrary_density_test(df, [1, 2], T_GOODS_SERVICES, "goods/services (ContractTypeId 1,2)")
    mccrary_density_test(df, [3],    T_WORKS,           "works (ContractTypeId 3)")

    # Build pairs: group by (CA, contractor, ContractTypeId); require >= 2 contracts
    print("\n" + "="*60)
    print("MAIN TEST: temporal splitting clusters")

    df_eligible = df[
        df["ContractTypeId"].isin([1, 2, 3])
        & df["TotalValue"].notna()
        & (df["TotalValue"] > 0)
        & df["ContractDate"].notna()
    ].copy()

    pair_groups = df_eligible.groupby(
        ["CAIdentificationNumber", "ContractorIdentificationNumber", "ContractTypeId"]
    )
    eligible_pairs = [
        (key, grp) for key, grp in pair_groups if len(grp) >= 2
    ]

    n_pairs_total = len(eligible_pairs)
    print(f"Eligible pairs (>=2 contracts): {n_pairs_total:,}")

    truncated = n_pairs_total > MAX_PAIRS
    if truncated:
        print(f"[WARN] Truncating to MAX_PAIRS={MAX_PAIRS:,} (first {MAX_PAIRS:,} pairs)")
        eligible_pairs = eligible_pairs[:MAX_PAIRS]

    n_significant = 0
    n_processed   = len(eligible_pairs)

    for idx, ((ca, contractor, ctype_id), pair_df) in enumerate(eligible_pairs):
        if idx > 0 and idx % 5000 == 0:
            print(f"  ... {idx:,}/{n_processed:,} pairs processed", flush=True)

        T         = CONTRACT_TYPE_T[ctype_id]
        obs_count = count_splitting_clusters(pair_df, T)

        if obs_count == 0:
            # Null will always be >= 0; skip permutation loop to save time
            continue

        null_counts = pair_temporal_null(pair_df, T, n=PAIR_NULL_ITERS)
        p95_null    = float(np.percentile(null_counts, 95))

        if obs_count > p95_null:
            n_significant += 1

    fraction, threshold_frac, p_binom = binomial_market_test(n_significant, n_processed)

    print(f"\n{'='*60}")
    print(f"RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Pairs analysed           : {n_processed:,}")
    if truncated:
        print(f"  [NOTE] Truncated from {n_pairs_total:,} — results cover only first {MAX_PAIRS:,} pairs")
    print(f"Pairs significant        : {n_significant:,}")
    print(f"Observed fraction        : {fraction:.4f}  ({100*fraction:.1f}%)")
    print(f"Binom threshold fraction : {threshold_frac:.4f}  ({100*threshold_frac:.1f}%)")
    print(f"Effect threshold         : {EFFECT_THRESHOLD:.2f}  ({100*EFFECT_THRESHOLD:.0f}%)")
    print(f"Binom p-value            : {p_binom:.4f}")
    print()

    reject_binom = p_binom <= ALPHA
    above_effect = fraction >= (0.05 + EFFECT_THRESHOLD)

    if reject_binom and above_effect:
        print("RESULT: reject null — fraction of splitting pairs exceeds effect threshold")
        print("        Consistent with deliberate threshold evasion beyond random contract timing")
    elif reject_binom:
        print("RESULT: reject null statistically but fraction below effect threshold")
        print("        Statistically detectable but not substantively meaningful")
    else:
        print("RESULT: fail to reject null — temporal clustering consistent with random ordering")

    print()
    print("NOTE: If H3 (Q4 fiscal year-end spike) is confirmed, test whether splitting clusters")
    print("also concentrate in Q4 — consistent with budget-pressure and threshold-evasion compounding.")


if __name__ == "__main__":
    main()
