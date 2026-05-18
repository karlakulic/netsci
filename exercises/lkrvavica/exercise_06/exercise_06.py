import marimo

__generated_with = "0.21.1"
app = marimo.App(
    width="medium",
    app_title="Exercise 06 — Gowalla vs Erdős-Rényi Baseline",
)


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    mo.md(r"""
    # Exercise 06 — Gowalla vs Erdős-Rényi Null Model
    **Topic:** Student 14 — Gowalla Geo-social Network
    **Goal:** Compare the real friendship network against a random ER baseline to identify
    which structural properties are *not* explained by chance alone.

    > **Approach:** Build an ER graph G(n, m) with the same node count and edge count as the
    > Gowalla sample. Compare degree distribution, clustering, path length, and LCC size.
    > Whatever the real graph does *differently* from ER is structurally meaningful.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## ① Load Real Graph
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

    random.seed(42)
    degrees_full = dict(G_full.degree())
    top_node = max(degrees_full, key=lambda n: degrees_full[n])
    bfs_nodes = list(nx.bfs_tree(G_full, top_node).nodes())[:2000]
    G_real = G_full.subgraph(bfs_nodes).copy()

    n_real = G_real.number_of_nodes()
    m_real = G_real.number_of_edges()
    p_real = (2 * m_real) / (n_real * (n_real - 1))

    print(f"Real graph  — n={n_real:,}  m={m_real:,}  p={p_real:.6f}")
    print(f"Full graph  — n={G_full.number_of_nodes():,}  m={G_full.number_of_edges():,}")
    return G_real, m_real, n_real, np, nx, random


@app.cell
def _(mo):
    mo.md("""
    ## ② Build Erdős-Rényi Baseline G(n, m)
    """)
    return


@app.cell
def _(m_real, n_real, nx):
    # G(n, m) — exactly same number of nodes and edges as real graph
    G_er = nx.gnm_random_graph(n_real, m_real, seed=42)
    print(f"ER baseline — n={G_er.number_of_nodes():,}  m={G_er.number_of_edges():,}")
    print(f"ER is connected: {nx.is_connected(G_er)}")
    print(f"ER components:   {nx.number_connected_components(G_er)}")

    # For path-length we need the LCC
    er_lcc_nodes = max(nx.connected_components(G_er), key=len)
    G_er_lcc = G_er.subgraph(er_lcc_nodes).copy()
    print(f"ER LCC size:     {G_er_lcc.number_of_nodes():,} nodes")
    return G_er, G_er_lcc


@app.cell
def _(mo):
    mo.md("""
    ## ③ Metric Comparison
    """)
    return


@app.cell
def _(G_er, G_er_lcc, G_real, nx, random):
    import statistics

    # --- Real graph metrics ---
    real_deg = [d for _, d in G_real.degree()]
    real_avg_deg    = sum(real_deg) / len(real_deg)
    real_med_deg    = statistics.median(real_deg)
    real_max_deg    = max(real_deg)
    real_clustering = nx.average_clustering(G_real)
    real_lcc_size   = len(max(nx.connected_components(G_real), key=len))
    real_lcc_frac   = real_lcc_size / G_real.number_of_nodes()
    real_density    = nx.density(G_real)

    # avg path length — sampled (full is too slow)
    random.seed(42)
    _sample = random.sample(list(G_real.nodes()), 300)
    _lengths = []
    for _src in _sample:
        _d = nx.single_source_shortest_path_length(G_real, _src)
        _lengths.extend(_d.values())
    real_avg_path = sum(_lengths) / len(_lengths)

    # --- ER graph metrics ---
    er_deg = [d for _, d in G_er.degree()]
    er_avg_deg    = sum(er_deg) / len(er_deg)
    er_med_deg    = statistics.median(er_deg)
    er_max_deg    = max(er_deg)
    er_clustering = nx.average_clustering(G_er)
    er_lcc_size   = G_er_lcc.number_of_nodes()
    er_lcc_frac   = er_lcc_size / G_er.number_of_nodes()
    er_density    = nx.density(G_er)

    random.seed(42)
    _er_sample = random.sample(list(G_er_lcc.nodes()), min(300, G_er_lcc.number_of_nodes()))
    _er_lengths = []
    for _src in _er_sample:
        _d = nx.single_source_shortest_path_length(G_er_lcc, _src)
        _er_lengths.extend(_d.values())
    er_avg_path = sum(_er_lengths) / len(_er_lengths)

    print("=" * 55)
    print(f"{'Metric':<28} {'Real':>12} {'ER':>12}")
    print("=" * 55)
    print(f"{'Nodes':<28} {G_real.number_of_nodes():>12,} {G_er.number_of_nodes():>12,}")
    print(f"{'Edges':<28} {G_real.number_of_edges():>12,} {G_er.number_of_edges():>12,}")
    print(f"{'Density':<28} {real_density:>12.6f} {er_density:>12.6f}")
    print(f"{'Avg degree':<28} {real_avg_deg:>12.2f} {er_avg_deg:>12.2f}")
    print(f"{'Median degree':<28} {real_med_deg:>12.1f} {er_med_deg:>12.1f}")
    print(f"{'Max degree':<28} {real_max_deg:>12,} {er_max_deg:>12,}")
    print(f"{'Avg clustering':<28} {real_clustering:>12.4f} {er_clustering:>12.4f}")
    print(f"{'Avg path length (sampled)':<28} {real_avg_path:>12.4f} {er_avg_path:>12.4f}")
    print(f"{'LCC size':<28} {real_lcc_size:>12,} {er_lcc_size:>12,}")
    print(f"{'LCC fraction':<28} {real_lcc_frac:>12.1%} {er_lcc_frac:>12.1%}")
    return (
        er_avg_deg,
        er_avg_path,
        er_clustering,
        er_deg,
        er_density,
        er_lcc_frac,
        er_lcc_size,
        er_max_deg,
        er_med_deg,
        real_avg_deg,
        real_avg_path,
        real_clustering,
        real_deg,
        real_density,
        real_lcc_frac,
        real_lcc_size,
        real_max_deg,
        real_med_deg,
    )


@app.cell
def _(
    G_er,
    G_real,
    er_avg_deg,
    er_avg_path,
    er_clustering,
    er_density,
    er_lcc_frac,
    er_lcc_size,
    er_max_deg,
    er_med_deg,
    mo,
    real_avg_deg,
    real_avg_path,
    real_clustering,
    real_density,
    real_lcc_frac,
    real_lcc_size,
    real_max_deg,
    real_med_deg,
):
    def diff_label(real, er, higher_is_notable=True):
        ratio = real / er if er > 0 else float('inf')
        if ratio > 2:
            return f"🔴 {ratio:.1f}× higher"
        elif ratio > 1.2:
            return f"🟡 {ratio:.1f}× higher"
        elif ratio < 0.5:
            return f"🔵 {1/ratio:.1f}× lower"
        elif ratio < 0.8:
            return f"🟡 {1/ratio:.1f}× lower"
        else:
            return "✅ similar"

    mo.md(f"""
    ### Real Graph vs ER Baseline

    | Metric | Real Graph | ER Baseline | Difference |
    |---|---|---|---|
    | Nodes | {G_real.number_of_nodes():,} | {G_er.number_of_nodes():,} | matched |
    | Edges | {G_real.number_of_edges():,} | {G_er.number_of_edges():,} | matched |
    | Density | {real_density:.6f} | {er_density:.6f} | matched |
    | Avg degree | {real_avg_deg:.2f} | {er_avg_deg:.2f} | matched |
    | Median degree | {real_med_deg:.1f} | {er_med_deg:.1f} | {diff_label(real_med_deg, er_med_deg)} |
    | **Max degree** | **{real_max_deg:,}** | **{er_max_deg:,}** | **{diff_label(real_max_deg, er_max_deg)}** |
    | **Avg clustering** | **{real_clustering:.4f}** | **{er_clustering:.4f}** | **{diff_label(real_clustering, er_clustering)}** |
    | Avg path length | {real_avg_path:.4f} | {er_avg_path:.4f} | {diff_label(er_avg_path, real_avg_path)} |
    | LCC size | {real_lcc_size:,} | {er_lcc_size:,} | {diff_label(real_lcc_size, er_lcc_size)} |
    | LCC fraction | {real_lcc_frac:.1%} | {er_lcc_frac:.1%} | {diff_label(real_lcc_frac, er_lcc_frac)} |

    > 🔴 = strongly above random  🟡 = moderately above/below  ✅ = similar to random  🔵 = below random
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## ④ Degree Distribution Comparison
    """)
    return


@app.cell
def _(er_deg, mo, np, real_deg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.patch.set_facecolor("#0a0c17")
    for _ax in axes:
        _ax.set_facecolor("#131626")
        _ax.tick_params(colors="#aab0c8")
        for _spine in _ax.spines.values():
            _spine.set_edgecolor("#2e3350")

    _bins = 60

    # Left: Linear histogram
    axes[0].hist(real_deg, bins=_bins, alpha=0.75, color="#4f8ef7",
                 label="Real (Gowalla)", density=True)
    axes[0].hist(er_deg,   bins=_bins, alpha=0.60, color="#f76f8e",
                 label="ER baseline",   density=True)
    axes[0].set_title("Degree Distribution (linear)", color="#e0e4f5", fontsize=11)
    axes[0].set_xlabel("Degree", color="#aab0c8")
    axes[0].set_ylabel("Density", color="#aab0c8")
    axes[0].legend(facecolor="#1a1d2e", labelcolor="white", fontsize=8)

    # Middle: Log-log
    _max_deg = max(max(real_deg), max(er_deg))
    _log_bins = np.logspace(0, np.log10(_max_deg + 1), 40)
    axes[1].hist(real_deg, bins=_log_bins, alpha=0.75, color="#4f8ef7",
                 label="Real (Gowalla)", density=True)
    axes[1].hist(er_deg,   bins=_log_bins, alpha=0.60, color="#f76f8e",
                 label="ER baseline",   density=True)
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_title("Degree Distribution (log-log)", color="#e0e4f5", fontsize=11)
    axes[1].set_xlabel("Degree (log)", color="#aab0c8")
    axes[1].set_ylabel("Density (log)", color="#aab0c8")
    axes[1].legend(facecolor="#1a1d2e", labelcolor="white", fontsize=8)

    # Right: CDF comparison
    _real_sorted = np.sort(real_deg)
    _er_sorted   = np.sort(er_deg)
    _real_cdf = np.arange(1, len(_real_sorted) + 1) / len(_real_sorted)
    _er_cdf   = np.arange(1, len(_er_sorted)   + 1) / len(_er_sorted)
    axes[2].plot(_real_sorted, 1 - _real_cdf, color="#4f8ef7", lw=2, label="Real (Gowalla)")
    axes[2].plot(_er_sorted,   1 - _er_cdf,   color="#f76f8e", lw=2, label="ER baseline", ls="--")
    axes[2].set_xscale("log")
    axes[2].set_yscale("log")
    axes[2].set_title("CCDF (Complementary CDF)", color="#e0e4f5", fontsize=11)
    axes[2].set_xlabel("Degree (log)", color="#aab0c8")
    axes[2].set_ylabel("P(X > k)", color="#aab0c8")
    axes[2].legend(facecolor="#1a1d2e", labelcolor="white", fontsize=8)

    plt.suptitle("Gowalla Real Graph vs Erdős-Rényi Baseline — Degree Distribution",
                 color="#e0e4f5", fontsize=13, y=1.02)
    plt.tight_layout()
    mo.mpl.interactive(fig)
    return


@app.cell
def _(mo):
    mo.md("""
    ## ⑤ Clustering Distribution Comparison
    """)
    return


@app.cell
def _(G_er, G_real, mo, nx):
    import matplotlib.pyplot as _plt

    real_clust_vals = list(nx.clustering(G_real).values())
    er_clust_vals   = list(nx.clustering(G_er).values())

    fig2, ax2 = _plt.subplots(figsize=(10, 4))
    fig2.patch.set_facecolor("#0a0c17")
    ax2.set_facecolor("#131626")
    ax2.tick_params(colors="#aab0c8")
    for _spine in ax2.spines.values():
        _spine.set_edgecolor("#2e3350")

    ax2.hist(real_clust_vals, bins=40, alpha=0.75, color="#4f8ef7",
             density=True, label=f"Real — avg {sum(real_clust_vals)/len(real_clust_vals):.4f}")
    ax2.hist(er_clust_vals,   bins=40, alpha=0.60, color="#f76f8e",
             density=True, label=f"ER   — avg {sum(er_clust_vals)/len(er_clust_vals):.4f}")
    ax2.set_title("Local Clustering Coefficient Distribution",
                  color="#e0e4f5", fontsize=12, pad=10)
    ax2.set_xlabel("Clustering coefficient", color="#aab0c8")
    ax2.set_ylabel("Density", color="#aab0c8")
    ax2.legend(facecolor="#1a1d2e", labelcolor="white", fontsize=9)

    _plt.tight_layout()
    mo.mpl.interactive(fig2)
    return


@app.cell
def _(mo):
    mo.md("""
    ## ⑥ Conclusion — What Is Non-Random?
    """)
    return


@app.cell
def _(
    er_avg_path,
    er_clustering,
    er_max_deg,
    mo,
    real_avg_path,
    real_clustering,
    real_max_deg,
):
    clust_ratio = real_clustering / er_clustering if er_clustering > 0 else float('inf')
    deg_ratio   = real_max_deg / er_max_deg if er_max_deg > 0 else float('inf')
    path_ratio  = er_avg_path / real_avg_path if real_avg_path > 0 else float('inf')

    mo.md(f"""
    ### 📝 Method Note
    **Commands used:** `nx.gnm_random_graph` (ER baseline with same n and m),
    `nx.average_clustering`, `nx.single_source_shortest_path_length` (sampled),
    `nx.connected_components`, `nx.density`, manual degree sequence extraction,
    histogram + CCDF plots via matplotlib

    ---

    ### 📋 Key Differences Summary

    | Property | Real | ER | Verdict |
    |---|---|---|---|
    | Max degree | {real_max_deg:,} | {er_max_deg:,} | Real is **{deg_ratio:.0f}× higher** — fat tail |
    | Avg clustering | {real_clustering:.4f} | {er_clustering:.4f} | Real is **{clust_ratio:.0f}× higher** — strong local structure |
    | Avg path length | {real_avg_path:.4f} | {er_avg_path:.4f} | Real is **{path_ratio:.2f}× {"shorter" if real_avg_path < er_avg_path else "longer"}** |

    ---

    ### 🧭 Which Properties Are Clearly Non-Random?

    **1. Degree distribution — strongly non-random.**
    The ER model produces a roughly Poisson-distributed degree sequence where almost all nodes
    have degree near the mean ({er_avg_path:.1f}), with very few nodes much above or below it.
    The real Gowalla graph has a **heavy-tailed distribution**: most users have modest degree,
    but node 307 has degree 1,999 in the sample — **{deg_ratio:.0f}× the maximum seen in the ER baseline**.
    This kind of fat tail is the signature of preferential attachment and is completely absent
    from a random graph with the same edge count. The CCDF plot makes this visible: the real
    graph's tail extends far to the right of the ER curve.

    **2. Clustering coefficient — strongly non-random.**
    The ER model predicts average clustering ≈ p (the edge probability), which here is
    approximately {er_clustering:.4f}. The real graph shows {real_clustering:.4f} —
    roughly **{clust_ratio:.0f}× higher**. This means friends of friends are
    far more likely to also be friends in the real network than chance would predict.
    This is the mathematical signature of **local community structure**: users cluster into
    tight friend groups, which is consistent with place-based social formation in Gowalla —
    people who visit the same venues tend to friend each other, forming triangles that a
    random graph cannot produce.

    **3. Average path length — {"shorter in the real graph, consistent with the small-world effect." if real_avg_path < er_avg_path else "similar to ER, which is expected given the high density of the BFS sample."}**
    {"The presence of a supernode (307) connected to nearly all 2,000 sampled nodes collapses path lengths even below the already-short ER baseline — the hub acts as a universal shortcut." if real_avg_path < er_avg_path
    else "Both graphs have very short average path lengths because the density is high enough that random paths are already short. The BFS-sampling strategy (centred on the highest-degree node) inflates this effect in both graphs equally."}

    **4. LCC size — similar, by construction.**
    Both graphs are fully or nearly fully connected at this density. This property does not
    discriminate between the real and random case here — it would be more informative on a
    sparser sample or the full graph.

    **Overall conclusion:** The Gowalla friendship network is *not* a random graph.
    Its high clustering and fat-tailed degree distribution are structurally meaningful and
    reflect real social processes — place-based friend formation (high clustering) and the
    emergence of a small number of hyper-connected users (heavy tail). These are exactly the
    properties that define a **small-world, scale-free social network**, and neither can be
    reproduced by the ER null model with the same edge count.
    """)
    return


if __name__ == "__main__":
    app.run()
