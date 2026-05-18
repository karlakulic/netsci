---
marp: true
theme: default
paginate: true
footer: 'Network Analysis - PMF-UNIST 2025/2026'
---

# Scale-Free Networks
## Power Laws and Preferential Attachment

Network Analysis - Lecture 8
Nikola Balic, Faculty of Natural Science, University of Split
Data Science and Engineering Master Program

04/05/2026

---

## Recap and What's Next

- **Previous Lectures:** Graph fundamentals, measures, connectivity, communities, random graphs, small-world networks.
- **Today:** Scale-Free Networks - networks with a power-law degree distribution.
- **Key Question:** How do networks with highly connected hubs form, and what are their properties?

---

## Introduction to Scale-Free Networks

Scale-free networks are characterized by:
- **Power-law degree distribution:** P(k) ~ k^(-α), where α typically ranges between 2 and 3
- **Presence of hubs:** Few nodes have extremely high connectivity
- **No characteristic scale:** No "typical" node in the network (hence "scale-free")

These properties are observed in many real-world networks!

---

## What Does "Scale-Free" Mean?

Scale-free means **free of one characteristic scale**.

In many networks, the average degree describes a typical node fairly well.

In a scale-free network, it does not:
- most nodes have few links
- a few hubs sit far above average
- the degree pattern looks similar when we zoom in or out

---

## Power-Law Degree Distribution

Unlike random networks (Poisson distribution) or small-world networks (peaked near average), scale-free networks have a heavy-tailed degree distribution

![width:900px bg right:70%](images/degree_distributions.png)

The BA curve decays slowly: many low-degree nodes, a few high-degree hubs.
On log-log axes, a power law appears roughly as a straight descending line.

---

## Scale-Free Property: Linear View

The degree distribution of scale-free networks shows a characteristic pattern:

![width:650px bg right:50%](images/scale_free_linear_distribution.png)

- **Most nodes have few connections**: The majority are low-degree nodes
- **Very few nodes have many connections**: A small number of "hubs" with high connectivity
- **No characteristic scale**: The degree distribution spans orders of magnitude

---

## Understanding Power Laws

Power-law distribution:

$$P(k) \sim k^{-\alpha}$$

Here, $k$ is node degree, $P(k)$ is the probability of degree $k$, and $\alpha$ controls how fast the tail decays.

- **Mathematical properties:**
  - The probability of finding a node with degree $k$ decreases as $k^{-\alpha}$
  - Heavy-tailed distribution: Hubs are rare, but not negligible
  - Scale invariance: Zooming in or out keeps a similar shape

![width:600px bg right](images/power_law_distribution.png)

---

## The Barabási-Albert Model

Introduced by Albert-László Barabási and Réka Albert in 1999.

Two key mechanisms:
1. **Growth:** Network continuously expands by adding new nodes
2. **Preferential Attachment:** New nodes connect preferentially to already well-connected nodes

> "The rich get richer" or "Matthew effect"

![width:500px bg right:40%](images/network_hubs.png)

---

## Preferential Attachment: Algorithm

1. Start with a small initial network of m₀ nodes
2. Add new nodes one at a time
3. Each new node connects to m existing nodes
4. Probability of connecting to node i is proportional to its degree:

   $$P(i) = \frac{k_i}{\sum_j k_j}$$

   Here, $k_i$ is the degree of node $i$.

5. Repeat until desired network size is reached

---

## Preferential Attachment: Visual Example

![width:800px bg right:70%](images/preferential_attachment.png)

---

## Implementing Barabási-Albert in NetworkX

```python
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# Parameters
n = 1000  # Number of nodes
m = 2     # Number of edges to attach from a new node

# Generate scale-free network
G = nx.barabasi_albert_graph(n, m, seed=42)

# Calculate degree distribution
degrees = [d for _, d in G.degree()]
degree_counts = Counter(degrees)
k = np.array(sorted(degree_counts))
counts = np.array([degree_counts[degree] for degree in k])

plt.scatter(k, counts)
plt.xscale('log')
plt.yscale('log')
plt.xlabel('Degree (log scale)')
plt.ylabel('Count (log scale)')
plt.title('Degree Distribution of BA Network')
plt.show()
```

---

## Barabási-Albert Networks: Effect of Parameter m

![width:700px bg right](images/ba_networks_comparison.png)

As m increases:
- Network becomes more densely connected
- Each new node enters with more edges, but the power-law exponent remains α = 3
- Hubs become less pronounced relative to other nodes

---

## Visualizing a Scale-Free Network

![width:650px bg right](images/ba_network_detailed.png)

Note the presence of highly connected hubs (brighter colors)

---

## Mathematical Properties of BA Networks

For the Barabási-Albert model:

Here, $N$ is the number of nodes, $k$ is node degree, and $C$ is average clustering.

- **Degree distribution:**
  $$P(k) \sim k^{-3}$$
- **Average path length:**
  $$L \sim \frac{\ln(N)}{\ln(\ln(N))}$$
- **Clustering coefficient:**
  $$C \sim N^{-0.75}$$

Unlike small-world networks, clustering is lower and decays with N, though it remains higher than an equivalent ER random graph for moderate network sizes.

---

## Emergence of Hubs

Hubs are nodes with exceptionally high degree that emerge naturally in scale-free networks.

![width:800px bg right](images/network_hubs.png)

Hubs play critical roles:
- Drastically reduce network diameter
- Facilitate efficient information flow
- Create vulnerability to targeted attacks

---

## Network Resilience in Scale-Free Networks

Scale-free networks exhibit:
- **High resilience to random failures**
- **High vulnerability to targeted attacks**

![width:700px bg right](images/network_attacks.png)

---

## The "Achilles' Heel" of Scale-Free Networks

- Random failures typically affect low-degree nodes → minimal impact
- Targeted attacks on hubs → catastrophic network fragmentation

**Real-world implications:**
- Internet resilience to random server failures
- Vulnerability of power grids to targeted attacks
- Spread of diseases in social networks

---

## Generating Scale-Free Networks: Alternatives

- **Configuration Model:** Generate networks with any desired degree distribution
- **Fitness Model:** Nodes have intrinsic fitness affecting attachment probability
- **Non-linear Preferential Attachment:** Attachment probability $$\sim k^{\beta}$$ ($$\beta \neq 1$$)
- **Aging Effects:** Older nodes become less attractive for attachment
- **Geographical Constraints:** Spatial limitations on connections

---

## Limitations of Pure Scale-Free Models

Real networks often deviate from perfect power laws:
- **Finite-size effects:** Real networks have limited size
- **Growth constraints:** Physical, technological, or resource limitations
- **Aging and death of nodes:** Nodes may become inactive or be removed
- **Costs of adding links:** Physical or maintenance costs limit connections
- **Directed and weighted connections:** More complex than simple undirected links

---

## Detecting Scale-Free Properties

How to determine if a network is scale-free:
1. Plot degree distribution on log-log scale
2. Fit power-law using maximum likelihood estimation
3. Calculate goodness-of-fit (Kolmogorov-Smirnov test)
4. Compare with alternative distributions (exponential, log-normal)

```python
import powerlaw
# Fit power law to degree distribution
positive_degrees = [degree for degree in degrees if degree > 0]
fit = powerlaw.Fit(positive_degrees, discrete=True)
print(f"Power law exponent: {fit.alpha}")
# Compare with alternative distributions
R, p = fit.distribution_compare('power_law', 'exponential')
```

---

## Controversies and Debates

- **Are most "scale-free" networks truly scale-free?**
  - 2018 paper by Broido & Clauset questioned prevalence
  - Different definitions and detection methods yield different results

- **Alternative models:**
  - Log-normal distributions
  - Stretched exponentials
  - Truncated power laws

→ Active area of research!

---

## Real-World Scale-Free Networks

![width:800px bg right:70%](images/real_world_examples.png)

---

## Network Model Comparison

![width:1200px bg](images/network_comparison_table.png)

---

## What Scale-Free Structure Changes

- **Hubs dominate outcomes:** A few nodes can control much of the flow
- **Random failure is misleading:** Average-case damage can look small
- **Targeted removal matters:** Attacking or protecting hubs changes the network quickly
- **Spreading thresholds shift:** Hubs can sustain diffusion even when average degree is low
- **Fairness concerns appear:** Hub-based strategies can reinforce existing visibility

---

## Python Tools for Scale-Free Network Analysis

```python
# Fitting and testing power-law distributions
import powerlaw
positive_degrees = [degree for degree in degrees if degree > 0]
fit = powerlaw.Fit(positive_degrees, discrete=True)
print(f"Alpha: {fit.alpha}, xmin: {fit.xmin}")
print(f"Goodness of fit: {fit.power_law.KS()}")

# Testing against alternative distributions
R, p = fit.distribution_compare('power_law', 'exponential')
print(f"Log-likelihood ratio: {R}, p-value: {p}")

# Creating scale-free networks with NetworkX
G_ba = nx.barabasi_albert_graph(n=1000, m=2, seed=42)
G_plc = nx.powerlaw_cluster_graph(n=1000, m=2, p=0.1, seed=42)
```

---

## Key Takeaways

1. Scale-free networks have a **power-law degree distribution** with P(k) ~ k^(-α)
2. They form through **growth** and **preferential attachment**
3. They contain **hubs** that connect many other nodes
4. They are **robust against random failures** but **vulnerable to targeted attacks**
5. Some **real-world networks** show scale-free-like degree patterns
6. Understanding scale-free structure helps design **more resilient systems**

---

## Next Lecture: Network Resilience

We'll expand on network robustness and resilience:
- Quantifying network resilience
- Cascading failures and percolation theory
- Design principles for resilient networks
- Case studies of network failures
- Strategies for improving network robustness
