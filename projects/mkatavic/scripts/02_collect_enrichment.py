"""02 — Priority 2 (+3) enrichment data collection.

Adds three layers on top of the Priority-1 backbone:

  1. COUNTRY enrichment  — GDP (current USD) and a political-risk score for the
     13 country nodes, fetched live:
        * GDP   : World Bank indicator NY.GDP.MKTP.CD (most recent value)
        * Risk  : World Bank WGI "Political Stability and Absence of
                  Violence/Terrorism: Estimate" (GOV_WGI_PV.EST, source 3),
                  range approx. -2.5 (fragile) .. +2.5 (stable)
        * Taiwan is not in the World Bank country list, so its GDP comes from the
          IMF World Economic Outlook (DataMapper NGDPD); its WGI score *is* in
          the World Bank data.

  2. FACILITY nodes + OPERATES edges — marquee fabs / sites of the major players,
     manually coded from public company / encyclopaedic sources. Wafer-start
     capacities are public approximations (300mm-equivalent wafers/month) and are
     left blank where not reliably reported, rather than fabricated.

  3. MATERIAL dependencies (Priority 3) — a deeper Product->Product layer for the
     specific gases / chemicals / minerals the process steps consume (neon, HF,
     WF6, C4F6, rare earths, synthetic quartz, EUV pellicle, ...). These are the
     choke-point inputs behind the 2020-2022 crisis narrative.

Every fact carries a source (logged to data/sources.csv). Network access is
required for layer 1; the script fails loudly rather than inventing numbers.

Run:
    python scripts/02_collect_enrichment.py
Then re-import:  python scripts/03_import_neo4j.py --import --export-nx
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import DATA_RAW, log, log_sources, write_csv  # noqa: E402

ACCESSED = _dt.date.today().isoformat()

# --------------------------------------------------------------------------- #
# Source registry
# --------------------------------------------------------------------------- #
SOURCES = {
    # --- country macro data ---
    "worldbank_gdp": dict(
        url="https://data.worldbank.org/indicator/NY.GDP.MKTP.CD",
        covers="GDP (current US$) — World Bank national accounts, most recent year"),
    "worldbank_wgi_pv": dict(
        url="https://databank.worldbank.org/source/worldwide-governance-indicators",
        covers="WGI Political Stability & Absence of Violence/Terrorism estimate (~ -2.5..2.5)"),
    "imf_weo_gdp": dict(
        url="https://www.imf.org/external/datamapper/NGDPD@WEO/TWN",
        covers="IMF World Economic Outlook GDP (current US$) — used for Taiwan"),
    # --- facility sources (one public page per operator) ---
    "tsmc_mfg": dict(
        url="https://www.tsmc.com/english/dedicatedFoundry/manufacturing",
        covers="TSMC manufacturing / fab locations & GigaFab capacities"),
    "esmc": dict(
        url="https://esmc.com/",
        covers="ESMC (TSMC-led JV) Dresden fab announcement"),
    "samsung_fab": dict(
        url="https://en.wikipedia.org/wiki/Samsung_Electronics",
        covers="Samsung semiconductor campuses (Pyeongtaek, Hwaseong, Taylor)"),
    "intel_fab": dict(
        url="https://www.intel.com/content/www/us/en/architecture-and-technology/arizona-fabs.html",
        covers="Intel manufacturing sites (Arizona Ocotillo, New Mexico)"),
    "gf_fab": dict(
        url="https://gf.com/about-us/manufacturing/",
        covers="GlobalFoundries manufacturing sites (Fab 8 Malta, NY)"),
    "micron_fab": dict(
        url="https://www.micron.com/about/our-commitment/operating-thoughtfully/global-locations",
        covers="Micron global fab locations (Hiroshima, Boise)"),
    "skhynix_fab": dict(
        url="https://www.skhynix.com/eng/about/businessArea.do",
        covers="SK Hynix fab sites (M16 Icheon)"),
    "smic_fab": dict(
        url="https://www.smics.com/en/site/company_intro",
        covers="SMIC fab locations (Shanghai)"),
    "umc_fab": dict(
        url="https://www.umc.com/en/Company/about_umc/page/Global_Presence",
        covers="UMC fab locations (Fab 12A Tainan)"),
    "infineon_fab": dict(
        url="https://www.infineon.com/cms/en/about-infineon/company/manufacturing/",
        covers="Infineon front-end manufacturing (Dresden, Villach)"),
    "asml_hq": dict(
        url="https://www.asml.com/en/company/about-asml/locations",
        covers="ASML HQ / manufacturing (Veldhoven, Netherlands)"),
    "kioxia_fab": dict(
        url="https://www.kioxia.com/en-jp/about/fab.html",
        covers="Kioxia/Western Digital Yokkaichi & Kitakami NAND fabs"),
    # --- material choke-point sources ---
    "neon_market": dict(
        url="https://www.reuters.com/technology/exclusive-ukraine-halts-half-worlds-neon-output-chips-clouding-outlook-2022-03-11/",
        covers="Neon gas for DUV excimer lasers — Ukraine ~half of world output"),
    "helium_market": dict(
        url="https://www.usgs.gov/centers/national-minerals-information-center/helium-statistics-and-information",
        covers="Helium supply (USGS) — EUV/process cooling & purge"),
    "hf_dispute": dict(
        url="https://www.reuters.com/article/us-japan-southkorea-laborers-explainer-idUSKCN1U50EZ",
        covers="High-purity hydrogen fluoride — Japan's ~70-90% etch/clean share"),
    "wf6_market": dict(
        url="https://www.kantodenka.co.jp/english/products/",
        covers="Tungsten hexafluoride (WF6) for tungsten CVD"),
    "etch_gas": dict(
        url="https://www.linde-gas.com/en/products_and_supply/electronic_gases/index.html",
        covers="Fluorinated etch gases incl. C4F6 (hexafluorobutadiene)"),
    "quartz_market": dict(
        url="https://www.shinetsu.co.jp/en/products/quartz/",
        covers="Synthetic quartz — crucibles for crystal growth, EUV mask substrate"),
    "rare_earth_controls": dict(
        url="https://www.reuters.com/markets/commodities/china-restricts-rare-earth-exports-2023-2024/",
        covers="Rare-earth elements — China export controls; CMP/polishing & magnets"),
    "pellicle_market": dict(
        url="https://jp.mitsuichemicals.com/en/release/2020/2020_0707.htm",
        covers="EUV pellicle — Mitsui Chemicals / ASML, protects EUV photomask"),
    "sputter_market": dict(
        url="https://www.jx-nmm.com/english/business/quality_material/",
        covers="High-purity sputtering targets for PVD metallisation"),
    "resin_market": dict(
        url="https://www.sumitomo-chem.co.jp/english/products/",
        covers="Photoresist polymer resins & specialty monomers"),
    # --- MANUFACTURES gap-fill (products left unconnected by the backbone) ---
    "infineon_gan": dict(
        url="https://www.infineon.com/products/power/gallium-nitride",
        covers="Infineon CoolGaN gallium-nitride power devices"),
    "st_gan": dict(
        url="https://www.st.com/en/power-management/gallium-nitride-gan-power-ics.html",
        covers="STMicroelectronics MasterGaN gallium-nitride power ICs"),
    "infineon_nor": dict(
        url="https://www.infineon.com/products/memories/nor-flash",
        covers="Infineon SEMPER NOR flash memory"),
    "microchip_nor": dict(
        url="https://www.microchip.com/en-us/products/memory/serial-and-parallel-flash",
        covers="Microchip SuperFlash (SST) serial/parallel NOR flash"),
    # --- 2024 market-share sources for capacity_share_pct (weighting) ---
    "trendforce_foundry_4q24": dict(
        url="https://www.trendforce.com/presscenter/news/20250310-12510.html",
        covers="TrendForce 4Q24 foundry market share (TSMC 67%, Samsung 8%, SMIC, UMC, GF)"),
    "dram_share_2024": dict(
        url="https://wccftech.com/global-dram-industry-revenue-grows-by-13-6-quarter-over-quarter-samsung-still-leads-with-around-41-market-share/",
        covers="DRAM market share 2024 (Samsung ~41%, SK Hynix ~34%, Micron ~22%)"),
    "hbm_share_2024": dict(
        url="https://eureka.patsnap.com/insight/the-hbm-wars-sk-hynixs-dominance-samsungs-roadmap-and-the-looming-threat-of-cyclicality",
        covers="HBM market share 2024 (SK Hynix 54%, Samsung 39%, Micron 7%)"),
    "eda_share_2024": dict(
        url="https://semiengineering.com/the-state-of-the-eda-industry-in-2024/",
        covers="EDA market share 2024 (Synopsys 31%, Cadence 30%, Siemens 13%)"),
    "tsmc_customers_2024": dict(
        url="https://www.sec.gov/Archives/edgar/data/0001046179/000104617925000004/a4q24e_withguidancexfinal.htm",
        covers="TSMC FY2024 customer concentration (top-10 ~76%; Apple ~25%, Nvidia ~10%)"),
}


def _url(source_id: str) -> str:
    if source_id in SOURCES:
        return SOURCES[source_id]["url"]
    raise KeyError(f"Unknown source_id: {source_id!r}")


# --------------------------------------------------------------------------- #
# Layer 1 — country macro data (live fetch)
# --------------------------------------------------------------------------- #
# iso2 must match countries.csv. World Bank uses these codes; Taiwan ("TW") has
# no World Bank GDP, so it is filled from the IMF (ISO3 "TWN").
COUNTRY_NAMES = {
    "NL": "Netherlands", "US": "United States", "JP": "Japan", "DE": "Germany",
    "TW": "Taiwan", "CN": "China", "KR": "South Korea", "GB": "United Kingdom",
    "FR": "France", "CH": "Switzerland", "IL": "Israel", "SG": "Singapore",
    "AT": "Austria",
}


def _get_json(url: str, tries: int = 3, timeout: int = 30):
    last = None
    for t in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 — re-raised below after retries
            last = e
            if t < tries - 1:
                time.sleep(2)
    raise RuntimeError(f"Network fetch failed for {url}: {last}")


def _wb_latest(iso2: str, indicator: str, source: int | None = None):
    """Most recent non-null World Bank value -> (year, value) or None."""
    src = f"&source={source}" if source else ""
    url = (f"https://api.worldbank.org/v2/country/{iso2}/indicator/{indicator}"
           f"?format=json&mrv=5&per_page=20{src}")
    data = _get_json(url)
    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        return None
    for rec in data[1]:
        if rec.get("value") is not None:
            return rec["date"], rec["value"]
    return None


def _imf_gdp(iso3: str, year: str):
    """IMF WEO GDP (current US$, billions) for a given ISO3 & year -> USD float."""
    url = f"https://www.imf.org/external/datamapper/api/v1/NGDPD/{iso3}"
    data = _get_json(url)
    vals = data["values"]["NGDPD"][iso3]
    if year in vals and vals[year] is not None:
        return float(vals[year]) * 1e9  # IMF reports billions
    return None


def collect_countries() -> list[dict]:
    rows = []
    for iso2, name in COUNTRY_NAMES.items():
        gdp = _wb_latest(iso2, "NY.GDP.MKTP.CD")
        pol = _wb_latest(iso2, "GOV_WGI_PV.EST", source=3)
        if gdp:
            gdp_year, gdp_val, gdp_src = gdp[0], round(gdp[1]), _url("worldbank_gdp")
        elif iso2 == "TW":
            # World Bank has no Taiwan GDP — fall back to the IMF WEO.
            wgi_year = pol[0] if pol else "2024"
            imf_val = _imf_gdp("TWN", wgi_year) or _imf_gdp("TWN", "2024")
            gdp_year = wgi_year if _imf_gdp("TWN", wgi_year) else "2024"
            gdp_val = round(imf_val) if imf_val else ""
            gdp_src = _url("imf_weo_gdp")
        else:
            gdp_year, gdp_val, gdp_src = "", "", ""
            log.warning("No GDP found for %s (%s)", name, iso2)
        if pol:
            pol_year, pol_val = pol[0], round(pol[1], 4)
        else:
            pol_year, pol_val = "", ""
            log.warning("No political-stability score for %s (%s)", name, iso2)
        rows.append(dict(
            name=name, iso2=iso2,
            gdp_usd=gdp_val, gdp_year=gdp_year, gdp_source_url=gdp_src,
            political_risk_score=pol_val, political_risk_year=pol_year,
            political_risk_source_url=_url("worldbank_wgi_pv") if pol else "",
            source_date=ACCESSED))
        log.info("  %-15s GDP=%s (%s)  PV.EST=%s (%s)",
                 name, gdp_val, gdp_year, pol_val, pol_year)
    return rows


# --------------------------------------------------------------------------- #
# Layer 2 — facilities + OPERATES
# company names must exist in companies.csv; countries in countries.csv.
# capacity_wafers_month: approx 300mm-equiv wafer starts/month ("" = not reported)
# --------------------------------------------------------------------------- #
FACILITIES = [
    # name, city, country, type, capacity, operator, source_id
    ("TSMC Fab 18", "Tainan", "Taiwan", "fab", 130000, "TSMC", "tsmc_mfg"),
    ("TSMC Fab 12", "Hsinchu", "Taiwan", "fab", 100000, "TSMC", "tsmc_mfg"),
    ("TSMC Fab 21 (Arizona)", "Phoenix", "United States", "fab", 20000, "TSMC", "tsmc_mfg"),
    ("TSMC JASM", "Kumamoto", "Japan", "fab", 55000, "TSMC", "tsmc_mfg"),
    ("ESMC Dresden", "Dresden", "Germany", "fab", "", "TSMC", "esmc"),
    ("Samsung Pyeongtaek Campus", "Pyeongtaek", "South Korea", "fab", 300000, "Samsung Memory", "samsung_fab"),
    ("Samsung Hwaseong Campus", "Hwaseong", "South Korea", "fab", 200000, "Samsung Memory", "samsung_fab"),
    ("Samsung Taylor", "Taylor", "United States", "fab", "", "Samsung Foundry", "samsung_fab"),
    ("Intel Ocotillo", "Chandler", "United States", "fab", "", "Intel", "intel_fab"),
    ("Intel Rio Rancho", "Rio Rancho", "United States", "assembly", "", "Intel", "intel_fab"),
    ("GlobalFoundries Fab 8", "Malta", "United States", "fab", 60000, "GlobalFoundries", "gf_fab"),
    ("Micron Hiroshima", "Hiroshima", "Japan", "fab", "", "Micron", "micron_fab"),
    ("SK Hynix M16", "Icheon", "South Korea", "fab", "", "SK Hynix", "skhynix_fab"),
    ("SMIC SN1", "Shanghai", "China", "fab", 35000, "SMIC", "smic_fab"),
    ("UMC Fab 12A", "Tainan", "Taiwan", "fab", 90000, "UMC", "umc_fab"),
    ("Infineon Dresden", "Dresden", "Germany", "fab", "", "Infineon", "infineon_fab"),
    ("ASML Veldhoven HQ", "Veldhoven", "Netherlands", "R&D", "", "ASML", "asml_hq"),
    ("Kioxia Yokkaichi", "Yokkaichi", "Japan", "fab", "", "Kioxia", "kioxia_fab"),
]

# --------------------------------------------------------------------------- #
# Layer 3 — material choke-points (new Product nodes) + DEPENDS_ON
# --------------------------------------------------------------------------- #
MATERIAL_PRODUCTS = [
    # name, source_id   (all category "material")
    ("Neon gas", "neon_market"),
    ("Helium", "helium_market"),
    ("Hydrogen fluoride (HF)", "hf_dispute"),
    ("Tungsten hexafluoride (WF6)", "wf6_market"),
    ("Hexafluorobutadiene (C4F6)", "etch_gas"),
    ("Synthetic quartz", "quartz_market"),
    ("Rare earth elements", "rare_earth_controls"),
    ("EUV pellicle", "pellicle_market"),
    ("Sputtering targets", "sputter_market"),
    ("Photoresist polymer resin", "resin_market"),
]

# MANUFACTURES gap-fill: products defined in the backbone but never connected to
# a maker (they showed up as isolated nodes). company, product, source_id.
MANUFACTURES_FILL = [
    ("Infineon", "GaN power device", "infineon_gan"),
    ("STMicroelectronics", "GaN power device", "st_gan"),
    ("Infineon", "NOR flash", "infineon_nor"),
    ("Microchip", "NOR flash", "microchip_nor"),
]

# Weighting layer 1: sourced 2024 capacity/market shares that OVERRIDE the
# backbone's capacity_share_pct on existing (company -> product) MANUFACTURES
# edges. company, product, capacity_share_pct, source_id.
CAPACITY_SHARES = [
    # HBM — the AI-memory choke point (backbone had this wrong)
    ("SK Hynix", "HBM", 54, "hbm_share_2024"),
    ("Samsung Memory", "HBM", 39, "hbm_share_2024"),
    ("Micron", "HBM", 7, "hbm_share_2024"),
    # DRAM
    ("Samsung Memory", "DRAM", 41, "dram_share_2024"),
    ("SK Hynix", "DRAM", 34, "dram_share_2024"),
    ("Micron", "DRAM", 22, "dram_share_2024"),
    # EDA software
    ("Synopsys", "EDA software", 31, "eda_share_2024"),
    ("Cadence", "EDA software", 30, "eda_share_2024"),
    ("Siemens EDA", "EDA software", 13, "eda_share_2024"),
]

# Weighting layer 2: sourced company->company volume shares on existing SUPPLIES
# edges (share of the supplier's output going to that customer). Only the few
# links public filings actually quantify. source, target, product_category,
# volume_share_pct, source_id.
SUPPLY_SHARES = [
    ("TSMC", "Apple", "logic", 25.2, "tsmc_customers_2024"),
    ("TSMC", "Nvidia", "logic", 10.1, "tsmc_customers_2024"),
]

MATERIAL_DEPENDS = [
    # source product, target product, dependency_type, source_id
    ("DUV lithography system", "Neon gas", "consumable", "neon_market"),
    ("EUV lithography system", "Helium", "consumable", "helium_market"),
    ("EUV lithography system", "EUV pellicle", "component", "pellicle_market"),
    ("Etch system", "Hexafluorobutadiene (C4F6)", "consumable", "etch_gas"),
    ("CVD deposition system", "Tungsten hexafluoride (WF6)", "consumable", "wf6_market"),
    ("Wafer cleaning system", "Hydrogen fluoride (HF)", "consumable", "hf_dispute"),
    ("Wet process chemicals", "Hydrogen fluoride (HF)", "feedstock", "hf_dispute"),
    ("ArF photoresist", "Photoresist polymer resin", "feedstock", "resin_market"),
    ("EUV photoresist", "Photoresist polymer resin", "feedstock", "resin_market"),
    ("CMP slurry", "Rare earth elements", "feedstock", "rare_earth_controls"),
    ("300mm silicon wafer", "Synthetic quartz", "tooling", "quartz_market"),
    ("EUV mask blank", "Synthetic quartz", "substrate", "quartz_market"),
    ("PVD deposition system", "Sputtering targets", "consumable", "sputter_market"),
]


# --------------------------------------------------------------------------- #
# Integrity helpers (read backbone CSVs written by 01)
# --------------------------------------------------------------------------- #
def _read_names(filename: str, col: str) -> set[str]:
    import csv
    path = DATA_RAW / filename
    if not path.exists():
        raise SystemExit(f"{filename} not found — run scripts/01_collect_backbone.py first.")
    with path.open(newline="", encoding="utf-8") as fh:
        return {row[col] for row in csv.DictReader(fh)}


def main() -> None:
    companies = _read_names("companies.csv", "name")
    countries = _read_names("countries.csv", "name")
    backbone_products = _read_names("products.csv", "name")

    # ----- Layer 1: countries -----
    log.info("Layer 1 — fetching country GDP & political-stability data ...")
    country_rows = collect_countries()
    write_csv(DATA_RAW / "country_enrichment.csv",
              ["name", "iso2", "gdp_usd", "gdp_year", "gdp_source_url",
               "political_risk_score", "political_risk_year",
               "political_risk_source_url", "source_date"],
              country_rows)

    # ----- Layer 2: facilities + operates -----
    facility_rows, operates_rows = [], []
    problems = []
    facility_names = {f[0] for f in FACILITIES}
    for name, city, country, ftype, cap, operator, sid in FACILITIES:
        if operator not in companies:
            problems.append(f"OPERATES company unknown: {operator!r} ({name})")
        if country not in countries:
            problems.append(f"Facility country not a Country node: {country!r} ({name})")
        facility_rows.append(dict(
            name=name, city=city, country=country, type=ftype,
            capacity_wafers_month=cap, source_url=_url(sid), source_date=ACCESSED))
        operates_rows.append(dict(
            company=operator, facility=name,
            source_url=_url(sid), source_date=ACCESSED))
    write_csv(DATA_RAW / "facilities.csv",
              ["name", "city", "country", "type", "capacity_wafers_month",
               "source_url", "source_date"], facility_rows)
    write_csv(DATA_RAW / "operates.csv",
              ["company", "facility", "source_url", "source_date"], operates_rows)

    # ----- Layer 3: material products + dependencies -----
    material_rows = []
    new_product_names = set()
    for name, sid in MATERIAL_PRODUCTS:
        new_product_names.add(name)
        material_rows.append(dict(
            name=name, category="material", node_size_nm="", year_introduced="",
            source_url=_url(sid), source_date=ACCESSED))
    known_products = backbone_products | new_product_names
    dep_rows = []
    for src, dst, dtype, sid in MATERIAL_DEPENDS:
        if src not in known_products:
            problems.append(f"DEPENDS_ON source product unknown: {src!r}")
        if dst not in known_products:
            problems.append(f"DEPENDS_ON target product unknown: {dst!r}")
        dep_rows.append(dict(
            source=src, target=dst, dependency_type=dtype,
            source_url=_url(sid), source_date=ACCESSED))

    # MANUFACTURES gap-fill (Company -> Product), same schema as manufactures.csv.
    mfill_rows = []
    for company, product, sid in MANUFACTURES_FILL:
        if company not in companies:
            problems.append(f"MANUFACTURES fill company unknown: {company!r}")
        if product not in known_products:
            problems.append(f"MANUFACTURES fill product unknown: {product!r}")
        mfill_rows.append(dict(
            company=company, product=product, process_node_nm="",
            capacity_share_pct="", source_url=_url(sid), source_date=ACCESSED))

    # ---- weighting layer 1: capacity-share overrides ----
    import csv as _csv
    man_pairs = {(r["company"], r["product"])
                 for r in _csv.DictReader((DATA_RAW / "manufactures.csv")
                                          .open(encoding="utf-8"))}
    man_pairs |= {(c, p) for c, p, _ in MANUFACTURES_FILL}
    cap_rows = []
    for company, product, share, sid in CAPACITY_SHARES:
        if (company, product) not in man_pairs:
            problems.append(f"capacity-share pair has no MANUFACTURES edge: "
                            f"{company!r}->{product!r}")
        cap_rows.append(dict(company=company, product=product,
                             capacity_share_pct=share,
                             source_url=_url(sid), source_date=ACCESSED))

    # ---- weighting layer 2: company->company supply shares ----
    sup_triples = {(r["source"], r["target"], r["product_category"])
                   for r in _csv.DictReader((DATA_RAW / "supplies.csv")
                                            .open(encoding="utf-8"))}
    sup_rows = []
    for s, t, cat, share, sid in SUPPLY_SHARES:
        if (s, t, cat) not in sup_triples:
            problems.append(f"supply-share has no SUPPLIES edge: "
                            f"{s!r}->{t!r} [{cat}]")
        sup_rows.append(dict(source=s, target=t, product_category=cat,
                             volume_share_pct=share,
                             source_url=_url(sid), source_date=ACCESSED))

    if problems:
        for p in sorted(set(problems)):
            log.error("  %s", p)
        raise SystemExit(f"Integrity check failed with {len(set(problems))} problem(s).")

    write_csv(DATA_RAW / "materials.csv",
              ["name", "category", "node_size_nm", "year_introduced",
               "source_url", "source_date"], material_rows)
    write_csv(DATA_RAW / "material_depends_on.csv",
              ["source", "target", "dependency_type", "source_url", "source_date"],
              dep_rows)
    write_csv(DATA_RAW / "manufactures_enrichment.csv",
              ["company", "product", "process_node_nm", "capacity_share_pct",
               "source_url", "source_date"], mfill_rows)
    write_csv(DATA_RAW / "capacity_shares.csv",
              ["company", "product", "capacity_share_pct", "source_url",
               "source_date"], cap_rows)
    write_csv(DATA_RAW / "supply_shares.csv",
              ["source", "target", "product_category", "volume_share_pct",
               "source_url", "source_date"], sup_rows)

    # ----- Log sources -----
    used_ids = ({"worldbank_gdp", "worldbank_wgi_pv", "imf_weo_gdp"}
                | {f[6] for f in FACILITIES}
                | {sid for _, sid in MATERIAL_PRODUCTS}
                | {sid for *_, sid in MATERIAL_DEPENDS}
                | {sid for *_, sid in MANUFACTURES_FILL}
                | {sid for *_, sid in CAPACITY_SHARES}
                | {sid for *_, sid in SUPPLY_SHARES})
    added = log_sources([
        dict(source_id=sid, url=SOURCES[sid]["url"], date_accessed=ACCESSED,
             covers=SOURCES[sid]["covers"], notes="enrichment (Priority 2/3)")
        for sid in sorted(used_ids)])

    # ----- Summary -----
    log.info("Enrichment collection complete.")
    log.info("  country_enrichment : %d", len(country_rows))
    log.info("  facilities         : %d", len(facility_rows))
    log.info("  OPERATES           : %d", len(operates_rows))
    log.info("  material products  : %d", len(material_rows))
    log.info("  material DEPENDS_ON: %d", len(dep_rows))
    log.info("  MANUFACTURES fill  : %d", len(mfill_rows))
    log.info("  capacity shares    : %d", len(cap_rows))
    log.info("  supply shares      : %d", len(sup_rows))
    log.info("  sources logged     : %d new", added)
    log.info("Output written to %s", DATA_RAW)
    log.info("Next: python scripts/03_import_neo4j.py --import --export-nx")
    _ = facility_names  # (kept for symmetry / future facility-facility links)


if __name__ == "__main__":
    main()
