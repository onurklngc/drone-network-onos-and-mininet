import glob
import logging
import pickle

import numpy as np
from tabulate import tabulate

from actors.Task import Status

TABLE_FORMAT = "simple"

REQUEST_INTERVAL_FILE_LIST = {
    "Optimum": "/home/onur/Coding/projects/sdnCaching/solutions/request_interval",
    "Adaptive": "/home/onur/Coding/projects/sdnCaching/results/request_interval/adaptive",
    "Aggressive": "/home/onur/Coding/projects/sdnCaching/results/request_interval/aggressive",
    "Aggressive-Wait": "/home/onur/Coding/projects/sdnCaching/results/request_interval/aggressive-wait",
    "Only-Cloud": "/home/onur/Coding/projects/sdnCaching/results/request_interval/only-cloud",
}
VEHICLE_SPEED_FILE_LIST = {
    "Optimum": "/home/onur/Coding/projects/sdnCaching/solutions/vehicle_speed",
    "Adaptive": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed/adaptive",
    "Aggressive": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed/aggressive",
    "Aggressive-Wait": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed/aggressive-wait",
}
VEHICLE_SPEED_V2_FILE_LIST = {
    "Optimum": "/home/onur/Coding/projects/sdnCaching/solutions/vehicle_speed_v2",
    "Adaptive": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed_v2/adaptive",
    "Aggressive": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed_v2/aggressive",
    "Aggressive-Wait": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed_v2/aggressive-wait",
    "Only-Cloud": "/home/onur/Coding/projects/sdnCaching/results/vehicle_speed_v2/only-cloud",

}
PROCESS_SPEED_FILE_LIST = {
    "Optimum": "/home/onur/Coding/projects/sdnCaching/solutions/process_speed",
    "Adaptive": "/home/onur/Coding/projects/sdnCaching/results/process_speed/adaptive",
    "Aggressive": "/home/onur/Coding/projects/sdnCaching/results/process_speed/aggressive",
    "Aggressive-Wait": "/home/onur/Coding/projects/sdnCaching/results/process_speed/aggressive-wait",
}
ORDERING = {
    "process_speed": ["slow", "medium", "fast"],
    "request_interval": ["5", "10", "15"],
    "vehicle_speed": ["5", "20", "40"]
}


def read_pickle_file(filename):
    with open(filename, 'rb') as handle:
        return pickle.load(handle)


def get_multiple_files(files):
    data_obtained = {}

    for group_name, group_path in files.items():
        data_obtained[group_name] = {}
        list_of_folders = glob.glob(group_path + "/*")
        for folder_path in list_of_folders:
            folder_name = folder_path.split("/")[-1]
            data_obtained[group_name][folder_name] = []
            list_of_files = glob.glob(folder_path + "/*")
            for file_path in list_of_files:
                data_obtained[group_name][folder_name].append(read_pickle_file(file_path))
    return data_obtained


def get_specific_tasks(results, assignment_method, subsection_name):
    specific_results = results[assignment_method][subsection_name]
    tasks = []
    for result in specific_results:
        tasks_by_run = result["tasks"] if isinstance(result, dict) else result.tasks
        tasks.extend(tasks_by_run)
    return tasks


def get_prioritized_penalties(tasks):
    penalties = []
    for task in tasks:
        penalties.append(task.get_prioritized_penalty())
    return penalties


def get_total_prioritized_penalty(tasks):
    total_penalty = 0
    for task in tasks:
        total_penalty += task.get_prioritized_penalty()
    return total_penalty


def get_system_delays(tasks):
    delays = []
    for task in tasks:
        if task.status in [Status.COMPLETED, Status.PROCESSING]:
            delays.append(task.end_time - task.start_time)
    return delays


def get_completed_task_deadlines(tasks):
    delays = []
    for task in tasks:
        if task.status in [Status.COMPLETED, Status.PROCESSING]:
            delays.append(task.deadline - task.start_time)
    return delays


def get_penalties(tasks):
    delays = []
    for task in tasks:
        if task.status in [Status.COMPLETED]:
            delays.append(task.penalty)
    return delays


def get_average_system_times(tasks):
    total_delay = 0
    total_pool_time = 0
    total_tx_time = 0
    total_queue_time = 0
    total_process_time = 0
    task_counter = 0
    for task in tasks:
        if task.status in [Status.COMPLETED, Status.PROCESSING]:
            task_counter += 1
            pool_time = task.tx_start_time - task.start_time
            tx_time = task.tx_end_time - task.tx_start_time
            queue_time = task.process_start_time - task.tx_end_time
            process_time = task.process_end_time - task.process_start_time
            total_pool_time += pool_time
            total_tx_time += tx_time
            total_queue_time += queue_time
            total_process_time += process_time
            task_delay = task.end_time - task.start_time
            if task_delay < pool_time + tx_time + queue_time + process_time:
                pass
            total_delay += task_delay
    averages = {
        "average_delay": total_delay / task_counter,
        "average_pool_time": total_pool_time / task_counter,
        "average_tx_time": total_tx_time / task_counter,
        "average_queue_time": total_queue_time / task_counter,
        "average_process_time": total_process_time / task_counter,
    }
    return averages


def get_average_prioritized_penalties(tasks):
    total_penalty = get_total_prioritized_penalty(tasks)
    average_penalty = total_penalty / len(tasks)
    return average_penalty


def get_deadline_met_ratio(prioritized_penalties):
    total = 0
    counter_deadline_met = 0
    for prioritized_penalty in prioritized_penalties:
        total += 1
        if prioritized_penalty == 0:
            counter_deadline_met += 1
    return counter_deadline_met / total


def get_ratio_of_failed_tasks(tasks):
    task_counter = 0
    for task in tasks:
        if task.status not in [Status.COMPLETED, Status.PROCESSING]:
            task_counter += 1

    return task_counter / len(tasks)


def get_ratio_of_tasks_assigned_to_cloud(tasks):
    task_counter = 0
    for task in tasks:
        if task.is_assigned_to_cloud:
            task_counter += 1
    return task_counter / len(tasks)


def get_category_delays(title, results):
    headers = ["Category", "Method", "AveragePrioritizedPenalty", "Std_Prioritized_Penalty",  # "Deadline_met_ratio",
               "Task_Failure_Ratio",
               "Cloud_Ratio", "Average_Delay",
               "Average_Pool_Time", "Average_Tx_Time", "Average_Queue_Time", "Average_Process_Time"]
    rows = []
    is_category_int = True
    for method_name, method_data in results.items():
        for category, category_results in method_data.items():
            is_category_int = category.isdigit()
            tasks = get_specific_tasks(results, method_name, category)
            if not tasks:
                continue
            prioritized_penalties = get_prioritized_penalties(tasks)
            avg_prioritized_penalty = np.mean(prioritized_penalties)
            std_prioritized_penalty = np.std(prioritized_penalties)
            deadline_met_ratio = get_deadline_met_ratio(prioritized_penalties)

            ratio_of_failed_tasks = get_ratio_of_failed_tasks(tasks)
            ratio_of_tasks_assigned_to_cloud = get_ratio_of_tasks_assigned_to_cloud(tasks)
            delay_averages = get_average_system_times(tasks)

            rows.append([method_name, category, f"{avg_prioritized_penalty:.2f}",
                         f"{std_prioritized_penalty:.2f}",
                         # f"{deadline_met_ratio:.3f}",
                         f"{ratio_of_failed_tasks:.3f}",
                         f"{ratio_of_tasks_assigned_to_cloud:.3f}", f"{delay_averages['average_delay']:.2f}",
                         f"{delay_averages['average_pool_time']:.2f}", f"{delay_averages['average_tx_time']:.2f}",
                         f"{delay_averages['average_queue_time']:.0f}",
                         f"{delay_averages['average_process_time']:.2f}"])
    if is_category_int:
        rows.sort(key=lambda x: (x[0], int(x[1])))
    else:
        rows.sort(key=lambda x: (x[0], x[1]))
    logging.info(f'{title}\n{tabulate(rows, headers, tablefmt=TABLE_FORMAT, stralign="left")}')


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")

    result_data = get_multiple_files(VEHICLE_SPEED_V2_FILE_LIST)
    get_category_delays("Vehicle Speed", result_data)
    result_data = get_multiple_files(VEHICLE_SPEED_FILE_LIST)
    get_category_delays("Request Interval", result_data)
    # result_data = get_multiple_files(VEHICLE_SPEED_FILE_LIST)
    # get_category_delays("Vehicle Speed", result_data)
    # result_data = get_multiple_files(PROCESS_SPEED_FILE_LIST)
    # get_category_delays("Process Speed", result_data)
