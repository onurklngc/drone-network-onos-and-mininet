import glob
import logging
import os
import time

from tabulate import tabulate

import settings as s
from actors.Simulation import Simulation
from actors.Task import Status
from actors.constant import Color
from utils import read_pickle_file

RESULT_FILENAME = ""
SWITCH_TO_LATEST_SIMULATION = True


def create_simulation_results_data():
    # for vehicle in Simulation.all_vehicles:
    #     vehicle.station = vehicle.station.name
    results = {"settings": Simulation.settings,
               "current_time": Simulation.current_time,
               "simulation_id": Simulation.simulation_id,
               "tasks": [task.get_result() for task in Simulation.tasks],
               # "vehicles": Simulation.all_vehicles,
               "drone_id_close_to_bs": Simulation.drone_id_close_to_bs,
               "events": Simulation.events,
               "number_of_reassigned_tasks": Simulation.number_of_reassigned_tasks,
               "upload_outputs": Simulation.upload_reports
               }
    return results


def get_simulation_results(filename=RESULT_FILENAME):
    try:
        return read_pickle_file(filename)
    except (EOFError, FileNotFoundError) as e:
        logging.error("Couldn't get simulation results from file. %s", e)
        return {}


def print_results(result_file_name, sim_results):
    total_weighted_penalty = 0
    headers = ["Task No", "Status", "Owner-Processor", "Timeline", "Deadline", "Penalty", "Priority",
               "Weighted Penalty"]
    rows = []
    settings_to_print = f'Name:{result_file_name}\tTime:{sim_results["current_time"]}\t' \
                        f'Method:{sim_results["settings"]["ASSIGNMENT_METHOD"]}\t' \
                        f'Task Interval:{sim_results["settings"]["TASK_GENERATION_INTERVAL"]}'
    for task in sim_results["tasks"]:
        if task.status in [Status.COMPLETED, Status.PROCESSING]:
            penalty = f"{task.penalty:.1f}"
        elif task.status == Status.OWNER_LEFT:
            task.penalty = task.owner_departure_time - task.deadline + s.TASK_FAILURE_PENALTY_OFFSET
            penalty = f"{task.penalty:.1f}"
        else:
            penalty = ""
        status = task.status.name
        if task.status == Status.COMPLETED:
            status = f"{Color.GREEN}{status}{Color.ENDC}"
        elif task.status in [Status.OWNER_LEFT, Status.PROCESSOR_LEFT]:
            status = f"{Color.RED}{status}{Color.ENDC}"
        processor = f"{Color.BLUE}cloud{Color.ENDC}" if task.is_assigned_to_cloud else task.assigned_processor
        if task.penalty:
            weighted_priority = max(0, task.penalty * task.priority)
            total_weighted_penalty += weighted_priority
            weighted_priority = f"{weighted_priority:.0f}"
        else:
            weighted_priority = ""
        rows.append([f"{task.no}", status, f"{task.owner}->{processor}", task.get_timeline(), task.deadline, penalty,
                     task.priority, weighted_priority])
    logging.info(f'{settings_to_print}\n'
                 f'{tabulate(rows, headers, tablefmt="pretty", stralign="left")}\n'
                 f'{settings_to_print}\t\t Total weighted penalty: {total_weighted_penalty:.1f}')


def get_latest_simulation_file():
    list_of_files = glob.glob('results/*')
    return max(list_of_files, key=os.path.getctime)


def tail_results(filename):
    while True:
        if SWITCH_TO_LATEST_SIMULATION:
            filename = get_latest_simulation_file()
        sim_results = get_simulation_results(filename)
        print_results(filename, sim_results)
        time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    if RESULT_FILENAME:
        result_file_to_view = RESULT_FILENAME
    else:
        result_file_to_view = get_latest_simulation_file()
    results = get_simulation_results(result_file_to_view)
    print_results(result_file_to_view, results)
    input("Press Enter to continue...")
    tail_results(result_file_to_view)
