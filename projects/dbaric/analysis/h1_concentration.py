"""
H1 — Contractor strength concentration
Bipartite configuration model null via stub-matching (degree-preserving).
"""

HYPOTHESIS_ID        = "H1"
HYPOTHESIS_STATEMENT = "A small number of contractors captures a disproportionate share of public contract value"
GRAPH_FORM           = "bipartite multigraph (IsUponFA=false only; sensitivity check with call-offs)"
NULL_MODEL           = "degree-preserving rewiring of the bipartite CA–contractor graph (bipartite configuration model)"
DATA_CONSTRAINT      = "exclude foreign contractors from strength metrics; test within CPV sector"

import random
import sys
import textwrap

import numpy as np
import pandas as pd

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
EFFECT_THRESHOLD_GINI = 0.05
EFFECT_THRESHOLD_HHI = 0.05
MIN_CONTRACTORS_PER_SECTOR = 10


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


def gini(values):
    """Standard Gini coefficient on a 1-D array of non-negative values."""
    arr = np.array(values, dtype=float)
    arr = arr[arr > 0]
    n = len(arr)
    if n == 0:
        return 0.0
    arr = np.sort(arr)
    ranks = np.arange(1, n + 1)
    return (2 * np.sum(ranks * arr) / (n * np.sum(arr))) - (n + 1) / n


def contractor_strength(df):
    """Sum TotalValue per contractor; return Series indexed by contractor OIB."""
    return df.groupby("ContractorIdentificationNumber")["TotalValue"].sum()


def contractor_hhi(df):
    """
    Mean Y_i = Σ_j (w_ij / s_i)² per contractor.
    w_ij = total value from contractor i to CA j; s_i = total contractor strength.
    """
    pair_weight = (
        df.groupby(["ContractorIdentificationNumber", "CAIdentificationNumber"])["TotalValue"]
        .sum()
        .reset_index()
    )
    strength = pair_weight.groupby("ContractorIdentificationNumber")["TotalValue"].sum()
    pair_weight = pair_weight.join(strength.rename("s_i"), on="ContractorIdentificationNumber")
    pair_weight["share_sq"] = (pair_weight["TotalValue"] / pair_weight["s_i"]) ** 2
    hhi_per = pair_weight.groupby("ContractorIdentificationNumber")["share_sq"].sum()
    return float(hhi_per.mean())


def bipartite_config_null(df, n=NULL_ITERATIONS):
    """
    Stub-matching null: shuffle contractor stubs while preserving both degree sequences.
    Each CA appears the same number of times (CA stubs unchanged).
    Each contractor appears the same number of times (contractor stubs shuffled but same multiset).
    Returns list of (gini_val, hhi_val) tuples.
    """
    ca_stubs = df["CAIdentificationNumber"].tolist()
    contractor_stubs = df["ContractorIdentificationNumber"].tolist()
    weights = df["TotalValue"].tolist()
    results = []
    for _ in range(n):
        shuffled = random.sample(contractor_stubs, len(contractor_stubs))
        null_df = pd.DataFrame({
            "CAIdentificationNumber": ca_stubs,
            "ContractorIdentificationNumber": shuffled,
            "TotalValue": weights,
        })
        g = gini(null_df.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values)
        h = contractor_hhi(null_df)
        results.append((g, h))
    return results


def report_metric(label, observed, null_values, effect_threshold):
    null_arr = np.array(null_values)
    null_median = float(np.median(null_arr))
    null_p95 = float(np.percentile(null_arr, 95))
    excess = observed - null_median
    p_value = (np.sum(null_arr >= observed) + 1) / (len(null_arr) + 1)

    print(f"  {label}")
    print(f"    Null median : {null_median:.4f}")
    print(f"    Null 95th % : {null_p95:.4f}")
    print(f"    Observed    : {observed:.4f}")
    print(f"    Excess      : {excess:+.4f}")
    print(f"    p-value     : {p_value:.4f}  (one-tailed, n={len(null_arr)} iterations)")
    if p_value <= ALPHA and abs(excess) >= effect_threshold:
        verdict = "REJECT NULL — effect above threshold"
    elif p_value <= ALPHA:
        verdict = "REJECT NULL — but excess below effect threshold (significant, not substantive)"
    else:
        verdict = "FAIL TO REJECT NULL"
    print(f"    Result      : {verdict}")
    print()


def run_analysis(df, label="AGGREGATE", n_null=NULL_ITERATIONS):
    if len(df) == 0:
        print(f"  {label}: no data — skip")
        return

    obs_gini = gini(contractor_strength(df).values)
    obs_hhi = contractor_hhi(df)

    null_results = bipartite_config_null(df, n=n_null)
    null_ginis = [r[0] for r in null_results]
    null_hhis = [r[1] for r in null_results]

    print(f"--- {label} (n_contracts={len(df):,}, "
          f"n_contractors={df['ContractorIdentificationNumber'].nunique():,}) ---")
    report_metric("Gini (contractor strength)", obs_gini, null_ginis, EFFECT_THRESHOLD_GINI)
    report_metric("Mean contractor HHI (Y_i)", obs_hhi, null_hhis, EFFECT_THRESHOLD_HHI)


def main():
    df_full, df = load_data(include_calloffs=False)
    print_header(df_full, df)

    print("\n=== PRIMARY ANALYSIS (IsUponFA=False) ===\n")
    run_analysis(df, label="AGGREGATE")

    print("\n=== PER-CPV-SECTOR (≥10 domestic contractors) ===\n")
    for sector, grp in df.groupby("cpv_division"):
        n_con = grp["ContractorIdentificationNumber"].nunique()
        if n_con >= MIN_CONTRACTORS_PER_SECTOR:
            run_analysis(grp, label=f"CPV {sector}")

    print("\n=== SENSITIVITY CHECK (IsUponFA=True included) ===\n")
    _, df_sens = load_data(include_calloffs=True)
    print(f"(sensitivity subset rows: {len(df_sens):,})\n")
    run_analysis(df_sens, label="AGGREGATE (incl. call-offs)")


if __name__ == "__main__":
    main()
