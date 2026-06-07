"""
H4 — CA–contractor pair reconnection rate.
Null: Chung-Lu bipartite approximation p_ij = (d_i × d_j) / |E_2025|.
"""

HYPOTHESIS_ID        = "H4"
HYPOTHESIS_STATEMENT = "Prior CA–contractor relationships independently predict future award allocation beyond market volume"
GRAPH_FORM           = "bipartite multigraph (annual subgraphs by ContractDate year)"
NULL_MODEL           = "Chung-Lu approximation p_ij = (d_i × d_j) / |E_2025| (bipartite normalisation)"
DATA_CONSTRAINT      = "single 2024→2025 transition only; exclude re-publications (same ContractNo and ContractDate within 30 days)"

import textwrap

import numpy as np
import pandas as pd
from scipy import stats

DATA_PATH = "data/contracts_clean.csv"
ALPHA = 0.05
Z_THRESHOLD = 1.645
EFFECT_THRESHOLD_RATE = 0.10
MIN_CONTRACTORS_PER_SECTOR = 5


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


def annual_pairs(df, year):
    """Return set of (CA, contractor) tuples active in the given ContractDate year."""
    yr_df = df[df["contract_year"] == year]
    return set(
        zip(yr_df["CAIdentificationNumber"], yr_df["ContractorIdentificationNumber"])
    )


def exclude_republications(df2024, df2025):
    """
    Remove from df2025 any contract that is a re-publication of a df2024 contract:
    - same Id (already handled by deduplication in prepare_data.py, but guard here)
    - same ContractNo AND ContractDate within 30 days of a 2024 contract with the same ContractNo
    Returns cleaned df2025.
    """
    df2024 = df2024.copy()
    df2025 = df2025.copy()
    df2024["ContractDate"] = pd.to_datetime(df2024["ContractDate"], errors="coerce")
    df2025["ContractDate"] = pd.to_datetime(df2025["ContractDate"], errors="coerce")

    # Index 2024 ContractNo → set of dates
    cn_to_dates_2024 = (
        df2024.dropna(subset=["ContractNo", "ContractDate"])
        .groupby("ContractNo")["ContractDate"]
        .apply(set)
        .to_dict()
    )

    def is_repub(row):
        cn = row["ContractNo"]
        dt = row["ContractDate"]
        if pd.isna(cn) or pd.isna(dt):
            return False
        dates_2024 = cn_to_dates_2024.get(cn, set())
        for d24 in dates_2024:
            if abs((dt - d24).days) <= 30:
                return True
        return False

    repub_mask = df2025.apply(is_repub, axis=1)
    n_removed = repub_mask.sum()
    print(f"  Re-publications excluded from 2025 subset: {n_removed:,}")
    return df2025[~repub_mask]


def chung_lu_expected(pairs_2024, df2025):
    """
    For each eligible 2024 pair (CA_i, contractor_j), compute:
      p_ij = (d_i × d_j) / |E_2025|
    where d_i = 2025 degree of CA_i, d_j = 2025 degree of contractor_j,
    |E_2025| = total 2025 edge count (bipartite normalisation: m, not 2m).

    Returns (expected_reconnection_count, variance, per_pair_p list, eligible_pairs list).
    Only pairs where both nodes appear in 2025 are included.
    """
    ca_degree_2025 = (
        df2025.groupby("CAIdentificationNumber")
        .size()
        .to_dict()
    )
    con_degree_2025 = (
        df2025.groupby("ContractorIdentificationNumber")
        .size()
        .to_dict()
    )
    E_2025 = len(df2025)

    eligible = []
    p_vals = []
    for ca, con in pairs_2024:
        d_i = ca_degree_2025.get(ca, 0)
        d_j = con_degree_2025.get(con, 0)
        if d_i == 0 or d_j == 0:
            continue
        p_ij = min((d_i * d_j) / E_2025, 1.0)
        eligible.append((ca, con))
        p_vals.append(p_ij)

    expected = sum(p_vals)
    variance = sum(p * (1 - p) for p in p_vals)
    return expected, variance, p_vals, eligible


def reconnection_ztest(observed, expected, variance):
    """
    z-score = (observed − expected) / sqrt(variance).
    One-tailed p-value: P(Z ≥ z).
    """
    if variance <= 0:
        return np.nan, np.nan
    z = (observed - expected) / np.sqrt(variance)
    p_value = 1.0 - stats.norm.cdf(z)
    return float(z), float(p_value)


def pairs_2025_set(df2025):
    """Set of (CA, contractor) pairs present in 2025."""
    return set(zip(df2025["CAIdentificationNumber"], df2025["ContractorIdentificationNumber"]))


def run_analysis(df, label="AGGREGATE", include_calloffs=False):
    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")

    df2024 = df[df["contract_year"] == 2024].copy()
    df2025_raw = df[df["contract_year"] == 2025].copy()

    print(f"\n  2024 contracts : {len(df2024):,}")
    print(f"  2025 contracts (before re-pub exclusion) : {len(df2025_raw):,}")

    df2025 = exclude_republications(df2024, df2025_raw)
    print(f"  2025 contracts (after re-pub exclusion)  : {len(df2025):,}")

    pairs_24 = annual_pairs(df2024, 2024)
    pairs_25_set = pairs_2025_set(df2025)

    # Nodes active in both years
    ca_active_both = (
        set(df2024["CAIdentificationNumber"]) &
        set(df2025["CAIdentificationNumber"])
    )
    con_active_both = (
        set(df2024["ContractorIdentificationNumber"]) &
        set(df2025["ContractorIdentificationNumber"])
    )

    # Eligible 2024 pairs: both nodes active in both years
    eligible_2024 = {
        (ca, con) for ca, con in pairs_24
        if ca in ca_active_both and con in con_active_both
    }

    print(f"\n  Unique 2024 pairs              : {len(pairs_24):,}")
    print(f"  Eligible 2024 pairs (both nodes active in 2024 and 2025): {len(eligible_2024):,}")

    if len(eligible_2024) == 0:
        print("  No eligible pairs — skip")
        return

    expected, variance, p_vals, eligible_list = chung_lu_expected(eligible_2024, df2025)

    # Observed reconnections
    observed = sum(1 for pair in eligible_list if pair in pairs_25_set)
    n_eligible = len(eligible_list)

    obs_rate = observed / n_eligible if n_eligible > 0 else 0.0
    exp_rate = expected / n_eligible if n_eligible > 0 else 0.0
    excess_rate = obs_rate - exp_rate

    print(f"\n  Eligible pairs entering Chung-Lu test : {n_eligible:,}")
    print(f"\n  Null (Chung-Lu bipartite, |E_2025|={len(df2025):,}):")
    print(f"    Expected reconnections : {expected:.2f}")
    print(f"    Expected rate          : {exp_rate:.4f}")
    print(f"\n  Observed reconnections : {observed:,}")
    print(f"  Observed rate          : {obs_rate:.4f}")
    print(f"  Excess rate            : {excess_rate:+.4f}")

    z, p_value = reconnection_ztest(observed, expected, variance)
    print(f"\n  z-score  : {z:.4f}")
    print(f"  p-value  : {p_value:.4f}  (one-tailed, z_threshold={Z_THRESHOLD})")

    if p_value <= ALPHA and excess_rate >= EFFECT_THRESHOLD_RATE:
        verdict = "REJECT NULL — excess reconnection rate ≥ 10pp and z significant"
    elif p_value <= ALPHA:
        verdict = "REJECT NULL — significant but excess rate below 10pp effect threshold"
    else:
        verdict = "FAIL TO REJECT NULL"
    print(f"  Result   : {verdict}")


def run_cpv_analysis(df):
    print(f"\n=== PER-CPV-SECTOR (≥{MIN_CONTRACTORS_PER_SECTOR} domestic contractors in sector) ===")
    for sector, grp in df.groupby("cpv_division"):
        n_con = grp["ContractorIdentificationNumber"].nunique()
        if n_con < MIN_CONTRACTORS_PER_SECTOR:
            continue

        grp2024 = grp[grp["contract_year"] == 2024]
        grp2025 = grp[grp["contract_year"] == 2025]
        if len(grp2024) == 0 or len(grp2025) == 0:
            continue

        pairs_24 = annual_pairs(grp2024, 2024)
        pairs_25_set_cpv = set(
            zip(grp2025["CAIdentificationNumber"], grp2025["ContractorIdentificationNumber"])
        )

        ca_active_both = (
            set(grp2024["CAIdentificationNumber"]) &
            set(grp2025["CAIdentificationNumber"])
        )
        con_active_both = (
            set(grp2024["ContractorIdentificationNumber"]) &
            set(grp2025["ContractorIdentificationNumber"])
        )
        eligible_2024 = {
            (ca, con) for ca, con in pairs_24
            if ca in ca_active_both and con in con_active_both
        }

        if len(eligible_2024) < 5:
            continue

        expected, variance, p_vals, eligible_list = chung_lu_expected(eligible_2024, grp2025)
        if len(eligible_list) == 0 or variance <= 0:
            continue

        observed = sum(1 for pair in eligible_list if pair in pairs_25_set_cpv)
        n_eligible = len(eligible_list)
        obs_rate = observed / n_eligible
        exp_rate = expected / n_eligible
        excess_rate = obs_rate - exp_rate
        z, p_value = reconnection_ztest(observed, expected, variance)

        verdict = "reject" if (p_value <= ALPHA and excess_rate >= EFFECT_THRESHOLD_RATE) else "fail"
        print(
            f"  CPV {sector:>4} | eligible={n_eligible:>6,} | obs_rate={obs_rate:.3f} "
            f"| exp_rate={exp_rate:.3f} | excess={excess_rate:+.3f} "
            f"| z={z:.2f} | p={p_value:.4f} | {verdict}"
        )


def main():
    df_full, df = load_data(include_calloffs=False)
    print_header(df_full, df)

    run_analysis(df, label="AGGREGATE (IsUponFA=False)")
    run_cpv_analysis(df)

    print("\n=== SENSITIVITY CHECK (IsUponFA=True included) ===")
    _, df_sens = load_data(include_calloffs=True)
    print(f"(sensitivity subset rows: {len(df_sens):,})")
    run_analysis(df_sens, label="AGGREGATE (incl. call-offs)")


if __name__ == "__main__":
    main()
