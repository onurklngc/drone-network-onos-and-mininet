import logging
from enum import Enum
from math import ceil


class EventType(Enum):
    PROCESS_COMPLETE = 0


class Event:
    def __init__(self, event_type, task, time):
        self.event_type = event_type
        self.task = task
        self.time = time

    def __str__(self) -> str:
        return f"{self.time} -> {self.event_type.name} for Task#{self.task.no}"


class EventManager:
    events = {}

    @staticmethod
    def add_event(event_time, event):
        logging.info("New event added: %s" % event)
        if ceil(event_time) in EventManager.events:
            EventManager.events[ceil(event_time)].append(event)
        else:
            EventManager.events[ceil(event_time)] = [event]

    @staticmethod
    def get_events_on_time_t(given_time):
        if given_time in EventManager.events:
            return EventManager.events.get(given_time)
        else:
            return []
