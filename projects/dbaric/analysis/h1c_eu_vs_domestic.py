"""
H1c — EU co-financing requirements reduce vendor concentration relative to domestic procurement
Funding-label permutation null within CPV sector.
"""

HYPOTHESIS_ID        = "H1c"
HYPOTHESIS_STATEMENT = "EU co-financing requirements reduce vendor concentration relative to domestic procurement"
GRAPH_FORM           = "bipartite multigraph (separate EU-funded and domestic subgraphs per CPV sector)"
NULL_MODEL           = "funding-type label permutation (shuffle ContractEUFinanc labels within CPV sector; compute Gini_domestic - Gini_EU)"
DATA_CONSTRAINT      = "parent dependency: H1 must confirm (reject null) before this is interpretable; EU subgraph requires ≥ 5 distinct contractors per CPV sector"

import random
import textwrap

import numpy as np
import pandas as pd

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
MIN_EU_CONTRACTORS = 5
EFFECT_THRESHOLD_DELTA = 0.05


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


def gini(values):
    values = np.array(values, dtype=float)
    values = values[values > 0]
    if len(values) == 0:
        return 0.0
    values = np.sort(values)
    n = len(values)
    idx = np.arange(1, n + 1)
    return (2 * np.sum(idx * values) / (n * np.sum(values))) - (n + 1) / n


def observed_delta(df_sector):
    eu_flag = df_sector["ContractEUFinanc"].fillna(False).astype(bool)
    domestic = df_sector[~eu_flag]
    eu = df_sector[eu_flag]
    dom_strength = domestic.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values
    eu_strength = eu.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values
    return gini(dom_strength) - gini(eu_strength), dom_strength, eu_strength


def funding_label_permutation_null(df_sector, n=NULL_ITERATIONS):
    eu_flags = df_sector["ContractEUFinanc"].fillna(False).astype(bool).tolist()
    results = []
    for _ in range(n):
        shuffled = eu_flags.copy()
        random.shuffle(shuffled)
        null_df = df_sector.copy()
        null_df["ContractEUFinanc"] = shuffled
        domestic = null_df[~null_df["ContractEUFinanc"]]
        eu = null_df[null_df["ContractEUFinanc"]]
        dom_strength = domestic.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values
        eu_strength = eu.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values
        if len(dom_strength) < 2 or len(eu_strength) < MIN_EU_CONTRACTORS:
            results.append(0.0)
            continue
        results.append(gini(dom_strength) - gini(eu_strength))
    return results


def main():
    print("H1c parent dependency: H1 must have CONFIRMED (rejected null) before these results are "
          "interpretable. Run h1_concentration.py first.")
    print()

    df_full, df = load_data()
    df["ContractEUFinanc"] = df["ContractEUFinanc"].fillna(False).astype(bool)
    print_header(df_full, df)

    sectors = df["cpv_division"].dropna().unique()
    testable = []
    underpowered = []
    skipped = []

    for sector in sorted(sectors):
        df_sector = df[df["cpv_division"] == sector]
        eu_flag = df_sector["ContractEUFinanc"]
        domestic = df_sector[~eu_flag]
        eu = df_sector[eu_flag]
        n_dom_con = domestic["ContractorIdentificationNumber"].nunique()
        n_eu_con = eu["ContractorIdentificationNumber"].nunique()
        if n_eu_con < MIN_EU_CONTRACTORS:
            underpowered.append((sector, n_dom_con, n_eu_con))
        elif n_dom_con < 5:
            skipped.append((sector, n_dom_con, n_eu_con))
        else:
            testable.append(sector)

    print(f"\nSectors total          : {len(sectors)}")
    print(f"Testable (≥5 each)     : {len(testable)}")
    print(f"Underpowered EU < 5    : {len(underpowered)}")
    print(f"Skipped domestic < 5   : {len(skipped)}")
    print()

    confirmed = 0
    print("=== PER-SECTOR RESULTS ===\n")
    print(f"{'Sector':<8}  {'Dom-G':>6}  {'EU-G':>6}  {'Obs-δ':>7}  "
          f"{'NullMed':>7}  {'Null95':>7}  {'Excess':>7}  {'p':>6}  {'Result'}")
    print("-" * 88)

    for sector in testable:
        df_sector = df[df["cpv_division"] == sector].copy()
        obs_delta, dom_strength, eu_strength = observed_delta(df_sector)
        null_values = funding_label_permutation_null(df_sector, n=NULL_ITERATIONS)
        null_arr = np.array(null_values)
        null_median = float(np.median(null_arr))
        null_p95 = float(np.percentile(null_arr, 95))
        excess = obs_delta - null_median
        p_value = (np.sum(null_arr >= obs_delta) + 1) / (len(null_arr) + 1)

        dom_g = gini(dom_strength)
        eu_g = gini(eu_strength)

        if p_value <= ALPHA and excess >= EFFECT_THRESHOLD_DELTA:
            verdict = "CONFIRM"
            confirmed += 1
        elif p_value <= ALPHA:
            verdict = "SIG/SMALL"
        else:
            verdict = "FAIL"

        print(f"CPV {sector:<4}  {dom_g:>6.4f}  {eu_g:>6.4f}  {obs_delta:>+7.4f}  "
              f"{null_median:>7.4f}  {null_p95:>7.4f}  {excess:>+7.4f}  {p_value:>6.4f}  {verdict}")

    print()
    print(f"=== SUMMARY ===")
    print(f"  Testable sectors    : {len(testable)}")
    print(f"  Confirmed (p≤{ALPHA}, δ≥{EFFECT_THRESHOLD_DELTA}) : {confirmed}")
    print(f"  Confirmation rate   : {confirmed / len(testable):.1%}" if testable else "  Confirmation rate   : N/A")
    print()
    if underpowered:
        print(f"  Underpowered sectors (EU contractors < {MIN_EU_CONTRACTORS}):")
        for s, nd, ne in underpowered:
            print(f"    CPV {s}: domestic={nd}, EU={ne}")
    print()


if __name__ == "__main__":
    main()
