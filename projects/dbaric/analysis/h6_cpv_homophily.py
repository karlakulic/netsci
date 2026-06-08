# ---------------------------------------------------------------------------
# Pre-flight spec — must match docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H6"
HYPOTHESIS_STATEMENT = "Contractor–contract sector alignment deviates from degree-sequence expectation: either specialisation dominates, or relationships override it"
GRAPH_FORM           = "bipartite multigraph"
NULL_MODEL           = "bipartite configuration model; CPV stays with contract edge in each null instance"
DATA_CONSTRAINT      = "restrict to domestic contractors with ≥ 3 contracts; modal 2-digit CPV prefix (tie-break by TotalValue)"
# ---------------------------------------------------------------------------

import sys
import textwrap
import random
import numpy as np
import pandas as pd

DATA_PATH        = "data/contracts_clean.csv"
NULL_ITERATIONS  = 500
ALPHA            = 0.05
EFFECT_THRESHOLD = 0.05
MIN_CONTRACTS    = 3
HIGH_SPEC_THRESH = 0.70


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
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
        & df["is_foreign_contractor"].eq(False)
    )
    return df, df[mask].copy()


def primary_cpv_division(df, min_contracts=MIN_CONTRACTS):
    # Per contractor: modal cpv_division by count, tie-break by sum TotalValue.
    # Computed once across the full post-cleaning analysis subset.
    counts = (
        df.groupby(["ContractorIdentificationNumber", "cpv_division"])
        .agg(n_contracts=("Id", "count"), total_value=("TotalValue", "sum"))
        .reset_index()
    )
    # Keep only contractors meeting minimum contract count across ALL their cpv_divisions
    contractor_totals = counts.groupby("ContractorIdentificationNumber")["n_contracts"].sum()
    eligible = contractor_totals[contractor_totals >= min_contracts].index
    counts   = counts[counts["ContractorIdentificationNumber"].isin(eligible)]

    # Sort so the modal CPV (most contracts, then highest value) is first
    counts = counts.sort_values(
        ["ContractorIdentificationNumber", "n_contracts", "total_value"],
        ascending=[True, False, False],
    )
    primary = counts.groupby("ContractorIdentificationNumber")["cpv_division"].first()
    return primary.to_dict()


def high_specialisation_contractors(df, primary_cpv_map, threshold=HIGH_SPEC_THRESH):
    # Contractors where ≥ threshold fraction of contracts are in their primary CPV division.
    eligible = df[df["ContractorIdentificationNumber"].isin(primary_cpv_map)].copy()
    eligible["primary_cpv"] = eligible["ContractorIdentificationNumber"].map(primary_cpv_map)
    eligible["is_match"] = eligible["cpv_division"] == eligible["primary_cpv"]
    spec = eligible.groupby("ContractorIdentificationNumber")["is_match"].mean()
    return set(spec[spec >= threshold].index)


def cpv_match_fraction(df, primary_cpv_map):
    # Fraction of eligible edges where contractor primary CPV == contract cpv_division.
    eligible = df[df["ContractorIdentificationNumber"].isin(primary_cpv_map)].copy()
    if eligible.empty:
        return np.nan
    eligible["primary_cpv"] = eligible["ContractorIdentificationNumber"].map(primary_cpv_map)
    matches = (eligible["cpv_division"] == eligible["primary_cpv"]).sum()
    return matches / len(eligible)


def null_cpv_fractions(df, primary_cpv_map, n=NULL_ITERATIONS):
    # Stub-matching shuffle; CPV stays with the contract row; recompute match fraction.
    # primary_cpv_map is fixed (from original data); contractor column is shuffled.
    eligible = df[df["ContractorIdentificationNumber"].isin(primary_cpv_map)].copy()
    if eligible.empty:
        return []
    contractor_col = eligible["ContractorIdentificationNumber"].tolist()
    cpv_col        = eligible["cpv_division"].tolist()

    results = []
    for _ in range(n):
        shuffled = contractor_col.copy()
        random.shuffle(shuffled)
        primary_cpvs = [primary_cpv_map.get(c) for c in shuffled]
        matches = sum(p == c for p, c in zip(primary_cpvs, cpv_col) if p is not None)
        total   = sum(1 for c in shuffled if c in primary_cpv_map)
        results.append(matches / total if total > 0 else np.nan)
    return [r for r in results if not np.isnan(r)]


def report(label, observed, null_values):
    null_arr    = np.array(null_values)
    null_median = float(np.median(null_arr))
    null_p2_5   = float(np.percentile(null_arr, 2.5))
    null_p97_5  = float(np.percentile(null_arr, 97.5))
    excess      = observed - null_median

    # Two-tailed p-value
    p_value = (
        min(
            np.sum(null_arr >= observed),
            np.sum(null_arr <= observed),
        ) * 2 + 1
    ) / (len(null_arr) + 1)

    direction = "above null (specialisation)" if observed > null_median else "below null (relational override)"

    print(f"  Null median     : {null_median:.4f}")
    print(f"  Null 2.5th %    : {null_p2_5:.4f}")
    print(f"  Null 97.5th %   : {null_p97_5:.4f}")
    print(f"  Observed        : {observed:.4f}")
    print(f"  Excess          : {excess:+.4f}  ({direction})")
    print(f"  p-value         : {p_value:.4f}  (two-tailed, n={len(null_values)} iterations)")
    outside_interval = observed < null_p2_5 or observed > null_p97_5
    if outside_interval and abs(excess) >= EFFECT_THRESHOLD:
        print(f"  RESULT [{label}]: reject null — effect above threshold — {direction}")
    elif outside_interval:
        print(f"  RESULT [{label}]: reject null — excess below effect threshold")
    else:
        print(f"  RESULT [{label}]: fail to reject null")
    print()


def main():
    df_full, df = load_data()
    print_header(df_full, df)

    print("Computing primary CPV division per contractor …")
    primary_cpv_map = primary_cpv_division(df, min_contracts=MIN_CONTRACTS)
    n_eligible_contractors = len(primary_cpv_map)
    n_eligible_edges = df["ContractorIdentificationNumber"].isin(primary_cpv_map).sum()
    print(f"Eligible contractors (≥{MIN_CONTRACTS} contracts): {n_eligible_contractors:,}")
    print(f"Eligible edges in analysis subset     : {n_eligible_edges:,}\n")

    # High-specialisation subset
    high_spec_set = high_specialisation_contractors(df, primary_cpv_map)
    print(f"High-specialisation contractors (≥{HIGH_SPEC_THRESH:.0%} in modal CPV): {len(high_spec_set):,}\n")

    # Observed match fractions
    obs_full = cpv_match_fraction(df, primary_cpv_map)
    high_spec_map = {k: v for k, v in primary_cpv_map.items() if k in high_spec_set}
    obs_highspec  = cpv_match_fraction(df, high_spec_map)

    print(f"Observed CPV match fraction — full eligible set : {obs_full:.4f}")
    print(f"Observed CPV match fraction — high-spec subset : {obs_highspec:.4f}\n")

    # Null ensembles
    print(f"Running null ensemble — full eligible set ({NULL_ITERATIONS} iterations) …")
    null_full = null_cpv_fractions(df, primary_cpv_map, n=NULL_ITERATIONS)

    print(f"Running null ensemble — high-spec subset ({NULL_ITERATIONS} iterations) …")
    null_highspec = null_cpv_fractions(df, high_spec_map, n=NULL_ITERATIONS)

    print("\n=== Full eligible set (contractors with ≥ 3 contracts) ===")
    report("full", obs_full, null_full)

    print("=== Stability check — high-specialisation contractors (≥ 70% in modal CPV) ===")
    report("high_spec", obs_highspec, null_highspec)


if __name__ == "__main__":
    main()
