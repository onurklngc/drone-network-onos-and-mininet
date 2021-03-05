import csv, json, urllib
from geopy.distance import geodesic
import networkx as nx
import matplotlib.pyplot as plt
import mplleaflet

graph = nx.Graph()

coordinates = []
links = []
nodes = {}
with open('barcelonaLL.txt', 'r') as f:
    reader = csv.reader(f, delimiter=' ')
    for row in reader:
        coordinate = [float(i) for i in row]
        coordinates.append(coordinate)
with open('links.txt', 'r') as f:
    reader = csv.reader(f, delimiter=' ')
    for row in reader:
        links.append(row)

for nodeID, coordinate in enumerate(coordinates):
    graph.add_node(str(nodeID), pos=coordinate)
    nodes[str(nodeID)] = coordinate

for link in links:
    graph.add_edge(str(link[0]), str(link[1]))

nx.draw_networkx(graph, pos=nodes, node_color='blue', edge_color='k', alpha=.4, node_size=100, with_labels=True)
nx.draw_networkx_edges(graph,pos=nodes,edge_color='green', alpha=.9,width=5 )
# nx.draw_networkx_nodes(Airport, pos=dic_pos, node_color='brown', ith_labels=True)

mplleaflet.show()
