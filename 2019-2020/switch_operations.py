import traceback
import urllib2
from random import sample

import numpy as np

import controller_utils
from energy_management import BatteryCapacityLogger
from settings import *
from switch_manager import SwitchManager
from switch_movement import SwitchMover


class SwitchOperator(object):
    switch_mover = None
    drone_battery_manager = None
    switch_manager = None
    cached_switches = []  # If cached, no fill cost
    caching_switches = []
    latest_switch_metrics = {}
    latest_packet_numbers = {}

    def __init__(self, switch_mover=None, drone_battery_manager=None, switch_manager=None,
                 switch_number=NUMBER_OF_SWITCHES, ratio_of_caching_nodes=RATIO_OF_CACHING_NODES):
        if switch_mover:
            self.switch_mover = switch_mover
        else:
            self.switch_mover = SwitchMover()
        if drone_battery_manager:
            self.drone_battery_manager = drone_battery_manager
        else:
            self.drone_battery_manager = BatteryCapacityLogger()
        if switch_manager:
            self.switch_manager = switch_manager
        else:
            self.switch_manager = SwitchManager()
        # Randomly select M switches for caching
        self.caching_switches = sample(range(0, switch_number), int(switch_number * ratio_of_caching_nodes))
        self.caching_switches.sort()
        print("Initially caching switches:" + str(self.caching_switches))

    def estimate_energy_cost(self, candidate_list, file_size):
        lowest_total_cost = np.inf
        candidate_id_with_lowest_cost = 0
        transmission_info = []
        storing_switches = []
        cache_read_switch = None
        cost_list = []
        for candidateID, candidate in enumerate(candidate_list):
            transmitting_switch_candidates = []
            storing_switch_candidates = []
            temp_transmission_info = []
            cache_read_switch_candidate = None
            if candidate[1] == SOURCE_SWITCH:
                # This is a switch
                transmitting_switch_candidates.append(candidate[0])
                cache_read_switch_candidate = candidate[0]
            for visitedSwitch in candidate[2]:
                transmitting_switch_candidates.append(visitedSwitch)
                if visitedSwitch in self.caching_switches:
                    storing_switch_candidates.append(visitedSwitch)
            link_pairs = [int(self.switch_mover.switch2switch_link_capacities[
                                  transmitting_switch_candidates[i],
                                  transmitting_switch_candidates[i + 1]]) for i in
                          range(len(transmitting_switch_candidates) - 1)]
            link_pairs.append(self.switch_mover.switch2host_link_capacities[transmitting_switch_candidates[-1]])

            for i, transmittingSwitchCandidate in enumerate(transmitting_switch_candidates):
                # 1Mbps=125KB/s
                temp_transmission_info.append([transmittingSwitchCandidate, float(file_size) / link_pairs[i] / 125])

            temp_cost = self.drone_battery_manager.route_cost_energy(
                temp_transmission_info, storing_switch_candidates, file_size, cache_read_switch)
            cost_list.append(temp_cost)
            if lowest_total_cost > temp_cost:
                candidate_id_with_lowest_cost = candidateID
                lowest_total_cost = temp_cost
                transmission_info = temp_transmission_info[:]
                storing_switches = storing_switch_candidates[:]
                cache_read_switch = cache_read_switch_candidate
        lowest_total_cost_real = 0
        for transmission in transmission_info:
            lowest_total_cost_real += self.drone_battery_manager.decrease_battery_tx(transmission[0], transmission[1])
        for storingSwitch in storing_switches:
            lowest_total_cost_real += self.drone_battery_manager.decrease_battery_write(storingSwitch, file_size)
        if cache_read_switch:
            lowest_total_cost_real += self.drone_battery_manager.decrease_battery_read(cache_read_switch, file_size)

        return candidate_id_with_lowest_cost, lowest_total_cost_real, storing_switches

    def get_switch_overheads(self):
        data = controller_utils.get_metrics()
        if "devices" not in data:
            print("Error while retrieving metrics:")
            print(data)
        for switch in data["devices"]:
            switch_id = self.switch_manager.get_id_by_of_name(switch["name"])
            latest_packet_number = sum(x.itervalues().next()["latest"] for x in switch["value"]["metrics"])
            if switch_id not in self.latest_packet_numbers:
                self.latest_packet_numbers[switch_id] = latest_packet_number
                continue
            previous_packet_number = self.latest_packet_numbers[switch_id]
            packet_difference = latest_packet_number - previous_packet_number
            self.drone_battery_manager.decrease_battery_process_packet(switch_id, packet_difference)
            self.latest_packet_numbers[switch_id] = latest_packet_number

    def update_device_coordinates_on_controller(self):
        current_info = controller_utils.get_network_configurations()
        if "devices" in current_info:
            switch_positions = self.switch_mover.get_switch_positions()
            for device_name, device_properties in current_info["devices"].items():
                device_id = self.switch_manager.get_id_by_of_name(device_name)
                if device_id in switch_positions:
                    current_info["devices"][device_name]["basic"] = {
                        "latitude": switch_positions[device_id][0],
                        "longitude": switch_positions[device_id][1],
                    }
            controller_utils.post_network_configurations(current_info)
        return current_info

    def select_caching_nodes(self):
        number_of_switches_caching = min(int(NUMBER_OF_SWITCHES * RATIO_OF_CACHING_NODES),
                                         len(self.switch_mover.operating_switches))
        if number_of_switches_caching == len(self.switch_mover.operating_switches):
            self.caching_switches = self.switch_mover.operating_switches[:]
            return

        energy_component = np.full_like(self.switch_mover.operating_switches, 0, dtype=float)
        divider_part = np.full_like(energy_component, 1)
        self_link_capacities = np.full_like(energy_component, 0)
        neighbors_total_link_capacities = np.full_like(energy_component, 0)
        hop_counts_to_server = np.full_like(energy_component, 0)

        link_capacities_and_neighbors = {}
        for switch in self.switch_mover.operating_switches:
            if switch not in self.switch_mover.neighbors:
                switch_neighbors = []
            else:
                switch_neighbors = self.switch_mover.neighbors[switch]
            link_capacities_and_neighbors[switch] = [sum(
                [int(self.switch_mover.switch2switch_link_capacities[switch, neighbor]) for neighbor in
                 switch_neighbors]), switch_neighbors]
        max_battery_level = self.drone_battery_manager.get_max_battery_level()

        for switch_relative_id, switch in enumerate(self.switch_mover.operating_switches):
            # Connectivity
            self_link_capacities[switch_relative_id] = link_capacities_and_neighbors[switch][0]
            switch_neighbors = link_capacities_and_neighbors[switch][1]
            neighbors_total_link_capacities[switch_relative_id] = sum(
                [link_capacities_and_neighbors[neighbor][0] for neighbor in switch_neighbors])
            try:
                if switch != self.switch_mover.content_server_switch_id:
                    src_id = urllib2.quote(self.switch_manager.get_of_name_by_id(switch))
                    dst_id = urllib2.quote(
                        self.switch_manager.get_of_name_by_id(self.switch_mover.content_server_switch_id))
                    distance = controller_utils.get_distance(src_id, dst_id)
                    if distance is None:
                        print("Switch %d has no connection to the content server." % switch)
                        distance = -1
                    else:
                        distance = distance + 1
                else:
                    # It is the switch connected to content server.
                    distance = 0
                hop_counts_to_server[switch_relative_id] = distance
            except Exception as e:
                print(traceback.format_exc())

            divider_part[switch_relative_id] = PARAMETER_DIVISION + (
                0 if switch in self.caching_switches else COST_START) + (
                                                   0 if switch in self.cached_switches else COST_CACHE_FILL)
            # Energy
            energy_weight = WEIGHT_ENERGY - (COST_CONTENT_SERVER if switch else 0)
            energy_component[switch_relative_id] = energy_weight * self.drone_battery_manager.get_switch_battery(
                switch) / max_battery_level

        # Normalize connectivity between 0 1
        max_self_link_capacity = max(self_link_capacities.max(), 1)
        max_total_neighbors_link_capacity = max(neighbors_total_link_capacities.max(), 1)
        max_hop_counts_to_server = max(hop_counts_to_server.max(), 1)
        self_link_capacities = self_link_capacities / max_self_link_capacity
        neighbors_total_link_capacities = neighbors_total_link_capacities / max_total_neighbors_link_capacity
        hop_counts_to_server = hop_counts_to_server / max_hop_counts_to_server

        connectivity_component = WEIGHT_CONNECTIVITY * np.add(
            np.add(WEIGHT_SELF_CAPACITY * self_link_capacities,
                   WEIGHT_NEIGHBOUR_CAPACITY * neighbors_total_link_capacities),
            WEIGHT_HOP_COUNT * hop_counts_to_server)

        scores = np.divide(np.add(energy_component, connectivity_component), divider_part)

        relative_switch_ids_with_highest_scores = np.argpartition(scores, -number_of_switches_caching)[
                                                  -number_of_switches_caching:].astype(int).tolist()
        relative_switch_ids_with_highest_scores.sort()
        self.caching_switches = [self.switch_mover.operating_switches[relativeSwitchID] for relativeSwitchID in
                                 relative_switch_ids_with_highest_scores]
        for switch in self.caching_switches:
            if switch not in self.cached_switches:
                self.cached_switches.append(switch)
        # print(self.caching_switches)
        # print(scores)


if __name__ == '__main__':
    switch_operator = SwitchOperator()
    switch_operator.select_caching_nodes()
    switch_operator.get_switch_overheads()
    switch_operator.update_device_coordinates_on_controller()
