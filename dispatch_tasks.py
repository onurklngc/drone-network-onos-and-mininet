import logging
import random
from concurrent.futures import ThreadPoolExecutor

import settings as s
from actors.Task import Task
from actors.Vehicle import TaskGeneratorVehicle
from actors.constant import Color
from sumo_traci import SumoVehicle

executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="news_reporter")
cloud_processes = {}
task_request_processes = {}


def send_task_request_to_task_assigner(task_assigner_host_ip, task):
    mn_station = task.owner.station
    command = "echo '{}' | nc {} {} -w 3".format(task.get_task_origin_data(), task_assigner_host_ip,
                                                 str(s.TASK_REQUEST_LISTEN_PORT))
    logging.info("Command to be called: %s" % command)
    # cmd_output = mn_station.cmd("ping -c 1 %s" % task_assigner_host_ip)
    # logging.info("Ping result: %s" % cmd_output)
    # cmd_output = mn_station.cmd(command)
    # if len(cmd_output) < 10:
    #     logging.error("Error while sending task request, shall try again")
    #     cmd_output = mn_station.cmd(command)
    # logging.info("Command result: %s" % cmd_output)
    # os.system(command)
    task_request_process = mn_station.popen(command)
    task_request_processes[task.no] = task_request_process


def send_task_data_to_cloud(cloud_ip, task, log_server_ip):
    logging.info(f"{Color.BLUE}Task #{task.no}: {task.owner.station.name}->Cloud{Color.ENDC}")
    mn_station = task.owner.station
    # cmd_output = mn_station.cmd("ping -c 1 %s" % cloud_ip)
    # logging.info("Ping result: %s" % cmd_output)
    command = get_send_file_command(cloud_ip, task.size, s.NAT_HOST_ID, log_server_ip)
    logging.info("Command to be called: %s" % command)
    data_send_process = mn_station.popen(command)
    cloud_processes[task.no] = data_send_process
    task.tx_process = data_send_process
    return data_send_process


def send_task_data_to_processor(task, log_server_ip):
    src_station = task.owner.station
    dst_station = task.assigned_processor.station
    dst_station_ip = dst_station.wintfs[0].ip
    dst_station.popen("ping -c 1 %s" % src_station.wintfs[0].ip)
    command = get_send_file_command(dst_station_ip, task.size, s.NAT_HOST_ID, log_server_ip)
    logging.info("Command to be called: %s" % command)
    data_send_process = src_station.popen(command)
    task_request_processes[task.no] = data_send_process
    task.tx_process = data_send_process
    return data_send_process


def get_send_file_command(target_ip, data_size, target_id, log_server_ip):
    if s.USE_IPERF:
        command = "iperf -c {0} -n {1}KB -f KB -y C".format(target_ip, data_size)
    else:
        command = "ITGSend -a {0} -T TCP -C 100000 -c 1408 -k {1} -L {2} TCP -l {3}/{4}.log " \
                  "-Sdp {5} -rp {7} -j 1 -poll" \
            .format(target_ip, data_size, log_server_ip,
                    s.ITG_SENDER_LOG_PATH, target_id, target_id + 9000, target_id + 9200, target_id + 9400
                    )
    return command


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
