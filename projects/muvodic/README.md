# Croatian Legal Network — Network Analysis

Analysis of the Croatian legislative citation network built from *Narodne novine*
(the official gazette) using NetworkX.

---

## Notebooks

Run in this order:

### 1. `network_state_overview.ipynb` — Data & network quality
Exploratory overview of the raw dataset: node and edge type distributions,
data quality checks, connectivity summary, and institution-level statistics.
Run this first to understand the data before interpreting the analysis.

### 2. `croatian_legal_network_analysis_with_kcore.ipynb` — Main analysis
- **Structural baseline** — degree distributions, comparison to Erdős–Rényi null
- **Centrality** — PageRank, betweenness, harmonic closeness on the `based_on`
  dependency layer; Spearman rank correlations
- **k-core decomposition** — legal backbone identification
- **Community detection** — Louvain on the undirected LCC projection, resolution
  sweep, Maslov–Sneppen null model comparison

---

## Data

`network_institutional.json` — NetworkX node-link format. Contains:

| Element | Count |
|---|---|
| Act nodes | 70,975 |
| Institution nodes | 46 |
| `based_on` edges | 11,727 |
| `amends` / `changes` edges | 12,312 |
| `repeals` edges | 4,335 |
| `corrects` edges | 863 |
| `passed_by` edges | 61,351 |

Source: scraped from narodne-novine.nn.hr via the ELI (European Legislation
Identifier) Linked Data endpoint.

---

## Setup

**Python version:** 3.14.3

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Launch Jupyter
jupyter notebook
```

Open `network_state_overview.ipynb` first, then
`croatian_legal_network_analysis_with_kcore.ipynb`.

The main analysis notebook takes **3–8 minutes** to run end-to-end.
The slowest cell is exact betweenness centrality (~9,700 nodes, 1–3 min
depending on hardware).

---

## Project structure

```
nn_analiza/
├── network_state_overview.ipynb                  # EDA and data quality
├── croatian_legal_network_analysis_with_kcore.ipynb  # Main analysis
├── network_institutional.json                    # Network data
├── requirements.txt                              # Pinned dependencies
└── README.md
```
