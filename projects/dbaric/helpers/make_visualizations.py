"""
Generate all course overview visualizations.
Output: results/visualizations/*.png
"""

import random
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import networkx as nx
from matplotlib.colors import to_hex

DATA_PATH = "data/contracts_clean.csv"
OUT_DIR = "results/visualizations"

CPV_NAMES = {
    9: "Naftni derivati", 14: "Rudarstvo", 15: "Prehrambeni proizvodi",
    19: "Koža/guma", 22: "Tiskovine", 24: "Kemikalije",
    30: "Uredska oprema", 32: "Radio/TV oprema", 33: "Medicinska oprema",
    34: "Motorna vozila", 39: "Namještaj", 41: "Voda (preč.)",
    42: "Industr. strojevi", 44: "Građ. materijali", 45: "Građevinski radovi",
    48: "Softver", 50: "Popravak/održ.", 55: "Hotelske usluge",
    60: "Prijevozne usluge", 63: "Prateće transp. usl.", 64: "Pošt./telekom. usl.",
    65: "Javne usluge", 66: "Financ. usluge", 70: "Nekretnine",
    71: "Arhit./inž. usl.", 72: "IT usluge", 73: "R&D usl.",
    75: "Javna uprava", 79: "Posl. usluge", 80: "Obrazovanje",
    85: "Zdravstvene usluge", 90: "Kanalizac./otpad", 92: "Rekreacija",
    98: "Ostale usluge",
}

PALETTE = {
    "primary": "#1a5276",
    "secondary": "#2874a6",
    "accent": "#e74c3c",
    "muted": "#85929e",
    "green": "#1e8449",
    "orange": "#d35400",
    "bg": "#fafafa",
    "grid": "#e5e5e5",
}


def load():
    df = pd.read_csv(DATA_PATH, low_memory=False)
    mask = (
        df["in_analysis_window"].eq(True)
        & df["is_eur"].eq(True)
        & df["is_foreign_contractor"].eq(False)
        & df["is_framework_calloff"].eq(False)
    )
    return df[mask].copy()


def _resolve_ca_col(df):
    """Return the CA name column present in the dataframe."""
    for c in ["CAName", "ContractingAuthorityName", "BuyerName", "AuthorityName"]:
        if c in df.columns:
            return c
    # fallback
    cand = [c for c in df.columns if "authority" in c.lower() or "buyer" in c.lower()]
    return cand[0] if cand else df.columns[0]


def _con_name_map(df):
    """Return dict: ContractorIdentificationNumber → ContractorName (truncated)."""
    mapping = {}
    for _, row in df[["ContractorIdentificationNumber", "ContractorName"]].drop_duplicates().iterrows():
        oid = row["ContractorIdentificationNumber"]
        name = str(row["ContractorName"]) if pd.notna(row["ContractorName"]) else str(oid)
        mapping[oid] = name
    return mapping


# ---------------------------------------------------------------------------
# 1. Per-sector bipartite graph — H1d
# ---------------------------------------------------------------------------
def viz_sector_bipartite(df):
    # Top 5 sectors by observed C1 (highest monopoly signal)
    top_sectors = [60, 64, 9, 66, 41]  # CPV with highest C1 obs values
    con_name = _con_name_map(df)
    ca_col = _resolve_ca_col(df)

    fig, axes = plt.subplots(1, 5, figsize=(22, 8), facecolor=PALETTE["bg"])
    fig.suptitle(
        "H1d — Bipartitni grafovi po sektoru (top-5 po C1 monopolnom signalu)",
        fontsize=13, fontweight="bold", y=1.02, color="#1a1a1a",
    )

    sector_c1 = {60: 0.660, 64: 0.756, 9: 0.510, 66: 0.404, 41: 0.284}
    sector_null_c1 = {60: 0.177, 64: 0.544, 9: 0.104, 66: 0.093, 41: 0.132}

    for ax, sector in zip(axes, top_sectors):
        ax.set_facecolor(PALETTE["bg"])
        grp = df[df["cpv_division"] == sector].copy()

        # Top-N contractors by value (keep readable)
        con_vals = grp.groupby("ContractorIdentificationNumber")["TotalValue"].sum()
        top_cons = con_vals.nlargest(12).index

        ca_vals = grp.groupby(ca_col)["TotalValue"].sum()
        top_cas = ca_vals.nlargest(15).index

        sub = grp[
            grp["ContractorIdentificationNumber"].isin(top_cons) &
            grp[ca_col].isin(top_cas)
        ]

        G = nx.Graph()
        for _, row in sub.iterrows():
            ca = str(row[ca_col])[:25]
            con = str(row["ContractorIdentificationNumber"])
            w = float(row["TotalValue"]) if pd.notna(row["TotalValue"]) else 0
            if G.has_edge(f"CA:{ca}", f"CON:{con}"):
                G[f"CA:{ca}"][f"CON:{con}"]["weight"] += w
            else:
                G.add_edge(f"CA:{ca}", f"CON:{con}", weight=w)

        ca_nodes = [n for n in G.nodes() if n.startswith("CA:")]
        con_nodes = [n for n in G.nodes() if n.startswith("CON:")]

        if not con_nodes:
            ax.text(0.5, 0.5, "Nema podataka", ha="center", va="center",
                    transform=ax.transAxes, fontsize=9)
            continue

        # Layout: CAs on left, contractors on right
        pos = {}
        for i, n in enumerate(sorted(ca_nodes)):
            pos[n] = (0.0, i / max(len(ca_nodes) - 1, 1))
        for i, n in enumerate(sorted(con_nodes)):
            pos[n] = (1.0, i / max(len(con_nodes) - 1, 1))

        # Node sizes
        ca_total = {n: sum(G[n][nb]["weight"] for nb in G.neighbors(n)) for n in ca_nodes}
        con_total = {n: sum(G[n][nb]["weight"] for nb in G.neighbors(n)) for n in con_nodes}

        all_vals = list(ca_total.values()) + list(con_total.values())
        max_val = max(all_vals) if all_vals else 1
        ca_sizes = [80 + 300 * (ca_total[n] / max_val) for n in ca_nodes]
        con_sizes = [80 + 300 * (con_total[n] / max_val) for n in con_nodes]

        # Color contractors: dominant (top 1-2) vs others
        sorted_cons = sorted(con_total, key=con_total.get, reverse=True)
        dom1 = sorted_cons[0] if len(sorted_cons) > 0 else None
        dom2 = sorted_cons[1] if len(sorted_cons) > 1 else None

        con_colors = []
        for n in con_nodes:
            if n == dom1:
                con_colors.append(PALETTE["accent"])
            elif n == dom2:
                con_colors.append(PALETTE["orange"])
            else:
                con_colors.append(PALETTE["muted"])

        # Edge widths
        edges = list(G.edges())
        max_w = max((G[u][v]["weight"] for u, v in edges), default=1)
        edge_widths = [0.3 + 2.5 * (G[u][v]["weight"] / max_w) for u, v in edges]
        edge_colors = []
        for u, v in edges:
            con_node = v if v.startswith("CON:") else u
            if con_node == dom1:
                edge_colors.append(PALETTE["accent"])
            elif con_node == dom2:
                edge_colors.append(PALETTE["orange"])
            else:
                edge_colors.append("#cccccc")

        nx.draw_networkx_nodes(G, pos, nodelist=ca_nodes, node_size=ca_sizes,
                                node_color=PALETTE["secondary"], alpha=0.75,
                                node_shape="s", ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=con_nodes, node_size=con_sizes,
                                node_color=con_colors, alpha=0.85,
                                node_shape="o", ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=edge_widths,
                                edge_color=edge_colors, alpha=0.55, ax=ax)

        # Labels: top-2 CAs (by total value) and top-2 contractors (by name)
        ca_sorted = sorted(ca_total, key=ca_total.get, reverse=True)
        con_sorted = sorted(con_total, key=con_total.get, reverse=True)
        label_nodes = {}
        for n in ca_sorted[:2]:
            label_nodes[n] = n[3:][:18]  # CA names are already names from CAName
        for n in con_sorted[:2]:
            con_id = n[4:]  # strip "CON:" prefix
            label_nodes[n] = con_name.get(con_id, str(con_id))[:16]
        nx.draw_networkx_labels(G, pos, label_nodes, font_size=4.5,
                                 font_color="#1a1a1a", font_weight="bold", ax=ax)

        name = CPV_NAMES.get(sector, f"CPV {sector}")
        c1_obs = sector_c1.get(sector, 0)
        c1_null = sector_null_c1.get(sector, 0)
        ax.set_title(
            f"CPV {sector} — {name}\nC1={c1_obs:.2f} (null={c1_null:.2f})",
            fontsize=8.5, fontweight="bold", pad=8, color="#1a1a1a",
        )

        ax.text(-0.08, 0.5, "Naručitelji", transform=ax.transAxes,
                ha="right", va="center", rotation=90, fontsize=7, color=PALETTE["secondary"])
        ax.text(1.08, 0.5, "Izvođači", transform=ax.transAxes,
                ha="left", va="center", rotation=270, fontsize=7, color="#333")

        ax.set_xlim(-0.15, 1.15)
        ax.axis("off")

    # Legend
    patch_ca = mpatches.Patch(color=PALETTE["secondary"], label="Naručitelj (CA)")
    patch_dom1 = mpatches.Patch(color=PALETTE["accent"], label="Dominantni izvođač (C1)")
    patch_dom2 = mpatches.Patch(color=PALETTE["orange"], label="2. izvođač (C2)")
    patch_rest = mpatches.Patch(color=PALETTE["muted"], label="Ostali izvođači")
    fig.legend(handles=[patch_ca, patch_dom1, patch_dom2, patch_rest],
               loc="lower center", ncol=4, fontsize=9, framealpha=0.9,
               bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout()
    fig.savefig(f"{OUT_DIR}/h1d_sector_bipartite.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    plt.close()
    print("  Saved: h1d_sector_bipartite.png")


# ---------------------------------------------------------------------------
# 2. Ego-networks — H1a
# ---------------------------------------------------------------------------
def viz_ego_networks(df):
    # Find CAs where >80% of spend goes to one contractor
    ca_col = _resolve_ca_col(df)
    con_name = _con_name_map(df)

    captive = []
    for ca, grp in df.groupby(ca_col):
        if grp["ContractorIdentificationNumber"].nunique() < 2:
            continue
        con_vals = grp.groupby("ContractorIdentificationNumber")["TotalValue"].sum()
        total = con_vals.sum()
        if total <= 0:
            continue
        top_share = con_vals.max() / total
        if top_share >= 0.80:
            captive.append({
                "ca": ca,
                "total": total,
                "top_share": top_share,
                "n_contractors": len(con_vals),
                "contractors": con_vals.to_dict(),
            })

    captive.sort(key=lambda x: x["total"], reverse=True)
    captive = captive[:24]  # top 24 by total spend

    cols = 6
    rows = 4
    fig, axes = plt.subplots(rows, cols, figsize=(18, 12), facecolor=PALETTE["bg"])
    fig.suptitle(
        "H1a — Ego-mreže 'zarobljenih' naručitelja (≥80% rashoda jednom izvođaču)\n"
        f"Prikazano top-24 naručitelja po ukupnoj vrijednosti od {len(captive)+ (0 if len(captive) <= 24 else len(captive)-24)} kvalificiranih",
        fontsize=12, fontweight="bold", y=1.01, color="#1a1a1a",
    )

    for idx, ax in enumerate(axes.flat):
        ax.set_facecolor(PALETTE["bg"])
        if idx >= len(captive):
            ax.axis("off")
            continue

        info = captive[idx]
        G = nx.Graph()
        G.add_node("CA", type="ca", label="Naruč.")

        con_dict = info["contractors"]
        total_val = sum(con_dict.values())
        for con_id, val in sorted(con_dict.items(), key=lambda x: x[1], reverse=True):
            G.add_node(con_id, type="contractor", val=val)
            G.add_edge("CA", con_id, weight=val)

        con_nodes = [n for n in G.nodes() if n != "CA"]
        # Layout: CA center, contractors in circle
        pos = {"CA": (0, 0)}
        n = len(con_nodes)
        for i, cn in enumerate(sorted(con_nodes, key=lambda x: -con_dict.get(x, 0))):
            angle = 2 * np.pi * i / max(n, 1)
            pos[cn] = (np.cos(angle) * 0.7, np.sin(angle) * 0.7)

        # Colors and sizes — all contractor sizes proportional to their value share
        dominant_con = max(con_dict, key=con_dict.get) if con_dict else None
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            if node == "CA":
                node_colors.append(PALETTE["secondary"])
                node_sizes.append(250)
            elif node == dominant_con:
                node_colors.append(PALETTE["accent"])
                node_sizes.append(60 + 300 * (con_dict[node] / total_val))
            else:
                node_colors.append(PALETTE["muted"])
                node_sizes.append(30 + 200 * (con_dict[node] / total_val))

        edges = list(G.edges())
        max_w = max((G[u][v]["weight"] for u, v in edges), default=1)
        edge_widths = [0.5 + 3.0 * (G[u][v]["weight"] / max_w) for u, v in edges]
        edge_cols = [PALETTE["accent"] if (u == dominant_con or v == dominant_con)
                     else "#cccccc" for u, v in edges]

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes,
                                node_color=node_colors, alpha=0.85, ax=ax)
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=edge_widths,
                                edge_color=edge_cols, alpha=0.6, ax=ax)

        # Labels: CA name and top-1 contractor name
        labels = {"CA": str(info["ca"])[:18]}
        if dominant_con is not None:
            labels[dominant_con] = con_name.get(dominant_con, str(dominant_con))[:16]
        label_pos = {k: (pos[k][0], pos[k][1] + 0.12) for k in labels}
        nx.draw_networkx_labels(G, label_pos, labels, font_size=4.5,
                                 font_color="#1a1a1a", font_weight="bold", ax=ax)

        ca_short = str(info["ca"])[:22]
        total_m = info["total"] / 1e6
        ax.set_title(
            f"{ca_short}\n{info['top_share']:.0%} → 1 izvođač | €{total_m:.1f}M",
            fontsize=6.5, pad=4, color="#1a1a1a",
        )
        ax.axis("off")
        ax.set_xlim(-1.1, 1.1)
        ax.set_ylim(-1.1, 1.1)

    patch_ca = mpatches.Patch(color=PALETTE["secondary"], label="Naručitelj (CA)")
    patch_dom = mpatches.Patch(color=PALETTE["accent"], label="Dominantni izvođač (>80%)")
    patch_rest = mpatches.Patch(color=PALETTE["muted"], label="Ostali izvođači")
    fig.legend(handles=[patch_ca, patch_dom, patch_rest],
               loc="lower center", ncol=3, fontsize=9, framealpha=0.9,
               bbox_to_anchor=(0.5, -0.02))

    plt.tight_layout()
    fig.savefig(f"{OUT_DIR}/h1a_ego_networks.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    plt.close()
    print("  Saved: h1a_ego_networks.png")


# ---------------------------------------------------------------------------
# 3. Reconnection bipartite graph — H4
# ---------------------------------------------------------------------------
def viz_reconnection(df):
    ca_col = _resolve_ca_col(df)
    con_name = _con_name_map(df)

    date_col = "ContractDate" if "ContractDate" in df.columns else \
               [c for c in df.columns if "date" in c.lower()][0]

    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col], errors="coerce")
    df2["year"] = df2[date_col].dt.year

    df24 = df2[df2["year"] == 2024]
    df25 = df2[df2["year"] == 2025]

    pairs24 = set(zip(df24[ca_col], df24["ContractorIdentificationNumber"]))
    pairs25 = set(zip(df25[ca_col], df25["ContractorIdentificationNumber"]))

    # Score CAs and contractors by reconnection involvement
    ca_recon = {}
    con_recon = {}
    for ca, con in pairs24 & pairs25:
        ca_recon[ca] = ca_recon.get(ca, 0) + 1
        con_recon[con] = con_recon.get(con, 0) + 1

    top_cas = sorted(ca_recon, key=ca_recon.get, reverse=True)[:50]
    top_cons = sorted(con_recon, key=con_recon.get, reverse=True)[:50]

    top_cas_set = set(top_cas)
    top_cons_set = set(top_cons)

    # Build edge lists
    only24 = []
    both = []
    only25 = []

    for ca, con in pairs24:
        if ca in top_cas_set and con in top_cons_set:
            if (ca, con) in pairs25:
                both.append((ca, con))
            else:
                only24.append((ca, con))

    for ca, con in pairs25:
        if ca in top_cas_set and con in top_cons_set:
            if (ca, con) not in pairs24:
                only25.append((ca, con))

    # Build graph
    G = nx.Graph()
    for edges in [only24, both, only25]:
        for ca, con in edges:
            G.add_node(f"CA:{ca}", side="ca")
            G.add_node(f"CON:{con}", side="con")

    # Layout — CAs on left, contractors on right, sorted by reconnection count
    ca_nodes = [n for n in G.nodes() if n.startswith("CA:")]
    con_nodes = [n for n in G.nodes() if n.startswith("CON:")]

    ca_nodes_sorted = sorted(ca_nodes, key=lambda n: -ca_recon.get(n[3:], 0))
    con_nodes_sorted = sorted(con_nodes, key=lambda n: -con_recon.get(n[4:], 0))

    pos = {}
    for i, n in enumerate(ca_nodes_sorted):
        pos[n] = (0.0, i / max(len(ca_nodes_sorted) - 1, 1))
    for i, n in enumerate(con_nodes_sorted):
        pos[n] = (1.0, i / max(len(con_nodes_sorted) - 1, 1))

    fig, ax = plt.subplots(figsize=(12, 10), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])

    # Node sizes
    max_ca = max(ca_recon.values()) if ca_recon else 1
    max_con = max(con_recon.values()) if con_recon else 1
    ca_sizes = [40 + 150 * (ca_recon.get(n[3:], 0) / max_ca) for n in ca_nodes_sorted]
    con_sizes = [40 + 150 * (con_recon.get(n[4:], 0) / max_con) for n in con_nodes_sorted]

    nx.draw_networkx_nodes(G, pos, nodelist=ca_nodes_sorted, node_size=ca_sizes,
                            node_color=PALETTE["secondary"], alpha=0.85, node_shape="s", ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=con_nodes_sorted, node_size=con_sizes,
                            node_color="#5d6d7e", alpha=0.85, node_shape="o", ax=ax)

    # Labels: top-3 CAs and top-3 contractors by reconnection count
    label_nodes = {}
    for n in ca_nodes_sorted[:3]:
        label_nodes[n] = n[3:][:18]  # CA names are already from CAName
    for n in con_nodes_sorted[:3]:
        con_id = n[4:]  # strip "CON:" prefix
        label_nodes[n] = con_name.get(con_id, str(con_id))[:16]
    label_pos = {k: (pos[k][0] + (0.04 if k.startswith("CA:") else -0.04),
                     pos[k][1]) for k in label_nodes}
    nx.draw_networkx_labels(G, label_pos, label_nodes, font_size=5.5,
                             font_color="#1a1a1a", font_weight="bold", ax=ax)

    # Draw edges by type
    def draw_edges(edge_list, color, alpha, lw, label, zorder=1):
        drawn = [(f"CA:{ca}", f"CON:{con}") for ca, con in edge_list
                 if f"CA:{ca}" in pos and f"CON:{con}" in pos]
        if drawn:
            nx.draw_networkx_edges(G, pos, edgelist=drawn, edge_color=color,
                                    alpha=alpha, width=lw, ax=ax)

    draw_edges(only24, "#5dade2", 0.25, 0.6, "Samo 2024")
    draw_edges(both, PALETTE["green"], 0.55, 1.2, "Oba (2024 i 2025)")
    draw_edges(only25, PALETTE["orange"], 0.25, 0.6, "Samo 2025")

    ax.set_title(
        "H4 — Reconnection bipartitni graf\n"
        f"Top-{len(ca_nodes)} naručitelja × top-{len(con_nodes)} izvođača po stopi ponovnog spajanja",
        fontsize=11, fontweight="bold", pad=12, color="#1a1a1a",
    )
    ax.text(-0.06, 0.5, "Naručitelji (CA)", transform=ax.transAxes,
            ha="right", va="center", rotation=90, fontsize=9, color=PALETTE["secondary"])
    ax.text(1.06, 0.5, "Izvođači", transform=ax.transAxes,
            ha="left", va="center", rotation=270, fontsize=9, color="#333")

    # Annotation
    ax.text(0.5, -0.04,
            f"Zeleni rubovi = perzistentni parovi (oba 2024 i 2025) = {len(both)} parova\n"
            f"Opažena stopa reconnection: 54,6% naspram null 5,9% (z=745, p=0.000)",
            transform=ax.transAxes, ha="center", va="top", fontsize=9,
            color="#333", style="italic")

    l1 = mlines.Line2D([], [], color=PALETTE["green"], linewidth=2, label=f"Oba — perzistentni ({len(both)})")
    l2 = mlines.Line2D([], [], color="#5dade2", linewidth=1, alpha=0.6, label=f"Samo 2024 ({len(only24)})")
    l3 = mlines.Line2D([], [], color=PALETTE["orange"], linewidth=1, alpha=0.6, label=f"Samo 2025 ({len(only25)})")
    p1 = mpatches.Patch(color=PALETTE["secondary"], label="Naručitelj (CA)")
    p2 = mpatches.Patch(color="#5d6d7e", label="Izvođač")
    ax.legend(handles=[l1, l2, l3, p1, p2], loc="upper right", fontsize=8.5,
              framealpha=0.9, edgecolor="#ccc")

    ax.set_xlim(-0.12, 1.12)
    ax.axis("off")
    plt.tight_layout()
    fig.savefig(f"{OUT_DIR}/h4_reconnection_bipartite.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    plt.close()
    print("  Saved: h4_reconnection_bipartite.png")


# ---------------------------------------------------------------------------
# 4. Quarterly bar chart — H3
# ---------------------------------------------------------------------------
def viz_h3_quarterly():
    data = {
        2024: {
            "Q1": {"New": 38263, "Repeat": 11962, "Value": 578.44},
            "Q2": {"New": 20773, "Repeat": 12109, "Value": 1116.04},
            "Q3": {"New": 15789, "Repeat": 12879, "Value": 1880.41},
            "Q4": {"New": 17741, "Repeat": 18059, "Value": 2441.28},
        },
        2025: {
            "Q1": {"New": 20974, "Repeat": 39470, "Value": 1916.27},
            "Q2": {"New": 14128, "Repeat": 25668, "Value": 2134.17},
            "Q3": {"New": 11100, "Repeat": 20761, "Value": 2027.30},
            "Q4": {"New": 12541, "Repeat": 26617, "Value": 1861.36},
        },
    }

    fig, axes = plt.subplots(1, 3, figsize=(16, 6), facecolor=PALETTE["bg"])
    fig.suptitle(
        "H3 — Kvartalna dinamika ugovora (2024 vs 2025)",
        fontsize=13, fontweight="bold", y=1.02, color="#1a1a1a",
    )

    quarters = ["Q1", "Q2", "Q3", "Q4"]
    x = np.arange(4)
    w = 0.35

    colors_new = [PALETTE["primary"], "#a9cce3"]
    colors_rep = [PALETTE["accent"], "#f1948a"]

    # Panel 1: Novi bridovi
    ax = axes[0]
    ax.set_facecolor(PALETTE["bg"])
    for i, (year, color) in enumerate(zip([2024, 2025], colors_new)):
        vals = [data[year][q]["New"] for q in quarters]
        bars = ax.bar(x + i * w, vals, w, label=str(year), color=color, edgecolor="white", linewidth=0.5)
    ax.axhline(y=sum(data[2024][q]["New"] for q in quarters) / 4,
               color=PALETTE["primary"], linestyle="--", alpha=0.5, linewidth=1.2,
               label="2024 prosjek/kvartalu")
    ax.axhline(y=sum(data[2025][q]["New"] for q in quarters) / 4,
               color="#a9cce3", linestyle="--", alpha=0.5, linewidth=1.2,
               label="2025 prosjek/kvartalu")
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels(quarters)
    ax.set_title("Novi bridovi (novi CA–izvođač parovi)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Broj ugovora")
    ax.legend(fontsize=8)
    ax.yaxis.grid(True, color=PALETTE["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.annotate("Q4 < prosjeka\n(odbijeno)", xy=(3 + w / 2, data[2024]["Q4"]["New"]),
                xytext=(2.5, 30000), fontsize=8, color=PALETTE["accent"],
                arrowprops=dict(arrowstyle="->", color=PALETTE["accent"], lw=1))

    # Panel 2: Repeat vs New stacked
    ax = axes[1]
    ax.set_facecolor(PALETTE["bg"])
    for i, (year, c_new, c_rep) in enumerate(zip([2024, 2025], colors_new, colors_rep)):
        new_vals = [data[year][q]["New"] for q in quarters]
        rep_vals = [data[year][q]["Repeat"] for q in quarters]
        bars_new = ax.bar(x + i * w, new_vals, w, label=f"{year} Novi" if i == 0 else None,
                          color=c_new, edgecolor="white", linewidth=0.5)
        bars_rep = ax.bar(x + i * w, rep_vals, w, bottom=new_vals,
                          label=f"{year} Ponovni" if i == 0 else None,
                          color=c_rep, edgecolor="white", linewidth=0.5)
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels(quarters)
    ax.set_title("Novi vs ponovni bridovi (stacked)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Broj ugovora")

    patch_new24 = mpatches.Patch(color=colors_new[0], label="2024 Novi")
    patch_rep24 = mpatches.Patch(color=colors_rep[0], label="2024 Ponovni")
    patch_new25 = mpatches.Patch(color=colors_new[1], label="2025 Novi")
    patch_rep25 = mpatches.Patch(color=colors_rep[1], label="2025 Ponovni")
    ax.legend(handles=[patch_new24, patch_rep24, patch_new25, patch_rep25], fontsize=7.5)
    ax.yaxis.grid(True, color=PALETTE["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    # Panel 3: Value per quarter
    ax = axes[2]
    ax.set_facecolor(PALETTE["bg"])
    colors_val = [PALETTE["primary"], "#a9cce3"]
    for i, (year, color) in enumerate(zip([2024, 2025], colors_val)):
        vals = [data[year][q]["Value"] for q in quarters]
        ax.bar(x + i * w, vals, w, label=str(year), color=color, edgecolor="white", linewidth=0.5)
    ax.set_xticks(x + w / 2)
    ax.set_xticklabels(quarters)
    ax.set_title("Vrijednost ugovora po kvartalu (M€)", fontsize=10, fontweight="bold")
    ax.set_ylabel("Vrijednost (M€)")
    ax.legend(fontsize=8)
    ax.yaxis.grid(True, color=PALETTE["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.annotate("Q4 2024:\nvrijednost visoka\nali ponovni bridovi\ndominiraju",
                xy=(3 + 0 * w, data[2024]["Q4"]["Value"]),
                xytext=(1.5, 2200), fontsize=7.5, color="#555",
                arrowprops=dict(arrowstyle="->", color="#888", lw=0.8))

    plt.tight_layout()
    fig.savefig(f"{OUT_DIR}/h3_quarterly_series.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    plt.close()
    print("  Saved: h3_quarterly_series.png")


# ---------------------------------------------------------------------------
# 5. McCrary histogram — H9
# ---------------------------------------------------------------------------
def viz_mccrary(df):
    T_goods = 26540

    # Goods/services contracts (ContractTypeId 1 or 2)
    type_col = "ContractTypeId" if "ContractTypeId" in df.columns else None
    if type_col:
        gs = df[df[type_col].isin([1, 2])].copy()
    else:
        gs = df.copy()

    gs = gs.dropna(subset=["TotalValue"])
    gs = gs[gs["TotalValue"] > 0]

    # Window: 0.1 × T to 5 × T
    lo, hi = T_goods * 0.1, T_goods * 5
    window = gs[(gs["TotalValue"] >= lo) & (gs["TotalValue"] <= hi)].copy()

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=PALETTE["bg"])
    ax.set_facecolor(PALETTE["bg"])

    # Histogram with fine bins in log space
    bins = np.linspace(lo, hi, 120)
    below = window[window["TotalValue"] < T_goods]["TotalValue"]
    above = window[window["TotalValue"] >= T_goods]["TotalValue"]

    ax.hist(below, bins=bins, color=PALETTE["accent"], alpha=0.75, label="Ispod praga")
    ax.hist(above, bins=bins, color=PALETTE["secondary"], alpha=0.75, label="Iznad praga")

    # Threshold line
    ax.axvline(x=T_goods, color="#1a1a1a", linestyle="--", linewidth=2,
               label=f"Prag = €{T_goods:,}")

    # Annotation for density ratio
    below_half_t = window[(window["TotalValue"] >= T_goods / 2) & (window["TotalValue"] < T_goods)]
    above_t_2t = window[(window["TotalValue"] > T_goods) & (window["TotalValue"] <= 2 * T_goods)]

    ax.annotate(
        f"Omjer gustoće\n[T/2, T) / (T, 2T]  =  2,70×\n"
        f"n ispod = {len(below_half_t):,}    n iznad = {len(above_t_2t):,}\n"
        f"Signal: nagomilavanje tik ispod praga",
        xy=(T_goods, ax.get_ylim()[1] * 0.6 if ax.get_ylim()[1] > 0 else 500),
        xytext=(T_goods * 1.4, ax.get_ylim()[1] * 0.7 if ax.get_ylim()[1] > 0 else 700),
        fontsize=10, color="#1a1a1a",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff3cd", edgecolor="#f39c12", alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#e67e22", lw=1.5),
    )

    # Fix annotation position after we know ylims
    ax.relim()
    ax.autoscale_view()
    ylim = ax.get_ylim()

    ax.set_xlabel("Vrijednost ugovora (€)", fontsize=11)
    ax.set_ylabel("Broj ugovora", fontsize=11)
    ax.set_title(
        "H9 — McCrary test diskontinuiteta gustoće\nRoba/usluge (ContractTypeId 1,2) — prag €26.540",
        fontsize=12, fontweight="bold", color="#1a1a1a",
    )
    ax.legend(fontsize=10, framealpha=0.9)
    ax.yaxis.grid(True, color=PALETTE["grid"], linewidth=0.7)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    # X ticks: mark T, T/2, 2T
    xticks = [T_goods * 0.5, T_goods, T_goods * 2, T_goods * 3, T_goods * 4]
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"€{int(v):,}" for v in xticks], rotation=20, ha="right")

    plt.tight_layout()
    fig.savefig(f"{OUT_DIR}/h9_mccrary_histogram.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    plt.close()
    print("  Saved: h9_mccrary_histogram.png")


# ---------------------------------------------------------------------------
# 6. Swim-lane rotation — H8
# ---------------------------------------------------------------------------
def viz_swimlane(df):
    ca_col = _resolve_ca_col(df)
    con_name = _con_name_map(df)

    date_col = "ContractDate" if "ContractDate" in df.columns else \
               [c for c in df.columns if "date" in c.lower()][0]

    df2 = df.copy()
    df2[date_col] = pd.to_datetime(df2[date_col], errors="coerce")
    df2 = df2.dropna(subset=[date_col])
    df2["cpv_div"] = df2["cpv_division"] if "cpv_division" in df2.columns else df2["CPVCode"].astype(str).str[:2].astype(int, errors="ignore")

    # Find CPV-45 (construction) cells with most alternation signal
    # Use cells with ≥8 contracts, ≥3 contractors, in CPV 45
    sector = 45
    sub = df2[df2["cpv_division"] == sector].copy()

    best_cells = []
    for (ca, cpv), grp in sub.groupby([ca_col, "cpv_division"]):
        grp_sorted = grp.sort_values(date_col)
        cons = grp_sorted["ContractorIdentificationNumber"].tolist()
        if len(cons) < 8 or len(set(cons)) < 3:
            continue
        # Alternation rate: fraction of consecutive pairs that differ
        alt = sum(1 for a, b in zip(cons, cons[1:]) if a != b) / (len(cons) - 1)
        best_cells.append({
            "ca": ca, "grp": grp_sorted, "alt": alt, "n": len(cons),
            "n_con": len(set(cons)),
        })

    best_cells.sort(key=lambda x: x["alt"], reverse=True)

    # Pick top-3 with highest alternation (and show 1 with low alt for contrast)
    high_alt = best_cells[:3]
    low_alt = [c for c in best_cells if c["alt"] < 0.25 and c["n"] >= 10][:1]
    to_plot = high_alt + low_alt
    if not to_plot:
        to_plot = best_cells[:4]

    n_panels = len(to_plot)
    if n_panels == 0:
        print("  SKIP: no suitable cells for swim-lane")
        return

    fig, axes = plt.subplots(1, n_panels, figsize=(5 * n_panels, 8), facecolor=PALETTE["bg"])
    if n_panels == 1:
        axes = [axes]
    fig.suptitle(
        "H8 — Swim-lane dijagram: kronološki redoslijed ugovora\npo izvođaču unutar CA–CPV ćelije (CPV 45 Građevina)",
        fontsize=11, fontweight="bold", y=1.03, color="#1a1a1a",
    )

    contractor_palettes = [
        "#1a5276", "#e74c3c", "#27ae60", "#8e44ad", "#d35400",
        "#1abc9c", "#c0392b", "#2980b9", "#f39c12", "#7f8c8d",
    ]

    for ax, info in zip(axes, to_plot):
        ax.set_facecolor(PALETTE["bg"])
        grp = info["grp"].reset_index(drop=True)
        cons = grp["ContractorIdentificationNumber"].tolist()
        dates = grp[date_col].tolist()

        unique_cons = list(dict.fromkeys(cons))  # preserve order of first appearance
        con_y = {c: i for i, c in enumerate(unique_cons)}
        colors = {c: contractor_palettes[i % len(contractor_palettes)]
                  for i, c in enumerate(unique_cons)}

        for j, (con, date, val) in enumerate(zip(cons, dates, grp["TotalValue"].tolist())):
            y = con_y[con]
            size = 30 + min(300, (float(val) / 50000 * 100) if pd.notna(val) else 30)
            ax.scatter(date, y, s=size, color=colors[con], zorder=3, alpha=0.85,
                       edgecolors="white", linewidths=0.5)

        # Connect dots per contractor with thin lines
        for con in unique_cons:
            sub_grp = grp[grp["ContractorIdentificationNumber"] == con].sort_values(date_col)
            if len(sub_grp) > 1:
                ax.plot(sub_grp[date_col], [con_y[con]] * len(sub_grp),
                        color=colors[con], alpha=0.3, linewidth=0.8, zorder=1)

        ax.set_yticks(range(len(unique_cons)))
        # Use contractor names as y-axis labels
        con_labels = [con_name.get(c, str(c))[:18] for c in unique_cons]
        ax.set_yticklabels(con_labels, fontsize=7)
        ax.tick_params(axis="x", rotation=30, labelsize=7)
        ax.set_ylabel("Izvođač", fontsize=8, color=PALETTE["secondary"])

        ca_short = str(info["ca"])[:30]
        ax.set_title(
            f"{ca_short}\n"
            f"Alt.={info['alt']:.2f} | n={info['n']} ugovora | {info['n_con']} izvođača",
            fontsize=8, fontweight="bold" if info["alt"] > 0.5 else "normal", pad=6,
        )
        ax.yaxis.grid(True, color=PALETTE["grid"], linewidth=0.5)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    # Comprehensive legend explaining the swim-lane metaphor
    fig.text(0.5, -0.06,
             'Swim-lane dijagram: svaki red ("staza") = jedan izvođač. Točke = ugovori (veličina ≈ vrijednost ugovora).\n'
             'Vodoravna os = datum potpisivanja. Vertikalno skakanje = izmjena izvođača (alternacija).\n'
             'Visoka alternacija (lijevi paneli) = izvođači se izmjenjuju; niska (desno) = isti izvođač pobjeđuje uzastopno.\n'
             'Srednja alternacijska stopa u cijelom datasetu: −0.021 (isti izvođači dominiraju — H8 odbijeno).',
             ha="center", fontsize=8, color="#333", style="italic")

    plt.tight_layout()
    fig.savefig(f"{OUT_DIR}/h8_swimlane_rotation.png", dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    plt.close()
    print("  Saved: h8_swimlane_rotation.png")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    print("Loading data ...")
    df = load()
    print(f"  Loaded {len(df):,} rows")

    print("\n[1/6] Per-sector bipartite graph (H1d) ...")
    viz_sector_bipartite(df)

    print("[2/6] Ego-networks captured CAs (H1a) ...")
    viz_ego_networks(df)

    print("[3/6] Reconnection bipartite graph (H4) ...")
    viz_reconnection(df)

    print("[4/6] Quarterly bar chart (H3) ...")
    viz_h3_quarterly()

    print("[5/6] McCrary histogram (H9) ...")
    viz_mccrary(df)

    print("[6/6] Swim-lane rotation (H8) ...")
    viz_swimlane(df)

    print("\nDone. All files in results/visualizations/")


if __name__ == "__main__":
    main()
