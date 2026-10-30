import matplotlib.pyplot as plt
import networkx as nx


def plot_coupling_map(proc, out_path):
    g = nx.Graph()
    g.add_nodes_from(range(proc["num_qubits"]))
    g.add_edges_from(tuple(e) for e in proc["coupling_map"])
    pos = nx.spring_layout(g, seed=1)
    plt.figure(figsize=(5, 4))
    nx.draw(g, pos, with_labels=True, node_size=900, node_color="#cfe3ff")
    plt.title(f'{proc["name"]} ({proc["num_qubits"]} qubits)')
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()


def plot_weighted_graph(edges, n, out_path, title="Max-Cut instance"):
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_weighted_edges_from(edges)
    pos = nx.spring_layout(g, seed=1)
    plt.figure(figsize=(5, 4))
    nx.draw(g, pos, with_labels=True, node_size=800, node_color="#ffe3b3")
    nx.draw_networkx_edge_labels(g, pos, edge_labels={(i, j): w for i, j, w in edges})
    plt.title(title)
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()