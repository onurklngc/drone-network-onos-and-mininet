import logging
from enum import Enum

import settings as s
from actors.EventManager import EventManager, Event, EventType
from actors.Simulation import Simulation
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
    OWNER_LEFT = 7
    PROCESSOR_LEFT = 8


class Task:
    no = 0
    status = None
    start_time = None
    end_time = None
    priority = None
    deadline = None
    penalty = None
    size = None
    owner = None
    assigned_processor = None
    general_queue_arrival_time = None
    tx_start_time = None
    tx_end_time = None
    estimated_tx_end_time = None
    processor_queue_arrival_time = None
    process_start_time = None
    process_end_time = None
    owner_departure_time = None

    is_assigned_to_cloud = False
    is_waited_in_general_queue = True
    is_waited_in_processor_queue = True
    tx_process = None
    server_process = None

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
        self.server_process = None
        self.ping_processes = []

    def __repr__(self) -> str:
        return f"Task#{self.no}: {self.status.name} owner:{self.owner} " \
               f"{self.start_time}-{self.end_time or 'Current'} {'(Cloud)' if self.is_assigned_to_cloud else ''}"

    def get_task_origin_data(self) -> str:
        return f"Task#{self.no} started at time {self.start_time} is from {self.owner.station.name} connected to" \
               f" {self.owner.station.wintfs[0].associatedTo}"

    def calculate_penalty(self):
        self.penalty = self.end_time - self.deadline
        logging.info(f"Penalty on Task#{self.no} is {self.penalty}")
        return self.penalty

    def get_prioritized_penalty(self):
        return self.priority * self.penalty

    def get_predicted_prioritized_penalty(self, possible_end_time):
        penalty = possible_end_time - self.deadline
        return self.priority * max(penalty, 0)

    def get_predicted_penalty_score(self, possible_end_time):
        penalty = possible_end_time - self.deadline
        if penalty < 0:
            score = penalty / self.priority
        else:
            score = penalty * self.priority
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
        if current_time == self.start_time:
            self.is_waited_in_general_queue = False
        self.tx_start_time = current_time

    def start_processing(self, current_time, process_duration):
        if current_time == self.tx_end_time:
            self.is_waited_in_processor_queue = False
        self.status = Status.PROCESSING
        self.process_start_time = current_time
        self.process_end_time = current_time + process_duration
        self.end_time = self.process_end_time
        self.calculate_penalty()
        new_event = Event(EventType.PROCESS_COMPLETE, self, self.end_time)
        EventManager.add_event(self.end_time, new_event)

    def get_process_time(self, processor_speed):
        return self.size / processor_speed

    def set_processor(self, processor):
        self.assigned_processor = processor

    def set_tx_complete(self, current_time):
        self.tx_end_time = current_time
        transfer_time = current_time - self.tx_start_time
        estimated_tx = self.estimated_tx_end_time - self.tx_start_time
        logging.info(f"Task#{self.no}'s {self.size}KB data is transfer in "
                     f"{Color.RED}{transfer_time:.1f}{Color.ENDC} s, "
                     f"estimated was {Color.GREEN}{estimated_tx}{Color.ENDC} s")
        TrafficObserver.decrement_traffic_on_sta(self.owner.station.name)
        if self.is_assigned_to_cloud:
            process_duration = self.get_process_time(s.CLOUD_PROCESSOR_SPEED)
            self.start_processing(current_time, process_duration)
            TrafficObserver.decrement_traffic_on_cloud()
        else:
            self.status = Status.WAITING_ON_QUEUE
            self.assigned_processor.start_to_process_task(current_time)
            TrafficObserver.decrement_traffic_on_sta(self.assigned_processor.station.name)

    def set_estimated_tx_end_time(self, current_time, estimated_tx_time):
        self.estimated_tx_end_time = current_time + estimated_tx_time

    def get_result(self):
        return TaskResult(self)

    def get_task_identifier(self):
        if self.is_assigned_to_cloud:
            assigned = f"cloud,{Simulation.cloud_server.name}"
        else:
            assigned = f"{self.assigned_processor.sumo_id}({self.assigned_processor.station.name})"
        return f"Task#{self.no} {self.owner.sumo_id}({self.owner.station.name})->{assigned}"


class TaskResult:
    no = 0
    status = None
    start_time = None
    end_time = None
    priority = None
    deadline = None
    penalty = None
    size = None
    owner = None
    assigned_processor = None
    general_queue_arrival_time = None
    tx_start_time = None
    tx_end_time = None
    estimated_tx_end_time = None
    processor_queue_arrival_time = None
    process_start_time = None
    process_end_time = None
    owner_departure_time = None

    is_assigned_to_cloud = None
    is_waited_in_general_queue = None
    is_waited_in_processor_queue = None
    tx_process = None

    def __init__(self, task):
        self.no = task.no
        self.status = task.status
        self.start_time = task.start_time
        self.end_time = task.end_time
        self.priority = task.priority
        self.deadline = task.deadline
        self.penalty = task.penalty
        self.size = task.size
        self.owner = f"{task.owner.sumo_id}({task.owner.station.name})"
        if task.assigned_processor:
            self.assigned_processor = f"{task.assigned_processor.sumo_id}({task.assigned_processor.station.name})"
        self.general_queue_arrival_time = task.general_queue_arrival_time
        self.tx_start_time = task.tx_start_time
        self.tx_end_time = task.tx_end_time
        self.processor_queue_arrival_time = task.processor_queue_arrival_time
        self.process_start_time = task.process_start_time
        self.process_end_time = task.process_end_time
        self.owner_departure_time = task.owner_departure_time
        self.estimated_tx_end_time = task.estimated_tx_end_time
        self.is_assigned_to_cloud = task.is_assigned_to_cloud
        self.is_waited_in_general_queue = task.is_waited_in_general_queue
        self.is_waited_in_processor_queue = task.is_waited_in_processor_queue
        if task.tx_process and task.tx_process.poll() is not None:
            self.tx_process = task.tx_process.communicate()

    def get_timeline(self):
        timeline = f"Start:{self.start_time} -> "
        if not self.is_assigned_to_cloud and {self.tx_start_time}:
            timeline += f"PoolLeave:{self.tx_start_time} -> "
        if self.status in [Status.TX_CLOUD, Status.TX_PROCESSOR]:
            return f"{timeline}EstimatedTx: {self.estimated_tx_end_time:.0f}"
        elif self.status == Status.OWNER_LEFT:
            timeline += f"OwnerLeft: {self.owner_departure_time}"
            return timeline
        elif not self.tx_end_time:
            return timeline
        if self.estimated_tx_end_time:
            estimated_tx_end_time = f"({self.estimated_tx_end_time:.0f})"
            if self.estimated_tx_end_time < self.tx_end_time:
                estimated_tx_end_time = f"{Color.RED}{estimated_tx_end_time}{Color.ENDC}"
        else:
            estimated_tx_end_time = ""
        timeline += f"Tx_end:{self.tx_end_time:.0f}{estimated_tx_end_time} -> "
        if not self.is_assigned_to_cloud:
            timeline += f"QueueLeave:{self.process_start_time} -> "
        end_time = f"End:{self.end_time:.0f}" if self.end_time else ""
        timeline += end_time
        return timeline

    def get_prioritized_penalty(self):
        result = 0
        if self.status == Status.OWNER_LEFT:
            self.penalty = self.owner_departure_time - self.deadline + s.TASK_FAILURE_PENALTY_OFFSET
        elif self.status in [Status.TX_PROCESSOR, Status.TX_CLOUD]:
            self.penalty = max(s.SIMULATION_DURATION - self.deadline, 0)
        if self.penalty:
            result = max(0, self.penalty * self.priority)
        return result

    def __str__(self) -> str:
        processor = f"{Color.BLUE}cloud{Color.ENDC}" if self.is_assigned_to_cloud else self.assigned_processor

        if self.status in [Status.COMPLETED, Status.PROCESSING]:
            penalty = f"Penalty:{self.penalty:.1f} Prioritized penalty: {self.priority * self.penalty:.1f}"
        else:
            penalty = ""

        status = self.status.name
        if self.status == Status.COMPLETED:
            status = f"{Color.GREEN}{status}{Color.ENDC}"
        elif self.status in [Status.OWNER_LEFT, Status.PROCESSOR_LEFT]:
            status = f"{Color.RED}{status}{Color.ENDC}"

        return f"Task#{self.no} \t{status} \t{self.owner}->{processor} \t {self.get_timeline()} \t" \
               f"{penalty}"
