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
    # Exercise 11: Case Study -- Facebook Ego Network 698

    This notebook is the final case-study package for Student 5's topic:
    the SNAP Facebook ego network centred on **ego node 698**.

    It rebuilds the graph-construction pipeline from raw SNAP files in a
    fully reproducible way, enriches nodes with **circle membership** attributes
    derived from the `.circles` file (the only non-anonymised structural
    metadata available), computes a compact set of final metrics, produces a
    ranked node-importance table, generates a publication-ready visualisation,
    and exports two artifacts: a **CSV node table** and a **GraphML file**.

    Required inputs (all under `data/facebook/`):
    - `698.edges`   -- alter-to-alter edge list
    - `698.circles` -- ego's friend-circle membership lists

    Exported outputs (written to the same folder as this notebook):
    - `ego698_node_table.csv`  -- ranked node-importance table
    - `ego698_network.graphml` -- enriched graph in GraphML format
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import networkx as nx
    import numpy as np
    import pandas as pd
    return Path, mpatches, np, nx, pd, plt


@app.cell
def _(Path):
    EGO_ID = 698

    def _resolve():
        candidates = []
        if "__file__" in globals():
            nb = Path(__file__).resolve().parent
            candidates += [
                nb / "facebook",
                nb.parent / "data" / "facebook",
                nb.parent / "facebook",
            ]
        cwd = Path.cwd()
        candidates += [
            cwd / "facebook",
            cwd / "exercises" / "mkatavic" / "data" / "facebook",
            cwd / "exercises" / "mkatavic" / "exercise_11" / "facebook",
        ]
        for d in candidates:
            if (d / f"{EGO_ID}.edges").exists():
                return d
        raise FileNotFoundError(
            "Cannot find Facebook data directory. Searched:\n"
            + "\n".join(str(c) for c in candidates)
        )

    _DATA_DIR = _resolve()
    EDGE_PATH = _DATA_DIR / f"{EGO_ID}.edges"
    CIRCLES_PATH = _DATA_DIR / f"{EGO_ID}.circles"
    return CIRCLES_PATH, EDGE_PATH, EGO_ID


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Graph Construction Pipeline

    **Step 1 -- Load alter graph**: read `698.edges` as an undirected graph.
    Each node is an alter (friend of the ego). Edges are mutual Facebook
    friendships between alters.

    **Step 2 -- Inject ego node**: add node 698 and connect it to every alter.
    This reconstructs the true ego graph because the original SNAP data omits
    ego edges to keep the edge list compact.

    **Step 3 -- Load circle annotations**: parse `698.circles` to record which
    named circle each alter belongs to. A node may appear in multiple circles
    (the circles overlap). The primary circle is taken as the first listed.

    **Step 4 -- Enrich nodes**: attach degree, betweenness centrality, clustering
    coefficient, and circle-membership as node attributes before export.
    """)
    return


@app.cell
def _(CIRCLES_PATH, EDGE_PATH, EGO_ID, nx):
    _alter_raw = nx.read_edgelist(EDGE_PATH, nodetype=int, create_using=nx.Graph())
    _alters = sorted(_alter_raw.nodes())

    G = _alter_raw.copy()
    G.add_node(EGO_ID)
    G.add_edges_from((EGO_ID, a) for a in _alters)

    circle_membership = {}
    with open(CIRCLES_PATH) as _fh:
        for _line in _fh:
            _parts = _line.strip().split()
            if len(_parts) < 2:
                continue
            _cname = _parts[0]
            for _nstr in _parts[1:]:
                _n = int(_nstr)
                circle_membership.setdefault(_n, []).append(_cname)

    for _nd in G.nodes():
        if _nd == EGO_ID:
            G.nodes[_nd]["circle_primary"] = "ego"
            G.nodes[_nd]["circles_all"] = "ego"
            G.nodes[_nd]["n_circles"] = 0
            G.nodes[_nd]["is_ego"] = True
        else:
            _cl = circle_membership.get(_nd, [])
            G.nodes[_nd]["circle_primary"] = _cl[0] if _cl else "unassigned"
            G.nodes[_nd]["circles_all"] = "|".join(_cl) if _cl else "unassigned"
            G.nodes[_nd]["n_circles"] = len(_cl)
            G.nodes[_nd]["is_ego"] = False

    print(f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G, circle_membership


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Compact Final Metrics
    """)
    return


@app.cell
def _(EGO_ID, G, circle_membership, nx, pd):
    degrees = dict(G.degree())
    betweenness = nx.betweenness_centrality(G, normalized=True)
    closeness = nx.closeness_centrality(G)
    clustering = nx.clustering(G)

    for _nd in G.nodes():
        G.nodes[_nd]["degree"] = degrees[_nd]
        G.nodes[_nd]["betweenness"] = betweenness[_nd]
        G.nodes[_nd]["closeness"] = closeness[_nd]
        G.nodes[_nd]["clustering"] = clustering[_nd]

    lcc = max(nx.connected_components(G), key=len)
    _lcc_sub = G.subgraph(lcc)

    _n_circles = len({v for vals in circle_membership.values() for v in vals})

    metrics_df = pd.DataFrame(
        [
            {"metric": "nodes", "value": G.number_of_nodes()},
            {"metric": "edges", "value": G.number_of_edges()},
            {"metric": "density", "value": round(nx.density(G), 5)},
            {"metric": "connected components", "value": nx.number_connected_components(G)},
            {"metric": "largest component (nodes)", "value": len(lcc)},
            {"metric": "avg degree", "value": round(sum(degrees.values()) / G.number_of_nodes(), 3)},
            {"metric": "max degree (ego)", "value": degrees[EGO_ID]},
            {"metric": "avg clustering", "value": round(nx.average_clustering(G), 4)},
            {"metric": "avg betweenness", "value": round(sum(betweenness.values()) / G.number_of_nodes(), 5)},
            {"metric": "diameter (LCC)", "value": nx.diameter(_lcc_sub)},
            {"metric": "avg shortest path (LCC)", "value": round(nx.average_shortest_path_length(_lcc_sub), 3)},
            {"metric": "unique circles", "value": _n_circles},
        ]
    )
    metrics_df
    return betweenness, closeness, clustering, degrees, lcc, metrics_df


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Ranked Node-Importance Table

    Nodes are ranked by a composite importance score that combines normalised
    degree and normalised betweenness centrality with equal weight.  This rewards
    nodes that are both highly connected **and** structurally critical as brokers.
    The ego node (698) is listed for completeness but annotated separately.
    """)
    return


@app.cell
def _(EGO_ID, G, betweenness, closeness, clustering, degrees, pd):
    _max_deg = max(degrees.values())
    _max_bc = max(betweenness.values()) if max(betweenness.values()) > 0 else 1.0

    _rows = []
    for _nd in G.nodes():
        _nd_deg = degrees[_nd]
        _nd_bc = betweenness[_nd]
        _score = 0.5 * (_nd_deg / _max_deg) + 0.5 * (_nd_bc / _max_bc)
        _rows.append(
            {
                "node": _nd,
                "role": "ego" if _nd == EGO_ID else "alter",
                "degree": _nd_deg,
                "betweenness": round(_nd_bc, 5),
                "closeness": round(closeness[_nd], 5),
                "clustering": round(clustering[_nd], 4),
                "circle": G.nodes[_nd]["circle_primary"],
                "n_circles": G.nodes[_nd]["n_circles"],
                "importance_score": round(_score, 4),
            }
        )

    node_table = (
        pd.DataFrame(_rows)
        .sort_values("importance_score", ascending=False)
        .reset_index(drop=True)
    )
    node_table.index += 1
    node_table.head(20)
    return (node_table,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Circle Membership Summary

    Distribution of nodes across the ego's named friend circles.
    Nodes in multiple circles are counted once per circle.
    """)
    return


@app.cell
def _(EGO_ID, G, pd):
    _circ_rows = []
    for _nd in G.nodes():
        if _nd == EGO_ID:
            continue
        _cstr = G.nodes[_nd]["circles_all"]
        if _cstr == "unassigned":
            _circ_rows.append({"circle": "unassigned", "node": _nd})
        else:
            for _c in _cstr.split("|"):
                _circ_rows.append({"circle": _c, "node": _nd})

    circle_df = (
        pd.DataFrame(_circ_rows)
        .groupby("circle")
        .agg(n_members=("node", "count"))
        .sort_values("n_members", ascending=False)
        .reset_index()
    )
    circle_df
    return (circle_df,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Final Visualisation

    The layout is computed with the spring (Fruchterman-Reingold) algorithm.
    Node colour encodes **primary circle membership**; node size encodes
    **degree** (log-scaled so the ego node does not overwhelm the plot).
    The ego node is drawn with a black border.
    """)
    return


@app.cell
def _(EGO_ID, G, circle_membership, mpatches, np, plt):
    _all_circles = sorted({c for cls in circle_membership.values() for c in cls})
    _palette = [
        "#D1495B", "#00798C", "#F4A35A", "#8B5CF6", "#22C55E",
        "#F59E0B", "#06B6D4", "#EC4899", "#84CC16", "#6366F1",
        "#14B8A6", "#F97316", "#A855F7",
    ]
    _cmap = {c: _palette[i % len(_palette)] for i, c in enumerate(_all_circles)}
    _cmap["unassigned"] = "#BBBBBB"
    _cmap["ego"] = "#111111"

    _pos = nx.spring_layout(G, seed=698, k=0.35, iterations=80)

    _colors = [_cmap.get(G.nodes[n]["circle_primary"], "#BBBBBB") for n in G.nodes()]
    _sizes = [max(30, 18 * np.log1p(G.nodes[n]["degree"])) for n in G.nodes()]
    _borders = [2.5 if n == EGO_ID else 0.3 for n in G.nodes()]
    _edge_colors = ["black" if n == EGO_ID else "#555555" for n in G.nodes()]

    _fig, _ax = plt.subplots(figsize=(13, 10))

    nx.draw_networkx_edges(G, _pos, ax=_ax, alpha=0.08, width=0.5, edge_color="#444444")
    nx.draw_networkx_nodes(
        G, _pos, ax=_ax,
        node_color=_colors, node_size=_sizes,
        linewidths=_borders, edgecolors=_edge_colors,
    )
    nx.draw_networkx_labels(
        G, _pos, ax=_ax,
        labels={EGO_ID: str(EGO_ID)},
        font_size=9, font_weight="bold", font_color="white",
    )

    _legend = [
        mpatches.Patch(facecolor=_cmap[c], label=c, edgecolor="#555555")
        for c in _all_circles
    ]
    _legend.append(mpatches.Patch(facecolor="#BBBBBB", label="unassigned", edgecolor="#555555"))
    _legend.append(mpatches.Patch(facecolor="#111111", label=f"ego ({EGO_ID})", edgecolor="black"))

    _ax.legend(
        handles=_legend, title="Primary circle",
        loc="upper left", framealpha=0.85, fontsize=8, title_fontsize=9,
    )
    _ax.set_title(
        f"Facebook Ego Network -- Ego {EGO_ID}\n"
        "Node colour = primary friend circle  |  Node size ~ log(degree)",
        fontsize=13,
    )
    _ax.axis("off")
    _fig.tight_layout()
    _fig
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Artifact Export

    Two files are written next to this notebook:
    1. `ego698_node_table.csv`  -- full ranked node-importance table.
    2. `ego698_network.graphml` -- enriched graph in GraphML format, including
       all node attributes (degree, betweenness, closeness, clustering,
       circle membership).
    """)
    return


@app.cell
def _(EGO_ID, G, Path, node_table, nx):
    if "__file__" in globals():
        _out = Path(__file__).resolve().parent
    else:
        _out = Path.cwd()

    _csv = _out / f"ego{EGO_ID}_node_table.csv"
    _gml = _out / f"ego{EGO_ID}_network.graphml"

    node_table.to_csv(_csv, index_label="rank")
    nx.write_graphml(G, str(_gml))

    print(f"CSV     -> {_csv}")
    print(f"GraphML -> {_gml}")
    return


@app.cell(hide_code=True)
def _(EGO_ID, G, lcc, metrics_df, mo, node_table, nx):
    _n = G.number_of_nodes()
    _e = G.number_of_edges()
    _density = nx.density(G)
    _avg_clust = nx.average_clustering(G)
    _diam = nx.diameter(G.subgraph(lcc))
    _avg_path = nx.average_shortest_path_length(G.subgraph(lcc))

    _top_alter = node_table[node_table["role"] == "alter"].iloc[0]
    _ta_node = int(_top_alter["node"])
    _ta_deg = int(_top_alter["degree"])
    _ta_bc = float(_top_alter["betweenness"])
    _ta_circ = _top_alter["circle"]

    _n_circles = int(
        metrics_df.loc[metrics_df["metric"] == "unique circles", "value"].iloc[0]
    )
    _ego_deg = G.degree(EGO_ID)

    mo.md(
        f"""
        ## Case-Study Summary

        ### Topic: Facebook Ego Network -- Who Is User 698?

        The SNAP dataset provides an anonymised snapshot of the Facebook social
        graph centred on a single user, **ego 698**. This ego network records
        {_n} nodes ({_n - 1} friends of the ego, plus the ego itself) and
        {_e} mutual friendship edges.

        ---

        ### Graph Structure

        The network is **sparse** (density {_density:.4f}) but highly clustered
        (avg clustering coefficient {_avg_clust:.3f}), which is the classic
        signature of a social ego network: friends of a person tend to know
        each other. Paths are short -- diameter {_diam}, average shortest path
        {_avg_path:.2f} hops -- reflecting the compact neighbourhood structure
        of a single person's friend list.

        The ego node itself ({EGO_ID}) has degree **{_ego_deg}** and
        connects to every alter, making it the single most important node by
        every centrality measure. The most important *alter* is node
        **{_ta_node}** (degree {_ta_deg}, betweenness
        {_ta_bc:.4f}, primary circle: {_ta_circ}), which serves
        as a secondary hub within its circle.

        ---

        ### Circle Structure

        The ego's friend list is partitioned into **{_n_circles} named circles**
        (a Facebook feature that lets users group friends manually). Circles
        overlap -- a node can appear in several circles -- but most alters belong
        to one primary circle. The circles correspond to real social contexts
        (school cohorts, work groups, family clusters) even though all personal
        identifiers have been anonymised. Nodes in the "unassigned" category
        are alters not placed in any circle by the ego.

        ---

        ### Course-Long Findings

        Across exercises 02-10, this ego network revealed:

        - **Hub-and-spoke topology**: the ego node is the absolute hub; its
          removal fragments the network into as many components as there are
          isolated circles (exercise 09).
        - **Small-world property**: high clustering with short paths (exercise 07).
        - **Moderate degree heterogeneity**: the alter-only graph shows mild hub
          dominance but is not strongly scale-free (exercise 08).
        - **Resilience gap**: random node failure is relatively harmless, while
          targeted degree/betweenness attack rapidly disconnects the network
          because the ego is a single point of failure (exercise 09).
        - **Diffusion advantage of the ego seed**: in an Independent Cascade model,
          starting from the ego node provides a large adoption advantage at low
          propagation probability, because it activates all {_ego_deg} alters
          in the very first step (exercise 10).

        ---

        ### Key Takeaway

        User 698's ego network is a **hub-star with clustered sub-communities**.
        Its resilience and diffusion properties are almost entirely determined by
        the ego's structural role as the unique bridge between circles. The most
        impactful network-design intervention -- adding even a small number of
        cross-circle ties -- would simultaneously improve resilience (exercise 09),
        reduce the seed-choice gap in diffusion (exercise 10), and shift the
        network toward a more distributed, resilient architecture.
        """
    )
    return


if __name__ == "__main__":
    app.run()
