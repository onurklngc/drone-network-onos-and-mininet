from enum import Enum

from actors.Task import Status
from actors.constant import Color
import settings as s


class Action(Enum):
    CLOUD = 0
    SKIP = 1

    def __repr__(self):
        return self.name


class Solution:
    decisions = None
    score = None
    scores_by_decision = None
    details = None
    tasks = None

    def __init__(self, decisions, score, scores_by_decision, details, tasks=None):
        self.decisions = decisions
        self.score = score
        self.scores_by_decision = scores_by_decision
        self.details = details
        self.tasks = tasks


class TaskSolution:
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
    tx_start_time = None
    tx_end_time = None
    estimated_tx_end_time = None
    processor_queue_arrival_time = None
    process_start_time = None
    process_end_time = None
    owner_departure_time = None
    is_assigned_to_cloud = False

    def __init__(self, no, start_time, end_time, priority, deadline, penalty, size, owner_sumo_id, owner_sta_name,
                 owner_departure_time):
        self.no = no
        self.start_time = start_time
        self.end_time = end_time
        self.priority = priority
        self.deadline = deadline
        self.penalty = penalty
        self.size = size
        self.owner = f"{owner_sumo_id}({owner_sta_name})"
        self.owner_departure_time = owner_departure_time

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
            # if self.owner_departure_time is None:
            #     self.owner_departure_time = s.SIMULATION_DURATION
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
