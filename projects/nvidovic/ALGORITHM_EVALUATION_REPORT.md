# Algorithm Evaluation Report: Recommendation System Graph

## 1. Executive Summary
This report analyzes 9 recommendation algorithms implemented on a movie-person bipartite graph and user rating data. Performance was evaluated using Precision@10, Recall@10, NDCG@10, and **Hit Rate**. **Item-Item Collaborative Filtering** and the **Popularity Baseline** remain the most effective strategies, while **Weighted LightGCN** shows strong potential as a graph-based neural approach.

---

## 2. Evaluation Methodology
- **Dataset**: TMDB 5000 Movies/Credits + MovieLens Ratings.
- **Graph Structure**: Bipartite graph (Movies $\leftrightarrow$ People).
- **Test Split**: Users with history in `ratings_x` (input) and liked movies (rating > 3.5) in `ratings_y` (ground truth).
- **Metric Definitions**:
    - **Precision@10**: Ratio of recommended items that are relevant (liked).
    - **Recall@10**: Ratio of relevant items that were successfully recommended.
    - **NDCG@10**: Ranking quality; rewards relevant items at the top of the list.
    - **Hit Rate**: Ratio of users for whom at least one correct recommendation was made.

---

## 3. Detailed Algorithm Analysis

### 3.1 Graph-Based Similarity Methods
| Algorithm | Logic | Finding |
|-----------|-------|---------|
| **Jaccard Similarity** | Person-neighbor overlap. | **Low precision (0.0127)** but surprisingly high Hit Rate (0.413). |
| **Adamic-Adar** | Rare neighbor weighting. | Slightly outperformed Jaccard in all metrics. |
| **Personalized PageRank** | Biased random walks. | Strong structural signal, comparable to Adamic-Adar. |

### 3.2 Clustering & Communities
| Algorithm | Logic | Finding |
|-----------|-------|---------|
| **Louvain Community** | Popularity within graph clusters. | Decent Hit Rate (0.381) but low precision. |
| **K-Means (Features)** | Metadata-based clustering. | **Worst performer.** Hit Rate (0.151) is even lower than Random. |

### 3.3 Graph Neural Networks (GNN)
| Algorithm | Logic | Finding |
|-----------|-------|---------|
| **LightGCN** | Linear message passing. | Base model is weak (0.0158 P@10). |
| **Weighted LightGCN** | Rating-weighted edges. | **High performance.** Hit Rate of 0.733. Rating values are essential. |

### 3.4 Embedding & Collaborative Filtering
| Algorithm | Logic | Finding |
|-----------|-------|---------|
| **Node2Vec** | Random walk embeddings. | Better than metadata clustering but trails simple graph metrics. |
| **Item-Item CF** | User behavior similarity. | **Dominant.** 0.287 Precision and 0.957 Hit Rate. |

---

## 4. Quantitative Results (Sorted by Precision)

| Pozicija | Algorithm | Hit Rate | NDCG@10 | Precision@10 | Recall@10 |
|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | Popularity Baseline | **0.968** | 0.299268 | 0.2320 | 0.209083 |
| 2 | Item-Item CF | **0.957** | 0.344523 | 0.2872 | 0.232342 |
| 3 | Weighted LightGCN | **0.673** | 0.080629 | 0.0723 | 0.056352 |
| 4 | Personalized PageRank | **0.448** | 0.016976 | 0.0158 | 0.011795 |
| 5 | Adamic-Adar | **0.443** | 0.020637 | 0.0173 | 0.012406 |
| 6 | LightGCN | **0.426** | 0.015664 | 0.0136 | 0.010100 |
| 7 | Jaccard Similarity | **0.413** | 0.014797 | 0.0127 | 0.008556 |
| 8 | Louvain Community | **0.394** | 0.017075 | 0.0143 | 0.009085 |
| 9 | Node2Vec | **0.364** | 0.013829 | 0.0122 | 0.010196 |
| 10 | Random Baseline | **0.327** | 0.011324 | 0.0070 | 0.007960 |
| 11 | K-Means Clustering | **0.151** | 0.003431 | 0.0043 | 0.003997 |

---

## 5. Key Findings & Insights
1. **Hit Rate vs. Precision**: Algorithms like Jaccard have very low precision but can "hit" at least one movie for 41% of users. This suggests they are useful for discovery but carry many irrelevant items.
2. **Behavioral Supremacy**: Item-Item CF (behavior) drastically outperforms metadata-based methods (K-Means).
3. **Graph Sparsity Mitigation**: Weighting edges with ratings (Weighted LightGCN) is the most effective way to improve graph-based models, nearly tripling the precision of standard LightGCN.
4. **Baseline Challenge**: The Popularity Baseline is extremely competitive, suggesting a high concentration of popular movies in the test set's "likes."

---

## 6. Qualitative Analysis (User Case: 5212)
- **Weighted LightGCN Improvement**: Now correctly hits *Beetlejuice*.
- **LightGCN**: Successfully recommended *License to Wed*.
- **Item-Item CF**: Continues to hit *Terminator 3: Rise of the Machines*.
- **Discovery**: Jaccard and PageRank successfully suggest sequels (*Bourne Supremacy/Ultimatum*), proving they capture series/franchise relationships well through cast overlap.

---

## 7. Future Improvements
- **Hybridize**: Merge Popularity Baseline with Item-Item CF to handle cold-start users.
- **Rich Graphs**: Add Genre and Keyword nodes to the bipartite graph to increase density.
- **Deep Learning**: Explore supervised GNN training (BPR Loss) for LightGCN instead of raw message passing.
