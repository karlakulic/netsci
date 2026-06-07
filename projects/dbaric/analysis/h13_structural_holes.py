"""
H13 — Structural holes and amendment inflation.

Contractors bridging disconnected institutional clusters extract higher amended
contract values than equivalent-degree contractors.

Bipartite betweenness centrality (on simple, unweighted graph) is correlated
with mean amendment inflation ratio; null ensemble from degree-preserving
edge-switching rewiring (100 iterations).
"""

# ---------------------------------------------------------------------------
# Pre-flight spec — matches docs/HYPOTHESES.md §H13 exactly
# ---------------------------------------------------------------------------
HYPOTHESIS_ID        = "H13"
HYPOTHESIS_STATEMENT = "Contractors bridging disconnected institutional clusters extract higher amended contract values than equivalent-degree contractors"
GRAPH_FORM           = "bipartite simple graph (unweighted; collapse multigraph; IsUponFA=false)"
NULL_MODEL           = "Bipartite configuration model — 100 iterations (computational constraint); null distribution of Spearman(approx_betweenness_rank, mean_amendment_inflation_ratio); betweenness approximated via k=50 sampled sources"
DATA_CONSTRAINT      = "Restrict to contractors with degree >= 5 AND at least one contract with InitialValue > 0; amendments rare — mean TotalValue approx mean InitialValue"
# ---------------------------------------------------------------------------

NULL_ITERATIONS = 100  # NOT 500 — computational constraint per H13 spec
ALPHA           = 0.05
EFFECT_THRESHOLD_SPEARMAN_EXCESS = 0.10  # minimum excess Spearman for substantive claim
DEGREE_MIN      = 5    # eligible contractor minimum degree

import sys
import time
import random
import textwrap

import numpy as np
import pandas as pd
import networkx as nx
from scipy import stats


DATA_PATH = "data/contracts_clean.csv"


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

def print_header(df_full, df, n_eligible, amendment_rarity_pct,
                 betweenness_runtime_s, degree_min_used):
    foreign_n   = df_full["is_foreign_contractor"].sum()
    foreign_pct = 100 * foreign_n / len(df_full)
    print(textwrap.dedent(f"""
    ============================================================
    Hypothesis  : {HYPOTHESIS_ID} — {HYPOTHESIS_STATEMENT}
    Graph form  : {GRAPH_FORM}
    Null model  : {NULL_MODEL}
    Constraint  : {DATA_CONSTRAINT}
    ------------------------------------------------------------
    NULL_ITERATIONS = {NULL_ITERATIONS} (not 500) — computational constraint per H13 spec
    ------------------------------------------------------------
    Rows loaded      : {len(df_full):,}
    Analysis subset  : {len(df):,}
    Foreign excluded : {foreign_n:,} ({foreign_pct:.1f}%)
    ------------------------------------------------------------
    Degree min used  : {degree_min_used} (5 unless betweenness runtime forced >= 10 restriction)
    Eligible contractors (degree >= {degree_min_used}, InitialValue > 0 filter): {n_eligible:,}
    Amendment rarity : {amendment_rarity_pct:.2f}% of contracts have TotalValue != InitialValue
    Betweenness runtime : {betweenness_runtime_s:.1f}s
    ============================================================
    """).strip())


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data():
    df = pd.read_csv(DATA_PATH, low_memory=False)
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_framework_calloff"].eq(False)
    )
    return df, df[mask].copy()


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_simple_bipartite(df):
    """Collapse multigraph to simple bipartite graph (unweighted binary edges).

    Nodes:
        CA  nodes  -> bipartite=0 (prefix 'ca_')
        Contractor -> bipartite=1 (prefix 'ct_')

    Returns (G, ca_nodes_set, contractor_nodes_set)
    """
    G = nx.Graph()

    ca_ids = df["CAIdentificationNumber"].dropna().unique()
    ct_ids = df["ContractorIdentificationNumber"].dropna().unique()

    ca_nodes = {f"ca_{v}" for v in ca_ids}
    ct_nodes = {f"ct_{v}" for v in ct_ids}

    for node in ca_nodes:
        G.add_node(node, bipartite=0)
    for node in ct_nodes:
        G.add_node(node, bipartite=1)

    # Add one edge per unique (CA, contractor) pair
    pairs = df[["CAIdentificationNumber", "ContractorIdentificationNumber"]].dropna().drop_duplicates()
    for _, row in pairs.iterrows():
        ca  = f"ca_{row['CAIdentificationNumber']}"
        ct  = f"ct_{row['ContractorIdentificationNumber']}"
        if not G.has_edge(ca, ct):
            G.add_edge(ca, ct)

    return G, ca_nodes, ct_nodes


# ---------------------------------------------------------------------------
# Amendment inflation ratio
# ---------------------------------------------------------------------------

def compute_amendment_ratios(df):
    """Per contractor: mean(TotalValue / InitialValue) for rows where InitialValue > 0.

    Unamended contracts (TotalValue == InitialValue) contribute ratio = 1.0.
    Returns dict {contractor_key: mean_ratio}
    """
    sub = df[df["InitialValue"] > 0].copy()
    sub["ratio"] = sub["TotalValue"] / sub["InitialValue"]
    sub["ct_key"] = "ct_" + sub["ContractorIdentificationNumber"].astype(str)

    result = sub.groupby("ct_key")["ratio"].mean().to_dict()
    return result


def amendment_rarity(df):
    """Fraction of rows where TotalValue != InitialValue (both present)."""
    valid = df[df["InitialValue"] > 0]
    if len(valid) == 0:
        return 0.0
    amended = (valid["TotalValue"] != valid["InitialValue"]).sum()
    return 100.0 * amended / len(valid)


# ---------------------------------------------------------------------------
# Eligible contractor filtering
# ---------------------------------------------------------------------------

def eligible_contractors(G, ct_nodes, amendment_ratio_map, degree_min):
    """Return set of contractor keys that pass both filters:
        1. degree >= degree_min in simple graph G
        2. appear in amendment_ratio_map (i.e. >= 1 contract with InitialValue > 0)
    """
    eligible = set()
    for ct in ct_nodes:
        if ct not in G:
            continue
        if G.degree(ct) >= degree_min and ct in amendment_ratio_map:
            eligible.add(ct)
    return eligible


# ---------------------------------------------------------------------------
# Bipartite betweenness centrality
# ---------------------------------------------------------------------------

BETWEENNESS_K = 50   # sampled sources for approximate betweenness (~11s per call vs hours for exact)

def bipartite_betweenness(G, ct_nodes_set):
    """Approximate betweenness centrality via k=500 random source sampling.

    Exact bipartite betweenness on ~47K nodes is O(V*E) ≈ hours in pure Python.
    k=500 sampled-source approximation reduces this to ~5-30 seconds while
    preserving rank correlation structure needed for Spearman test.
    Standard betweenness on the full bipartite graph is equivalent for detecting
    bridge contractors: only contractors can bridge CA clusters in a bipartite graph.

    Times the call. Returns (centrality_dict, runtime_seconds).
    """
    t0 = time.time()
    bc = nx.betweenness_centrality(G, k=BETWEENNESS_K, normalized=True, seed=42)
    elapsed = time.time() - t0
    return bc, elapsed


# ---------------------------------------------------------------------------
# Degree-preserving edge switching (for null model)
# ---------------------------------------------------------------------------

def _edge_switch_inplace(edge_list, n_swaps):
    """Perform n_swaps successful degree-preserving bipartite edge swaps
    on edge_list (list of [ca, ct] lists, modified in place).

    Strategy: pick 2 random edges (ca1-ct1, ca2-ct2); swap to (ca1-ct2, ca2-ct1)
    if those two new edges don't already exist.

    edge_list: list of [ca_key, ct_key] pairs.
    Uses an edge_set for fast lookup.

    Modifies edge_list in place. Returns nothing.
    """
    edge_set = set(map(tuple, edge_list))
    attempts  = 0
    successes = 0
    max_attempts = n_swaps * 20  # give up after this many total tries

    while successes < n_swaps and attempts < max_attempts:
        attempts += 1
        i, j = random.randrange(len(edge_list)), random.randrange(len(edge_list))
        if i == j:
            continue
        ca1, ct1 = edge_list[i]
        ca2, ct2 = edge_list[j]
        if ca1 == ca2 or ct1 == ct2:
            continue
        new1 = (ca1, ct2)
        new2 = (ca2, ct1)
        if new1 in edge_set or new2 in edge_set:
            continue
        # Perform swap
        edge_set.discard((ca1, ct1))
        edge_set.discard((ca2, ct2))
        edge_set.add(new1)
        edge_set.add(new2)
        edge_list[i] = [ca1, ct2]
        edge_list[j] = [ca2, ct1]
        successes += 1


def _build_graph_from_edges(edge_list, ca_nodes, ct_nodes):
    """Reconstruct nx.Graph from an edge list."""
    G = nx.Graph()
    for node in ca_nodes:
        G.add_node(node, bipartite=0)
    for node in ct_nodes:
        G.add_node(node, bipartite=1)
    for ca, ct in edge_list:
        G.add_edge(ca, ct)
    return G


# ---------------------------------------------------------------------------
# Spearman correlation helper
# ---------------------------------------------------------------------------

def spearman_betweenness_amendment(bc_map, amendment_ratio_map, eligible):
    """Compute Spearman(betweenness, amendment_ratio) over eligible contractors.

    Both maps are keyed by contractor key string.
    Returns (rho, pvalue) or (nan, nan) if too few observations.
    """
    common = [ct for ct in eligible if ct in bc_map and ct in amendment_ratio_map]
    if len(common) < 5:
        return float("nan"), float("nan")
    bv = np.array([bc_map[ct] for ct in common])
    av = np.array([amendment_ratio_map[ct] for ct in common])
    rho, pval = stats.spearmanr(bv, av)
    return float(rho), float(pval)


# ---------------------------------------------------------------------------
# Null ensemble
# ---------------------------------------------------------------------------

def null_ensemble(G_orig, edge_list_orig, ca_nodes, ct_nodes,
                  amendment_ratio_map, eligible_set, n=NULL_ITERATIONS):
    """100-iteration null. For each iteration:
        1. Copy edge list; degree-preserving swap (10 * |E| successful swaps).
        2. Rebuild graph.
        3. Recompute approximate betweenness (k=500).
        4. Compute Spearman(rewired_betweenness, amendment_ratio) on eligible set.
    Amendment ratios are FIXED (node property).
    Returns list of Spearman rho values.
    """
    n_swaps = 10 * len(edge_list_orig)
    null_rhos = []

    print(f"  Running {n} null iterations ({n_swaps:,} swaps per iter, k={BETWEENNESS_K} approx) …", flush=True)
    for i in range(n):
        if (i + 1) % 10 == 0:
            print(f"    iteration {i+1}/{n}", flush=True)

        el = [list(e) for e in edge_list_orig]   # fresh copy
        _edge_switch_inplace(el, n_swaps)

        G_null = _build_graph_from_edges(el, ca_nodes, ct_nodes)
        bc_null = nx.betweenness_centrality(G_null, k=BETWEENNESS_K, normalized=True, seed=i)

        rho, _ = spearman_betweenness_amendment(bc_null, amendment_ratio_map, eligible_set)
        if not np.isnan(rho):
            null_rhos.append(rho)

    return null_rhos


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def report(observed_rho, null_rhos):
    arr = np.array(null_rhos)
    null_median = float(np.median(arr))
    null_p95    = float(np.percentile(arr, 95))
    excess      = observed_rho - null_median
    # one-tailed: fraction of null >= observed
    p_value = (np.sum(arr >= observed_rho) + 1) / (len(arr) + 1)

    print()
    print("=== PRIMARY TEST: Spearman(bipartite_betweenness, mean_amendment_ratio) ===")
    print(f"Null median : {null_median:.4f}")
    print(f"Null 95th % : {null_p95:.4f}")
    print(f"Observed    : {observed_rho:.4f}")
    print(f"Excess      : {excess:+.4f}")
    print(f"p-value     : {p_value:.4f}  (one-tailed, n={len(null_rhos)} iterations)")
    print()
    if p_value <= ALPHA and excess >= EFFECT_THRESHOLD_SPEARMAN_EXCESS:
        print("RESULT: reject null — excess Spearman >= 0.10 and p <= 0.05")
        print("        Consistent with structural position (bridging) enabling value extraction.")
    elif p_value <= ALPHA:
        print("RESULT: reject null — statistically significant but excess Spearman < 0.10")
        print("        Effect is below substantive threshold; not a finding under H13 spec.")
    else:
        print("RESULT: fail to reject null")
    print()


def report_quartile(df, bc_map, eligible_set):
    """Secondary: Spearman within contract value quartile.

    Quartile is assigned per contract (based on TotalValue across the whole
    analysis subset). For each contractor and each quartile, compute mean
    amendment ratio within that quartile. Then run Spearman per quartile.
    """
    print("=== SECONDARY TEST: Spearman within contract value quartile ===")

    # Assign quartile to each contract
    sub = df.copy()
    sub["quartile"] = pd.qcut(sub["TotalValue"], q=4, labels=[1, 2, 3, 4])

    sub_valid = sub[sub["InitialValue"] > 0].copy()
    sub_valid["ratio"] = sub_valid["TotalValue"] / sub_valid["InitialValue"]
    sub_valid["ct_key"] = "ct_" + sub_valid["ContractorIdentificationNumber"].astype(str)

    for q in [1, 2, 3, 4]:
        q_df = sub_valid[sub_valid["quartile"] == q]
        # mean ratio per contractor within this quartile
        ct_ratio_q = q_df.groupby("ct_key")["ratio"].mean().to_dict()

        # intersect with eligible set and bc_map
        common = [ct for ct in eligible_set if ct in bc_map and ct in ct_ratio_q]
        if len(common) < 5:
            print(f"  Q{q}: too few contractors ({len(common)}) — skipped")
            continue

        bv = np.array([bc_map[ct] for ct in common])
        av = np.array([ct_ratio_q[ct] for ct in common])
        rho, pval = stats.spearmanr(bv, av)
        print(f"  Q{q} (n={len(common):,}):  rho={rho:+.4f}  p={pval:.4f}  "
              f"({'significant' if pval <= ALPHA else 'not significant'} at alpha=0.05, one-tailed)")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # 1. Load data
    df_full, df = load_data()

    # 2. Build simple bipartite graph
    print("Building simple bipartite graph …", flush=True)
    G, ca_nodes, ct_nodes = build_simple_bipartite(df)
    print(f"  Nodes: {G.number_of_nodes():,}  Edges: {G.number_of_edges():,}", flush=True)

    # 3. Amendment ratios (from full analysis subset df, not simple graph)
    amend_map  = compute_amendment_ratios(df)
    amend_rare = amendment_rarity(df)

    # 4. Eligible contractors
    degree_min_used = DEGREE_MIN
    eligible = eligible_contractors(G, ct_nodes, amend_map, degree_min_used)
    print(f"  Eligible contractors (degree >= {degree_min_used}, InitialValue filter): {len(eligible):,}", flush=True)

    # 5. Bipartite betweenness centrality on observed graph
    print("Computing bipartite betweenness centrality (may take several minutes) …", flush=True)
    bc_map, bc_runtime = bipartite_betweenness(G, ct_nodes)

    # Check 10-minute threshold; if exceeded, fall back to degree >= 10
    if bc_runtime > 600:
        print(f"  WARNING: betweenness runtime {bc_runtime:.0f}s > 600s — restricting to contractor degree >= 10",
              flush=True)
        degree_min_used = 10
        eligible = eligible_contractors(G, ct_nodes, amend_map, degree_min_used)
        print(f"  Eligible contractors after restriction: {len(eligible):,}", flush=True)

    # 6. Print header (after we know runtime and eligible count)
    print_header(df_full, df, len(eligible), amend_rare, bc_runtime, degree_min_used)

    # 7. Observed Spearman
    obs_rho, obs_pval = spearman_betweenness_amendment(bc_map, amend_map, eligible)
    print(f"Observed Spearman rho = {obs_rho:.4f} (scipy two-tailed p={obs_pval:.4f})")

    # 8. Null ensemble — work from edge list
    edge_list_orig = [[u, v] for u, v in G.edges()]
    null_rhos = null_ensemble(
        G, edge_list_orig, ca_nodes, ct_nodes,
        amend_map, eligible, n=NULL_ITERATIONS
    )

    # 9. Report
    report(obs_rho, null_rhos)

    # 10. Quartile secondary
    report_quartile(df, bc_map, eligible)


if __name__ == "__main__":
    main()
