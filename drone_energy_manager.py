import numpy as np
from settings import *
import time


class DroneEnergyManager(object):
    battery_levels = []
    depleted_battery_ids = np.array([])
    number_of_drones = NUM_OF_DRONES
    simulation_start_time = 0

    def __init__(self, number_of_drones=NUM_OF_DRONES):
        self.number_of_drones = number_of_drones
        self.battery_levels = np.full(number_of_drones, INITIAL_DRONE_BATTERY_CAPACITY, dtype=float)
        self.simulation_start_time = str(int(time.time() // 10))
        self.energy_consumption_statistics = np.full((number_of_drones, 5), 0, dtype=float)

    def print_energy_consumption_statistics_to_file(self, current_time):
        file_name = "energyConsumption/%d.npy" % current_time
        np.save(file_name, self.energy_consumption_statistics)

    def add_extra_battery(self, drone_id):
        self.battery_levels[drone_id] = INITIAL_DRONE_BATTERY_CAPACITY * 1.25

    def check_for_depleted_batteries(self):
        temp_depleted_battery_ids = np.where(self.battery_levels <= 0)[0].tolist()
        new_depleted_battery_ids = np.setdiff1d(temp_depleted_battery_ids, self.depleted_battery_ids)
        if new_depleted_battery_ids.size > 0:
            self.depleted_battery_ids = temp_depleted_battery_ids
            return new_depleted_battery_ids.tolist()

    def check_for_single_battery(self, drone_id):
        if self.battery_levels[drone_id] <= 0:
            return self.check_for_depleted_batteries()

    def decrease_battery_fly(self):
        energy = POWER_FLY
        self.battery_levels -= energy
        self.energy_consumption_statistics[
            [i for i in range(self.number_of_drones) if not i in self.depleted_battery_ids], 0] += energy
        # return self.checkForDepletedBatteries()

    def decrease_battery_tx(self, drone_id, current_time):
        current_time = current_time if current_time > 0 else 0
        energy = current_time * POWER_TX
        self.battery_levels[drone_id] -= energy
        self.energy_consumption_statistics[drone_id, 1] += energy
        return energy

    def decrease_battery_read(self, drone_id, data_size):
        energy = data_size * POWER_READ
        self.battery_levels[drone_id] -= energy
        self.energy_consumption_statistics[drone_id, 2] += energy
        return energy

    def decrease_battery_write(self, drone_id, data_size):
        energy = data_size * POWER_WRITE
        self.battery_levels[drone_id] -= energy
        self.energy_consumption_statistics[drone_id, 3] += energy
        return energy

    def decrease_battery_process_packet(self, drone_id, packet_number):
        energy = packet_number * POWER_PROCESS_PACKET
        self.battery_levels[drone_id] -= energy
        self.energy_consumption_statistics[drone_id, 4] += energy
        return energy

    def get_max_battery_level(self):
        return self.battery_levels.max()

    def get_drone_battery(self, drone_id):
        return self.battery_levels[drone_id]

    def route_cost_energy(self, transmission_info, cache_write_drone_list, data_size, cache_read_drone=None):
        route_cost = 0
        e_max = self.battery_levels.max()

        for drone_and_transmission_time in transmission_info:
            route_cost += e_max / self.get_drone_battery(drone_and_transmission_time[0]) * POWER_TX * \
                          drone_and_transmission_time[1]
        for droneID in cache_write_drone_list:
            route_cost += e_max / self.get_drone_battery(droneID) * POWER_WRITE * data_size
        if cache_read_drone:
            route_cost += e_max / self.get_drone_battery(cache_read_drone) * POWER_WRITE * data_size

        return route_cost


if __name__ == '__main__':
    drone_battery_manager = DroneEnergyManager()
    drone_battery_manager.decrease_battery_fly()
    drone_battery_manager.decrease_battery_fly()
    drone_battery_manager.battery_levels[3] = -2
    a = drone_battery_manager.check_for_depleted_batteries()
    print a
    a = drone_battery_manager.check_for_depleted_batteries()
    print a
    print(drone_battery_manager.battery_levels)
