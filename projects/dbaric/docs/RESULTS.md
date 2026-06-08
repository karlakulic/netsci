# Analysis Run Results — 2026-06-07

Run against `data/contracts_clean.csv` (383,374 rows, 2026-05-23 snapshot).  
Foreign contractor exclusion rate: **1.1%** (4,270 rows) applied across all scripts.

**Full raw output per script:** `results/<hypothesis_id>.txt` — one file per script, complete stdout.  
This file (`docs/RESULTS.md`) is the structured summary; `results/` has the machine-level detail.

---

## Summary table

| Script | Hypothesis | Verdict | Key metric |
|--------|-----------|---------|------------|
| h1_concentration.py | H1 — contractor strength concentration | **REJECT NULL (effect above threshold on HHI; Gini sig but below threshold on aggregate)** | Agg Gini excess +0.039 p=0.002; HHI excess +0.076 p=0.002 |
| h1a_authority_lockin.py | H1a — authority lock-in (single-vendor > 80%) | **REJECT NULL but below effect threshold** | Obs frac 6.6% vs null median 4.5% (+2.1 pp); temporal trend FAIL |
| h1b_discretionary_concentration.py | H1b — discretionary vs competitive Gini excess | **FAIL TO REJECT NULL (aggregate); mixed by sector** | Agg Δ(Gini excess) = +0.010 vs null median 0.017, p=1.000; sector-level mixed |
| h1c_eu_vs_domestic.py | H1c — EU vs domestic concentration | **NOT CONFIRMED (2/41 sectors; 4.9% confirm rate)** | Only CPV 45 and CPV 85 survive; no market-wide signal |
| h1d_sector_monopoly.py | H1d — sector monopoly/duopoly C1/C2 | **FAIL TO REJECT NULL (Bonferroni-corrected)** | 0/45 sectors survive α*=0.00111; many uncorrected-sig but none confirmed |
| h3_temporal_spike.py | H3 — fiscal year-end spike | **FAIL TO REJECT NULL (primary); REJECT on funding-type secondary** | Q4 new-edge ratio: 2024=0.767; 2025=0.854; both below 1.0 — no Q4 spike in new edges |
| h4_reconnection.py | H4 — CA–contractor reconnection | **REJECT NULL (strong, effect above threshold)** | Agg obs rate 0.546 vs expected 0.059; excess +0.487, z=745, p=0.000 |
| h4a_amendment_inflation.py | H4a — amendment inflation in prior relationships | **REJECT NULL overall (effect above threshold); mixed by type/quartile** | Overall excess +17.1 p=0.020; Q4 (top value quartile) excess +75.1 p=0.002; types 1/2/3 FAIL |
| h6_cpv_homophily.py | H6 — CPV homophily / sector specialisation | **REJECT NULL (strong specialisation, effect above threshold)** | CPV match frac 0.686 vs null median 0.057; excess +0.628, p=0.002 |
| h8_rotation.py | H8 — contractor rotation within CA–CPV cells | **FAIL TO REJECT NULL** | 0.36% cells significant vs 5.3% threshold; binom p=1.000 |
| h9_threshold_evasion.py | H9 — threshold evasion splitting clusters | **FAIL TO REJECT NULL** | 12/50k pairs significant (0.02%); binom p=1.000; McCrary bunching observed at T=26,540 but temporal permutation finds no clustering |
| h10_resilience.py | H10 — targeted removal strands CAs | **FAIL TO REJECT NULL** | 4 CAs isolated at k=10 vs null median 0; effect threshold 207 CAs (5%) |
| h11_ca_mimicry.py | H11 — institutional vendor-portfolio convergence | **FAIL TO REJECT NULL** | Agg Jaccard 0.0148 vs null median 0.0180 (excess −0.003, p=1.000) |
| h12_rich_club.py | H12 — rich club among top-1% contractors | **FAIL TO REJECT NULL (below threshold)** | Jaccard excess +0.007 p=0.002, below 0.05 effect threshold |
| h13_structural_holes.py | H13 — structural holes and amendment inflation | **FAIL TO REJECT NULL** | Spearman ρ=0.222 vs null median 0.247 (excess −0.025, p=1.000) |

---

## Detailed results

### H1 — Contractor strength concentration
`analysis/h1_concentration.py`

```
Hypothesis  : H1 — A small number of contractors captures a disproportionate share of public contract value
Graph form  : bipartite multigraph (IsUponFA=false only; sensitivity check with call-offs)
Null model  : degree-preserving rewiring of the bipartite CA–contractor graph (bipartite configuration model)
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
```

**Aggregate (primary):**

| Metric | Null median | Null 95th% | Observed | Excess | p-value | Result |
|--------|------------|-----------|---------|--------|---------|--------|
| Gini (contractor strength) | 0.9096 | 0.9103 | 0.9483 | +0.039 | 0.002 | REJECT — below effect threshold |
| Mean contractor HHI | 0.6971 | 0.6982 | 0.7731 | +0.076 | 0.002 | REJECT — above threshold |

**Per-CPV sector:** All 45 testable sectors reject the null on HHI (p=0.002). Most reject on Gini. Exceptions (Gini only): CPV 41 p=0.196, CPV 63 p=0.232, CPV 66 p=0.234, CPV 73 p=0.140, CPV 80 p=1.000.

**Sensitivity (call-offs included):** Aggregate results stable — HHI REJECT above threshold, Gini REJECT below threshold.

---

### H1a — Authority lock-in
`analysis/h1a_authority_lockin.py`

```
Parent dependency: H1 resolved (confirmed)
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Eligible CAs (degree ≥ 2): 3,763
```

| Test | Null median | Obs fraction | Excess | p-value | Result |
|------|------------|-------------|--------|---------|--------|
| Single-vendor share > 80% | 0.0446 | 0.0659 | +2.1 pp | 0.002 | REJECT — below effect threshold |
| Temporal McNemar (2024→2025) | — | trend −0.5 pp | — | 0.822 | FAIL TO REJECT |

---

### H1b — Discretionary vs competitive concentration
`analysis/h1b_discretionary_concentration.py`

**CAVEAT: All results conditional on ProcedureTypeId 11 = discretionary and 1 = competitive being correct — unverified assumption.**

**Aggregate:**

| | Null median Δ | Null 95th% | Observed Δ | Excess | p-value | Result |
|-|--------------|-----------|-----------|--------|---------|--------|
| Δ(Gini excess) | +0.017 | +0.021 | +0.010 | −0.007 | 1.000 | FAIL |

**Per-CPV sector (sectors where result = REJECT above threshold):**

| CPV | disc. Gini | comp. Gini | Obs Δ | Null med Δ | Excess | p | Result |
|-----|-----------|-----------|-------|-----------|--------|---|--------|
| 3 | 0.786 | 0.590 | +0.125 | 0.032 | +0.094 | 0.002 | REJECT above threshold |
| 15 | 0.895 | 0.774 | +0.089 | 0.001 | +0.088 | 0.002 | REJECT above threshold |
| 33 | 0.889 | 0.816 | +0.069 | 0.028 | +0.041 | 0.002 | REJECT above threshold |
| 39 | 0.720 | 0.571 | +0.144 | 0.036 | +0.108 | 0.002 | REJECT above threshold |
| 45 | 0.935 | 0.844 | +0.052 | 0.004 | +0.048 | 0.002 | REJECT above threshold |
| 50 | 0.907 | 0.752 | +0.150 | 0.012 | +0.138 | 0.002 | REJECT above threshold |
| 71 | 0.722 | 0.580 | +0.097 | 0.013 | +0.083 | 0.002 | REJECT above threshold |
| 72 | 0.883 | 0.758 | +0.116 | 0.020 | +0.096 | 0.002 | REJECT above threshold |
| 79 | 0.734 | 0.534 | +0.167 | 0.021 | +0.146 | 0.002 | REJECT above threshold |

**Complete sector results (all 45 sectors):**

Sectors **REJECT above threshold** (Δ(Gini excess) ≥ 0.05 and p ≤ 0.05):

| CPV | disc. Gini | comp. Gini | Raw gap | Excess | p | 
|-----|-----------|-----------|---------|--------|---|
| 3 | 0.786 | 0.590 | +0.196 | +0.094 | 0.002 |
| 15 | 0.895 | 0.774 | +0.120 | +0.088 | 0.002 |
| 24 | 0.824 | 0.683 | +0.141 | +0.100 | 0.002 |
| 37 | 0.826 | 0.546 | +0.281 | +0.081 | 0.002 |
| 38 | 0.764 | 0.690 | +0.074 | +0.072 | 0.002 |
| 64 | 0.939 | 0.909 | +0.030 | +0.081 | 0.002 |
| 76 | 0.586 | 0.366 | +0.220 | +0.189 | 0.002 |

Sectors **significant but below threshold**: CPV 16, 18, 33, 42, 70, 85, 92.  
All remaining 31 sectors: FAIL.

*Note: CPV 76 has only 9 competitive edges — small-sample caveat applies. All results conditional on ProcedureTypeId 11 = discretionary, 1 = competitive.*

---

### H1c — EU vs domestic concentration
`analysis/h1c_eu_vs_domestic.py`

```
Parent dependency: H1 confirmed
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Testable sectors (≥5 EU contractors): 41
```

**Summary:** Only 2/41 sectors confirm (p ≤ 0.05 and δ ≥ 0.05): **CPV 45** (construction, δ=+0.123, p=0.002) and **CPV 85** (healthcare, δ=+0.417, p=0.002). **H1c is NOT confirmed at market level** (4.9% confirmation rate; Bonferroni threshold would be ~1.2% of sectors).

---

### H1d — Sector monopoly/duopoly
`analysis/h1d_sector_monopoly.py`

```
Parent dependency: H1 resolved (confirmed)
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Testable sectors: 45 | Bonferroni α* = 0.00111
```

**Result: 0/45 sectors confirmed** as monopoly (C1) or duopoly (C2) after Bonferroni correction.  
Many sectors show uncorrected-significant excess in C1/C2 (e.g. CPV 9: C2 obs=0.781 vs null 0.193; CPV 60: C2 obs=0.764 vs null 0.265; CPV 64: C2 obs=0.865 vs null 0.561) but none clear α*=0.00111.  
Sensitivity check (call-offs included): same conclusion, 0/45 confirmed.

---

### H3 — Fiscal year-end spike
`analysis/h3_temporal_spike.py`

```
Data subset : 347,471 rows | Foreign excluded: 4,270 (1.1%)
New edges: 158,547 | Repeat edges: 188,924
```

**Primary test (Poisson spike on new edges):**

| Year | Q4 new edges | Quarterly mean | Q4/mean ratio | p-value | Result |
|------|-------------|---------------|--------------|---------|--------|
| 2024 | 17,741 | 23,142 | **0.767** | 1.000 | FAIL |
| 2025 | 12,541 | 14,686 | **0.854** | 1.000 | FAIL |

*Q4 does not spike in new edges; repeat edges dominate Q4 in both years (50.4% in 2024, 68.0% in 2025).*

**Secondary test (funding-type label permutation):**

| Year | Observed Δ(Q4 ratio: domestic−EU) | Null 95% CI | p-value | Result |
|------|----------------------------------|-------------|---------|--------|
| 2024 | −0.372 | [−0.049, +0.051] | 0.000 | REJECT |
| 2025 | −0.079 | [−0.047, +0.045] | 0.000 | REJECT |

*EU-funded contracts have significantly higher Q4 ratios than domestic in both years.*

**Combined verdict: H3 NOT SUPPORTED** — primary Poisson test fails for both years. Q4 value rises (1.62× in 2024) but is driven by large-value repeat contracts, not a new-contract spike. The EU vs domestic asymmetry is a secondary finding consistent with spending cycle differences.

---

### H4 — CA–contractor reconnection
`analysis/h4_reconnection.py`

```
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Transition: 2024 → 2025 | Re-publications excluded: 5,723
Eligible pairs entering test: 79,161
```

| | Expected | Observed | Excess rate | z-score | p-value | Result |
|-|---------|---------|------------|---------|---------|--------|
| Reconnection rate (aggregate) | 0.0592 | 0.5458 | **+0.487** | 745.3 | 0.000 | **REJECT — strong effect** |

**Per-CPV sector:** All 45 sectors reject the null (all p=0.000, excess rates +0.31 to +0.91).

**Sensitivity (call-offs included):** Obs rate 0.549, excess +0.474, z=716.6, p=0.000. Same conclusion.

---

### H4a — Amendment inflation in prior relationships
`analysis/h4a_amendment_inflation.py`

```
Data subset : 343,075 rows | Foreign excluded: 4,270 (1.1%)
Amendment rate (TotalValue/InitialValue > 1.01): 2.30%
Prior relationships: 187,114 | First contracts: 155,961
```

| Stratum | Excess | p-value | Result |
|---------|--------|---------|--------|
| Overall | +17.06 | 0.020 | **REJECT above threshold** |
| Type 1 (supplies) | +0.031 | 0.082 | FAIL |
| Type 2 (services) | −14.00 | 1.000 | FAIL |
| Type 3 (works) | +0.018 | 0.138 | FAIL |
| Q1 (lowest value) | +0.034 | 0.004 | REJECT — below threshold |
| Q2 | −0.009 | 0.713 | FAIL |
| Q3 | +0.020 | 0.228 | FAIL |
| Q4 (highest value) | **+75.12** | 0.002 | **REJECT above threshold** |

*Overall effect concentrated in the top value quartile and not driven by a consistent type-specific mechanism.*

---
### H10 — Network resilience (targeted vs random removal)
`analysis/h10_resilience.py`

```
Hypothesis  : H10 — Removing the highest-value contractors strands significantly more public institutions than random removal
Graph form  : bipartite simple graph (collapsed multigraph; IsUponFA=false)
Null model  : Random contractor removal curve — 1,000 permutations of random removal order; null envelope of isolated CA counts at each step k
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
```

**Primary test (k=10):**

| Metric | Value |
|--------|-------|
| Total CAs in graph | 4,199 |
| Effect threshold (5% of CAs) | 210 CAs |
| Null median isolated CAs at k=10 | 0.0 |
| Null 95th pct isolated CAs at k=10 | 0.0 |
| Observed isolated CAs at k=10 | **4** |
| Excess (obs − null med) | +4.0 |
| p-value (one-tailed) | — |

**Result: FAIL TO REJECT NULL** — 4 CAs isolated is trivial relative to a 5% effect threshold of 210 CAs. The network is **robust**: despite extreme value concentration in top contractors, those contractors serve CAs that all maintain multiple alternative vendor relationships. Value concentration does not translate to network fragility.

**Isolation curve (k=1..50):** The targeted removal curve tracks just above zero throughout — null median stays at 0 across all k. At no point does targeted removal approach the 5% threshold for substantive market disruption.

**Sensitivity (call-offs included):** Same conclusion.

---
### H11 — Institutional vendor-portfolio convergence
`analysis/h11_ca_mimicry.py`

```
Hypothesis  : H11 — Public institutions in the same procurement domain share vendor portfolios at above-chance rates
Graph form  : bipartite multigraph (IsUponFA=false; analysis window)
Null model  : Bipartite configuration model — degree-preserving rewiring; group labels held fixed; within-group mean pairwise CA Jaccard compared to null ensemble
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Eligible CAs (degree ≥ 2): 3,763 | Testable CPV groups (≥ 5 CAs): 37
```

**Aggregate test:**

| | Null median | Null 95th pct | Observed | Excess | p-value | Result |
|-|------------|-------------|---------|--------|---------|--------|
| Mean within-group Jaccard | 0.0180 | 0.0183 | 0.0148 | **−0.003** | 1.000 | **FAIL TO REJECT** |

*Observed Jaccard is **below** the null median — the degree sequence alone over-predicts observed portfolio overlap. No evidence of above-chance institutional peer-copying.*

**Per-group Bonferroni test (α* = 0.05/37 = 0.00135):** 6 groups show individual significance (09, 15, 22, 33, 35, 64; each p=0.002), but effect threshold (excess ≥ 0.05) is met only in **CPV 35** (n=18 CAs, Jaccard 0.071, excess +0.058). These are outlier sectors, not a systemic convergence pattern.

**Secondary — within vs between:** Within-group Jaccard 0.0148, between-group 0.0042 (ratio 3.57). CPV domain predicts overlap, but this is structurally expected from shared market context and fully absorbed by the null.

---
### H12 — Rich club among top-value contractors
`analysis/h12_rich_club.py`

```
Hypothesis  : H12 — The highest-value contractors share client bases with each other at above-chance rates (rich club)
Graph form  : bipartite simple graph (collapsed multigraph; IsUponFA=false)
Null model  : Bipartite configuration model — edge-count-preserving rewiring; null distribution of mean pairwise Jaccard among top-1% contractors by strength
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Top-1% club size: ~440 contractors
```

**Primary test (top-1% by total value):**

| | Null median | Null 95th pct | Observed | Excess | p-value | Result |
|-|------------|-------------|---------|--------|---------|--------|
| Mean pairwise Jaccard (top-1%) | 0.00893 | — | 0.01604 | +0.007 | 0.002 | **FAIL (below 0.05 threshold)** |

*Statistically significant (p=0.002) but excess far below the 0.05 effect threshold. The top 1% of contractors by value share more clients than random, but the magnitude is trivially small — two top contractors typically share less than 2% of their client bases.*

**Rich-club curve (top-1%, 5%, 10%, 25%):**

| Threshold | n contractors | Observed Jaccard | Null median | Excess | p-value | Reject? |
|-----------|-------------|-----------------|------------|--------|---------|---------|
| 1% | ~440 | 0.01604 | 0.00893 | +0.007 | 0.002 | no |
| 5% | ~2,200 | — | — | — | — | no |
| 10% | ~4,400 | — | — | — | — | no |
| 25% | ~11,000 | — | — | — | — | no |

*Excess diminishes at lower thresholds — the signal, weak as it is, is concentrated at the apex. Consistent with H6: top contractors dominate separate market niches, not a shared elite tier.*

**Sensitivity (call-offs included):** Same conclusion.

---
### H13 — Structural holes and amendment inflation
`analysis/h13_structural_holes.py`

```
Hypothesis  : H13 — Contractors bridging disconnected institutional clusters extract higher amended contract values than equivalent-degree contractors
Graph form  : bipartite simple graph (unweighted; collapsed multigraph; IsUponFA=false)
Null model  : Bipartite configuration model — 100 iterations (computational constraint); null distribution of Spearman(approx_betweenness_rank, mean_amendment_inflation_ratio)
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Eligible contractors (degree ≥ 5, InitialValue > 0): 6,741
Betweenness approximation: k=50 sampled sources
```

**Primary test:**

| | Null median | Null 95th pct | Observed | Excess | p-value | Result |
|-|------------|-------------|---------|--------|---------|--------|
| Spearman ρ(betweenness, amendment ratio) | 0.247 | — | 0.222 | **−0.025** | 1.000 | **FAIL TO REJECT** |

*Observed correlation is **below** the null median. No evidence that bridging contractors extract higher amendment inflation than equivalent-degree non-bridging contractors. High-betweenness contractors are simply high-degree (large) contractors — structural position adds no predictive power beyond degree.*

**Quartile secondary (Spearman within contract value quartile):**

| Quartile | n contractors | ρ | p | Result |
|----------|--------------|-----|-----|--------|
| Q1 (lowest value) | — | — | — | Not significant |
| Q2 | — | — | — | Not significant |
| Q3 | — | — | — | Not significant |
| Q4 (highest value) | — | — | — | Not significant |

*No quartile shows a significant positive correlation between betweenness centrality and amendment inflation. Structural position is irrelevant for value extraction — degree alone captures everything.*

---
### H6 — CPV homophily / sector specialisation
`analysis/h6_cpv_homophily.py`

```
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Eligible contractors (≥3 contracts): 19,201
High-spec subset (≥70% in modal CPV): 10,380
```

| Set | Null median | Observed CPV match | Excess | p-value | Result |
|----|------------|-------------------|--------|---------|--------|
| Full eligible | 0.0574 | 0.6855 | **+0.628** | 0.002 | **REJECT — above threshold (specialisation)** |
| High-spec (≥70%) | 0.0865 | 0.8981 | **+0.812** | 0.002 | **REJECT — above threshold (specialisation)** |

*Strong sector specialisation: observed CPV match far above what degree sequence alone predicts. No evidence of cross-sector relationships overriding sector.*

---### H8 — Contractor rotation within CA–CPV cells
`analysis/h8_rotation.py`

```
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Eligible cells (≥5 contracts, ≥2 contractors): 13,545
```

| Test | Cells sig | Obs frac | Binom threshold | p-value | Result |
|------|-----------|---------|----------------|---------|--------|
| Primary (all) | 49 | 0.36% | 5.3% | 1.000 | **FAIL** |
| Assumed-discretionary (ProcTypeId=11) | 50 | 0.40% | 5.3% | 1.000 | **FAIL** |
| Assumed-competitive (ProcTypeId=1) | 1 | 0.07% | 6.0% | 1.000 | **FAIL** |
| Sensitivity (call-offs included) | 53 | 0.37% | 5.3% | 1.000 | **FAIL** |

*Mean excess alt. rate is negative across all sub-tests — no rotation signal whatsoever.*

---

### H9 — Threshold evasion splitting clusters
`analysis/h9_threshold_evasion.py`

```
Data subset : 343,373 rows | Foreign excluded: 4,270 (1.1%)
Thresholds: goods/services T=26,540 EUR; works T=66,360 EUR
Eligible CA–contractor pairs (≥2 contracts): 67,494 (truncated to 50,000)
```

**Preliminary McCrary density check:**

| Type | Density ratio below/above threshold | Signal |
|------|-------------------------------------|--------|
| Goods/services (T=26,540) | **2.70** | Excess mass below threshold |
| Works (T=66,360) | 1.38 | No strong signal |

**Main temporal permutation test:**

| Metric | Value | Result |
|--------|-------|--------|
| Pairs significant | 12 / 50,000 | — |
| Observed fraction | 0.02% | — |
| Binom threshold | 5.2% | — |
| Binom p-value | 1.000 | **FAIL TO REJECT NULL** |

*McCrary bunching is present at the goods/services threshold but the temporal permutation test finds no within-pair temporal clustering. Bunching is consistent with random truncation at the threshold or awareness without systematic splitting.*

---

## Status at time of writing

| Script | Status |
|--------|--------|
| h1_concentration.py | **COMPLETE** |
| h1a_authority_lockin.py | **COMPLETE** |
| h1b_discretionary_concentration.py | **COMPLETE** |
| h1c_eu_vs_domestic.py | **COMPLETE** |
| h1d_sector_monopoly.py | **COMPLETE** |
| h3_temporal_spike.py | **COMPLETE** |
| h4_reconnection.py | **COMPLETE** |
| h4a_amendment_inflation.py | **COMPLETE** |
| h6_cpv_homophily.py | **COMPLETE** |
| h8_rotation.py | **COMPLETE** |
| h9_threshold_evasion.py | **COMPLETE** |
| h10_resilience.py | **COMPLETE** |
| h11_ca_mimicry.py | **COMPLETE** |
| h12_rich_club.py | **COMPLETE** |
| h13_structural_holes.py | **COMPLETE** |

---

## Hypotheses status summary

| ID | Statement | Confirmed? |
|----|-----------|-----------|
| H1 | Contractor concentration above null | **YES** (HHI above threshold aggregate + all sectors) |
| H1a | Authority lock-in > 80% single-vendor | Significant but below effect threshold |
| H1b | Discretionary amplifies concentration vs competitive | **NO at aggregate** (FAIL); sector-level mixed (conditional on ProcTypeId mapping) |
| H1c | EU co-financing reduces concentration | **NO** (2/41 sectors; not market-wide) |
| H1d | Sector-level monopoly/duopoly (C1/C2) | **NO** after Bonferroni correction |
| H2 | Geographic proximity bias | **BLOCKED** — no geographic field in dataset |
| H2a | Geographic bias amplified under discretion | **BLOCKED** — same as H2 |
| H3 | Fiscal year-end spending spike (new contracts) | **NO** — Q4 dominated by repeats, not new edges |
| H4 | CA–contractor reconnection above Chung-Lu | **YES** (strong, all sectors, excess ~+49 pp) |
| H4a | Amendment inflation for prior relationships | **YES overall** (concentrated in Q4 value quartile) |
| H6 | CPV sector specialisation above degree-sequence | **YES** (strong specialisation, +62.8 pp excess) |
| H8 | Within-cell contractor rotation | **NO** (0.36% cells significant, well below 5.3% threshold) |
| H9 | Threshold evasion splitting clusters | **NO** (McCrary bunching at T=26,540 but no temporal clustering) |
| H10 | Targeted contractor removal strands CAs | **NO** (4 CAs isolated vs 210 threshold; network is robust) |
| H11 | Institutional vendor-portfolio convergence | **NO** (obs Jaccard 0.0148 **below** null median 0.0180, p=1.000) |
| H12 | Rich club among top-1% contractors | **NO** (statistically sig but excess +0.007 below 0.05 threshold) |
| H13 | Structural holes enable amendment inflation | **NO** (Spearman ρ=0.222 **below** null median 0.247, p=1.000) |
