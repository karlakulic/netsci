"""
H1b — Concentration in discretionary vs competitive (exploratory).
CAVEAT: results are conditional on ProcedureTypeId 11 = discretionary and
1 = competitive being correct — unverified assumption.
"""

HYPOTHESIS_ID        = "H1b"
HYPOTHESIS_STATEMENT = "Removing the competitive requirement amplifies vendor concentration"
GRAPH_FORM           = "bipartite multigraph (assumed-discretionary and assumed-competitive subgraphs)"
NULL_MODEL           = "procedure-type label permutation (shuffle is_discretionary/is_competitive labels across edges)"
DATA_CONSTRAINT      = "ProcedureTypeId label mapping unverified — all results conditional on ID 11=discretionary, ID 1=competitive"

CAVEAT = (
    "CAVEAT: results are conditional on ProcedureTypeId 11 = discretionary and "
    "1 = competitive being correct — unverified assumption"
)

import random
import textwrap

import numpy as np
import pandas as pd

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05
EFFECT_THRESHOLD_DELTA = 0.05
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
    {CAVEAT}
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
    arr = np.array(values, dtype=float)
    arr = arr[arr > 0]
    n = len(arr)
    if n == 0:
        return 0.0
    arr = np.sort(arr)
    ranks = np.arange(1, n + 1)
    return (2 * np.sum(ranks * arr) / (n * np.sum(arr))) - (n + 1) / n


def subgraph_gini(df_sub):
    """Gini of contractor strength in a subgraph DataFrame."""
    if len(df_sub) == 0:
        return np.nan
    strength = df_sub.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values
    return gini(strength)


def config_null_gini(df_sub, n=100):
    """
    Bipartite stub-matching null for a single subgraph.
    Returns list of null Gini values.
    """
    ca_stubs = df_sub["CAIdentificationNumber"].tolist()
    contractor_stubs = df_sub["ContractorIdentificationNumber"].tolist()
    weights = df_sub["TotalValue"].tolist()
    results = []
    for _ in range(n):
        shuffled = random.sample(contractor_stubs, len(contractor_stubs))
        null_df = pd.DataFrame({
            "CAIdentificationNumber": ca_stubs,
            "ContractorIdentificationNumber": shuffled,
            "TotalValue": weights,
        })
        g = gini(null_df.groupby("ContractorIdentificationNumber")["TotalValue"].sum().values)
        results.append(g)
    return results


def gini_excess(df_sub, n_null=100):
    """
    Observed Gini minus null median for a subgraph.
    Uses a smaller inner null (100) since it is called inside the outer permutation loop.
    """
    if len(df_sub) < 2:
        return np.nan
    obs = subgraph_gini(df_sub)
    null_vals = config_null_gini(df_sub, n=n_null)
    return obs - float(np.median(null_vals))


def delta_gini_excess(df, disc_mask, comp_mask):
    """
    Δ(Gini excess) = Gini_excess_discretionary − Gini_excess_competitive.
    Uses inner null of 50 per subgraph to keep outer permutation tractable.
    """
    df_disc = df[disc_mask]
    df_comp = df[comp_mask]
    exc_disc = gini_excess(df_disc, n_null=50)
    exc_comp = gini_excess(df_comp, n_null=50)
    if np.isnan(exc_disc) or np.isnan(exc_comp):
        return np.nan
    return exc_disc - exc_comp


def permutation_null(df, n=NULL_ITERATIONS):
    """
    Shuffle the is_discretionary flag across rows; recompute Δ(Gini excess) per permutation.
    Preserves counts of True/False labels (same multiset).
    """
    disc_labels = df["is_discretionary"].tolist()
    results = []
    for _ in range(n):
        shuffled = random.sample(disc_labels, len(disc_labels))
        perm_df = df.copy()
        perm_df["is_discretionary"] = shuffled
        perm_df["is_competitive"] = ~perm_df["is_discretionary"]
        disc_mask = perm_df["is_discretionary"].eq(True)
        comp_mask = perm_df["is_competitive"].eq(True)
        delta = delta_gini_excess(perm_df, disc_mask, comp_mask)
        if not np.isnan(delta):
            results.append(delta)
    return results


def run_analysis(df, label="AGGREGATE"):
    print(f"\n--- {label}  [{CAVEAT}] ---")
    disc_mask = df["is_discretionary"].eq(True)
    comp_mask = df["is_competitive"].eq(True)

    n_disc = disc_mask.sum()
    n_comp = comp_mask.sum()
    print(f"  Assumed-discretionary edges : {n_disc:,}")
    print(f"  Assumed-competitive edges   : {n_comp:,}")

    if n_disc < 2 or n_comp < 2:
        print(f"  Insufficient data in one subgraph — skip  [{CAVEAT}]")
        return

    obs_disc_gini = subgraph_gini(df[disc_mask])
    obs_comp_gini = subgraph_gini(df[comp_mask])
    obs_delta = obs_disc_gini - obs_comp_gini

    print(f"  Observed Gini (assumed-discretionary) : {obs_disc_gini:.4f}  [{CAVEAT}]")
    print(f"  Observed Gini (assumed-competitive)   : {obs_comp_gini:.4f}  [{CAVEAT}]")
    print(f"  Observed raw Gini gap                 : {obs_delta:+.4f}  [{CAVEAT}]")

    # For the permutation null, Δ is Gini_excess_disc - Gini_excess_comp
    # Observed Δ uses full inner nulls
    exc_disc = gini_excess(df[disc_mask], n_null=100)
    exc_comp = gini_excess(df[comp_mask], n_null=100)
    if np.isnan(exc_disc) or np.isnan(exc_comp):
        print(f"  Could not compute Gini excess — skip  [{CAVEAT}]")
        return
    obs_delta_excess = exc_disc - exc_comp

    print(f"  Observed Δ(Gini excess)               : {obs_delta_excess:+.4f}  [{CAVEAT}]")
    print(f"  Running permutation null (n={NULL_ITERATIONS}) …")

    null_deltas = permutation_null(df, n=NULL_ITERATIONS)
    if len(null_deltas) == 0:
        print(f"  No valid permutation results — skip  [{CAVEAT}]")
        return

    null_arr = np.array(null_deltas)
    null_median = float(np.median(null_arr))
    null_p95 = float(np.percentile(null_arr, 95))
    excess = obs_delta_excess - null_median
    p_value = (np.sum(null_arr >= obs_delta_excess) + 1) / (len(null_arr) + 1)

    print(f"  Null median Δ : {null_median:.4f}  [{CAVEAT}]")
    print(f"  Null 95th %   : {null_p95:.4f}  [{CAVEAT}]")
    print(f"  Observed Δ    : {obs_delta_excess:.4f}  [{CAVEAT}]")
    print(f"  Excess        : {excess:+.4f}  [{CAVEAT}]")
    print(f"  p-value       : {p_value:.4f}  (one-tailed, n={len(null_arr)})  [{CAVEAT}]")

    if p_value <= ALPHA and abs(excess) >= EFFECT_THRESHOLD_DELTA:
        verdict = "REJECT NULL — effect above threshold"
    elif p_value <= ALPHA:
        verdict = "REJECT NULL — but excess below effect threshold (significant, not substantive)"
    else:
        verdict = "FAIL TO REJECT NULL"
    print(f"  Result        : {verdict}  [{CAVEAT}]")


def main():
    df_full, df = load_data()
    print_header(df_full, df)

    print(
        "\nH1 outcome must be examined before interpreting H1b results. "
        "H1b is exploratory — cannot be elevated to a finding without a separate pre-registered test."
    )

    run_analysis(df, label="AGGREGATE")

    print(f"\n=== PER-CPV-SECTOR (≥{MIN_CONTRACTORS_PER_SECTOR} domestic contractors) ===")
    for sector, grp in df.groupby("cpv_division"):
        n_con = grp["ContractorIdentificationNumber"].nunique()
        if n_con >= MIN_CONTRACTORS_PER_SECTOR:
            run_analysis(grp, label=f"CPV {sector}")


if __name__ == "__main__":
    main()
