import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Exercise 08: Degree Distribution and Scale-Free Test for a Facebook Ego Network

    This notebook keeps the same SNAP Facebook ego network used in the earlier
    `mkatavic` exercises: ego node **698**.

    Goal:
    study degree inequality, hubs, and the plausibility of scale-free structure
    in this ego neighborhood. Specifically, measure whether the local network is
    centered on the ego only or also contains secondary hubs.

    Required input:
    `data/facebook/698.edges`

    Expected output:
    a degree-distribution figure (with log-log view), a top-hubs table, a
    Barabási-Albert baseline comparison, and a short statement on whether
    scale-free language is justified.
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    import pandas as pd
    from networkx.algorithms import community as nx_comm
    return Path, np, nx, nx_comm, pd, plt


@app.cell
def _(Path):
    EGO_ID = 698
    BA_SAMPLE_COUNT = 200
    RANDOM_SEED = 698

    def resolve_data_dir():
        candidates = []

        if "__file__" in globals():
            notebook_dir = Path(__file__).resolve().parent
            candidates.extend(
                [
                    notebook_dir / "facebook",
                    notebook_dir.parent / "data" / "facebook",
                    notebook_dir.parent / "facebook",
                ]
            )

        cwd = Path.cwd()
        candidates.extend(
            [
                cwd / "facebook",
                cwd / "exercises" / "mkatavic" / "data" / "facebook",
                cwd / "exercises" / "mkatavic" / "exercise_08" / "facebook",
            ]
        )

        for data_dir in candidates:
            if (data_dir / f"{EGO_ID}.edges").exists():
                return data_dir

        searched = "\n".join(str(candidate) for candidate in candidates)
        raise FileNotFoundError(
            "Could not find the Facebook ego data directory. Searched:\n"
            f"{searched}"
        )

    DATA_DIR = resolve_data_dir()
    EDGE_PATH = DATA_DIR / f"{EGO_ID}.edges"
    return BA_SAMPLE_COUNT, EDGE_PATH, EGO_ID, RANDOM_SEED


@app.cell
def _(nx):
    def load_ego_network(edge_path, ego_id):
        alter_graph = nx.read_edgelist(
            edge_path,
            nodetype=int,
            create_using=nx.Graph(),
        )
        alters = sorted(alter_graph.nodes())

        graph = alter_graph.copy()
        graph.add_node(ego_id)
        graph.add_edges_from((ego_id, alter) for alter in alters)

        return graph, alter_graph

    def degree_frequency(graph, label, pd_module):
        degree_counts = (
            pd_module.Series(dict(graph.degree()), dtype=int)
            .value_counts()
            .sort_index()
        )
        df = pd_module.DataFrame(
            {
                "degree": degree_counts.index.astype(int),
                "count": degree_counts.values.astype(int),
                "graph": label,
            }
        )
        total_nodes = graph.number_of_nodes()
        df["probability"] = df["count"] / total_nodes
        return df

    def top_hubs_table(graph, top_k, pd_module):
        degrees = sorted(graph.degree(), key=lambda x: (-x[1], x[0]))
        betweenness = nx.betweenness_centrality(graph)
        rows = []
        for node, deg in degrees[:top_k]:
            rows.append(
                {
                    "node": node,
                    "degree": deg,
                    "betweenness": betweenness[node],
                    "pct_of_total": deg / (graph.number_of_nodes() - 1),
                }
            )
        return pd_module.DataFrame(rows)

    return degree_frequency, load_ego_network, top_hubs_table


@app.cell
def _(EDGE_PATH, EGO_ID, load_ego_network, nx):
    G, alter_graph = load_ego_network(EDGE_PATH, EGO_ID)
    return G, alter_graph


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Graph Overview
    """)
    return


@app.cell
def _(G, alter_graph, nx, pd):
    graph_stats = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": nx.density(G),
        "avg degree": np.mean([d for _, d in G.degree()]),
        "max degree": max(d for _, d in G.degree()),
        "avg clustering": nx.average_clustering(G),
    }

    alter_stats = {
        "alter nodes": alter_graph.number_of_nodes(),
        "alter edges": alter_graph.number_of_edges(),
        "alter density": nx.density(alter_graph),
        "alter avg degree": np.mean([d for _, d in alter_graph.degree()]),
        "alter max degree": max(d for _, d in alter_graph.degree()),
        "alter avg clustering": nx.average_clustering(alter_graph),
    }

    stats_df = pd.DataFrame([graph_stats, alter_stats])
    stats_df.index = ["Full ego graph", "Alter-only graph"]
    stats_df.round(4)
    return alter_stats, graph_stats, stats_df


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Degree Distribution

    The plot below shows the degree distribution for both the full ego graph
    (which includes ego node 698 connected to all alters) and the alter-only
    graph (which reveals structure among friends without the ego hub).
    """)
    return


@app.cell
def _(EGO_ID, degree_frequency, pd, plt, alter_graph, G):
    full_freq = degree_frequency(G, "Full ego graph", pd)
    alter_freq = degree_frequency(alter_graph, "Alter-only graph", pd)

    _fig_linear, _axes_linear = plt.subplots(1, 2, figsize=(12, 5))

    palette = {"Full ego graph": "#D1495B", "Alter-only graph": "#00798C"}

    for _ax_lin, (freq_df, title) in zip(
        _axes_linear,
        [(full_freq, "Full ego graph (linear)"), (alter_freq, "Alter-only graph (linear)")],
    ):
        _ax_lin.plot(
            freq_df["degree"],
            freq_df["count"],
            marker="o",
            markersize=5,
            linewidth=2,
            color=palette[freq_df["graph"].iloc[0]],
            label=freq_df["graph"].iloc[0],
        )
        _ax_lin.set_xlabel("degree k")
        _ax_lin.set_ylabel("count N(k)")
        _ax_lin.set_title(title)
        _ax_lin.grid(alpha=0.22, linewidth=0.6)
        _ax_lin.set_xlim(left=0)

    _fig_linear.tight_layout()
    _fig_linear
    return alter_freq, full_freq


@app.cell
def _(alter_freq, full_freq, plt):
    _fig_loglog, _axes_loglog = plt.subplots(1, 2, figsize=(12, 5))

    _palette_full = "#D1495B"
    _palette_alter = "#00798C"

    _valid_full_loglog = full_freq[full_freq["probability"] > 0]
    _valid_alter_loglog = alter_freq[alter_freq["probability"] > 0]

    _axes_loglog[0].scatter(
        _valid_full_loglog["degree"],
        _valid_full_loglog["probability"],
        s=50,
        color=_palette_full,
        zorder=3,
    )
    _axes_loglog[0].set_xscale("log")
    _axes_loglog[0].set_yscale("log")
    _axes_loglog[0].set_xlabel("degree k (log)")
    _axes_loglog[0].set_ylabel("P(k) (log)")
    _axes_loglog[0].set_title("Full ego graph (log-log)")
    _axes_loglog[0].grid(alpha=0.22, linewidth=0.6, which="both")

    _axes_loglog[1].scatter(
        _valid_alter_loglog["degree"],
        _valid_alter_loglog["probability"],
        s=50,
        color=_palette_alter,
        zorder=3,
    )
    _axes_loglog[1].set_xscale("log")
    _axes_loglog[1].set_yscale("log")
    _axes_loglog[1].set_xlabel("degree k (log)")
    _axes_loglog[1].set_ylabel("P(k) (log)")
    _axes_loglog[1].set_title("Alter-only graph (log-log)")
    _axes_loglog[1].grid(alpha=0.22, linewidth=0.6, which="both")

    _fig_loglog.tight_layout()
    _fig_loglog
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Top Hubs

    This table lists the highest-degree nodes in the full ego graph. The ego
    node (698) is included for completeness but should be interpreted cautiously
    since it connects to every alter by construction. The alter-only hubs are the
    more meaningful signal for secondary hub structure.
    """)
    return


@app.cell
def _(EGO_ID, G, pd, top_hubs_table):
    hubs_df = top_hubs_table(G, 10, pd)
    hubs_df_display = hubs_df.copy()
    hubs_df_display["node"] = hubs_df_display["node"].apply(
        lambda x: f"{x} (ego)" if x == EGO_ID else str(x)
    )
    hubs_df_display.round({"betweenness": 5, "pct_of_total": 3})
    return hubs_df, hubs_df_display


@app.cell
def _(alter_graph, pd, top_hubs_table):
    alter_hubs_df = top_hubs_table(alter_graph, 10, pd)
    alter_hubs_df.round({"betweenness": 5, "pct_of_total": 3})
    return alter_hubs_df


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Degree Inequality Metrics

    These metrics quantify how concentrated degree is in the network. A
    perfectly equal network has Gini = 0; a star network approaches Gini = 1.
    The coefficient of variation (CV) measures relative spread of degrees.
    """)
    return


@app.cell
def _(G, alter_graph, np, pd):
    def gini_coefficient(values):
        sorted_vals = np.sort(values)
        n = len(sorted_vals)
        index = np.arange(1, n + 1)
        return (2 * np.sum(index * sorted_vals) - (n + 1) * np.sum(sorted_vals)) / (
            n * np.sum(sorted_vals)
        )

    full_degrees = np.array([d for _, d in G.degree()], dtype=float)
    alter_degrees = np.array([d for _, d in alter_graph.degree()], dtype=float)

    inequality_metrics = pd.DataFrame(
        [
            {
                "graph": "Full ego graph",
                "gini": gini_coefficient(full_degrees),
                "cv": np.std(full_degrees) / np.mean(full_degrees),
                "max_degree_ratio": np.max(full_degrees) / np.mean(full_degrees),
            },
            {
                "graph": "Alter-only graph",
                "gini": gini_coefficient(alter_degrees),
                "cv": np.std(alter_degrees) / np.mean(alter_degrees),
                "max_degree_ratio": np.max(alter_degrees) / np.mean(alter_degrees),
            },
        ]
    ).round(4)
    return alter_degrees, full_degrees, gini_coefficient, inequality_metrics


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Barabási-Albert Baseline Comparison

    The Barabási-Albert model generates scale-free networks through preferential
    attachment. If the ego network were scale-free, its degree distribution should
    resemble a BA network of similar size. I generate BA graphs with the same
    number of nodes and edges (matching the alter graph), then compare degree
    statistics across 200 samples.
    """)
    return


@app.cell
def _(BA_SAMPLE_COUNT, RANDOM_SEED, alter_graph, np, nx, pd):
    n_alter = alter_graph.number_of_nodes()
    m_alter = alter_graph.number_of_edges()

    ba_m = max(1, m_alter // n_alter)

    ba_sample_rows = []
    for i in range(BA_SAMPLE_COUNT):
        ba_graph = nx.barabasi_albert_graph(n_alter, ba_m, seed=RANDOM_SEED + i)
        ba_degrees = np.array([d for _, d in ba_graph.degree()], dtype=float)
        ba_sample_rows.append(
            {
                "mean_degree": ba_degrees.mean(),
                "std_degree": ba_degrees.std(ddof=0),
                "max_degree": ba_degrees.max(),
                "cv": ba_degrees.std(ddof=0) / ba_degrees.mean(),
                "avg_clustering": nx.average_clustering(ba_graph),
            }
        )

    ba_samples_df = pd.DataFrame(ba_sample_rows)
    ba_m
    return ba_m, ba_samples_df, n_alter


@app.cell
def _(alter_degrees, alter_graph, ba_samples_df, np, nx, pd):
    alter_real = {
        "mean_degree": alter_degrees.mean(),
        "std_degree": alter_degrees.std(ddof=0),
        "max_degree": alter_degrees.max(),
        "cv": alter_degrees.std(ddof=0) / alter_degrees.mean(),
        "avg_clustering": nx.average_clustering(alter_graph),
    }

    comparison = pd.DataFrame(
        [
            {
                "metric": "mean degree",
                "real alter graph": alter_real["mean_degree"],
                "BA mean (200 samples)": ba_samples_df["mean_degree"].mean(),
                "BA 5%-95% range": (
                    f"{ba_samples_df['mean_degree'].quantile(0.05):.2f} - "
                    f"{ba_samples_df['mean_degree'].quantile(0.95):.2f}"
                ),
            },
            {
                "metric": "std degree",
                "real alter graph": alter_real["std_degree"],
                "BA mean (200 samples)": ba_samples_df["std_degree"].mean(),
                "BA 5%-95% range": (
                    f"{ba_samples_df['std_degree'].quantile(0.05):.2f} - "
                    f"{ba_samples_df['std_degree'].quantile(0.95):.2f}"
                ),
            },
            {
                "metric": "max degree",
                "real alter graph": alter_real["max_degree"],
                "BA mean (200 samples)": ba_samples_df["max_degree"].mean(),
                "BA 5%-95% range": (
                    f"{ba_samples_df['max_degree'].quantile(0.05):.1f} - "
                    f"{ba_samples_df['max_degree'].quantile(0.95):.1f}"
                ),
            },
            {
                "metric": "CV",
                "real alter graph": alter_real["cv"],
                "BA mean (200 samples)": ba_samples_df["cv"].mean(),
                "BA 5%-95% range": (
                    f"{ba_samples_df['cv'].quantile(0.05):.3f} - "
                    f"{ba_samples_df['cv'].quantile(0.95):.3f}"
                ),
            },
            {
                "metric": "avg clustering",
                "real alter graph": alter_real["avg_clustering"],
                "BA mean (200 samples)": ba_samples_df["avg_clustering"].mean(),
                "BA 5%-95% range": (
                    f"{ba_samples_df['avg_clustering'].quantile(0.05):.3f} - "
                    f"{ba_samples_df['avg_clustering'].quantile(0.95):.3f}"
                ),
            },
        ]
    ).round(3)
    return alter_real, comparison


@app.cell
def _(alter_freq, ba_samples_df, plt, alter_graph, nx, RANDOM_SEED, n_alter, ba_m):
    ba_for_plot = nx.barabasi_albert_graph(n_alter, ba_m, seed=RANDOM_SEED)
    ba_freq_dict = {}
    deg_counts = dict(ba_for_plot.degree())
    for d in deg_counts.values():
        ba_freq_dict[d] = ba_freq_dict.get(d, 0) + 1
    ba_freq_df = pd.DataFrame(
        {
            "degree": list(ba_freq_dict.keys()),
            "probability": [c / n_alter for c in ba_freq_dict.values()],
        }
    ).sort_values("degree")

    _valid_alter_ba = alter_freq[alter_freq["probability"] > 0]

    _fig_ba, _ax_ba = plt.subplots(figsize=(9, 5))

    _ax_ba.scatter(
        _valid_alter_ba["degree"],
        _valid_alter_ba["probability"],
        s=50,
        color="#D1495B",
        zorder=3,
        label="Real alter graph",
    )
    _ax_ba.scatter(
        ba_freq_df["degree"],
        ba_freq_df["probability"],
        s=50,
        color="#00798C",
        zorder=2,
        label="BA baseline",
    )

    _ax_ba.set_xscale("log")
    _ax_ba.set_yscale("log")
    _ax_ba.set_xlabel("degree k (log)")
    _ax_ba.set_ylabel("P(k) (log)")
    _ax_ba.set_title("Degree distribution: alter graph vs. BA baseline (log-log)")
    _ax_ba.grid(alpha=0.22, linewidth=0.6, which="both")
    _ax_ba.legend(frameon=False)

    _fig_ba.tight_layout()
    _fig_ba
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Hubs vs. Earlier Centrality Results

    This section compares the top degree hubs with the top betweenness
    centrality nodes to see whether the same nodes dominate both measures.
    """)
    return


@app.cell
def _(EGO_ID, G, alter_graph, nx, pd):
    alter_betweenness = nx.betweenness_centrality(alter_graph)
    alter_degree = dict(alter_graph.degree())

    top_betweenness = sorted(alter_betweenness.items(), key=lambda x: -x[1])[:10]
    top_degree = sorted(alter_degree.items(), key=lambda x: -x[1])[:10]

    betweenness_nodes = {node for node, _ in top_betweenness}
    degree_nodes = {node for node, _ in top_degree}
    overlap = betweenness_nodes & degree_nodes

    overlap_df = pd.DataFrame(
        [
            {
                "node": node,
                "degree": alter_degree[node],
                "betweenness": alter_betweenness[node],
                "in_top_degree": node in degree_nodes,
                "in_top_betweenness": node in betweenness_nodes,
            }
            for node in sorted(overlap)
        ]
    ).round({"betweenness": 5})

    overlap_count = len(overlap)
    return betweenness_nodes, degree_nodes, overlap_count, overlap_df


@app.cell(hide_code=True)
def _(EGO_ID, G, alter_graph, alter_hubs_df, alter_real, ba_samples_df, comparison, gini_coefficient, inequality_metrics, mo, np, overlap_count):
    alter_degrees_array = np.array([d for _, d in alter_graph.degree()], dtype=float)
    alter_gini = gini_coefficient(alter_degrees_array)
    alter_max_deg = int(alter_degrees_array.max())
    alter_mean_deg = alter_degrees_array.mean()

    ba_max_mean = ba_samples_df["max_degree"].mean()
    ba_max_q95 = ba_samples_df["max_degree"].quantile(0.95)
    ba_clustering_mean = ba_samples_df["avg_clustering"].mean()

    real_clustering = alter_real["avg_clustering"]

    top_alter_node = int(alter_hubs_df.iloc[0]["node"])
    top_alter_degree = int(alter_hubs_df.iloc[0]["degree"])
    second_alter_node = int(alter_hubs_df.iloc[1]["node"])
    second_alter_degree = int(alter_hubs_df.iloc[1]["degree"])

    mo.md(
        f"""
        ## Conclusion

        The Facebook ego network for user **{EGO_ID}** shows **mild to moderate
        degree skew**, but it does **not** present a clean scale-free picture.

        **Ego dominance is structural, not organic**: node {EGO_ID} has degree
        {G.degree(EGO_ID)} because it connects to every alter by construction.
        The more meaningful question is whether the alter-only graph contains
        secondary hubs.

        In the alter-only graph ({alter_graph.number_of_nodes()} nodes), the
        maximum degree is **{alter_max_deg}** with a mean of
        **{alter_mean_deg:.1f}**, giving a max-to-mean ratio of
        **{alter_max_deg / alter_mean_deg:.1f}x**. The Gini coefficient for alter
        degrees is **{alter_gini:.3f}**, indicating moderate inequality. The
        top alter hub is node **{top_alter_node}** (degree {top_alter_degree}),
        followed by node **{second_alter_node}** (degree {second_alter_degree}).
        There are several secondary hubs, not just one dominant alter.

        Against the Barabási-Albert baseline, the real alter graph has
        **lower clustering** ({real_clustering:.3f} vs. BA mean {ba_clustering_mean:.3f})
        and a **less extreme max degree** ({alter_max_deg} vs. BA mean
        {ba_max_mean:.1f}, 95th percentile {ba_max_q95:.1f}). The degree
        CV is also lower than the BA expectation, meaning the real network
        is more evenly distributed than a preferential-attachment model would
        predict.

        The overlap between top-degree and top-betweenness nodes is
        **{overlap_count} out of 10**, indicating that hubs do serve as
        structural bridges, but the relationship is not perfect.

        **Verdict**: this ego neighborhood shows **mild hub dominance** from a
        few secondary connectors, but it is **not strongly scale-free**. The
        preferential attachment story does not fit well here because Facebook
        friendships form through mutual consent and social context (school,
        work, geography), not through a "rich-get-richer" attachment process.
        The degree distribution has a heavy-ish tail but lacks the clean
        power-law straight line that characterizes true scale-free networks.
        Scale-free language is **not well justified** for this ego network.
        """
    )
    return


if __name__ == "__main__":
    app.run()
