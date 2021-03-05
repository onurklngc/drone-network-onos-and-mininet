import numpy as np
from settings import *
import time

INITIAL_DRONE_BATTERY_CAPACITY = 187545.6  # Joule(Ws) 0.8 * 65.12Wh=4.4Ah@14.8V %20 Reserved
POWER_FLY = 174.34  # Watt INITIAL_DRONE_BATTERY_CAPACITY/(22.41*60)sec
# Flight time is 17.93 if 20% reserved.
POWER_TX = 5 * DATA_SCALING  # Watt
POWER_WRITE = 2.34375e-05 * DATA_SCALING  # per Kb 3V*0.2A=0.6W/ 25MBbps
POWER_READ = 7.8125e-06 * DATA_SCALING  # per Kb # 1V*0.2A=0.2W/ 25MBps
POWER_PROCESS_PACKET = 7.8125e-06 * 1500 * DATA_SCALING


class BatteryCapacityLogger(object):
    battery_levels = []
    depleted_battery_ids = np.array([])
    switch_number = NUMBER_OF_SWITCHES
    simulation_start_time = 0

    def __init__(self, switch_number=NUMBER_OF_SWITCHES):
        self.switch_number = switch_number
        self.battery_levels = np.full(switch_number, INITIAL_DRONE_BATTERY_CAPACITY, dtype=float)
        self.simulation_start_time = str(int(time.time() // 10))
        self.energy_consumption_statistics = np.full((switch_number, 5), 0, dtype=float)

    def print_battery_levels_to_file(self, file_name=None):
        if file_name is None:
            file_name = "batteryLogs/%s-%.1f-%.1f-%.1f.csv" % (self.simulation_start_time,
                                                               WEIGHT_SELF_CAPACITY, WEIGHT_NEIGHBOUR_CAPACITY,
                                                               WEIGHT_HOP_COUNT)
        with open(file_name, "ab+") as f:
            np.savetxt(f, self.battery_levels, newline=",")
            f.write("\n")

    def print_proportional_battery_levels_to_file(self, file_name, current_time):
        with open(file_name, "ab+") as f:
            battery_capacities_with_time_tag = [current_time]
            battery_capacities_with_time_tag.extend([i / INITIAL_DRONE_BATTERY_CAPACITY for i in self.battery_levels])
            np.savetxt(f, battery_capacities_with_time_tag, newline=",")
            f.write("\n")

    def print_energy_consumption_statistics_to_file(self, current_time):
        file_name = "energyConsumption/%d.npy" % current_time
        np.save(file_name, self.energy_consumption_statistics)

    def add_extra_battery(self, switch_id):
        self.battery_levels[switch_id] = INITIAL_DRONE_BATTERY_CAPACITY * 1.25

    def check_for_depleted_batteries(self):
        temp_depleted_battery_ids = np.where(self.battery_levels <= 0)[0].tolist()
        new_depleted_battery_ids = np.setdiff1d(temp_depleted_battery_ids, self.depleted_battery_ids)
        if new_depleted_battery_ids.size > 0:
            self.depleted_battery_ids = temp_depleted_battery_ids
            return new_depleted_battery_ids.tolist()

    def check_for_single_battery(self, switch_id):
        if self.battery_levels[switch_id] <= 0:
            return self.check_for_depleted_batteries()

    def decrease_battery_fly(self):
        self.print_battery_levels_to_file()
        energy = MOVE_EVENT_INTERVALS * POWER_FLY
        self.battery_levels -= energy
        self.energy_consumption_statistics[
            [i for i in range(self.switch_number) if not i in self.depleted_battery_ids], 0] += energy
        # return self.checkForDepletedBatteries()

    def decrease_battery_tx(self, switch_id, current_time):
        current_time = current_time if current_time > 0 else 0
        energy = current_time * POWER_TX
        self.battery_levels[switch_id] -= energy
        self.energy_consumption_statistics[switch_id, 1] += energy
        return energy

    def decrease_battery_read(self, switch_id, data_size):
        energy = data_size * POWER_READ
        self.battery_levels[switch_id] -= energy
        self.energy_consumption_statistics[switch_id, 2] += energy
        return energy

    def decrease_battery_write(self, switch_id, data_size):
        energy = data_size * POWER_WRITE
        self.battery_levels[switch_id] -= energy
        self.energy_consumption_statistics[switch_id, 3] += energy
        return energy

    def decrease_battery_process_packet(self, switch_id, packet_number):
        energy = packet_number * POWER_PROCESS_PACKET
        self.battery_levels[switch_id] -= energy
        self.energy_consumption_statistics[switch_id, 4] += energy
        return energy

    def get_max_battery_level(self):
        return self.battery_levels.max()

    def get_switch_battery(self, switch_id):
        return self.battery_levels[switch_id]

    def route_cost_energy(self, transmission_info, cache_write_switch_list, data_size, cache_read_switch=None):
        route_cost = 0
        e_max = self.battery_levels.max()

        for switch_and_transmission_time in transmission_info:
            route_cost += e_max / self.get_switch_battery(switch_and_transmission_time[0]) * POWER_TX * \
                          switch_and_transmission_time[1]
        for switchID in cache_write_switch_list:
            route_cost += e_max / self.get_switch_battery(switchID) * POWER_WRITE * data_size
        if cache_read_switch:
            route_cost += e_max / self.get_switch_battery(cache_read_switch) * POWER_WRITE * data_size

        return route_cost


if __name__ == '__main__':
    drone_battery_manager = BatteryCapacityLogger()
    drone_battery_manager.decrease_battery_fly()
    drone_battery_manager.decrease_battery_fly()
    drone_battery_manager.decrease_battery_fly()
    drone_battery_manager.battery_levels[3] = -2
    a = drone_battery_manager.check_for_depleted_batteries()
    print a
    a = drone_battery_manager.check_for_depleted_batteries()
    print a
    print(drone_battery_manager.battery_levels)
