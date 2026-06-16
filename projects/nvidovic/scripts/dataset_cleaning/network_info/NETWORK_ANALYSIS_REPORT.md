# TMDB Movie Network Analysis Report

**Generated on:** 2026-06-07 01:38:33

---

## Executive Summary

This report contains a comprehensive analysis of the TMDB (The Movie Database) network, constructed from 5,000 movies and their associated cast and crew members. The network includes all production team members, creating a global bipartite graph where nodes represent movies and people, and edges represent professional relationships.

---

## Network Overview

### Key Statistics

| Metric | Value |
|--------|-------|
| **Total Nodes** | 107,913 |
| **Total Edges** | 226,540 |
| **Network Density** | 0.000039 |
| **Average Node Degree** | 4.20 |
| **Maximum Degree** | 455 |
| **Minimum Degree** | 1 |
| **Number of Communities** | 112 |
| **Network Diameter** | 15 |
| **Average Clustering Coefficient** | 0.000000 |

**Interpretation:** 
- The network density of 0.000039 indicates a sparse network.
- The average degree of 4.20 suggests that on average, each node is connected to approximately 4 other nodes.
- 112 distinct communities were identified using the Louvain algorithm, indicating distinct clusters of movies and production team members.

---

## Detailed Data Files

The following CSV files contain detailed analysis results and are referenced below:

### 1. **nodes_by_degree.csv**
Contains comprehensive information for all 107,913 nodes in the network, including:
- **Node_ID**: Unique identifier within the network
- **Node_Name**: Name of the movie or person
- **Degree**: Number of connections for this node
- **Community**: Community identifier (from Louvain clustering)
- **Betweenness_Centrality**: Measure of how often a node lies on shortest paths between other nodes

**Top 10 Most Connected Nodes:**
| Rank | Node Name | Degree | Community |
|------|-----------|--------|-----------|
| 1 | Jurassic World | 455 | 26 |
| 2 | 15 Minutes | 410 | 46 |
| 3 | The Wolf of Wall Street | 373 | 15 |
| 4 | The Dark Knight Rises | 366 | 7 |
| 5 | Jason Bourne | 320 | 40 |
| 6 | Monsters, Inc. | 278 | 14 |
| 7 | The Core | 273 | 17 |
| 8 | Contact | 268 | 1 |
| 9 | Batman v Superman: Dawn of Justice | 261 | 4 |
| 10 | V for Vendetta | 258 | 2 |


### 2. **nodes_by_betweenness_centrality.csv**
Nodes ranked by betweenness centrality, identifying key "bridge" nodes that connect different parts of the network.

**Top 10 Bridge Nodes (Highest Betweenness Centrality):**
| Rank | Node Name | Betweenness Centrality | Degree |
|------|-----------|------------------------|--------|
| 1 | Jurassic World | 46422401.11 | 455 |
| 2 | The Dark Knight Rises | 45488042.07 | 366 |
| 3 | 15 Minutes | 41387707.90 | 410 |
| 4 | Mary Vernieu | 39838411.27 | 81 |
| 5 | Avy Kaufman | 37037900.70 | 83 |
| 6 | The Wolf of Wall Street | 36919059.49 | 373 |
| 7 | Steven Spielberg | 33130222.81 | 68 |
| 8 | Jason Bourne | 30942068.88 | 320 |
| 9 | John Williams | 29199518.80 | 53 |
| 10 | Harvey Weinstein | 28710566.25 | 70 |


**Interpretation:** These nodes act as critical connectors in the network. High betweenness centrality indicates that many shortest paths between nodes pass through these nodes.

### 3. **communities_info.csv**
Contains information about 112 communities detected using the Louvain algorithm:
- **Community_ID**: Unique identifier for each community
- **Number_of_Members**: Count of nodes in the community
- **Average_Degree**: Mean degree of nodes within the community
- **Members**: Sample list of members (first 20)

**Community Size Distribution:**
| Community ID | Size | Average Degree |
|--------------|------|----------------|
| 2 | 12101 | 4.35 |
| 15 | 7990 | 4.80 |
| 9 | 7488 | 4.97 |
| 1 | 5890 | 5.37 |
| 17 | 5260 | 4.81 |
| 20 | 5039 | 3.82 |
| 5 | 5018 | 4.86 |
| 14 | 4391 | 4.67 |
| 28 | 4187 | 2.93 |
| 21 | 4171 | 4.34 |
| 3 | 3735 | 4.01 |
| 19 | 3220 | 4.55 |
| 24 | 2666 | 3.80 |
| 30 | 2574 | 3.09 |
| 25 | 2523 | 4.59 |


### 4. **edges_list.csv**
Complete edge list containing all 226,540 connections in the network:
- **Source**: First node in the connection
- **Target**: Second node in the connection

This file can be used for network visualization in tools like Gephi, Cytoscape, or NetworkX.

### 5. **network_statistics.csv**
Summary of core network metrics and their values, useful for quick reference and comparative analysis.

---

## Network Analysis Insights

### Network Characteristics

1. **Connectivity**: With 107,913 nodes and 226,540 edges, this network represents a substantial production ecosystem within the TMDB database.

2. **Community Structure**: The detection of 112 communities suggests natural clustering of movies and personnel, likely reflecting different production eras, genres, or cultural contexts.

3. **Hub Nodes**: The most connected nodes (appearing in nodes_by_degree.csv) likely represent major production companies, prolific directors/actors, or blockbuster franchises.

4. **Bridge Nodes**: Nodes with high betweenness centrality (in nodes_by_betweenness_centrality.csv) are crucial for information flow and represent influential connectors across different parts of the network.

5. **Network Diameter**: A diameter of 15 indicates that the longest shortest path between any two nodes requires 15 steps, reflecting the overall structure and connectivity of the production world.

---

## How to Use These Files

1. **For Network Visualization**: Use edges_list.csv with tools like:
   - Gephi (open-source network visualization)
   - Cytoscape (network analysis software)
   - NetworkX (Python library)

2. **For Statistical Analysis**: Use nodes_by_degree.csv and network_statistics.csv for:
   - Correlation analysis
   - Distribution studies
   - Comparative metrics

3. **For Community Analysis**: Use communities_info.csv to:
   - Identify distinct production clusters
   - Analyze community-level patterns
   - Study inter-community relationships

4. **For Centrality Studies**: Use nodes_by_betweenness_centrality.csv to:
   - Identify key influencers
   - Analyze information flow
   - Study network resilience

---

## Technical Details

- **Graph Construction**: Bipartite network of movies and production team members
- **Community Detection**: Louvain algorithm for modularity optimization
- **Centrality Measures**: 
  - Degree centrality (number of direct connections)
  - Betweenness centrality (frequency on shortest paths)
- **Analysis Date**: 2026-06-07
- **Data Source**: TMDB 5000 Movies and Credits datasets

---

## Data File References

All data files are stored in the `network_info/` directory:

1. `nodes_by_degree.csv` - All nodes with degree and centrality metrics
2. `nodes_by_betweenness_centrality.csv` - Nodes ranked by betweenness centrality
3. `communities_info.csv` - Community-level statistics
4. `edges_list.csv` - Complete edge list for network visualization
5. `network_statistics.csv` - Summary statistics

---

*This analysis provides a comprehensive foundation for understanding the structure and dynamics of the TMDB production network.*
