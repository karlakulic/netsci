"""Shared analysis helpers for the notebooks.

Loads the pickled NetworkX mirror (data/processed/graph.pkl) and exposes the
canonical graph projections the analysis is built on, so every notebook agrees
on what "the supply network" means:

  * full_graph()            -> the raw MultiDiGraph (all node/edge types)
  * company_supply_digraph()-> directed Company-only graph of SUPPLIES edges
  * company_supply_undirected() -> undirected view (for components / small-world)

The SUPPLIES projection is the object the hypothesis is about (who supplies
whom). COMPETES_WITH / LOCATED_IN / the Product layer are kept out of it and
analysed separately where relevant.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GRAPH_PKL = PROJECT_ROOT / "data" / "processed" / "graph.pkl"
FIGURES = PROJECT_ROOT / "reports" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)


# Consistent colours per company tier, shared across notebooks.
TIER_COLORS = {
    "equipment": "#dd6b20",   # orange
    "subsystem": "#f6ad55",   # light orange
    "materials": "#d69e2e",   # gold
    "gases": "#b7791f",       # dark gold
    "substrate": "#975a16",   # brown
    "photomask": "#c05621",   # rust
    "fab": "#2b6cb0",         # blue
    "IDM": "#3182ce",         # light blue
    "fabless": "#38a169",     # green
    "EDA": "#6b46c1",         # purple
    "IP": "#9f7aea",          # light purple
    "EMS": "#e53e3e",         # red
}


def tier_color(t: str) -> str:
    return TIER_COLORS.get(t, "#a0aec0")


def full_graph(path: Path = GRAPH_PKL) -> nx.MultiDiGraph:
    """Load the raw pickled mirror produced by 03_import_neo4j.py --export-nx."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run: python scripts/03_import_neo4j.py --all"
        )
    with path.open("rb") as fh:
        return pickle.load(fh)


def nodes_of_label(g: nx.MultiDiGraph, label: str) -> list[str]:
    return [n for n, d in g.nodes(data=True) if d.get("label") == label]


def company_supply_digraph(g: nx.MultiDiGraph | None = None) -> nx.DiGraph:
    """Directed Company graph keeping only SUPPLIES edges.

    Parallel SUPPLIES edges (different product categories) are collapsed to one
    directed edge whose `categories` attribute lists them and `weight` counts
    them. Company node attributes are carried over.
    """
    g = g if g is not None else full_graph()
    companies = set(nodes_of_label(g, "Company"))
    d = nx.DiGraph()
    for n in companies:
        d.add_node(n, **g.nodes[n])
    for u, v, k, data in g.edges(keys=True, data=True):
        if data.get("rel_type") != "SUPPLIES":
            continue
        if u not in companies or v not in companies:
            continue
        if d.has_edge(u, v):
            d[u][v]["weight"] += 1
            d[u][v]["categories"].append(data.get("product_category"))
        else:
            d.add_edge(u, v, weight=1,
                       categories=[data.get("product_category")])
    return d


def company_supply_undirected(g: nx.MultiDiGraph | None = None) -> nx.Graph:
    """Undirected simple-graph view of the SUPPLIES projection."""
    return company_supply_digraph(g).to_undirected(as_view=False)


def giant_component(graph: nx.Graph) -> nx.Graph:
    """Largest (weakly) connected component as a subgraph copy."""
    if graph.is_directed():
        comp = max(nx.weakly_connected_components(graph), key=len)
    else:
        comp = max(nx.connected_components(graph), key=len)
    return graph.subgraph(comp).copy()


# --------------------------------------------------------------------------- #
# Weighted / concentration analysis (uses MANUFACTURES capacity_share_pct)
# --------------------------------------------------------------------------- #
def product_concentration(g: nx.MultiDiGraph | None = None) -> dict:
    """Per-product supplier concentration from MANUFACTURES edges.

    Returns {product: {makers, n_makers, shares, n_with_share, top, max_share,
    hhi, single_source}} where shares are normalised to sum to 100% (reported
    shares are public approximations and need not sum to 100). `single_source`
    is True only when the *whole graph* records a single maker for the product —
    a structural monopoly in the model, not merely a gap in share data.
    """
    g = g if g is not None else full_graph()
    makers: dict[str, set] = {}
    shares: dict[str, list] = {}
    for u, v, _, d in g.edges(keys=True, data=True):
        if d.get("rel_type") != "MANUFACTURES":
            continue
        makers.setdefault(v, set()).add(u)
        s = d.get("capacity_share_pct")
        if s is not None:
            shares.setdefault(v, []).append((u, float(s)))
    out = {}
    for p, mk in makers.items():
        lst = shares.get(p, [])
        tot = sum(s for _, s in lst) or 1.0
        norm = [(c, 100 * s / tot) for c, s in lst]
        top = max(norm, key=lambda x: x[1]) if norm else (None, 0.0)
        out[p] = dict(
            makers=sorted(mk), n_makers=len(mk), shares=norm,
            n_with_share=len(lst), top=top[0], max_share=round(top[1], 1),
            hhi=round(sum((s / 100) ** 2 for _, s in norm) * 10000),
            single_source=len(mk) == 1)
    return out


def production_weight(g: nx.MultiDiGraph | None = None) -> dict:
    """Company -> production-control weight = sum of capacity_share_pct it holds
    across all products it manufactures (a proxy for how much output it commands)."""
    g = g if g is not None else full_graph()
    w: dict[str, float] = {}
    for u, v, _, d in g.edges(keys=True, data=True):
        if d.get("rel_type") == "MANUFACTURES" and d.get("capacity_share_pct") is not None:
            w[u] = w.get(u, 0.0) + float(d["capacity_share_pct"])
    return w


def production_at_risk(g: nx.MultiDiGraph | None = None) -> dict:
    """Company -> production-at-risk profile, using *raw* reported capacity shares.

    Returns {company: {controlled, single_source, n_single_source}} where:
      * controlled       = sum of capacity_share_pct held across all products
                           (output directly lost if the firm fails)
      * single_source    = the subset of that capacity on products for which the
                           firm is the *sole* maker in the model — irreplaceable,
                           no alternative supplier (the hard core of the risk)
      * n_single_source  = how many products it is the sole (share-reporting) maker of

    Only quantified capacity counts; a sole maker with no reported share is noted
    by product_concentration() but contributes 0 here (we don't invent numbers).
    """
    g = g if g is not None else full_graph()
    conc = product_concentration(g)
    controlled = production_weight(g)
    raw = {(u, v): float(d["capacity_share_pct"])
           for u, v, _, d in g.edges(keys=True, data=True)
           if d.get("rel_type") == "MANUFACTURES" and d.get("capacity_share_pct") is not None}
    single: dict[str, float] = {}
    n_single: dict[str, int] = {}
    for p, c in conc.items():
        if c["single_source"]:
            sole = c["makers"][0]
            sh = raw.get((sole, p))
            if sh is not None:
                single[sole] = single.get(sole, 0.0) + sh
                n_single[sole] = n_single.get(sole, 0) + 1
    return {comp: dict(controlled=round(ctrl, 1),
                       single_source=round(single.get(comp, 0.0), 1),
                       n_single_source=n_single.get(comp, 0))
            for comp, ctrl in controlled.items()}
