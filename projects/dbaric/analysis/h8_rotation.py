"""
H8 — Temporal contractor rotation within CA–CPV cells.
One script per hypothesis.
"""

# ---------------------------------------------------------------------------
# Pre-flight spec — matches docs/HYPOTHESES.md exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H8"
HYPOTHESIS_STATEMENT = "Within specific authority–sector combinations, the same small set of contractors takes turns winning contracts"
GRAPH_FORM           = "bipartite multigraph sorted by ContractDate within CA–CPV cells"
NULL_MODEL           = "within-cell sequence permutation (1,000 permutations per cell)"
DATA_CONSTRAINT      = "cells require >=5 contracts and >=2 distinct contractors; ProcedureTypeId classification caveat for secondary test"
# ---------------------------------------------------------------------------

import random
import sys
import textwrap

import numpy as np
import pandas as pd
from scipy.stats import binom

DATA_PATH           = "data/contracts_clean.csv"
ALPHA               = 0.05
CELL_NULL_ITERS     = 1000
MIN_CONTRACTS       = 5
MIN_CONTRACTORS     = 2
EFFECT_THRESHOLD    = 0.15     # 15% fraction threshold (10pp above 5% baseline)
PROGRESS_INTERVAL   = 1000


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    df = pd.read_csv(DATA_PATH, low_memory=False, parse_dates=["ContractDate"])
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
        & df["is_foreign_contractor"].eq(False)
    )
    return df, df[mask].copy()


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


# ---------------------------------------------------------------------------
# Core metrics
# ---------------------------------------------------------------------------

def alternation_rate(contractor_sequence):
    if len(contractor_sequence) < 2:
        return 0.0
    pairs     = list(zip(contractor_sequence[:-1], contractor_sequence[1:]))
    different = sum(1 for a, b in pairs if a != b)
    return different / len(pairs)


def cell_permutation_null(contractor_sequence, n=CELL_NULL_ITERS):
    seq = list(contractor_sequence)
    results = []
    for _ in range(n):
        random.shuffle(seq)
        results.append(alternation_rate(seq))
    return results


def binomial_market_test(n_significant, n_cells, alpha=ALPHA):
    """Test whether fraction of significant cells exceeds Binomial(n_cells, 0.05) at alpha."""
    if n_cells == 0:
        return 0.0, 0.0, 1.0
    threshold   = binom.ppf(1 - alpha, n_cells, 0.05)
    fraction    = n_significant / n_cells
    p_value     = 1 - binom.cdf(n_significant - 1, n_cells, 0.05)
    return fraction, threshold / n_cells, p_value


# ---------------------------------------------------------------------------
# Run cells
# ---------------------------------------------------------------------------

def run_cells(df, label="primary"):
    cells = df.groupby(["CAIdentificationNumber", "cpv_division"])
    eligible   = []
    for (ca, cpv), group in cells:
        if len(group) >= MIN_CONTRACTS and group["ContractorIdentificationNumber"].nunique() >= MIN_CONTRACTORS:
            eligible.append((ca, cpv, group))

    n_cells = len(eligible)
    print(f"\n[{label}] Eligible cells: {n_cells:,}")
    if n_cells == 0:
        print(f"  No eligible cells — skipping.")
        return None

    n_significant      = 0
    excess_rates       = []

    for idx, (ca, cpv, group) in enumerate(eligible):
        if idx > 0 and idx % PROGRESS_INTERVAL == 0:
            print(f"  ... processed {idx:,}/{n_cells:,} cells", flush=True)

        seq      = (
            group.sort_values("ContractDate")["ContractorIdentificationNumber"].tolist()
        )
        obs_a    = alternation_rate(seq)
        null_a   = cell_permutation_null(seq, n=CELL_NULL_ITERS)
        p95_null = float(np.percentile(null_a, 95))
        med_null = float(np.median(null_a))

        significant = obs_a > p95_null
        if significant:
            n_significant += 1
        excess_rates.append(obs_a - med_null)

    fraction, threshold_frac, p_binom = binomial_market_test(n_significant, n_cells)
    mean_excess = float(np.mean(excess_rates))

    print(f"\n  [{label}] Market-level results")
    print(f"  Cells eligible         : {n_cells:,}")
    print(f"  Cells significant      : {n_significant:,}")
    print(f"  Observed fraction      : {fraction:.4f}  ({100*fraction:.1f}%)")
    print(f"  Binom threshold frac   : {threshold_frac:.4f}  ({100*threshold_frac:.1f}%)")
    print(f"  Effect threshold       : {EFFECT_THRESHOLD:.2f}  ({100*EFFECT_THRESHOLD:.0f}%)")
    print(f"  Binom p-value          : {p_binom:.4f}")
    print(f"  Mean excess alt. rate  : {mean_excess:+.4f}")

    reject_binom  = p_binom <= ALPHA
    above_effect  = fraction >= EFFECT_THRESHOLD
    if reject_binom and above_effect:
        print(f"  RESULT: reject null — fraction={fraction:.3f} >= {EFFECT_THRESHOLD}, p={p_binom:.4f}")
    elif reject_binom:
        print(f"  RESULT: reject null statistically but fraction={fraction:.3f} < effect threshold {EFFECT_THRESHOLD}")
    else:
        print(f"  RESULT: fail to reject null (p={p_binom:.4f})")

    return {
        "label":          label,
        "n_cells":        n_cells,
        "n_significant":  n_significant,
        "fraction":       fraction,
        "p_binom":        p_binom,
        "mean_excess":    mean_excess,
        "reject":         reject_binom and above_effect,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    df_full, df = load_data()
    print_header(df_full, df)

    # Primary test
    run_cells(df, label="primary")

    # Secondary: assumed-discretionary subset
    print("\n" + "-"*60)
    print("SECONDARY TEST — assumed-discretionary (ProcedureTypeId==11)")
    print("CAVEAT: ID 11 = discretionary is a working assumption, not a verified fact.")
    print("Results conditional on this classification being correct.")
    disc_df = df[df["is_discretionary"].eq(True)]
    run_cells(disc_df, label="assumed-discretionary")

    # Secondary: assumed-competitive subset
    print("\n" + "-"*60)
    print("SECONDARY TEST — assumed-competitive (ProcedureTypeId==1)")
    print("CAVEAT: ID 1 = competitive is a working assumption, not a verified fact.")
    comp_df = df[df["is_competitive"].eq(True)]
    run_cells(comp_df, label="assumed-competitive")

    # Sensitivity: rerun including IsUponFA=true
    print("\n" + "-"*60)
    print("SENSITIVITY CHECK — including IsUponFA=true (framework call-offs)")
    sens_mask = (
        df_full["in_analysis_window"].eq(True)
        & df_full["is_eur"].eq(True)
        & df_full["is_foreign_contractor"].eq(False)
    )
    sens_df = df_full[sens_mask].copy()
    if "ContractDate" in sens_df.columns and not pd.api.types.is_datetime64_any_dtype(sens_df["ContractDate"]):
        sens_df["ContractDate"] = pd.to_datetime(sens_df["ContractDate"], errors="coerce")
    print(f"Sensitivity subset: {len(sens_df):,} rows (call-offs included)")
    run_cells(sens_df, label="sensitivity-with-calloffs")


if __name__ == "__main__":
    main()
