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
    # Exercise 07: Small-World Test for a Facebook Ego Network

    This notebook keeps the same SNAP Facebook ego network used in the earlier
    `mkatavic` exercises: ego node **698**.

    Goal:
    test whether this ego neighborhood has the small-world pattern: short paths
    together with much stronger local clustering than a comparable random graph.

    Required input:
    `data/facebook/698.edges`

    Expected output:
    graph and ER baseline path/clustering values, shortcut candidates, and a
    short conclusion about whether the small-world idea fits this topic.
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
    ER_SAMPLE_COUNT = 200
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
                cwd / "exercises" / "mkatavic" / "exercise_07" / "facebook",
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
    return EDGE_PATH, EGO_ID, ER_SAMPLE_COUNT, RANDOM_SEED


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

    def largest_component_subgraph(graph, nx_module):
        if graph.number_of_nodes() == 0:
            return graph.copy()

        largest_nodes = max(nx_module.connected_components(graph), key=len)
        return graph.subgraph(largest_nodes).copy()

    def path_length_with_basis(graph, nx_module):
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

    def graph_summary(graph, label, nx_module):
        average_path_length, path_basis, path_nodes = path_length_with_basis(
            graph,
            nx_module,
        )
        return {
            "graph": label,
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": nx_module.density(graph),
            "connected components": nx_module.number_connected_components(graph),
            "average shortest path length": average_path_length,
            "path-length basis": path_basis,
            "path-length nodes": path_nodes,
            "average clustering": nx_module.average_clustering(graph),
            "transitivity": nx_module.transitivity(graph),
        }

    def sorted_communities(communities):
        return sorted(
            (set(community_nodes) for community_nodes in communities),
            key=lambda community_nodes: (-len(community_nodes), min(community_nodes)),
        )

    def normalized_edge(edge):
        return tuple(sorted(edge))

    return (
        graph_summary,
        largest_component_subgraph,
        load_ego_network,
        normalized_edge,
        path_length_with_basis,
        sorted_communities,
    )


@app.cell
def _(EDGE_PATH, EGO_ID, load_ego_network, nx):
    G, alter_graph = load_ego_network(EDGE_PATH, EGO_ID)

    full_graph_connected = nx.is_connected(G)
    full_graph_basis = "full graph" if full_graph_connected else "largest connected component"
    alter_components = sorted(
        nx.connected_components(alter_graph),
        key=len,
        reverse=True,
    )
    alter_component_sizes = [len(component) for component in alter_components]
    return G, alter_component_sizes, alter_components, alter_graph, full_graph_basis


@app.cell
def _(G, RANDOM_SEED, graph_summary, nx, pd):
    er_graph = nx.gnm_random_graph(
        G.number_of_nodes(),
        G.number_of_edges(),
        seed=RANDOM_SEED,
    )

    real_summary = graph_summary(G, "Facebook ego graph", nx)
    er_single_summary = graph_summary(er_graph, "ER baseline G(n, m)", nx)

    comparison_df = pd.DataFrame([real_summary, er_single_summary])[
        [
            "graph",
            "nodes",
            "edges",
            "density",
            "connected components",
            "average shortest path length",
            "average clustering",
            "transitivity",
            "path-length basis",
        ]
    ].copy()
    comparison_df["nodes"] = comparison_df["nodes"].astype(int)
    comparison_df["edges"] = comparison_df["edges"].astype(int)
    comparison_df["connected components"] = comparison_df[
        "connected components"
    ].astype(int)
    comparison_df = comparison_df.round(
        {
            "density": 4,
            "average shortest path length": 3,
            "average clustering": 3,
            "transitivity": 3,
        }
    )
    return comparison_df, er_graph, real_summary


@app.cell
def _(ER_SAMPLE_COUNT, G, RANDOM_SEED, graph_summary, nx, pd):
    er_sample_rows = []

    for sample_index in range(ER_SAMPLE_COUNT):
        sample_graph = nx.gnm_random_graph(
            G.number_of_nodes(),
            G.number_of_edges(),
            seed=RANDOM_SEED + sample_index,
        )
        sample_summary = graph_summary(sample_graph, "ER sample", nx)
        er_sample_rows.append(
            {
                "average shortest path length": sample_summary[
                    "average shortest path length"
                ],
                "average clustering": sample_summary["average clustering"],
                "transitivity": sample_summary["transitivity"],
                "connected components": sample_summary["connected components"],
                "path-length nodes": sample_summary["path-length nodes"],
            }
        )

    er_samples_df = pd.DataFrame(er_sample_rows)
    return (er_samples_df,)


@app.cell
def _(er_samples_df, pd, real_summary):
    metric_names = [
        "average shortest path length",
        "average clustering",
        "transitivity",
    ]

    er_context_df = pd.DataFrame(
        [
            {
                "metric": metric_name,
                "real graph": real_summary[metric_name],
                "ER mean (200 samples)": er_samples_df[metric_name].mean(),
                "ER 5%-95% range": (
                    f"{er_samples_df[metric_name].quantile(0.05):.3f} - "
                    f"{er_samples_df[metric_name].quantile(0.95):.3f}"
                ),
            }
            for metric_name in metric_names
        ]
    ).round(
        {
            "real graph": 3,
            "ER mean (200 samples)": 3,
        }
    )

    clustering_ratio = (
        real_summary["average clustering"]
        / er_samples_df["average clustering"].mean()
    )
    path_length_ratio = (
        real_summary["average shortest path length"]
        / er_samples_df["average shortest path length"].mean()
    )
    return clustering_ratio, er_context_df, path_length_ratio


@app.cell
def _(
    EGO_ID,
    alter_graph,
    normalized_edge,
    nx,
    nx_comm,
    pd,
    sorted_communities,
):
    louvain_partition = sorted_communities(
        nx_comm.louvain_communities(
            alter_graph,
            seed=EGO_ID,
            resolution=1.0,
        )
    )
    community_lookup = {
        node: community_index
        for community_index, community_nodes in enumerate(louvain_partition, start=1)
        for node in community_nodes
    }

    alter_edge_betweenness = {
        normalized_edge(edge): score
        for edge, score in nx.edge_betweenness_centrality(alter_graph).items()
    }

    cross_community_edge_rows = []
    for source, target in alter_graph.edges():
        source_community = community_lookup[source]
        target_community = community_lookup[target]
        if source_community == target_community:
            continue

        edge = normalized_edge((source, target))
        cross_community_edge_rows.append(
            {
                "edge": f"{edge[0]}-{edge[1]}",
                "source community": source_community,
                "target community": target_community,
                "source degree": alter_graph.degree(source),
                "target degree": alter_graph.degree(target),
                "alter edge betweenness": alter_edge_betweenness[edge],
            }
        )

    shortcut_edge_df = (
        pd.DataFrame(cross_community_edge_rows)
        .sort_values(
            [
                "alter edge betweenness",
                "source degree",
                "target degree",
                "edge",
            ],
            ascending=[False, False, False, True],
        )
        .reset_index(drop=True)
    )
    return community_lookup, louvain_partition, shortcut_edge_df


@app.cell
def _(EGO_ID, G, alter_graph, community_lookup, louvain_partition, nx, pd):
    node_betweenness = nx.betweenness_centrality(G)

    shortcut_node_rows = []
    for node, betweenness in sorted(
        node_betweenness.items(),
        key=lambda item: (-item[1], item[0]),
    )[:8]:
        if node == EGO_ID:
            own_region = "ego"
            reached_regions = list(range(1, len(louvain_partition) + 1))
            cross_region_edges = len(reached_regions)
        else:
            own_region = str(community_lookup[node])
            reached_regions = sorted(
                {
                    community_lookup[neighbor]
                    for neighbor in alter_graph.neighbors(node)
                    if community_lookup[neighbor] != community_lookup[node]
                }
            )
            cross_region_edges = sum(
                1
                for neighbor in alter_graph.neighbors(node)
                if community_lookup[neighbor] != community_lookup[node]
            )

        shortcut_node_rows.append(
            {
                "node": node,
                "role": "ego" if node == EGO_ID else "alter",
                "degree in full graph": G.degree(node),
                "own region": own_region,
                "regions reached": ", ".join(str(region) for region in reached_regions),
                "cross-region edges": cross_region_edges,
                "node betweenness": betweenness,
            }
        )

    shortcut_node_df = pd.DataFrame(shortcut_node_rows)
    return (shortcut_node_df,)


@app.cell(hide_code=True)
def _(
    EGO_ID,
    ER_SAMPLE_COUNT,
    G,
    alter_component_sizes,
    clustering_ratio,
    er_samples_df,
    full_graph_basis,
    mo,
    path_length_ratio,
    real_summary,
):
    _er_clustering_mean = er_samples_df["average clustering"].mean()
    _er_path_mean = er_samples_df["average shortest path length"].mean()
    _er_clustering_q95 = er_samples_df["average clustering"].quantile(0.95)

    mo.md(
        f"""
        The Facebook ego graph has **{G.number_of_nodes()} nodes** and
        **{G.number_of_edges()} edges**. It is connected, so the path-length
        measurement uses the **{full_graph_basis}** as required.

        The ego node **{EGO_ID}** is included to keep the same dataset definition
        used in the previous exercises. Without the ego, the alter graph splits
        into components of sizes **{", ".join(str(size) for size in alter_component_sizes)}**,
        so the ego tie pattern is part of the shortcut story.

        Across **{ER_SAMPLE_COUNT}** deterministic ER graphs with the same number
        of nodes and edges, real average clustering is **{clustering_ratio:.1f}x**
        the ER mean (**{real_summary["average clustering"]:.3f}** vs.
        **{_er_clustering_mean:.3f}**) and is above the ER 95th percentile
        (**{_er_clustering_q95:.3f}**). Real average path length is still short:
        **{real_summary["average shortest path length"]:.3f}** vs. an ER mean of
        **{_er_path_mean:.3f}**, a ratio of **{path_length_ratio:.2f}**.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Graph vs. One ER Baseline
    """)
    return


@app.cell
def _(comparison_df):
    comparison_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## ER Ensemble Context
    """)
    return


@app.cell
def _(er_context_df):
    er_context_df
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Small-World Metrics
    """)
    return


@app.cell
def _(er_samples_df, plt, real_summary):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    metric_specs = [
        ("average shortest path length", "Average shortest path length"),
        ("average clustering", "Average clustering coefficient"),
    ]
    colors = ["#D1495B", "#00798C"]

    for axis, (metric_name, title) in zip(axes, metric_specs):
        er_mean = er_samples_df[metric_name].mean()
        er_low = er_samples_df[metric_name].quantile(0.05)
        er_high = er_samples_df[metric_name].quantile(0.95)
        values = [real_summary[metric_name], er_mean]
        labels = ["real", "ER mean"]

        axis.bar(labels, values, color=colors, width=0.62)
        axis.errorbar(
            [1],
            [er_mean],
            yerr=[[er_mean - er_low], [er_high - er_mean]],
            fmt="none",
            ecolor="#222222",
            elinewidth=1.5,
            capsize=5,
        )
        axis.set_title(title)
        axis.grid(axis="y", alpha=0.25, linewidth=0.6)

    axes[1].text(
        0.04,
        0.95,
        "ER bar shows mean; whisker is 5%-95% range",
        transform=axes[1].transAxes,
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "edgecolor": "#D0D0D0"},
    )
    fig.tight_layout()
    fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Shortcut Candidates

    I use Louvain communities on the alter graph to define local regions. The
    first table ranks high-betweenness nodes in the full ego graph. The second
    table ranks alter-alter edges that cross Louvain regions.
    """)
    return


@app.cell
def _(shortcut_node_df):
    shortcut_node_df.round({"node betweenness": 4})
    return


@app.cell
def _(shortcut_edge_df):
    shortcut_edge_df.head(10).round({"alter edge betweenness": 4})
    return


@app.cell(hide_code=True)
def _(
    EGO_ID,
    clustering_ratio,
    er_samples_df,
    mo,
    path_length_ratio,
    real_summary,
    shortcut_edge_df,
    shortcut_node_df,
):
    _er_clustering_mean = er_samples_df["average clustering"].mean()
    _er_path_mean = er_samples_df["average shortest path length"].mean()
    _top_alter_node = int(
        shortcut_node_df.loc[shortcut_node_df["role"] == "alter", "node"].iloc[0]
    )
    _top_cross_edge = shortcut_edge_df.iloc[0]
    _second_cross_edge = shortcut_edge_df.iloc[1]

    mo.md(
        f"""
        ## Conclusion

        This Facebook ego neighborhood is **small-world relative to an ER
        baseline with the same size and density**.

        The path length is already very short: **{real_summary["average shortest path length"]:.3f}**
        in the real graph compared with **{_er_path_mean:.3f}** for the ER mean
        (**{path_length_ratio:.2f}x** the ER path length). The stronger evidence
        is clustering: the real graph has average clustering
        **{real_summary["average clustering"]:.3f}**, while the ER baseline
        averages **{_er_clustering_mean:.3f}**. That is **{clustering_ratio:.1f}x**
        higher clustering than random chance at the same density.

        The small-world explanation fits the topic well because a Facebook ego
        neighborhood naturally contains dense friend circles, but a few connectors
        keep those circles easy to traverse. The dominant shortcut is ego
        **{EGO_ID}**, which links to every alter and gives the graph many paths
        of length one or two. Among alters, node **{_top_alter_node}** is the main
        non-ego shortcut candidate by betweenness. The strongest cross-region
        alter edges are **{_top_cross_edge["edge"]}** and
        **{_second_cross_edge["edge"]}**, which connect different Louvain regions.

        Because the ego node is included by construction, this is best read as a
        small-world result for the **ego neighborhood**, not as a claim about the
        entire Facebook network.
        """
    )
    return


if __name__ == "__main__":
    app.run()
