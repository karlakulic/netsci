# Croatian public procurement — graph network analysis

Analysis of 383,374 public procurement contracts in Croatia (2024–2026, ~€21.7B) using bipartite network analysis and structured null models. 15 hypotheses tested on market concentration, relational persistence, temporal anomalies, structural position, sectoral specialization, and network resilience.

**Confirmed hypotheses:**

- **Portfolio concentration (HHI):** +0.076 above null (p=0.002)
- **Relational persistence:** existing buyer–supplier pairs reconnect at **9.2×** the null expectation (z=745)
- **Amendment inflation:** established relationships inflate contract values in high-value contracts
- **Sectoral specialization:** 68.6% contract match rate vs. 5.7% null median (~12×)

**Key rejected findings:** market is resilient, not fragile (H10); no cartel-like rotation (H8); no systematic threshold evasion at scale (H9); no rich club among top suppliers (H12); no institutional mimicry across buyers (H11); structural position adds no predictive power beyond degree (H13).

**_Note:_** Data is too sparse and could be cleaner.

Applied **spectral clustering** on the bipartite core graph (9,856 nodes, 99,857 edges) — clusters show **20.2×** higher NMI with CPV sectors than random baseline.

## Project structure

```
├── PROJECT_SUMMARY.md       # Full report (methods, hypotheses, results)
├── docs/
│   ├── HYPOTHESES.md        # Hypothesis tree + null model specs
│   ├── DATA_PROFILE.md      # Data schema, missing values, limitations
│   └── RESULTS.md           # Structured results summary
├── data/
│   ├── contracts.csv        # Raw data (397,973 records)
│   └── contracts_clean.csv  # Cleaned data (383,374 records)
├── helpers/
│   └── prepare_data.py      # Data cleaning script
├── analysis/                # One script per hypothesis + exploration
│   ├── exploration.py
│   ├── exploitation_spectral.py
│   ├── h1_concentration.py
│   ├── h4_reconnection.py
│   ├── h4a_amendment_inflation.py
│   ├── h6_cpv_homophily.py
│   └── ... (15 scripts total)
├── results/
│   ├── *.txt                # Full stdout per analysis script
│   └── visualizations/      # All .png figures
```

### Data sample

```csv
TenderId,Id,ProcedureTypeId,ContractCAId,CAName,CAIdentificationNumber,ReferenceNumber,TenderName,Cpv,AgreementTypeId,ContractTypeId,ExemptionLegalBaseId,IsUponFA,Noticenumber,ContractNo,ContractDate,ContractorName,ContractorIdentificationNumber,TotalValue,TotalValueVat,TotalValueCurrencyId,ContractRationale,ContractEUFinanc,ContractStatusId,FrameworkAgreementId,FrameworkAgreementNo,DurationType,DurationMonth,DurationDay,DurationFrom,DurationTo,InitialPublishTimestamp,LastPublishedAt,InitialValue,InitialValueVAT,InitialCurrencyId,IsReversed,PayedAmount,TerminationDate,HasTenderId,last_fetched_at,cpv_code,cpv_division,is_foreign_contractor,is_framework_calloff,is_eur,in_analysis_window,is_discretionary,is_competitive,contract_year,contract_quarter,contract_year_quarter
,1053486,11.0,89308,Dječji vrtić Veseli planet,53040997965,JN 9-26,Proizvodi za čišćenje i poliranje,39800000 - Proizvodi za čišćenje i poliranje,1,2,142.0,False,,JN-9-26,2026-04-24,KTC d.d.,95970838122,2147.44,2684.3,1,,False,2,,,1.0,,,2026-04-24T00:00:00,2026-12-31,2026-05-10T18:18:01.84,2026-05-10 18:18:01.840000+00:00,2147.44,2684.3,1,False,,,True,2026-05-10T18:55:49.878Z,39800000,39,False,False,True,True,True,False,2026,2,2026-Q2
54452.0,669048,56.0,8819,HRVATSKO KATOLIČKO SVEUČILIŠTE,07730927366,2025-11,Nabava usluge stručnog nadzora za uređenje okoliša,71247000 - Nadzor građevinskih radova,1,3,,False,2025/S F03-0017708,"KLASA: 400-09/25-04/12, URBR: 251-498-03-09-01-25-5",2025-11-20,MIPAL Konzalting d.o.o.,86292962875,40320.0,50400.0,1,,True,3,,,1.0,5.0,,2025-11-20T00:00:00,2026-06-25,2025-11-27T00:14:21.38,2026-05-09 16:50:38.410000+00:00,28800.0,36000.0,1,False,,,False,2026-05-10T18:22:44.336Z,71247000,71,False,False,True,True,False,False,2025,4,2025-Q4
```

## Key documents

- [Full project report](PROJECT_SUMMARY.md)
- [Hypotheses & null models](docs/HYPOTHESES.md)
- [Results summary](docs/RESULTS.md)

## Reproducibility

Dependencies: Python 3.12+, NetworkX, Pandas, NumPy, Matplotlib, SciPy.

```bash
python helpers/prepare_data.py
python analysis/exploration.py
python analysis/h4_reconnection.py
# ... each hypothesis script is independent
python analysis/exploitation_spectral.py
```

License: CC BY-NC-ND 4.0
