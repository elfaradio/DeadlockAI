import networkx as nx

G = nx.DiGraph()

G.add_edge("R1", "P1")
G.add_edge("P1", "R2")

print(G.edges())