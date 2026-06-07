# Hypothesis Tree: Croatian Public Procurement

This is the living research agenda. Hypotheses are organised by domain question. Branches test the same underlying claim from a different angle or under a different conditioning set. Every hypothesis states a mechanism, a null model, a test specification, and a graph signal.

Status labels: `open` · `active` · `blocked` · `resolved-reject` · `resolved-confirm` · `exploratory`

`blocked`: hypothesis cannot be tested with current data — do not begin analysis.  
`exploratory`: data is available but conditions for confirmatory claims are not met; results cannot be elevated to findings without a separate pre-registered test.

---

## Market Concentration

**The underlying question**: Does the distribution of public money across contractors reflect market structure, or does it reflect preferential access?

In a small economy, some concentration is structurally inevitable — few firms can supply specialised goods. The question is whether observed concentration exceeds what the degree sequence of the procurement network alone predicts. Excess concentration, after controlling for sector, is the signature of preferential access rather than natural market structure.

---

### H1 — A small number of contractors captures a disproportionate share of public contract value `resolved-confirm`

**In plain terms**: When controlling for how many clients a contractor serves and how many contracts an authority issues, do the same few companies still receive far more public money than their market size alone would predict?

**Mechanism**: Contracting authorities repeatedly return to familiar vendors, producing a contractor node strength distribution more skewed than the bipartite degree sequence alone would generate. This is relational lock-in: not a single corrupt act, but accumulated preference across many independent contracting decisions.

**Null model**: Bipartite configuration model.

**Graph construction**: Primary graph excludes `IsUponFA = true` contracts (rationale: `docs/DATA_PROFILE.md §7`).

**Test**: One-tailed. The observed Gini of contractor node strength is compared to the ensemble distribution of Gini values from the null. Reject if the observed Gini exceeds the 95th percentile of the null distribution (α = 0.05). Test must be run within CPV sector, not only in aggregate.  
**Effect threshold**: Minimum Gini excess (observed − null median) of **0.05**. Results below this threshold are statistically significant but not substantively meaningful.

**Secondary metric — contractor portfolio HHI**: For each contractor node i, compute the inverse participation ratio (IPR), equivalently the Herfindahl-Hirschman Index of contractor i's CA portfolio: Y_i = Σ_j (w_ij / s_i)², where w_ij is the edge value to CA j and s_i is total contractor strength. Y_i is not a "participation ratio" (which would be 1/Y_i, the effective number of CAs) but its inverse: Y_i → 1 indicates complete concentration on a single CA (captive vendor); Y_i → 1/k_i (the lower bound under equal weights across k_i CAs) indicates broad market distribution. Compare mean Ȳ across contractor nodes to the null ensemble mean. Reject if observed Ȳ exceeds the 95th percentile of the null (α = 0.05). **Effect threshold**: excess mean HHI (observed − null median) ≥ **0.05**. Gini measures aggregate value concentration across contractors; contractor portfolio HHI measures whether each contractor's revenue concentrates on few CA relationships or spreads broadly. Both must be reported and interpreted together.

**Graph signal (active)**: Gini coefficient of contractor node strength (total awarded value per contractor) is significantly higher than the null ensemble. Excess concentration is visible beyond what structure alone produces. Mean contractor disparity also significantly exceeds the null — contractor strength concentrates on single-authority relationships, consistent with captive vendor dynamics rather than broad market leadership.

**Graph signal (absent)**: Observed Gini falls within the null distribution. Concentration is explained by the degree sequence — large contractors win more because they serve more authorities, not because they have preferential access to any specific one.

**Real-world meaning**:  
*If confirmed:* A small number of companies receives a share of Croatian public funds that their market size alone cannot explain. For a business trying to enter the market, this is a structural barrier: access to public contracts is not purely a function of capability and capacity, but also of relational position. For the taxpayer, it means competitive pressure — which should push prices down and quality up — is partially absent. The specific contractors and sectors where this is largest are identifiable from the analysis.  
*If rejected:* Concentration is proportional to market volume. The companies that dominate procurement do so because they are genuinely large and serve many institutions — not because of relational preference. The distribution of public money is consistent with a size-stratified competitive market.

**Strongest innocent alternative**: Sector specialisation. Some CPV sectors have very few qualified vendors; high concentration within those sectors is expected and legitimate. This alternative is addressed by conditioning on CPV sector before testing — concentration must exceed the null within sector, not just in aggregate.

---

### H1a — Individual public institutions award the majority of their budget to a single vendor at above-chance rates `resolved-reject`

*Branch of H1. Tests the same concentration claim at the level of individual authorities rather than the market overall.*

**In plain terms**: Do many public institutions end up with one company receiving more than 80% of their total contract budget — at rates that cannot be explained by the institution's small size or narrow mandate?

**Parent dependency**: H1 must resolve (in either direction) before H1a results are interpreted. If H1 confirms, H1a examines whether the aggregate signal is driven by extreme individual cases. If H1 rejects, H1a tests whether concentration that is invisible at the market level is present at the authority level.

**Mechanism**: Individual authorities develop persistent exclusive relationships with single vendors — not through cartel behaviour but through institutional inertia and risk aversion. Once a vendor has delivered, the authority avoids switching even when competitive procedures would require it.

**Null model**: Bipartite configuration model. Degree-driven share concentration is absorbed by the null; restricted to authority nodes with degree ≥ 2.

**Graph construction**: Same as H1.

**Test**: One-tailed. The observed fraction of authority nodes exceeding a single-vendor spend share threshold of **80%** is compared to the null ensemble distribution of the same statistic. Reject if the observed fraction exceeds the 95th percentile of the null (α = 0.05).  
**Effect threshold**: Minimum excess fraction (observed − null median) of **10 percentage points**. An 80% single-vendor spend share represents functional dependence on one vendor; an excess fraction below 10pp over the null is not substantively meaningful.

**Secondary test — temporal trend**: Restrict to CAs with ≥ 2 contracts in each of the 2024 and 2025 annual subgraphs. Compute single-vendor spend share within each annual subgraph and record the fraction of CAs exceeding 80% in each year. Apply a one-tailed McNemar test on matched pairs (same CA observed in both years) to test whether the 2025 fraction exceeds the 2024 fraction (α = 0.05). **Effect threshold**: increase ≥ **5 percentage points** (2025 fraction − 2024 fraction). A static high fraction is consistent with structural explanation; a fraction that increases from 2024 to 2025 is not.

**Graph signal (active)**: A non-trivial fraction of authority nodes allocate the majority of their spend to a single contractor at a rate that significantly exceeds the configuration model null. The distribution of single-vendor spend share across authorities is more right-skewed than the null predicts.

**Graph signal (absent)**: The fraction of authorities with high single-vendor concentration is consistent with the null. Authorities that appear locked in have degree one or two, making concentration structurally trivial rather than behaviourally meaningful.

**Real-world meaning**:  
*If confirmed:* A substantial share of Croatian public institutions effectively operate with a single preferred supplier receiving more than 80% of their contract budget. For qualified companies not already in that relationship, the institution's procurement outcomes are structurally predetermined — not decided contract by contract. For oversight bodies, single-vendor dependence is a direct risk factor: any pricing dispute, conflict of interest, or delivery failure at the captive vendor has immediate consequences for the institution's service delivery.  
*If rejected:* High single-vendor shares at the authority level are explained by the institution's narrow mandate and small size: a specialised hospital, a small municipality. The concentration is structural, not relational — and does not indicate preferential selection.

**Strongest innocent alternative**: Authorities with narrow mandates (a single hospital, a single school) legitimately have few contractor relationships. This alternative is addressed by excluding authorities with only one contract in the observation window, for whom a concentration ratio of 1.0 is trivially structural.

---

### H1b — Removing the competitive requirement amplifies vendor concentration `resolved-reject`

*Branch of H1. Tests whether preferential access is amplified where authorities have unilateral vendor selection discretion.*

**In plain terms**: When the law does not require open competition — in direct awards below the procurement threshold — is public money distributed even more narrowly than in procedures where competition is legally required?

**Classification caveat (binding)**: `ProcedureTypeId` label mapping is not available in the dataset. The classification ID 11 = discretionary (below-threshold direct award) and ID 1 = competitive (open procedure) is a working assumption, not a verified fact. All results from this hypothesis are conditional on this classification being correct and must be reported as "consistent with higher concentration in what is assumed to be discretionary procurement" — not as "discretionary procurement is more concentrated." This caveat applies to the null model, the test, and any reported finding (data gap documented in `docs/DATA_PROFILE.md §7`).

**Parent dependency**: Soft. H1b can run regardless of H1's outcome, but interpretation differs: if H1 confirms, H1b decomposes the anomalous signal; if H1 rejects, H1b tests whether differential subgraph structure exists where no aggregate anomaly is present — a weaker and harder-to-interpret result. H1's outcome direction must be stated before H1b results are reported.

**Mechanism**: Where authorities have unilateral discretion over vendor selection (no legal obligation to compete), preferential access compounds — the same vendors are chosen repeatedly because there is no competitive pressure forcing alternatives. In competitive procedures, the legal process constrains the choice even if relationships exist. If preferential access drives concentration, Gini excess over the configuration model null should be larger in the assumed-discretionary subgraph than the assumed-competitive subgraph.

**Null model**: Procedure-type label permutation. Note: the permutation randomises what are themselves assumed labels — this must appear in the reported method.

**Test**: One-tailed. The observed Δ(Gini excess) is compared to the permutation null distribution. Reject if the observed Δ exceeds the 95th percentile of the null (α = 0.05). Test must be run within CPV sector.  
**Effect threshold**: Minimum Δ(Gini excess) of **0.05** — consistent with H1's effect floor, the unit of measurement across the Market Concentration domain.

**Graph signal (active)**: Gini excess is significantly larger in the assumed-discretionary subgraph than the assumed-competitive subgraph, exceeding the permutation null. Consistent with preferential access being amplified by discretion.

**Graph signal (absent)**: No significant difference in Gini excess between subgraphs. Concentration does not vary by assumed procedure type. Either the mechanism is not present, or the classification assumption is wrong — these cannot be distinguished without the label mapping.

**Real-world meaning**:  
*If confirmed (under the classification assumption):* Legal competitive requirements appear to partially restrain preferential vendor selection: where the requirement is absent, the concentration of public money in a small number of companies is measurably higher. This is direct evidence for the value of competitive thresholds — raising or enforcing them would, under this finding, widen the distribution of public contracts. For small companies, the direct-award market is structurally less accessible than the open-procedure market.  
*If rejected:* Concentration does not differ between assumed-discretionary and assumed-competitive awards. Either competitive procedure requirements do not meaningfully change who wins contracts, or the procedure-type classification assumption is incorrect. Both interpretations must be reported — the data cannot distinguish between them without the verified label mapping.

**Strongest innocent alternative**: Below-threshold contracts (assumed ID 11) are smaller and served by different market segments than open-procedure contracts. CPV sector conditioning addresses this; if the differential disappears after conditioning, the mechanism is not supported.

---

### H1c — EU co-financing requirements reduce vendor concentration relative to domestic procurement `resolved-reject`

*Branch of H1. Tests whether external oversight suppresses preferential vendor access.*

**In plain terms**: Is public money distributed to a wider range of companies when EU co-financing brings external auditors and stricter eligibility rules, compared to contracts funded purely from the national budget?

**Parent dependency**: H1 must confirm (aggregate concentration anomalous) before H1c is interpretable. Without a confirmed excess, there is no preferential access signal to decompose.

**Mechanism**: EU co-financed procurement is subject to external audit, stricter eligibility rules, and reporting requirements set by the funding programme. These oversight mechanisms constrain authorities' vendor selection discretion in ways that domestic procurement is not. If preferential access drives the concentration anomaly in H1, EU oversight should partially suppress it — producing lower Gini excess in the EU-funded subgraph than in the domestic-funded subgraph.

**Null model**: Funding-type label permutation. Permute the `ContractEUFinanc` label across all edges within each CPV sector, holding the number of EU-funded edges fixed. For each permutation, compute the Gini of contractor strength in each resulting subgraph (domestic and EU-funded); the permutation null distribution of (Gini_domestic − Gini_EU) within each sector constitutes the test baseline. Comparing two independently estimated Gini excesses from separate null model runs is not a valid test — the correct baseline is the difference between subgraph Ginis under random funding-label assignment, which holds degree sequence and sector composition constant.

**Graph construction prerequisite**: The EU-funded subgraph must contain ≥ **5 distinct contractors** per CPV sector before the test runs. Sectors below this threshold are reported as underpowered and do not contribute to or invalidate results from adequately-powered sectors.

**Test**: One-tailed. For each adequately-powered CPV sector, compare the observed (Gini_domestic − Gini_EU) to the 95th percentile of the permutation null distribution (α = 0.05). The effect threshold serves as an additional gate on top of the statistical test.  
**Effect threshold**: Minimum observed difference in Gini (domestic − EU-funded) of **0.05** — consistent with H1's effect floor across the Market Concentration domain. Both the p-value criterion and the effect threshold must be satisfied for a sector to count as confirming.

**Graph signal (active)**: Gini excess over the configuration model null is substantially lower in EU-funded contracts than in domestic-funded contracts after conditioning on CPV sector. Consistent with oversight suppressing preferential access.

**Graph signal (absent)**: No meaningful difference in Gini excess between subgraphs. Oversight intensity does not predict concentration. Concentration is structural rather than a product of unconstrained discretion.

**Real-world meaning**:  
*If confirmed:* External institutional oversight changes procurement outcomes in a measurable way. The concentration of public funds among a small number of vendors is lower precisely where EU auditors and eligibility requirements impose additional scrutiny on vendor selection decisions. This is direct evidence that stronger accountability mechanisms broaden access to public contracts — and that the absence of such mechanisms in purely domestic procurement is a structural risk factor.  
*If rejected:* EU oversight does not produce a measurably different contractor distribution. Concentration is equally present in EU-funded and domestic contracts — suggesting either that the oversight mechanisms do not reach vendor selection decisions, or that the concentration observed in H1 has a structural explanation that oversight cannot address.

**Strongest innocent alternative**: EU-funded contracts cluster in specific CPV sectors (infrastructure, large works) where market structure differs from the rest of the portfolio. Addressed by conditioning on CPV sector before comparing subgraphs.

---

### H1d — Specific procurement sectors are structurally dominated by one or two companies beyond their market volume `resolved-reject`

*Branch of H1. Decomposes H1's aggregate concentration signal into sector-level market structure: which specific CPV sectors are monopolised or duopolised beyond what degree sequence predicts.*

**In plain terms**: In identifiable procurement categories — specific types of goods, services, or works — does a single company, or a pair of companies together, hold a share of total sector value too large to be explained by how many clients they serve?

**Stated**: 2026-05-23. Stated before any examination of per-sector C1/C2 concentration ratios in the data.

**Parent dependency**: H1 must resolve (in either direction) before H1d is interpreted. If H1 confirms aggregate concentration anomaly, H1d identifies which sectors drive it. If H1 rejects, H1d tests whether sector-level monopoly or duopoly structure exists even where the aggregate Gini is within the null — a weaker configuration that must be stated explicitly if found.

**Mechanism**: H1's Gini statistic measures aggregate inequality across all contractors in a sector but does not specifically identify sectors where one contractor (monopoly) or two contractors together (duopoly) hold anomalously large shares. A sector with moderate Gini can still have extreme C1 concentration. Relational incumbency can consolidate repeat awards toward a single dominant firm — or toward a two-firm equilibrium where the contractors divide the sector's CAs between them. C1 and C2 tested against the bipartite null are the direct measures of these structural positions.

**Operationalisation**:
- *C1 per sector*: share of total sector `TotalValue` held by the single contractor with highest strength in that sector.
- *C2 per sector*: share held by the top two contractors combined.
- Sector = CPV 2-digit division. Sector minimum: ≥ **5 distinct contractors** — sectors with fewer cannot produce informative null distributions and are reported as structurally thin, not tested.

**Null model**: Bipartite configuration model. In each null instance, compute C1 and C2 per CPV sector. The null ensemble distributions of C1 and C2 per sector constitute the test baseline.

**Graph construction**: Same as H1.

**Test**: One-tailed per sector. The observed C1 (C2) in each sector is compared to its null ensemble distribution. Report C1 and C2 separately — a sector where C2 significantly exceeds the null but C1 does not is duopoly structure; a sector where C1 significantly exceeds the null is monopoly structure.

**Multiple testing correction**: Testing C1 and C2 across all adequately-powered CPV sectors inflates the familywise error rate. Apply Bonferroni correction: α* = 0.05 / n_testable_sectors, where n_testable_sectors is the count of sectors with ≥ 5 distinct contractors. A sector is identified as monopoly or duopoly only if C1 or C2 exceeds the (1 − α*)th percentile of its null. Additionally report all uncorrected per-sector p-values for transparency.  
**Effect threshold**: C1 excess (observed − null median) ≥ **0.05**; C2 excess ≥ **0.05**. Consistent with the Market Concentration effect floor. Both the Bonferroni-corrected p-value criterion and the effect threshold must be satisfied.

**Graph signal (active — monopoly)**: C1 exceeds the 95th percentile of the null in one or more adequately-powered sectors. A single contractor holds a share of sector value significantly larger than degree sequence alone predicts. Consistent with relational incumbency consolidating to single-firm dominance.

**Graph signal (active — duopoly)**: C2 exceeds the null but C1 does not in one or more sectors. The top-2 contractors collectively dominate but neither holds a monopoly share. Consistent with a two-firm relational equilibrium. Cross-reference H8: if C2 anomaly is present in a sector and H8 confirms rotation, the mechanism is temporal rotation within a two-firm cell.

**Graph signal (absent)**: C1 and C2 are within the null distribution across all adequately-powered sectors. Top-contractor shares are fully explained by degree sequence. No structural monopoly or duopoly beyond what market volume alone produces.

**Real-world meaning**:  
*If confirmed (monopoly or duopoly in one or more sectors):* Identifiable procurement categories are structurally captured by one or two companies. For a business with the qualifications to compete in that sector, the barrier is not just market entry (capital, expertise) but relational incumbency: the dominant company's repeat-award history reinforces its structural position. The specific sectors where this holds are named in the analysis — this is directly actionable for competition policy and procurement oversight targeting.  
*If rejected:* The leading companies in each sector are dominant because they are genuinely large and serve many institutions — not because any specific sector is structurally theirs. Top-contractor shares are fully proportional to their market volume.

**Strongest innocent alternative**: Natural monopoly and specialised supply. Some CPV sectors have genuine barriers to entry — few firms qualify for specialised medical devices or large civil infrastructure. Addressed by the null model: the bipartite configuration model preserves the degree sequence, so a dominant contractor that wins frequently because few alternatives exist is partially absorbed into the null. Residual C1/C2 excess beyond the null is the signal.

---

## Geographic Proximity

**The underlying question**: Does physical proximity between an authority and a contractor predict award allocation beyond what sector specialisation explains?

This domain is currently blocked. No geographic field exists in this dataset (see `docs/DATA_PROFILE.md §10`). Reopening requires an external OIB→county mapping joined to both CA and contractor node sets.

---

### H2 — Authorities systematically favour geographically proximate contractors beyond sector specialisation `blocked`

**In plain terms**: Do public institutions systematically choose nearby companies over equally qualified distant ones — beyond what is explained by shared sector geography?

**Unblocking condition**: External OIB→county mapping joined to both CA and contractor node sets (see `docs/DATA_PROFILE.md §10`). Full specification (test, effect threshold) must be completed before any data examination after unblocking.

**Mechanism**: Contracting authorities prefer vendors in the same county due to reduced monitoring costs, familiarity, and informal networks. This produces positive geographic assortativity in the bipartite graph that exceeds what sector specialisation alone explains.

**Null model**: Sector-conditioned edge permutation. County co-assignment is shuffled within CPV sector; assortativity exceeding the permutation null is the signal.

**Graph signal (active)**: Positive county co-location assortativity that significantly exceeds the sector-conditioned permutation null.

**Graph signal (absent)**: No significant assortativity. Geographic proximity does not predict award allocation after conditioning on sector.

**Real-world meaning**:  
*If confirmed:* Companies located outside an authority's county face a structural disadvantage not explained by sector geography alone. Public money flows locally at rates that exceed what fair, geography-neutral competition would produce. For national market integration and efficiency of public spending, this is evidence that procurement markets remain locally fragmented.  
*If rejected:* Once sector is controlled for, geography adds nothing. Authorities and their contractors co-locate because they operate in the same sector geography, not because of geographic favouritism or informal local networks.

---

### H2a — Geographic favouritism is amplified when competitive requirements are removed `blocked`

**In plain terms**: Does the county-level preference identified in H2 become even stronger in direct awards where competition is not legally required?

**Unblocking condition**: Same as H2, plus resolution of `ProcedureTypeId` label mapping (see `docs/DATA_PROFILE.md §7`). Full specification must be completed before any data examination after unblocking.

**Parent dependency**: H2 must become testable before H2a can be interpreted.

**Mechanism**: Competitive procedures constrain geographic bias through legal requirements; discretionary awards do not. If H2 confirms geographic assortativity, the effect should be amplified in the assumed-discretionary subgraph.

**Null model**: Sector-conditioned edge permutation within each procedure-type subgraph; comparison of assortativity excess between subgraphs.

**Graph signal (active)**: Geographic assortativity excess over the permutation null is significantly larger in the assumed-discretionary subgraph.

**Graph signal (absent)**: No significant difference between subgraphs. Locality bias, if present, does not vary by procedure type.

**Real-world meaning**:  
*If confirmed:* Competitive legal requirements partially constrain geographic favouritism. Removing that constraint amplifies local preference — consistent with discretion enabling informal local network effects that competitive procedures otherwise suppress.  
*If rejected:* Geographic assortativity, if present in H2, does not intensify in direct awards. Geographic preference is not moderated by the competitive requirement — it operates equally across procedure types, suggesting a structural rather than discretion-driven channel.

---

## Temporal Anomalies

**The underlying question**: Does the rate at which new procurement relationships form — and the value flowing through them — follow a calendar pattern that reflects budget pressure rather than procurement need?

Genuine procurement need is distributed across the year in proportion to operational requirements. Budget-driven procurement is concentrated at fiscal year-end, when unspent allocations must be committed or returned. The graph structure changes over time: new edges form, new nodes appear, edge weights grow. The temporal pattern of these changes is the signal.

**Note on execution quality**: `PayedAmount` and `TerminationDate` are each ~59% missing with non-random missingness (see `docs/DATA_PROFILE.md §2`). The available 41% reflects completed, paid contracts — the least informative population for detecting failure. No execution quality branch is included in this domain.

---

### H3 — Contract formation surges at fiscal year-end at rates consistent with budget-pressure spending, not procurement need `resolved-reject`

**In plain terms**: Is a disproportionate share of public contracts signed in the last three months of the year — specifically in domestically-funded contracts where authorities face a use-it-or-lose-it budget deadline — at rates too large to be seasonal coincidence?

**Mechanism**: Public institutions face use-it-or-lose-it budget pressure at the end of the fiscal year. Unspent allocations are returned to the treasury, creating an incentive to commit funds quickly regardless of procurement need. This produces a spike in new contract edges in the final fiscal quarter that is disproportionate to the preceding months and is visible in domestic-funded contracts but not in EU-funded contracts, which have exogenous project-driven deadlines that legitimately concentrate spend.

**Null model**: Stationary Poisson process; the null expectation for any quarter is one-quarter of the annual total. Secondary null: funding-type label permutation, testing whether domestic and EU-funded subgraphs follow the same seasonal process.

**Test**: One-tailed. Run **separately for each of fiscal years 2024 and 2025** (α = 0.05 per year). Both years must independently show a statistically significant Q4 spike for the hypothesis to be supported — a spike in one year only does not support the mechanism, which is systematic budget pressure, not a one-off procurement wave.

*Primary test statistic (Poisson):* Let N_y = total new edges in fiscal year y. Under the stationary null, Q4 count ~ Poisson(N_y / 4). One-tailed p-value: P(X ≥ observed_Q4 | X ~ Poisson(N_y / 4)). Reject if p < 0.05 **and** the observed Q4-to-quarterly-mean ratio (= 4 × observed_Q4 / N_y) exceeds the 1.5× effect threshold. Both conditions must hold; a low p-value below the effect threshold is not sufficient.

*Secondary test (funding-type difference):* Permute `ContractEUFinanc` labels across edges within each fiscal year (funding-type label permutation). For each permutation compute the Q4 spike magnitude in the domestic and EU-funded permuted subgraphs. The null distribution of (spike_domestic − spike_EU) under random label assignment constitutes the comparison baseline. Two-tailed test: reject if observed difference falls outside the 2.5th–97.5th percentile of the permutation distribution (α = 0.05).

**Observation window constraint**: The 2024–2026 dataset covers at most two complete fiscal years (2024 and 2025; 2026 is partial). The per-year requirement makes this a replication check, not a pattern claim. A confirmed spike in both years is consistent with systematic budget pressure but cannot establish a multi-year trend. This constraint must be stated explicitly in any reported result.

**Effect threshold**: Q4-to-quarterly-mean ratio > **1.5** (50% above the flat expectation). Below this ratio, a Q4 excess is statistically detectable but not substantively distinguishable from normal seasonal variation.

**Secondary test — edge type decomposition**: For each contract with `ContractDate` in month M, classify the edge as *new* (no prior contract between this CA and contractor with `ContractDate` < M in the observation window) or *repeat* (the pair has ≥ 1 prior contract before M). Apply the stationary Poisson null independently to the monthly new-edge series and the monthly repeat-edge series within each fiscal year. Report for each of 2024 and 2025: (a) whether Q4 new-edge count exceeds the 1.5× quarterly-mean threshold, (b) whether Q4 repeat-edge count exceeds the threshold, (c) which type dominates the Q4 spike. Repeat-edge dominance is consistent with risk-aversion under budget pressure (rushing to familiar vendors); new-edge dominance is inconsistent with the stated mechanism and requires a separate explanation.

**Graph signal (active)**: Monthly new-edge count and new-edge value show a statistically significant spike in the final fiscal quarter in both 2024 and 2025, each exceeding the 1.5× threshold. The spike is present in domestic-funded contracts and absent or weaker in EU-funded contracts. New contractor nodes also appear at an elevated rate in the spike period — suggesting rushed procurement reaches outside existing relationships.

**Graph signal (absent)**: Monthly edge formation is consistent with a stationary process in either or both years. No quarter deviates significantly from the mean. If a Q4 concentration exists, it is equally present in EU-funded and domestic-funded contracts, consistent with operational scheduling rather than budget pressure.

**Real-world meaning**:  
*If confirmed:* A disproportionate volume of Croatian public contracts is signed in the final quarter of the fiscal year specifically to avoid returning unspent budget to the treasury. This is tax money committed under time pressure rather than deliberate procurement planning. Contracts signed under this pressure are more likely to go to familiar vendors — which, if H4 also confirms, means that the least competitive period of the year also produces the most relationally concentrated awards. For procurement quality, rushed year-end spending is associated with reduced price competition and weaker specification quality.  
*If rejected:* Contract formation is seasonally uniform, or the spike is equally strong in EU-funded contracts — consistent with operational scheduling (project deadlines, seasonal work) rather than fiscal deadline pressure. The procurement calendar is driven by genuine need, not budget mechanics.

**Strongest innocent alternative**: Seasonal demand. Some procurement categories are genuinely seasonal — outdoor construction in summer, heating contracts in autumn. This alternative is addressed by testing within CPV sector and by focusing on domestic non-infrastructure categories where seasonality has the weakest a priori justification.

---

## Relational Persistence

**The underlying question**: Does a prior CA–contractor relationship independently predict future award allocation, beyond what each party's market volume explains?

Market Concentration tests structure at a point in time. Relational persistence is a temporal property: a pair that connected in one year reconnects in the next at above-chance rates, where "chance" is calibrated to the pair's individual market positions (their degree in the subsequent year). An authority may have high single-vendor concentration for structural reasons — niche sector, few qualified vendors — without relational memory. Relational persistence tests whether the past relationship itself adds predictive power beyond market position.

---

### H4 — Prior CA–contractor relationships independently predict future award allocation beyond market volume `resolved-confirm`

**In plain terms**: When controlling for how active each party is in the market, are institutions and contractors that worked together last year significantly more likely to work together this year than equally active pairs who have not previously contracted?

**Stated**: 2026-05-23. Stated before any examination of temporal reconnection rates in the data.

**Mechanism**: A prior contract encodes institutional familiarity, delivery record, and reduced transaction costs on both sides. These advantages are embedded in the relationship, not in either party's market position. Controlling for each node's degree in the subsequent year — which captures market volume — a pair with a prior relationship should reconnect at a higher rate than a pair of the same market size that did not previously connect. This is relational memory: the past award is itself a factor in the next, not merely correlated through shared market volume.

**Null model**: Bipartite configuration model applied to the 2025 annual subgraph. For each CA–contractor pair (CA_i, Contractor_j) that appeared in the 2024 annual subgraph, compute the expected reconnection probability under the bipartite Chung-Lu approximation: p_ij = (d_i · d_j) / |E_2025|, where d_i and d_j are the 2025 degrees of CA_i and Contractor_j and |E_2025| is the 2025 edge count. The denominator is |E_2025|, not 2|E_2025| — in a bipartite graph the sum of CA degrees equals |E| (not 2|E| as in unipartite graphs), so the bipartite normalisation is m, not 2m. This ensures the expected degree equals the observed degree: Σ_j p_ij = d_i. Sum these to get the expected reconnection count across all eligible pairs.

**Scope restriction**: Restrict to pairs where both the CA and the contractor have ≥ 1 contract in each of 2024 and 2025 (active in both years). Pairs where either node is absent in 2025 cannot reconnect and must not inflate the denominator. Exclude pairs where the 2025 contract is a re-publication of the 2024 contract — same `Id` after deduplication, or same `ContractNo` with `ContractDate` within 30 days of the 2024 contract. The test must count distinct procurement decisions, not the same contract appearing in both annual windows.

**Graph construction**: Bipartite multigraph; assign contracts to annual subgraphs by `ContractDate` year. Apply data preparation canon. Sensitivity check required: re-run including `IsUponFA = true` contracts.

**Test**: One-tailed. Compute the observed reconnection count (number of eligible 2024 pairs that also appear in 2025). Compare to the expected count from the Chung-Lu approximation. Compute z-score: z = (observed − expected) / √(Σ_ij p_ij(1 − p_ij)). Reject if z > 1.645 (α = 0.05). Report the excess reconnection rate: (observed count / total eligible 2024 pairs) − (expected count / total eligible 2024 pairs).  
**Effect threshold**: Excess reconnection rate ≥ **10 percentage points**. Below this, the effect may be statistically detectable but the substantive claim — that past relationships predict future awards above market volume — is too weak to support a finding.

**Graph signal (active)**: Observed reconnection rate significantly exceeds the degree-sequence expectation. CA–contractor pairs with a prior 2024 relationship reconnect in 2025 at a rate above what their individual 2025 market positions predict. The excess holds within CPV sector, ruling out the explanation that within-sector pairs reconnect simply because they share the same narrow market.

**Graph signal (absent)**: Reconnection rate is consistent with the degree-sequence null. Which specific pairs reconnect in 2025 is fully determined by their market positions — high-degree CAs and high-degree contractors reconnect more because of volume, not because of the prior relationship itself.

**Real-world meaning**:  
*If confirmed:* A past contract is a structural asset for a vendor — it predicts future contracts with the same authority beyond what either party's market activity alone explains. For a new company entering the market with equivalent qualifications, this means the first contract with an institution is structurally harder to win than subsequent contracts: incumbency is self-reinforcing. For oversight bodies, past contract history is a predictor of future award patterns that operates independently of competitive merit — and compounds over time.  
*If rejected:* Which pairs reconnect is fully explained by each party's market activity. High-volume authorities and high-volume contractors work together repeatedly because they are both active in the same market — not because the prior relationship itself is an advantage. The system is consistent with relationship-agnostic market competition.

**Strongest innocent alternative**: Multi-year contracts. A single contract spanning 2024 and 2025 generates records in both annual subgraphs, appearing as a "reconnection" without a new procurement decision. Addressed by the scope restriction: exclude pairs where the 2025 contract is the same `ContractNo` as the 2024 contract, or where `ContractDate` values are within 30 days of each other for the same pair.

---

### H4a — Contracts with established vendors are amended to higher values more than first-contract pairs of equivalent market size `resolved-confirm`

*Branch of H4. Tests whether prior CA–contractor relationships predict not just the probability of reconnection (H4) but the magnitude of value inflation after award.*

**In plain terms**: After controlling for contract size and type, do contracts between an authority and a familiar vendor end up costing more than the original award — through post-award amendments — at higher rates than contracts with first-time vendors?

**Stated**: 2026-05-23. Stated before any examination of per-pair amendment inflation ratios in the data.

**Parent dependency**: H4 can run independently; H4a does not require H4 to confirm. If H4 confirms relational persistence, H4a tests whether established relationships also enable value extraction after award — strengthening the incumbency mechanism. If H4 rejects, H4a tests a distinct value-extraction channel that does not require reconnection as its entry point.

**Mechanism**: A prior CA–contractor relationship reduces the authority's willingness to challenge post-award price changes. The incumbent's delivery record makes re-tendering costly; the authority absorbs upward amendments it would resist from an unknown vendor. If incumbency enables value extraction, the mean `TotalValue / InitialValue` ratio — the post-award amendment inflation ratio — should be higher for contracts in established pairs (CA–contractor pairs with ≥ 1 prior contract by `ContractDate`) than for first-contract pairs of equivalent market size.

**Data constraint**: Amendments are rare in this dataset — mean `TotalValue` ≈ mean `InitialValue` (see `docs/DATA_PROFILE.md §4`). The signal, if present, is concentrated in a small fraction of contracts. The effect threshold is set accordingly.

**Null model**: Bipartite configuration model. In each null instance, degree-preserving rewiring determines which pairs have prior relationships by construction — a pair that connects multiple times in the null has "prior relationship" status. Compute the mean amendment inflation ratio for null prior-relationship edges vs. null first-contract edges. The null distribution of the excess (prior-relationship mean − first-contract mean) constitutes the test baseline. Degree-sequence control is non-negotiable: high-degree contractors are over-represented in prior-relationship pairs by volume alone, not by incumbency.

**Graph construction**: Bipartite multigraph. Apply data preparation canon. Restrict to contracts where both `TotalValue` and `InitialValue` are present and `InitialValue > 0`. Test on all contracts including unamended ones (ratio = 1.0) — restricting to amended contracts only selects on the dependent variable and weakens the claim. Apply `ContractTypeId` split; compute results within contract value quartile.

**Test**: One-tailed. Compute observed excess mean amendment ratio: mean(TotalValue/InitialValue) for prior-relationship contracts − mean(TotalValue/InitialValue) for first-contract pairs. Compare to the null distribution of the same excess. Reject if observed excess exceeds the 95th percentile of the null (α = 0.05). Run within `ContractTypeId` and within contract value quartile.  
**Effect threshold**: Excess mean amendment ratio ≥ **0.05** (5 percentage points — prior-relationship contracts on average 5% more inflated than first-contract pairs of equivalent degree).

**Graph signal (active)**: Contracts in established CA–contractor pairs show significantly higher post-award value inflation than first-contract pairs of equivalent degree. The excess holds within contract value quartile, ruling out contract size as the driver. Consistent with incumbency enabling value extraction — the prior relationship reduces scrutiny of price amendments.

**Graph signal (absent)**: Amendment inflation ratio is consistent with the degree-sequence null. Established pairs are not more inflated than random pairs of equivalent market size. Post-award prices reflect contract complexity and sector norms rather than incumbency.

**Real-world meaning**:  
*If confirmed:* The advertised award value systematically understates the final cost in established vendor relationships. The true cost of procuring from a familiar vendor is higher than the initial contract suggests — and this gap is larger than for comparable first-time contracts. For budget planning, this means that relational concentration (found in H1 and H4) has a compounding cost: established vendors are chosen more often and cost more than awarded. For procurement audit, contracts in established pairs are a higher-priority review target for post-award price justification.  
*If rejected:* Amendment inflation is the same regardless of relationship history. Price changes reflect contract complexity, scope evolution, and sector norms — not incumbency. Authorities scrutinise amendments equally whether the vendor is familiar or new.

**Strongest innocent alternative**: Large contracts are amended for legitimate scope changes — construction cost overruns, service extensions, material price escalations. These are more common in prior-relationship pairs because established pairs handle larger, longer-running contracts, not because incumbency reduces scrutiny. Addressed by running the test within contract value quartile: if amendment inflation excess disappears when comparing established vs. first-contract pairs within the same value quartile, the mechanism is contract size, not incumbency.

---

## Structural Position

**The underlying question**: Does where a contractor sits in the network — rather than just how large it is — predict procurement outcomes?

Market Concentration and relational persistence capture size and history. Structural position is a third property: the topology of a node's neighbourhood in the whole graph independently affects outcomes. Two contractors with identical total value and identical prior-relationship history may occupy structurally different positions — one bridging disconnected institutional clusters, the other embedded in a tight clique. These positions are invisible from any per-node statistic and require the full graph.

---

### H12 — The highest-value contractors share client bases with each other at above-chance rates `resolved-reject`

**In plain terms**: Do the top procurement companies all compete for (and win from) the same pool of government clients — forming a tight structural "club" at the top — or does each dominate a separate corner of the market?

**Stated**: 2026-05-29. Stated before any examination of pairwise Jaccard similarity among high-value contractors.

**Mechanism**: High-budget contracting authorities generate the largest and most attractive contracts. In a stratified market, the top contractors are pulled toward the same institutional clients regardless of sector, because the incentive to win large contracts dominates sector specialisation. This produces a rich-club structure in the contractor layer: high-value contractors share more CA clients with each other than lower-value contractors do with each other, above what the weighted degree sequence alone predicts. H1 establishes that top contractors receive a large share of total value; H12 tests whether those top contractors are competing for the *same* pool of institutions or separate ones.

**Operationalisation**:
- *Rich club set*: top 1% of contractors by total strength (~440 nodes). Threshold set before data examination; not adjusted based on results.
- *Pairwise Jaccard similarity between contractors i and j*: |CAs(i) ∩ CAs(j)| / |CAs(i) ∪ CAs(j)|, where CAs(x) is the set of distinct CA OIBs contractor x has an edge to in the observation window.
- *Primary metric*: mean pairwise Jaccard similarity among all pairs within the rich club set.

**Null model**: Bipartite configuration model (weighted variant: degree-preserving rewiring preserving edge count per node; edge weights reassigned proportionally). In each rewired instance, compute mean pairwise Jaccard among the same contractor nodes, identified by their observed strength rank which is preserved under the weighted null. The null distribution of mean Jaccard constitutes the baseline.

**Graph construction**: Bipartite simple graph (collapse multigraph: CA–contractor edge exists if ≥ 1 contract between them in the observation window). IsUponFA = false.

**Test**: One-tailed. The observed mean pairwise Jaccard among the top-1% contractors is compared to the null ensemble 95th percentile (α = 0.05).  
**Effect threshold**: Excess mean Jaccard (observed − null median) ≥ **0.05**. Below this, top-contractor client overlap is attributable to shared market volume, not structural club formation.

**Secondary check**: Compute mean pairwise Jaccard at additional thresholds (top-5%, top-10%, top-25%) and compare each to its null. If excess is present at top-1% and diminishes monotonically at lower thresholds, the club is tight and limited to the apex. If it holds broadly, stratification is market-wide.

**Graph signal (active)**: Mean pairwise Jaccard among top-1% contractors significantly exceeds the null. The highest-value contractors share institutional clients with each other at rates above what their market volume alone predicts. The procurement market is structurally stratified: a small elite tier competes for the same pool of high-budget institutions, forming a club within the contractor layer.

**Graph signal (absent)**: Top-contractor client overlap is consistent with the null. High-value contractors each dominate separate, non-overlapping client clusters — concentration is driven by sector specialisation or segmentation, not by convergence on shared institutional clients.

**Real-world meaning**:  
*If confirmed:* The top tier of Croatian contractors forms a structural club — they compete for the same clients and win. For a large, well-qualified company trying to enter the top tier, the barrier is not just winning a first contract (H4) but breaking into a pool of clients already shared among incumbents. The club reinforces itself: being in it means competing for the same high-value CAs, which generates the revenue that keeps the contractor in the top tier. For competition policy, this stratification is a distinct form of market closure not visible from concentration statistics alone.  
*If rejected:* Top contractors dominate separate market corners. Concentration reflects specialised market dominance rather than convergence on the same clients. A specialist company can grow to the top tier in its own niche without confronting the entire incumbent group.

**Strongest innocent alternative**: Top contractors appear to share clients because they operate in the same CPV sectors, and those sectors' CAs naturally overlap. Addressed by the null model: the degree-preserving rewiring absorbs the fact that top contractors are large and serve many clients each. Residual excess Jaccard above the null is the signal that cannot be explained by size alone.


---

### H13 — Contractors that bridge disconnected institutional clusters extract higher amended contract values `resolved-reject`

*Branch of Structural Position. Tests whether structural position — bridging otherwise-disconnected CA clusters — predicts value extraction above what market size alone explains.*

**In plain terms**: Are there specific companies that act as bridges between groups of government agencies that otherwise share no vendor in common — and do those bridge companies end up getting more money (through post-award amendments) than equally large companies embedded in a single tight cluster?

**Stated**: 2026-05-29. Stated before any examination of betweenness centrality or amendment ratios by structural position.

**Mechanism**: A contractor that bridges otherwise disconnected CA clusters occupies a structural hole: it sees procurement needs across institutional worlds that have no other common vendor. This position confers information advantage (access to procurement signals from multiple non-overlapping client groups) and negotiating leverage (the broker is harder to substitute, because no alternative vendor has the same cross-cluster reach). If structural position drives value extraction, contractors with high bipartite betweenness centrality should show higher mean amendment inflation ratios than contractors of equivalent degree with low betweenness — after controlling for degree sequence.

**Null model**: Bipartite configuration model (degree-preserving rewiring). In each rewired instance, recompute bipartite betweenness centrality for all eligible contractor nodes. The null distribution of the Spearman correlation (betweenness rank → mean amendment inflation ratio) constitutes the baseline. Degree sequence is preserved in the null, so any correlation above the null cannot be explained by a contractor simply being large.

**Graph construction**: Bipartite simple graph (collapse multigraph; edge weight = sum TotalValue; betweenness computed on the unweighted binary graph). IsUponFA = false; analysis window only. Restrict to contractors with ≥ 5 contracts and with at least one record where InitialValue > 0.

**Computational note (binding)**: Bipartite betweenness on ~4,000 CAs and ~20,000+ eligible contractors is O(V · E). Use 100 null iterations (not 500); state this in the script output header. If single-core runtime exceeds 30 minutes, restrict to contractors with degree ≥ 10 and note the restriction.

**Test**: One-tailed. Compute Spearman rank correlation between contractor bipartite betweenness centrality and mean (TotalValue / InitialValue) amendment inflation ratio across all eligible contractors. Compare to null ensemble. Reject if observed correlation exceeds the 95th percentile of the null (α = 0.05). Run additionally within contract value quartile.  
**Effect threshold**: Excess Spearman correlation (observed − null median) ≥ **0.10**. Below this, the betweenness–amendment relationship is statistically detectable but too weak for a substantive claim of positional value extraction.

**Graph signal (active)**: Spearman correlation between bipartite betweenness and amendment inflation ratio significantly exceeds the null. Contractors that bridge disconnected CA clusters receive higher final contract values relative to initial award than contractors of equivalent degree embedded in tight, redundant client clusters. Consistent with structural position enabling value extraction.

**Graph signal (absent)**: Betweenness–amendment correlation is consistent with the null. Amendment inflation is driven by contract complexity and sector norms, not by the contractor's structural position. Being a broker adds nothing to a contractor's value extraction above what degree alone predicts.

**Real-world meaning**:  
*If confirmed:* Network position is a source of pricing power. A contractor that bridges institutional clusters extracts more value from contracts through post-award amendments. This is invisible from any per-contractor statistic; it requires the full graph to detect. For procurement auditors, contractors with high betweenness and high amendment ratios are a structurally prioritised audit target: they have both the positional leverage and the observed outcome.  
*If rejected:* Amendment inflation does not depend on structural position. High-betweenness contractors also happen to handle more complex procurement, and complexity drives amendments — not leverage. Structural position adds nothing beyond market size.

**Strongest innocent alternative**: High-betweenness contractors handle structurally complex procurement — large, long-duration, multi-sector contracts — that legitimately requires post-award amendments for scope changes or cost overruns. Addressed by running the test within contract value quartile: if the betweenness–amendment correlation disappears within the same value quartile, contract complexity explains the pattern. If it persists within quartile, structural position adds explanatory power beyond contract size.


---

## Sector Fit vs. Relational Override

**The underlying question**: Does CPV sector alignment between a contractor's primary specialisation and the contract's CPV code predict award outcomes, or do established relationships override sector fit?

In a market-structured system, authorities select contractors who specialise in the relevant CPV sector. In a relationship-structured system, familiar contractors win contracts outside their primary sector because institutional trust overrides sector matching. The fraction of contracts where the winning contractor's primary CPV division matches the contract's CPV division — relative to what the degree sequence alone predicts — measures which force dominates. This question is distinct from aggregate concentration (H1): a contractor can be highly concentrated while still winning within its primary sector, or can win across sectors without being concentrated overall.

---

### H6 — Contractor–contract sector alignment deviates from degree-sequence expectation: either specialisation dominates, or relationships override it `resolved-confirm`

**In plain terms**: Do contractors consistently win contracts in their area of expertise (suggesting the market selects on competence), or do familiar vendors regularly win contracts outside their primary sector (suggesting relationships override sector fit)?

**Stated**: 2026-05-23. Stated before any examination of CPV match rates in the data.

**Mechanism**: Market-driven procurement produces CPV homophily — authorities match contractors to contracts by sector expertise, so the winning contractor's primary sector aligns with the contract's CPV division at rates above what random contractor assignment (given degrees) would predict. Relationship-driven procurement suppresses homophily: a familiar contractor wins contracts outside its primary sector because the authority's trust overrides sector matching. If observed CPV homophily significantly exceeds the null, sector specialisation is a genuine discriminating factor in selection. If at or below the null, relational access dominates sector fit — incumbency extends across sector lines.

**Operationalisation**:
- *Primary CPV division of a contractor*: the 2-digit CPV prefix (first two characters of the 8-digit numeric code; ) appearing in the plurality of that contractor's contracts by count. Ties broken by total `TotalValue`. Computed once across the full post-cleaning dataset.
- *CPV division of a contract*: the 2-digit prefix of that contract's `Cpv` field.
- *CPV-matched edge*: a contract where the contractor's primary CPV division equals the contract's CPV division.

**Null model**: Bipartite configuration model. In each null instance (degree-preserving rewiring), assign to each rewired edge the same CPV code as the original contract on that edge — CPV belongs to the contract, not the contractor. For each null instance, compute the fraction of edges that are CPV-matched. This produces the null distribution of the CPV match fraction under random contractor assignment, preserving the CPV composition of each CA's procurement portfolio and each contractor's degree.

**Graph construction**: Bipartite multigraph. Apply data preparation canon. Restrict to domestic contractors (non-numeric OIBs excluded) and to contractors with ≥ 3 contracts in the observation window — below this threshold the modal CPV division is unstable (see `docs/DATA_PROFILE.md §10`).

**Test**: Two-tailed. No strong prior on whether market-matching (high homophily) or relational override (low homophily) dominates; both are informative and in opposite directions. Reject if the observed CPV match fraction falls outside the 2.5th–97.5th percentile of the null ensemble (α = 0.05). Report the direction explicitly.  
**Effect threshold**: |observed match fraction − null median| ≥ **5 percentage points**.

**Stability check**: Re-run restricted to contractors with ≥ 70% of their contracts in a single CPV division (high-specialisation subset). If the effect holds in this subset, it is not driven by label noise from multi-sector contractors.

**Graph signal (above null — market structured)**: Contractors win contracts in their primary CPV division at rates significantly higher than random contractor assignment predicts. Sector specialisation is a genuine discriminating factor in vendor selection.

**Graph signal (below null — relational override)**: Contractors win contracts outside their primary CPV division more than the null expects. Authorities award familiar vendors across sector boundaries — relational access is a stronger selection criterion than sector fit.

**Graph signal (consistent with null)**: CPV match fraction is fully explained by contractor and CA degree sequences. Neither systematic market-matching nor relational override is detectable at the structural level.

**Real-world meaning**:  
*If above null (sector fit dominates):* The Croatian procurement market selects on competence: contractors tend to win contracts in the sector where they specialise. A specialist company competing on merit has a structural advantage over a generalist. This is the expected outcome in a well-functioning competitive market.  
*If below null (relational override dominates):* Familiar vendors win contracts outside their primary area of expertise more than random assignment would predict. An authority's trust in a vendor extends across sector lines — sector specialisation is a weaker selection criterion than the vendor's relational position. For a competent specialist entering a category already held by a relationally embedded generalist, this is a structural barrier not reducible to capability.  
*If consistent with null:* Neither market specialisation nor relational override is detectable. The match rate is fully explained by market volumes — no systematic pattern in either direction.

**Strongest innocent alternative**: Large multi-sector contractors legitimately operate across many CPV divisions; their primary CPV label marks them as "mismatched" even when competent across sectors. Addressed by the stability check restricted to high-specialisation contractors (≥ 70% of contracts in one division) and by separately reporting results for contractors with degree ≤ median.

---

## Temporal Coordination

**The underlying question**: Does the temporal sequence of contractor awards within CA–CPV cells show a rotation pattern — contractors taking turns — that exceeds what random independent assignment would produce?

Concentration and market segmentation are structural properties measured at a point in time. Temporal coordination is a dynamic property: the same small set of contractors wins in succession within a CA–CPV cell, with no single contractor dominating continuously. This pattern is structurally distinct from lock-in (H1a). A market where both segmentation and rotation are present shows the strongest form of the coordination signal: the segmentation is not static monopoly but sustained through turn-taking.

---

### H8 — Within specific authority–sector combinations, the same small set of contractors takes turns winning contracts `resolved-reject`

**In plain terms**: Within a specific institution and procurement category, do a fixed small number of companies alternate winning successive contracts — each taking a turn — at rates that cannot be explained by their individual market shares under independent selection?

**Stated**: 2026-05-23. Stated before any examination of contractor award sequences in the data.

**Mechanism**: In a coordinated market, a fixed set of contractors divides contracts over time within specific CA–CPV cells by taking turns winning. Each contractor wins, then yields to another, then returns — producing a temporal alternation pattern that exceeds what independent draws from the observed market shares would generate. The coordination need not be explicit: stable relational networks and repeated informal negotiation produce the same structural signal. This is temporally complementary to H7: H7 detects that the market is structurally segmented at a point in time; H8 tests whether that segmentation sustains itself through temporal rotation rather than permanent monopoly.

**Null model**: Within-cell sequence permutation. For each eligible CA–CPV cell, shuffle the contractor label sequence (holding contractor counts fixed) 1,000 times. The alternation rate A = (consecutive pairs with different contractors) / (total consecutive pairs) is computed for each permutation.

**Graph construction**: Bipartite multigraph. Apply data preparation canon. Restrict to CA–CPV 2-digit cells with ≥ **5 contracts** and ≥ **2 distinct contractors** — cells with fewer contracts cannot produce reliable permutation null distributions, and single-contractor cells have trivially zero alternation. Sort contracts within each cell by `ContractDate`.

**Test**: One-tailed.  
*Cell-level*: A cell shows significant rotation if its observed A exceeds the 95th percentile of its within-cell permutation null (α = 0.05 per cell).  
*Market-level (primary)*: The observed fraction of eligible cells showing significant rotation is compared to the global null fraction of 5% (false-positive rate under independent draws). Reject if the observed fraction exceeds the 95th percentile of Binomial(n_cells, 0.05) (α = 0.05).  
**Effect threshold**: Observed fraction of cells with significant rotation ≥ **15%** (≥ 10 percentage points above the 5% baseline). Below this, rotation is too sparse to constitute a market-level structural claim.  
**Secondary metric**: Mean excess alternation rate Ā_excess = mean(A_obs − median(A_perm)) across all eligible cells. Report alongside the fraction test.

**Secondary test — procedure type decomposition**: Apply the fraction test independently to the assumed-discretionary (ProcedureTypeId = 11) and assumed-competitive (ProcedureTypeId = 1) subsets.  
**Classification caveat (binding)**: same as H1b — ID 11 = discretionary and ID 1 = competitive are working assumptions, not verified facts. All results conditional on this classification; report as "consistent with higher rotation in what is assumed to be discretionary procurement."

**Graph signal (active)**: ≥ 15% of eligible CA–CPV cells show contractor award sequences more alternating than the within-cell permutation null predicts. The effect is more pronounced in assumed-discretionary cells, consistent with temporal coordination being more valuable where competitive pressure is absent.

**Graph signal (absent)**: The fraction of cells with significant rotation is consistent with the 5% false-positive rate. Contractor sequences within cells are fully explained by independent draws from observed market shares. No evidence of temporal coordination beyond random assignment.

**Real-world meaning**:  
*If confirmed:* A structural rotation pattern exists in identifiable institution–sector combinations: the same small group of companies cycles through winning contracts in sequence, systematically excluding others. The temporal outcome looks fair (no single company wins every contract) while the structural outcome is exclusive (only the rotating group wins). For a company outside the rotation, the pattern is structurally invisible from any single tender but detectable in the sequence. The specific institution-sector cells with the strongest rotation are named in the analysis. Note: deliberate fairness rotation (authorities consciously cycling to avoid single-source dependency) produces the same graph signal — the two mechanisms are structurally indistinguishable from outcome data alone. The procedure-type decomposition provides a partial handle: rotation concentrated in assumed-discretionary awards is more consistent with coordination than with deliberate fairness, which would also appear under competitive procedures.  
*If rejected:* Contractor sequences within cells are random given market shares. The same companies win repeatedly because they are the most active in that cell — not because of any turn-taking behaviour, coordinated or otherwise.

**Strongest innocent alternative**: Deliberate fairness rotation — authorities consciously cycle through qualified vendors to avoid single-source dependency. This produces an identical graph signal to cartel-like coordination: above-expectation alternation within CA–CPV cells. The two mechanisms are structurally indistinguishable from outcome data alone. The secondary test on assumed procedure type provides a partial handle: if rotation excess is significantly higher in assumed-discretionary awards than in assumed-competitive awards, the coordination mechanism is more plausible than the fairness mechanism (authorities subject to competitive obligation have less motive for deliberate fairness rotation). This distinction is partial and must be stated explicitly in any reported result.

---

## Value Threshold Evasion

**The underlying question**: Does the value distribution of contracts, and the timing of contracts within CA–contractor pairs, show evidence of deliberate structuring to remain below legal procurement thresholds?

Croatian procurement law (ZJN 2016) requires competitive procedures above specific contract value thresholds. Below those thresholds, authorities may award directly without competition. If authorities split what would be a single large procurement into multiple smaller contracts — each below the threshold — to avoid the competitive requirement, this produces temporal clusters of below-threshold contracts within CA–contractor pairs whose aggregate value exceeds the threshold. The cluster rate should exceed what random contract timing would produce for the same pairs.

This domain extends the project's graph-native scope narrowly into value anomaly detection: contract splitting is expressed as a multi-edge temporal cluster property of the bipartite graph. Pure threshold clustering (univariate value distribution analysis) is not a graph hypothesis and is reported separately as an exploratory note.

---

### H9 — Authorities cluster below-threshold contracts with the same vendor within short time windows at rates consistent with deliberate threshold evasion `resolved-reject`

**In plain terms**: Do public institutions sign multiple small contracts with the same company in quick succession — where each contract is individually below the legal threshold requiring open competition, but their combined total exceeds it — at rates that exceed what random contract timing would produce?

**Stated**: 2026-05-23. Stated before any examination of contract value clustering patterns in the data.

**Mechanism**: An authority that wishes to award a large contract to a preferred vendor without triggering open competition splits the procurement into multiple smaller contracts, each below the legal threshold T. This produces a temporal cluster of below-threshold contracts within the CA–contractor pair whose aggregate value exceeds T. The cluster rate should exceed what random contract timing would produce for the same pair.

**Threshold values (primary)**: From Croatian ZJN 2016:
- T_goods_services = **€26,540** for `ContractTypeId` ∈ {1 (supplies), 2 (services)}
- T_works = **€66,360** for `ContractTypeId` = 3 (works)

**Robustness check**: Empirically detected threshold from a McCrary-style density discontinuity test on the `TotalValue` distribution, run as a preliminary analysis. The detected value must be stated before the main test runs — not derived from the same test population.

**Null model**: Within-pair temporal permutation — temporal application of the within-cell sequence permutation. For each CA–contractor pair, shuffle `ContractDate` values across that pair's contracts while preserving edge count and values. Recompute how often k ≥ 2 contracts with individual values below T fall within any 90-day rolling window in the permuted sequence. Generate 1,000 permutations per pair.

**Graph construction**: Bipartite multigraph. Apply data preparation canon. Restrict to CA–contractor pairs with ≥ 2 contracts in the observation window. Apply T split by `ContractTypeId`.

**Test**: One-tailed. Time window: **90-day rolling**. Minimum cluster: **k ≥ 2** contracts within the window with individual `TotalValue` < T and aggregate cluster value ≥ T.  
*Pair-level*: A pair shows significant temporal splitting if the observed cluster count exceeds the 95th percentile of its within-pair temporal permutation null (α = 0.05 per pair).  
*Market-level (primary)*: The observed fraction of eligible pairs showing significant temporal clustering is compared to the global null fraction of 5%. Reject if the observed fraction exceeds the 95th percentile of Binomial(n_pairs, 0.05) (α = 0.05).  
**Effect threshold**: Excess fraction of pairs with significant clustering ≥ **10 percentage points** above the 5% baseline.

**Graph signal (active)**: A significant fraction of CA–contractor pairs produce temporal clusters of below-threshold contracts whose aggregate value exceeds T, at a rate exceeding random timing. Clusters concentrate in assumed-discretionary (ProcedureTypeId = 11) pairs. Cross-reference H3: if Q4 fiscal year-end spike (H3) is confirmed, test whether splitting clusters also concentrate in Q4 — consistent with budget-pressure and threshold-evasion mechanisms compounding at year-end.

**Graph signal (absent)**: Temporal clustering of below-threshold contracts is consistent with random contract timing. No evidence of deliberate value structuring beyond what the pair's contract frequency and value distribution would produce under random ordering.

**Real-world meaning**:  
*If confirmed:* A significant share of authority–vendor pairs produce temporal clusters of individually-small contracts whose combined value exceeds the legal threshold that would require open competition. This is the structural signature of procurement splitting: a large purchase formally compliant on each individual contract, but structurally equivalent to a single above-threshold direct award. For the taxpayer, this means a portion of public spending is shielded from competition in ways that no individual contract reveals. For procurement auditors, the specific authority–vendor pairs with the highest cluster rates are identifiable from the analysis — a direct prioritisation input for audit targeting. Cross-referencing with H3: if year-end budget pressure (H3) is also confirmed, the Q4 concentration of splitting clusters indicates that deadline pressure and threshold evasion compound at the same time of year.  
*If rejected:* Temporal clustering of below-threshold contracts is consistent with normal procurement patterns. Small, frequent contracts between the same authority and vendor are legitimately recurring procurement — consumables, maintenance services, regular supplies — rather than disguised single large procurements. The aggregate value crossing the threshold is coincidental, not structural.

**Strongest innocent alternative**: Recurring small procurements. Some CA–contractor pairs legitimately have many small repeat contracts — a hospital buying medical supplies monthly, a school buying office materials quarterly. Addressed by requiring aggregate cluster value ≥ T: recurring small procurement where no cluster sum exceeds the threshold is excluded by definition. The signal is specifically CA–contractor pairs where the cluster aggregate crosses the threshold — the structural signature of splitting, not recurrence.

---

## Network Resilience

**The underlying question**: Is the procurement market structurally fragile — are there a small number of contractors whose removal would leave many public institutions without any vendor relationship?

H1 establishes that a few contractors hold large value shares. Resilience asks the complementary question: does that concentration also mean those contractors are irreplaceable? A concentrated market may still be resilient if high-value contractors serve CAs that have many alternative vendors. It is fragile if high-value contractors are the exclusive vendor for many CAs. The network structure — not the value share — determines fragility.

---

### H10 — Removing the highest-value contractors strands significantly more public institutions than random removal `resolved-reject`

**In plain terms**: If the largest procurement companies suddenly became unavailable — due to insolvency, debarment, or any other reason — would a disproportionate number of government agencies be left with no vendor at all? Or is the market robust enough that agencies always have alternatives?

**Stated**: 2026-05-29. Stated before any examination of CA isolation rates under simulated contractor removal.

**Mechanism**: In a relationship-captured market, high-value contractors serve as exclusive vendors to many CAs — institutions that have no other contractor relationships in the observation window. Targeted removal of the largest contractors by value therefore strands these CAs immediately. In a market-structured system, high-value contractors serve CAs that also maintain relationships with many other contractors, so removing any single contractor leaves most CAs with residual coverage. The difference between targeted and random removal — excess isolation under value-ordered attack — is the structural signal of exclusivity at the top of the market.

**Null model**: Random contractor removal curve — 1,000 permutations of the removal sequence, each ordering contractors randomly rather than by value. After each removal step k, record the count of isolated CAs (CAs with no remaining contractor edge). The distribution of isolated CA counts at each k constitutes the null.

**Graph construction**: Bipartite simple graph (collapse multigraph: CA–contractor edge present if ≥ 1 contract in the observation window). IsUponFA = false. Sensitivity check: rerun including IsUponFA = true contracts.

**Test**: One-tailed. Primary k = 10 (the top 10 contractors by total value, < 0.1% of all contractors). Compare observed isolated CA count at k = 10 to the 95th percentile of the random removal null at k = 10 (α = 0.05).  
**Effect threshold**: Excess isolated CA count (observed − null median) at k = 10 ≥ **5% of all CAs** (≥ 207 CAs). Below this, targeted fragility is statistically significant but not operationally meaningful.

**Secondary analysis**: Plot the full isolation curve — isolated CAs vs. k removed — for both targeted removal and the random removal null (median and 95th pct). Report the k at which 10% of CAs become isolated under targeted vs. random removal. The gap between these two k values quantifies how much faster targeted removal strands institutions.

**Graph signal (active)**: Removing the top 10 contractors by value isolates significantly more CAs than removing 10 random contractors. The isolation curve rises sharply under targeted attack relative to the random null. Consistent with high-value contractors serving as exclusive, non-substitutable vendors for specific institutional clusters.

**Graph signal (absent)**: Targeted removal produces no more CA isolation than random removal. High-value contractors serve CAs that maintain many alternative vendor relationships — concentration of value is not accompanied by exclusivity of access.

**Real-world meaning**:  
*If confirmed:* A small number of procurement companies are systemically critical not because of their market share, but because many public institutions have no alternative vendor if they disappear. This procurement continuity risk is invisible from any single contract or per-contractor value share. The specific contractors and the specific CAs they would strand are identifiable from the analysis — directly actionable for vendor diversification policy.  
*If rejected:* Despite concentration (H1), the market is structurally resilient. High-value contractors are concentrated in value but not in access: the CAs that use them also maintain other vendor relationships. Removing any single contractor does not cascade into institutional procurement paralysis.

**Strongest innocent alternative**: Many CAs appear to have only one contractor in the observation window because the window is short (2024–2026) and they procure infrequently. Their "isolation" under removal reflects data sparsity, not genuine dependency. Addressed by the comparison to the random removal null: under random removal the same sparse CAs isolate at a proportional rate; excess isolation under targeted removal above the random null controls for window-length sparsity.


---

## Institutional Convergence

**The underlying question**: Do public institutions that operate in the same procurement domain independently converge on the same vendor choices — beyond what their shared market environment alone would produce?

Market Concentration and relational persistence are contractor-side properties. Institutional convergence is a CA-side property: do agencies in the same domain share vendor portfolios at rates that exceed what shared market structure predicts? If they do, the mechanism is institutional rather than competitive: agencies conform to peer practice, or informal inter-agency networks channel them toward the same suppliers.

---

### H11 — Public institutions in the same procurement domain share vendor portfolios at above-chance rates `resolved-reject`

**In plain terms**: Do hospitals that procure similar things end up using the same companies? Do municipalities? And is the overlap greater than you'd expect just from them all fishing in the same limited market?

**Stated**: 2026-05-29. Stated before any examination of pairwise CA Jaccard similarity in the data.

**Mechanism**: Contracting authorities face accountability risk when selecting vendors. One risk-reduction strategy is to choose vendors already used by peer institutions — the choice is defensible because it is corroborated. This produces within-group portfolio similarity (CAs in the same domain share more vendors than random pairs of equivalent market activity). The mechanism is institutional isomorphism: conformity to peer practice. Excess within-group Jaccard similarity above the degree-sequence null is the structural signal.

**Operationalisation**:
- *CA group label*: modal CPV 2-digit division across all of that CA's contracts (the sector they procure in most). Ties broken by total TotalValue. Computed once over the full post-cleaning dataset.
- *Jaccard similarity between CA_i and CA_j*: |contractors(i) ∩ contractors(j)| / |contractors(i) ∪ contractors(j)|, where contractors(x) is the set of distinct contractor OIBs CA x has contracted with in the observation window.
- *Primary metric*: mean pairwise Jaccard across all within-group CA pairs (all pairs sharing the same modal CPV division), weighted equally.

**Null model**: Bipartite configuration model (degree-preserving rewiring). In each rewired instance, compute mean pairwise within-group Jaccard among CA pairs sharing the same modal CPV division. The null distribution constitutes the baseline. The group labels are held fixed (based on observed modal CPV of each CA); only the graph edges are rewired.

**Graph construction**: Bipartite multigraph; IsUponFA = false; analysis window only. Restrict to CAs with degree ≥ 2 (single-contractor CAs contribute trivially to overlap). Group minimum: ≥ 5 CAs with the same modal CPV division — groups below this threshold are reported as underpowered and excluded from the test.

**Test**: One-tailed (aggregate). The observed mean within-group Jaccard aggregated across all adequately-powered groups is compared to the null ensemble 95th percentile (α = 0.05). Per-group test also run with Bonferroni correction: α* = 0.05 / n_testable_groups.  
**Effect threshold**: Excess mean within-group Jaccard (observed − null median) ≥ **0.05**. Below this, within-group overlap is attributable to shared market structure, not institutional convergence.

**Secondary analysis**: Compute within-group vs. between-group Jaccard ratio. Report per-group mean Jaccard for the five largest adequately-powered groups. If within-group similarity substantially exceeds between-group, the group structure in vendor portfolios mirrors the institutional grouping.

**Graph signal (active)**: Mean within-group Jaccard significantly exceeds the configuration model null. CAs in the same procurement domain share vendors at rates above what their individual market activity explains. Consistent with institutional peer-copying: agencies converge on the same supplier choices beyond what shared market structure dictates.

**Graph signal (absent)**: Within-group Jaccard is consistent with the null. Agencies in the same domain share vendors only to the extent their shared procurement context (same CPV sector → same potential vendor pool) would predict. No additional convergence beyond market structure.

**Real-world meaning**:  
*If confirmed:* Public institutions in the same domain systematically converge on the same vendor choices beyond what market structure explains. For a vendor not already in that institutional cluster's de-facto accepted list, breaking in is doubly difficult: not only must they win their first contract (H4), but they must win in a market where agencies actively conform to peer practice. For oversight bodies, a vendor mistake in one institution propagates peer-acceptance risk across the cluster.  
*If rejected:* Portfolio similarity within groups is fully explained by shared market structure — hospitals share vendors because they procure the same things from the same limited vendor pool, not because they copy each other. Vendor selection is independent across institutions in the same domain.

**Strongest innocent alternative**: Shared procurement context produces shared vendor pools without any copying. All hospitals buying the same medical supplies will naturally share vendors. Addressed by the configuration model null, which preserves each CA's degree and each vendor's degree. Jaccard similarity above the null, where the null already accounts for shared market structure, is the excess the innocent alternative cannot explain.


---

## Market Intelligence: Descriptive Outputs

The hypotheses above are inferential: each tests whether an observed graph property deviates from a structured null model, with a named mechanism and a named innocent alternative.

Separately, the same dataset supports **non-inferential market intelligence outputs** — structured descriptions of where anomalies are largest, which authorities have single-vendor dependencies, which CPV sectors are most concentrated, and where structural gaps may indicate underserved procurement markets. These outputs answer "where are the anomalies largest?" not "are the anomalies statistically anomalous?" They are useful for practitioners but do not constitute findings under this research protocol and are clearly labelled as descriptive.

Market intelligence outputs are produced after the corresponding inferential hypotheses have been tested and draw directly from those results:
- Per-CA single-vendor spend share rankings (from H1a)
- Per-CPV sector C1/C2/Gini concentration rankings (from H1, H1d)
- Sector-level monopoly and duopoly identification (from H1d)
- Per-CA amendment inflation rankings (from H4a)
- Temporal splitting hotspots: CA–contractor pairs with highest splitting cluster rates (from H9)
- Rotation hotspots: CA–CPV cells with highest excess alternation (from H8)

---

## Adding new hypotheses

New hypotheses are added under the appropriate domain, or a new domain is opened with a clear explanation of why it is distinct from the ones above.

**Stated date:** every new hypothesis must include a stated date with an attestation that it preceded first examination of the relevant data. Hypotheses H1–H3 predate this requirement and are grandfathered; they carry no stated date.
