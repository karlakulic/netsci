"""
H3 — Fiscal year-end graph density spike.
Both 2024 and 2025 must independently exceed the effect threshold for the hypothesis to be supported.
"""

HYPOTHESIS_ID        = "H3"
HYPOTHESIS_STATEMENT = "Contract formation surges at fiscal year-end at rates consistent with budget-pressure spending, not procurement need"
GRAPH_FORM           = "bipartite multigraph (new vs repeat edge classification by ContractDate)"
NULL_MODEL           = "stationary Poisson process (expected quarterly count = annual_total / 4); secondary: funding-type label permutation"
DATA_CONSTRAINT      = "only two complete fiscal years (2024, 2025); both must independently confirm"

import random
import textwrap

import numpy as np
import pandas as pd
from scipy import stats

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
EFFECT_THRESHOLD_RATIO = 1.5


def print_header(df_full, df_analysis):
    foreign_n = df_full["is_foreign_contractor"].sum()
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
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
    )
    return df, df[mask].copy()


def classify_edges(df):
    """
    Globally sort by ContractDate; for each (CA, contractor) pair, the first
    occurrence across the full dataset is 'new'; all subsequent are 'repeat'.
    Returns df with edge_type column added.
    """
    df = df.copy()
    df["ContractDate"] = pd.to_datetime(df["ContractDate"], errors="coerce")
    df = df.sort_values("ContractDate")
    pair_seen = set()
    edge_types = []
    for ca, contractor in zip(df["CAIdentificationNumber"], df["ContractorIdentificationNumber"]):
        pair = (ca, contractor)
        if pair in pair_seen:
            edge_types.append("repeat")
        else:
            pair_seen.add(pair)
            edge_types.append("new")
    df["edge_type"] = edge_types
    return df


def quarterly_counts(df, year):
    """
    For a given fiscal year, return dicts of quarterly contract counts and total values.
    Returns ({Q: count}, {Q: total_value}) for Q in 1..4.
    """
    yr_df = df[df["contract_year"] == year].copy()
    counts = {}
    values = {}
    for q in [1, 2, 3, 4]:
        subset = yr_df[yr_df["contract_quarter"] == q]
        counts[q] = len(subset)
        values[q] = float(subset["TotalValue"].sum())
    return counts, values


def poisson_spike_test(q4_count, annual_total):
    """
    One-tailed Poisson test: H0 = stationary process with rate annual_total / 4.
    Returns (p_value, ratio).
    ratio = q4_count / (annual_total / 4).
    """
    mu = annual_total / 4.0
    if mu <= 0:
        return np.nan, np.nan
    # P(X >= q4_count) under Poisson(mu)
    p_value = 1.0 - stats.poisson.cdf(q4_count - 1, mu)
    ratio = q4_count / mu
    return float(p_value), float(ratio)


def funding_split_test(df, year, n=NULL_ITERATIONS):
    """
    Permute ContractEUFinanc labels within the year; recompute Q4 spike ratio
    for domestic vs EU-funded; compute null distribution of (ratio_domestic - ratio_eu).
    Two-tailed test at α=0.05.
    Returns observed_delta, null distribution list, p_value.
    """
    yr_df = df[df["contract_year"] == year].copy()

    def q4_ratio(sub_df):
        if len(sub_df) == 0:
            return np.nan
        q4 = len(sub_df[sub_df["contract_quarter"] == 4])
        annual = len(sub_df)
        return q4 / (annual / 4.0)

    eu_labels = yr_df["ContractEUFinanc"].tolist()
    obs_domestic_ratio = q4_ratio(yr_df[yr_df["ContractEUFinanc"].eq(False)])
    obs_eu_ratio = q4_ratio(yr_df[yr_df["ContractEUFinanc"].eq(True)])

    if np.isnan(obs_domestic_ratio) or np.isnan(obs_eu_ratio):
        return np.nan, [], np.nan

    obs_delta = obs_domestic_ratio - obs_eu_ratio

    null_deltas = []
    for _ in range(n):
        shuffled = random.sample(eu_labels, len(eu_labels))
        perm_df = yr_df.copy()
        perm_df["ContractEUFinanc"] = shuffled
        r_dom = q4_ratio(perm_df[perm_df["ContractEUFinanc"].eq(False)])
        r_eu = q4_ratio(perm_df[perm_df["ContractEUFinanc"].eq(True)])
        if not np.isnan(r_dom) and not np.isnan(r_eu):
            null_deltas.append(r_dom - r_eu)

    if len(null_deltas) == 0:
        return obs_delta, [], np.nan

    null_arr = np.array(null_deltas)
    # Two-tailed: fraction outside [2.5th, 97.5th]
    lo = np.percentile(null_arr, 2.5)
    hi = np.percentile(null_arr, 97.5)
    p_value = float(np.mean((null_arr <= obs_delta) | (null_arr >= obs_delta)))
    # Correct two-tailed p: proportion of null at least as extreme in absolute deviation
    p_value = float(np.mean(np.abs(null_arr - np.median(null_arr)) >= abs(obs_delta - np.median(null_arr))))

    return obs_delta, null_deltas, p_value


def report_year(df, year):
    print(f"\n{'='*60}")
    print(f"FISCAL YEAR {year}")
    print(f"{'='*60}")

    yr_df = df[df["contract_year"] == year]
    if len(yr_df) == 0:
        print(f"  No data for {year} — skip")
        return

    # New/repeat classification is computed globally before this call
    all_counts, all_values = quarterly_counts(yr_df, year)
    new_df = yr_df[yr_df["edge_type"] == "new"]
    repeat_df = yr_df[yr_df["edge_type"] == "repeat"]
    new_counts, new_values = quarterly_counts(new_df, year)
    repeat_counts, repeat_values = quarterly_counts(repeat_df, year)

    print(f"\nQuarterly contract counts (all / new / repeat):")
    print(f"  {'Q':<4} {'All':>8} {'New':>8} {'Repeat':>8} {'Value (M€)':>12}")
    for q in [1, 2, 3, 4]:
        print(f"  {q:<4} {all_counts[q]:>8,} {new_counts[q]:>8,} {repeat_counts[q]:>8,} "
              f"{all_values[q]/1e6:>12.2f}")

    annual_new = sum(new_counts.values())
    annual_all = sum(all_counts.values())
    print(f"\n  Annual new edges  : {annual_new:,}")
    print(f"  Annual all edges  : {annual_all:,}")

    print(f"\nPrimary test — Poisson spike (new edges):")
    p_val, ratio = poisson_spike_test(new_counts[4], annual_new)
    expected_q = annual_new / 4.0
    print(f"  Null: Poisson(μ={expected_q:.1f}) per quarter (annual/4)")
    print(f"  Q4 new-edge count   : {new_counts[4]:,}")
    print(f"  Q4-to-quarterly-mean ratio : {ratio:.3f}")
    print(f"  p-value (one-tailed)       : {p_val:.4f}")

    stat_sig = p_val <= ALPHA
    effect_met = ratio >= EFFECT_THRESHOLD_RATIO
    if stat_sig and effect_met:
        print(f"  Result : REJECT NULL — ratio {ratio:.2f} ≥ {EFFECT_THRESHOLD_RATIO} and p={p_val:.4f} ≤ {ALPHA}")
    elif stat_sig:
        print(f"  Result : REJECT NULL — significant but ratio {ratio:.2f} < {EFFECT_THRESHOLD_RATIO} (below effect threshold)")
    else:
        print(f"  Result : FAIL TO REJECT NULL")

    print(f"\nQ4 value spike (all edges):")
    q4_value = all_values[4]
    mean_q_value = sum(all_values.values()) / 4.0
    value_ratio = q4_value / mean_q_value if mean_q_value > 0 else np.nan
    print(f"  Q4 total value          : {q4_value/1e6:.2f} M€")
    print(f"  Quarterly mean value    : {mean_q_value/1e6:.2f} M€")
    print(f"  Q4-to-quarterly ratio   : {value_ratio:.3f}")

    print(f"\nEdge-type dominance in Q4:")
    q4_new = new_counts[4]
    q4_repeat = repeat_counts[4]
    q4_total = q4_new + q4_repeat
    if q4_total > 0:
        print(f"  Q4 new edges    : {q4_new:,} ({100*q4_new/q4_total:.1f}%)")
        print(f"  Q4 repeat edges : {q4_repeat:,} ({100*q4_repeat/q4_total:.1f}%)")
        if q4_new > q4_repeat:
            print("  Dominance : NEW edges dominate Q4 spike")
        else:
            print("  Dominance : REPEAT edges dominate Q4 spike — consistent with risk-aversion / budget-pressure")

    print(f"\nSecondary test — funding-type label permutation (n={NULL_ITERATIONS}):")
    obs_delta, null_deltas, p_val_fund = funding_split_test(df, year, n=NULL_ITERATIONS)
    if np.isnan(obs_delta) or len(null_deltas) == 0:
        print("  Insufficient EU-funded data for this test — skip")
    else:
        null_arr = np.array(null_deltas)
        print(f"  Observed Δ(Q4 ratio: domestic − EU) : {obs_delta:+.4f}")
        print(f"  Null median Δ                       : {float(np.median(null_arr)):+.4f}")
        print(f"  Null 2.5th–97.5th pct               : [{np.percentile(null_arr,2.5):+.4f}, {np.percentile(null_arr,97.5):+.4f}]")
        print(f"  p-value (two-tailed)                : {p_val_fund:.4f}")
        if p_val_fund <= ALPHA:
            print("  Result : REJECT NULL — domestic and EU-funded Q4 ratios differ significantly")
        else:
            print("  Result : FAIL TO REJECT NULL — no significant funding-type difference")


def main():
    df_full, df = load_data()
    print_header(df_full, df)

    print("\nClassifying edges as new/repeat globally across full dataset …")
    df = classify_edges(df)
    n_new = (df["edge_type"] == "new").sum()
    n_repeat = (df["edge_type"] == "repeat").sum()
    print(f"  New edges    : {n_new:,}")
    print(f"  Repeat edges : {n_repeat:,}")

    print(
        "\nConstraint: both 2024 and 2025 must independently exceed the effect threshold "
        "(ratio > 1.5 and p < 0.05) for H3 to be supported."
    )

    report_year(df, 2024)
    report_year(df, 2025)

    print("\n=== COMBINED VERDICT ===")
    print(
        "H3 is supported only if BOTH years individually reject the null AND ratio > 1.5. "
        "See per-year results above."
    )


if __name__ == "__main__":
    main()
