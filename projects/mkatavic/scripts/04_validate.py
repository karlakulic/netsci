"""04 — Validate collected data before import.

Enforces the project's critical rule:
    Every SUPPLIES and MANUFACTURES relationship MUST have a non-empty
    source_url AND source_date.

Also runs sanity checks:
    * every relationship endpoint refers to a known Company/Product node
    * every cited source_url appears in data/sources.csv
    * no duplicate company names

Reads from data/raw/ by default. Exits non-zero if any check fails, so it can
gate the import step in a pipeline.

Run:
    python scripts/04_validate.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import DATA_RAW, SOURCES_CSV, log  # noqa: E402


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    errors: list[str] = []

    companies = _read(DATA_RAW / "companies.csv")
    products = _read(DATA_RAW / "products.csv")
    supplies = _read(DATA_RAW / "supplies.csv")
    manufactures = _read(DATA_RAW / "manufactures.csv")
    manufactures += _read(DATA_RAW / "manufactures_enrichment.csv")  # gap-fill
    sources = _read(SOURCES_CSV)
    # Priority 2/3 enrichment (optional — present once scripts/02 has been run).
    country_enrich = _read(DATA_RAW / "country_enrichment.csv")
    facilities = _read(DATA_RAW / "facilities.csv")
    operates = _read(DATA_RAW / "operates.csv")
    materials = _read(DATA_RAW / "materials.csv")
    material_depends = _read(DATA_RAW / "material_depends_on.csv")
    capacity_shares = _read(DATA_RAW / "capacity_shares.csv")
    supply_shares = _read(DATA_RAW / "supply_shares.csv")

    company_names = {c["name"] for c in companies}
    product_names = {p["name"] for p in products} | {m["name"] for m in materials}
    facility_names = {f["name"] for f in facilities}
    source_urls = {s["url"] for s in sources}

    # --- duplicate company names ---
    if len(company_names) != len(companies):
        errors.append("Duplicate company names in companies.csv")

    # --- critical rule: SUPPLIES source coverage + valid endpoints ---
    for i, r in enumerate(supplies, 1):
        if not r.get("source_url") or not r.get("source_date"):
            errors.append(f"SUPPLIES row {i} ({r.get('source')}->{r.get('target')}) "
                          "missing source_url/source_date")
        if r.get("source") not in company_names:
            errors.append(f"SUPPLIES row {i}: unknown source company {r.get('source')!r}")
        if r.get("target") not in company_names:
            errors.append(f"SUPPLIES row {i}: unknown target company {r.get('target')!r}")
        if r.get("source_url") and r["source_url"] not in source_urls:
            errors.append(f"SUPPLIES row {i}: source_url not in sources.csv")

    # --- critical rule: MANUFACTURES source coverage + valid endpoints ---
    for i, r in enumerate(manufactures, 1):
        if not r.get("source_url") or not r.get("source_date"):
            errors.append(f"MANUFACTURES row {i} ({r.get('company')}->{r.get('product')}) "
                          "missing source_url/source_date")
        if r.get("company") not in company_names:
            errors.append(f"MANUFACTURES row {i}: unknown company {r.get('company')!r}")
        if r.get("product") not in product_names:
            errors.append(f"MANUFACTURES row {i}: unknown product {r.get('product')!r}")
        if r.get("source_url") and r["source_url"] not in source_urls:
            errors.append(f"MANUFACTURES row {i}: source_url not in sources.csv")

    # --- enrichment: endpoints valid + every cited source logged ---
    for i, r in enumerate(facilities, 1):
        if r.get("source_url") and r["source_url"] not in source_urls:
            errors.append(f"facilities row {i} ({r.get('name')}): source_url not in sources.csv")
        if r.get("country") and r["country"] not in {c["name"] for c in _read(DATA_RAW / 'countries.csv')}:
            errors.append(f"facilities row {i}: country {r.get('country')!r} not a Country node")
    for i, r in enumerate(operates, 1):
        if r.get("company") not in company_names:
            errors.append(f"operates row {i}: unknown company {r.get('company')!r}")
        if r.get("facility") not in facility_names:
            errors.append(f"operates row {i}: unknown facility {r.get('facility')!r}")
    for i, r in enumerate(material_depends, 1):
        if not r.get("source_url") or not r.get("source_date"):
            errors.append(f"material_depends_on row {i} missing source_url/source_date")
        if r.get("source") not in product_names:
            errors.append(f"material_depends_on row {i}: unknown source product {r.get('source')!r}")
        if r.get("target") not in product_names:
            errors.append(f"material_depends_on row {i}: unknown target product {r.get('target')!r}")
        if r.get("source_url") and r["source_url"] not in source_urls:
            errors.append(f"material_depends_on row {i}: source_url not in sources.csv")
    for i, r in enumerate(country_enrich, 1):
        for col in ("gdp_source_url", "political_risk_source_url"):
            if r.get(col) and r[col] not in source_urls:
                errors.append(f"country_enrichment row {i} ({r.get('name')}): {col} not in sources.csv")

    man_pairs = {(r.get("company"), r.get("product")) for r in manufactures}
    for i, r in enumerate(capacity_shares, 1):
        if (r.get("company"), r.get("product")) not in man_pairs:
            errors.append(f"capacity_shares row {i}: no MANUFACTURES edge "
                          f"{r.get('company')!r}->{r.get('product')!r}")
        if r.get("source_url") and r["source_url"] not in source_urls:
            errors.append(f"capacity_shares row {i}: source_url not in sources.csv")
    sup_triples = {(r.get("source"), r.get("target"), r.get("product_category"))
                   for r in supplies}
    for i, r in enumerate(supply_shares, 1):
        if (r.get("source"), r.get("target"), r.get("product_category")) not in sup_triples:
            errors.append(f"supply_shares row {i}: no SUPPLIES edge "
                          f"{r.get('source')!r}->{r.get('target')!r} [{r.get('product_category')}]")
        if r.get("source_url") and r["source_url"] not in source_urls:
            errors.append(f"supply_shares row {i}: source_url not in sources.csv")

    # --- report ---
    log.info("Validation summary:")
    log.info("  companies=%d products=%d supplies=%d manufactures=%d sources=%d",
             len(companies), len(products), len(supplies), len(manufactures),
             len(sources))
    log.info("  enrichment: countries=%d facilities=%d operates=%d materials=%d "
             "material_depends=%d",
             len(country_enrich), len(facilities), len(operates), len(materials),
             len(material_depends))
    if errors:
        log.error("FAILED — %d problem(s):", len(errors))
        for e in errors[:50]:
            log.error("  - %s", e)
        if len(errors) > 50:
            log.error("  ... and %d more", len(errors) - 50)
        return 1
    log.info("PASSED — all SUPPLIES/MANUFACTURES edges are sourced and consistent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
