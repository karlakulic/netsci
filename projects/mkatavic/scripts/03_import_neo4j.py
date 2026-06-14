"""03 — Import collected data into Neo4j (and mirror to NetworkX).

Usage:
    python scripts/03_import_neo4j.py --init      # create schema constraints
    python scripts/03_import_neo4j.py --import    # load data/raw CSVs
    python scripts/03_import_neo4j.py --export-nx # pickle NetworkX mirror
    python scripts/03_import_neo4j.py --all       # init + import + export

Connection comes from utils.get_driver() which reads NEO4J_URI / NEO4J_USER /
NEO4J_PASSWORD from the environment or a local .env (never hardcoded).

Per project convention #5, after import the graph is exported to a NetworkX
DiGraph and pickled to data/processed/graph.pkl for fast offline analysis.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import DATA_PROCESSED, DATA_RAW, get_driver, log  # noqa: E402

CONSTRAINTS = [
    "CREATE CONSTRAINT company_name IF NOT EXISTS FOR (c:Company) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE",
    "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
    "CREATE CONSTRAINT facility_name IF NOT EXISTS FOR (f:Facility) REQUIRE f.name IS UNIQUE",
]


def _read(name: str) -> list[dict]:
    path = DATA_RAW / name
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num(v):
    """Coerce numeric-looking strings to int/float, else return as-is/None."""
    if v is None or v == "":
        return None
    try:
        return int(v)
    except ValueError:
        try:
            return float(v)
        except ValueError:
            return v


def init_schema(driver) -> None:
    with driver.session() as s:
        for c in CONSTRAINTS:
            s.run(c)
    log.info("Schema constraints created (%d).", len(CONSTRAINTS))


def import_data(driver) -> None:
    companies = _read("companies.csv")
    countries = _read("countries.csv")
    products = _read("products.csv")
    supplies = _read("supplies.csv")
    manufactures = _read("manufactures.csv")
    competes = _read("competes_with.csv")
    located = _read("located_in.csv")
    depends = _read("depends_on.csv")
    # Priority 2/3 enrichment (optional — present once scripts/02 has been run).
    country_enrich = _read("country_enrichment.csv")
    facilities = _read("facilities.csv")
    operates = _read("operates.csv")
    materials = _read("materials.csv")
    material_depends = _read("material_depends_on.csv")
    manufactures_fill = _read("manufactures_enrichment.csv")
    capacity_shares = _read("capacity_shares.csv")
    supply_shares = _read("supply_shares.csv")

    with driver.session() as s:
        # Nodes
        s.run("""
            UNWIND $rows AS r
            MERGE (c:Company {name: r.name})
            SET c.country = r.country, c.region = r.region, c.type = r.type,
                c.founded = toInteger(r.founded),
                c.employees = toInteger(r.employees),
                c.market_cap_usd = CASE WHEN r.market_cap_usd = '' THEN null
                                        ELSE toInteger(r.market_cap_usd) END
        """, rows=companies)

        s.run("""
            UNWIND $rows AS r
            MERGE (c:Country {name: r.name})
            SET c.iso2 = r.iso2, c.region = r.region
        """, rows=countries)

        s.run("""
            UNWIND $rows AS r
            MERGE (p:Product {name: r.name})
            SET p.category = r.category,
                p.node_size_nm = CASE WHEN r.node_size_nm = '' THEN null
                                      ELSE toInteger(r.node_size_nm) END,
                p.year_introduced = CASE WHEN r.year_introduced = '' THEN null
                                         ELSE toInteger(r.year_introduced) END
        """, rows=products)

        # Relationships
        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.source}), (b:Company {name: r.target})
            MERGE (a)-[x:SUPPLIES {product_category: r.product_category}]->(b)
            SET x.value_usd_annual = CASE WHEN r.value_usd_annual = '' THEN null
                                          ELSE toInteger(r.value_usd_annual) END,
                x.volume_share_pct = CASE WHEN r.volume_share_pct = '' THEN null
                                          ELSE toFloat(r.volume_share_pct) END,
                x.year_established = CASE WHEN r.year_established = '' THEN null
                                         ELSE toInteger(r.year_established) END,
                x.source_url = r.source_url, x.source_date = r.source_date
        """, rows=supplies)

        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.company}), (p:Product {name: r.product})
            MERGE (a)-[x:MANUFACTURES]->(p)
            SET x.process_node_nm = CASE WHEN r.process_node_nm = '' THEN null
                                         ELSE toInteger(r.process_node_nm) END,
                x.capacity_share_pct = CASE WHEN r.capacity_share_pct = '' THEN null
                                            ELSE toFloat(r.capacity_share_pct) END,
                x.source_url = r.source_url, x.source_date = r.source_date
        """, rows=manufactures)

        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.source}), (b:Company {name: r.target})
            MERGE (a)-[x:COMPETES_WITH]->(b) SET x.market_segment = r.market_segment
        """, rows=competes)

        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.company}), (c:Country {name: r.country})
            MERGE (a)-[:LOCATED_IN]->(c)
        """, rows=located)

        s.run("""
            UNWIND $rows AS r
            MATCH (a:Product {name: r.source}), (b:Product {name: r.target})
            MERGE (a)-[x:DEPENDS_ON]->(b) SET x.dependency_type = r.dependency_type
        """, rows=depends)

        # ---- Priority 2/3 enrichment ----
        # Country macro attributes (GDP, political-risk score).
        s.run("""
            UNWIND $rows AS r
            MATCH (c:Country {name: r.name})
            SET c.gdp_usd = CASE WHEN r.gdp_usd = '' THEN null
                                 ELSE toInteger(r.gdp_usd) END,
                c.political_risk_score = CASE WHEN r.political_risk_score = '' THEN null
                                              ELSE toFloat(r.political_risk_score) END
        """, rows=country_enrich)

        # Facility nodes.
        s.run("""
            UNWIND $rows AS r
            MERGE (f:Facility {name: r.name})
            SET f.city = r.city, f.country = r.country, f.type = r.type,
                f.capacity_wafers_month = CASE WHEN r.capacity_wafers_month = '' THEN null
                                               ELSE toInteger(r.capacity_wafers_month) END
        """, rows=facilities)

        # OPERATES (Company -> Facility).
        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.company}), (f:Facility {name: r.facility})
            MERGE (a)-[:OPERATES]->(f)
        """, rows=operates)

        # Additional material Product nodes (Priority 3).
        s.run("""
            UNWIND $rows AS r
            MERGE (p:Product {name: r.name})
            SET p.category = r.category,
                p.node_size_nm = CASE WHEN r.node_size_nm = '' THEN null
                                      ELSE toInteger(r.node_size_nm) END,
                p.year_introduced = CASE WHEN r.year_introduced = '' THEN null
                                         ELSE toInteger(r.year_introduced) END
        """, rows=materials)

        # Material DEPENDS_ON (Product -> Product) with source provenance.
        s.run("""
            UNWIND $rows AS r
            MATCH (a:Product {name: r.source}), (b:Product {name: r.target})
            MERGE (a)-[x:DEPENDS_ON]->(b)
            SET x.dependency_type = r.dependency_type,
                x.source_url = r.source_url, x.source_date = r.source_date
        """, rows=material_depends)

        # MANUFACTURES gap-fill (Company -> Product) — same shape as manufactures.
        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.company}), (p:Product {name: r.product})
            MERGE (a)-[x:MANUFACTURES]->(p)
            SET x.process_node_nm = CASE WHEN r.process_node_nm = '' THEN null
                                         ELSE toInteger(r.process_node_nm) END,
                x.capacity_share_pct = CASE WHEN r.capacity_share_pct = '' THEN null
                                            ELSE toFloat(r.capacity_share_pct) END,
                x.source_url = r.source_url, x.source_date = r.source_date
        """, rows=manufactures_fill)

        # Weighting overrides: sourced 2024 capacity shares on MANUFACTURES.
        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.company})-[x:MANUFACTURES]->(p:Product {name: r.product})
            SET x.capacity_share_pct = toFloat(r.capacity_share_pct),
                x.source_url = r.source_url, x.source_date = r.source_date
        """, rows=capacity_shares)

        # Weighting overrides: sourced company->company volume shares on SUPPLIES.
        s.run("""
            UNWIND $rows AS r
            MATCH (a:Company {name: r.source})-[x:SUPPLIES {product_category: r.product_category}]->(b:Company {name: r.target})
            SET x.volume_share_pct = toFloat(r.volume_share_pct),
                x.source_url = r.source_url, x.source_date = r.source_date
        """, rows=supply_shares)

    log.info("Imported: %d companies, %d countries, %d products | "
             "%d SUPPLIES, %d MANUFACTURES, %d COMPETES_WITH, %d LOCATED_IN, "
             "%d DEPENDS_ON",
             len(companies), len(countries), len(products), len(supplies),
             len(manufactures), len(competes), len(located), len(depends))
    log.info("Enrichment: %d country rows, %d facilities, %d OPERATES, "
             "%d material products, %d material DEPENDS_ON",
             len(country_enrich), len(facilities), len(operates),
             len(materials), len(material_depends))


def export_networkx(driver) -> None:
    """Mirror the graph to a NetworkX MultiDiGraph and pickle it (convention #5)."""
    import pickle

    import networkx as nx

    g = nx.MultiDiGraph()
    with driver.session() as s:
        for rec in s.run("MATCH (n) RETURN n, labels(n) AS labels"):
            n = rec["n"]
            g.add_node(n.get("name"), label=rec["labels"][0], **dict(n))
        for rec in s.run("MATCH (a)-[r]->(b) RETURN a.name AS a, b.name AS b, "
                         "type(r) AS t, properties(r) AS p"):
            g.add_edge(rec["a"], rec["b"], key=rec["t"], rel_type=rec["t"], **rec["p"])

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out = DATA_PROCESSED / "graph.pkl"
    with out.open("wb") as fh:
        pickle.dump(g, fh)
    log.info("NetworkX mirror pickled: %d nodes, %d edges -> %s",
             g.number_of_nodes(), g.number_of_edges(), out)


def _int(v):
    return int(v) if v not in (None, "") else None


def _float(v):
    return float(v) if v not in (None, "") else None


def export_networkx_from_csv() -> None:
    """Build the NetworkX mirror directly from data/raw CSVs (no Neo4j needed).

    Mirrors export_networkx() exactly: same MultiDiGraph, key=rel_type edges,
    same node/edge properties, and Neo4j's "drop null props" behaviour (empty
    cells are omitted rather than stored as None). Because edge keys are the
    relationship type, parallel SUPPLIES between the same company pair (differing
    only by product_category) collapse to a single edge — identical to the
    Neo4j export path.
    """
    import pickle

    import networkx as nx

    companies = _read("companies.csv")
    countries = _read("countries.csv")
    products = _read("products.csv")
    supplies = _read("supplies.csv")
    manufactures = _read("manufactures.csv")
    competes = _read("competes_with.csv")
    located = _read("located_in.csv")
    depends = _read("depends_on.csv")
    # Priority 2/3 enrichment (optional — present once scripts/02 has been run).
    country_enrich = {r["name"]: r for r in _read("country_enrichment.csv")}
    facilities = _read("facilities.csv")
    operates = _read("operates.csv")
    materials = _read("materials.csv")
    material_depends = _read("material_depends_on.csv")
    manufactures_fill = _read("manufactures_enrichment.csv")
    cap_override = {(r["company"], r["product"]): r for r in _read("capacity_shares.csv")}
    sup_override = {(r["source"], r["target"], r["product_category"]): r
                   for r in _read("supply_shares.csv")}

    g = nx.MultiDiGraph()

    def add_node(name, label, **props):
        g.add_node(name, label=label, name=name,
                   **{k: v for k, v in props.items() if v not in (None, "")})

    for r in companies:
        add_node(r["name"], "Company", country=r["country"], region=r["region"],
                 type=r["type"], founded=_int(r.get("founded")),
                 employees=_int(r.get("employees")),
                 market_cap_usd=_int(r.get("market_cap_usd")))
    for r in countries:
        e = country_enrich.get(r["name"], {})
        add_node(r["name"], "Country", iso2=r.get("iso2"), region=r.get("region"),
                 gdp_usd=_int(e.get("gdp_usd")),
                 political_risk_score=_float(e.get("political_risk_score")))
    for r in products:
        add_node(r["name"], "Product", category=r.get("category"),
                 node_size_nm=_int(r.get("node_size_nm")),
                 year_introduced=_int(r.get("year_introduced")))
    for r in materials:  # additional material Product nodes
        add_node(r["name"], "Product", category=r.get("category"),
                 node_size_nm=_int(r.get("node_size_nm")),
                 year_introduced=_int(r.get("year_introduced")))
    for r in facilities:
        add_node(r["name"], "Facility", city=r.get("city"), country=r.get("country"),
                 type=r.get("type"),
                 capacity_wafers_month=_int(r.get("capacity_wafers_month")))

    companies_set = {r["name"] for r in companies}
    countries_set = {r["name"] for r in countries}
    products_set = {r["name"] for r in products} | {r["name"] for r in materials}
    facilities_set = {r["name"] for r in facilities}
    skipped = 0

    def add_edge(a, b, a_ok, b_ok, rel_type, **props):
        nonlocal skipped
        if not (a in a_ok and b in b_ok):
            skipped += 1
            return
        g.add_edge(a, b, key=rel_type, rel_type=rel_type,
                   **{k: v for k, v in props.items() if v not in (None, "")})

    for r in supplies:
        ov = sup_override.get((r["source"], r["target"], r.get("product_category")))
        vol = _float(ov["volume_share_pct"]) if ov else _float(r.get("volume_share_pct"))
        src_url = ov["source_url"] if ov else r.get("source_url")
        src_date = ov["source_date"] if ov else r.get("source_date")
        add_edge(r["source"], r["target"], companies_set, companies_set, "SUPPLIES",
                 product_category=r.get("product_category"),
                 value_usd_annual=_int(r.get("value_usd_annual")),
                 volume_share_pct=vol,
                 year_established=_int(r.get("year_established")),
                 source_url=src_url, source_date=src_date)
    for r in manufactures + manufactures_fill:
        ov = cap_override.get((r["company"], r["product"]))
        share = _float(ov["capacity_share_pct"]) if ov else _float(r.get("capacity_share_pct"))
        src_url = ov["source_url"] if ov else r.get("source_url")
        src_date = ov["source_date"] if ov else r.get("source_date")
        add_edge(r["company"], r["product"], companies_set, products_set, "MANUFACTURES",
                 process_node_nm=_int(r.get("process_node_nm")),
                 capacity_share_pct=share,
                 source_url=src_url, source_date=src_date)
    for r in competes:
        add_edge(r["source"], r["target"], companies_set, companies_set,
                 "COMPETES_WITH", market_segment=r.get("market_segment"))
    for r in located:
        add_edge(r["company"], r["country"], companies_set, countries_set, "LOCATED_IN")
    for r in depends:
        add_edge(r["source"], r["target"], products_set, products_set, "DEPENDS_ON",
                 dependency_type=r.get("dependency_type"))
    for r in material_depends:
        add_edge(r["source"], r["target"], products_set, products_set, "DEPENDS_ON",
                 dependency_type=r.get("dependency_type"),
                 source_url=r.get("source_url"), source_date=r.get("source_date"))
    for r in operates:
        add_edge(r["company"], r["facility"], companies_set, facilities_set, "OPERATES")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out = DATA_PROCESSED / "graph.pkl"
    with out.open("wb") as fh:
        pickle.dump(g, fh)
    if skipped:
        log.warning("Skipped %d edge(s) with endpoints missing from node CSVs.", skipped)
    log.info("NetworkX mirror (from CSV) pickled: %d nodes, %d edges -> %s",
             g.number_of_nodes(), g.number_of_edges(), out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Import backbone data into Neo4j.")
    ap.add_argument("--init", action="store_true", help="create schema constraints")
    ap.add_argument("--import", dest="do_import", action="store_true",
                    help="load CSVs from data/raw into Neo4j")
    ap.add_argument("--export-nx", action="store_true",
                    help="pickle a NetworkX mirror to data/processed/graph.pkl")
    ap.add_argument("--export-nx-csv", action="store_true",
                    help="pickle the NetworkX mirror straight from data/raw CSVs "
                         "(no Neo4j connection required)")
    ap.add_argument("--all", action="store_true", help="init + import + export-nx")
    args = ap.parse_args()

    if not any([args.init, args.do_import, args.export_nx, args.export_nx_csv,
                args.all]):
        ap.error("nothing to do — pass --init, --import, --export-nx, "
                 "--export-nx-csv, or --all")

    # The CSV export path needs no DB connection — handle it before opening one.
    if args.export_nx_csv:
        export_networkx_from_csv()
        if not any([args.init, args.do_import, args.export_nx, args.all]):
            return

    driver = get_driver()
    try:
        if args.init or args.all:
            init_schema(driver)
        if args.do_import or args.all:
            import_data(driver)
        if args.export_nx or args.all:
            export_networkx(driver)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
