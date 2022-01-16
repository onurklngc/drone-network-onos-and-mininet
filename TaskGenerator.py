import logging
import random

import numpy as np

import settings as s
from actors.Task import Task


class TaskGenerator(object):
    available_task_generators = None
    completed_tasks = None
    task_timeline = None
    next_task_id = 0

    def __init__(self, timeline=None):
        self.available_task_generators = {}
        self.pool = []
        self.completed_tasks = []
        self.task_timeline = []
        self.next_task_id = 0
        if not timeline:
            self.generate_task_timeline()
        else:
            self.task_timeline = timeline
        self.number_of_tasks = len(self.task_timeline)

    def add_to_available_task_generators(self, vehicle):
        self.available_task_generators[vehicle.sumo_id] = vehicle
        logging.debug(f"New generator vehicle is added: {vehicle.sumo_id}")

    def remove_task_generator(self, vehicle_id):
        self.available_task_generators.pop(vehicle_id)
        logging.debug(f"Generator vehicle is removed: {vehicle_id}")

    def generate_task_timeline(self):
        t = s.TASK_GENERATION_START_TIME
        while t < s.TASK_GENERATION_END_TIME:
            self.task_timeline.append(t)
            next_interval = round(np.random.exponential(s.TASK_GENERATION_INTERVAL))
            t += next_interval
        return self.task_timeline

    def select_generator(self):
        idle_generators = []
        for generator in self.available_task_generators.values():
            if generator.station.wintfs[0].associatedTo and not generator.is_leaving_soon:
                number_of_active_tasks = generator.get_number_of_pool_and_tx_tasks()
                for i in range(s.GENERATOR_ACTIVE_TASKS_MAX-number_of_active_tasks):
                    idle_generators.append(generator)
        if idle_generators:
            return random.choice(idle_generators)
        return None

    def generate_new_tasks(self, current_time, generator_id=None, new_tasks=None):
        if new_tasks is None:
            new_tasks = []
        if self.next_task_id == self.number_of_tasks:
            return new_tasks

        start_time = self.task_timeline[self.next_task_id]

        if start_time == current_time:
            logging.info("Creating task at time %d", current_time)
            self.next_task_id += 1
            if not self.available_task_generators:
                logging.error("No task generator vehicle available at time %d", current_time)
                return new_tasks
            if generator_id:
                selected_generator = None  # TODO
            else:
                selected_generator = self.select_generator()
            if not selected_generator:
                logging.error("No connected generator vehicle available at time %d", current_time)
                return new_tasks
            size = random.randint(*s.TASK_SIZE)
            deadline = current_time + random.randint(*s.DEADLINE)
            task = Task(start_time, selected_generator, size, deadline)
            selected_generator.add_task(task)
            new_tasks.append(task)
            return self.generate_new_tasks(current_time, generator_id, new_tasks)
        else:
            logging.debug("No task at time %d", current_time)
            return new_tasks


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")

    task_generator = TaskGenerator()
    task_generator.generate_task_timeline()
    print(
        f"For {s.TASK_GENERATION_END_TIME - s.TASK_GENERATION_START_TIME} seconds, "
        f"{len(task_generator.task_timeline)} tasks generated with "
        f"{s.TASK_GENERATION_INTERVAL} exponential interval.")
    print(task_generator.task_timeline)
