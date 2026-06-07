"""
Fast Graph Exploration — computes standard topological metrics efficiently.
Outputs computed values for PROJECT_SUMMARY.md.
"""
import time, textwrap
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx; import numpy as np; import pandas as pd
from scipy import stats
from sklearn.metrics import normalized_mutual_info_score

DATA_PATH = "data/contracts_clean.csv"
PLOT_DIR = "results/visualizations"
RNG = np.random.RandomState(42)

def load():
    df = pd.read_csv(DATA_PATH, low_memory=False)
    m = (df["in_analysis_window"].eq(True) & df["is_eur"].eq(True)
         & df["is_foreign_contractor"].eq(False) & df["is_framework_calloff"].eq(False))
    return df, df[m].copy()

def build_graph(df):
    """Build bipartite simple graph. Cast all IDs to string for consistent type."""
    B = nx.Graph()
    ca = sorted(df["CAIdentificationNumber"].astype(str).unique())
    co = sorted(df["ContractorIdentificationNumber"].astype(str).unique())
    B.add_nodes_from(ca, bipartite=0)
    B.add_nodes_from(co, bipartite=1)
    pairs = df[["CAIdentificationNumber","ContractorIdentificationNumber"]].drop_duplicates()
    pairs["CAIdentificationNumber"] = pairs["CAIdentificationNumber"].astype(str)
    pairs["ContractorIdentificationNumber"] = pairs["ContractorIdentificationNumber"].astype(str)
    B.add_edges_from(zip(pairs["CAIdentificationNumber"], pairs["ContractorIdentificationNumber"]))
    return B, set(ca), set(co)

def components_and_diameter(B):
    print("  Components + diameter...", end=" ", flush=True); t0=time.time()
    comps = list(nx.connected_components(B))
    giant = max(comps, key=len)
    gsub = B.subgraph(giant).copy()
    nodes = list(gsub.nodes())
    best = 0
    for src in RNG.choice(nodes, size=min(3, len(nodes)), replace=False):
        l1 = nx.single_source_shortest_path_length(gsub, str(src))
        far = max(l1, key=l1.get)
        l2 = nx.single_source_shortest_path_length(gsub, str(far))
        d = max(l2.values())
        if d > best: best = d
    print(f"done ({time.time()-t0:.1f}s)")
    return len(comps), len(giant), 100*len(giant)/B.number_of_nodes(), best

def degree_stats_and_plot(B, ca_set, co_set):
    print("  Degree distributions...", end=" ", flush=True); t0=time.time()
    ca_d = np.array([d for n,d in B.degree() if n in ca_set])
    co_d = np.array([d for n,d in B.degree() if n in co_set])
    # Power-law fit on CO
    degrees = co_d[co_d>0]
    alpha, xmin_val = float("nan"), 0
    best_ks = np.inf
    for xm in sorted(set(degrees))[:30]:
        tail = degrees[degrees>=xm]
        if len(tail)<10: continue
        a = 1 + len(tail)/np.sum(np.log(tail/xm))
        ks,_ = stats.kstest(tail, lambda x,a=a,xm=xm: 1-(x/xm)**(-a+1))
        if ks<best_ks: best_ks, alpha, xmin_val = ks, a, xm
    # Plot
    fig, axes = plt.subplots(1,2,figsize=(14,5))
    for ax, degs, title, col in [(axes[0],ca_d,"CA","#1f77b4"),(axes[1],co_d,"CO","#ff7f0e")]:
        degs=degs[degs>0]
        bins=np.logspace(np.log10(1),np.log10(max(degs)+1),35)
        h,e=np.histogram(degs,bins=bins); bc=np.sqrt(e[:-1]*e[1:])
        ax.loglog(bc[h>0],h[h>0],"o-",color=col,ms=4,alpha=.8)
        ax.set_xlabel("Degree"); ax.set_ylabel("Count"); ax.set_title(f"Degree Distribution — {title}")
        ax.grid(True,alpha=.3)
    plt.tight_layout(); plt.savefig(f"{PLOT_DIR}/exploration_degree_distribution.png",dpi=150); plt.close()
    print(f"done ({time.time()-t0:.1f}s)")
    return ca_d, co_d, alpha, xmin_val

def bipartite_clustering(B, ca_set):
    """Robins-Alexander bipartite clustering coefficient, sampled."""
    print("  Bipartite clustering...", end=" ", flush=True); t0=time.time()
    ca_list = sorted(ca_set)
    if len(ca_list)>3000:
        ca_list = sorted(RNG.choice(ca_list, size=3000, replace=False))
    total_cc, count = 0.0, 0
    for ca in ca_list:
        neighbors = list(B.neighbors(ca))
        d = len(neighbors)
        if d<2: continue
        closed, paths = 0, 0
        for i in range(d):
            for j in range(i+1,d):
                n1,n2 = neighbors[i],neighbors[j]
                deg1,deg2 = B.degree(n1),B.degree(n2)
                if deg1<=1 and deg2<=1: continue
                shared=len(set(B.neighbors(n1))&set(B.neighbors(n2)))
                if shared>=2: closed+=shared-1
                paths+=max(0,deg1-1)+max(0,deg2-1)-2
        if paths>0:
            total_cc+=closed/paths; count+=1
    avg = total_cc/count if count>0 else 0.0
    print(f"done ({time.time()-t0:.1f}s, n={count})")
    return avg

def centrality_sampled(B, ca_set, co_set, df):
    print("  Centrality...", end=" ", flush=True); t0=time.time()
    giant = max(nx.connected_components(B), key=len)
    gsub = B.subgraph(giant).copy()

    dc = nx.degree_centrality(B)
    ca_dc = {n:dc.get(n,0) for n in ca_set}
    co_dc = {n:dc.get(n,0) for n in co_set}

    bt = nx.betweenness_centrality(gsub, k=15, seed=42, normalized=True)
    gsub_set = set(gsub.nodes())
    ca_bt = {n:bt.get(str(n),0) for n in ca_set if str(n) in gsub_set}
    co_bt = {n:bt.get(str(n),0) for n in co_set if str(n) in gsub_set}

    try: ec = nx.eigenvector_centrality(gsub, max_iter=100, tol=1e-3)
    except: ec = dc
    ca_ec = {n:ec.get(str(n),0) for n in ca_set if str(n) in gsub_set}
    co_ec = {n:ec.get(str(n),0) for n in co_set if str(n) in gsub_set}

    # Closeness sampled
    gsub_nodes = list(gsub.nodes())
    sources = list(RNG.choice(gsub_nodes,size=min(100,len(gsub_nodes)),replace=False))
    ca_cl = {n:0.0 for n in ca_set if str(n) in gsub_set}
    co_cl = {n:0.0 for n in co_set if str(n) in gsub_set}
    ns = len(sources)
    for src in sources:
        src_str = str(src)
        for tgt,d in nx.single_source_shortest_path_length(gsub, src_str).items():
            if d==0: continue
            tgt_str = str(tgt)
            if tgt_str in ca_cl: ca_cl[tgt_str] += 1.0/d
            elif tgt_str in co_cl: co_cl[tgt_str] += 1.0/d
    for dct in [ca_cl,co_cl]:
        for n in dct: dct[n] /= ns

    def top3(d): return sorted(d.items(),key=lambda x:-x[1])[:3]
    print(f"done ({time.time()-t0:.1f}s)")

    fig,axes=plt.subplots(2,2,figsize=(14,10))
    for ax,dca,dco,title in [(axes[0,0],ca_dc,co_dc,"Degree"),(axes[0,1],ca_bt,co_bt,"Betweenness"),
                              (axes[1,0],ca_ec,co_ec,"Eigenvector"),(axes[1,1],ca_cl,co_cl,"Closeness")]:
        for vals,lbl,col in [(dca.values(),"CA","#1f77b4"),(dco.values(),"CO","#ff7f0e")]:
            v=[x for x in vals if x>0]
            ax.hist(v,bins=50,alpha=.6,label=f"{lbl} (n={len(v)})",color=col,log=True)
        ax.set_xlabel("Centrality"); ax.set_ylabel("Count (log)"); ax.set_title(title)
        ax.legend(fontsize=8); ax.grid(True,alpha=.3)
    plt.tight_layout(); plt.savefig(f"{PLOT_DIR}/exploration_centrality_distributions.png",dpi=150); plt.close()
    return {"degree":(ca_dc,co_dc,top3(ca_dc),top3(co_dc)),
            "betweenness":(ca_bt,co_bt,top3(ca_bt),top3(co_bt)),
            "eigenvector":(ca_ec,co_ec,top3(ca_ec),top3(co_ec)),
            "closeness":(ca_cl,co_cl,top3(ca_cl),top3(co_cl))}

def modularity_fast(B, ca_set, df):
    """Louvain on CA-CA projection with edge filtering for speed."""
    print("  Modularity (Louvain)...", end=" ", flush=True); t0=time.time()
    ca_list = sorted(ca_set)
    ca_idx = {ca:i for i,ca in enumerate(ca_list)}
    neighbors = {ca:set(B.neighbors(ca)) for ca in ca_list}
    G = nx.Graph(); G.add_nodes_from(range(len(ca_list)))
    edge_n=0
    all_co = set()
    for ca in ca_list: all_co |= neighbors[ca]
    for co in sorted(all_co):
        ca_nbrs_of_co = [n for n in list(B.neighbors(co)) if n in ca_set]
        ca_indices = [ca_idx[n] for n in ca_nbrs_of_co]
        d=len(ca_indices)
        if d<2: continue
        if d>200:  # subsample high-degree COs
            for i in range(d):
                for j in range(i+1, min(i+11,d)):
                    a,b=ca_indices[i],ca_indices[j]
                    if a>b: a,b=b,a
                    G.add_edge(a,b); edge_n+=1
            continue
        for i in range(d):
            for j in range(i+1,d):
                a,b=ca_indices[i],ca_indices[j]
                if a>b: a,b=b,a
                G.add_edge(a,b); edge_n+=1
    print(f"{edge_n} edges, ", end="", flush=True)
    from networkx.algorithms.community import greedy_modularity_communities
    comms=list(greedy_modularity_communities(G))
    part={}; Q=0
    for idx,c in enumerate(comms):
        for node in c: part[node]=idx
    Q=nx.algorithms.community.modularity(G,comms)
    n_comm=len(set(part.values()))
    # NMI with CPV
    ca_cpv={}
    for ca in ca_list:
        m=df["CAIdentificationNumber"].astype(str)==ca
        if m.any():
            mv=df.loc[m,"cpv_division"].mode()
            ca_cpv[ca]=int(mv.iloc[0]) if len(mv)>0 else 0
    cpv_l=[ca_cpv.get(ca,0) for ca in ca_list]
    louv_l=[part.get(ca_idx[ca],0) for ca in ca_list]
    nmi=normalized_mutual_info_score(np.array(cpv_l),np.array(louv_l)) if len(set(cpv_l))>1 else 0.0
    print(f"Q={Q:.4f}, NMI={nmi:.4f}, {n_comm} comms, {time.time()-t0:.1f}s)")
    return n_comm, float(Q), float(nmi)

def main():
    df_full, df = load()
    print(f"Loaded: {len(df):,} rows\n")
    B, ca_set, co_set = build_graph(df)
    n_ca,n_co=len(ca_set),len(co_set); m=B.number_of_edges()
    density=m/(n_ca*n_co)
    print(f"Graph: {n_ca:,} CA × {n_co:,} CO | {m:,} edges | density={density:.2e}\n")

    n_comp, giant_sz, giant_pct, diam = components_and_diameter(B)
    print(f"Components: {n_comp} | Giant: {giant_sz:,} ({giant_pct:.1f}%) | Diameter: {diam}\n")

    ca_d, co_d, alpha, xmin_val = degree_stats_and_plot(B, ca_set, co_set)
    print(f"CA deg: median={np.median(ca_d):.0f} mean={np.mean(ca_d):.1f} max={max(ca_d)}")
    print(f"CO deg: median={np.median(co_d):.0f} mean={np.mean(co_d):.2f} max={max(co_d)}")
    if not np.isnan(alpha):
        typ = "Scale-free (2<α<3)" if 2<alpha<3 else f"Power-law α={alpha:.2f}"
    else: typ = "Heterogeneous (power-law fit failed)"
    print(f"α={alpha:.3f} xmin={xmin_val} → {typ}\n")

    cc = bipartite_clustering(B, ca_set)
    print(f"Bipartite clustering coefficient (CA): {cc:.6f}\n")

    cent = centrality_sampled(B, ca_set, co_set, df)
    for mname,(dca,dco,tca,tco) in cent.items():
        print(f"  {mname}: mean CA={np.mean(list(dca.values())):.4f} CO={np.mean(list(dco.values())):.4f}")
    print()

    n_comm, Q, nmi = modularity_fast(B, ca_set, df)
    print(f"Louvain: {n_comm} communities, Q={Q:.4f}, NMI(CPV)={nmi:.4f}\n")

    print("="*60)
    print("PASTE INTO PROJECT_SUMMARY.md:")
    print(f"  Nodes: {n_ca+n_co:,} ({n_ca:,} CA + {n_co:,} CO)")
    print(f"  Simple edges: {m:,}")
    print(f"  Multiedges (contracts): {len(df):,}")
    print(f"  Components: {n_comp} (giant: {giant_pct:.1f}%)")
    print(f"  Diameter: {diam}")
    print(f"  Density: {density:.2e}")
    print(f"  CA degree: median={np.median(ca_d):.0f}, mean={np.mean(ca_d):.1f}")
    print(f"  CO degree: median={np.median(co_d):.0f}, mean={np.mean(co_d):.2f}")
    print(f"  α={alpha:.2f}, type: {typ}")
    print(f"  Bipartite clustering (CA): {cc:.4f}")
    print(f"  Louvain: Q={Q:.4f}, {n_comm} communities, NMI={nmi:.4f}")

if __name__=="__main__":
    main()
