import glob
import logging
import os
import pickle

from actors.Simulation import Simulation

RESULT_FILENAME = "results/164237026.pickle"


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
               }
    return results


def get_simulation_results(filename=RESULT_FILENAME):
    try:
        with open(filename, 'rb') as handle:
            return pickle.load(handle)
    except (EOFError, FileNotFoundError) as e:
        logging.error("Couldn't get simulation results from file. %s", e)
        return {}


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    list_of_files = glob.glob('results/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    sim_results = get_simulation_results(latest_file)
    logging.info(f"Current time: {sim_results['current_time']}")
    for task in sim_results["tasks"]:
        logging.info(task)
