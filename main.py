#!/usr/bin/python

"""UAVs providing network to vehicles."""
import argparse
import logging
import time

from mininet.log import setLogLevel
from mininet.term import makeTerms

import controller_utils
import settings as s
from TaskGenerator import TaskGenerator
from TaskOrganizer import TaskOrganizer, AssignmentMethod
from actors.Record import SimulationRecord
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
from utils import get_wait_time, write_as_pickle, get_settings_to_simulation_object, get_simulation_record, \
    get_solution

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
        write_as_pickle(create_simulation_results_data(), Simulation.results_file_name)
        wait_time = get_wait_time(step_start_time, step_end_time, s.SIMULATION_STEP_DELAY / 1000.0)
        time.sleep(wait_time)


def start_host_roles(new_net):
    Simulation.task_assigner_host.popen("python listen_tasks.py")
    for station in new_net.stations:
        station.popen("ping %s" % Simulation.task_assigner_host_ip)
        # station.popen("ping %s" % Simulation.cloud_server_ip)
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


def parse_cli_arguments():
    parser = argparse.ArgumentParser("Simulate network")
    parser.add_argument('-m', '--mode', type=str,
                        help="Assignment mode",
                        default=s.ASSIGNMENT_METHOD)
    parser.add_argument('-r', '--request-interval', type=int, help="Request interval in seconds",
                        default=s.TASK_GENERATION_INTERVAL)
    parser.add_argument('--seed-no', type=int, help="Randomness seed no", default=s.SUMO_SEED_TO_USE)
    parser.add_argument('--wait-previous-queue', type=bool, help="Wait previous task to be processed",
                        default=s.WAIT_PREVIOUS_TASK_TO_BE_PROCESSED, action=argparse.BooleanOptionalAction)
    parser.add_argument("-l", "--log", dest="log_level", choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level", default=s.LOG_LEVEL)
    parser.add_argument('--record-file', type=str, help="Record file to use to import tasks and vehicle assignments")
    return parser.parse_args()


def apply_arguments(arguments):
    s.ASSIGNMENT_METHOD = arguments.mode.upper()
    Simulation.settings['ASSIGNMENT_METHOD'] = s.ASSIGNMENT_METHOD
    s.TASK_GENERATION_INTERVAL = arguments.request_interval
    Simulation.settings['TASK_GENERATION_INTERVAL'] = s.TASK_GENERATION_INTERVAL
    s.SUMO_SEED_TO_USE = arguments.seed_no
    Simulation.settings['SUMO_SEED_TO_USE'] = s.SUMO_SEED_TO_USE
    s.DRONE_ID_CLOSE_TO_BS = arguments.seed_no
    Simulation.settings['DRONE_ID_CLOSE_TO_BS'] = s.DRONE_ID_CLOSE_TO_BS

    s.WAIT_PREVIOUS_TASK_TO_BE_PROCESSED = arguments.wait_previous_queue
    Simulation.settings['WAIT_PREVIOUS_TASK_TO_BE_PROCESSED'] = s.WAIT_PREVIOUS_TASK_TO_BE_PROCESSED
    logging.basicConfig(level=getattr(logging, arguments.log_level.upper()),
                        format="%(asctime)s %(levelname)s -> %(message)s")
    Simulation.settings['LOG_LEVEL'] = arguments.log_level.upper()

    if arguments.record_file:
        s.USE_RECORD = True
        Simulation.settings['USE_RECORD'] = True
        s.RECORD_FILE = arguments.record_file
        Simulation.settings['RECORD_FILE'] = s.RECORD_FILE


def set_output_file_names():
    if s.USE_RECORD:
        record_file_representation = s.RECORD_FILE
        if '/' in record_file_representation:
            record_file_representation = record_file_representation.split('/')[-1]
        Simulation.results_file_name = \
            f"results/result_{s.ASSIGNMENT_METHOD}_wait{s.WAIT_PREVIOUS_TASK_TO_BE_PROCESSED}_" \
            f"{record_file_representation}___{Simulation.real_life_start_time}.pickle"
    else:
        Simulation.results_file_name = \
            f"results/result_{s.ASSIGNMENT_METHOD}_wait{s.WAIT_PREVIOUS_TASK_TO_BE_PROCESSED}_" \
            f"lambda{s.TASK_GENERATION_INTERVAL}_seed{s.SUMO_SEED_TO_USE}_{Simulation.real_life_start_time}.pickle"
    logging.info(f"Results file: {Simulation.results_file_name}")


if __name__ == '__main__':
    Simulation.settings = get_settings_to_simulation_object()
    cli_arguments = parse_cli_arguments()
    apply_arguments(cli_arguments)
    set_output_file_names()
    Simulation.record_file_name = f"records/{s.CASE}/lambda{s.TASK_GENERATION_INTERVAL}_seed{s.SUMO_SEED_TO_USE}"
    controller_utils.delete_all_links()
    setLogLevel(s.MN_WIFI_LOG_LEVEL.lower())
    Simulation.record = SimulationRecord(Simulation.simulation_id, Simulation.real_life_start_time,
                                         s.SKIPPED_STEPS + 1, s.SIMULATION_DURATION)
    if s.USE_RECORD:
        Simulation.old_record = get_simulation_record(s.RECORD_FILE)
        vehicle_records = Simulation.old_record.vehicles
        task_records = Simulation.old_record.tasks
        # s.SUMO_SEED_TO_USE = Simulation.old_record["settings"]["SUMO_SEED_TO_USE"]
        # s.DRONE_ID_CLOSE_TO_BS = s.SUMO_SEED_TO_USE
        # s.SUMO_CFG_PATH = Simulation.old_record["settings"]["SUMO_CFG_PATH"]
        logging.info(f"Using record file: {s.RECORD_FILE}")
    else:
        vehicle_records = None
        task_records = None
    if AssignmentMethod(s.ASSIGNMENT_METHOD) == AssignmentMethod.OPTIMUM:
        solution = get_solution(s.RECORD_FILE)
    else:
        solution = None
    Simulation.task_generator = TaskGenerator(task_records=task_records)
    Simulation.task_organizer = TaskOrganizer(solution=solution)
    current_drone_mover = DroneMover()
    drone_operator = DroneOperator(current_drone_mover)
    net = create_topology(current_drone_mover)
    manager = SumoManager(vehicle_records=vehicle_records)
    add_aps_as_poi_to_sumo(net, manager)
    drone_operator.send_host_coordinates_on_controller(net)
    if s.START_XTERM:
        makeTerms(net.stations, 'station')
        makeTerms(net.hosts, 'host')

    start_host_roles(net)
    # CLI(net)
    simulate_sumo(manager, current_drone_mover)
    if not s.USE_RECORD:
        write_as_pickle(Simulation.record, Simulation.record_file_name)
    # CLI(net)
    # handle_tasks()
    write_as_pickle(create_simulation_results_data(), Simulation.results_file_name)
    net.stop()
    del manager
    # subprocess.call(["python", "clean.py"])
    stop_children_processes([])
