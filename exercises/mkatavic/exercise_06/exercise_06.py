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
    # Exercise 06: Facebook Ego Network vs. Erdos-Renyi Baseline

    This notebook keeps the same SNAP Facebook ego network used in the earlier
    `mkatavic` exercises: ego node **698**.

    Goal:
    compare the real local Facebook network with an Erdos-Renyi null model and
    test whether the observed structure is more clustered or more unequal than
    chance.

    Required input:
    `data/facebook/698.edges`

    Expected output:
    a short comparison table, one degree-distribution plot, and a conclusion
    about which properties are clearly non-random.
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    import pandas as pd
    return Path, np, nx, pd, plt


@app.cell
def _(Path):
    BASELINE_SEED = 698
    EGO_ID = 698
    ER_SAMPLE_COUNT = 200

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
                cwd / "exercises" / "mkatavic" / "exercise_06" / "facebook",
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
    return BASELINE_SEED, EDGE_PATH, EGO_ID, ER_SAMPLE_COUNT


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

        return graph

    def largest_component_subgraph(graph, nx_module):
        if graph.number_of_nodes() == 0:
            return graph.copy()

        largest_nodes = max(nx_module.connected_components(graph), key=len)
        return graph.subgraph(largest_nodes).copy()

    def average_path_length_for_comparison(graph, nx_module):
        if graph.number_of_nodes() <= 1:
            return 0.0, "single node", graph.number_of_nodes()

        if nx_module.is_connected(graph):
            return (
                nx_module.average_shortest_path_length(graph),
                "full graph",
                graph.number_of_nodes(),
            )

        largest_component = largest_component_subgraph(graph, nx_module)
        return (
            nx_module.average_shortest_path_length(largest_component),
            "largest connected component",
            largest_component.number_of_nodes(),
        )

    def degree_array(graph, np_module):
        return np_module.array([degree for _, degree in graph.degree()], dtype=float)

    def summarize_graph(graph, label, nx_module, np_module):
        degrees = degree_array(graph, np_module)
        avg_path_length, path_basis, path_nodes = average_path_length_for_comparison(
            graph, nx_module
        )
        largest_component = largest_component_subgraph(graph, nx_module)

        return {
            "graph": label,
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": nx_module.density(graph),
            "average degree": degrees.mean(),
            "median degree": np_module.median(degrees),
            "degree std": degrees.std(ddof=0),
            "max degree": degrees.max(),
            "average clustering": nx_module.average_clustering(graph),
            "transitivity": nx_module.transitivity(graph),
            "average path length": avg_path_length,
            "path-length basis": path_basis,
            "path-length nodes": path_nodes,
            "largest connected component size": largest_component.number_of_nodes(),
            "connected components": nx_module.number_connected_components(graph),
        }

    def degree_frequency_df(graph, label, pd_module):
        degree_counts = (
            pd_module.Series(dict(graph.degree()), dtype=int).value_counts().sort_index()
        )
        return pd_module.DataFrame(
            {
                "degree": degree_counts.index.astype(int),
                "count": degree_counts.values.astype(int),
                "graph": label,
            }
        )
    return degree_frequency_df, load_ego_network, summarize_graph


@app.cell
def _(BASELINE_SEED, EDGE_PATH, EGO_ID, load_ego_network, nx):
    real_graph = load_ego_network(EDGE_PATH, EGO_ID)
    er_graph = nx.gnm_random_graph(
        real_graph.number_of_nodes(),
        real_graph.number_of_edges(),
        seed=BASELINE_SEED,
    )
    return er_graph, real_graph


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Baseline choice

    I use the Erdos-Renyi **G(n, m)** form from the lecture so the null model
    keeps the **same number of nodes** and **exactly the same number of edges**
    as the real network.

    That makes density identical and lets the comparison focus on structure.
    I keep the full ego graph for continuity with the earlier exercises, but I
    interpret the extreme hub cautiously because the ego node is linked to every
    alter by construction.
    """)
    return


@app.cell
def _(er_graph, np, nx, pd, real_graph, summarize_graph):
    real_summary = summarize_graph(
        real_graph,
        "Real Facebook ego graph",
        nx,
        np,
    )
    er_summary = summarize_graph(
        er_graph,
        "ER baseline G(n, m)",
        nx,
        np,
    )

    comparison_df = pd.DataFrame([real_summary, er_summary])
    comparison_table_df = comparison_df[
        [
            "graph",
            "nodes",
            "edges",
            "density",
            "average degree",
            "degree std",
            "max degree",
            "average clustering",
            "average path length",
            "largest connected component size",
            "connected components",
        ]
    ].copy()
    comparison_table_df["max degree"] = comparison_table_df["max degree"].astype(int)
    comparison_table_df["largest connected component size"] = comparison_table_df[
        "largest connected component size"
    ].astype(int)
    comparison_table_df["connected components"] = comparison_table_df[
        "connected components"
    ].astype(int)
    comparison_table_df = comparison_table_df.round(
        {
            "density": 4,
            "average degree": 3,
            "degree std": 3,
            "average clustering": 3,
            "average path length": 3,
        }
    )
    return comparison_table_df, real_summary


@app.cell
def _(
    BASELINE_SEED,
    ER_SAMPLE_COUNT,
    np,
    nx,
    pd,
    real_graph,
    real_summary,
    summarize_graph,
):
    er_sample_rows = []

    for sample_offset in range(ER_SAMPLE_COUNT):
        sample_graph = nx.gnm_random_graph(
            real_graph.number_of_nodes(),
            real_graph.number_of_edges(),
            seed=BASELINE_SEED + sample_offset,
        )
        sample_summary = summarize_graph(sample_graph, "ER sample", nx, np)
        er_sample_rows.append(
            {
                "average clustering": sample_summary["average clustering"],
                "average path length": sample_summary["average path length"],
                "degree std": sample_summary["degree std"],
                "max degree": sample_summary["max degree"],
                "largest connected component size": sample_summary[
                    "largest connected component size"
                ],
            }
        )

    er_samples_df = pd.DataFrame(er_sample_rows)

    metric_labels = {
        "average clustering": "average clustering",
        "average path length": "average path length",
        "degree std": "degree std",
        "max degree": "max degree",
        "largest connected component size": "largest connected component size",
    }

    er_context_df = pd.DataFrame(
        [
            {
                "metric": label,
                "real graph": real_summary[metric_name],
                "ER mean (200 samples)": er_samples_df[metric_name].mean(),
                "ER 5%-95% range": (
                    f"{er_samples_df[metric_name].quantile(0.05):.3f} - "
                    f"{er_samples_df[metric_name].quantile(0.95):.3f}"
                ),
            }
            for metric_name, label in metric_labels.items()
        ]
    ).round(
        {
            "real graph": 3,
            "ER mean (200 samples)": 3,
        }
    )
    return er_context_df, er_samples_df


@app.cell(hide_code=True)
def _(ER_SAMPLE_COUNT, er_samples_df, mo, real_summary):
    clustering_ratio = (
        real_summary["average clustering"] / er_samples_df["average clustering"].mean()
    )
    degree_std_ratio = real_summary["degree std"] / er_samples_df["degree std"].mean()
    path_gap = (
        er_samples_df["average path length"].mean()
        - real_summary["average path length"]
    )

    mo.md(
        f"""
        The real ego graph has **{real_summary["nodes"]} nodes** and
        **{real_summary["edges"]} edges**.
        Across **{ER_SAMPLE_COUNT} deterministic ER samples**, the main signal is
        already clear:

        - real average clustering is **{clustering_ratio:.1f}x** the ER mean
        - real degree spread is **{degree_std_ratio:.1f}x** the ER mean
        - real average path length is only **{path_gap:.3f}** shorter than the ER mean

        So the strongest non-random features are not basic connectivity or path
        length, but **triangle-rich local structure** and **much more unequal
        degree than chance would predict**.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Comparison table
    """)
    return


@app.cell
def _(comparison_table_df):
    comparison_table_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ER ensemble context
    """)
    return


@app.cell
def _(er_context_df):
    er_context_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Degree distribution
    """)
    return


@app.cell
def _(degree_frequency_df, er_graph, pd, plt, real_graph):
    degree_plot_df = pd.concat(
        [
            degree_frequency_df(real_graph, "Real Facebook ego graph", pd),
            degree_frequency_df(er_graph, "ER baseline G(n, m)", pd),
        ],
        ignore_index=True,
    )

    palette = {
        "Real Facebook ego graph": "#D1495B",
        "ER baseline G(n, m)": "#00798C",
    }

    fig, ax = plt.subplots(figsize=(9, 5))

    for label, color in palette.items():
        subset = degree_plot_df.loc[degree_plot_df["graph"] == label]
        ax.plot(
            subset["degree"],
            subset["count"],
            marker="o",
            markersize=5,
            linewidth=2.2,
            color=color,
            label=label,
        )

    ax.text(
        0.02,
        0.96,
        "The real graph includes ego 698, which connects to every alter.",
        transform=ax.transAxes,
        va="top",
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#D0D0D0"},
    )
    ax.set_xlabel("degree")
    ax.set_ylabel("node count")
    ax.set_title("Degree distribution: real ego graph vs. ER baseline")
    ax.grid(alpha=0.22, linewidth=0.6)
    ax.legend(frameon=False)
    ax.set_xlim(left=0)
    fig.tight_layout()
    fig
    return


@app.cell(hide_code=True)
def _(er_samples_df, mo, real_summary):
    er_clustering_mean = er_samples_df["average clustering"].mean()
    er_clustering_q95 = er_samples_df["average clustering"].quantile(0.95)
    er_degree_std_mean = er_samples_df["degree std"].mean()
    er_max_degree_mean = er_samples_df["max degree"].mean()
    er_path_mean = er_samples_df["average path length"].mean()

    mo.md(
        f"""
        ## Conclusion

        This Facebook ego network looks **more structured than chance**.

        The clearest non-random property is **local social clustering**.
        The real graph has average clustering **{real_summary["average clustering"]:.3f}**,
        while the ER baseline averages only **{er_clustering_mean:.3f}** and stays
        below **{er_clustering_q95:.3f}** even at the 95th percentile across the
        sampled baselines.
        That means the neighborhood contains many more closed friend triangles than
        a random graph with the same size and density.

        The degree pattern is also **much more unequal** than ER.
        The real graph has degree standard deviation **{real_summary["degree std"]:.2f}**
        versus about **{er_degree_std_mean:.2f}** for ER, and its maximum degree is
        **{int(real_summary["max degree"])}** versus an ER average near
        **{er_max_degree_mean:.1f}**.
        Part of that gap is expected because the ego-network format creates one very
        high-degree ego node, so I treat the hub result as a useful warning sign
        rather than the only piece of evidence.

        By contrast, **largest connected component size is not a strong discriminator
        here**:
        both the real graph and the ER baseline keep all
        **{real_summary["largest connected component size"]} nodes** in one component,
        and the average path length difference is modest
        (**{real_summary["average path length"]:.3f}** vs. **{er_path_mean:.3f}**).

        My conclusion is that the Facebook ego neighborhood is non-random mainly
        because it is **far more clustered** than an ER graph and because its degree
        pattern is **more unequal than chance**, even after acknowledging that the ego
        representation itself creates one dominant hub.
        """
    )
    return


if __name__ == "__main__":
    app.run()
