import bisect
import logging
import random
import subprocess
import sys
from enum import Enum
from operator import attrgetter

import settings as s
from actors.EventManager import EventManager, EventType
from actors.Simulation import Simulation
from actors.Solution import Action
from actors.Task import Task, Status
from actors.TrafficObserver import TrafficObserver
from actors.Vehicle import TaskGeneratorVehicle, ProcessorVehicle, ConnectionStatus
from actors.constant import Color
from dispatch_tasks import send_task_data_to_cloud, send_task_data_to_processor
from sumo_traci import SumoVehicle
from utils import get_estimated_tx_time_between_stations, get_estimated_tx_time_station_to_cloud


class AssignmentMethod(Enum):
    AGGRESSIVE = "AGGRESSIVE"
    ADAPTIVE = "ADAPTIVE"
    OPTIMUM = "OPTIMUM"


class TaskProcessorMatching:
    task = None
    processor = None
    task_penalty_score = None
    estimated_tx_time = None

    def __init__(self, task, processor, task_penalty_score, estimated_tx_time):
        self.task = task
        self.processor = processor
        self.task_penalty_score = task_penalty_score
        self.estimated_tx_time = estimated_tx_time

    def __repr__(self) -> str:
        return f"Task#{self.task.no}: owner:{self.task.owner} candidateProcessor:{self.processor} " \
               f"penalty:{self.task_penalty_score} estimatedTx:{self.estimated_tx_time:.0f}"


class TaskOrganizer:
    pool = None
    tasks_being_processed_on_cloud = None
    active_tasks = None
    completed_tasks = None
    cloud_thresholds = None
    available_task_processors = {}
    download_processes = None
    traffic_count_on_ap = None
    solution = None

    def __init__(self, solution=None):
        self.available_task_processors = {}
        self.tasks_being_processed_on_cloud = []
        TaskOrganizer.cloud_thresholds = list(s.CLOUD_PROBABILITY_BY_POOL_SIZE.keys())
        TaskOrganizer.cloud_thresholds.sort()

        self.pool = []
        self.active_tasks = {}
        self.completed_tasks = []
        self.download_processes = {}
        self.traffic_count_on_ap = {}
        self.solution = solution

    def check_events(self, current_time):
        events = EventManager.get_events_on_time_t(current_time)
        for event in events:
            logging.info(f"{Color.CYAN}NEW EVENT: {event}{Color.ENDC}")
            if event.event_type == EventType.PROCESS_COMPLETE:
                self.completed_tasks.append(event.task)
                self.active_tasks.pop(event.task.no)
                event.task.status = Status.COMPLETED
                if event.task.is_assigned_to_cloud:
                    logging.info(f"Task#{event.task.no} process on cloud is complete.")
                else:
                    processor = event.task.assigned_processor
                    logging.info(f"Task#{event.task.no} process on processor {processor.sumo_id} is complete.")
                    processor.start_to_process_next_task(current_time)

    def check_download_processes(self, current_time):
        for task_no, process in self.download_processes.copy().items():
            state = process.poll()
            if state is not None:
                task = self.active_tasks[task_no]
                self.download_processes.pop(task_no)
                if task.status in [Status.OWNER_LEFT, Status.PROCESSOR_LEFT]:
                    logging.info(f"{Color.ORANGE}Task#{task_no} was {task.status.name}. Skipping...{Color.ENDC}")
                    continue
                destination = "Cloud" if task.is_assigned_to_cloud else task.assigned_processor.station.name
                logging.info(f"{Color.ORANGE}Task#{task_no} data transferr output: "
                             f"{task.owner.station.name}->{destination}{Color.ENDC}")
                out, err = process.communicate()
                if err:
                    logging.info(
                        f"Err for Task#{task.no}: {err.decode()}")
                    if task.is_assigned_to_cloud:
                        Simulation.cloud_server.popen("ping -c 3 %s" % task.owner.station.wintfs[0].ip)
                    else:
                        task.assigned_processor.station.popen("ping -c 3 %s" % task.owner.station.wintfs[0].ip)
                    defaults = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE}
                    self.download_processes[task_no] = subprocess.Popen(process.args, **defaults)
                    continue
                task_identifier = task.get_task_identifier()
                logging.info(f"Upload data report({task_identifier}):\n{out.decode()}")
                Simulation.upload_reports[task_identifier] = out
                task.server_process.kill()
                task.server_process.wait()
                for ping_process in task.ping_processes:
                    ping_process.kill()
                    ping_process.wait()
                task.set_tx_complete(current_time)

    def get_next_task_pair(self, current_time, processors):
        task_scores = []
        for task in self.pool:
            if task.owner.connection_status != ConnectionStatus.CONNECTED:
                logging.error(f"Task#{task.no} owner {task.owner.station.name} is {task.owner.connection_status.name}. "
                              f"Skipping...")
                continue
            if task.owner.station.wintfs[0].associatedTo is None:
                logging.error(
                    f"Task#{task.no} owner {task.owner.station.name} does not have associated AP. Skipping...")
                continue
            best_matching_for_task = None
            for processor in processors:
                if processor.connection_status != ConnectionStatus.CONNECTED:
                    logging.error(
                        f"Processor {processor.sumo_id}({processor.station.name}) is "
                        f"{task.owner.connection_status.name}. Skipping...")
                    continue
                if processor.station.wintfs[0].associatedTo is None:
                    logging.error(f"Processor {processor.sumo_id}({processor.station.name}) does not have "
                                  f"associated AP. Skipping...")
                    continue
                if task.size > processor.remaining_queue_size:
                    continue
                tx_time = get_estimated_tx_time_between_stations(current_time, task.owner.station, processor.station,
                                                                 task)
                if tx_time > s.ALLOWED_MAX_TX_TIME:
                    continue
                earliest_time_to_process_task = processor.estimated_earliest_time_to_process_new_task
                processing_time = task.get_process_time(processor.process_speed)
                estimated_task_end_time = max(current_time + tx_time, earliest_time_to_process_task) + processing_time
                task_penalty_score = task.get_predicted_penalty_score(estimated_task_end_time)
                if best_matching_for_task and best_matching_for_task.task_penalty_score < task_penalty_score:
                    continue
                best_matching_for_task = TaskProcessorMatching(task, processor, task_penalty_score, tx_time)
                task_scores.append(best_matching_for_task)
        if task_scores:
            logging.info(f"Candidate pairs: {task_scores}")
            pair = max(task_scores, key=attrgetter('task_penalty_score'))
            return pair
        else:
            return False

    def aggressive_assignment(self, current_time, processors):
        new_matching = self.get_next_task_pair(current_time, processors)
        if new_matching:
            self.assign_task_to_processor(current_time, new_matching)
            return self.aggressive_assignment(current_time, processors)

    def adaptive_assignment(self, current_time, processors):
        processors_with_no_active_download_operation = []
        for processor in processors:
            has_download_job = False
            for task in processor.queue:
                if task.status == Status.TX_PROCESSOR:
                    has_download_job = True
                    break
            if not has_download_job:
                processors_with_no_active_download_operation.append(processor)
                logging.debug(f"Processor{processor} queue: {processor.queue}")
        new_matching = self.get_next_task_pair(current_time, processors_with_no_active_download_operation)
        while new_matching:
            processors_with_no_active_download_operation.remove(new_matching.processor)
            self.assign_task_to_processor(current_time, new_matching)
            new_matching = self.get_next_task_pair(current_time, processors_with_no_active_download_operation)
        if new_matching:
            self.assign_task_to_processor(current_time, new_matching)
            return self.aggressive_assignment(current_time, processors)

    def assignment_from_solution(self, current_time):
        for task in self.pool.copy():
            action = self.solution.decisions[task.no]
            if action == Action.SKIP:
                continue
            if action.sumo_id in Simulation.all_vehicles:
                processor = Simulation.all_vehicles[action.sumo_id]
                if processor.departure_time:
                    self.pool.remove(task)
                    task.set_assignment_to_cloud(current_time)
                    self.assign_to_cloud(current_time, task)
                    continue
                if task.size > processor.remaining_queue_size:
                    logging.info(f"Processor queue size is not enough for task#{task.no}")
                    continue
                self.pool.remove(task)
                estimated_tx_time = get_estimated_tx_time_between_stations(current_time, task.owner.station,
                                                                           processor.station,
                                                                           task)
                task.set_estimated_tx_end_time(current_time, estimated_tx_time)
                task.status = Status.TX_PROCESSOR
                processor.assign_task(current_time, task)
                download_process = send_task_data_to_processor(task, Simulation.nat_host_ip)
                self.download_processes[task.no] = download_process
                TrafficObserver.increment_traffic_on_sta(task.owner.station.name)
                TrafficObserver.increment_traffic_on_sta(processor.station.name)

    def handle_tasks(self, current_time):
        self.check_events(current_time)
        self.check_download_processes(current_time)
        processors_not_leaving_soon = [processor for processor in self.available_task_processors.values() if
                                       not processor.is_leaving_soon and
                                       processor.connection_status == ConnectionStatus.CONNECTED]
        if AssignmentMethod(s.ASSIGNMENT_METHOD) == AssignmentMethod.AGGRESSIVE:
            self.aggressive_assignment(current_time, processors_not_leaving_soon)
        elif AssignmentMethod(s.ASSIGNMENT_METHOD) == AssignmentMethod.ADAPTIVE:
            self.adaptive_assignment(current_time, processors_not_leaving_soon)
        elif AssignmentMethod(s.ASSIGNMENT_METHOD) == AssignmentMethod.OPTIMUM:
            self.assignment_from_solution(current_time)
        else:
            logging.error("Wrong task assignment setting is set")
            sys.exit(1)

    def add_task(self, current_time, task):
        self.active_tasks[task.no] = task
        pool_size = len(self.pool)
        logging.info(f"{Color.DARK_WHITE}Current pool size: {pool_size}{Color.ENDC} ")
        threshold_index = bisect.bisect_right(TaskOrganizer.cloud_thresholds, pool_size) - 1
        cloud_probability = s.CLOUD_PROBABILITY_BY_POOL_SIZE[TaskOrganizer.cloud_thresholds[threshold_index]]
        lottery = random.random()
        is_assigned_to_cloud = lottery < cloud_probability

        if AssignmentMethod(s.ASSIGNMENT_METHOD) == AssignmentMethod.OPTIMUM:
            if self.solution.decisions[task.no] == Action.CLOUD:
                is_assigned_to_cloud = True
            else:
                is_assigned_to_cloud = False
        if is_assigned_to_cloud:
            task.set_assignment_to_cloud(current_time)
            self.assign_to_cloud(current_time, task)
        else:
            self.pool.append(task)
            task.assign_to_pool(current_time)
        logging.info(f"{task}")
        return task

    def assign_task_to_processor(self, current_time, new_matching):
        self.pool.remove(new_matching.task)
        estimated_tx_time = new_matching.estimated_tx_time
        new_matching.task.set_estimated_tx_end_time(current_time, estimated_tx_time)
        new_matching.task.status = Status.TX_PROCESSOR
        new_matching.processor.assign_task(current_time, new_matching.task)
        download_process = send_task_data_to_processor(new_matching.task, Simulation.nat_host_ip)
        self.download_processes[new_matching.task.no] = download_process
        TrafficObserver.increment_traffic_on_sta(new_matching.task.owner.station.name)
        TrafficObserver.increment_traffic_on_sta(new_matching.processor.station.name)

    def assign_to_cloud(self, current_time, new_task):
        estimated_tx_time = get_estimated_tx_time_station_to_cloud(current_time, new_task)
        new_task.set_estimated_tx_end_time(current_time, estimated_tx_time)
        download_process = send_task_data_to_cloud(Simulation.cloud_server, Simulation.cloud_server_ip, new_task,
                                                   Simulation.nat_host_ip)
        self.download_processes[new_task.no] = download_process
        TrafficObserver.increment_traffic_on_sta(new_task.owner.station.name)
        TrafficObserver.increment_traffic_on_cloud()

    def add_to_available_task_processors(self, vehicle):
        self.available_task_processors[vehicle.sumo_id] = vehicle
        logging.debug(f"New processor vehicle is added: {vehicle.sumo_id}")

    def remove_from_available_task_processors(self, vehicle_id):
        if vehicle_id in self.available_task_processors:
            self.available_task_processors.pop(vehicle_id)
            logging.debug(f"Processor vehicle is removed: {vehicle_id}")
        else:
            logging.info(f"Processor vehicle is already removed: {vehicle_id}")

    def handle_vehicle_departure(self, vehicle):
        is_processor = isinstance(vehicle, ProcessorVehicle)
        if is_processor and vehicle.iperf_server_processes:
            for iperf_server_process in vehicle.iperf_server_processes:
                iperf_server_process.kill()
                iperf_server_process.wait()
        for task in vehicle.task_list:
            if task.status not in [Status.TX_CLOUD, Status.TX_PROCESSOR, Status.ON_POOL]:
                continue
            if is_processor:
                task.status = Status.PROCESSOR_LEFT
                logging.error(
                    f"{Color.RED}Task#{task.no} processor {vehicle.station.name} is left the area."
                    f"Reassigning the task.{Color.ENDC}")
                Simulation.number_of_reassigned_tasks += 1
                self.add_task(Simulation.current_time, task)
                task.assigned_processor.drop_task(Simulation.current_time, task)
                TrafficObserver.decrement_traffic_on_sta(task.owner.station.name)
            else:
                task.status = Status.OWNER_LEFT
                task.owner_departure_time = Simulation.current_time
                logging.error(
                    f"{Color.RED}Task#{task.no} owner {vehicle.station.name} is left the area.{Color.ENDC}")
                if task in self.pool:
                    self.pool.remove(task)
                elif task.is_assigned_to_cloud:
                    TrafficObserver.decrement_traffic_on_cloud()
                else:
                    task.assigned_processor.drop_task(Simulation.current_time, task)
                    TrafficObserver.decrement_traffic_on_sta(task.assigned_processor.station.name)
            if task.tx_process:
                task.tx_process.kill()
                task.tx_process.wait()
                task.server_process.kill()
                task.server_process.wait()
                for ping_process in task.ping_processes:
                    ping_process.kill()
                    ping_process.wait()
            if task.no in self.download_processes:
                self.download_processes.pop(task.no)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    task_organizer = TaskOrganizer()
    for i in range(900):
        sumo_vehicle = SumoVehicle("veh%d" % i, type_abbreviation=random.choice(["E", "T"]), route_length=350)
        task_generator_vehicle = TaskGeneratorVehicle(sumo_vehicle, None, i)
        size = random.randint(*s.TASK_SIZE)
        deadline = random.randint(*s.DEADLINE)
        dummy_task = Task(i, task_generator_vehicle, size, deadline)
        task_organizer.add_task(i, dummy_task)
