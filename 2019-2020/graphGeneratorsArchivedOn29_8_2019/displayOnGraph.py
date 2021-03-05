import csv
import networkx as nx
import matplotlib.pyplot as plt
import bisect
from matplotlib.colors import LinearSegmentedColormap
from matplotlib import cm

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

# create colormap
cdict = {'green': ((0.0, 1.0, 1.0),
                   (0.5, 1.0, 1.0),
                   (1.0, 0.0, 0.0)),

         'red': ((0.0, 0.0, 0.0),
                 (0.5, 1.0, 1.0),
                 (1.0, 1.0, 1.0)),

         'blue': ((0.0, 0.0, 0.0),
                  (1.0, 0.0, 0.0))
         }
green_yellow_red = LinearSegmentedColormap('GYR', cdict)

with open('sims/batteryLevelsSpecific.csv', 'r') as f:
    reader = csv.reader(f, delimiter=',')
    for row in reader:
        batteryLevels[int(float(row[0]))] = [float(i) for i in row[1:] if len(i) != 0]


def drawGraph(timeID):
    graph = nx.Graph()
    time = timeStops[timeID]
    coordinates = []
    links = []

    positions = {}

    with open('barcelonaSpecific.txt', 'r') as f:
        reader = csv.reader(f, delimiter=' ')
        for row in reader:
            coordinate = [int(i) for i in row]
            coordinates.append(coordinate)
    with open('sims/links/links_%d' % time, 'r') as f:
        reader = csv.reader(f, delimiter=' ')
        for row in reader:
            links.append(row)
    batteryLevelsCurrently = batteryLevels[time]
    for nodeID, coordinate in enumerate(coordinates):
        graph.add_node(str(nodeID), pos=coordinate)
        positions[str(nodeID)] = coordinate
        batteryLevelOfNode = max(min(batteryLevelsCurrently[nodeID], 1), -0.1)
        colorID = bisect.bisect_left(batteryColors, (batteryLevelOfNode,))
        batteryColor = batteryColors[colorID - 1][1]
        graph.add_node(str(nodeID), pos=coordinate, node_color=batteryLevelOfNode, cmap=cm.jet)

    for link in links:
        graph.add_edge(link[0], link[1])

    colors = map(lambda x: graph.node[x]['node_color'], graph.nodes())

    ax = plt.subplot(331 + timeID)
    ax.title.set_text('t=%d min' % time)
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.margins(0.1)
    nx.draw_networkx(graph, pos=positions, node_color=colors,vmin=-0.1, vmax=1, cmap=cm.Set1, alpha=1, node_size=500,
                     with_labels=True)
    nx.draw_networkx_edges(graph, pos=positions, edge_color='blue', alpha=.3, width=1)


for timeID in range(len(timeStops)):
    drawGraph(timeID)
plt.suptitle('UAV Battery Levels After Time t')
plt.show()
