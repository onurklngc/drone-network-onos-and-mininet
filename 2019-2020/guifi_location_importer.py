import libcnml
from geopy.distance import distance
from settings import *
import matplotlib.pyplot as plt
from math import sqrt

CLOSEST_DISTANCE = 80


def check_closeness_to_others(x_distance, y_distance, node_locations):
    for nodeLocation in node_locations:
        if sqrt((x_distance - nodeLocation[0]) ** 2 + (y_distance - nodeLocation[1]) ** 2) < CLOSEST_DISTANCE:
            return False
    return True


def get_positions(node_number=NUMBER_OF_SWITCHES):
    zone_id = 2436  # 34163
    cnml_data = libcnml.CNMLParser("http://guifi.net/en/guifi/cnml/%d/nodes" % zone_id)
    zone_box_corner_point = cnml_data.zones[zone_id].box[0]
    zone_box_corner_point = (float(zone_box_corner_point[1]), float(zone_box_corner_point[0]))

    # zoneBoxCornerPointUTM = from_latlon(float(zone_box_corner_point[0]), float(zone_box_corner_point[1]))
    node_locations = []
    x_points = []
    y_points = []
    for node in cnml_data.nodes.values():
        x_distance = distance(zone_box_corner_point, (zone_box_corner_point[0], node.longitude)).m
        y_distance = distance(zone_box_corner_point, (node.latitude, zone_box_corner_point[1])).m

        # # Remove the outlier
        # if x_distance > 5000:
        #     continue
        #
        # if x_distance < 9100 or x_distance > 9500:
        #     continue
        # if y_distance < 5900 or y_distance > 6400:
        #     continue
        # x_distance = int(x_distance - 9133)
        # y_distance = int(y_distance - 5900)

        if x_distance < 7000 or x_distance > 8000:
            continue
        if y_distance < 5500 or y_distance > 6500:
            continue
        x_distance = int(x_distance - 7000)
        y_distance = int(y_distance - 5500)
        if check_closeness_to_others(x_distance, y_distance, node_locations):
            node_locations.append((x_distance, y_distance, node.longitude, node.latitude))
            x_points.append(x_distance)
            y_points.append(y_distance)
            if len(node_locations) == node_number:
                break
    print(len(node_locations))
    with open('barcelona.txt', 'w+') as f:
        f.write('\n'.join('{} {}'.format(node[0], node[1]) for node in node_locations))
    with open('barcelonaLL.txt', 'w+') as f:
        f.write('\n'.join('{} {}'.format(node[2], node[3]) for node in node_locations))
    plt.scatter(x_points, y_points)
    plt.show()


get_positions(node_number=25)
