#!/usr/bin/python

"""UAVs providing network to vehicles."""
import logging
import os
import time

from mininet.log import setLogLevel
from mininet.term import makeTerms
from mn_wifi.cli import CLI

import controller_utils
import settings as s
from TaskGenerator import TaskGenerator
from TaskOrganizer import TaskOrganizer
from actors.Simulation import Simulation
from clean import stop_children_processes
from drone_movement import DroneMover
from drone_operator import DroneOperator
from manage_tasks import handle_tasks
from mn_interface import update_drone_locations_on_mn, update_station_locations_on_mn, vehicle_to_mn_sta, \
    create_topology, \
    check_station_connections
from results import create_simulation_results_data
from sumo_interface import disassociate_sumo_vehicles_leaving_area, \
    associate_sumo_vehicles_with_mn_stations, update_drone_locations_on_sumo, add_aps_as_poi_to_sumo
from sumo_traci import SumoManager
from utils import get_wait_time, write_simulation_results, get_settings_to_simulation_object

simulation_id = str(int(time.time() // 10))
processes = []


def estimate_access_point_locations(vehicle_data_list):
    logging.debug(vehicle_data_list)


def simulate_sumo(sumo_manager, drone_mover):
    if s.SKIPPED_STEPS:
        sumo_manager.move_simulation_to_step(s.SKIPPED_STEPS)
    current_time = sumo_manager.get_time()
    for step in range(s.SIMULATION_DURATION - s.SKIPPED_STEPS + 1):
        step_start_time = time.time()
        current_time += 1
        sumo_manager.wait_simulation_step()
        Simulation.current_time = current_time
        logging.info("Current step: %s", Simulation.current_time)
        drone_mover.move_drones_for_one_time_interval(Simulation.current_time)
        # logging.info("Time it")
        update_drone_locations_on_mn(drone_mover)
        # logging.info("Time it 2")
        served_vehicle_data_list, vehicles_just_left_area = sumo_manager.get_vehicle_states()
        disassociate_sumo_vehicles_leaving_area(vehicles_just_left_area, vehicle_to_mn_sta)
        associate_sumo_vehicles_with_mn_stations(current_time, sumo_manager, served_vehicle_data_list,
                                                 vehicle_to_mn_sta)
        # estimate_access_point_locations(served_vehicle_data_list)
        # logging.info("Time it 3")
        update_station_locations_on_mn(served_vehicle_data_list)
        drone_operator.update_station_coordinates_on_controller(net)
        # logging.info("Time it 3.2")
        check_station_connections()
        # logging.info("Time it 4")
        # randomly_move_drones()
        update_drone_locations_on_sumo(net, sumo_manager)
        # logging.info("Time it 5")
        if s.UPDATE_SW_LOCATIONS_ON_ONOS:
            drone_operator.update_device_coordinates_on_controller(net)
        # logging.info("Time it 6")
        handle_tasks()
        # logging.info("Time it 7")
        step_end_time = time.time()
        wait_time = get_wait_time(step_start_time, step_end_time, s.SIMULATION_STEP_DELAY / 1000.0)
        write_simulation_results(create_simulation_results_data(), Simulation.results_file_name)
        time.sleep(wait_time)


def start_host_roles(new_net):
    Simulation.task_assigner_host.popen("python listen_tasks.py")
    for station in new_net.stations:
        station.popen("ping %s" % Simulation.task_assigner_host_ip)
        station.popen("ping %s" % Simulation.cloud_server_ip)
    # if s.CLOUD_SERVER == "BS_HOST":
    #     Simulation.cloud_iperf_process = Simulation.cloud_server.popen("iperf -s -y C")


def stop_servers():
    if Simulation.cloud_iperf_process:
        Simulation.cloud_iperf_process.wait()
        out, err = Simulation.cloud_iperf_process.communicate()
        logging.info(f"Cloud iperf server log out: {out}\nerr:{err}")
        log_file_name = f'logs_iperf/{Simulation.real_life_start_time}_cloud_server.log'
        with open(log_file_name, 'wb') as log_file:
            log_file.write(out)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    Simulation.settings = get_settings_to_simulation_object()
    os.mkdir(f"logs_iperf/{Simulation.real_life_start_time}")
    controller_utils.delete_all_links()
    setLogLevel(s.MN_WIFI_LOG_LEVEL.lower())
    Simulation.task_organizer = TaskOrganizer()
    Simulation.task_generator = TaskGenerator()
    current_drone_mover = DroneMover()
    drone_operator = DroneOperator(current_drone_mover)
    net = create_topology(current_drone_mover)
    manager = SumoManager()
    add_aps_as_poi_to_sumo(net, manager)
    drone_operator.send_host_coordinates_on_controller(net)
    makeTerms(net.stations, 'station')
    makeTerms(net.hosts, 'host')

    start_host_roles(net)
    # CLI(net)
    simulate_sumo(manager, current_drone_mover)
    # stop_servers()
    write_simulation_results(create_simulation_results_data(), Simulation.results_file_name)
    CLI(net)
    del manager
    net.stop()
    stop_children_processes([])
