"""01 — Priority 1 backbone data collection (expanded).

Manually-coded, source-backed model of ~100 of the most important companies in
the global semiconductor supply chain and the relationships between them, across
every tier:

    materials feedstock (ABF film, mask blanks)
        -> wafers / photoresist / gases / photomasks / substrates
            -> wafer-fab & test equipment  (+ their subsystem suppliers)
                -> foundries / IDMs
                    -> EDA & IP (design enablers, cross-cutting)
                        -> fabless designers
                            -> OSAT (assembly & test) -> EMS

Every SUPPLIES and MANUFACTURES edge carries a source_id that resolves to a
public URL + access date (the project's "no data without a source" rule). An
internal integrity check fails fast if any relationship references an unknown
company or product, so referential mistakes never reach the CSVs.

Run:
    python scripts/01_collect_backbone.py

NOTE ON FIGURES: market caps, employee counts and share percentages are public
industry-reported approximations (company filings, Wikipedia, SEMI/WSTS,
companiesmarketcap.com) as accessed on the date below — good for *structural*
network analysis but not to be quoted as exact financials. Exact annual contract
values (value_usd_annual) are rarely public and are left blank, not fabricated.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import DATA_RAW, log, log_sources, write_csv  # noqa: E402

ACCESSED = "2026-06-06"  # date all sources were accessed

# --------------------------------------------------------------------------- #
# Source registry  (relationship / industry-level sources).
# Company node attributes are sourced per-company via the `wiki` slug below.
# --------------------------------------------------------------------------- #
SOURCES = {
    "marketcap": dict(
        url="https://companiesmarketcap.com/semiconductors/largest-semiconductor-companies-by-market-cap/",
        covers="Market capitalisation of semiconductor companies (approx.)"),
    "semi_equipment": dict(
        url="https://www.semi.org/en/products-services/market-data/equipment",
        covers="Worldwide semiconductor manufacturing equipment market shares"),
    "semi_materials": dict(
        url="https://www.semi.org/en/products-services/market-data/materials",
        covers="SEMI materials market — silicon wafers, gases, chemicals"),
    "wsts_market": dict(
        url="https://www.wsts.org/",
        covers="World Semiconductor Trade Statistics — market size by segment"),
    "asml_ar2024": dict(
        url="https://www.asml.com/en/investors/annual-report/2024",
        covers="ASML 2024 Annual Report — customers, EUV/DUV shipments"),
    "asml_zeiss": dict(
        url="https://www.asml.com/en/technology/lithography-principles/zeiss-optics",
        covers="ASML–Carl Zeiss SMT exclusive EUV optics partnership"),
    "tsmc_ar2024": dict(
        url="https://investor.tsmc.com/english/annual-reports",
        covers="TSMC 2024 Annual Report — major customers, process nodes"),
    "tsmc_esg": dict(
        url="https://esg.tsmc.com/en/resource/supply-chain.html",
        covers="TSMC supply-chain / ESG report — material & equipment suppliers"),
    "arm_partners": dict(
        url="https://www.arm.com/partners",
        covers="Arm IP licensees / ecosystem partners"),
    "hbm_nvidia": dict(
        url="https://www.reuters.com/technology/sk-hynix-says-2025-hbm-chips-sold-out-2024-05-02/",
        covers="HBM memory supply (SK Hynix/Samsung/Micron) to Nvidia AI GPUs"),
    "wafer_market": dict(
        url="https://www.semi.org/en/products-services/market-data/materials/semiconductor-silicon-wafer",
        covers="Silicon wafer market — Shin-Etsu, SUMCO, GlobalWafers, Siltronic, SK Siltron"),
    "resist_market": dict(
        url="https://www.reuters.com/article/us-japan-southkorea-laborers-explainer-idUSKCN1U50EZ",
        covers="Photoresist & specialty-chemical supply (Japan's ~90% resist share)"),
    "gas_market": dict(
        url="https://www.airliquide.com/group/activities/electronics",
        covers="Electronics specialty & bulk gases to fabs (Air Liquide/Linde/Air Products/TNSC/Messer)"),
    "photomask_market": dict(
        url="https://www.photronics.com/products/",
        covers="Photomask market — Photronics, Toppan, Hoya (mask blanks)"),
    "substrate_market": dict(
        url="https://www.unimicron.com/en/products/",
        covers="IC / ABF substrate market — Unimicron, Ibiden, Shinko, AT&S, Nan Ya PCB"),
    "abf_market": dict(
        url="https://www.ajinomoto.com/ir/event/pdf/2021/ABF_briefing.pdf",
        covers="Ajinomoto Build-up Film (ABF) — near-monopoly substrate material"),
    "eda_market": dict(
        url="https://www.semi.org/en/communities/esd-alliance",
        covers="EDA market — Synopsys, Cadence, Siemens EDA (~3-firm oligopoly)"),
    "ip_market": dict(
        url="https://www.arm.com/company",
        covers="Semiconductor IP market — Arm, Synopsys, Cadence, Imagination, SiFive, Ceva"),
    "ate_market": dict(
        url="https://www.advantest.com/products/",
        covers="Automated test equipment (ATE) — Advantest, Teradyne"),
    "subsystem_market": dict(
        url="https://www.mks.com/n/semiconductor",
        covers="Wafer-fab equipment subsystems — MKS, Ultra Clean, Edwards, Zeiss"),
    "soi_market": dict(
        url="https://www.soitec.com/en/products",
        covers="SOI / engineered substrates — Soitec"),
    "osat_market": dict(
        url="https://www.yolegroup.com/product/report/status-of-the-advanced-packaging-industry/",
        covers="OSAT / advanced-packaging market (ASE, Amkor, JCET, PTI, Tongfu, ...)"),
    "intel_foundry": dict(
        url="https://www.intel.com/content/www/us/en/foundry/overview.html",
        covers="Intel Foundry — process nodes and offerings"),
    "foundry_share": dict(
        url="https://www.trendforce.com/presscenter/news/",
        covers="TrendForce foundry revenue ranking & market share by quarter"),
}

# --------------------------------------------------------------------------- #
# Companies (nodes)
# type: fab / fabless / IDM / equipment / subsystem / materials / substrate /
#       photomask / gases / EDA / IP / EMS
# market_cap_usd / employees left "" where private/subsidiary or uncertain.
# --------------------------------------------------------------------------- #
COMPANIES = [
    # ===== Wafer-fab & test EQUIPMENT =====
    dict(name="ASML", country="Netherlands", region="Europe", type="equipment",
         market_cap_usd=320_000_000_000, founded=1984, employees=44_000, wiki="ASML_Holding"),
    dict(name="Applied Materials", country="United States", region="North America", type="equipment",
         market_cap_usd=145_000_000_000, founded=1967, employees=35_700, wiki="Applied_Materials"),
    dict(name="Lam Research", country="United States", region="North America", type="equipment",
         market_cap_usd=110_000_000_000, founded=1980, employees=17_200, wiki="Lam_Research"),
    dict(name="KLA", country="United States", region="North America", type="equipment",
         market_cap_usd=95_000_000_000, founded=1997, employees=15_000, wiki="KLA_Corporation"),
    dict(name="Tokyo Electron", country="Japan", region="Asia", type="equipment",
         market_cap_usd=110_000_000_000, founded=1963, employees=18_600, wiki="Tokyo_Electron"),
    dict(name="Nikon", country="Japan", region="Asia", type="equipment",
         market_cap_usd=5_000_000_000, founded=1917, employees=19_000, wiki="Nikon"),
    dict(name="Canon", country="Japan", region="Asia", type="equipment",
         market_cap_usd=40_000_000_000, founded=1937, employees=180_000, wiki="Canon_Inc."),
    dict(name="ASM International", country="Netherlands", region="Europe", type="equipment",
         market_cap_usd=30_000_000_000, founded=1968, employees=5_000, wiki="ASM_International"),
    dict(name="Screen Holdings", country="Japan", region="Asia", type="equipment",
         market_cap_usd=9_000_000_000, founded=1943, employees=8_000, wiki="Dainippon_Screen"),
    dict(name="Hitachi High-Tech", country="Japan", region="Asia", type="equipment",
         market_cap_usd="", founded=2001, employees=11_000, wiki="Hitachi_High-Tech"),
    dict(name="Advantest", country="Japan", region="Asia", type="equipment",
         market_cap_usd=35_000_000_000, founded=1954, employees=7_000, wiki="Advantest"),
    dict(name="Teradyne", country="United States", region="North America", type="equipment",
         market_cap_usd=18_000_000_000, founded=1960, employees=6_000, wiki="Teradyne"),
    dict(name="Onto Innovation", country="United States", region="North America", type="equipment",
         market_cap_usd=8_000_000_000, founded=2019, employees=2_400, wiki="Onto_Innovation"),
    dict(name="Lasertec", country="Japan", region="Asia", type="equipment",
         market_cap_usd=15_000_000_000, founded=1960, employees=1_000, wiki="Lasertec"),
    dict(name="Disco Corporation", country="Japan", region="Asia", type="equipment",
         market_cap_usd=30_000_000_000, founded=1937, employees=6_000, wiki="Disco_Corporation"),
    dict(name="Kulicke & Soffa", country="Singapore", region="Asia", type="equipment",
         market_cap_usd=3_000_000_000, founded=1951, employees=3_000, wiki="Kulicke_%26_Soffa"),

    # ===== Equipment SUBSYSTEMS (sell to equipment makers) =====
    dict(name="MKS Instruments", country="United States", region="North America", type="subsystem",
         market_cap_usd=8_000_000_000, founded=1961, employees=11_000, wiki="MKS_Instruments"),
    dict(name="Ultra Clean Holdings", country="United States", region="North America", type="subsystem",
         market_cap_usd=2_000_000_000, founded=1991, employees=6_000, wiki="Ultra_Clean_Holdings"),
    dict(name="Edwards Vacuum", country="United Kingdom", region="Europe", type="subsystem",
         market_cap_usd="", founded=1919, employees=8_000, wiki="Edwards_Vacuum"),
    dict(name="Carl Zeiss SMT", country="Germany", region="Europe", type="subsystem",
         market_cap_usd="", founded=1846, employees=6_000, wiki="Carl_Zeiss_AG"),

    # ===== Silicon WAFERS =====
    dict(name="Shin-Etsu Chemical", country="Japan", region="Asia", type="materials",
         market_cap_usd=80_000_000_000, founded=1926, employees=26_000, wiki="Shin-Etsu_Chemical"),
    dict(name="SUMCO", country="Japan", region="Asia", type="materials",
         market_cap_usd=6_000_000_000, founded=1999, employees=9_400, wiki="SUMCO"),
    dict(name="GlobalWafers", country="Taiwan", region="Asia", type="materials",
         market_cap_usd=7_000_000_000, founded=2011, employees=8_000, wiki="GlobalWafers"),
    dict(name="Siltronic", country="Germany", region="Europe", type="materials",
         market_cap_usd=3_000_000_000, founded=2004, employees=4_400, wiki="Siltronic"),
    dict(name="SK Siltron", country="South Korea", region="Asia", type="materials",
         market_cap_usd="", founded=1983, employees=4_000, wiki="SK_Siltron"),

    # ===== Photoresist / process CHEMICALS / CMP =====
    dict(name="Tokyo Ohka Kogyo", country="Japan", region="Asia", type="materials",
         market_cap_usd=5_000_000_000, founded=1940, employees=4_000, wiki="Tokyo_Ohka_Kogyo"),
    dict(name="JSR Corporation", country="Japan", region="Asia", type="materials",
         market_cap_usd=6_000_000_000, founded=1957, employees=9_000, wiki="JSR_Corporation"),
    dict(name="Fujifilm", country="Japan", region="Asia", type="materials",
         market_cap_usd=40_000_000_000, founded=1934, employees=74_000, wiki="Fujifilm"),
    dict(name="Merck KGaA", country="Germany", region="Europe", type="materials",
         market_cap_usd=70_000_000_000, founded=1668, employees=63_000, wiki="Merck_Group"),
    dict(name="DuPont", country="United States", region="North America", type="materials",
         market_cap_usd=33_000_000_000, founded=1802, employees=24_000, wiki="DuPont_(2017%E2%80%93present)"),
    dict(name="Sumitomo Chemical", country="Japan", region="Asia", type="materials",
         market_cap_usd=4_000_000_000, founded=1913, employees=35_000, wiki="Sumitomo_Chemical"),
    dict(name="Resonac", country="Japan", region="Asia", type="materials",
         market_cap_usd=5_000_000_000, founded=1939, employees=24_000, wiki="Resonac"),
    dict(name="Dongjin Semichem", country="South Korea", region="Asia", type="materials",
         market_cap_usd="", founded=1967, employees=2_000, wiki="Dongjin_Semichem"),
    dict(name="Entegris", country="United States", region="North America", type="materials",
         market_cap_usd=16_000_000_000, founded=1966, employees=9_400, wiki="Entegris"),

    # ===== Industrial / specialty GASES =====
    dict(name="Air Liquide", country="France", region="Europe", type="gases",
         market_cap_usd=110_000_000_000, founded=1902, employees=67_000, wiki="Air_Liquide"),
    dict(name="Linde", country="Germany", region="Europe", type="gases",
         market_cap_usd=210_000_000_000, founded=1879, employees=66_000, wiki="Linde_plc"),
    dict(name="Air Products", country="United States", region="North America", type="gases",
         market_cap_usd=63_000_000_000, founded=1940, employees=23_000, wiki="Air_Products_and_Chemicals"),
    dict(name="Taiyo Nippon Sanso", country="Japan", region="Asia", type="gases",
         market_cap_usd=15_000_000_000, founded=1910, employees=19_000, wiki="Nippon_Sanso"),
    dict(name="Messer", country="Germany", region="Europe", type="gases",
         market_cap_usd="", founded=1898, employees=11_000, wiki="Messer_Group"),

    # ===== PHOTOMASKS / mask blanks =====
    dict(name="Photronics", country="United States", region="North America", type="photomask",
         market_cap_usd=1_500_000_000, founded=1969, employees=1_900, wiki="Photronics"),
    dict(name="Toppan Photomask", country="Japan", region="Asia", type="photomask",
         market_cap_usd="", founded=1900, employees=3_000, wiki="Toppan"),
    dict(name="Hoya", country="Japan", region="Asia", type="photomask",
         market_cap_usd=45_000_000_000, founded=1941, employees=37_000, wiki="Hoya_Corporation"),

    # ===== SUBSTRATES (ABF / IC substrate) =====
    dict(name="Ajinomoto", country="Japan", region="Asia", type="materials",
         market_cap_usd=20_000_000_000, founded=1909, employees=34_000, wiki="Ajinomoto"),
    dict(name="Unimicron", country="Taiwan", region="Asia", type="substrate",
         market_cap_usd=6_000_000_000, founded=1990, employees=20_000, wiki="Unimicron"),
    dict(name="Ibiden", country="Japan", region="Asia", type="substrate",
         market_cap_usd=6_000_000_000, founded=1912, employees=14_000, wiki="Ibiden"),
    dict(name="Shinko Electric Industries", country="Japan", region="Asia", type="substrate",
         market_cap_usd=5_000_000_000, founded=1946, employees=6_000, wiki="Shinko_Electric_Industries"),
    dict(name="AT&S", country="Austria", region="Europe", type="substrate",
         market_cap_usd=1_000_000_000, founded=1987, employees=14_000, wiki="AT%26S"),
    dict(name="Nan Ya PCB", country="Taiwan", region="Asia", type="substrate",
         market_cap_usd=2_000_000_000, founded=1997, employees=6_000, wiki="Nan_Ya_PCB"),
    dict(name="Soitec", country="France", region="Europe", type="materials",
         market_cap_usd=4_000_000_000, founded=1992, employees=2_000, wiki="Soitec"),

    # ===== FOUNDRIES =====
    dict(name="TSMC", country="Taiwan", region="Asia", type="fab",
         market_cap_usd=900_000_000_000, founded=1987, employees=76_000, wiki="TSMC"),
    dict(name="Samsung Foundry", country="South Korea", region="Asia", type="fab",
         market_cap_usd="", founded=2005, employees=20_000, wiki="Samsung_Foundry"),
    dict(name="GlobalFoundries", country="United States", region="North America", type="fab",
         market_cap_usd=25_000_000_000, founded=2009, employees=13_000, wiki="GlobalFoundries"),
    dict(name="UMC", country="Taiwan", region="Asia", type="fab",
         market_cap_usd=18_000_000_000, founded=1980, employees=20_000, wiki="United_Microelectronics_Corporation"),
    dict(name="SMIC", country="China", region="Asia", type="fab",
         market_cap_usd=50_000_000_000, founded=2000, employees=20_000, wiki="Semiconductor_Manufacturing_International_Corporation"),
    dict(name="Hua Hong Semiconductor", country="China", region="Asia", type="fab",
         market_cap_usd=6_000_000_000, founded=1996, employees=6_000, wiki="Hua_Hong_Semiconductor"),
    dict(name="Tower Semiconductor", country="Israel", region="Middle East", type="fab",
         market_cap_usd=5_000_000_000, founded=1993, employees=6_000, wiki="Tower_Semiconductor"),
    dict(name="Powerchip (PSMC)", country="Taiwan", region="Asia", type="fab",
         market_cap_usd=3_000_000_000, founded=1994, employees=6_000, wiki="Powerchip"),
    dict(name="Vanguard (VIS)", country="Taiwan", region="Asia", type="fab",
         market_cap_usd=6_000_000_000, founded=1994, employees=5_000, wiki="Vanguard_International_Semiconductor"),
    dict(name="Nexchip", country="China", region="Asia", type="fab",
         market_cap_usd=6_000_000_000, founded=2015, employees=4_000, wiki="Nexchip"),

    # ===== IDMs (memory) =====
    dict(name="Samsung Memory", country="South Korea", region="Asia", type="IDM",
         market_cap_usd="", founded=1983, employees=40_000, wiki="Samsung_Electronics"),
    dict(name="SK Hynix", country="South Korea", region="Asia", type="IDM",
         market_cap_usd=120_000_000_000, founded=1983, employees=31_000, wiki="SK_Hynix"),
    dict(name="Micron", country="United States", region="North America", type="IDM",
         market_cap_usd=110_000_000_000, founded=1978, employees=48_000, wiki="Micron_Technology"),
    dict(name="Kioxia", country="Japan", region="Asia", type="IDM",
         market_cap_usd=10_000_000_000, founded=2017, employees=15_000, wiki="Kioxia"),
    dict(name="Western Digital", country="United States", region="North America", type="IDM",
         market_cap_usd=22_000_000_000, founded=1970, employees=51_000, wiki="Western_Digital"),
    dict(name="Nanya Technology", country="Taiwan", region="Asia", type="IDM",
         market_cap_usd=5_000_000_000, founded=1995, employees=4_000, wiki="Nanya_Technology"),

    # ===== IDMs (logic / analog / power) =====
    dict(name="Intel", country="United States", region="North America", type="IDM",
         market_cap_usd=130_000_000_000, founded=1968, employees=108_000, wiki="Intel"),
    dict(name="Infineon", country="Germany", region="Europe", type="IDM",
         market_cap_usd=45_000_000_000, founded=1999, employees=58_000, wiki="Infineon_Technologies"),
    dict(name="STMicroelectronics", country="Switzerland", region="Europe", type="IDM",
         market_cap_usd=25_000_000_000, founded=1987, employees=50_000, wiki="STMicroelectronics"),
    dict(name="NXP", country="Netherlands", region="Europe", type="IDM",
         market_cap_usd=55_000_000_000, founded=2006, employees=34_000, wiki="NXP_Semiconductors"),
    dict(name="Texas Instruments", country="United States", region="North America", type="IDM",
         market_cap_usd=170_000_000_000, founded=1930, employees=34_000, wiki="Texas_Instruments"),
    dict(name="Analog Devices", country="United States", region="North America", type="IDM",
         market_cap_usd=110_000_000_000, founded=1965, employees=24_000, wiki="Analog_Devices"),
    dict(name="Microchip", country="United States", region="North America", type="IDM",
         market_cap_usd=40_000_000_000, founded=1989, employees=22_000, wiki="Microchip_Technology"),
    dict(name="onsemi", country="United States", region="North America", type="IDM",
         market_cap_usd=30_000_000_000, founded=1999, employees=32_000, wiki="Onsemi"),
    dict(name="Renesas", country="Japan", region="Asia", type="IDM",
         market_cap_usd=30_000_000_000, founded=2010, employees=21_000, wiki="Renesas_Electronics"),
    dict(name="Rohm", country="Japan", region="Asia", type="IDM",
         market_cap_usd=6_000_000_000, founded=1958, employees=24_000, wiki="Rohm"),
    dict(name="Wolfspeed", country="United States", region="North America", type="IDM",
         market_cap_usd=1_000_000_000, founded=1987, employees=5_000, wiki="Wolfspeed"),

    # ===== FABLESS designers =====
    dict(name="Nvidia", country="United States", region="North America", type="fabless",
         market_cap_usd=3_000_000_000_000, founded=1993, employees=30_000, wiki="Nvidia"),
    dict(name="AMD", country="United States", region="North America", type="fabless",
         market_cap_usd=200_000_000_000, founded=1969, employees=26_000, wiki="AMD"),
    dict(name="Qualcomm", country="United States", region="North America", type="fabless",
         market_cap_usd=180_000_000_000, founded=1985, employees=50_000, wiki="Qualcomm"),
    dict(name="Broadcom", country="United States", region="North America", type="fabless",
         market_cap_usd=700_000_000_000, founded=1991, employees=20_000, wiki="Broadcom"),
    dict(name="MediaTek", country="Taiwan", region="Asia", type="fabless",
         market_cap_usd=70_000_000_000, founded=1997, employees=20_000, wiki="MediaTek"),
    dict(name="Apple", country="United States", region="North America", type="fabless",
         market_cap_usd=3_200_000_000_000, founded=1976, employees=164_000, wiki="Apple_Inc."),
    dict(name="Marvell", country="United States", region="North America", type="fabless",
         market_cap_usd=60_000_000_000, founded=1995, employees=6_500, wiki="Marvell_Technology"),
    dict(name="Realtek", country="Taiwan", region="Asia", type="fabless",
         market_cap_usd=8_000_000_000, founded=1987, employees=6_000, wiki="Realtek"),
    dict(name="Novatek", country="Taiwan", region="Asia", type="fabless",
         market_cap_usd=10_000_000_000, founded=1997, employees=4_000, wiki="Novatek_Microelectronics"),
    dict(name="HiSilicon", country="China", region="Asia", type="fabless",
         market_cap_usd="", founded=2004, employees=7_000, wiki="HiSilicon"),
    dict(name="Google", country="United States", region="North America", type="fabless",
         market_cap_usd=2_000_000_000_000, founded=1998, employees=180_000, wiki="Google"),
    dict(name="Amazon", country="United States", region="North America", type="fabless",
         market_cap_usd=1_900_000_000_000, founded=1994, employees=1_500_000, wiki="Amazon_(company)"),
    dict(name="Microsoft", country="United States", region="North America", type="fabless",
         market_cap_usd=3_100_000_000_000, founded=1975, employees=221_000, wiki="Microsoft"),
    dict(name="Tesla", country="United States", region="North America", type="fabless",
         market_cap_usd=800_000_000_000, founded=2003, employees=140_000, wiki="Tesla,_Inc."),
    dict(name="Cerebras", country="United States", region="North America", type="fabless",
         market_cap_usd="", founded=2015, employees=400, wiki="Cerebras"),
    dict(name="Ambarella", country="United States", region="North America", type="fabless",
         market_cap_usd=2_000_000_000, founded=2004, employees=900, wiki="Ambarella_(company)"),

    # ===== EDA & IP =====
    dict(name="Synopsys", country="United States", region="North America", type="EDA",
         market_cap_usd=85_000_000_000, founded=1986, employees=20_000, wiki="Synopsys"),
    dict(name="Cadence", country="United States", region="North America", type="EDA",
         market_cap_usd=80_000_000_000, founded=1988, employees=12_000, wiki="Cadence_Design_Systems"),
    dict(name="Siemens EDA", country="United States", region="North America", type="EDA",
         market_cap_usd="", founded=1981, employees=6_000, wiki="Mentor_Graphics"),
    dict(name="ARM", country="United Kingdom", region="Europe", type="IP",
         market_cap_usd=140_000_000_000, founded=1990, employees=7_000, wiki="Arm_Holdings"),
    dict(name="Imagination Technologies", country="United Kingdom", region="Europe", type="IP",
         market_cap_usd="", founded=1985, employees=1_500, wiki="Imagination_Technologies"),
    dict(name="SiFive", country="United States", region="North America", type="IP",
         market_cap_usd="", founded=2015, employees=900, wiki="SiFive"),
    dict(name="Ceva", country="United States", region="North America", type="IP",
         market_cap_usd="", founded=1999, employees=500, wiki="Ceva,_Inc."),

    # ===== OSAT (assembly & test) / EMS =====
    dict(name="ASE Group", country="Taiwan", region="Asia", type="EMS",
         market_cap_usd=20_000_000_000, founded=1984, employees=90_000, wiki="ASE_Technology_Holding"),
    dict(name="Amkor", country="United States", region="North America", type="EMS",
         market_cap_usd=9_000_000_000, founded=1968, employees=30_000, wiki="Amkor_Technology"),
    dict(name="JCET", country="China", region="Asia", type="EMS",
         market_cap_usd=8_000_000_000, founded=1972, employees=25_000, wiki="JCET_Group"),
    dict(name="Powertech Technology", country="Taiwan", region="Asia", type="EMS",
         market_cap_usd=4_000_000_000, founded=1997, employees=15_000, wiki="Powertech_Technology"),
    dict(name="Tongfu Microelectronics", country="China", region="Asia", type="EMS",
         market_cap_usd=4_000_000_000, founded=1997, employees=20_000, wiki="Tongfu_Microelectronics"),
    dict(name="King Yuan Electronics", country="Taiwan", region="Asia", type="EMS",
         market_cap_usd=2_000_000_000, founded=1987, employees=18_000, wiki="King_Yuan_Electronics"),
    dict(name="ChipMOS", country="Taiwan", region="Asia", type="EMS",
         market_cap_usd=1_000_000_000, founded=1997, employees=7_000, wiki="ChipMOS"),
    dict(name="UTAC", country="Singapore", region="Asia", type="EMS",
         market_cap_usd="", founded=1997, employees=10_000, wiki="UTAC"),
    dict(name="Foxconn", country="Taiwan", region="Asia", type="EMS",
         market_cap_usd=70_000_000_000, founded=1974, employees=770_000, wiki="Foxconn"),
]

# --------------------------------------------------------------------------- #
# Countries (nodes)
# --------------------------------------------------------------------------- #
COUNTRIES = [
    dict(name="Netherlands", iso2="NL", region="Europe"),
    dict(name="United States", iso2="US", region="North America"),
    dict(name="Japan", iso2="JP", region="Asia"),
    dict(name="Germany", iso2="DE", region="Europe"),
    dict(name="Taiwan", iso2="TW", region="Asia"),
    dict(name="China", iso2="CN", region="Asia"),
    dict(name="South Korea", iso2="KR", region="Asia"),
    dict(name="United Kingdom", iso2="GB", region="Europe"),
    dict(name="France", iso2="FR", region="Europe"),
    dict(name="Switzerland", iso2="CH", region="Europe"),
    dict(name="Israel", iso2="IL", region="Middle East"),
    dict(name="Singapore", iso2="SG", region="Asia"),
    dict(name="Austria", iso2="AT", region="Europe"),
]

# --------------------------------------------------------------------------- #
# Products (nodes)  category: logic / memory / analog / equipment / material /
#                             EDA / IP / package
# --------------------------------------------------------------------------- #
PRODUCTS = [
    # logic nodes
    dict(name="2nm logic wafer", category="logic", node_size_nm=2, year_introduced=2025),
    dict(name="3nm logic wafer", category="logic", node_size_nm=3, year_introduced=2022),
    dict(name="5nm logic wafer", category="logic", node_size_nm=5, year_introduced=2020),
    dict(name="7nm logic wafer", category="logic", node_size_nm=7, year_introduced=2018),
    dict(name="16nm logic wafer", category="logic", node_size_nm=16, year_introduced=2015),
    dict(name="28nm logic wafer", category="logic", node_size_nm=28, year_introduced=2011),
    dict(name="65nm logic wafer", category="logic", node_size_nm=65, year_introduced=2006),
    dict(name="90nm logic wafer", category="logic", node_size_nm=90, year_introduced=2004),
    # memory
    dict(name="DRAM", category="memory", node_size_nm="", year_introduced=""),
    dict(name="DDR5 DRAM", category="memory", node_size_nm="", year_introduced=2021),
    dict(name="NAND flash", category="memory", node_size_nm="", year_introduced=""),
    dict(name="3D NAND", category="memory", node_size_nm="", year_introduced=2013),
    dict(name="HBM", category="memory", node_size_nm="", year_introduced=2015),
    dict(name="NOR flash", category="memory", node_size_nm="", year_introduced=""),
    # analog / power / sensors
    dict(name="Power semiconductor", category="analog", node_size_nm="", year_introduced=""),
    dict(name="SiC power device", category="analog", node_size_nm="", year_introduced=""),
    dict(name="GaN power device", category="analog", node_size_nm="", year_introduced=""),
    dict(name="Microcontroller (MCU)", category="analog", node_size_nm="", year_introduced=""),
    dict(name="Analog IC", category="analog", node_size_nm="", year_introduced=""),
    dict(name="CMOS image sensor", category="analog", node_size_nm="", year_introduced=""),
    dict(name="RF front-end module", category="analog", node_size_nm="", year_introduced=""),
    # equipment
    dict(name="EUV lithography system", category="equipment", node_size_nm="", year_introduced=2019),
    dict(name="DUV lithography system", category="equipment", node_size_nm="", year_introduced=2001),
    dict(name="Nanoimprint lithography system", category="equipment", node_size_nm="", year_introduced=2023),
    dict(name="Etch system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="CVD deposition system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="PVD deposition system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="ALD deposition system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="CMP system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="Ion implanter", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="Metrology & inspection system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="Automated test equipment", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="Wire bonder", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="Dicing saw", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="EUV mask inspection system", category="equipment", node_size_nm="", year_introduced=2017),
    dict(name="Wafer cleaning system", category="equipment", node_size_nm="", year_introduced=""),
    dict(name="EUV optics module", category="equipment", node_size_nm="", year_introduced=2019),
    # materials
    dict(name="300mm silicon wafer", category="material", node_size_nm="", year_introduced=2001),
    dict(name="200mm silicon wafer", category="material", node_size_nm="", year_introduced=1990),
    dict(name="SOI wafer", category="material", node_size_nm="", year_introduced=""),
    dict(name="SiC substrate", category="material", node_size_nm="", year_introduced=""),
    dict(name="ArF photoresist", category="material", node_size_nm="", year_introduced=""),
    dict(name="EUV photoresist", category="material", node_size_nm="", year_introduced=2019),
    dict(name="CMP slurry", category="material", node_size_nm="", year_introduced=""),
    dict(name="Specialty gases", category="material", node_size_nm="", year_introduced=""),
    dict(name="Bulk gases", category="material", node_size_nm="", year_introduced=""),
    dict(name="Photomask", category="material", node_size_nm="", year_introduced=""),
    dict(name="EUV mask blank", category="material", node_size_nm="", year_introduced=2019),
    dict(name="ABF build-up film", category="material", node_size_nm="", year_introduced=""),
    dict(name="IC substrate", category="material", node_size_nm="", year_introduced=""),
    dict(name="Wet process chemicals", category="material", node_size_nm="", year_introduced=""),
    # EDA / IP
    dict(name="EDA software", category="EDA", node_size_nm="", year_introduced=""),
    dict(name="CPU IP core", category="IP", node_size_nm="", year_introduced=""),
    dict(name="GPU IP core", category="IP", node_size_nm="", year_introduced=""),
    dict(name="RISC-V IP core", category="IP", node_size_nm="", year_introduced=""),
    dict(name="DSP IP core", category="IP", node_size_nm="", year_introduced=""),
    # packaging
    dict(name="Advanced packaging (2.5D/3D)", category="package", node_size_nm="", year_introduced=2016),
    dict(name="Flip-chip package", category="package", node_size_nm="", year_introduced=""),
]

# --------------------------------------------------------------------------- #
# Reusable customer/supplier groups (single source of truth for supply logic).
# All names must exist in COMPANIES — enforced by the integrity guard in main().
# --------------------------------------------------------------------------- #
LEADING_FABS = ["TSMC", "Samsung Foundry", "Intel"]
ALL_FOUNDRIES = ["TSMC", "Samsung Foundry", "GlobalFoundries", "UMC", "SMIC",
                 "Hua Hong Semiconductor", "Tower Semiconductor", "Powerchip (PSMC)",
                 "Vanguard (VIS)", "Nexchip"]
MEMORY_IDMS = ["Samsung Memory", "SK Hynix", "Micron", "Kioxia",
               "Western Digital", "Nanya Technology"]
ANALOG_IDMS = ["Infineon", "STMicroelectronics", "NXP", "Texas Instruments",
               "Analog Devices", "Microchip", "onsemi", "Renesas", "Rohm", "Wolfspeed"]
LOGIC_IDMS = ["Intel"]
ALL_IDMS = MEMORY_IDMS + ANALOG_IDMS + LOGIC_IDMS
# Everything that runs a fab and therefore consumes equipment + materials:
FABS_AND_IDMS = sorted(set(ALL_FOUNDRIES + ALL_IDMS))
FABLESS = ["Nvidia", "AMD", "Qualcomm", "Broadcom", "MediaTek", "Apple", "Marvell",
           "Realtek", "Novatek", "HiSilicon", "Google", "Amazon", "Microsoft",
           "Tesla", "Cerebras", "Ambarella"]
OSAT = ["ASE Group", "Amkor", "JCET", "Powertech Technology", "Tongfu Microelectronics",
        "King Yuan Electronics", "ChipMOS", "UTAC"]
SUBSTRATE_MAKERS = ["Unimicron", "Ibiden", "Shinko Electric Industries", "AT&S", "Nan Ya PCB"]
WAFER_MAKERS = ["Shin-Etsu Chemical", "SUMCO", "GlobalWafers", "Siltronic", "SK Siltron"]
GAS_MAJORS = ["Air Liquide", "Linde", "Air Products", "Taiyo Nippon Sanso", "Messer"]
EDA_FIRMS = ["Synopsys", "Cadence", "Siemens EDA"]
# Firms that design silicon and therefore consume EDA + IP:
DESIGNERS = sorted(set(FABLESS + ALL_IDMS + LEADING_FABS))

# --------------------------------------------------------------------------- #
# SUPPLIES (Company -> Company)
# helper: S(supplier, [customers], product_category, source_id, share="", year="")
# --------------------------------------------------------------------------- #
SUPPLIES: list[tuple] = []


def S(supplier, customers, category, source_id, share="", year=""):
    for c in customers:
        SUPPLIES.append((supplier, c, category, share, year, source_id))


# --- Equipment makers -> fabs/IDMs ---
S("ASML", FABS_AND_IDMS, "equipment", "asml_ar2024")
S("Nikon", ALL_FOUNDRIES + ANALOG_IDMS, "equipment", "semi_equipment")
S("Canon", ALL_FOUNDRIES + ANALOG_IDMS, "equipment", "semi_equipment")
for maker in ["Applied Materials", "Lam Research", "Tokyo Electron", "KLA",
              "ASM International", "Screen Holdings", "Hitachi High-Tech",
              "Onto Innovation"]:
    S(maker, FABS_AND_IDMS, "equipment", "semi_equipment")
# Test (ATE) -> IDMs + OSAT
S("Advantest", MEMORY_IDMS + ANALOG_IDMS + OSAT, "equipment", "ate_market")
S("Teradyne", MEMORY_IDMS + ANALOG_IDMS + OSAT, "equipment", "ate_market")
# Back-end / packaging equipment -> OSAT + leading fabs
S("Disco Corporation", OSAT + LEADING_FABS, "equipment", "semi_equipment")
S("Kulicke & Soffa", OSAT, "equipment", "semi_equipment")
# EUV mask inspection -> leading fabs + mask makers
S("Lasertec", LEADING_FABS + ["Photronics", "Toppan Photomask", "Hoya"],
  "equipment", "semi_equipment")

# --- Equipment subsystem suppliers -> equipment makers ---
S("MKS Instruments", ["Lam Research", "Applied Materials", "Tokyo Electron", "KLA", "ASML"],
  "equipment", "subsystem_market")
S("Ultra Clean Holdings", ["Lam Research", "Applied Materials", "Tokyo Electron"],
  "equipment", "subsystem_market")
S("Edwards Vacuum", ["Applied Materials", "Lam Research", "Tokyo Electron", "ASML"],
  "equipment", "subsystem_market")
S("Carl Zeiss SMT", ["ASML"], "equipment", "asml_zeiss", share=100, year=1997)

# --- Silicon wafer makers -> fabs/IDMs ---
for w in WAFER_MAKERS:
    S(w, FABS_AND_IDMS, "material", "wafer_market")

# --- Photoresist / process chemicals / CMP -> fabs/IDMs ---
for chem in ["Tokyo Ohka Kogyo", "JSR Corporation", "Shin-Etsu Chemical",
             "Fujifilm", "Merck KGaA", "DuPont", "Sumitomo Chemical",
             "Resonac", "Dongjin Semichem", "Entegris"]:
    S(chem, FABS_AND_IDMS, "material", "resist_market")

# --- Industrial / specialty gases -> fabs/IDMs ---
for g in GAS_MAJORS:
    S(g, FABS_AND_IDMS, "material", "gas_market")

# --- Photomask supply chain ---
S("Hoya", ["Photronics", "Toppan Photomask"] + LEADING_FABS, "material", "photomask_market")
S("Photronics", ALL_FOUNDRIES + ANALOG_IDMS, "material", "photomask_market")
S("Toppan Photomask", ALL_FOUNDRIES + ANALOG_IDMS, "material", "photomask_market")

# --- Substrate supply chain (ABF -> substrate makers -> packagers/fabless) ---
S("Ajinomoto", SUBSTRATE_MAKERS, "material", "abf_market", share=100)
for sub in SUBSTRATE_MAKERS:
    S(sub, OSAT + ["Nvidia", "AMD", "Intel", "Apple", "Qualcomm", "Broadcom", "TSMC"],
      "material", "substrate_market")
# SOI wafers -> RF / analog
S("Soitec", ["STMicroelectronics", "GlobalFoundries", "Qualcomm", "NXP"],
  "material", "soi_market")

# --- EDA -> everyone who designs silicon ---
for eda in EDA_FIRMS:
    S(eda, DESIGNERS, "EDA", "eda_market")

# --- IP cores -> fabless + IDMs ---
S("ARM", ["Apple", "Qualcomm", "MediaTek", "Nvidia", "Broadcom", "AMD",
          "Samsung Foundry", "HiSilicon", "Marvell", "Amazon", "Microsoft",
          "Google", "Realtek", "Renesas", "NXP", "STMicroelectronics", "Infineon"],
  "IP", "arm_partners")
S("Synopsys", ["Nvidia", "AMD", "Intel", "Samsung Memory", "MediaTek", "Marvell"],
  "IP", "ip_market")
S("Cadence", ["Nvidia", "Broadcom", "MediaTek", "Tesla", "Microsoft"], "IP", "ip_market")
S("Imagination Technologies", ["MediaTek", "Apple", "Realtek"], "IP", "ip_market")
S("SiFive", ["Google", "Renesas", "NXP"], "IP", "ip_market")
S("Ceva", ["Qualcomm", "Realtek", "Novatek"], "IP", "ip_market")

# --- Foundries -> fabless (manufactured logic) ---
S("TSMC", ["Nvidia", "AMD", "Apple", "Qualcomm", "Broadcom", "MediaTek", "Marvell",
           "Google", "Amazon", "Microsoft", "Tesla", "Cerebras", "Ambarella",
           "HiSilicon", "Realtek", "Novatek", "Intel"], "logic", "tsmc_ar2024")
S("Samsung Foundry", ["Nvidia", "Qualcomm", "Google", "Tesla", "Ambarella"],
  "logic", "foundry_share")
S("GlobalFoundries", ["AMD", "Qualcomm", "NXP", "Broadcom"], "logic", "foundry_share")
S("UMC", ["MediaTek", "Qualcomm", "Realtek", "Novatek", "Texas Instruments"],
  "logic", "foundry_share")
S("SMIC", ["HiSilicon", "Novatek", "Realtek"], "logic", "foundry_share")
S("Powerchip (PSMC)", ["Novatek", "Realtek"], "logic", "foundry_share")
S("Vanguard (VIS)", ["Novatek", "Realtek"], "logic", "foundry_share")
S("Tower Semiconductor", ["Broadcom", "Analog Devices"], "analog", "foundry_share")
S("Hua Hong Semiconductor", ["HiSilicon"], "logic", "foundry_share")

# --- Memory IDMs -> customers (incl. HBM for AI GPUs) ---
S("SK Hynix", ["Nvidia"], "memory", "hbm_nvidia", share=50, year=2023)
S("Samsung Memory", ["Nvidia"], "memory", "hbm_nvidia", share=30, year=2023)
S("Micron", ["Nvidia"], "memory", "hbm_nvidia", share=20, year=2024)
S("SK Hynix", ["Apple", "AMD", "Microsoft", "Amazon"], "memory", "wsts_market")
S("Samsung Memory", ["Apple", "Qualcomm", "Google", "Tesla"], "memory", "wsts_market")
S("Micron", ["Apple", "Intel", "AMD"], "memory", "wsts_market")
S("Kioxia", ["Apple", "Microsoft"], "memory", "wsts_market")
S("Western Digital", ["Apple", "Amazon"], "memory", "wsts_market")
S("Nanya Technology", ["Realtek", "Novatek"], "memory", "wsts_market")

# --- Analog/power IDMs -> downstream device makers ---
for idm in ANALOG_IDMS:
    S(idm, ["Apple", "Tesla"], "analog", "wsts_market")

# --- OSAT (assembly & test) -> fabless / foundries ---
S("ASE Group", ["Nvidia", "AMD", "Qualcomm", "Broadcom", "MediaTek", "Apple",
                "Marvell", "TSMC"], "package", "osat_market")
S("Amkor", ["Apple", "Qualcomm", "Nvidia", "Intel", "NXP", "Infineon"], "package", "osat_market")
S("JCET", ["HiSilicon", "Qualcomm", "MediaTek", "SMIC"], "package", "osat_market")
S("Powertech Technology", ["Micron", "Nanya Technology", "Kioxia"], "package", "osat_market")
S("Tongfu Microelectronics", ["AMD", "HiSilicon"], "package", "osat_market")
S("King Yuan Electronics", ["MediaTek", "Novatek", "Nvidia"], "package", "osat_market")
S("ChipMOS", ["Novatek", "Realtek"], "package", "osat_market")
S("UTAC", ["STMicroelectronics", "NXP"], "package", "osat_market")

# --- EMS integrators -> consume finished chips ---
S("Apple", ["Foxconn"], "logic", "wsts_market")
S("Qualcomm", ["Foxconn"], "logic", "wsts_market")
S("Nvidia", ["Foxconn"], "logic", "wsts_market")

# --------------------------------------------------------------------------- #
# MANUFACTURES (Company -> Product)
# tuple: (company, product, process_node_nm, capacity_share_pct, source_id)
# --------------------------------------------------------------------------- #
MANUFACTURES: list[tuple] = []


def M(company, products, source_id, node="", share=""):
    for p in products:
        MANUFACTURES.append((company, p, node, share, source_id))


# Foundries / logic
MANUFACTURES += [
    ("TSMC", "2nm logic wafer", 2, 90, "tsmc_ar2024"),
    ("TSMC", "3nm logic wafer", 3, 90, "tsmc_ar2024"),
    ("TSMC", "5nm logic wafer", 5, 80, "tsmc_ar2024"),
    ("TSMC", "7nm logic wafer", 7, 65, "tsmc_ar2024"),
    ("TSMC", "16nm logic wafer", 16, 50, "tsmc_ar2024"),
    ("TSMC", "28nm logic wafer", 28, 30, "tsmc_ar2024"),
    ("TSMC", "Advanced packaging (2.5D/3D)", "", 60, "tsmc_ar2024"),
    ("Samsung Foundry", "3nm logic wafer", 3, 10, "foundry_share"),
    ("Samsung Foundry", "5nm logic wafer", 5, 15, "foundry_share"),
    ("Samsung Foundry", "7nm logic wafer", 7, 10, "foundry_share"),
    ("Samsung Foundry", "28nm logic wafer", 28, 10, "foundry_share"),
    ("Intel", "7nm logic wafer", 7, 12, "intel_foundry"),
    ("Intel", "Advanced packaging (2.5D/3D)", "", 15, "intel_foundry"),
    ("GlobalFoundries", "16nm logic wafer", 16, 8, "foundry_share"),
    ("GlobalFoundries", "28nm logic wafer", 28, 18, "foundry_share"),
    ("GlobalFoundries", "65nm logic wafer", 65, 12, "foundry_share"),
    ("UMC", "28nm logic wafer", 28, 16, "foundry_share"),
    ("UMC", "65nm logic wafer", 65, 18, "foundry_share"),
    ("UMC", "90nm logic wafer", 90, 15, "foundry_share"),
    ("SMIC", "16nm logic wafer", 16, 6, "foundry_share"),
    ("SMIC", "28nm logic wafer", 28, 14, "foundry_share"),
    ("Hua Hong Semiconductor", "90nm logic wafer", 90, 8, "foundry_share"),
    ("Powerchip (PSMC)", "65nm logic wafer", 65, 6, "foundry_share"),
    ("Vanguard (VIS)", "90nm logic wafer", 90, 6, "foundry_share"),
    ("Nexchip", "28nm logic wafer", 28, 5, "foundry_share"),
    ("Tower Semiconductor", "90nm logic wafer", 90, 5, "foundry_share"),
]

# Lithography & front-end equipment
M("ASML", ["EUV lithography system"], "asml_ar2024", share=100)
M("ASML", ["DUV lithography system"], "asml_ar2024", share=80)
M("Nikon", ["DUV lithography system"], "semi_equipment", share=12)
M("Canon", ["DUV lithography system", "Nanoimprint lithography system"], "semi_equipment", share=8)
M("Applied Materials", ["CVD deposition system", "PVD deposition system",
                        "Ion implanter", "CMP system", "Etch system"], "semi_equipment")
M("Lam Research", ["Etch system", "ALD deposition system", "Wafer cleaning system"],
  "semi_equipment", share=45)
M("Tokyo Electron", ["Etch system", "CVD deposition system", "Wafer cleaning system"],
  "semi_equipment", share=25)
M("KLA", ["Metrology & inspection system"], "semi_equipment", share=55)
M("Onto Innovation", ["Metrology & inspection system"], "semi_equipment")
M("ASM International", ["ALD deposition system"], "semi_equipment", share=55)
M("Screen Holdings", ["Wafer cleaning system"], "semi_equipment", share=45)
M("Hitachi High-Tech", ["Etch system", "Metrology & inspection system"], "semi_equipment")
M("Lasertec", ["EUV mask inspection system"], "semi_equipment", share=100)
M("Advantest", ["Automated test equipment"], "ate_market", share=55)
M("Teradyne", ["Automated test equipment"], "ate_market", share=40)
M("Disco Corporation", ["Dicing saw"], "semi_equipment", share=70)
M("Kulicke & Soffa", ["Wire bonder"], "semi_equipment", share=60)
M("Carl Zeiss SMT", ["EUV optics module"], "asml_zeiss", share=100)

# Wafers & SOI & SiC substrate
M("Shin-Etsu Chemical", ["300mm silicon wafer", "200mm silicon wafer"], "wafer_market", share=30)
M("SUMCO", ["300mm silicon wafer", "200mm silicon wafer"], "wafer_market", share=25)
M("GlobalWafers", ["300mm silicon wafer", "200mm silicon wafer"], "wafer_market", share=15)
M("Siltronic", ["300mm silicon wafer"], "wafer_market", share=12)
M("SK Siltron", ["300mm silicon wafer", "SiC substrate"], "wafer_market", share=10)
M("Soitec", ["SOI wafer"], "soi_market", share=70)
M("Wolfspeed", ["SiC substrate", "SiC power device"], "wsts_market", share=50)

# Photoresist / chemicals / CMP
M("Tokyo Ohka Kogyo", ["ArF photoresist", "EUV photoresist"], "resist_market", share=25)
M("JSR Corporation", ["ArF photoresist", "EUV photoresist"], "resist_market", share=22)
M("Shin-Etsu Chemical", ["ArF photoresist", "EUV photoresist"], "resist_market")
M("Fujifilm", ["ArF photoresist", "Wet process chemicals"], "resist_market")
M("Merck KGaA", ["EUV photoresist", "Wet process chemicals"], "resist_market")
M("DuPont", ["CMP slurry", "ArF photoresist"], "resist_market")
M("Sumitomo Chemical", ["ArF photoresist", "Wet process chemicals"], "resist_market")
M("Resonac", ["CMP slurry", "Wet process chemicals"], "resist_market")
M("Dongjin Semichem", ["ArF photoresist"], "resist_market")
M("Entegris", ["CMP slurry", "Wet process chemicals"], "resist_market", share=30)

# Gases
for g in GAS_MAJORS:
    M(g, ["Specialty gases", "Bulk gases"], "gas_market")

# Photomasks
M("Photronics", ["Photomask"], "photomask_market", share=40)
M("Toppan Photomask", ["Photomask"], "photomask_market")
M("Hoya", ["EUV mask blank", "Photomask"], "photomask_market", share=70)

# Substrates
M("Ajinomoto", ["ABF build-up film"], "abf_market", share=100)
for sub in SUBSTRATE_MAKERS:
    M(sub, ["IC substrate", "Flip-chip package"], "substrate_market")

# Memory
M("Samsung Memory", ["DRAM", "DDR5 DRAM", "NAND flash", "3D NAND", "HBM"], "wsts_market", share=40)
M("SK Hynix", ["DRAM", "DDR5 DRAM", "NAND flash", "HBM"], "hbm_nvidia", share=35)
M("Micron", ["DRAM", "NAND flash", "HBM"], "wsts_market", share=25)
M("Kioxia", ["NAND flash", "3D NAND"], "wsts_market", share=20)
M("Western Digital", ["NAND flash", "3D NAND"], "wsts_market", share=15)
M("Nanya Technology", ["DRAM"], "wsts_market", share=3)

# Analog / power / sensors
M("Infineon", ["Power semiconductor", "SiC power device", "Microcontroller (MCU)"], "wsts_market", share=20)
M("STMicroelectronics", ["Microcontroller (MCU)", "SiC power device", "Power semiconductor"], "wsts_market")
M("NXP", ["Microcontroller (MCU)", "RF front-end module"], "wsts_market")
M("Texas Instruments", ["Analog IC", "Microcontroller (MCU)"], "wsts_market", share=18)
M("Analog Devices", ["Analog IC"], "wsts_market", share=12)
M("Microchip", ["Microcontroller (MCU)", "Analog IC"], "wsts_market")
M("onsemi", ["Power semiconductor", "SiC power device", "CMOS image sensor"], "wsts_market")
M("Renesas", ["Microcontroller (MCU)", "Analog IC"], "wsts_market")
M("Rohm", ["Power semiconductor", "SiC power device"], "wsts_market")
M("Qualcomm", ["RF front-end module"], "wsts_market")

# EDA / IP "products"
M("Synopsys", ["EDA software", "CPU IP core", "DSP IP core"], "eda_market", share=32)
M("Cadence", ["EDA software", "DSP IP core"], "eda_market", share=30)
M("Siemens EDA", ["EDA software"], "eda_market", share=28)
M("ARM", ["CPU IP core", "GPU IP core"], "ip_market", share=45)
M("Imagination Technologies", ["GPU IP core"], "ip_market")
M("SiFive", ["RISC-V IP core"], "ip_market")
M("Ceva", ["DSP IP core"], "ip_market")

# OSAT packaging
M("ASE Group", ["Advanced packaging (2.5D/3D)", "Flip-chip package"], "osat_market", share=30)
M("Amkor", ["Advanced packaging (2.5D/3D)", "Flip-chip package"], "osat_market", share=15)
for o in ["JCET", "Powertech Technology", "Tongfu Microelectronics", "UTAC"]:
    M(o, ["Flip-chip package"], "osat_market")

# --------------------------------------------------------------------------- #
# COMPETES_WITH (Company -> Company)  — stored once per pair, market_segment
# --------------------------------------------------------------------------- #
COMPETES_WITH = [
    ("TSMC", "Samsung Foundry", "leading-edge foundry"),
    ("TSMC", "Intel", "leading-edge foundry"),
    ("TSMC", "GlobalFoundries", "foundry"),
    ("TSMC", "UMC", "foundry"),
    ("TSMC", "SMIC", "foundry"),
    ("UMC", "SMIC", "mature-node foundry"),
    ("GlobalFoundries", "UMC", "mature-node foundry"),
    ("Powerchip (PSMC)", "Vanguard (VIS)", "specialty foundry"),
    ("Hua Hong Semiconductor", "Nexchip", "mature-node foundry (China)"),
    ("Nvidia", "AMD", "GPU / datacenter accelerators"),
    ("AMD", "Intel", "x86 CPU"),
    ("Qualcomm", "MediaTek", "mobile SoC"),
    ("Broadcom", "Marvell", "networking / custom silicon"),
    ("Realtek", "Novatek", "display driver / connectivity"),
    ("Micron", "SK Hynix", "DRAM / NAND"),
    ("SK Hynix", "Samsung Memory", "DRAM / NAND"),
    ("Micron", "Samsung Memory", "DRAM / NAND"),
    ("Kioxia", "Western Digital", "NAND flash"),
    ("Nanya Technology", "Micron", "DRAM"),
    ("Applied Materials", "Lam Research", "wafer-fab equipment"),
    ("Lam Research", "Tokyo Electron", "etch / deposition equipment"),
    ("Applied Materials", "Tokyo Electron", "wafer-fab equipment"),
    ("ASML", "Nikon", "lithography"),
    ("Nikon", "Canon", "lithography"),
    ("Advantest", "Teradyne", "automated test equipment"),
    ("KLA", "Onto Innovation", "metrology / inspection"),
    ("Shin-Etsu Chemical", "SUMCO", "silicon wafers"),
    ("GlobalWafers", "Siltronic", "silicon wafers"),
    ("Tokyo Ohka Kogyo", "JSR Corporation", "photoresist"),
    ("Air Liquide", "Linde", "industrial gases"),
    ("Linde", "Air Products", "industrial gases"),
    ("Photronics", "Toppan Photomask", "photomasks"),
    ("Unimicron", "Ibiden", "IC substrates"),
    ("Ibiden", "Shinko Electric Industries", "IC substrates"),
    ("Synopsys", "Cadence", "EDA tools"),
    ("Cadence", "Siemens EDA", "EDA tools"),
    ("ARM", "SiFive", "CPU IP (Arm vs. RISC-V)"),
    ("Infineon", "STMicroelectronics", "power / automotive"),
    ("Infineon", "onsemi", "power / SiC"),
    ("Texas Instruments", "Analog Devices", "analog IC"),
    ("Wolfspeed", "Rohm", "silicon carbide"),
    ("ASE Group", "Amkor", "OSAT / packaging"),
    ("Amkor", "JCET", "OSAT / packaging"),
    ("ASE Group", "JCET", "OSAT / packaging"),
    ("Hoya", "Toppan Photomask", "EUV mask blanks / masks"),
]

# --------------------------------------------------------------------------- #
# DEPENDS_ON (Product -> Product)  — dependency_type
# --------------------------------------------------------------------------- #
DEPENDS_ON = [
    ("2nm logic wafer", "EUV lithography system", "process"),
    ("3nm logic wafer", "EUV lithography system", "process"),
    ("5nm logic wafer", "EUV lithography system", "process"),
    ("7nm logic wafer", "EUV lithography system", "process"),
    ("16nm logic wafer", "DUV lithography system", "process"),
    ("28nm logic wafer", "DUV lithography system", "process"),
    ("EUV lithography system", "EUV optics module", "component"),
    ("EUV lithography system", "EUV mask blank", "consumable"),
    ("EUV lithography system", "EUV photoresist", "consumable"),
    ("EUV lithography system", "Specialty gases", "consumable"),
    ("Photomask", "EUV mask blank", "substrate"),
    ("2nm logic wafer", "300mm silicon wafer", "substrate"),
    ("3nm logic wafer", "300mm silicon wafer", "substrate"),
    ("5nm logic wafer", "300mm silicon wafer", "substrate"),
    ("7nm logic wafer", "300mm silicon wafer", "substrate"),
    ("3nm logic wafer", "EUV photoresist", "material"),
    ("5nm logic wafer", "EUV photoresist", "material"),
    ("28nm logic wafer", "ArF photoresist", "material"),
    ("3nm logic wafer", "Photomask", "tooling"),
    ("3nm logic wafer", "Specialty gases", "material"),
    ("3nm logic wafer", "CMP slurry", "material"),
    ("3nm logic wafer", "EDA software", "design"),
    ("3nm logic wafer", "CPU IP core", "design"),
    ("HBM", "DRAM", "composition"),
    ("HBM", "Advanced packaging (2.5D/3D)", "integration"),
    ("Advanced packaging (2.5D/3D)", "IC substrate", "substrate"),
    ("IC substrate", "ABF build-up film", "material"),
    ("Flip-chip package", "IC substrate", "substrate"),
    ("SiC power device", "SiC substrate", "substrate"),
    ("CPU IP core", "EDA software", "design"),
    ("DDR5 DRAM", "DRAM", "generation"),
    ("3D NAND", "NAND flash", "generation"),
]


def _resolve(source_id: str) -> tuple[str, str]:
    if source_id in SOURCES:
        return SOURCES[source_id]["url"], ACCESSED
    raise KeyError(f"Unknown source_id: {source_id!r}")


def _integrity_check(company_names: set[str], product_names: set[str]) -> None:
    """Fail fast if any relationship references an unknown node."""
    problems = []
    for s, d, *_ in SUPPLIES:
        if s not in company_names:
            problems.append(f"SUPPLIES source not a company: {s!r}")
        if d not in company_names:
            problems.append(f"SUPPLIES target not a company: {d!r}")
    for c, p, *_ in MANUFACTURES:
        if c not in company_names:
            problems.append(f"MANUFACTURES company unknown: {c!r}")
        if p not in product_names:
            problems.append(f"MANUFACTURES product unknown: {p!r}")
    for a, b, _ in COMPETES_WITH:
        if a not in company_names or b not in company_names:
            problems.append(f"COMPETES_WITH unknown endpoint: {a!r} / {b!r}")
    for a, b, _ in DEPENDS_ON:
        if a not in product_names or b not in product_names:
            problems.append(f"DEPENDS_ON unknown product: {a!r} / {b!r}")
    if problems:
        for p in sorted(set(problems)):
            log.error("  %s", p)
        raise SystemExit(f"Integrity check failed with {len(set(problems))} problem(s).")


def main() -> None:
    company_names = {c["name"] for c in COMPANIES}
    product_names = {p["name"] for p in PRODUCTS}
    if len(company_names) != len(COMPANIES):
        raise SystemExit("Duplicate company name in COMPANIES.")
    _integrity_check(company_names, product_names)

    used_source_ids: set[str] = set()

    # ----- Company nodes + per-company Wikipedia sources -----
    company_rows, company_source_rows, located_in_rows = [], [], []
    for c in COMPANIES:
        sid = f"wiki_{c['wiki'].lower()}"
        wiki_url = f"https://en.wikipedia.org/wiki/{c['wiki']}"
        company_rows.append(
            {k: c[k] for k in ["name", "country", "region", "market_cap_usd",
                               "founded", "employees", "type"]}
            | {"source_id": sid, "source_url": wiki_url, "source_date": ACCESSED})
        company_source_rows.append(dict(
            source_id=sid, url=wiki_url, date_accessed=ACCESSED,
            covers=f"{c['name']} — company profile (country, founded, employees)",
            notes="Market cap cross-checked with companiesmarketcap.com"))
        located_in_rows.append(dict(company=c["name"], country=c["country"]))

    write_csv(DATA_RAW / "companies.csv",
              ["name", "country", "region", "market_cap_usd", "founded",
               "employees", "type", "source_id", "source_url", "source_date"],
              company_rows)
    write_csv(DATA_RAW / "located_in.csv", ["company", "country"], located_in_rows)
    write_csv(DATA_RAW / "countries.csv", ["name", "iso2", "region"], COUNTRIES)
    write_csv(DATA_RAW / "products.csv",
              ["name", "category", "node_size_nm", "year_introduced"], PRODUCTS)

    # ----- SUPPLIES -----
    # A supplier can be reached by more than one S(...) call with the same
    # product_category but a different source (e.g. Shin-Etsu appears in both
    # WAFER_MAKERS and the process-chemicals group, both as "material"). Those
    # collapse to a single edge downstream (Neo4j keys SUPPLIES on
    # source+target+product_category), so de-duplicate here on that same key,
    # keeping the first occurrence, to keep supplies.csv 1:1 with the graph.
    supplies_rows = []
    seen_supplies: set[tuple[str, str, str]] = set()
    dropped_supplies = 0
    for src, dst, cat, share, year, sid in SUPPLIES:
        key = (src, dst, cat)
        if key in seen_supplies:
            dropped_supplies += 1
            continue
        seen_supplies.add(key)
        url, date = _resolve(sid)
        used_source_ids.add(sid)
        supplies_rows.append(dict(
            source=src, target=dst, product_category=cat, value_usd_annual="",
            volume_share_pct=share, year_established=year,
            source_url=url, source_date=date))
    if dropped_supplies:
        log.info("  SUPPLIES dedup : dropped %d duplicate (source,target,"
                 "product_category) row(s)", dropped_supplies)
    write_csv(DATA_RAW / "supplies.csv",
              ["source", "target", "product_category", "value_usd_annual",
               "volume_share_pct", "year_established", "source_url", "source_date"],
              supplies_rows)

    # ----- MANUFACTURES -----
    manufactures_rows = []
    for comp, prod, node, share, sid in MANUFACTURES:
        url, date = _resolve(sid)
        used_source_ids.add(sid)
        manufactures_rows.append(dict(
            company=comp, product=prod, process_node_nm=node,
            capacity_share_pct=share, source_url=url, source_date=date))
    write_csv(DATA_RAW / "manufactures.csv",
              ["company", "product", "process_node_nm", "capacity_share_pct",
               "source_url", "source_date"],
              manufactures_rows)

    # ----- COMPETES_WITH / DEPENDS_ON -----
    write_csv(DATA_RAW / "competes_with.csv",
              ["source", "target", "market_segment"],
              [dict(source=a, target=b, market_segment=seg) for a, b, seg in COMPETES_WITH])
    write_csv(DATA_RAW / "depends_on.csv",
              ["source", "target", "dependency_type"],
              [dict(source=a, target=b, dependency_type=t) for a, b, t in DEPENDS_ON])

    # ----- Log all sources -----
    industry_source_rows = [
        dict(source_id=sid, url=SOURCES[sid]["url"], date_accessed=ACCESSED,
             covers=SOURCES[sid]["covers"], notes="")
        for sid in sorted(used_source_ids)]
    industry_source_rows.append(
        dict(source_id="marketcap", url=SOURCES["marketcap"]["url"],
             date_accessed=ACCESSED, covers=SOURCES["marketcap"]["covers"],
             notes="Reference for market_cap_usd column"))
    added = log_sources(company_source_rows + industry_source_rows)

    # ----- Summary -----
    log.info("Backbone collection complete (expanded).")
    log.info("  companies      : %d", len(company_rows))
    log.info("  countries      : %d", len(COUNTRIES))
    log.info("  products       : %d", len(PRODUCTS))
    log.info("  SUPPLIES       : %d", len(supplies_rows))
    log.info("  MANUFACTURES   : %d", len(manufactures_rows))
    log.info("  COMPETES_WITH  : %d", len(COMPETES_WITH))
    log.info("  LOCATED_IN     : %d", len(located_in_rows))
    log.info("  DEPENDS_ON     : %d", len(DEPENDS_ON))
    log.info("  sources logged : %d new", added)
    log.info("Output written to %s", DATA_RAW)


if __name__ == "__main__":
    main()
