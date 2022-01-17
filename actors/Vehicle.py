import logging
from enum import Enum

import settings as s
from actors.EventManager import Event, EventType, EventManager
from actors.Simulation import Simulation
from actors.Task import Status
from actors.constant import Color


class ConnectionStatus(Enum):
    CONNECTING = 0
    CONNECTED = 1
    DISCONNECTED = 1
    LEFT = 3


class Vehicle(object):
    sumo_id = None
    station = None
    connection_status = None
    sumo_vehicle = None
    current_route_no = None
    arrival_time = None
    departure_time = None
    task_list = None
    associated_ap = None
    is_leaving_soon = None

    def __init__(self, sumo_vehicle, station, arrival_time):
        self.sumo_id = sumo_vehicle.sumo_id
        self.sumo_vehicle = sumo_vehicle
        sumo_vehicle.role_object = self
        self.station = station
        self.connection_status = ConnectionStatus.CONNECTING
        self.type_abbreviation = sumo_vehicle.type_abbreviation
        self.properties = s.VEHICLE_TYPE_PROPERTIES[self.type_abbreviation]
        self.arrival_time = arrival_time
        self.task_list = []
        self.is_leaving_soon = False

    def add_task(self, task):
        self.task_list.append(task)

    def set_as_connecting(self):
        self.connection_status = ConnectionStatus.CONNECTING

    def set_as_disconnected(self):
        self.connection_status = ConnectionStatus.DISCONNECTED

    def leave(self, leave_time):
        self.connection_status = ConnectionStatus.LEFT
        self.departure_time = leave_time


class ProcessorVehicle(Vehicle):
    process_speed = None
    queue_size = None
    remaining_queue_size = None
    currently_processed_task = None
    currently_processed_task_end_time = None
    queue = None
    being_downloaded_tasks = None
    estimated_earliest_time_to_process_new_task = None
    iperf_server_process = None

    def __init__(self, sumo_vehicle, station, arrival_time):
        super().__init__(sumo_vehicle, station, arrival_time)
        self.process_speed = self.properties["process_speed"]
        self.queue_size = self.properties["queue_size"]
        self.remaining_queue_size = self.queue_size
        self.currently_processed_task = None
        self.queue = []
        self.being_downloaded_tasks = []
        self.estimated_earliest_time_to_process_new_task = arrival_time
        self.iperf_server_process = None

    def assign_task(self, current_time, task):
        task.start_tx(current_time)
        self.add_task(task)
        self.queue.append(task)
        task.set_processor(self)
        self.being_downloaded_tasks.append(task)
        self.remaining_queue_size -= task.size
        self.estimate_all_tasks_processed_time(current_time)
        logging.info(f"{Color.GREEN}Task #{task.no}: {task.owner.station.name}->"
                     f"{self.station.name}(Remaining:{self.remaining_queue_size}KB){Color.ENDC}")

    def start_task(self, current_time):
        if not self.currently_processed_task and self.queue[0].status == Status.WAITING_ON_QUEUE:
            task = self.queue.pop(0)
            self.currently_processed_task = task
            self.remaining_queue_size += task.size
            process_time = task.get_process_time(self.process_speed)
            task.start_processing(current_time, process_time)
            self.currently_processed_task_end_time = current_time + process_time


    def start_to_process_next_task(self, current_time):
        self.currently_processed_task = None
        self.estimate_all_tasks_processed_time(current_time)
        if len(self.queue) > 0:
            self.start_task(current_time)

    def estimate_all_tasks_processed_time(self, current_time):
        total_wait_time = 0
        if self.currently_processed_task:
            next_task_start_time = self.currently_processed_task.end_time
        else:
            next_task_start_time = current_time
        if self.queue and self.queue[0].status == Status.TX_PROCESSOR:
            next_task_start_time = max(next_task_start_time, self.queue[0].estimated_tx_end_time)
        for queue_task in self.queue:
            total_wait_time += queue_task.get_process_time(self.process_speed)
        next_task_start_time += total_wait_time
        self.estimated_earliest_time_to_process_new_task = next_task_start_time
        logging.info(f"{self.sumo_id}({self.station.name}): the earliest time to process a new task is estimated as "
                     f"{next_task_start_time}")
        return next_task_start_time


class TaskGeneratorVehicle(Vehicle):
    priority = None
    is_generating = False

    def __init__(self, sumo_vehicle, station, arrival_time):
        super().__init__(sumo_vehicle, station, arrival_time)
        self.priority = self.properties["priority"]
        self.is_generating = False

    def get_number_of_pool_and_tx_tasks(self):
        total = 0
        for task in self.task_list:
            if task.status in [Status.TX_CLOUD, Status.TX_PROCESSOR, Status.ON_POOL]:
                total += 1
        return total


class VehicleMoment:
    sumo_id = None
    step = None
    x = None
    y = None
    associated_ap = None

    def __init__(self, sumo_id, step, x, y):
        self.sumo_id = sumo_id
        self.step = step
        self.x = x
        self.y = y
        self.associated_ap = None

    def set_associated_ap(self, ap_name):
        self.associated_ap = ap_name

    def __str__(self) -> str:
        return f"{self.sumo_id}|step:{self.step}|x:{self.x}|y:{self.y}"
