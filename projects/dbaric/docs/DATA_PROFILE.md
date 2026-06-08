# Data Profile — contracts.csv

**Source:** EOJN (Elektronički oglasnik javne nabave) — Croatian public procurement portal  
**File:** `data/contracts.csv`  
**Fetched:** 2026-05-10 (rolling batch — all rows have a `last_fetched_at` on 2026-05-10 but across 3,981 distinct timestamps throughout the day, not a single snapshot moment)  
**Rows:** 397,973 · **Columns:** 45  
**Updated:** 2026-05-23 — added graph estimates, hypothesis testability assessment, and geographic data gap finding

**Working file:** `data/contracts_clean.csv` — produced by `helpers/prepare_data.py`. All analysis scripts must load this file, not the raw CSV. The clean file has 383,374 rows and 52 columns; hard cleans (deduplication, reversed contracts, negative values, sentinel dates, CA OIB zero-padding, CPV parsing) are already applied. Filtering for framework call-offs, analysis window, currency, and procedure type is done per-script via flag columns (`is_framework_calloff`, `in_analysis_window`, `is_eur`, `is_discretionary`, `is_competitive`).

> **Critical finding:** The dataset contains **no geographic fields**. Hypotheses H2 and H2a (geographic proximity) are untestable without an external data source. See §9 (geographic enrichment) and §10 (hypothesis testability) for detail.

---

## 1. Temporal Coverage

`ContractDate` spans 2014-03-06 to 2026-05-08, but the distribution is heavily front-loaded on the portal's data-collection window:

| Year   | Contracts        |
| ------ | ---------------- |
| ≤ 2023 | 223 (0.06 %)     |
| 2024   | 159,529 (40.1 %) |
| 2025   | 203,132 (51.0 %) |
| 2026   | 35,089 (8.8 %)   |

**Pre-2024 records (223)** are retroactive entries — late submissions or corrections published after the portal went live. They span as far back as 2014 and are not a usable longitudinal series. For temporal or cohort analysis, restrict to `ContractDate >= 2024-01-01`.

`InitialPublishTimestamp` and `LastPublishedAt` both range 2024-01-02 to 2026-05-10, confirming the portal's live window.

---

## 2. Missing Values

| Column                 | Missing | %                              |
| ---------------------- | ------- | ------------------------------ |
| `MainTenderId`         | 397,973 | **100 %** — always empty, drop |
| `DurationFromText`     | 397,973 | **100 %** — always empty, drop |
| `DurationToText`       | 397,973 | **100 %** — always empty, drop |
| `ObjectId`             | 397,973 | **100 %** — always empty, drop |
| `ContractRationale`    | 374,595 | 94.1 %                         |
| `FrameworkAgreementNo` | 371,732 | 93.4 %                         |
| `FrameworkAgreementId` | 360,092 | 90.5 %                         |
| `Noticenumber`         | 317,928 | 79.9 %                         |
| `TenderId`             | 312,684 | 78.6 %                         |
| `DurationDay`          | 297,224 | 74.7 %                         |
| `DurationMonth`        | 263,512 | 66.2 %                         |
| `TerminationDate`      | 238,368 | 59.9 %                         |
| `DurationTo`           | 237,392 | 59.7 %                         |
| `DurationFrom`         | 237,391 | 59.7 %                         |
| `PayedAmount`          | 234,539 | 58.9 %                         |
| `ExemptionLegalBaseId` | 75,516  | 19.0 %                         |
| `DurationType`         | 4,584   | 1.2 %                          |
| All others             | 0–1     | < 0.01 %                       |

The four 100 %-empty columns carry no information. `TenderId` and `Noticenumber` are absent for ~80 % of contracts (call-offs and direct awards where no tender notice exists). Duration fields are missing for ~60 % — duration data is unreliable as a standalone feature. `PayedAmount` (populated only after payment) and `TerminationDate` (populated only after formal termination) are both absent for ~59 % of contracts. The missingness is non-random: ongoing contracts have no termination date, and contracts where payment was never recorded do not populate `PayedAmount`. The available ~41 % reflects completed, paid contracts and is not a representative sample of the full population. Execution-quality analysis is underpowered; see §11.

---

## 3. Core Identifier Quality

### Contracting Authorities (CA)

- **Unique CA names:** 4,211 · **Unique CA OIBs:** 4,223
- **Leading-zero stripping affects 411 CA OIBs (38,458 rows, 9.7 %).** The CSV stores OIBs as integers, silently dropping any leading zero. Affected OIBs are 10 digits (385 unique), 9 digits (25 unique), or 8 digits (1 unique) — all numeric, all mapping to legitimate Croatian public bodies. **Before any external join (e.g. OIB→address lookup), zero-pad `CAIdentificationNumber` to 11 digits.** Within-dataset analysis using the raw value as a key is unaffected since the truncated form is consistent across all rows for a given authority.
- **OIB → multiple names (30 cases):** Name variation over time (abbreviations, reorganisations) and shared OIBs for sub-units (e.g. one OIB covers three regional MUP police units; the Ministry of Finance OIB covers three sub-agencies). **Use `CAIdentificationNumber` (OIB) as the canonical CA key**, not `CAName`.

### Contractors

- **Unique contractor names:** 45,573 · **Unique contractor OIBs:** 44,188
- **4,502 non-numeric OIBs (1.1 %):** Two distinct patterns:
  - Foreign VAT numbers: `SI…`, `AT…`, `NL…`, `DE…`, etc. — legitimate EU contractors using their home-country VAT ID. **Dominant pattern: 4,375 rows (97.2 % of non-numeric).**
  - `KRIVO_SE_REGISTRIRALI_<11 digits>` — portal's flag for foreign contractors who incorrectly registered with a Croatian OIB. The embedded 11-digit string is not a valid Croatian tax ID. **Minority: 127 rows (2.8 % of non-numeric).**
- **5,998 wrong-length OIBs (1.5 %, includes the above)** — non-11-digit numeric strings plus all non-numeric values.

For graph analysis, foreign contractors cannot be deduplicated via OIB. Options: exclude them (small share), use a composite key (name + country prefix), or treat each unique string as its own node with a `foreign` flag.

---

## 4. Value Distribution (TotalValue, EUR)

| Statistic       | TotalValue  | TotalValueVat |
| --------------- | ----------- | ------------- |
| Count           | 397,973     | 397,973       |
| Minimum         | −456.77     | −570.63       |
| Q1              | 1,150       | 1,350         |
| Median          | 4,955       | 5,974         |
| Mean            | 54,412      | 70,627        |
| Q3              | 14,025      | 16,920        |
| Maximum         | 397,981,460 | 1,341,941,798 |
| **Total (sum)** | **~21.7 B** | **~28.1 B**   |
| Top-10 % share  | **88.5 %**  | 89.2 %        |

The distribution is severely right-skewed. The top decile of contracts accounts for 88.5 % of total value — extreme concentration that will exceed any degree-sequence null model and must be established as baseline before interpreting graph-level concentration metrics.

- **Negative values:** 2 records (IDs 239768, 639700) — credit notes or data entry errors. Trivial count; treat as invalid and exclude.
- **Zero values:** 323 records — contracts with no declared monetary value. Retain as edges only if value-weighted metrics are not the target; otherwise exclude.

`InitialValue` vs `TotalValue`: mean and distribution are nearly identical, confirming amendments are rare but the max `TotalValueVat` (1.34 B) is markedly higher than `InitialValueVAT` max, suggesting post-award upward amendments on a small number of large contracts.

---

## 5. Duplicate Contract IDs

**2,114 `Id` values appear more than once** (2 occurrences: 2,007 IDs; 3 occurrences: 102 IDs; 4 occurrences: 5 IDs). Deduplication removes 2,226 extra rows, not 2,114. This is likely re-publication after amendment (the `LastPublishedAt` field changes). Before graph construction, deduplicate by keeping the latest `LastPublishedAt` per `Id`, or verify whether duplicates represent distinct contract versions.

---

## 6. Date Anomalies

| Field             | Outlier condition | Count      |
| ----------------- | ----------------- | ---------- |
| `DurationTo`      | year > 2035       | 12         |
| `TerminationDate` | year > 2035       | 10         |
| `DurationTo`      | max value         | 2205-12-17 |
| `TerminationDate` | max value         | 2205-12-31 |

The outlier cluster is around 2202–2205 (not the extreme sentinels like 9999-12-31 that some portals use). These appear to be placeholder dates for open-ended or indefinite-duration contracts — not real dates. Treat any year > 2099 as "indefinite" and recode to NULL before any duration-based analysis.

---

## 7. Categorical Fields

### Procedure Type (`ProcedureTypeId`)

| ID         | Count   | Share  |
| ---------- | ------- | ------ |
| 11         | 312,745 | 78.6 % |
| 1          | 72,513  | 18.2 % |
| 53         | 4,503   | 1.1 %  |
| 6          | 3,115   | 0.8 %  |
| 52         | 2,016   | 0.5 %  |
| others (9) | 3,081   | 0.8 %  |

ID 11 dominates — almost certainly "Bagatelna nabava" (below-threshold direct award, no competitive procedure required). ID 1 is almost certainly open procedure. The CSV contains only integer codes; **no label mapping table exists within this dataset and no external source is available.**

**Critical implication:** If ID 11 is below-threshold direct award, then ~78.6 % of all contracts — and the corresponding fraction of all edges in the bipartite graph — represent discretionary vendor selection with no legal requirement to compete. The graph is overwhelmingly a record of uncontested choices. This is the most analytically relevant regime for preferential selection research. It also means that splitting the graph into "competitive" vs. "discretionary" subgraphs (required by H2a) depends on resolving the code–label mapping. **Without that mapping, competitive/discretionary segmentation is unavailable.**

For analysis, a working assumption of ID 11 = discretionary, ID 1 = competitive can be adopted and flagged as unverified. All findings conditional on this split carry an additional caveat.

### Contract Status (`ContractStatusId`)

| ID  | Count   | Interpretation     |
| --- | ------- | ------------------ |
| 2   | 231,653 | Active / published |
| 4   | 158,962 | Completed          |
| 3   | 6,715   | Amended            |
| 5   | 641     | Terminated         |
| 6   | 2       | —                  |

### Agreement Type (`AgreementTypeId`) / Contract Type (`ContractTypeId`)

Three values each. Agreement type: 1 (51 %), 3 (38 %), 4 (11 %). Contract type: 2-services (48 %), 3-works (41 %), 1-supplies (11 %).

### IsUponFA — Framework Agreement call-offs

**37,881 contracts (9.5 %)** are call-offs against a pre-existing framework agreement. The vendor selection decision occurred at framework stage, not at the call-off stage. The framework procurement itself is **not in this dataset** — we see the call-off outcome but not the competitive process that determined the eligible vendor pool.

For preferential selection analysis, framework call-offs represent vendor relationships that were established through a process invisible to this analysis. Including them inflates contractor–CA edge weights without those edges reflecting per-contract selection discretion. Excluding them removes 37,881 rows (~10 %) but produces a cleaner signal of active selection behaviour.

### IsReversed

**12,372 contracts (3.1 %)** are reversed/cancelled. Their `TotalValue` distribution is similar to normal contracts (median 4,360 vs 4,980). They should be excluded from graph construction unless modelling contract cancellation as a separate phenomenon.

### Currency

99.94 % of contracts use currency ID 1 (EUR — Croatia joined the eurozone in 2023, prior HRK contracts are also coded as 1 in the source). 226 records use foreign currencies. For all-EUR analysis, restrict to `TotalValueCurrencyId = 1`.

---

## 8. CPV Codes

CPV codes are stored as free text: `<8-digit code> - <Croatian label>` (e.g. `45000000 - Građevinski radovi`). The 8-digit numeric prefix is the standard EU CPV code; the label is in Croatian. Parse by splitting on `-` to extract the code.

Top CPV divisions (first 2 digits of 8-digit code):

| Division | Domain                    | Contracts |
| -------- | ------------------------- | --------- |
| 45       | Construction works        | 45,012    |
| 33       | Medical / pharmaceutical  | 42,162    |
| 71       | Engineering & consultancy | 33,922    |
| 50       | Repair & maintenance      | 33,604    |
| 79       | Business services         | 22,384    |
| 15       | Food & beverages          | 19,934    |
| 39       | Furniture & equipment     | 18,308    |
| 30       | Office / IT equipment     | 15,610    |
| 72       | IT services               | 14,308    |
| 44       | Construction materials    | 12,432    |

---

## 9. Derived Graph Properties

Graph construction protocol (default form, graph form by metric, edge weight, foreign contractor handling) is in `docs/PLAN.md §Graph construction canon`. This section records the resulting graph estimates and geographic data gap.

**Geographic enrichment (external source required):** H2 and H2a require county-level assignment for CAs and contractors. No geographic field exists in the dataset — no county, region, municipality, postal code, or address for either entity class. OIB is a tax identifier with no geographic encoding. This cannot be derived from the CSV alone; it requires an external source (e.g., Croatian business registry or OIB→address lookup).

**Estimated bipartite graph after pre-processing:**

| Property                                                  | Estimate                                                         |
| --------------------------------------------------------- | ---------------------------------------------------------------- |
| CA nodes                                                  | ~4,223 (unique OIBs)                                             |
| Domestic contractor nodes                                 | ~43,700 (after dedup and exclusions)                             |
| Foreign contractor nodes                                  | ~4,502 (non-numeric OIB; isolated from OIB-keyed analysis)       |
| Total edges (contracts)                                   | ~383,000                                                         |
| Multi-edges (same CA–contractor pair, multiple contracts) | substantial — distribution unknown until computed                |
| Edge density (bipartite)                                  | very sparse; most CAs connect to a small fraction of contractors |
| Framework call-offs (if excluded per step 9a)             | ~345,000 edges                                                   |

The multi-edge structure is analytically significant: collapsing to a simple weighted graph (sum of contract values per CA–contractor pair) discards timing information needed for H3; retaining multi-edges preserves it. Analysis should default to the multi-graph and collapse only when the metric requires it.

---

## 10. Hypothesis Testability

Cross-reference of the hypotheses in `docs/HYPOTHESES.md` against what this dataset can actually support. Constraints are hard unless marked otherwise.

| Hypothesis                                                                                     | Status                            | Binding constraint                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------------------------------------------------------------------------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **H1** — Contractor strength concentration vs null                                             | **Testable**                      | None significant. Gini vs configuration model is computable from the clean bipartite graph.                                                                                                                                                                                                                                                                                                                                     |
| **H1a** — Single-vendor lock-in at authority level                                             | **Testable**                      | None significant. Requires excluding degree-1 CAs as per hypothesis spec.                                                                                                                                                                                                                                                                                                                                                       |
| **H1b** — Concentration higher in assumed-discretionary vs assumed-competitive (`exploratory`) | **Severely limited**              | `ProcedureTypeId` label mapping unavailable — ID 11 = discretionary and ID 1 = competitive are working assumptions, not verified facts (see §7). All results conditional on this classification.                                                                                                                                                                                                                                |
| **H1c** — Concentration lower in EU-funded than domestic-funded contracts                      | **Testable (conditional)**        | H1 must confirm first. `ContractEUFinanc` flag available. EU-funded subgraph may be thin in some CPV sectors — underpowered sectors must be reported separately rather than excluded.                                                                                                                                                                                                                                           |
| **H2** — County co-location assortativity                                                      | **Blocked**                       | No geographic fields in the dataset (see §9). Requires external OIB→county mapping for both entity classes before analysis can begin.                                                                                                                                                                                                                                                                                           |
| **H2a** — Locality bias stronger in assumed-discretionary awards                               | **Blocked**                       | Same as H2; additionally blocked by `ProcedureTypeId` label gap (see §7). Both blockers must be resolved before analysis can begin.                                                                                                                                                                                                                                                                                             |
| **H3** — Graph density spikes at fiscal year-end                                               | **Testable**                      | The 2024–2026 window covers at most two complete fiscal years. A Q4 spike can be detected within each year; a multi-year trend cannot be established. The EU-funded contrast (`ContractEUFinanc`) is available.                                                                                                                                                                                                                 |
| **H4** — CA–contractor pair reconnection rate vs degree-sequence null                          | **Testable — single transition**  | Only one year-over-year transition (2024 → 2025) is available; H4 produces a single point estimate, not a replicated pattern. Restrict to pairs where both nodes are active in both years. Exclude re-publications of the same contract spanning the year boundary (same `ContractNo`, `ContractDate` within 30 days).                                                                                                          |
| **H6** — CPV contract homophily vs degree-sequence null                                        | **Testable — label noise caveat** | Primary CPV division per contractor (modal 2-digit CPV prefix by contract count) is unstable for contractors with < 3 contracts in the observation window. Restrict to ≥ 3-contract contractors; this excludes the one-time-contractor long tail but preserves the large majority of contract value. Non-numeric OIBs (foreign contractors) excluded — no reliable primary CPV can be assigned without domestic market context. |
| **H1d** — Within-sector C1/C2 concentration vs degree-sequence null                            | **Testable**                      | Same constraints as H1. Sector minimum filter (≥ 5 distinct contractors per CPV 2-digit division) will exclude very thin sectors; report as structurally thin rather than silently drop.                                                                                                                                                                                                                                        |
| **H4a** — Post-award amendment inflation higher in established pairs                           | **Testable — low signal caveat**  | `InitialValue` present for nearly all contracts (< 0.01% missing per §2). Amendments are rare — mean `TotalValue` ≈ mean `InitialValue` (§4); signal is concentrated in a small fraction of contracts. Restrict to contracts where `InitialValue > 0`.                                                                                                                                                                          |
| **H8** — Contractor award rotation within CA–CPV cells                                         | **Testable**                      | `ContractDate` present for all contracts. Cell eligibility filter (≥ 5 contracts, ≥ 2 distinct contractors) will reduce eligible cells; distribution unknown until computed. Secondary procedure-type test carries ID 11/1 label assumption caveat identical to H1b.                                                                                                                                                            |
| **H9** — Contract splitting temporal clusters within CA–contractor pairs                       | **Testable — threshold caveat**   | Primary thresholds (T_services = €26,540, T_works = €66,360) are from ZJN 2016 and are not directly verifiable from the dataset itself. Empirical threshold detection (robustness check) requires a density discontinuity test as a declared preliminary step. `ContractTypeId` present for all contracts (1=supplies, 2=services, 3=works).                                                                                    |

**The geographic data absence (H2, H2a) is the single largest gap between the hypothesis tree and the dataset.** Those two hypotheses remain blocked until an external OIB→county mapping is joined to both entity classes. H6 tests a related sector-structure question (whether sector fit or relational access drives selection) using fields available in the dataset, but the mechanism is distinct from geographic proximity — H6 does not substitute for H2.

---

## 11. Column Reference

_Quick lookup only. Full discussion of each column is in the relevant section above._

| Column                           | Type     | Notes                                                      |
| -------------------------------- | -------- | ---------------------------------------------------------- |
| `Id`                             | int      | Contract record ID (primary key; 2,114 duplicates)         |
| `TenderId`                       | int      | Tender ID (78.6 % missing — absent for direct awards)      |
| `ProcedureTypeId`                | int      | Procurement procedure type (14 values; integer codes only) |
| `ContractCAId`                   | int      | CA internal ID                                             |
| `CAName`                         | string   | CA name (use OIB as key; 28 OIBs have multiple names)      |
| `CAIdentificationNumber`         | string   | CA OIB — 11-digit, 100 % valid                             |
| `ReferenceNumber`                | string   | Internal reference (free text)                             |
| `MainTenderId`                   | —        | **Always empty — drop**                                    |
| `TenderName`                     | string   | Subject / title of the procurement                         |
| `Cpv`                            | string   | `<8-digit code> - <label>` format                          |
| `AgreementTypeId`                | int      | 3 values                                                   |
| `ContractTypeId`                 | int      | 1=supplies, 2=services, 3=works                            |
| `ExemptionLegalBaseId`           | int      | 19 % missing                                               |
| `IsUponFA`                       | bool     | True = framework agreement call-off (9.5 %)                |
| `Noticenumber`                   | string   | Notice reference (79.9 % missing)                          |
| `ContractNo`                     | string   | Contract number (free text)                                |
| `ContractDate`                   | datetime | Date contract was signed                                   |
| `ContractorName`                 | string   | Vendor name (use OIB as key)                               |
| `ContractorIdentificationNumber` | string   | Vendor OIB or foreign VAT (1.1 % non-standard)             |
| `TotalValue`                     | float    | Contract value excl. VAT (EUR)                             |
| `TotalValueVat`                  | float    | Contract value incl. VAT (EUR)                             |
| `TotalValueCurrencyId`           | int      | Currency (99.94 % = 1 = EUR)                               |
| `ContractRationale`              | string   | 94.1 % missing                                             |
| `ContractEUFinanc`               | bool     | EU co-financed flag                                        |
| `ContractStatusId`               | int      | 5 values (active/completed/amended/terminated)             |
| `FrameworkAgreementId`           | int      | FA parent ID (90.5 % missing)                              |
| `FrameworkAgreementNo`           | string   | FA reference number (93.4 % missing)                       |
| `DurationType`                   | int      | 1/2/3 (1.2 % missing)                                      |
| `DurationMonth`                  | int      | Duration in months (66.2 % missing)                        |
| `DurationDay`                    | int      | Duration in days (74.7 % missing)                          |
| `DurationFrom`                   | datetime | Duration start (59.7 % missing)                            |
| `DurationTo`                     | datetime | Duration end (59.7 % missing; sentinel: 9999-12-31)        |
| `DurationFromText`               | —        | **Always empty — drop**                                    |
| `DurationToText`                 | —        | **Always empty — drop**                                    |
| `InitialPublishTimestamp`        | datetime | First publication on portal                                |
| `LastPublishedAt`                | datetime | Most recent publication                                    |
| `InitialValue`                   | float    | Value at initial publication                               |
| `InitialValueVAT`                | float    | Value at initial publication incl. VAT                     |
| `InitialCurrencyId`              | int      | Currency at initial publication                            |
| `IsReversed`                     | bool     | Reversed/cancelled (3.1 %)                                 |
| `PayedAmount`                    | float    | Amount paid (58.9 % missing)                               |
| `TerminationDate`                | datetime | Termination date (59.9 % missing; sentinel outliers)       |
| `HasTenderId`                    | bool     | Whether a tender ID is linked                              |
| `ObjectId`                       | —        | **Always empty — drop**                                    |
| `last_fetched_at`                | datetime | Snapshot date — uniform 2026-05-10                         |
