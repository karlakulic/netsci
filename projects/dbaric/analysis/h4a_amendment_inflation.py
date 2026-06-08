# ---------------------------------------------------------------------------
# Pre-flight spec — must match docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H4a"
HYPOTHESIS_STATEMENT = "Contracts with established vendors are amended to higher values more than first-contract pairs of equivalent market size"
GRAPH_FORM           = "bipartite multigraph (prior-relationship label from graph structure)"
NULL_MODEL           = "bipartite configuration model; prior-relationship status determined by rewired graph structure"
DATA_CONSTRAINT      = "amendments are rare (mean TotalValue ≈ mean InitialValue); restrict to InitialValue > 0; signal concentrated in small fraction of contracts"
# ---------------------------------------------------------------------------

import sys
import textwrap
import random
import numpy as np
import pandas as pd

DATA_PATH       = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA           = 0.05
EFFECT_THRESHOLD = 0.05


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
        & df["InitialValue"].notna()
        & df["InitialValue"].gt(0)
        & df["TotalValue"].notna()
    )
    return df, df[mask].copy()


def label_prior_relationships(df):
    # Sort by ContractDate; first occurrence of each (CA, contractor) pair = 'first_contract',
    # all subsequent = 'prior_relationship'.
    df = df.sort_values("ContractDate").copy()
    df["_pair_order"] = df.groupby(
        ["CAIdentificationNumber", "ContractorIdentificationNumber"]
    ).cumcount()
    df["relationship_type"] = np.where(
        df["_pair_order"] == 0, "first_contract", "prior_relationship"
    )
    df = df.drop(columns=["_pair_order"])
    return df


def amendment_excess(df):
    df = df.copy()
    df["ratio"] = df["TotalValue"] / df["InitialValue"]
    prior = df.loc[df["relationship_type"] == "prior_relationship", "ratio"]
    first = df.loc[df["relationship_type"] == "first_contract", "ratio"]
    if len(prior) == 0 or len(first) == 0:
        return np.nan
    return prior.mean() - first.mean()


def null_excess(df, n=NULL_ITERATIONS):
    # Stub-matching: shuffle contractor column → re-label prior vs first-contract → recompute excess.
    ca_col         = df["CAIdentificationNumber"].tolist()
    contractor_col = df["ContractorIdentificationNumber"].tolist()
    initial_col    = df["InitialValue"].tolist()
    total_col      = df["TotalValue"].tolist()
    date_col       = df["ContractDate"].tolist()

    results = []
    for _ in range(n):
        shuffled = contractor_col.copy()
        random.shuffle(shuffled)
        null_df = pd.DataFrame({
            "CAIdentificationNumber":         ca_col,
            "ContractorIdentificationNumber": shuffled,
            "InitialValue":                   initial_col,
            "TotalValue":                     total_col,
            "ContractDate":                   date_col,
        })
        null_df = label_prior_relationships(null_df)
        results.append(amendment_excess(null_df))
    return [r for r in results if not np.isnan(r)]


def report(label, observed, null_values):
    null_arr    = np.array(null_values)
    null_median = float(np.median(null_arr))
    null_p95    = float(np.percentile(null_arr, 95))
    excess      = observed - null_median
    p_value     = (np.sum(null_arr >= observed) + 1) / (len(null_arr) + 1)

    print(f"  Null median : {null_median:.4f}")
    print(f"  Null 95th % : {null_p95:.4f}")
    print(f"  Observed    : {observed:.4f}")
    print(f"  Excess      : {excess:+.4f}")
    print(f"  p-value     : {p_value:.4f}  (one-tailed, n={len(null_values)} iterations)")
    if p_value <= ALPHA and excess >= EFFECT_THRESHOLD:
        print(f"  RESULT [{label}]: reject null — effect above threshold")
    elif p_value <= ALPHA:
        print(f"  RESULT [{label}]: reject null — excess below effect threshold")
    else:
        print(f"  RESULT [{label}]: fail to reject null")
    print()


def run_split(df, split_col, split_values, label_prefix):
    for val in split_values:
        subset = df[df[split_col] == val].copy()
        if subset.empty:
            print(f"  [{label_prefix}={val}] — no data")
            continue
        subset = label_prior_relationships(subset)
        counts = subset["relationship_type"].value_counts()
        n_prior = counts.get("prior_relationship", 0)
        n_first = counts.get("first_contract", 0)
        print(f"  [{label_prefix}={val}]  prior={n_prior:,}  first={n_first:,}")
        obs  = amendment_excess(subset)
        null = null_excess(subset)
        if np.isnan(obs):
            print("    Skipped — insufficient data in one group\n")
            continue
        report(f"{label_prefix}={val}", obs, null)


def main():
    df_full, df = load_data()
    print_header(df_full, df)

    # Amendment rarity
    amended_frac = (df["TotalValue"] / df["InitialValue"] > 1.01).mean()
    print(f"Amendment rarity (TotalValue/InitialValue > 1.01): {amended_frac:.4f} ({100*amended_frac:.2f}% of contracts)\n")

    # Label relationships on the full analysis set
    df = label_prior_relationships(df)
    counts = df["relationship_type"].value_counts()
    n_prior = counts.get("prior_relationship", 0)
    n_first = counts.get("first_contract", 0)
    print(f"Prior relationships : {n_prior:,}")
    print(f"First contracts     : {n_first:,}\n")

    # Overall test
    print("=== Overall ===")
    obs_overall  = amendment_excess(df)
    null_overall = null_excess(df)
    report("overall", obs_overall, null_overall)

    # Within ContractTypeId
    print("=== By ContractTypeId (1=supplies, 2=services, 3=works) ===")
    run_split(df, "ContractTypeId", [1, 2, 3], "type")

    # Within TotalValue quartile
    print("=== By TotalValue quartile ===")
    df["_value_quartile"] = pd.qcut(df["TotalValue"], q=4, labels=[1, 2, 3, 4])
    run_split(df, "_value_quartile", [1, 2, 3, 4], "quartile")


if __name__ == "__main__":
    main()
