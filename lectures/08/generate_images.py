import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import os
import powerlaw
from collections import Counter

# Create images directory if it doesn't exist
os.makedirs('images', exist_ok=True)

# Set random seed for reproducibility
np.random.seed(42)

def save_figure(filename, title=None, figsize=(10, 8), dpi=120):
    """Save figure with consistent styling."""
    if title:
        plt.title(title, fontsize=16)

    plt.tight_layout()
    plt.savefig(f'images/{filename}', dpi=dpi)
    plt.close()

def degree_probability(degrees):
    """Return sorted degree values and their empirical probabilities."""
    counts = Counter(degrees)
    k_values = np.array(sorted(counts))
    probabilities = np.array([counts[k] / len(degrees) for k in k_values])
    return k_values, probabilities

def generate_ba_networks():
    """Generate Barabási-Albert networks with different parameters."""
    print("Generating BA network visualizations...")

    # Parameters
    n = 100  # Number of nodes
    m_values = [1, 2, 3, 5]  # Different m values for comparison

    # Create a figure with multiple subplots
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()

    for i, m in enumerate(m_values):
        # Generate BA network
        G = nx.barabasi_albert_graph(n, m)

        # Compute positions for nodes (spring layout for nicer visualization)
        pos = nx.spring_layout(G, seed=42)

        # Get node degrees for sizing
        degrees = dict(nx.degree(G))
        node_sizes = [20 + 10 * degrees[node] for node in G.nodes()]

        # Draw network in the corresponding subplot
        ax = axes[i]
        nx.draw_networkx(
            G,
            pos=pos,
            ax=ax,
            node_size=node_sizes,
            with_labels=False,
            node_color='lightblue',
            edge_color='gray',
            alpha=0.8
        )
        ax.set_title(f"BA Model: m={m}")
        ax.axis('off')

    plt.tight_layout()
    plt.savefig('images/ba_networks_comparison.png', dpi=120)
    plt.close()

    # Create a larger visualization of a single BA network for detail
    fig, ax = plt.subplots(figsize=(10, 10))
    G_detailed = nx.barabasi_albert_graph(n=150, m=2)
    pos = nx.spring_layout(G_detailed, seed=42)

    # Get node degrees for sizing and coloring
    degrees = dict(nx.degree(G_detailed))
    node_sizes = [20 + 15 * degrees[node] for node in G_detailed.nodes()]
    node_colors = [degrees[node] for node in G_detailed.nodes()]

    nx.draw_networkx(
        G_detailed,
        pos=pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        with_labels=False,
        edge_color='gray',
        alpha=0.7,
        cmap=plt.cm.viridis
    )

    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=min(degrees.values()), vmax=max(degrees.values())))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Node Degree')

    plt.title("Barabási-Albert Model (n=150, m=2)", fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('images/ba_network_detailed.png', dpi=120)
    plt.close()

def generate_degree_distributions():
    """Generate and visualize degree distributions for different network models."""
    print("Generating degree distribution visualizations...")

    # Larger network sizes for smoother distributions
    n = 10000  # Increased from 5000

    # Create three different networks
    ba_graph = nx.barabasi_albert_graph(n=n, m=2, seed=42)  # Scale-free
    er_graph = nx.erdos_renyi_graph(n=n, p=4/n, seed=42)    # Random
    ws_graph = nx.watts_strogatz_graph(n=n, k=4, p=0.1, seed=42)  # Small-world

    # Extract degree distributions
    ba_degrees = [d for _, d in ba_graph.degree()]
    er_degrees = [d for _, d in er_graph.degree()]
    ws_degrees = [d for _, d in ws_graph.degree()]

    # Create two separate figures for better clarity
    # Figure 1: Linear scale comparison
    plt.figure(figsize=(10, 6))
    plt.hist(ba_degrees, bins=30, alpha=0.7, label='BA (Scale-Free)')
    plt.hist(er_degrees, bins=30, alpha=0.7, label='ER (Random)')
    plt.hist(ws_degrees, bins=30, alpha=0.7, label='WS (Small-World)')
    plt.xlabel('Degree (k)', fontsize=14)
    plt.ylabel('Count', fontsize=14)
    plt.title('Degree Distributions (Linear Scale)', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('images/degree_distributions_linear.png', dpi=120)
    plt.close()

    # Figure 2: Log-log plot using empirical P(k) for each integer degree
    fig, ax = plt.subplots(figsize=(10, 6))

    ba_k, ba_p = degree_probability(ba_degrees)
    er_k, er_p = degree_probability(er_degrees)
    ws_k, ws_p = degree_probability(ws_degrees)

    # Create log-log plots with larger markers and clear lines
    ax.loglog(ba_k, ba_p, 'o-', color='#3274A1', linewidth=2,
              markersize=8, label='BA (Scale-Free)')
    ax.loglog(er_k, er_p, 'o-', color='#E1812C', linewidth=2,
              markersize=8, label='ER (Random)')
    ax.loglog(ws_k, ws_p, 'o-', color='#3A923A', linewidth=2,
              markersize=8, label='WS (Small-World)')

    # Draw a reference power-law line
    # Fit the BA network to find alpha
    fit = powerlaw.Fit(ba_degrees, discrete=True, verbose=False)
    alpha = fit.alpha

    # Plot a reference power-law line
    max_degree = max(ba_degrees)
    k_range = np.logspace(np.log10(2), np.log10(max_degree/2), 10)
    # Adjust the normalization constant to match the BA data
    norm_const = ba_p[np.argmin(np.abs(ba_k - 5))] * (5**alpha)
    power_law = norm_const * k_range**(-alpha)

    ax.loglog(k_range, power_law, 'r--', linewidth=2.5,
              label=f'Reference: k^(-{alpha:.2f})')

    # Improve readability with grid, labels and annotations
    ax.grid(True, which="both", ls="-", alpha=0.2)
    ax.set_xlabel('Degree (k)', fontsize=14)
    ax.set_ylabel('Probability P(k)', fontsize=14)
    ax.set_title('Degree Distributions (Log-Log Scale)', fontsize=16)
    ax.legend(fontsize=12, loc='lower left')

    # Add text annotation explaining power-law
    ax.text(0.65, 0.95, 'Power-law distribution:\nP(k) $\\propto$ k$^{-\\alpha}$',
            transform=ax.transAxes, fontsize=12,
            bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))

    plt.tight_layout()
    plt.savefig('images/degree_distributions.png', dpi=120)
    plt.close()

    # Create another clear power-law visualization with fit
    plt.figure(figsize=(10, 8))

    # Generate a larger BA network for clearer distribution
    large_ba = nx.barabasi_albert_graph(n=10000, m=2)
    degrees = [d for _, d in large_ba.degree()]

    # Compute the empirical PDF (probability density function)
    hist, bin_edges = np.histogram(degrees,
                                  bins=np.logspace(np.log10(min(degrees)),
                                                  np.log10(max(degrees)), 20),
                                  density=True)
    centers = (bin_edges[1:] + bin_edges[:-1]) / 2

    # Plot the PDF
    plt.loglog(centers, hist, 'o', markersize=10, color='#3274A1',
               label='Empirical data')

    # Fit and plot the power-law line
    fit = powerlaw.Fit(degrees)
    alpha = fit.alpha
    xmin = fit.xmin

    # Generate the power-law fit line
    x = np.logspace(np.log10(xmin), np.log10(max(degrees)), 50)
    y = x**(-alpha) * x[0]**(alpha) * hist[np.argmin(np.abs(centers - x[0]))]

    plt.loglog(x, y, 'r-', linewidth=3,
               label=f'Power law ($\\alpha$ = {alpha:.2f})')

    plt.xlabel('Degree (k)', fontsize=14)
    plt.ylabel('Probability P(k)', fontsize=14)
    plt.title('Scale-Free Degree Distribution: P(k) ~ k^(-α)', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3, which='both')

    # Add annotation explaining key characteristics
    plt.text(0.02, 0.2,
             'Key characteristics:\n' +
             '• Straight line in log-log plot\n' +
             '• Heavy tail (many low-degree nodes,\n  few high-degree hubs)\n' +
             '• Scale invariance',
             transform=plt.gca().transAxes, fontsize=12,
             bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))

    plt.tight_layout()
    plt.savefig('images/power_law_distribution.png', dpi=120)
    plt.close()

def generate_preferential_attachment_visual():
    """Create a visual illustration of preferential attachment process."""
    print("Generating preferential attachment illustration...")

    # Create a figure with 4 evolving networks
    fig = plt.figure(figsize=(13, 11))

    # Create a grid layout with more space for annotation
    grid = plt.GridSpec(3, 2, height_ratios=[1, 1, 0.2], hspace=0.3, wspace=0.3)

    # Create axes for the 4 network panels
    axes = [
        plt.subplot(grid[0, 0]),
        plt.subplot(grid[0, 1]),
        plt.subplot(grid[1, 0]),
        plt.subplot(grid[1, 1])
    ]

    # Create a clearer color map for node ID ages
    age_cmap = plt.cm.viridis

    # Start with a small network (2 nodes)
    G = nx.Graph()
    G.add_node(0)
    G.add_node(1)
    G.add_edge(0, 1)

    stages = [2, 6, 10, 20]  # Number of nodes at each stage

    # Create initial node positions - more spread out for clarity
    pos = {0: np.array([-0.5, 0]), 1: np.array([0.5, 0])}

    # Create a dictionary to store node creation times
    node_ages = {0: 0, 1: 0}

    # In the first panel, draw the initial graph
    nx.draw_networkx(
        G,
        pos=pos,
        ax=axes[0],
        node_size=600,
        node_color=[age_cmap(0), age_cmap(0)],
        edge_color='black',
        width=2.5,
        with_labels=True,
        font_weight='bold',
        font_size=10
    )
    axes[0].set_title("Initial Network (n=2)", fontsize=14)
    axes[0].axis('off')

    # Create a new position dictionary that will be updated with new nodes
    full_pos = pos.copy()

    # Add nodes using preferential attachment for the next panels
    new_node_id = 2
    current_time = 1

    for i, n_nodes in enumerate(stages[1:], 1):
        current_time += 1
        # Add nodes until we reach the desired number
        while len(G.nodes) < n_nodes:
            # Calculate connection probabilities based on current degrees
            degrees = dict(G.degree())
            total_edges = sum(degrees.values())
            probabilities = [degrees[node]/total_edges for node in G.nodes]

            # Choose nodes to connect to based on their degree
            # For simplicity, connect to exactly 1 node for clarity when m=1
            num_connections = min(2, len(G.nodes))
            targets = np.random.choice(
                list(G.nodes),
                size=num_connections,
                replace=False,
                p=probabilities
            )

            # Add the new node and edges
            G.add_node(new_node_id)
            node_ages[new_node_id] = current_time  # Track when this node was created

            for target in targets:
                G.add_edge(new_node_id, target)

            # Add new position - more strategic positioning
            angle = 2 * np.pi * np.random.random()
            radius = 0.8 + 0.2 * np.random.random()
            full_pos[new_node_id] = np.array([radius * np.cos(angle), radius * np.sin(angle)])

            new_node_id += 1

        # After adding nodes, update layout for better visualization
        # Use stronger repulsion for clearer structure
        full_pos = nx.spring_layout(
            G,
            pos=full_pos,
            fixed=list(pos.keys()),
            k=1/np.sqrt(len(G.nodes())),
            iterations=50,
            seed=42
        )

        # Normalize node ages for coloring
        max_time = max(node_ages.values())
        normalized_ages = {node: node_ages[node]/max_time for node in G.nodes()}

        # Draw the current state of the network
        degrees = dict(G.degree())

        # Make node sizes proportional to their degree
        node_sizes = [300 + 200 * degrees[node] for node in G.nodes()]

        # Color nodes based on when they were added - older nodes are darker
        node_colors = [age_cmap(1 - normalized_ages[node]) for node in G.nodes()]

        # Make edges thicker based on node importance
        edge_weights = []
        for u, v in G.edges():
            weight = 1 + 0.5 * (degrees[u] + degrees[v]) / max(1, max(degrees.values()))
            edge_weights.append(weight)

        nx.draw_networkx(
            G,
            pos=full_pos,
            ax=axes[i],
            node_size=node_sizes,
            node_color=node_colors,
            edge_color='gray',
            width=edge_weights,
            with_labels=True,
            font_size=9,
            font_weight='bold',
            font_color='black',
            alpha=0.9
        )

        axes[i].set_title(f"Network Growth (n={len(G.nodes)})", fontsize=14)
        axes[i].axis('off')

    # Create a new axis for the colorbar at the bottom
    cax = plt.subplot(grid[2, :])
    sm = plt.cm.ScalarMappable(cmap=age_cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, cax=cax, orientation='horizontal')
    cbar.set_label('Node Age (Darker = Older Nodes)', fontsize=12)

    # Add an explanation annotation at the very bottom
    plt.figtext(
        0.5, 0.01,
        "Preferential Attachment: New nodes connect to existing nodes with probability proportional to their degree.\n"
        "Node size represents degree, node color represents age, and edge thickness represents connection importance.",
        ha='center',
        fontsize=12,
        bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5')
    )

    plt.savefig('images/preferential_attachment.png', dpi=150)
    plt.close()

def generate_hub_and_authority_image():
    """Visualize the concept of hubs and authorities in scale-free networks."""
    print("Generating hub and authority visualization...")

    # Create a scale-free network
    G = nx.barabasi_albert_graph(n=50, m=2)

    # Get degree for node sizing
    degrees = dict(nx.degree(G))

    # Calculate centrality metrics
    betweenness = nx.betweenness_centrality(G)

    # Layout for visualization
    pos = nx.spring_layout(G, seed=42)

    # Draw the network
    fig, ax = plt.subplots(figsize=(12, 8))

    # Size nodes by degree
    node_sizes = [100 + 50 * degrees[node] for node in G.nodes()]

    # Color nodes by betweenness centrality
    node_colors = [betweenness[node] for node in G.nodes()]

    # Draw network
    nx.draw_networkx(
        G,
        pos=pos,
        ax=ax,
        node_size=node_sizes,
        node_color=node_colors,
        with_labels=False,
        edge_color='lightgray',
        cmap=plt.cm.YlOrRd
    )

    # Highlight top 3 hubs (highest degree nodes)
    hub_nodes = sorted(degrees, key=degrees.get, reverse=True)[:3]
    nx.draw_networkx_nodes(
        G,
        pos=pos,
        ax=ax,
        nodelist=hub_nodes,
        node_size=[250 + 50 * degrees[node] for node in hub_nodes],
        node_color='blue',
        label='Hubs'
    )

    # Add legend
    ax.legend(fontsize=10)

    # Add colorbar for betweenness centrality
    sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd,
                              norm=plt.Normalize(vmin=min(betweenness.values()),
                                                vmax=max(betweenness.values())))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Betweenness Centrality')

    plt.title("Hubs in Scale-Free Networks", fontsize=16)
    ax.axis('off')
    plt.tight_layout()
    plt.savefig('images/network_hubs.png', dpi=120)
    plt.close()

def generate_network_attack_comparison():
    """Create visualization comparing random vs targeted attacks on scale-free networks."""
    print("Generating network attack visualization...")

    # Initialize network
    n = 200
    G = nx.barabasi_albert_graph(n=n, m=2)

    # Create a copy for the two types of attacks
    G_random = G.copy()
    G_targeted = G.copy()

    # Set up metrics tracking
    random_gc_sizes = []
    targeted_gc_sizes = []

    # Function to get largest component size ratio
    def largest_cc_size_ratio(g):
        if len(g) == 0:
            return 0
        components = list(nx.connected_components(g))
        if not components:
            return 0
        return len(max(components, key=len)) / n

    # Track initial size
    random_gc_sizes.append(largest_cc_size_ratio(G_random))
    targeted_gc_sizes.append(largest_cc_size_ratio(G_targeted))

    # Number of nodes to remove
    removal_steps = 20
    nodes_per_step = n // removal_steps

    # Simulate random removal
    for i in range(removal_steps):
        # Choose random nodes
        if len(G_random) < nodes_per_step:
            break
        nodes_to_remove = np.random.choice(list(G_random.nodes()), nodes_per_step, replace=False)
        G_random.remove_nodes_from(nodes_to_remove)
        random_gc_sizes.append(largest_cc_size_ratio(G_random))

    # Simulate targeted removal (highest degree nodes first)
    for i in range(removal_steps):
        if len(G_targeted) < nodes_per_step:
            break
        # Get highest degree nodes
        degrees = dict(G_targeted.degree())
        nodes_to_remove = sorted(degrees, key=degrees.get, reverse=True)[:nodes_per_step]
        G_targeted.remove_nodes_from(nodes_to_remove)
        targeted_gc_sizes.append(largest_cc_size_ratio(G_targeted))

    # Ensure same length
    steps = min(len(random_gc_sizes), len(targeted_gc_sizes))
    random_gc_sizes = random_gc_sizes[:steps]
    targeted_gc_sizes = targeted_gc_sizes[:steps]

    # Plotting
    plt.figure(figsize=(10, 6))
    x = np.linspace(0, 1, len(random_gc_sizes))

    plt.plot(x, random_gc_sizes, 'bo-', label='Random Failures', linewidth=2, markersize=8)
    plt.plot(x, targeted_gc_sizes, 'ro-', label='Targeted Attacks', linewidth=2, markersize=8)

    plt.xlabel('Fraction of Nodes Removed', fontsize=14)
    plt.ylabel('Relative Size of Giant Component', fontsize=14)
    plt.title('Scale-Free Network Resilience: Random vs. Targeted Attacks', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('images/network_attacks.png', dpi=120)
    plt.close()

def generate_real_world_examples():
    """Create a visual showing examples of real-world scale-free networks."""
    print("Generating real-world examples visualization...")

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    titles = [
        "Internet Network",
        "Protein-Protein Interaction Network",
        "Citation Network",
        "Social Media Network"
    ]

    # For each example, create a scale-free network with slightly different parameters
    for i, (ax, title) in enumerate(zip(axes, titles)):
        # Adjust parameters to create visual variety
        n = 100 + i * 20  # Varying number of nodes
        m = max(1, i)     # Varying m parameter

        # Create network
        G = nx.barabasi_albert_graph(n=n, m=m)

        # Get node properties for visualization
        degrees = dict(nx.degree(G))
        node_sizes = [5 + 3 * degrees[node] for node in G.nodes()]

        # Draw with different layout and color for each example
        if i == 0:  # Internet - circular layout
            pos = nx.circular_layout(G)
            color = 'lightblue'
        elif i == 1:  # PPI - spring layout
            pos = nx.spring_layout(G, seed=42)
            color = 'lightgreen'
        elif i == 2:  # Citation - shell layout
            pos = nx.shell_layout(G)
            color = 'lightcoral'
        else:  # Social - spectral layout
            pos = nx.spectral_layout(G)
            color = 'lightyellow'

        # Draw network
        nx.draw_networkx(
            G,
            pos=pos,
            ax=ax,
            node_size=node_sizes,
            node_color=color,
            edge_color='gray',
            with_labels=False,
            alpha=0.7
        )

        ax.set_title(title)
        ax.axis('off')

    plt.tight_layout()
    plt.savefig('images/real_world_examples.png', dpi=120)
    plt.close()

def generate_comparison_table_image():
    """Create a visual comparison table of network types."""
    print("Generating network comparison table...")

    # Define the comparison data
    network_types = ['Random Network', 'Small-World Network', 'Scale-Free Network']
    properties = [
        'Degree Distribution',
        'Path Length',
        'Clustering',
        'Hubs Formation',
        'Resilience to Random Failures',
        'Resilience to Targeted Attacks'
    ]

    # Values for each network type and property
    values = [
        ['Poisson', 'Peaked Near Average', 'Power Law'],
        ['Short', 'Short', 'Short'],
        ['Low', 'High', 'Variable'],
        ['No', 'Limited', 'Yes'],
        ['Medium', 'Medium', 'High'],
        ['Medium', 'Medium', 'Low']
    ]

    # Create a figure
    fig, ax = plt.subplots(figsize=(10, 8))
    ax.axis('off')

    # Draw the table
    table = ax.table(
        cellText=values,
        rowLabels=properties,
        colLabels=network_types,
        cellLoc='center',
        loc='center',
        colWidths=[0.25, 0.25, 0.25]
    )

    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 1.5)

    # Color the headers
    for i in range(len(network_types)):
        table[(0, i)].set_facecolor('#4472C4')
        table[(0, i)].set_text_props(color='white', fontweight='bold')

    for i in range(len(properties)):
        table[(i+1, -1)].set_facecolor('#C5D9F1')

    # Color specific cells based on property highlight
    for i in range(len(properties)):
        for j in range(len(network_types)):
            # Highlight positive traits
            if (
                (values[i][j] == 'Power Law' and properties[i] == 'Degree Distribution') or
                (values[i][j] == 'Short') or
                (values[i][j] == 'High') or
                (values[i][j] == 'Yes' and properties[i] == 'Hubs Formation') or
                (values[i][j] == 'High' and properties[i] == 'Resilience to Random Failures')
            ):
                table[(i+1, j)].set_facecolor('#C6EFCE')

            # Highlight negative traits
            elif (
                (values[i][j] == 'Low' and properties[i] == 'Clustering') or
                (values[i][j] == 'Low' and properties[i] == 'Resilience to Targeted Attacks')
            ):
                table[(i+1, j)].set_facecolor('#FFC7CE')

    plt.title('Comparison of Network Types', fontsize=16, y=0.9)
    plt.tight_layout()
    plt.savefig('images/network_comparison_table.png', dpi=120)
    plt.close()

def generate_linear_scale_distribution():
    """Generate a linear scale visualization specifically focused on scale-free properties."""
    print("Generating linear scale distribution visualization...")

    # Create a larger BA network for clear distribution
    n = 20000  # Large network for better statistics
    m = 2      # Minimal connectivity parameter

    # Generate scale-free network
    G = nx.barabasi_albert_graph(n=n, m=m)

    # Get degree distribution
    degrees = [d for _, d in G.degree()]

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot the histogram with custom styling
    counts, bins, patches = ax.hist(
        degrees,
        bins=100,  # More bins for finer detail
        alpha=0.7,
        color='skyblue',
        edgecolor='black',
        linewidth=0.5
    )

    # Add a zoomed inset for the tail
    # Create the inset axes
    axins = ax.inset_axes([0.5, 0.5, 0.45, 0.45])

    # Zoom into the extreme tail: last portion of the degree range
    max_degree = max(degrees)
    zoom_xmin = int(max_degree * 0.6)
    zoom_xmax = max_degree + max_degree * 0.05

    # Filter degrees to the zoom range
    high_degrees = [d for d in degrees if d >= zoom_xmin]

    # Use narrow bins so individual hub nodes are visible
    zoom_bins = np.arange(zoom_xmin, zoom_xmax + 1, 1)

    axins.hist(
        high_degrees,
        bins=zoom_bins,
        alpha=0.8,
        color='salmon',
        edgecolor='black',
        linewidth=0.5
    )

    axins.set_xlim(zoom_xmin, zoom_xmax)

    # Add title and labels to inset
    axins.set_title('Zoom: Hub Nodes (High Degree)', fontsize=10)
    axins.set_xlabel('Degree', fontsize=8)
    axins.set_ylabel('Count', fontsize=8)
    axins.tick_params(labelsize=8)

    # Draw a rectangle on the main plot indicating the zoomed region
    from matplotlib.patches import Rectangle
    rect = Rectangle(
        (zoom_xmin, 0), zoom_xmax - zoom_xmin, max(counts) * 0.5,
        linewidth=1.5, edgecolor='red', facecolor='none', linestyle='--'
    )
    ax.add_patch(rect)

    # Main plot styling
    ax.set_xlabel('Degree (k)', fontsize=14)
    ax.set_ylabel('Number of Nodes', fontsize=14)
    ax.set_title('Scale-Free Network: Degree Distribution (Linear Scale)', fontsize=16)

    # Annotations to explain the scale-free property
    ax.text(
        0.02, 0.95,
        "Scale-Free Property:\nMany nodes with few connections,\nFew nodes with many connections",
        transform=ax.transAxes,
        fontsize=12,
        verticalalignment='top',
        bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5')
    )

    # Draw an arrow pointing to the tail
    max_bin_height = max(counts)
    ax.annotate(
        'Power-law tail:\nHubs with many connections',
        xy=(max_degree*0.7, max_bin_height*0.05),  # Point to the tail
        xytext=(max_degree*0.4, max_bin_height*0.3),  # Text position
        arrowprops=dict(
            facecolor='black',
            shrink=0.05,
            width=1.5,
            headwidth=7,
            alpha=0.7
        ),
        fontsize=10,
        bbox=dict(facecolor='white', alpha=0.8, boxstyle='round')
    )

    # Add grid for readability
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('images/scale_free_linear_distribution.png', dpi=120)
    plt.close()

# Main execution
if __name__ == "__main__":
    generate_ba_networks()
    generate_degree_distributions()
    generate_linear_scale_distribution()
    generate_preferential_attachment_visual()
    generate_hub_and_authority_image()
    generate_network_attack_comparison()
    generate_real_world_examples()
    generate_comparison_table_image()

    print("All images generated successfully.")
