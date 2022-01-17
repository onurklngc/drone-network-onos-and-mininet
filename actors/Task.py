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
    OWNER_LEFT = 7
    PROCESSOR_LEFT = 8


class Task:
    no = 0
    status = None
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
    tx_process = None

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
        self.calculate_delay()
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
        logging.info(f"Task #{self.no}'s {self.size}KB data is transfer in "
                     f"{Color.RED}{transfer_time:.1f}{Color.ENDC} s, "
                     f"estimated was {Color.GREEN}{estimated_tx}{Color.ENDC} s")
        TrafficObserver.decrement_traffic_on_sta(self.owner.station.name)
        if self.is_assigned_to_cloud:
            process_duration = self.get_process_time(s.CLOUD_PROCESSOR_SPEED)
            self.start_processing(current_time, process_duration)
            TrafficObserver.decrement_traffic_on_cloud()
        else:
            self.status = Status.WAITING_ON_QUEUE
            self.assigned_processor.start_task(current_time)
            TrafficObserver.decrement_traffic_on_sta(self.assigned_processor.station.name)

    def set_estimated_tx_end_time(self, current_time, estimated_tx_time):
        self.estimated_tx_end_time = current_time + estimated_tx_time

    def get_result(self):
        return TaskResult(self)


class TaskResult:
    no = 0
    status = None
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
        self.delay = task.delay
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
        self.is_assigned_to_cloud = task.is_assigned_to_cloud
        self.is_waited_in_general_queue = task.is_waited_in_general_queue
        self.is_waited_in_processor_queue = task.is_waited_in_processor_queue
        if task.tx_process and task.tx_process.poll() is not None:
            self.tx_process = task.tx_process.communicate()

    def get_timeline(self):
        timeline = f"Start:{self.start_time} -> "
        if not self.is_assigned_to_cloud:
            timeline += f"Pool_leave:{self.tx_start_time} -> "
        timeline += f"Tx_end:{self.tx_end_time} -> "
        if not self.is_assigned_to_cloud:
            timeline += f"Queue_leave:{self.process_start_time} -> "
        timeline += f"End:{self.end_time}"
        return timeline

    def __str__(self) -> str:
        processor = f"{Color.BLUE}cloud{Color.ENDC}" if self.is_assigned_to_cloud else self.assigned_processor

        if self.status == Status.COMPLETED:
            delay = f"Delay:{self.delay:.1f} Prioritized delay: {self.priority * self.delay:.1f}"
        else:
            delay = ""

        status = self.status.name
        if self.status == Status.COMPLETED:
            status = f"{Color.GREEN}{status}{Color.ENDC}"
        elif self.status in [Status.OWNER_LEFT, Status.PROCESSOR_LEFT]:
            status = f"{Color.RED}{status}{Color.ENDC}"

        return f"Task #{self.no} \t{status} \t{self.owner}->{processor} \t {self.get_timeline()} \t" \
               f"{delay}"
