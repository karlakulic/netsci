"""
H1a — Single-vendor lock-in at authority level
Bipartite configuration model null via stub-matching.
"""

HYPOTHESIS_ID        = "H1a"
HYPOTHESIS_STATEMENT = "Individual public institutions award the majority of their budget to a single vendor at above-chance rates"
GRAPH_FORM           = "bipartite multigraph (IsUponFA=false; CA nodes with degree ≥ 2)"
NULL_MODEL           = "bipartite configuration model; fraction of CAs with single-vendor spend share > 80% vs null ensemble"
DATA_CONSTRAINT      = "parent dependency: H1 must resolve (either direction) before interpretation; CA degree ≥ 2 required"

import random
import textwrap

import numpy as np
import pandas as pd
from scipy.stats import binom

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
SV_THRESHOLD = 0.80
MIN_DEGREE = 2
EFFECT_THRESHOLD_PP = 0.10
TEMPORAL_EFFECT_THRESHOLD_PP = 0.05


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
        & df["is_foreign_contractor"].eq(False)
    )
    return df, df[mask].copy()


def sv_share(ca_group):
    total = ca_group["TotalValue"].sum()
    if total == 0:
        return 0.0
    max_contractor = ca_group.groupby("ContractorIdentificationNumber")["TotalValue"].sum().max()
    return max_contractor / total


def fraction_above_threshold(df, threshold=SV_THRESHOLD, min_degree=MIN_DEGREE):
    ca_data = (
        df.groupby("CAIdentificationNumber")["ContractorIdentificationNumber"]
        .nunique()
        .reset_index()
        .rename(columns={"ContractorIdentificationNumber": "n_contractors"})
    )
    eligible_cas = ca_data.loc[ca_data["n_contractors"] >= min_degree, "CAIdentificationNumber"]
    eligible_df = df[df["CAIdentificationNumber"].isin(eligible_cas)]
    shares = eligible_df.groupby("CAIdentificationNumber").apply(sv_share)
    return (shares > threshold).mean(), len(shares)


def shuffle_contractors(df):
    contractors = df["ContractorIdentificationNumber"].tolist()
    random.shuffle(contractors)
    null_df = df.copy()
    null_df["ContractorIdentificationNumber"] = contractors
    return null_df


def null_ensemble(df, n=NULL_ITERATIONS):
    results = []
    for _ in range(n):
        null_df = shuffle_contractors(df)
        frac, _ = fraction_above_threshold(null_df)
        results.append(frac)
    return results


def mcnemar_test(flags_2024, flags_2025, common_cas):
    both_true  = sum(1 for c in common_cas if flags_2024[c] and flags_2025[c])
    true_false = sum(1 for c in common_cas if flags_2024[c] and not flags_2025[c])
    false_true = sum(1 for c in common_cas if not flags_2024[c] and flags_2025[c])
    both_false = sum(1 for c in common_cas if not flags_2024[c] and not flags_2025[c])
    n_discordant = true_false + false_true
    if n_discordant == 0:
        return 1.0, false_true, true_false, both_true, both_false
    p_value = float(binom.pmf(range(false_true, n_discordant + 1), n_discordant, 0.5).sum())
    return p_value, false_true, true_false, both_true, both_false


def temporal_analysis(df):
    df_2024 = df[df["contract_year"] == 2024]
    df_2025 = df[df["contract_year"] == 2025]

    def eligible_cas_for_year(df_year):
        ca_data = (
            df_year.groupby("CAIdentificationNumber")["ContractorIdentificationNumber"]
            .nunique()
            .reset_index()
            .rename(columns={"ContractorIdentificationNumber": "n_contractors"})
        )
        return set(ca_data.loc[ca_data["n_contractors"] >= MIN_DEGREE, "CAIdentificationNumber"])

    eligible_2024 = eligible_cas_for_year(df_2024)
    eligible_2025 = eligible_cas_for_year(df_2025)
    common_cas = eligible_2024 & eligible_2025

    if len(common_cas) == 0:
        print("  Temporal McNemar: no CAs with ≥ 2 contractors in both 2024 and 2025 — skip")
        return

    def sv_flags_for_year(df_year, cas):
        sub = df_year[df_year["CAIdentificationNumber"].isin(cas)]
        shares = sub.groupby("CAIdentificationNumber").apply(sv_share)
        return {ca: (shares[ca] > SV_THRESHOLD) for ca in cas if ca in shares.index}

    flags_2024 = sv_flags_for_year(df_2024, common_cas)
    flags_2025 = sv_flags_for_year(df_2025, common_cas)
    matched_cas = set(flags_2024.keys()) & set(flags_2025.keys())

    if len(matched_cas) == 0:
        print("  Temporal McNemar: no matched CA pairs — skip")
        return

    frac_2024 = sum(flags_2024[c] for c in matched_cas) / len(matched_cas)
    frac_2025 = sum(flags_2025[c] for c in matched_cas) / len(matched_cas)
    trend_pp = frac_2025 - frac_2024

    p_value, false_true, true_false, both_true, both_false = mcnemar_test(
        flags_2024, flags_2025, matched_cas
    )

    print(f"  Temporal McNemar (CAs with ≥ {MIN_DEGREE} contractors in both years)")
    print(f"    Matched CA pairs     : {len(matched_cas):,}")
    print(f"    Lock-in 2024         : {frac_2024:.4f}  ({sum(flags_2024[c] for c in matched_cas)} CAs)")
    print(f"    Lock-in 2025         : {frac_2025:.4f}  ({sum(flags_2025[c] for c in matched_cas)} CAs)")
    print(f"    Trend (2025-2024)    : {trend_pp:+.4f} pp")
    print(f"    McNemar table        : TT={both_true}  TF={true_false}  FT={false_true}  FF={both_false}")
    print(f"    p-value (one-tailed) : {p_value:.4f}  (H_a: more gaining lock-in than losing)")
    if p_value <= ALPHA and trend_pp >= TEMPORAL_EFFECT_THRESHOLD_PP:
        verdict = "REJECT NULL — trend above effect threshold"
    elif p_value <= ALPHA:
        verdict = "REJECT NULL — but trend below effect threshold (significant, not substantive)"
    else:
        verdict = "FAIL TO REJECT NULL"
    print(f"    Result               : {verdict}")
    print()


def main():
    print("H1a parent dependency: H1 must have resolved before interpreting these results. "
          "H1 outcome direction: [run h1_concentration.py first]")
    print()

    df_full, df = load_data()
    print_header(df_full, df)

    obs_frac, n_eligible = fraction_above_threshold(df)
    null_values = null_ensemble(df)
    null_arr = np.array(null_values)
    null_median = float(np.median(null_arr))
    null_p95 = float(np.percentile(null_arr, 95))
    excess = obs_frac - null_median
    p_value = (np.sum(null_arr >= obs_frac) + 1) / (len(null_arr) + 1)

    print(f"\n=== PRIMARY ANALYSIS — Single-vendor spend share > {SV_THRESHOLD:.0%} ===\n")
    print(f"  Eligible CAs (degree ≥ {MIN_DEGREE}) : {n_eligible:,}")
    print(f"  Null median              : {null_median:.4f}")
    print(f"  Null 95th %              : {null_p95:.4f}")
    print(f"  Observed fraction        : {obs_frac:.4f}")
    print(f"  Excess                   : {excess:+.4f} ({excess * 100:+.1f} pp)")
    print(f"  p-value (one-tailed)     : {p_value:.4f}  (n={len(null_arr)} iterations)")
    if p_value <= ALPHA and excess >= EFFECT_THRESHOLD_PP:
        verdict = "REJECT NULL — effect above threshold"
    elif p_value <= ALPHA:
        verdict = "REJECT NULL — but excess below effect threshold (significant, not substantive)"
    else:
        verdict = "FAIL TO REJECT NULL"
    print(f"  Result                   : {verdict}")
    print()

    print("=== SECONDARY ANALYSIS — Temporal trend (McNemar, 2024 → 2025) ===\n")
    temporal_analysis(df)


if __name__ == "__main__":
    main()
