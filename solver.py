import argparse
import itertools
import logging
from math import ceil

import numpy as np
from tabulate import tabulate

import settings as s
from actors.Solution import Action, Solution
from actors.Vehicle import ConnectionStatus
from utils import read_pickle_file, get_link_speed_by_rssi, write_as_pickle

record_file = "records/request_interval/lambda10_seed7"

TIME_WINDOW = 600
MAX_COMBINATION_TO_TRY_PER_WINDOW = 10000000
processor_records = {}
generator_records = {}
ap_records = {}
processors = {}
generators = {}
task_based_available_processors = {}
record = None
CLOUD = 0
earliest_next_task_start_tx_time = {CLOUD: 0}
traffics = {}
traffic_indices = {}
vehicle_by_traffic_index = {}


def count_possible_pairs(task_processor_pairing):
    counter = 0
    number_of_possibilities = 1
    for possible_processors in task_processor_pairing.values():
        number_of_possibilities *= len(possible_processors) + 1
        counter += len(possible_processors)
    logging.debug(f"Number of possible pairings: {counter}, possibilities: {number_of_possibilities}")
    return counter, number_of_possibilities


def find_smallest_sublist_length(given_list, desired_sum):
    sublist_sum = 0
    min_length = len(given_list)
    sublist_left_index = s.SKIPPED_STEPS

    for sublist_right_index in range(len(given_list)):
        sublist_sum += given_list[sublist_right_index]

        while sublist_sum > desired_sum and sublist_left_index <= sublist_right_index:
            min_length = min(min_length, sublist_right_index - sublist_left_index + 1)
            sublist_sum -= given_list[sublist_left_index]
            sublist_left_index = sublist_left_index + 1

    return min_length


def get_number_of_elements_sum_equal_to_given_number(given_list, desired_sum):
    sum = 0
    for index, element in enumerate(given_list):
        if sum > desired_sum:
            return index
        sum += element


def get_time_slots_sharing_same_ap(veh1, veh2):
    shared_slots = []
    for moment_time, moment in veh1.moments.items():
        if moment_time not in veh2.moments:
            continue
        if moment.associated_ap:
            if moment.associated_ap == veh2.moments[moment_time].associated_ap:
                shared_slots.append(moment_time)
    return shared_slots


def get_simulation_record(filename):
    global ap_records, traffics
    sim_record = read_pickle_file(filename)
    ap_records = sim_record.aps
    traffics = np.zeros((sim_record.sim_end_time + 1, len(sim_record.vehicles) + 1), dtype=int)
    traffic_index = 0
    for sumo_id, vehicle in sim_record.vehicles.items():
        traffic_index += 1
        if vehicle.type_abbreviation in s.PROCESSOR_VEHICLE_TYPES:
            processor_records[sumo_id] = vehicle
            vehicle.process_speed = s.VEHICLE_TYPE_PROPERTIES[vehicle.type_abbreviation]["process_speed"]
            vehicle.queue_size = s.VEHICLE_TYPE_PROPERTIES[vehicle.type_abbreviation]["queue_size"]

        else:
            generator_records[sumo_id] = vehicle
        vehicle.max_moment_bw = 0
        vehicle.bw = np.zeros(sim_record.sim_end_time + 2)
        if not vehicle.departure_time:
            vehicle.departure_time = sim_record.sim_end_time
        vehicle.departure_time -= 5
        if not vehicle.no_new_task_start_time:
            vehicle.no_new_task_start_time = sim_record.sim_end_time
        for moment_time, moment in vehicle.moments.items():
            if moment_time > vehicle.departure_time:
                break
            if moment.rssi and moment.connection_status == ConnectionStatus.CONNECTED and \
                    moment.associated_ap in sim_record.aps:
                moment.bw = get_link_speed_by_rssi(moment.rssi)
                sim_record.aps[moment.associated_ap].add_station(moment_time, sumo_id)
                vehicle.bw[moment_time] = moment.bw
                if sumo_id not in earliest_next_task_start_tx_time:
                    earliest_next_task_start_tx_time[sumo_id] = vehicle.entry_time
                if moment.bw > vehicle.max_moment_bw:
                    vehicle.max_moment_bw = moment.bw
        vehicle.index = traffic_index
        traffic_indices[vehicle.sumo_id] = vehicle.index
        vehicle_by_traffic_index[vehicle.index] = vehicle
    for task_no, task in sim_record.tasks.items():
        task.pair_bw = {}
        task_based_available_processors[task_no] = []
        owner = generator_records[task.owner_sumo_id]
        task.owner_object = owner
        owner_departure_time = owner.departure_time
        for processor in processor_records.values():
            owner_bw_for_task = owner.bw.copy()
            owner_bw_for_task[:task.start_time] = 0
            pair_bw = np.row_stack((owner_bw_for_task, processor.bw)).min(axis=0)
            time_slots_sharing_same_ap = get_time_slots_sharing_same_ap(owner, processor)
            task.pair_bw[processor.sumo_id] = pair_bw
            tmp_pair_bw = pair_bw.copy()
            for time_slot in time_slots_sharing_same_ap:
                tmp_pair_bw[time_slot] /= 2
            min_tx_time = find_smallest_sublist_length(tmp_pair_bw, task.size)
            # min_tx_time = task.size / owner.bw.max()
            if task.start_time + 60 < processor.entry_time:
                continue
            if owner_departure_time - min_tx_time > processor.entry_time:
                if task.start_time >= processor.no_new_task_start_time:
                    continue
                task_based_available_processors[task_no].append(processor)
    counter, number_of_possibilities = count_possible_pairs(task_based_available_processors)
    logging.info(f"Global: Number of possible pairings: {counter}, possibilities: {number_of_possibilities}")
    return sim_record


def get_estimated_tx_time_station_to_cloud(task_size, given_time, owner_object, temp_earliest_next_task_start_tx_time,
                                           temp_traffics):
    # given_time = max(temp_earliest_next_task_start_tx_time[CLOUD], given_time)
    if owner_object.departure_time <= given_time:
        return
    associated_ap = owner_object.get_moment(given_time).associated_ap
    if not associated_ap:
        return
    ap_moment = ap_records[associated_ap].get_moment(given_time)
    ap_load = 1
    for station in ap_moment.associated_stations:
        ap_load += temp_traffics[given_time][traffic_indices[station]]
    sta_side_tx_time = get_number_of_elements_sum_equal_to_given_number(owner_object.bw[given_time:],
                                                                        task_size * ap_load)
    if sta_side_tx_time is None:
        logging.debug("Skipping station_to_cloud")
        return
    sta_side_tx_time += 3  # Connection delay
    load_on_cloud_on_time_t = temp_traffics[given_time][CLOUD] + 1
    cloud_side_tx_time = task_size * load_on_cloud_on_time_t / 800
    tx_time = ceil(max(sta_side_tx_time, cloud_side_tx_time)) + 5
    if tx_time + given_time > record.sim_end_time:
        return

    temp_traffics[given_time:tx_time + given_time][:, owner_object.index] += 1
    temp_traffics[given_time:tx_time + given_time][:, CLOUD] += 1
    temp_earliest_next_task_start_tx_time[CLOUD] = tx_time + given_time
    logging.debug(f"Estimated tx time: {tx_time} to cloud")
    return tx_time


def get_estimated_tx_time_station_to_station(task_size, task_start_time, owner_object, processor_object, task_pair_bw,
                                             temp_earliest_next_task_start_tx_time, temp_traffics):
    tx_start_time = ceil(max(temp_earliest_next_task_start_tx_time[processor_object.sumo_id], task_start_time))
    if processor_object.no_new_task_start_time <= tx_start_time:
        return
    if owner_object.departure_time <= tx_start_time:
        return
    generator_associated_ap = owner_object.get_moment(tx_start_time).associated_ap
    processor_associated_ap = processor_object.get_moment(tx_start_time).associated_ap
    if not generator_associated_ap or not processor_associated_ap or \
            generator_associated_ap not in ap_records or processor_associated_ap not in ap_records:
        return
    generator_ap_moment = ap_records[generator_associated_ap].get_moment(tx_start_time)
    processor_ap_moment = ap_records[processor_associated_ap].get_moment(tx_start_time)

    if generator_ap_moment.associated_stations is None or processor_ap_moment.associated_stations is None:
        return

    generator_ap_load = 1
    processor_ap_load = 1
    for station in generator_ap_moment.associated_stations:
        generator_ap_load += temp_traffics[tx_start_time][traffic_indices[station]]

    for station in processor_ap_moment.associated_stations:
        processor_ap_load += temp_traffics[tx_start_time][traffic_indices[station]]

    ap_load = max(generator_ap_load, processor_ap_load)
    tx_time = get_number_of_elements_sum_equal_to_given_number(task_pair_bw[task_start_time:], task_size * ap_load)
    if tx_time is None:
        logging.debug("Skipping station_to_station")
        return
    tx_time += 5  # connection delay
    tx_time += tx_start_time - task_start_time
    temp_traffics[task_start_time:tx_time + task_start_time][:, owner_object.index] += 1
    temp_traffics[task_start_time:tx_time + task_start_time][:, processor_object.index] += 1

    logging.debug(f"Estimated tx time: {tx_time} to station")
    return ceil(tx_time)


def evaluate_combination(best_total_prioritized_penalty, tasks_to_be_decided, combination):
    total_prioritized_penalty = 0
    temp_earliest_next_task_start_tx_time = earliest_next_task_start_tx_time.copy()
    temp_traffics = traffics.copy()
    penalties_by_task = []
    estimated_tx_times = []
    for decision_index, task in enumerate(tasks_to_be_decided):
        owner_object = task.owner_object
        decision = combination[decision_index]
        if decision == Action.CLOUD:
            estimated_tx_time = get_estimated_tx_time_station_to_cloud(task.size, task.start_time, owner_object,
                                                                       temp_earliest_next_task_start_tx_time,
                                                                       temp_traffics)
            if not estimated_tx_time or estimated_tx_time > s.ALLOWED_MAX_TX_TIME:
                return decision_index
            process_time = ceil(task.size / s.CLOUD_PROCESSOR_SPEED)
            prioritized_penalty = task.priority * (task.start_time + estimated_tx_time + process_time - task.deadline)
        elif decision == Action.SKIP:
            prioritized_penalty = task.priority * (
                    owner_object.departure_time - task.deadline + s.TASK_FAILURE_PENALTY_OFFSET)
            estimated_tx_time = 0
        else:
            estimated_tx_time = get_estimated_tx_time_station_to_station(task.size, task.start_time, owner_object,
                                                                         decision, task.pair_bw[decision.sumo_id],
                                                                         temp_earliest_next_task_start_tx_time,
                                                                         temp_traffics)
            if not estimated_tx_time or estimated_tx_time > s.ALLOWED_MAX_TX_TIME:
                return decision_index
            process_time = ceil(task.size / decision.process_speed)
            temp_earliest_next_task_start_tx_time[decision.sumo_id] += \
                estimated_tx_time + process_time * (task.size / decision.queue_size)
            prioritized_penalty = task.priority * (task.start_time + estimated_tx_time + process_time - task.deadline)
        if prioritized_penalty < 0:
            prioritized_penalty = max(-10, prioritized_penalty)
        estimated_tx_times.append(estimated_tx_time)
        total_prioritized_penalty += prioritized_penalty
        if best_total_prioritized_penalty < total_prioritized_penalty:
            logging.debug(
                f"best_total_prioritized_penalty({best_total_prioritized_penalty}) < "
                f"current total_prioritized_penalty({total_prioritized_penalty})")
            return decision_index
        penalties_by_task.append(prioritized_penalty)
    return total_prioritized_penalty, penalties_by_task, temp_earliest_next_task_start_tx_time, temp_traffics, \
           estimated_tx_times


def optimize_time_window(decisions, start, end):
    num_of_combinations_tried = 0
    num_of_combinations_skipped = 0
    tasks_to_be_decided = [record.tasks[task_no] for task_no in decisions.keys()]
    if not tasks_to_be_decided:
        return [], 0, [], \
               earliest_next_task_start_tx_time, traffics
    option_costs = []
    best_total_prioritized_penalty = 99999
    best_combination = []
    best_scores_by_decision = []
    temp_earliest_next_task_start_tx_time = earliest_next_task_start_tx_time  # To suppress ide warning
    temp_traffics = traffics  # To suppress ide warning
    failed_part = []
    tasks_table = [[task] for task in tasks_to_be_decided]
    logging.info(f"\n{tabulate(tasks_table, ['Tasks to be decided'])}")
    for combination in itertools.product(*decisions.values()):
        if failed_part and combination[:len(failed_part)] == failed_part:
            logging.debug(f"Skipping this combination: {combination}")
            num_of_combinations_skipped += 1
        combination_result = evaluate_combination(best_total_prioritized_penalty, tasks_to_be_decided, combination)
        if isinstance(combination_result, int):
            failed_part = combination[:combination_result + 1]
            continue
        num_of_combinations_tried += 1
        decision_set_cost, temp_scores, temp_earliest_next_task_start_tx_time, temp_traffics, estimated_tx_times = \
            combination_result
        option_costs.append(decision_set_cost)
        if decision_set_cost < best_total_prioritized_penalty:
            best_total_prioritized_penalty = decision_set_cost
            best_combination = combination
            best_scores_by_decision = temp_scores
            logging.info(f"Better combination found: {best_combination}: {best_scores_by_decision}")
            logging.info(f"Estimated tx times: {estimated_tx_times}")
    logging.info(option_costs)
    logging.info(
        f"Best decision for ({start},{end}) has {best_total_prioritized_penalty:.0f} penalty "
        f"(combinationsTried:{num_of_combinations_tried},"
        f"num_of_combinations_skipped:{num_of_combinations_skipped})")
    tasks_table = [[task, best_combination[task_index], best_scores_by_decision[task_index]] for task_index, task in
                   enumerate(tasks_to_be_decided)]
    logging.info(f"\n{tabulate(tasks_table, ['Task', 'Decision'], tablefmt='pretty', stralign='left')}")
    return best_combination, best_total_prioritized_penalty, best_scores_by_decision, \
           temp_earliest_next_task_start_tx_time, temp_traffics


def save_to_solution_file(solution_to_save, filename):
    write_as_pickle(solution_to_save, filename)


def estimate_window_load(sim_record, start, end):
    decisions_in_the_given_time_window = {}

    for task_no, current_task in sim_record.tasks.items():
        if start <= current_task.start_time < end:
            decisions_in_the_given_time_window[task_no] = [Action.CLOUD, Action.SKIP]
            # decisions_in_the_given_time_window[task_no] = []
            for processor in task_based_available_processors[task_no]:
                if current_task.start_time < processor.no_new_task_start_time and processor.entry_time < end:
                    decisions_in_the_given_time_window[task_no].append(processor)
    decision_counter, possibilities_in_window = count_possible_pairs(decisions_in_the_given_time_window)
    return decisions_in_the_given_time_window, decision_counter, possibilities_in_window


def get_decisions_for_given_time(given_time, decisions, corresponding_combinations_selected):
    decisions_on_given_time = {}
    for decision_index, task_no in enumerate(decisions.keys()):
        start_time = record.tasks[task_no].start_time
        if start_time == given_time:
            decisions_on_given_time[task_no] = [corresponding_combinations_selected[decision_index]]
    return decisions_on_given_time


def parse_cli_arguments():
    global record_file
    parser = argparse.ArgumentParser("Create solution for record")
    parser.add_argument('--record-file', type=str, help="Record file to use to import tasks and vehicle assignments")
    parser.add_argument("-l", "--log-level", dest="log_level",
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help="Set the logging level", default="INFO")
    arguments = parser.parse_args()
    logging.basicConfig(level=getattr(logging, arguments.log_level), format="%(asctime)s %(levelname)s -> %(message)s")
    if arguments.record_file:
        record_file = arguments.record_file


if __name__ == '__main__':
    parse_cli_arguments()
    solution_filename = record_file.replace("record", "solution") + "_solution"
    record = get_simulation_record(record_file)
    solution = []
    scores = []
    total_score = 0
    number_of_tasks = len(record.tasks)
    next_task_index = 0
    while next_task_index < number_of_tasks:
        window_start_time = record.tasks[next_task_index].start_time
        window_end_time = window_start_time + TIME_WINDOW
        logging.info(f"Window: {window_start_time}-{window_end_time} (size:{window_end_time - window_start_time})")
        decisions_in_given_time_window, num_of_decisions, possibilities = \
            estimate_window_load(record, window_start_time, window_end_time)
        logging.info(f"Number of possible pairings: {num_of_decisions}, possibilities: {possibilities}")

        is_shrunk_window = False
        while possibilities > MAX_COMBINATION_TO_TRY_PER_WINDOW:
            is_shrunk_window = True
            window_end_time -= 1
            decisions_in_given_time_window, num_of_decisions, possibilities = \
                estimate_window_load(record, window_start_time, window_end_time)
        if is_shrunk_window:
            logging.info(f"Readjusting window: {window_start_time}-{window_end_time} "
                         f"(size:{window_end_time - window_start_time})")
            logging.info(f"Number of possible pairings: {num_of_decisions}, possibilities: {possibilities}")

        window_result = optimize_time_window(decisions_in_given_time_window, window_start_time, window_end_time)
        combinations_selected = window_result[0]
        tasks_on_current_time = get_decisions_for_given_time(window_start_time, decisions_in_given_time_window,
                                                             combinations_selected)
        selected_combination, window_score, scores_by_decision, earliest_next_task_start_tx_time, traffics = \
            optimize_time_window(tasks_on_current_time, window_start_time, window_end_time)

        for decision_score in scores_by_decision:
            if decision_score > 0:
                total_score += decision_score
        solution.extend(selected_combination)
        scores.extend(scores_by_decision)
        next_task_index = len(solution)
    logging.info(f"Solution score for {len(solution)} tasks: {total_score}")
    # solution_text = ""
    headers = ["Task", "Action", "Score"]
    rows = []
    for current_task_no, current_task in record.tasks.items():
        rows.append([current_task, solution[current_task_no], f"{scores[current_task_no]:.0f}"])
    logging.info(f'Decisions: \n{tabulate(rows, headers, tablefmt="pretty", stralign="left")}')
    solution_data = Solution(solution, total_score, scores)
    save_to_solution_file(solution_data, solution_filename)