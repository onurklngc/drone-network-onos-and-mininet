import csv
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
import pickle
import matplotlib.colors as colors

file_name = "situation-158206022.pkl"

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "22"

time_stops = [0, 5, 7, 11, 14, 15, 16, 17]
battery_levels = {}
results = {}
nodes_graph_for_color_bar = None

depleted_drone_color = 'red'

content_server_figure = plt.scatter([], [], marker="*", color="white", edgecolors="blue",
                                    label="Content server connected UAV", s=360)
depleted_uav_figure = plt.scatter([], [], marker="x", color="red", label="Depleted UAV", s=120)

legend_elements = [content_server_figure, depleted_uav_figure]


# batteryColors = [
#     (-10, "brown"),
#     (0, "red"),
#     (0.199, "pink"),
#     (0.399, "yellow"),
#     (0.599, "orange"),
#     (0.799, "g"),
# ]
# with open('sims/batteryLevelsSpecific.csv', 'r') as f:
#     reader = csv.reader(f, delimiter=',')
#     for row in reader:
#         battery_levels[int(float(row[0]))] = [float(i) for i in row[1:] if len(i) != 0]
def truncate_colormap(color_map, min_val=0.0, max_val=1.0, n=100):
    new_color_map = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=color_map.name, a=min_val, b=max_val),
        color_map(np.linspace(min_val, max_val, n)))
    return new_color_map


color_map = plt.get_cmap('PiYG')
new_color_map = truncate_colormap(color_map, 0, 0.8)


def draw_graph(timeID):
    global nodes_graph_for_color_bar
    graph = nx.Graph()
    current_time = time_stops[timeID]
    current_time_in_sec = current_time * 60
    coordinates = []
    positions = {}
    active_nodes = []
    depleted_nodes = []
    current_content_server = results[current_time_in_sec]['content_server']

    with open('barcelonaSpecific.txt', 'r') as f:
        reader = csv.reader(f, delimiter=' ')
        for row in reader:
            coordinate = [int(i) for i in row]
            coordinates.append(coordinate)
    # with open('sims/links/links_%d' % current_time, 'r') as f:
    #     reader = csv.reader(f, delimiter=' ')
    #     for row in reader:
    #         links.append(row)
    battery_levels_currently = results[current_time_in_sec]['battery_levels'] / initialBatteryCapacity
    for nodeID, coordinate in enumerate(coordinates):
        positions[str(nodeID)] = coordinate
        battery_level_of_node = battery_levels_currently[nodeID]
        # colorID = bisect.bisect_left(batteryColors, (battery_level_of_node,))
        # batteryColor = batteryColors[colorID - 1][1]
        if battery_level_of_node <= 0:
            depleted_nodes.append(str(nodeID))

        elif not current_content_server == nodeID:
            active_nodes.append(str(nodeID))
            graph.add_node(str(nodeID), pos=coordinate, node_color=battery_level_of_node)

    colors_except_content_server_and_depleted_nodes = map(lambda x: graph.node[x]['node_color'], graph.nodes())

    for nodes in depleted_nodes:
        graph.add_node(nodes)

    battery_level_of_content_server = battery_levels_currently[current_content_server]
    coordinate_content_server = coordinates[current_content_server]
    graph.add_node(str(current_content_server), pos=coordinate_content_server,
                   node_color=battery_level_of_content_server)

    for link in results[current_time_in_sec]['links']:
        graph.add_edge(str(link[0]), str(link[1]))

    ax = plt.subplot(331 + timeID)
    plt.title('t=%d min' % current_time, y=-0.01)
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)
    ax.margins(0.1)
    nx.draw_networkx_nodes(graph, pos=positions, nodelist=[str(current_content_server)], node_shape="*",
                           node_color=[
                               battery_level_of_content_server] if battery_level_of_content_server > 0 else depleted_drone_color,
                           vmin=0.0, vmax=1.25, cmap=cm.PiYG, alpha=1,
                           node_size=750,
                           )
    nx.draw_networkx_nodes(graph, pos=positions, nodelist=depleted_nodes, node_shape="x",
                           node_color=depleted_drone_color, alpha=1, node_size=100,
                           )
    nodes_graph = nx.draw_networkx_nodes(graph, pos=positions, nodelist=active_nodes, node_shape="o",
                                         node_color=colors_except_content_server_and_depleted_nodes, vmin=0.0, vmax=1,
                                         cmap=new_color_map, alpha=1,
                                         node_size=500,
                                         )
    if timeID == 0:
        nodes_graph_for_color_bar = nodes_graph
    nx.draw_networkx_edges(graph, pos=positions, edge_color='blue', alpha=.3, width=1)
    nx.draw_networkx_labels(graph, pos=positions)
    # nx.draw(graph)


if __name__ == '__main__':
    with open(file_name, 'rb') as handle:
        results = pickle.load(handle)
    initialBatteryCapacity = results[0]['battery_levels'].min()
    fig = plt.figure()

    for timeID in range(len(time_stops)):
        draw_graph(timeID)
    fig.subplots_adjust(bottom=0.15, top=0.95, left=0.05, right=0.9,
                        wspace=0.02, hspace=0.02)
    cb_ax = fig.add_axes([0.91, 0.15, 0.01, 0.7])
    color_bar = fig.colorbar(nodes_graph_for_color_bar, cax=cb_ax, )
    color_bar.set_ticks([0, 0.5, 1.0])
    color_bar.set_ticklabels(['0%', '50%', '100%'])
    color_bar.set_label('Battery Level')
    # color_bar.ax.tick_params(labelsize=16)
    # plt.legend(loc='center')
    fig.legend(handles=legend_elements, loc="lower right", fontsize=28, bbox_to_anchor=(0.909, 0))
    # plt.suptitle('UAV Battery Levels After Time t')

    plt.show()
