import numpy as np
from random import randint
from settings import *
import math
import bisect
import traceback


def rss_to_data_rate(rss):
    min_sensitivity = [
        (-82.1, 0),
        (-82, 6),
        (-81, 9),
        (-79, 12),
        (-77, 18),
        (-74, 24),
        (-70, 36),
        (-66, 48),
        (-65, 54),
    ]
    satisfied_min_value = bisect.bisect_left(min_sensitivity, (rss,))
    if satisfied_min_value >= len(min_sensitivity):
        satisfied_min_value = len(min_sensitivity) - 1
    return min_sensitivity[satisfied_min_value][1]


class SwitchMover(object):
    initial_switch_positions = []
    initial_switch_positions_ll = []
    switch_positions = []
    host_positions = []
    switch2switch_distances = []
    switch2host_distances = []
    neighbors = {}
    switch2switch_link_capacities = []
    switch2host_link_capacities = []
    switch2host_link_capacities_previous = []
    number_of_switches_initial = 0
    number_of_switches_alive = 0
    operating_switches = []
    active_link_pair_capacity_table = []
    previous_link_pair_capacity_table = []

    def __init__(self, switch_number=NUMBER_OF_SWITCHES):
        # switch_positions = np.random.randint(low=0, high=COORDINATE_LIMIT, size=(switch_number, 2))
        # switch2switch_distances = np.array([complex(c.m_x, c.m_y) for c in cells])
        self.get_initial_locations_from_file()
        self.get_initial_locations_from_file_ll()
        self.number_of_switches_alive = switch_number
        self.number_of_switches_initial = switch_number
        self.operating_switches = np.arange(switch_number)
        self.switch_positions = np.array(self.initial_switch_positions)
        self.host_positions = np.array(self.initial_switch_positions)
        self.host_positions[:, 2] = 0
        if FIGURE_8_SWITCH_MOVEMENT:
            self.initialCircularPhase = np.random.uniform(low=-np.pi, high=np.pi, size=(NUMBER_OF_SWITCHES, 1))
            self.move_switches_figure8(0)
        self.switch2switch_distances = np.zeros(shape=(NUMBER_OF_SWITCHES, NUMBER_OF_SWITCHES))
        self.switch2host_distances = self.switch_positions[:, 2]
        self.switch2switch_link_capacities = np.full_like(self.switch2switch_distances, 0)
        self.switch2host_link_capacities = np.full_like(self.switch2host_distances, 0)
        self.get_distances()
        self.get_link_capacities()
        self.content_server_switch_id = self.get_central_node()
        self.select_links()

    def get_central_node(self):
        central_point = np.mean(self.switch_positions[self.operating_switches], axis=0)
        number_of_points = self.number_of_switches_alive
        center_to_switch_distances = np.zeros(shape=(number_of_points, 1))
        for i in range(number_of_points):
            center_to_switch_distances[i] = np.sqrt(
                np.sum((self.switch_positions[self.operating_switches[i]] - central_point) ** 2, axis=0))
        try:
            self.content_server_switch_id = self.operating_switches[int(np.argmin(center_to_switch_distances))]
        except Exception as e:
            print(traceback.format_exc())
            print(e)
        print("Content server is: %d" % self.content_server_switch_id)
        return self.content_server_switch_id

    def grid_initialization(self, coordinate_limit):
        initial_switch_positions = []
        effective_area = coordinate_limit / 2
        row_distance = effective_area / NUMBER_OF_SWITCHES_PER_ROW
        column_distance = effective_area / NUMBER_OF_SWITCHES_PER_COLUMN
        effective_area_start_point = (
            coordinate_limit / 4 + row_distance / 2, coordinate_limit / 4 + column_distance / 2)

        for i in range(NUMBER_OF_SWITCHES_PER_ROW):
            for j in range(NUMBER_OF_SWITCHES_PER_COLUMN):
                initial_switch_positions.append(
                    [effective_area_start_point[0] + row_distance * i,
                     effective_area_start_point[1] + column_distance * j,
                     randint(AVERAGE_HEIGHT - HEIGHT_DEVIATION, AVERAGE_HEIGHT + HEIGHT_DEVIATION)])
        self.initial_switch_positions = np.array(initial_switch_positions)

    def get_initial_locations_from_file(self, file_name="barcelona.txt"):
        xy_coordinates = np.genfromtxt(file_name, dtype=int, delimiter=' ')
        z_coordinate = np.random.randint(low=AVERAGE_HEIGHT - HEIGHT_DEVIATION, high=AVERAGE_HEIGHT + HEIGHT_DEVIATION,
                                         size=(len(xy_coordinates), 1))
        self.initial_switch_positions = np.concatenate((xy_coordinates, z_coordinate), axis=1)
        self.initial_switch_positions = self.initial_switch_positions[0:NUMBER_OF_SWITCHES, :]

    def get_initial_locations_from_file_ll(self, file_name="barcelonaLL.txt"):
        # Longitude latitude values
        self.initial_switch_positions_ll = np.genfromtxt(file_name, dtype=float, delimiter=' ')

    def get_switch_positions(self):
        return self.switch_positions

    def select_links(self, max_link_number=3):
        linking_switches = []
        connected_switches = []
        candidate_links = []
        self.active_link_pair_capacity_table = []
        self.neighbors.clear()
        for switch in self.operating_switches:
            self.neighbors[switch] = []
        if self.number_of_switches_alive < 2:
            print("One switch is left")
            return
        temp_switch2switch_link_capacities = np.copy(self.switch2switch_link_capacities)
        connected_switches.append(self.content_server_switch_id)
        link_number = max_link_number
        while link_number > 0:
            linking_switches = np.argpartition(self.switch2switch_link_capacities[self.content_server_switch_id],
                                               -link_number)[
                               -link_number:].astype(int).tolist()
            if self.switch2switch_link_capacities[self.content_server_switch_id, linking_switches[0]] <= 0:
                # Content server switch does not have links to connect, decrement link number for this server
                link_number -= 1
                linking_switches = [self.content_server_switch_id]
            else:
                linking_switches.reverse()
                self.neighbors[self.content_server_switch_id] = linking_switches[:]
                break

        for switch in linking_switches:
            temp_pair = [self.content_server_switch_id, switch]
            temp_pair.sort()
            temp_pair.append(int(self.switch2switch_link_capacities[self.content_server_switch_id, switch]))
            self.active_link_pair_capacity_table.append(temp_pair)
            self.neighbors[switch] = [self.content_server_switch_id]
        # Add closest neighbors
        connected_switches = connected_switches + linking_switches
        # Eliminate content_server_switch_id from capacity matrix, it has max link number
        temp_switch2switch_link_capacities[:, self.content_server_switch_id] = -1

        capacity_matrix_for_linking_switches = np.array(
            [temp_switch2switch_link_capacities[i] for i in linking_switches])
        # for switch in connected_switches:
        #     capacity_matrix_for_linking_switches[:, switch] = -1
        try:
            # Obtain minimum spanning tree
            while len(connected_switches) != self.number_of_switches_alive:
                closest_switch_index = np.argmax(capacity_matrix_for_linking_switches)
                new_switch = int(closest_switch_index % self.number_of_switches_initial)
                source_switch_index = closest_switch_index / self.number_of_switches_initial
                if capacity_matrix_for_linking_switches[source_switch_index, new_switch] <= 0:
                    break
                source_switch = linking_switches[source_switch_index]
                temp_pair = [source_switch, new_switch]
                temp_pair.sort()
                temp_pair.append(int(self.switch2switch_link_capacities[source_switch, new_switch]))
                # Prevent arg_max to get the same value
                capacity_matrix_for_linking_switches[source_switch_index, new_switch] = -1
                if source_switch == new_switch:
                    continue
                if new_switch in linking_switches:
                    new_switch_index = linking_switches.index(new_switch)
                    capacity_matrix_for_linking_switches[new_switch_index, source_switch] = -1
                temp_switch2switch_link_capacities[new_switch, source_switch] = -1
                if new_switch not in connected_switches:
                    self.neighbors[source_switch].append(new_switch)
                    # Create a list and add the first element
                    self.neighbors[new_switch] = [source_switch]
                    self.active_link_pair_capacity_table.append(temp_pair)
                    if len(self.neighbors[source_switch]) == max_link_number:
                        capacity_matrix_for_linking_switches = np.delete(capacity_matrix_for_linking_switches,
                                                                         source_switch_index, 0)
                        linking_switches.remove(source_switch)
                        temp_switch2switch_link_capacities[:, source_switch] = -1
                        capacity_matrix_for_linking_switches[:, source_switch] = -1
                    # Eliminate already connected switches from the new switch's row on the capacity list
                    # temp_switch2switch_link_capacities[new_switch, connected_switches] = -1
                    # Add new switch's neighbors to the search list
                    connected_switches.append(new_switch)
                    linking_switches.append(new_switch)
                    capacity_matrix_for_linking_switches = np.vstack((capacity_matrix_for_linking_switches,
                                                                      temp_switch2switch_link_capacities[new_switch]))
                else:
                    candidate_links.append(temp_pair)
            if len(connected_switches) != self.number_of_switches_alive:
                # Disconnected graph
                print("Disconnected graph")
                for switch in self.operating_switches:
                    if switch not in connected_switches:
                        linking_switches.append(switch)
                        capacity_matrix_for_linking_switches = np.vstack((capacity_matrix_for_linking_switches,
                                                                          temp_switch2switch_link_capacities[switch]))

            # Add extra links from candidates
            while len(linking_switches) > 1 and len(candidate_links):
                temp_pair = candidate_links.pop(0)
                if len(self.neighbors[temp_pair[0]]) != max_link_number and len(
                        self.neighbors[temp_pair[1]]) != max_link_number:
                    self.neighbors[temp_pair[0]].append(temp_pair[1])
                    self.neighbors[temp_pair[1]].append(temp_pair[0])
                    self.active_link_pair_capacity_table.append(temp_pair)
                    if len(self.neighbors[temp_pair[0]]) == max_link_number:
                        new_switch_index = linking_switches.index(temp_pair[0])
                        capacity_matrix_for_linking_switches = np.delete(capacity_matrix_for_linking_switches,
                                                                         new_switch_index, 0)
                        capacity_matrix_for_linking_switches[:, temp_pair[0]] = -1
                        linking_switches.remove(temp_pair[0])
                        # Update source_switch_index
                    if len(self.neighbors[temp_pair[1]]) == max_link_number:
                        source_switch_index = linking_switches.index(temp_pair[1])
                        capacity_matrix_for_linking_switches = np.delete(capacity_matrix_for_linking_switches,
                                                                         source_switch_index, 0)
                        capacity_matrix_for_linking_switches[:, temp_pair[1]] = -1
                        linking_switches.remove(temp_pair[1])
            # Add extra links
            while len(linking_switches) > 1 and np.amax(capacity_matrix_for_linking_switches) > 0:
                closest_switch_index = np.argmax(capacity_matrix_for_linking_switches)
                new_switch = int(closest_switch_index % self.number_of_switches_initial)
                source_switch_index = closest_switch_index / self.number_of_switches_initial
                source_switch = linking_switches[source_switch_index]
                new_switch_index = linking_switches.index(new_switch)
                self.neighbors[source_switch].append(new_switch)
                self.neighbors[new_switch].append(source_switch)
                if source_switch == new_switch:
                    break
                temp_pair = [source_switch, new_switch]
                temp_pair.sort()
                link_capacity = int(self.switch2switch_link_capacities[source_switch, new_switch])
                if link_capacity <= 0:
                    print("Error here")
                temp_pair.append(link_capacity)
                self.active_link_pair_capacity_table.append(temp_pair)
                # Prevent arg_max to get the same value
                capacity_matrix_for_linking_switches[source_switch_index, new_switch] = -1
                capacity_matrix_for_linking_switches[new_switch_index, source_switch] = -1
                if len(self.neighbors[new_switch]) == max_link_number:
                    capacity_matrix_for_linking_switches = np.delete(capacity_matrix_for_linking_switches,
                                                                     new_switch_index, 0)
                    capacity_matrix_for_linking_switches[:, new_switch] = -1
                    linking_switches.remove(new_switch)
                    # Update source_switch_index
                    source_switch_index = linking_switches.index(source_switch)
                if len(self.neighbors[source_switch]) == max_link_number:
                    capacity_matrix_for_linking_switches = np.delete(capacity_matrix_for_linking_switches,
                                                                     source_switch_index, 0)
                    capacity_matrix_for_linking_switches[:, source_switch] = -1
                    linking_switches.remove(source_switch)
        except Exception as e:
            print("Link establishment error:")
            print(traceback.format_exc())
            print(e)
        # with open('links.txt', 'w+') as f:
        #     f.write('\n'.join('{} {}'.format(node[0], node[1]) for node in self.active_link_pair_capacity_table))
        # print(self.active_link_pair_capacity_table)

    def print_links_to_file(self, file_name=None):
        if file_name is None:
            file_name = "links.txt"
        with open(file_name, 'w+') as f:
            f.write('\n'.join('{} {}'.format(node[0], node[1]) for node in self.active_link_pair_capacity_table))

    def get_switch2switch_distances(self):
        for i in range(NUMBER_OF_SWITCHES):
            for j in range(NUMBER_OF_SWITCHES):
                self.switch2switch_distances[i, j] = np.sqrt(
                    np.sum((self.switch_positions[i] - self.switch_positions[j]) ** 2, axis=0)) if i != j else np.inf

    def get_switch2host_distances(self):
        for i in range(NUMBER_OF_SWITCHES):
            self.switch2host_distances[i] = np.sqrt(
                np.sum((self.switch_positions[i] - self.host_positions[i]) ** 2, axis=0))

    def get_distances(self):
        self.get_switch2switch_distances()
        self.get_switch2host_distances()

    def get_switch2switch_link_capacities(self):
        try:
            for i, j in np.ndindex(self.switch2switch_distances.shape):
                # P_r(dB) = P_t(dB) + G(dB) - 10 * a * log10(d) - L_FS
                # Transmission power P_t=20dBm, Power gains factor G=-6dBi, U2U pathloss coefficient a=2
                # L_FS = 10 * a  log(f) + 20 log( 4 * pi / c ) = 40dB for f=2.4GHz and a=2
                # Pr(dB) = P_r(dB) - 20*log10(d)
                # SNR(dB) = P_r(dB) - No(dB) * f  Noise variance No=-96dBm or -84
                # SNR(dB) = 58 - 20*log10(d)
                # shannon_capacity = BW * log2(1+SNR)
                distance = self.switch2switch_distances[i, j]
                if i not in self.operating_switches or j not in self.operating_switches:
                    # One of the switches is not operating
                    self.switch2switch_link_capacities[i, j] = -3
                    continue
                if distance == np.inf:
                    self.switch2switch_link_capacities[i, j] = -2
                    continue
                elif distance > 500:
                    self.switch2switch_link_capacities[i, j] = -1
                    continue
                snr = 58 - 20 * math.log10(distance)
                shannon_capacity = 10 * math.log(1 + 10 ** (snr / 10))
                self.switch2switch_link_capacities[i, j] = shannon_capacity
        except Exception as e:
            print(e)

    # def getSwitchToSwitchLinkCapacities():
    #     try:
    #         for i, j in np.ndindex(switch2switch_distances.shape):
    #             # P_r(dB) = P_t(dB) + G(dB) - 10 * a * log10(4 * pi / lambda ) - 10 * a * log10(d)
    #             # Transmission power P_t=20dBm, Power gains factor G=-31.5dB, U2U pathloss coefficient a=2.6
    #             # L_FS = 10 * a  log(f) + 20 log( 4 * pi / c ) = 40dB for f=2.4GHz and a=2.6
    #             # Pr(dB) = P_r(dB) - 20*log10(d)
    #
    #             distance = switch2switch_distances[i, j]
    #             if distance == -1:
    #                 switch2switch_link_capacities[i, j] = 0
    #                 continue
    #             rss = -22 - 26 * math.log10(distance)
    #             switch2switch_link_capacities[i, j] = rssToDataRate(rss)
    #     except Exception as e:
    #         print(e)

    def get_switch2host_link_capacities(self):
        try:
            for i in range(self.switch2host_distances.shape[0]):
                # Probability LoS: pr_los = 1 / ( 1 + a * exp(-b * (elevation_angle - a)) )
                # U2I channel parameter a=12 and b=0.135
                # elevation_angle = sin^-1(h / distance)
                # Free space address loss: pl_fs = 10 * a  log(f) + 20 log( 4 * pi / c ) = 32.44dB for f=1GHz,
                # 40dB for f=2.4GHz
                # pl_los  = pl_fs + 20*log10(d) + n_los
                # pl_nlos = pl_fs + 20*log10(d) + n_nlos
                # n_LoS=1 and n_NLoS=20 are additional attenuation factors due to the LoS and NLoS
                # pl_avg = pl_los * pr_los + pl_nlos * (1-pr_los)
                # p_t=20dBm
                a = 12
                b = 0.135
                pl_fs = 40
                p_t = 20
                distance = self.switch2host_distances[i]
                height = self.switch_positions[i][2]
                elevation_angle = math.asin(height / distance)
                path_loss = pl_fs + 20 * math.log10(distance)
                pr_los = 1 / (1 + 12 * math.exp(-b * (elevation_angle - a)))
                pl_los = path_loss  # +0
                pl_nlos = pl_fs + 20 * math.log10(distance) + 13.01
                pl_avg = pl_los * pr_los + pl_nlos * (1 - pr_los)
                rss = p_t - pl_avg
                snr = rss + 84
                shannon_capacity = 10 * math.log(1 + 10 ** (snr / 10))
                self.switch2host_link_capacities[i] = shannon_capacity
        except Exception as e:
            print(e)

    def get_link_capacities(self):
        self.get_switch2switch_link_capacities()
        self.get_switch2host_link_capacities()

    def store_previous_link_capacities(self):
        self.switch2host_link_capacities_previous = np.copy(self.switch2host_link_capacities)
        self.previous_link_pair_capacity_table = self.active_link_pair_capacity_table[:]

    def move_switches_random(self):
        movements = np.random.randint(low=-1, high=2, size=(NUMBER_OF_SWITCHES, 3))
        self.switch_positions = np.add(self.switch_positions, movements)
        self.switch_positions = np.clip(self.switch_positions, 0, COORDINATE_LIMIT)

    def move_switches_figure8(self, current_time):
        t = 2 * np.pi * current_time / FIGURE_8_PERIOD + self.initialCircularPhase
        x_delta = FIGURE_8_ALPHA_VAR * np.sqrt(2) * np.cos(t) / (np.sin(t) ** 2 + 1)
        y_delta = FIGURE_8_ALPHA_VAR * np.sqrt(2) * np.cos(t) * np.sin(t) / (np.sin(t) ** 2 + 1)
        z_delta = np.random.randint(low=-1, high=2, size=(NUMBER_OF_SWITCHES, 1))
        movements = np.concatenate((x_delta, y_delta, z_delta), axis=1)
        movements = np.rint(movements).astype(int)
        self.switch_positions = np.add(self.switch_positions, movements)
        self.switch_positions = np.clip(self.switch_positions, 0, COORDINATE_LIMIT)

    def move_switches_for_one_time_interval(self, current_time=0):
        if RANDOM_SWITCH_MOVEMENT:
            self.move_switches_random()
        elif FIGURE_8_SWITCH_MOVEMENT:
            self.move_switches_figure8(current_time)
        # print(self.switch_positions)
        # print("**********")
        self.get_distances()
        self.store_previous_link_capacities()
        self.get_link_capacities()
        self.select_links()
        # print("----------")


if __name__ == '__main__':
    switchMover = SwitchMover()
    switchMover.move_switches_for_one_time_interval()
