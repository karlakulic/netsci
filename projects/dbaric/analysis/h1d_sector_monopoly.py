"""
H1d — Sector-level monopoly/duopoly (C1/C2)
Bipartite configuration model null via stub-matching; Bonferroni correction.
"""

HYPOTHESIS_ID        = "H1d"
HYPOTHESIS_STATEMENT = "Specific procurement sectors are structurally dominated by one or two companies beyond their market volume"
GRAPH_FORM           = "bipartite multigraph (IsUponFA=false; same as H1; sensitivity check with call-offs)"
NULL_MODEL           = "bipartite configuration model; C1 and C2 per CPV sector in each null instance"
DATA_CONSTRAINT      = "sector minimum ≥ 5 distinct contractors; Bonferroni correction α* = 0.05/n_testable_sectors; H1 must resolve (either direction) before interpretation"

import random
import textwrap

import numpy as np
import pandas as pd

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
MIN_CONTRACTORS = 5
EFFECT_THRESHOLD_C1 = 0.05
EFFECT_THRESHOLD_C2 = 0.05


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


def concentration_ratios(df_sector):
    contractor_vals = df_sector.groupby("ContractorIdentificationNumber")["TotalValue"].sum()
    total = contractor_vals.sum()
    if total == 0:
        return 0.0, 0.0
    sorted_vals = contractor_vals.sort_values(ascending=False)
    c1 = sorted_vals.iloc[0] / total
    c2 = sorted_vals.iloc[:2].sum() / total if len(sorted_vals) >= 2 else c1
    return float(c1), float(c2)


def null_sector_ratios(df, testable_sectors, n=NULL_ITERATIONS):
    null_results = {s: {"C1": [], "C2": []} for s in testable_sectors}
    contractors = df["ContractorIdentificationNumber"].tolist()
    for _ in range(n):
        shuffled = contractors.copy()
        random.shuffle(shuffled)
        null_df = df.copy()
        null_df["ContractorIdentificationNumber"] = shuffled
        for sector in testable_sectors:
            sector_df = null_df[null_df["cpv_division"] == sector]
            c1, c2 = concentration_ratios(sector_df)
            null_results[sector]["C1"].append(c1)
            null_results[sector]["C2"].append(c2)
    return null_results


def run_analysis(df, label="PRIMARY (call-offs excluded)"):
    sectors = df["cpv_division"].dropna().unique()

    sector_info = {}
    for sector in sectors:
        grp = df[df["cpv_division"] == sector]
        n_con = grp["ContractorIdentificationNumber"].nunique()
        sector_info[sector] = n_con

    testable_sectors = sorted(s for s, n in sector_info.items() if n >= MIN_CONTRACTORS)
    thin_sectors = sorted(s for s, n in sector_info.items() if n < MIN_CONTRACTORS)
    n_testable = len(testable_sectors)

    if n_testable == 0:
        print("  No testable sectors — skip")
        return

    alpha_corrected = ALPHA / n_testable
    print(f"\n=== {label} ===\n")
    print(f"  Sectors total          : {len(sectors)}")
    print(f"  Testable (≥{MIN_CONTRACTORS} contractors) : {n_testable}")
    print(f"  Structurally thin      : {len(thin_sectors)}")
    print(f"  Bonferroni α*          : {alpha_corrected:.5f}  (= {ALPHA}/{n_testable})")
    print()

    print("  Computing null ensemble (500 shuffles × all testable sectors) ...")
    null_results = null_sector_ratios(df, testable_sectors, n=NULL_ITERATIONS)

    obs_c1 = {}
    obs_c2 = {}
    for sector in testable_sectors:
        c1, c2 = concentration_ratios(df[df["cpv_division"] == sector])
        obs_c1[sector] = c1
        obs_c2[sector] = c2

    header = (
        f"{'Sector':<8}  {'nCon':>4}  "
        f"{'ObsC1':>6}  {'NMedC1':>6}  {'N95C1':>6}  {'ExcC1':>7}  {'pC1':>6}  "
        f"{'ObsC2':>6}  {'NMedC2':>6}  {'N95C2':>6}  {'ExcC2':>7}  {'pC2':>6}  "
        f"{'Verdict'}"
    )
    print(f"\n  {header}")
    print("  " + "-" * (len(header) + 2))

    monopoly_sectors = []
    duopoly_sectors = []
    confirmed_sectors = []

    for sector in testable_sectors:
        null_c1 = np.array(null_results[sector]["C1"])
        null_c2 = np.array(null_results[sector]["C2"])
        n_con = sector_info[sector]

        oc1 = obs_c1[sector]
        oc2 = obs_c2[sector]

        med_c1 = float(np.median(null_c1))
        p95_c1 = float(np.percentile(null_c1, 95))
        exc_c1 = oc1 - med_c1
        p_c1 = (np.sum(null_c1 >= oc1) + 1) / (len(null_c1) + 1)

        med_c2 = float(np.median(null_c2))
        p95_c2 = float(np.percentile(null_c2, 95))
        exc_c2 = oc2 - med_c2
        p_c2 = (np.sum(null_c2 >= oc2) + 1) / (len(null_c2) + 1)

        c1_sig = p_c1 <= alpha_corrected and exc_c1 >= EFFECT_THRESHOLD_C1
        c2_sig = p_c2 <= alpha_corrected and exc_c2 >= EFFECT_THRESHOLD_C2

        if c1_sig and c2_sig:
            verdict = "MONOPOLY+DUOPOLY"
            monopoly_sectors.append(sector)
            confirmed_sectors.append(sector)
        elif c1_sig:
            verdict = "MONOPOLY"
            monopoly_sectors.append(sector)
            confirmed_sectors.append(sector)
        elif c2_sig:
            verdict = "DUOPOLY"
            duopoly_sectors.append(sector)
            confirmed_sectors.append(sector)
        elif p_c1 <= ALPHA or p_c2 <= ALPHA:
            verdict = "SIG/UNCORR"
        else:
            verdict = "FAIL"

        row = (
            f"  CPV {sector:<4}  {n_con:>4}  "
            f"{oc1:>6.4f}  {med_c1:>6.4f}  {p95_c1:>6.4f}  {exc_c1:>+7.4f}  {p_c1:>6.4f}  "
            f"{oc2:>6.4f}  {med_c2:>6.4f}  {p95_c2:>6.4f}  {exc_c2:>+7.4f}  {p_c2:>6.4f}  "
            f"{verdict}"
        )
        print(row)

    print()
    print(f"  === SUMMARY ({label}) ===")
    print(f"  Testable sectors        : {n_testable}")
    print(f"  Bonferroni α*           : {alpha_corrected:.5f}")
    print(f"  Monopoly (C1 sig)       : {len(monopoly_sectors)}  — {monopoly_sectors if monopoly_sectors else 'none'}")
    print(f"  Duopoly (C2 sig, C1 not): {len(duopoly_sectors)}  — {duopoly_sectors if duopoly_sectors else 'none'}")
    print(f"  Total sectors confirmed : {len(confirmed_sectors)}")
    if thin_sectors:
        print(f"  Structurally thin (not tested): {thin_sectors}")
    print()


def main():
    print("H1d parent dependency: H1 must have resolved before interpreting these results. "
          "If H1 confirmed: H1d identifies which sectors drive aggregate concentration. "
          "If H1 rejected: H1d tests whether sector-level monopoly/duopoly exists where aggregate Gini is within null.")
    print()

    df_full, df = load_data(include_calloffs=False)
    print_header(df_full, df)

    run_analysis(df, label="PRIMARY (call-offs excluded)")

    print("=== SENSITIVITY CHECK (call-offs included) ===\n")
    _, df_sens = load_data(include_calloffs=True)
    print(f"  Sensitivity subset rows: {len(df_sens):,}\n")
    run_analysis(df_sens, label="SENSITIVITY (call-offs included)")


if __name__ == "__main__":
    main()
