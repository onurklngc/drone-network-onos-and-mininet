import itertools
import logging
from enum import Enum
from math import ceil

import numpy as np

import settings as s
from actors.Vehicle import ConnectionStatus
from utils import read_pickle_file, get_link_speed_by_rssi, get_estimated_tx_time_station_to_cloud

RECORD_FILE = "records/record_20220121-031650.pickle"

processor_records = {}
generator_records = {}
ap_records = {}
processors = {}
generators = {}
task_based_available_processors = {}
TIME_WINDOW = 20
record = None
earliest_next_task_start_tx_time = {}
traffics = {}
CLOUD = 0
traffic_indices = {}
vehicle_by_traffic_index = {}


class Action(Enum):
    CLOUD = 0
    SKIP = 1

    def __repr__(self):
        return self.name


def count_possible_pairs(task_processor_pairing):
    counter = 0
    possibilities = 1
    for possible_processors in task_processor_pairing.values():
        possibilities *= len(possible_processors) + 1
        counter += len(possible_processors)
    logging.info(f"Number of possible pairings: {counter}, possibilities: {possibilities}")
    return counter, possibilities


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


def get_simulation_record(filename=RECORD_FILE):
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
        if not vehicle.no_new_task_start_time:
            vehicle.no_new_task_start_time = sim_record.sim_end_time
        for moment_time, moment in vehicle.moments.items():
            if moment.rssi and moment.connection_status == ConnectionStatus.CONNECTED:
                moment.bw = get_link_speed_by_rssi(moment.rssi)
                vehicle.bw[moment_time] = moment.bw
                sim_record.aps[moment.associated_ap].add_station(moment_time, sumo_id)
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
        task_start_time = task.start_time
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
            if owner_departure_time - min_tx_time > processor.entry_time:
                if task_start_time >= processor.no_new_task_start_time:
                    continue
                task_based_available_processors[task_no].append(processor)
    count_possible_pairs(task_based_available_processors)
    return sim_record


def get_estimated_tx_time_station_to_cloud(task_size, given_time, owner_object, temp_traffics):
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

    load_on_cloud_on_time_t = temp_traffics[given_time][CLOUD] + 1
    cloud_side_tx_time = task_size * load_on_cloud_on_time_t / 4360
    tx_time = ceil(max(sta_side_tx_time, cloud_side_tx_time)) + 3
    if tx_time + given_time > record.sim_end_time:
        return

    temp_traffics[given_time:tx_time + given_time][:, owner_object.index] += 1
    temp_traffics[given_time:tx_time + given_time][:, CLOUD] += 1

    logging.debug(f"Estimated tx time: {tx_time} to cloud")
    return tx_time


def get_estimated_tx_time_station_to_station(task_size, task_start_time, owner_object, processor_object, task_pair_bw,
                                             temp_earliest_next_task_start_tx_time, temp_traffics):
    tx_start_time = max(temp_earliest_next_task_start_tx_time[processor_object.sumo_id], task_start_time)
    if processor_object.no_new_task_start_time <= tx_start_time:
        return
    if owner_object.departure_time <= tx_start_time:
        return
    generator_associated_ap = owner_object.get_moment(tx_start_time).associated_ap
    processor_associated_ap = processor_object.get_moment(tx_start_time).associated_ap
    if not generator_associated_ap or not processor_associated_ap:
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
    tx_time = get_number_of_elements_sum_equal_to_given_number(task_pair_bw[tx_start_time:], task_size * ap_load)
    if tx_time is None:
        logging.debug("Skipping station_to_station")
        return

    temp_traffics[tx_start_time:tx_time + tx_start_time][:, owner_object.index] += 1
    temp_traffics[tx_start_time:tx_time + tx_start_time][:, processor_object.index] += 1

    logging.debug(f"Estimated tx time: {tx_time} to cloud")
    return ceil(tx_time)


def evaluate_combination(best_total_prioritized_penalty, tasks_to_be_decided, combination):
    total_prioritized_penalty = 0
    temp_earliest_next_task_start_tx_time = earliest_next_task_start_tx_time.copy()
    temp_traffics = traffics.copy()
    for decision_index, task in enumerate(tasks_to_be_decided):
        owner_object = task.owner_object
        decision = combination[decision_index]
        if decision == Action.CLOUD:
            estimated_tx_time = get_estimated_tx_time_station_to_cloud(task.size, task.start_time, owner_object,
                                                                       temp_traffics)
            if not estimated_tx_time or estimated_tx_time > s.ALLOWED_MAX_TX_TIME:
                return decision_index
            process_time = ceil(task.size / s.CLOUD_PROCESSOR_SPEED)
            prioritized_penalty = task.priority * (task.start_time + estimated_tx_time + process_time - task.deadline)
        elif decision == Action.SKIP:
            prioritized_penalty = task.priority * (
                    owner_object.departure_time - task.deadline + s.TASK_FAILURE_PENALTY_OFFSET)
        else:
            estimated_tx_time = get_estimated_tx_time_station_to_station(task.size, task.start_time, owner_object,
                                                                         decision, task.pair_bw[decision.sumo_id],
                                                                         temp_earliest_next_task_start_tx_time,
                                                                         temp_traffics)
            if not estimated_tx_time or estimated_tx_time > s.ALLOWED_MAX_TX_TIME:
                return decision_index
            process_time = ceil(task.size / decision.process_speed)
            temp_earliest_next_task_start_tx_time[decision.sumo_id] += max(estimated_tx_time, process_time)
            prioritized_penalty = task.priority * (task.start_time + estimated_tx_time + process_time - task.deadline)

        total_prioritized_penalty += prioritized_penalty
        if best_total_prioritized_penalty < total_prioritized_penalty:
            logging.debug(
                f"best_total_prioritized_penalty({best_total_prioritized_penalty}) < "
                f"current total_prioritized_penalty({total_prioritized_penalty})")
            return decision_index
    return total_prioritized_penalty, temp_earliest_next_task_start_tx_time, temp_traffics


def optimize_time_window(sim_record, start, end):
    num_of_combinations_tried = 0
    decisions_in_the_given_time_window = {}
    for task_no, task in sim_record.tasks.items():
        if start <= task.start_time < end:
            decisions_in_the_given_time_window[task_no] = [Action.CLOUD, Action.SKIP]
            for processor in task_based_available_processors[task_no]:
                if task.start_time < processor.no_new_task_start_time and processor.entry_time < end:
                    decisions_in_the_given_time_window[task_no].append(processor)
    decision_counter, possibilities = count_possible_pairs(decisions_in_the_given_time_window)

    for given_time in range(sim_record.sim_start_time, start):
        temp_decrease_traffic_events = traffics.copy()

    tasks_to_be_decided = [record.tasks[task_no] for task_no in decisions_in_the_given_time_window.keys()]
    option_costs = []
    best_total_prioritized_penalty = 99999
    best_combination = None
    temp_earliest_next_task_start_tx_time = earliest_next_task_start_tx_time
    temp_traffics = traffics
    failed_part = []
    logging.info(f"Tasks to be decided: {tasks_to_be_decided}")
    for combination in itertools.product(*decisions_in_the_given_time_window.values()):
        if failed_part and combination[:len(failed_part)] == failed_part:
            logging.debug(f"Skipping this combination: {combination}")
        combination_result = evaluate_combination(best_total_prioritized_penalty, tasks_to_be_decided, combination)
        if isinstance(combination_result, int):
            failed_part = combination[:combination_result]
            continue
        num_of_combinations_tried += 1
        option_cost, temp_earliest_next_task_start_tx_time, temp_traffics = combination_result
        option_costs.append(option_cost)
        if option_cost and option_cost < best_total_prioritized_penalty:
            best_total_prioritized_penalty = option_cost
            best_combination = combination
    logging.info(option_costs)
    logging.info(f"Best decision for ({start},{end}): {best_combination} with {best_total_prioritized_penalty} penalty "
                 f"(combinationsTried:{num_of_combinations_tried})")
    return best_combination, best_total_prioritized_penalty, temp_earliest_next_task_start_tx_time, temp_traffics


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    record = get_simulation_record()
    for i in range(record.sim_start_time, record.sim_end_time, TIME_WINDOW):
        selected_combination, score, earliest_next_task_start_tx_time, traffics = optimize_time_window(record, i,
                                                                                                       i + TIME_WINDOW)
    logging.info(record)
