import logging
from enum import Enum

import settings as s
from actors.EventManager import EventManager, Event, EventType
from actors.TrafficObserver import TrafficObserver
from actors.constant import Color


class Status(Enum):
    GENERATED = 0
    ON_POOL = 1
    TX_CLOUD = 2
    TX_PROCESSOR = 3
    WAITING_ON_QUEUE = 4
    PROCESSING = 5
    COMPLETED = 6
    TASK_OWNER_LEFT = 7
    ASSIGNED_PROCESSOR_LEFT = 8


class Task(object):
    no = 0
    start_time = None
    end_time = None
    priority = None
    deadline = None
    delay = None
    size = None
    owner = None
    assigned_processor = None
    general_queue_arrival_time = None
    tx_start_time = None
    tx_end_time = None
    processor_queue_arrival_time = None
    process_start_time = None
    process_end_time = None

    is_assigned_to_cloud = False
    is_waited_in_general_queue = True
    is_waited_in_processor_queue = True
    tx_process = True

    def __init__(self, start_time, owner, size, deadline):
        self.no = Task.no
        self.status = Status.GENERATED
        Task.no += 1
        self.start_time = start_time
        self.general_queue_arrival_time = start_time
        self.owner = owner
        self.priority = owner.priority
        self.size = size
        self.deadline = deadline
        self.estimated_tx_end_time = None
        self.tx_process = None

    def __str__(self) -> str:
        return f"Task #{self.no} from {self.owner.station.name}: {self.status.name}\t" \
               f"{self.start_time}-{self.end_time or 'Current'} {'(Cloud)' if self.is_assigned_to_cloud else ''}"

    def get_task_origin_data(self) -> str:
        return f"Task #{self.no} started at time {self.start_time} is from {self.owner.station.name} connected to" \
               f" {self.owner.station.wintfs[0].associatedTo}"

    def calculate_delay(self):
        self.delay = self.end_time - self.deadline
        logging.info(f"Delay on task #{self.no} is {self.delay}")
        return self.delay

    def get_prioritized_delay(self):
        return self.priority * self.delay

    def get_predicted_prioritized_delay(self, possible_end_time):
        delay = possible_end_time - self.deadline
        return self.priority * max(delay, 0)

    def get_predicted_delay_score(self, possible_end_time):
        delay = possible_end_time - self.deadline
        if delay < 0:
            score = delay / self.priority
        else:
            score = delay * self.priority
        return score

    def get_task_time(self):
        return self.end_time - self.start_time

    def set_assignment_to_cloud(self, current_time):
        self.is_assigned_to_cloud = True
        self.status = Status.TX_CLOUD
        self.tx_start_time = current_time
        self.general_queue_arrival_time = current_time

    def assign_to_pool(self, current_time):
        self.is_assigned_to_cloud = False
        self.status = Status.ON_POOL
        self.general_queue_arrival_time = current_time

    def is_in_tx_mode(self):
        return self.status in [Status.TX_CLOUD, Status.TX_PROCESSOR]

    def start_tx(self, current_time):
        self.tx_start_time = current_time

    def start_processing(self, current_time, process_duration):
        self.status = Status.PROCESSING
        self.process_start_time = current_time
        self.process_end_time = current_time + process_duration
        self.end_time = self.process_end_time
        self.calculate_delay()

    def get_process_time(self, processor_speed):
        return self.size / processor_speed

    def set_processor(self, processor):
        self.assigned_processor = processor

    def set_tx_complete(self, current_time):
        self.tx_end_time = current_time
        transfer_time = current_time - self.tx_start_time
        estimated_tx = self.estimated_tx_end_time - self.tx_start_time
        logging.info(f"Task #{self.no}'s {self.size}KB data is transfer in "
                     f"{Color.RED}{transfer_time:.1f}{Color.ENDC} s, "
                     f"estimated was {Color.GREEN}{estimated_tx}{Color.ENDC} s")
        TrafficObserver.decrement_traffic_on_sta(self.owner.station.name)
        if self.is_assigned_to_cloud:
            self.status = Status.TX_CLOUD
            self.process_start_time = current_time
            process_duration = self.get_process_time(s.CLOUD_PROCESSOR_SPEED)
            self.end_time = current_time + process_duration
            new_event = Event(EventType.PROCESS_COMPLETE, self, self.end_time)
            EventManager.add_event(current_time, new_event)
            TrafficObserver.decrement_traffic_on_cloud()
        else:
            self.status = Status.WAITING_ON_QUEUE
            self.assigned_processor.start_task(current_time)
            TrafficObserver.decrement_traffic_on_sta(self.assigned_processor.station.name)

    def set_estimated_tx_end_time(self, current_time, estimated_tx_time):
        self.estimated_tx_end_time = current_time + estimated_tx_time
