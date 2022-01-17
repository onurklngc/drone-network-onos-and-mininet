import glob
import logging
import os
import pickle
import time

from tabulate import tabulate

from actors.Simulation import Simulation
from actors.Task import Status
from actors.constant import Color

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
        with open(filename, 'rb') as handle:
            return pickle.load(handle)
    except (EOFError, FileNotFoundError) as e:
        logging.error("Couldn't get simulation results from file. %s", e)
        return {}


def print_results(sim_results):
    headers = ["Task No", "Status", "Owner-Processor", "Timeline", "Delay"]
    rows = []
    settings_to_print = f'Time:{sim_results["current_time"]}\tMethod:{sim_results["settings"]["ASSIGNMENT_METHOD"]}\t' \
                        f'Task Interval:{sim_results["settings"]["TASK_GENERATION_INTERVAL"]}'
    for task in sim_results["tasks"]:
        if task.status in [Status.COMPLETED, Status.PROCESSING]:
            delay = f"Delay:{task.delay:.1f} Prioritized delay: {task.priority * task.delay:.1f}"
        else:
            delay = ""
        status = task.status.name
        if task.status == Status.COMPLETED:
            status = f"{Color.GREEN}{status}{Color.ENDC}"
        elif task.status in [Status.OWNER_LEFT, Status.PROCESSOR_LEFT]:
            status = f"{Color.RED}{status}{Color.ENDC}"
        processor = f"{Color.BLUE}cloud{Color.ENDC}" if task.is_assigned_to_cloud else task.assigned_processor

        rows.append([f"{task.no}", status, f"{task.owner}->{processor}", task.get_timeline(), delay])

    logging.info(f'{settings_to_print}\n'
                 f'{tabulate(rows, headers, tablefmt="pretty", stralign="left")}\n'
                 f'{settings_to_print}')


def get_latest_simulation_file():
    list_of_files = glob.glob('results/*')
    return max(list_of_files, key=os.path.getctime)


def tail_results(filename):
    while True:
        if SWITCH_TO_LATEST_SIMULATION:
            filename = get_latest_simulation_file()
        sim_results = get_simulation_results(filename)
        print_results(sim_results)
        time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    if RESULT_FILENAME:
        result_file_to_view = RESULT_FILENAME
    else:
        result_file_to_view = get_latest_simulation_file()
    results = get_simulation_results(result_file_to_view)
    print_results(results)
    input("Press Enter to continue...")
    tail_results(result_file_to_view)
