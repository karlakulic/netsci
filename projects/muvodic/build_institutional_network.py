"""
build_institutional_network.py

Builds a heterogeneous directed network of Croatian legal acts and their
issuing institutions from the nn.sqlite3 database.

Node types:
  - act:         a legal act (ELI URI as ID)
  - institution: an issuing body (institution IRI as ID)

Edge types (all directed):
  - passed_by:  act -> institution  (which body issued the act)
  - amends:     act -> act          (modifies specific articles)
  - changes:    act -> act          (general substantive change)
  - based_on:   act -> act          (derives legal authority from)
  - repeals:    act -> act          (revokes entirely)
  - corrects:   act -> act          (fixes erratum)

Inverse relation types (amended_by, changed_by, etc.) are dropped
because they are redundant duplicates in a directed graph.

Output: network_institutional.json  (NetworkX node-link format)
"""

import sqlite3
import json
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = "data/nn.sqlite3"
OUTPUT_PATH = "network_institutional.json"

# Relations to keep (canonical direction only — no inverses)
CANONICAL_RELATIONS = {"amends", "changes", "based_on", "repeals", "corrects"}

# Minimum number of acts for an institution to get its own node.
# Institutions below this threshold are grouped under "Ostalo" to
# avoid cluttering the graph with dozens of one-off bodies.
MIN_ACTS_FOR_NODE = 50

# Human-readable names for the top institutions, inferred from act
# titles and document types (IDs are Narodne novine internal vocab).
INSTITUTION_NAMES = {
    "19560": "Vlada RH",
    "19505": "Hrvatski sabor",
    "19548": "Predsjedništvo RH",        # collective presidency, early 1990s
    "19656": "Min. poljoprivrede",
    "19956": "HANFA",
    "21402": "Min. zdravstva",
    "21555": "Predsjednik RH",           # individual presidency post-1990 constitution
    "20086": "HZMO",
    "19957": "HNB",
    "21646": "Visoki upravni sud RH",
    "20088": "HZZO",
    "21080": "Državnoodvjetničko vijeće",
    "19874": "Državni zavod za mjeriteljstvo",
    "19670": "Min. pomorstva, prometa i infrastr.",
    "21986": "Min. znanosti i obrazovanja",
    "22114": "Stožer civilne zaštite",   # COVID-era civil protection HQ
    "21637": "Ustavni sud RH",
    "21636": "Ustavni sud RH (poslovnik)",
    "19591": "Min. financija",
    "21308": "Državno izborno povjerenstvo",
    "20241": "HAKOM",
    "21366": "Min. mora, prometa i infrastrukture",
    "19835": "Državna geodetska uprava",
    "21077": "Državno sudbeno vijeće",
    "19886": "Državni zavod za statistiku",
    "20233": "Agencija za elektroničke medije",
    "19732": "Min. unutarnjih poslova",
    "23262": "Min. polj., šumarstva i ribarstva",
    "20102": "HERA",
    "20191": "Zavod za unap. zaštite na radu",
    "23261": "Min. znanosti, obraz. i mladih",
    "22122": "Min. rada, obitelji i soc. pol.",
    "19693": "Min. rada i mir. sustava",
    "19631": "Min. obrane",
    "19784": "Min. zdravlja",
    "22065": "Min. pravosuđa i uprave",
    "19682": "Min. pravosuđa",
    "19614": "Min. graditeljstva i prostornog uređenja",
    "22121": "Min. gosp. i održivog razvoja",
    "20103": "Hrvatska gospodarska komora",
    "19601": "Min. gospodarstva",
    "19623": "Min. kulture",
    "21177": "Upravni sud u Rijeci",
    "21179": "Upravni sud u Zagrebu",
    "21347": "Kolektivni ugovori",
    "21984": "Min. zaštite okoliša i energetike",
}

IRI_BASE = "https://narodne-novine.nn.hr/eli/vocabularies/nn-institutions/"
DOC_TYPE_BASE = "https://narodne-novine.nn.hr/resource/authority/document-type/"

# Acts that the scraper could not ingest because their page has no JSON-LD metadata,
# but whose identity and institution are verified from the HTML page and Croatian law.
# These are added as full act nodes so they receive proper institution attribution
# instead of being blank stubs.
MANUAL_ACTS = {
    # NN 150/2011, act 3084 — Zakon o Vladi Republike Hrvatske.
    # HTML page: /clanci/sluzbeni/2011_12_150_3084.html  (Donositelj: Hrvatski sabor)
    # Has no JSON-LD block, so the scraper never ingested it.
    # 1,517 incoming act_links edges (highest in-degree in the network) because every
    # Vlada uredba cites this act as its constitutional legal basis.
    "https://narodne-novine.nn.hr/eli/sluzbeni/2011/150/3084": {
        "title": "Zakon o Vladi Republike Hrvatske",
        "year": 2011,
        "document_type": "ZAKON",
        "passed_by_id": "19505",  # Hrvatski sabor
    },
    # NN 18/2009, act 403 — Statut Hrvatskog zavoda za zdravstveno osiguranje.
    # In DB with passed_by_iri=NULL and doc_type=STATUT (not in INFER_INSTITUTION_BY_DOC_TYPE),
    # so the act was scraped but never attributed. 159 incoming based_on edges.
    # Donositelj: HZZO (Upravno vijeće issues the statute of its own institution).
    "https://narodne-novine.nn.hr/eli/sluzbeni/2009/18/403": {
        "title": "Statut Hrvatskog zavoda za zdravstveno osiguranje",
        "year": 2009,
        "document_type": "STATUT",
        "passed_by_id": "20088",  # HZZO
    },
    # NN 16/2007, act 651 — Zakon o državnoj izmjeri i katastru nekretnina.
    # In DB with passed_by_iri=NULL and doc_type=ODLUKA (scraper classification error —
    # the DB title is "Zakon o državnoj izmjeri i katastru nekretnina" and the NN HTML
    # page confirms Donositelj: Hrvatski sabor; this is unambiguously a ZAKON, not an ODLUKA).
    # 23 incoming based_on edges from geodesy/cadastre regulations.
    "https://narodne-novine.nn.hr/eli/sluzbeni/2007/16/651": {
        "title": "Zakon o državnoj izmjeri i katastru nekretnina",
        "year": 2007,
        "document_type": "ZAKON",
        "passed_by_id": "19505",  # Hrvatski sabor
    },
}

# Document types whose issuing institution is unambiguous from Croatian constitutional law:
#   ZAKON / USTAV / USTAVNI_ZAKON → only Sabor can pass these (Constitution Art. 2, 81)
#   UREDBA (all variants) → only Vlada can issue these (Constitution Art. 112)
# These are applied as a fallback when passed_by_iri is NULL in the database.
# The inference is constitutional fact, not heuristic — there are no exceptions.
INFER_INSTITUTION_BY_DOC_TYPE = {
    "ZAKON":                              "19505",  # Hrvatski sabor
    "USTAV":                              "19505",
    "USTAVNI_ZAKON":                      "19505",
    "UREDBA":                             "19560",  # Vlada RH
    "UREDBA_SA_ZAKONSKOM_SNAGOM":         "19560",
    "UREDBA_NA_TEMELJU_ZAKONSKE_OVLASTI": "19560",
}


def inst_label(iri: str) -> str:
    inst_id = iri.replace(IRI_BASE, "")
    return INSTITUTION_NAMES.get(inst_id, f"Institucija-{inst_id}")


def doc_type_label(iri: str | None) -> str | None:
    if not iri:
        return None
    return iri.replace(DOC_TYPE_BASE, "")


def build_network():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ------------------------------------------------------------------ #
    # 1. Load institution act counts to decide which get their own node   #
    # ------------------------------------------------------------------ #
    print("Loading institution statistics...")
    c.execute(
        """SELECT passed_by_iri, COUNT(*) AS cnt
           FROM acts
           WHERE passed_by_iri IS NOT NULL
           GROUP BY passed_by_iri"""
    )
    inst_counts = {row["passed_by_iri"]: row["cnt"] for row in c.fetchall()}

    # Count acts with inferred institutions and add to inst_counts
    _doc_types_sql = ",".join(f"'{dt}'" for dt in INFER_INSTITUTION_BY_DOC_TYPE)
    c.execute(
        f"""SELECT REPLACE(document_type_iri, '{DOC_TYPE_BASE}', '') AS doc_type,
                   COUNT(*) AS cnt
            FROM acts
            WHERE passed_by_iri IS NULL
              AND document_type_iri IS NOT NULL
              AND REPLACE(document_type_iri, '{DOC_TYPE_BASE}', '') IN ({_doc_types_sql})
            GROUP BY doc_type"""
    )
    for row in c.fetchall():
        inst_id = INFER_INSTITUTION_BY_DOC_TYPE[row["doc_type"]]
        iri = IRI_BASE + inst_id
        inst_counts[iri] = inst_counts.get(iri, 0) + row["cnt"]

    significant_insts = {
        iri for iri, cnt in inst_counts.items() if cnt >= MIN_ACTS_FOR_NODE
    }
    print(f"  {len(inst_counts)} distinct institutions found.")
    print(f"  {len(significant_insts)} have >= {MIN_ACTS_FOR_NODE} acts (get own node).")

    # ------------------------------------------------------------------ #
    # 2. Load all acts that have a passed_by_iri, plus acts with an      #
    #    inferrable institution from document type.                       #
    # ------------------------------------------------------------------ #
    print("Loading acts...")
    c.execute(
        """SELECT eli, title, year, passed_by_iri, document_type_iri
           FROM acts
           WHERE passed_by_iri IS NOT NULL
             AND eli IS NOT NULL"""
    )
    act_rows = list(c.fetchall())
    print(f"  {len(act_rows)} acts with explicit passed_by_iri loaded.")

    # Load acts with inferred institution (passed_by_iri IS NULL but doc type is known)
    c.execute(
        f"""SELECT eli, title, year,
                   '{IRI_BASE}' ||
                   CASE REPLACE(document_type_iri, '{DOC_TYPE_BASE}', '')
                     WHEN 'ZAKON'                              THEN '19505'
                     WHEN 'USTAV'                              THEN '19505'
                     WHEN 'USTAVNI_ZAKON'                      THEN '19505'
                     WHEN 'UREDBA'                             THEN '19560'
                     WHEN 'UREDBA_SA_ZAKONSKOM_SNAGOM'         THEN '19560'
                     WHEN 'UREDBA_NA_TEMELJU_ZAKONSKE_OVLASTI' THEN '19560'
                   END AS inferred_iri,
                   document_type_iri
            FROM acts
            WHERE passed_by_iri IS NULL
              AND eli IS NOT NULL
              AND REPLACE(document_type_iri, '{DOC_TYPE_BASE}', '') IN ({_doc_types_sql})"""
    )
    inferred_rows = list(c.fetchall())
    print(f"  {len(inferred_rows)} acts with institution inferred from document type.")
    inferred_elis = {row["eli"] for row in inferred_rows}
    act_rows.extend(inferred_rows)
    print(f"  {len(act_rows)} acts total.")

    # ------------------------------------------------------------------ #
    # 3. Load canonical act-to-act links                                  #
    # ------------------------------------------------------------------ #
    print("Loading act-to-act links...")
    placeholders = ",".join(f"'{r}'" for r in CANONICAL_RELATIONS)
    c.execute(
        f"""SELECT
               a.eli AS source_eli,
               al.relation_type,
               al.target_eli
           FROM act_links al
           JOIN acts a
             ON  a.part            = al.source_part
             AND a.year            = al.source_year
             AND a.issue_number    = al.source_issue_number
             AND a.act_number      = al.source_act_number
           WHERE al.relation_type IN ({placeholders})
             AND al.target_eli IS NOT NULL"""
    )
    act_links = c.fetchall()
    print(f"  {len(act_links)} canonical act-to-act links loaded.")

    conn.close()

    # ------------------------------------------------------------------ #
    # 4. Build node and edge lists                                         #
    # ------------------------------------------------------------------ #
    print("Building graph structure...")

    nodes = []
    links = []

    # Collect all act ELIs that appear in act_links (both sides)
    linked_elis = set()
    for row in act_links:
        linked_elis.add(row["source_eli"])
        linked_elis.add(row["target_eli"])

    # Institution nodes
    inst_node_ids = set()
    for iri in significant_insts:
        inst_node_ids.add(iri)
        nodes.append(
            {
                "id": iri,
                "node_type": "institution",
                "name": inst_label(iri),
                "act_count": inst_counts[iri],
            }
        )

    # Act nodes + passed_by edges
    # Both explicit rows (passed_by_iri IS NOT NULL) and inferred rows (IS NULL but
    # doc-type known) are in act_rows. Column 3 is the institution IRI in both cases
    # (passed_by_iri for explicit; the CASE-computed IRI for inferred).
    # inferred_elis tracks which ELIs came from the inference fallback.
    act_node_ids = set()
    for row in act_rows:
        eli = row["eli"]
        if eli in act_node_ids:
            continue
        act_node_ids.add(eli)

        inst_iri = row[3]  # passed_by_iri (explicit) or inferred IRI (inferred)
        is_inferred = eli in inferred_elis

        nodes.append(
            {
                "id": eli,
                "node_type": "act",
                "title": row["title"] or "",
                "year": row["year"],
                "document_type": doc_type_label(row["document_type_iri"]),
                **({"institution_inferred": True} if is_inferred else {}),
            }
        )

        # passed_by edge — only to significant institution nodes
        if inst_iri in inst_node_ids:
            links.append(
                {
                    "source": eli,
                    "target": inst_iri,
                    "relation": "passed_by",
                }
            )

    # Manually curated acts — pre-populate before the stub loop so these ELIs
    # are recognised as full nodes rather than stubs.
    for eli, attrs in MANUAL_ACTS.items():
        if eli in act_node_ids:
            continue
        act_node_ids.add(eli)
        nodes.append(
            {
                "id": eli,
                "node_type": "act",
                "title": attrs["title"],
                "year": attrs["year"],
                "document_type": attrs["document_type"],
                "manual_curated": True,
            }
        )
        inst_iri = IRI_BASE + attrs["passed_by_id"]
        if inst_iri in inst_node_ids:
            links.append({"source": eli, "target": inst_iri, "relation": "passed_by"})
    print(f"  {len(MANUAL_ACTS)} manually curated acts added.")

    # For target ELIs in act_links that aren't in the DB (external references),
    # add minimal stub act nodes so edges aren't dangling.
    for row in act_links:
        for eli in (row["source_eli"], row["target_eli"]):
            if eli not in act_node_ids:
                act_node_ids.add(eli)
                nodes.append(
                    {
                        "id": eli,
                        "node_type": "act",
                        "title": "",
                        "year": None,
                        "document_type": None,
                        "stub": True,   # external reference, no DB metadata
                    }
                )

    # Act-to-act edges
    seen_edges = set()
    for row in act_links:
        key = (row["source_eli"], row["target_eli"], row["relation_type"])
        if key in seen_edges:
            continue
        seen_edges.add(key)
        links.append(
            {
                "source": row["source_eli"],
                "target": row["target_eli"],
                "relation": row["relation_type"],
            }
        )

    # ------------------------------------------------------------------ #
    # 5. Assemble and write output                                         #
    # ------------------------------------------------------------------ #
    graph = {
        "directed": True,
        "multigraph": False,
        "graph": {
            "name": "Croatian Legal Network — Institutional",
            "description": (
                "Heterogeneous directed network of Croatian legal acts (nodes) "
                "and their issuing institutions (nodes), connected by passed_by, "
                "amends, based_on, repeals, changes, and corrects edges."
            ),
        },
        "nodes": nodes,
        "links": links,
    }

    print(f"Writing {OUTPUT_PATH}...")
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(graph, f, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------ #
    # 6. Connectivity report                                               #
    # ------------------------------------------------------------------ #
    print("\n=== Network Summary ===")
    act_nodes = [n for n in nodes if n["node_type"] == "act"]
    inst_nodes = [n for n in nodes if n["node_type"] == "institution"]
    passed_by_edges = [e for e in links if e["relation"] == "passed_by"]
    act_act_edges = [e for e in links if e["relation"] != "passed_by"]

    print(f"  Act nodes:            {len(act_nodes):>8,}")
    print(f"  Institution nodes:    {len(inst_nodes):>8,}")
    print(f"  Total nodes:          {len(nodes):>8,}")
    print(f"  passed_by edges:      {len(passed_by_edges):>8,}")
    print(f"  act-to-act edges:     {len(act_act_edges):>8,}")
    print(f"  Total edges:          {len(links):>8,}")

    print("\n  Act-to-act edge breakdown:")
    rel_counts = defaultdict(int)
    for e in act_act_edges:
        rel_counts[e["relation"]] += 1
    for rel, cnt in sorted(rel_counts.items(), key=lambda x: -x[1]):
        print(f"    {rel:<12} {cnt:>7,}")

    print("\n  Top 10 institutions by act count:")
    top_insts = sorted(inst_nodes, key=lambda n: n["act_count"], reverse=True)[:10]
    for n in top_insts:
        print(f"    {n['name']:<45} {n['act_count']:>6,} acts")

    # Quick connectivity check using adjacency sets
    print("\n  Estimating connectivity (undirected)...")
    adj = defaultdict(set)
    for e in links:
        adj[e["source"]].add(e["target"])
        adj[e["target"]].add(e["source"])

    all_ids = {n["id"] for n in nodes}
    visited = set()
    components = []

    for start in all_ids:
        if start in visited:
            continue
        component = set()
        queue = [start]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            component.add(node)
            queue.extend(adj[node] - visited)
        components.append(component)

    components.sort(key=len, reverse=True)
    print(f"  Connected components:  {len(components):>7,}")
    print(f"  Largest component:     {len(components[0]):>7,} nodes "
          f"({len(components[0])/len(all_ids)*100:.1f}%)")
    if len(components) > 1:
        print(f"  2nd largest:           {len(components[1]):>7,} nodes")


if __name__ == "__main__":
    build_network()
