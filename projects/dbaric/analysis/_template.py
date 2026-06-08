"""
Template for EOJN hypothesis analysis scripts.
Copy this file, rename to h<ID>_<name>.py, fill in the constants and TODO sections.
Do not run this file directly.
"""

# ---------------------------------------------------------------------------
# Pre-flight spec — must match docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H?"
HYPOTHESIS_STATEMENT = "TODO: one-line statement from docs/HYPOTHESES.md"
GRAPH_FORM           = "TODO: bipartite multigraph | weighted simple | projected unipartite"
NULL_MODEL           = "TODO: one-line description from docs/PLAN.md null model catalog"
DATA_CONSTRAINT      = "TODO: relevant constraint from docs/DATA_PROFILE.md, or 'none'"
# ---------------------------------------------------------------------------

import sys
import textwrap
import pandas as pd
import networkx as nx

DATA_PATH = "data/contracts_clean.csv"
NULL_ITERATIONS = 500
ALPHA = 0.05


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

    # Standard filters — adjust per hypothesis
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)   # remove if call-offs are in scope
    )
    return df, df[mask].copy()


def build_graph(df):
    # TODO: construct the bipartite graph
    # B = nx.MultiGraph()
    # B.add_nodes_from(df["CAIdentificationNumber"].unique(), bipartite=0)
    # B.add_nodes_from(df["ContractorIdentificationNumber"].unique(), bipartite=1)
    # for _, row in df.iterrows():
    #     B.add_edge(row["CAIdentificationNumber"],
    #                row["ContractorIdentificationNumber"],
    #                weight=row["TotalValue"])
    raise NotImplementedError


def observed_metric(G):
    # TODO: compute the metric under test
    raise NotImplementedError


def null_ensemble(df, n=NULL_ITERATIONS):
    # TODO: implement degree-preserving rewiring and compute metric per iteration
    # Return list of null metric values
    raise NotImplementedError


def report(observed, null_values):
    import numpy as np
    null_median = float(np.median(null_values))
    null_p95    = float(np.percentile(null_values, 95))
    excess      = observed - null_median
    p_value     = (np.sum(np.array(null_values) >= observed) + 1) / (len(null_values) + 1)

    print(f"Null median : {null_median:.4f}")
    print(f"Null 95th % : {null_p95:.4f}")
    print(f"Observed    : {observed:.4f}")
    print(f"Excess      : {excess:+.4f}")
    print(f"p-value     : {p_value:.4f}  (one-tailed, n={len(null_values)} iterations)")
    print()
    if p_value <= ALPHA and abs(excess) >= 0.05:
        print("RESULT: reject null — effect above threshold")
    elif p_value <= ALPHA:
        print("RESULT: reject null — but excess below effect threshold (statistically significant, not substantively meaningful)")
    else:
        print("RESULT: fail to reject null")


def main():
    df_full, df = load_data()
    print_header(df_full, df)

    G = build_graph(df)
    obs = observed_metric(G)
    null = null_ensemble(df)
    report(obs, null)


if __name__ == "__main__":
    main()
