import queue
from enum import Enum

import settings as s


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

    def __init__(self, sumo_vehicle, station, arrival_time):
        self.sumo_id = sumo_vehicle.sumo_id
        self.sumo_vehicle = sumo_vehicle
        self.station = station
        self.connection_status = ConnectionStatus.CONNECTING
        self.type_abbreviation = sumo_vehicle.type_abbreviation
        self.properties = s.VEHICLE_TYPE_PROPERTIES[self.type_abbreviation]
        self.arrival_time = arrival_time
        self.task_list = []

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
    processor_type = None
    process_speed = None
    queue_size = None
    remaining_queue_size = None
    currently_processed_task = None
    queue = None

    def __init__(self, sumo_vehicle, station, arrival_time):
        super().__init__(sumo_vehicle, station, arrival_time)
        self.process_speed = self.properties["process_speed"]
        self.queue_size = self.properties["queue_size"]
        self.remaining_queue_size = self.queue_size
        self.currently_processed_task = None
        self.queue = queue.Queue()


class TaskGeneratorVehicle(Vehicle):
    processor_type = None
    priority = None
    is_generating = False

    def __init__(self, sumo_vehicle, station, arrival_time):
        super().__init__(sumo_vehicle, station, arrival_time)
        self.priority = self.properties["priority"]
        self.is_generating = False


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
