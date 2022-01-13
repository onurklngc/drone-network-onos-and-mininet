from enum import Enum


class Status(Enum):
    GENERATED = 0
    ON_POOL = 1
    TX_CLOUD = 2
    TX_PROCESSOR = 3
    WAITING_ON_QUEUE = 4
    PROCESSING = 5
    COMPLETED = 6


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
    general_queue_departure_time = None
    tx_time = None
    tx_complete_time = None
    processor_queue_arrival_time = None
    processor_queue_departure_time = None
    process_start_time = None
    process_end_time = None

    is_assigned_to_cloud = False
    is_waited_in_general_queue = True
    is_waited_in_processor_queue = True

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

    def __str__(self) -> str:
        return f"Task #{self.no} from {self.owner.station.name}: {self.status.name}\t" \
               f"{self.start_time}-{self.end_time or 'Current'} {'(Cloud)' if self.is_assigned_to_cloud else ''}"

    def get_task_origin_data(self) -> str:
        return f"Task #{self.no} started at time {self.start_time} is from {self.owner.station.name} connected to" \
               f" {self.owner.station.wintfs[0].associatedTo}"

    def get_prioritized_delay(self):
        self.delay = self.deadline - (self.end_time - self.start_time)
        return self.priority * self.delay

    def get_task_time(self):
        return self.end_time - self.start_time

    def assign_to_cloud(self):
        self.is_assigned_to_cloud = True
        self.status = Status.TX_CLOUD

    def assign_to_pool(self):
        self.is_assigned_to_cloud = False
        self.status = Status.ON_POOL
