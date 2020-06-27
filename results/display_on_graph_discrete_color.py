import csv
import networkx as nx
import matplotlib.pyplot as plt
import bisect

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "18"

timeStops = [0, 5, 7, 11, 14, 15, 16, 17, 18]
batteryLevels = {}

batteryColors = [
    (-10, "brown"),
    (0, "red"),
    (0.199, "pink"),
    (0.399, "yellow"),
    (0.599, "orange"),
    (0.799, "g"),
]

with open('sims/batteryLevelsSpecific.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    for row in reader:
        batteryLevels[int(float(row[0]))] = [float(i) for i in row[1:] if len(i) != 0]


def draw_graph(time_id):
    graph = nx.Graph()
    time = timeStops[time_id]
    coordinates = []
    links = []

    positions = {}
    with open('barcelonaSpecific.txt', 'r') as f:
        file_reader = csv.reader(f, delimiter=' ')
        for current_row in file_reader:
            coordinate = [int(i) for i in current_row]
            coordinates.append(coordinate)
    with open('sims/links/links_%d' % time, 'r') as f:
        file_reader = csv.reader(f, delimiter=' ')
        for current_row in file_reader:
            links.append(current_row)
    battery_levels_currently = batteryLevels[time]
    for nodeID, coordinate in enumerate(coordinates):
        graph.add_node(str(nodeID), pos=coordinate)
        positions[str(nodeID)] = coordinate
        battery_level_of_node = battery_levels_currently[nodeID]
        color_id = bisect.bisect_left(batteryColors, (battery_level_of_node,))
        battery_color = batteryColors[color_id - 1][1]
        graph.add_node(str(nodeID), pos=coordinate, node_color=battery_color)

    for link in links:
        graph.add_edge(link[0], link[1])

    colors = map(lambda x: graph.node[x]['node_color'], graph.nodes())

    ax = plt.subplot(331 + time_id)
    ax.title.set_text('t=%d min' % time)
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.margins(0.1)
    nx.draw_networkx(graph, pos=positions, node_color=colors, alpha=1, node_size=500, with_labels=True)
    nx.draw_networkx_edges(graph, pos=positions, edge_color='blue', alpha=.3, width=1)


for timeID in range(len(timeStops)):
    draw_graph(timeID)
plt.suptitle('UAV Battery Levels After Time t')
plt.show()
