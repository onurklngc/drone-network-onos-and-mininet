import bisect
import logging
import random

import settings as s
from actors.Task import Task
from actors.Vehicle import TaskGeneratorVehicle
from sumo_traci import SumoVehicle


class TaskOrganizer(object):
    pool = None
    tasks_being_processed_on_cloud = None
    active_tasks = None
    completed_tasks = None
    cloud_thresholds = None
    available_task_generators = {}

    def __init__(self):
        self.available_task_generators = {}
        self.tasks_being_processed_on_cloud = []
        TaskOrganizer.cloud_thresholds = list(s.CLOUD_PROBABILITY_BY_POOL_SIZE.keys())
        TaskOrganizer.cloud_thresholds.sort()

        self.pool = []
        self.active_tasks = []
        self.completed_tasks = []

    def handle_tasks(self, current_time):
        pass

    def add_task(self, current_time, task):
        pool_size = len(self.pool)
        threshold_index = bisect.bisect_right(TaskOrganizer.cloud_thresholds, pool_size) - 1
        cloud_probability = s.CLOUD_PROBABILITY_BY_POOL_SIZE[TaskOrganizer.cloud_thresholds[threshold_index]]
        lottery = random.random()
        is_assigned_to_cloud = lottery < cloud_probability

        if is_assigned_to_cloud:
            task.assign_to_cloud()
            self.assign_to_cloud(task)
        else:
            self.pool.append(task)
            task.assign_to_pool()
        logging.info(f"{task}")

    def assign_to_cloud(self, new_task):
        self.tasks_being_processed_on_cloud.append(new_task)

    def add_to_available_task_processors(self, vehicle):
        self.available_task_generators[vehicle.sumo_id] = vehicle
        logging.debug(f"New generator vehicle is added: {vehicle.sumo_id}")

    def remove_from_available_task_processors(self, vehicle_id):
        self.available_task_generators.pop(vehicle_id)
        logging.debug(f"Generator vehicle is removed: {vehicle_id}")


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
