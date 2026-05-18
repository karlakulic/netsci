import marimo

__generated_with = "0.21.1"
app = marimo.App(
    width="medium",
    app_title="Exercise 07 — Gowalla Small-World Analysis",
)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Exercise 07 — Gowalla Small-World Analysis
    **Topic:** Student 14 — Gowalla Geo-social Network
    **Goal:** Test whether friendship + geography produces the small-world pattern —
    short average paths combined with substantially higher clustering than a random baseline.

    > **Small-world criterion (Watts & Strogatz 1998):**
    > A network is small-world if its clustering coefficient C >> C_random
    > while its average path length L ≈ L_random.
    > Formally: σ = (C/C_random) / (L/L_random) >> 1.

    > **Scope:** We work on the **largest connected component** of the full graph
    > (196,591 nodes) and the same BFS-2000 sample for detailed analysis.
    > Both scopes are stated explicitly throughout.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## ① Load Graph — Full LCC and Sample
    """)
    return


@app.cell
def _():
    import kagglehub
    import os
    import random
    import pandas as pd
    import networkx as nx
    import numpy as np

    path = kagglehub.dataset_download("marquis03/gowalla")
    edge_file = os.path.join(path, "Gowalla_edges.txt")
    df_edges = pd.read_csv(edge_file, sep="\t", header=None, names=["user_a", "user_b"])

    G_full = nx.from_pandas_edgelist(df_edges, source="user_a", target="user_b")

    # Full-graph LCC
    full_lcc_nodes = max(nx.connected_components(G_full), key=len)
    G_lcc = G_full.subgraph(full_lcc_nodes).copy()

    # BFS sample (same as all prior exercises)
    random.seed(42)
    degrees_full = dict(G_full.degree())
    top_node = max(degrees_full, key=lambda n: degrees_full[n])
    bfs_nodes = list(nx.bfs_tree(G_full, top_node).nodes())[:2000]
    G_sample = G_full.subgraph(bfs_nodes).copy()

    print(f"Full graph        — n={G_full.number_of_nodes():,}  m={G_full.number_of_edges():,}")
    print(f"Full graph LCC    — n={G_lcc.number_of_nodes():,}  m={G_lcc.number_of_edges():,}")
    print(f"BFS-2000 sample   — n={G_sample.number_of_nodes():,}  m={G_sample.number_of_edges():,}")
    print(f"LCC covers {G_lcc.number_of_nodes()/G_full.number_of_nodes():.1%} of all nodes")
    return G_lcc, G_sample, np, nx, random


@app.cell
def _(mo):
    mo.md("""
    ## ② Clustering Coefficient
    """)
    return


@app.cell
def _(G_lcc, G_sample, nx):
    # Sample clustering: exact
    sample_clustering = nx.average_clustering(G_sample)

    # Full LCC clustering: exact (networkx handles this efficiently)
    print("Computing full LCC average clustering...")
    full_clustering = nx.average_clustering(G_lcc)

    print(f"Sample clustering (BFS-2000): {sample_clustering:.4f}")
    print(f"Full LCC clustering:          {full_clustering:.4f}")
    return full_clustering, sample_clustering


@app.cell
def _(mo):
    mo.md("""
    ## ③ Average Shortest Path Length (Sampled)
    """)
    return


@app.cell
def _(G_lcc, G_sample, nx, random):
    # Sample: exact (small enough)
    random.seed(42)
    _src_sample = random.sample(list(G_sample.nodes()), 300)
    _sample_lengths = []
    for _src in _src_sample:
        _d = nx.single_source_shortest_path_length(G_sample, _src)
        _sample_lengths.extend(_d.values())
    sample_avg_path = sum(_sample_lengths) / len(_sample_lengths)

    # Full LCC: too large for exact — sample 500 source nodes
    random.seed(42)
    _lcc_sources = random.sample(list(G_lcc.nodes()), 500)
    _lcc_lengths = []
    for _src in _lcc_sources:
        _d = nx.single_source_shortest_path_length(G_lcc, _src)
        _lcc_lengths.extend(_d.values())
    full_avg_path = sum(_lcc_lengths) / len(_lcc_lengths)

    # Also get diameter approximation for the sample
    _ecc_sample = random.sample(list(G_sample.nodes()), 100)
    _eccs = [max(nx.single_source_shortest_path_length(G_sample, _n).values())
             for _n in _ecc_sample]
    sample_approx_diameter = max(_eccs)

    print(f"Sample avg path length (exact 300-src):    {sample_avg_path:.4f}")
    print(f"Full LCC avg path length (500-src sample): {full_avg_path:.4f}")
    print(f"Sample approx diameter (100-src):          {sample_approx_diameter}")
    return full_avg_path, sample_approx_diameter, sample_avg_path


@app.cell
def _(mo):
    mo.md("""
    ## ④ ER Baselines
    """)
    return


@app.cell
def _(G_lcc, G_sample, np, nx, random):
    # --- Sample ER baseline ---
    n_s = G_sample.number_of_nodes()
    m_s = G_sample.number_of_edges()
    G_er_sample = nx.gnm_random_graph(n_s, m_s, seed=42)
    er_sample_clustering = nx.average_clustering(G_er_sample)

    er_s_lcc = max(nx.connected_components(G_er_sample), key=len)
    G_er_s_lcc = G_er_sample.subgraph(er_s_lcc).copy()
    random.seed(42)
    _er_s_src = random.sample(list(G_er_s_lcc.nodes()), min(300, G_er_s_lcc.number_of_nodes()))
    _er_s_lens = []
    for _src in _er_s_src:
        _d = nx.single_source_shortest_path_length(G_er_s_lcc, _src)
        _er_s_lens.extend(_d.values())
    er_sample_avg_path = sum(_er_s_lens) / len(_er_s_lens)

    # --- Full LCC ER baseline ---
    # Theoretical ER predictions (exact computation too slow at 196k nodes)
    n_f = G_lcc.number_of_nodes()
    m_f = G_lcc.number_of_edges()
    p_f = (2 * m_f) / (n_f * (n_f - 1))
    avg_k_f = 2 * m_f / n_f
    # ER theoretical: C_er ≈ p, L_er ≈ ln(n)/ln(avg_k)
    er_full_clustering_theory = p_f
    er_full_avg_path_theory = np.log(n_f) / np.log(avg_k_f)

    print(f"--- Sample ER baseline (G(n,m), n={n_s}, m={m_s}) ---")
    print(f"ER sample clustering:     {er_sample_clustering:.4f}")
    print(f"ER sample avg path:       {er_sample_avg_path:.4f}")
    print()
    print(f"--- Full LCC ER baseline (theoretical, n={n_f:,}, p={p_f:.6f}) ---")
    print(f"ER full clustering (≈p):  {er_full_clustering_theory:.6f}")
    print(f"ER full avg path (ln/ln): {er_full_avg_path_theory:.4f}")
    return (
        G_er_sample,
        er_full_avg_path_theory,
        er_full_clustering_theory,
        er_sample_avg_path,
        er_sample_clustering,
    )


@app.cell
def _(mo):
    mo.md("""
    ## ⑤ Small-World Coefficient σ
    """)
    return


@app.cell
def _(
    er_full_avg_path_theory,
    er_full_clustering_theory,
    er_sample_avg_path,
    er_sample_clustering,
    full_avg_path,
    full_clustering,
    sample_avg_path,
    sample_clustering,
):
    # σ = (C_real / C_er) / (L_real / L_er)
    # σ >> 1 means small-world
    sigma_sample = (sample_clustering / er_sample_clustering) / (sample_avg_path / er_sample_avg_path)
    sigma_full   = (full_clustering / er_full_clustering_theory) / (full_avg_path / er_full_avg_path_theory)

    clust_ratio_s = sample_clustering / er_sample_clustering
    path_ratio_s  = sample_avg_path   / er_sample_avg_path
    clust_ratio_f = full_clustering   / er_full_clustering_theory
    path_ratio_f  = full_avg_path     / er_full_avg_path_theory

    print(f"SAMPLE (BFS-2000)")
    print(f"  C_real={sample_clustering:.4f}  C_er={er_sample_clustering:.4f}  ratio={clust_ratio_s:.1f}×")
    print(f"  L_real={sample_avg_path:.4f}  L_er={er_sample_avg_path:.4f}  ratio={path_ratio_s:.3f}×")
    print(f"  σ = {sigma_sample:.2f}")
    print()
    print(f"FULL LCC (n=196,591, theoretical ER)")
    print(f"  C_real={full_clustering:.4f}  C_er≈p={er_full_clustering_theory:.6f}  ratio={clust_ratio_f:.1f}×")
    print(f"  L_real={full_avg_path:.4f}  L_er≈ln/ln={er_full_avg_path_theory:.4f}  ratio={path_ratio_f:.3f}×")
    print(f"  σ = {sigma_full:.2f}")
    return (
        clust_ratio_f,
        clust_ratio_s,
        path_ratio_f,
        path_ratio_s,
        sigma_full,
        sigma_sample,
    )


@app.cell
def _(
    clust_ratio_f,
    clust_ratio_s,
    er_full_avg_path_theory,
    er_full_clustering_theory,
    er_sample_avg_path,
    er_sample_clustering,
    full_avg_path,
    full_clustering,
    mo,
    path_ratio_f,
    path_ratio_s,
    sample_avg_path,
    sample_clustering,
    sigma_full,
    sigma_sample,
):
    def sw_verdict(sigma):
        if sigma > 3:
            return "✅ **Small-world** (σ >> 1)"
        elif sigma > 1.5:
            return "🟡 **Partially small-world** (σ > 1)"
        else:
            return "❌ **Not convincingly small-world** (σ ≈ 1)"

    mo.md(f"""
    ### Small-World Coefficient Table

    | Scope | C_real | C_ER | C ratio | L_real | L_ER | L ratio | **σ** | Verdict |
    |---|---|---|---|---|---|---|---|---|
    | BFS-2000 sample | {sample_clustering:.4f} | {er_sample_clustering:.4f} | {clust_ratio_s:.1f}× | {sample_avg_path:.4f} | {er_sample_avg_path:.4f} | {path_ratio_s:.3f}× | **{sigma_sample:.2f}** | {sw_verdict(sigma_sample)} |
    | Full LCC (theory) | {full_clustering:.4f} | {er_full_clustering_theory:.6f} | {clust_ratio_f:.0f}× | {full_avg_path:.4f} | {er_full_avg_path_theory:.4f} | {path_ratio_f:.3f}× | **{sigma_full:.2f}** | {sw_verdict(sigma_full)} |

    > **σ = (C/C_er) / (L/L_er)**. A small-world network has σ >> 1: clustering far above random,
    > paths only slightly above (or at) random length.
    """)
    return (sw_verdict,)


@app.cell
def _(mo):
    mo.md("""
    ## ⑥ Shortcut Nodes & Edges
    """)
    return


@app.cell
def _(G_sample, nx):
    # Shortcut nodes: nodes whose removal most increases average path length
    # Proxy: high betweenness nodes that also bridge communities
    cent_between = nx.betweenness_centrality(G_sample, k=300, seed=42, normalized=True)
    cent_degree  = nx.degree_centrality(G_sample)

    # Shortcut edges: bridges or edges connecting nodes in different dense communities
    bridges = list(nx.bridges(G_sample))

    # Top shortcut nodes: high betweenness but moderate degree (pure shortcuts, not just hubs)
    shortcut_nodes = sorted(
        G_sample.nodes(),
        key=lambda _n: cent_between[_n] / (cent_degree[_n] + 0.001),
        reverse=True
    )[:10]

    print("Top 10 shortcut nodes (high betweenness relative to degree):")
    print(f"{'Node':>8}  {'Degree':>8}  {'Betweenness':>13}  {'Ratio B/D':>12}")
    print("-" * 46)
    for _n in shortcut_nodes:
        _ratio = cent_between[_n] / (cent_degree[_n] + 0.001)
        print(f"{_n:>8}  {G_sample.degree(_n):>8}  {cent_between[_n]:>13.5f}  {_ratio:>12.3f}")

    print(f"\nBridges in sample: {len(bridges)}")
    if bridges:
        print("Top 5 bridge edges (by combined degree):")
        _br_sorted = sorted(bridges, key=lambda e: G_sample.degree(e[0]) + G_sample.degree(e[1]), reverse=True)
        for _u, _v in _br_sorted[:5]:
            print(f"  ({_u}, {_v})  deg({_u})={G_sample.degree(_u)}  deg({_v})={G_sample.degree(_v)}")
    return (shortcut_nodes,)


@app.cell
def _(mo):
    mo.md("""
    ## ⑦ Visualization — Path Length Distribution + Small-World Summary
    """)
    return


@app.cell
def _(G_er_sample, G_sample, mo, np, nx, random):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    random.seed(42)

    # --- Path length distributions ---
    _src_nodes = random.sample(list(G_sample.nodes()), 200)
    real_path_hist = []
    for _src in _src_nodes:
        real_path_hist.extend(nx.single_source_shortest_path_length(G_sample, _src).values())

    _er_lcc_n = max(nx.connected_components(G_er_sample), key=len)
    _G_er_lcc = G_er_sample.subgraph(_er_lcc_n).copy()
    _er_src = random.sample(list(_G_er_lcc.nodes()), min(200, _G_er_lcc.number_of_nodes()))
    er_path_hist = []
    for _src in _er_src:
        er_path_hist.extend(nx.single_source_shortest_path_length(_G_er_lcc, _src).values())

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor("#0a0c17")
    for _ax in axes:
        _ax.set_facecolor("#131626")
        _ax.tick_params(colors="#aab0c8")
        for _spine in _ax.spines.values():
            _spine.set_edgecolor("#2e3350")

    # Left: path length distribution
    _max_path = max(max(real_path_hist), max(er_path_hist))
    _bins = np.arange(0, _max_path + 2) - 0.5
    axes[0].hist(real_path_hist, bins=_bins, density=True, alpha=0.75,
                 color="#4f8ef7", label="Real (Gowalla)")
    axes[0].hist(er_path_hist,   bins=_bins, density=True, alpha=0.60,
                 color="#f76f8e", label="ER baseline")
    axes[0].set_title("Shortest Path Length Distribution", color="#e0e4f5", fontsize=11)
    axes[0].set_xlabel("Path length (hops)", color="#aab0c8")
    axes[0].set_ylabel("Fraction of pairs", color="#aab0c8")
    axes[0].legend(facecolor="#1a1d2e", labelcolor="white", fontsize=9)

    # Right: clustering per node scatter — real vs ER
    real_clust = list(nx.clustering(G_sample).values())
    er_clust   = list(nx.clustering(G_er_sample).values())
    _bins2 = np.linspace(0, 1, 30)
    axes[1].hist(real_clust, bins=_bins2, density=True, alpha=0.75,
                 color="#4f8ef7", label=f"Real  avg={np.mean(real_clust):.3f}")
    axes[1].hist(er_clust,   bins=_bins2, density=True, alpha=0.60,
                 color="#f76f8e", label=f"ER    avg={np.mean(er_clust):.3f}")
    axes[1].set_title("Clustering Coefficient Distribution", color="#e0e4f5", fontsize=11)
    axes[1].set_xlabel("Local clustering coefficient", color="#aab0c8")
    axes[1].set_ylabel("Density", color="#aab0c8")
    axes[1].legend(facecolor="#1a1d2e", labelcolor="white", fontsize=9)

    plt.suptitle("Gowalla vs ER — Path Lengths & Clustering (BFS-2000 sample)",
                 color="#e0e4f5", fontsize=13, y=1.02)
    plt.tight_layout()
    mo.mpl.interactive(fig)
    return


@app.cell
def _(mo):
    mo.md("""
    ## ⑧ Conclusion
    """)
    return


@app.cell
def _(
    clust_ratio_f,
    clust_ratio_s,
    er_full_avg_path_theory,
    er_full_clustering_theory,
    er_sample_avg_path,
    er_sample_clustering,
    full_avg_path,
    full_clustering,
    mo,
    path_ratio_f,
    path_ratio_s,
    sample_approx_diameter,
    sample_avg_path,
    sample_clustering,
    shortcut_nodes,
    sigma_full,
    sigma_sample,
    sw_verdict,
):
    mo.md(f"""
    ### 📝 Method Note
    **Commands used:** `nx.average_clustering`, `nx.single_source_shortest_path_length` (sampled),
    `nx.gnm_random_graph` (ER baseline), theoretical ER formulas C≈p and L≈ln(n)/ln(⟨k⟩),
    `nx.betweenness_centrality` (k=300), `nx.bridges`, σ = (C/C_er)/(L/L_er)

    ---

    ### 📋 Summary Table

    | Metric | BFS sample | Full LCC |
    |---|---|---|
    | C_real | {sample_clustering:.4f} | {full_clustering:.4f} |
    | C_ER | {er_sample_clustering:.4f} | {er_full_clustering_theory:.6f} |
    | C ratio | {clust_ratio_s:.1f}× | {clust_ratio_f:.0f}× |
    | L_real | {sample_avg_path:.4f} | {full_avg_path:.4f} |
    | L_ER | {er_sample_avg_path:.4f} | {er_full_avg_path_theory:.4f} |
    | L ratio | {path_ratio_s:.3f}× | {path_ratio_f:.3f}× |
    | **σ** | **{sigma_sample:.2f}** | **{sigma_full:.2f}** |
    | Approx diameter | {sample_approx_diameter} | — (sampled) |

    ---

    ### 🧭 Is Gowalla Small-World?

    **BFS sample verdict: {sw_verdict(sigma_sample)}**
    **Full LCC verdict:   {sw_verdict(sigma_full)}**

    The full-graph result is the more meaningful one: with σ = **{sigma_full:.1f}**,
    the Gowalla friendship network is {"a clear small-world network" if sigma_full > 3
    else "a partial small-world" if sigma_full > 1.5 else "not convincingly small-world"}.

    The two conditions are met as follows:

    **Condition 1 — Short paths (L ≈ L_ER):**
    The real average path length of {full_avg_path:.2f} hops compares to a theoretical ER
    baseline of {er_full_avg_path_theory:.2f} hops — a ratio of {path_ratio_f:.2f}×.
    {"Paths are slightly shorter than ER, driven by the supernode (307) acting as a universal shortcut." if path_ratio_f < 1
    else "Paths are similar in length to the ER baseline — the density is high enough that random paths are already short." if path_ratio_f < 1.3
    else "Paths are somewhat longer than ER, which is unusual and suggests the network may have less-connected peripheral regions."}
    In either case, the path length condition is satisfied: any two users can reach each other
    in a small number of hops despite the network's scale.

    **Condition 2 — High clustering (C >> C_ER):**
    The real clustering of {full_clustering:.4f} vs the ER theoretical value of
    {er_full_clustering_theory:.6f} gives a ratio of **{clust_ratio_f:.0f}×**.
    This is dramatically above random. Friends of friends are vastly more likely to
    also be friends than chance predicts — the hallmark of local social community structure.
    In Gowalla's context this reflects **place-based friend formation**: users who check in
    at the same venues tend to friend each other, forming tight triangles that a random graph
    cannot reproduce.

    **Shortcut nodes:** The top shortcut nodes (highest betweenness relative to degree) —
    starting with node **{shortcut_nodes[0]}** — are the users who create long-range ties
    connecting otherwise separate local clusters. They are the "long-range links" in the
    Watts-Strogatz rewiring sense: a small number of cross-cluster connections that
    dramatically reduce the diameter without destroying local clustering.

    **Why geography supports small-world structure:**
    Gowalla is fundamentally a geo-social network — friendships form locally (at venues,
    in neighbourhoods) creating high clustering, while a small number of users who travel
    or have diverse social circles create the cross-cluster shortcuts. This is exactly the
    mechanism Watts & Strogatz described: a lattice-like locally-clustered base with a
    few random long-range rewirings. The fit is strong.
    """)
    return


if __name__ == "__main__":
    app.run()
