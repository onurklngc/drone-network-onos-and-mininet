import logging
import random
from concurrent.futures import ThreadPoolExecutor

import settings as s
from actors.Task import Task
from actors.Vehicle import TaskGeneratorVehicle
from sumo_traci import SumoVehicle

executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="news_reporter")


def send_task_request_to_task_assigner(task_assigner_host_ip, task):
    mn_station = task.owner.station
    command = "echo '{}' | nc {} {} -w 3".format(task.get_task_origin_data(), task_assigner_host_ip,
                                                 str(s.TASK_REQUEST_LISTEN_PORT))
    logging.info("Command to be called: %s" % command)
    # cmd_output = mn_station.cmd("ping -c 1 %s" % task_assigner_host_ip)
    # logging.info("Ping result: %s" % cmd_output)
    cmd_output = mn_station.cmd(command)
    if len(cmd_output) < 10:
        logging.error("Error while sending task request, shall try again")
        cmd_output = mn_station.cmd(command)
    logging.info("Command result: %s" % cmd_output)
    # os.system(command)


def send_task_request_to_task_assigner_async(task_assigner_host_ip, task):
    executor.submit(send_task_request_to_task_assigner, task_assigner_host_ip, task)


if __name__ == '__main__':
    start_time = 111
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    sumo_vehicle = SumoVehicle("veh111", type_abbreviation=random.choice(["E", "T"]), route_length=350)
    task_generator_vehicle = TaskGeneratorVehicle(sumo_vehicle, None, start_time)
    size = random.randint(*s.TASK_SIZE)
    deadline = random.randint(*s.DEADLINE)
    dummy_task = Task(start_time, task_generator_vehicle, size, deadline)
    send_task_request_to_task_assigner("127.0.0.1", dummy_task)
    send_task_request_to_task_assigner_async("127.0.0.1", dummy_task)
