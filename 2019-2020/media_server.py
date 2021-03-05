import json
import os
import pickle
import signal
import socket
import sys
import threading
import traceback
import urllib2  # ,base64
from random import choice
from time import sleep

import numpy as np

from controller_utils import get_distance_and_switches_passed
from network_utils import *
from settings import *
from switch_manager import SwitchManager
from switch_operations import SwitchOperator

DEBUG = True

server_ip = None
media_server = None

request_id = 0
lock_request_number = threading.Lock()
lock_found = threading.Lock()
lock_taken = threading.Lock()
switch_id_to_name = {}
switch_name_to_id = {}


def debug(msg):
    if DEBUG:
        print(msg)


def redirect_request_to_device(file_sender_device, message, requested_file_size):
    redirect_message = message.strip() + ";" + str(requested_file_size)
    # debug("redirect_message: %s" % redirect_message)
    if file_sender_device.startswith("of"):
        # This is a switch
        file_sender_device = switch_id_to_its_cache_host_ip(file_sender_device)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((file_sender_device, FILE_REQUEST_LISTEN_PORT))
        s.sendall(redirect_message.encode('ascii'))
        s.close()
    except Exception as e:
        debug(e)


def inform_host_is_available(sender_ip, host_ip):
    message = sender_ip + ";" + host_ip
    debug("Inform %s" % message)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((MININET_IP, HOST_AVAILABILITY_LISTEN_PORT))
        s.sendall(message.encode('ascii'))
        s.close()
    except Exception as e:
        debug(e)


def send_file(requesting_host_ip, file_size):
    if USE_IPERF:
        result = os.system(
            "iperf -c {0} -n {1}KB -f KB >/dev/null".format(
                requesting_host_ip,
                file_size,
            )
        )
    else:
        pass
        # debug(
        #     "ITGSend -a {0} -T TCP -C 100000 -c 1408 -k {1} -L {2} TCP -l {3}/{4}.log -Sdp {5} -rp {7} -j 1 -poll"
        #     .format(
        #         requesting_host_ip,
        #         file_size,
        #         ITG_LOG_SERVER_IP,
        #         ITG_SENDER_LOG_PATH,
        #         "media_server",
        #         destinationHostID + 9000,
        #         destinationHostID + 9200,
        #         destinationHostID + 9400
        #     )
        # )
        result = os.system(
            "ITGSend -a {0} -T TCP -C 10000  -c 1408 -k {1} -L {2} TCP -X {2} TCP -l logsS/{3}.log -x logsR/{3}.log".format(
                requesting_host_ip, file_size,
                ITG_LOG_SERVER_IP, "media_server"))
    debug("Send result to %s: %d" % (requesting_host_ip, result))
    inform_host_is_available(server_ip, requesting_host_ip)


class MediaServer(object):
    switch_operator = None
    switch_manager = None

    file_sizes = []
    file_request_number = []
    total_file_request_number = 0
    number_of_files = 0
    hosts_cached_file = {}
    switches_cached_file = {}
    remaining_device_memory_sizes = {}
    media_files_on_devices = {}
    cache_found_at_requester = 0
    cache_found_at_another_host = 0
    cache_found_at_switch = 0
    total_distance_taken = 0
    switch_selected_as_source = 0
    host_selected_as_source = 0
    media_server_selected_as_source = 0
    number_of_requests_connection_is_missing = 0
    transferred_data_kb = 0

    def __init__(self, switch_operator=None, switch_manager=None, number_of_files=NUMBER_OF_FILES,
                 mean_file_size_in_kb=MEAN_FILE_SIZE_IN_KB):

        if switch_operator:
            self.switch_operator = switch_operator
        else:
            self.switch_operator = SwitchOperator()
        if switch_manager:
            self.switch_manager = switch_manager
        else:
            self.switch_manager = SwitchManager()

        self.file_sizes = np.random.uniform(low=mean_file_size_in_kb * 0.8, high=mean_file_size_in_kb * 1.2,
                                            size=number_of_files).astype(int)
        self.number_of_files = number_of_files
        self.file_request_number = np.zeros(number_of_files, dtype=int)
        self.hosts_cached_file = {}
        self.switches_cached_file = {}
        self.media_files_on_devices = {}
        self.remaining_device_memory_sizes = {}
        self.energy_cost_matrix = []
        self.flow_hop_matrix = []

    def get_remaining_device_storage(self, device):

        if device not in self.remaining_device_memory_sizes:
            if device.startswith("of"):
                # This is a switch
                self.remaining_device_memory_sizes[device] = CACHING_STORAGE_PER_SWITCH
            else:
                # This is an end user
                self.remaining_device_memory_sizes[device] = CACHING_STORAGE_PER_HOST
            self.media_files_on_devices[device] = []

            debug("Initial memory on %s is %d" % (device, self.remaining_device_memory_sizes[device]))
        else:
            debug("Remaining memory on %s is %d" % (device, self.remaining_device_memory_sizes[device]))
        return self.remaining_device_memory_sizes[device]

    def change_remaining_device_memory_size(self, device, recorded_file=None, removed_file=None):
        change = 0
        if recorded_file is not None:
            change = -self.file_sizes[recorded_file]
        if removed_file is not None:
            change += self.file_sizes[removed_file]
        # debug("Storage change is %d" % change)
        self.remaining_device_memory_sizes[device] += change
        # debug("Remaining memory on %s is %d" % (device, self.remaining_device_memory_sizes[device]))

    def get_file_from_own_cache(self, host, file_id):
        # Change the access order.
        debug(host + " already has file %d" % file_id)
        lock_found.acquire()
        self.cache_found_at_requester += 1
        lock_found.release()
        self.media_files_on_devices[host].remove(file_id)
        self.media_files_on_devices[host].append(file_id)

    def decide_on_which_files_to_delete_on_device(self, device, required_storage):
        if device.startswith("of"):
            # This is a switch
            if CACHING_MODE_SWITCH == "LRU":
                self.caching_lru(device, required_storage)
            elif CACHING_MODE_SWITCH == "PROB":
                self.caching_probability_based(device, required_storage)
            elif CACHING_MODE_SWITCH == "MRU":
                self.caching_mru(device, required_storage)
        else:
            # This is an end user
            if CACHING_MODE_HOST == "LRU":
                self.caching_lru(device, required_storage)
            elif CACHING_MODE_HOST == "PROB":
                self.caching_probability_based(device, required_storage)
            elif CACHING_MODE_HOST == "MRU":
                self.caching_mru(device, required_storage)

    def remove_file(self, device, file_id):
        self.media_files_on_devices[device].remove(file_id)
        if device.startswith("of"):
            # This is a switch
            self.switches_cached_file[file_id].remove(device)
        else:
            # This is an end user
            self.hosts_cached_file[file_id].remove(device)
        # debug("Remove %d file on %s" % (file_id, device))

    def add_file(self, device, file_id):
        self.media_files_on_devices[device].append(file_id)
        if device.startswith("of"):
            # This is a switch
            self.switches_cached_file[file_id].append(device)
        else:
            # This is an end user
            self.hosts_cached_file[file_id].append(device)
        # debug("Add %d file on %s" % (file_id, device))

    def get_hosts_having_this_file(self, file_id):
        if file_id in self.hosts_cached_file:
            return self.hosts_cached_file[file_id]
        else:
            self.hosts_cached_file[file_id] = []
            return []

    def get_switches_having_this_file(self, file_id):
        if file_id in self.switches_cached_file:
            return self.switches_cached_file[file_id]
        else:
            self.switches_cached_file[file_id] = []
            return []

    def cache_media_on_device(self, device, file_id):
        file_size = self.file_sizes[file_id]
        # debug("File size %d" % (file_size))
        remaining_device_storage = self.get_remaining_device_storage(device)
        if remaining_device_storage >= file_size:
            # debug("There is space")
            self.add_file(device, file_id)
            self.change_remaining_device_memory_size(device, recorded_file=file_id)
        else:
            required_storage = file_size - remaining_device_storage
            self.decide_on_which_files_to_delete_on_device(device, required_storage)

            self.add_file(device, file_id)
            self.change_remaining_device_memory_size(device, recorded_file=file_id)

    def caching_lru(self, device, required_storage):
        # Least Recently Used
        deleted_file_size = 0
        while deleted_file_size <= required_storage:
            files_on_device = self.media_files_on_devices[device]
            # debug("Files on device %s : %s" % (device, str(files_on_device)))
            file_to_be_deleted = files_on_device[0]
            deleted_file_size += self.file_sizes[file_to_be_deleted]
            # debug("file_to_be_deleted %d" % file_to_be_deleted)
            self.remove_file(device, file_to_be_deleted)
            self.change_remaining_device_memory_size(device, removed_file=file_to_be_deleted)

    def caching_mru(self, device, required_storage):
        # Most Recently Used
        deleted_file_size = 0
        while deleted_file_size <= required_storage:
            files_on_device = self.media_files_on_devices[device]
            # debug("Files on device %s : %s" % (device, str(files_on_device)))
            file_to_be_deleted = files_on_device[-1]
            deleted_file_size += self.file_sizes[file_to_be_deleted]
            # debug("file_to_be_deleted %d" % file_to_be_deleted)
            self.remove_file(device, file_to_be_deleted)
            self.change_remaining_device_memory_size(device, removed_file=file_to_be_deleted)

    def caching_probability_based(self, device, required_storage):
        deleted_file_size = 0
        while deleted_file_size <= required_storage:
            files_on_device = self.media_files_on_devices[device]
            # debug("Files on device %s : %s" % (device, str(files_on_device)))
            available_cache_numbers = [len(self.hosts_cached_file[file_id]) + len(self.switches_cached_file[file_id])
                                       for file_id
                                       in
                                       files_on_device]
            total_request_numbers = [self.file_request_number[file_id] for file_id in files_on_device]
            availability_of_files = [float(available_cache_numbers[i]) / total_request_numbers[i] for i in
                                     range(len(files_on_device))]
            # debug("Availability ratios are : %s" % str(availability_of_files))
            index_of_max = availability_of_files.index(max(availability_of_files))
            file_to_be_deleted = files_on_device[index_of_max]
            deleted_file_size += self.file_sizes[file_to_be_deleted]
            # debug("file_to_be_deleted %d" % file_to_be_deleted)
            self.remove_file(device, file_to_be_deleted)
            self.change_remaining_device_memory_size(device, removed_file=file_to_be_deleted)

    def get_caching_statistics(self):
        # self.printEnergyCostToFile()
        average_distance_taken = 1.0 * self.total_distance_taken / self.total_file_request_number \
            if self.total_file_request_number != 0 else 0
        report = {"file_request_number": self.total_file_request_number,
                  "cache_found_at_requester": self.cache_found_at_requester,
                  "cache_found_at_switch": self.cache_found_at_switch,
                  "cache_found_at_another_host": self.cache_found_at_another_host,
                  "cache_taken_from_switch": self.switch_selected_as_source,
                  "cache_taken_from_host": self.host_selected_as_source,
                  "media_server_selected_as_source": self.media_server_selected_as_source,
                  "total_distance_taken": self.total_distance_taken,
                  "average_distance_taken": average_distance_taken,
                  "number_of_requests_connection_is_missing": self.number_of_requests_connection_is_missing,
                  "transferred_data_kb": self.transferred_data_kb,
                  }
        return report

    def print_energy_cost_to_file(self, file_name=None):
        if file_name is None:
            file_name = "energyCostArray/1.csv"
        with open(file_name, 'wb+') as fp:
            pickle.dump(self.energy_cost_matrix, fp)

    def get_switch_distances(self):
        pass

    def get_closest_host(self):
        pass

    def update_switch_caches(self, switches_visited, requested_file_id):
        if CACHE_ON_SWITCHES:
            for switch in switches_visited:
                self.cache_media_on_device(switch, requested_file_id)

    def select_source_energy_aware(self, hosts_having_this_file,
                                   switches_having_this_file, requesting_host_ip, file_size):

        candidate_list = []
        distance_list = []
        try:
            switch_ids_having_this_file = [self.switch_manager.get_id_by_of_name(switch) for switch in
                                           switches_having_this_file]
            for switch in switch_ids_having_this_file:
                if switch not in self.switch_operator.caching_switches:
                    switch_ids_having_this_file.remove(switch)
            # Host sources
            for srcHost in hosts_having_this_file:
                if host_ip_to_its_one_by_one_switch_id(srcHost) in switch_ids_having_this_file:
                    # Skip host if its switch has the file
                    continue
                try:
                    temp_distance, temp_switches_visited = get_distance_and_switches_passed(srcHost, requesting_host_ip)
                except:
                    continue
                candidate_list.append(
                    [srcHost, SOURCE_HOST,
                     [self.switch_manager.get_id_by_of_name(switch) for switch in temp_switches_visited]])
                distance_list.append(temp_distance)
            # Switch sources
            for srcSwitch in switches_having_this_file:
                try:
                    temp_distance, temp_switches_visited = get_distance_and_switches_passed(srcSwitch,
                                                                                            requesting_host_ip)
                except:
                    continue
                candidate_list.append([self.switch_manager.get_id_by_of_name(srcSwitch), SOURCE_SWITCH,
                                       [self.switch_manager.get_id_by_of_name(switch) for switch in
                                        temp_switches_visited]])
                distance_list.append(temp_distance)

            # # Consider Content server
            if len(candidate_list) == 0:
                # TODO at the end content server shall rock
                try:
                    temp_distance, temp_switches_visited = get_distance_and_switches_passed(server_ip,
                                                                                            requesting_host_ip)
                    candidate_list.append(
                        [server_ip, SOURCE_CONTENT_SERVER,
                         [self.switch_manager.get_id_by_of_name(switch) for switch in temp_switches_visited]])
                    distance_list.append(temp_distance)
                except:
                    debug("It has no access to content server")
            if not len(candidate_list) > 0:
                debug("No internet")
                return SOURCE_NOT_AVAILABLE, SOURCE_NOT_AVAILABLE, 0, []

            candidate_id, lowest_cost, switches_shall_cache = self.switch_operator.estimate_energy_cost(candidate_list,
                                                                                                        file_size)
            self.energy_cost_matrix.append(lowest_cost)
            if candidate_list[candidate_id][1] == SOURCE_SWITCH:
                chosen_source = self.switch_manager.get_of_name_by_id(candidate_list[candidate_id][0])
            else:
                chosen_source = candidate_list[candidate_id][0]
            switches_shall_cache = [self.switch_manager.get_of_name_by_id(switch) for switch in switches_shall_cache]
            debug("Request shall be redirected to %s with cost %f" % (chosen_source, lowest_cost))
            return chosen_source, candidate_list[candidate_id][1], distance_list[
                candidate_id], switches_shall_cache
        except Exception as e:
            print(traceback.format_exc())
            debug(traceback.format_exc())
            print(e)

    def select_source_min_hop(self, hosts_having_this_file, switches_having_this_file, requesting_host_ip, file_size):
        lowest_distance = np.inf
        switches_visited = []
        chosen_source = ""
        source_type = SOURCE_HOST
        for srcHost in hosts_having_this_file:
            try:
                temp_distance, temp_switches_visited = get_distance_and_switches_passed(srcHost, requesting_host_ip)
            except:
                continue
            if lowest_distance > temp_distance:
                chosen_source = srcHost
                lowest_distance = temp_distance
                switches_visited = temp_switches_visited[:]
        for srcSwitch in switches_having_this_file:
            try:
                temp_distance, temp_switches_visited = get_distance_and_switches_passed(srcSwitch, requesting_host_ip)
            except:
                continue
            if lowest_distance > temp_distance:
                chosen_source = srcSwitch
                lowest_distance = temp_distance
                switches_visited = temp_switches_visited[:]
                source_type = SOURCE_SWITCH
        # # Check content server as well
        # try:
        #     temp_distance, temp_switches_visited = getDistance(server_ip, requesting_host_ip)
        #     if lowest_distance > temp_distance:
        #         chosen_source = srcSwitch
        #         lowest_distance = temp_distance
        #         switches_visited = temp_switches_visited[:]
        #         source_type = SOURCE_CONTENT_SERVER
        # except:
        #     debug("It has no access to content server")
        if lowest_distance == np.inf:
            debug("No internet")
            return SOURCE_NOT_AVAILABLE, SOURCE_NOT_AVAILABLE, 0, []
        if source_type == SOURCE_SWITCH:
            chosen_source = self.switch_manager.get_id_by_of_name(chosen_source)
        candidate_list = [[chosen_source, source_type,
                           [self.switch_manager.get_id_by_of_name(switch) for switch in switches_visited]]]
        candidate_id, lowest_cost, switches_shall_cache = self.switch_operator.estimate_energy_cost(candidate_list,
                                                                                                    file_size)
        if candidate_list[candidate_id][1] == SOURCE_SWITCH:
            chosen_source = self.switch_manager.get_of_name_by_id(candidate_list[candidate_id][0])
        else:
            chosen_source = candidate_list[candidate_id][0]
        switches_shall_cache = [self.switch_manager.get_of_name_by_id(switch) for switch in switches_shall_cache]
        debug("Request shall be redirected to %s with distance %d" % (chosen_source, int(lowest_distance)))
        return chosen_source, source_type, lowest_distance, switches_shall_cache

    def process_file_request(self, message, current_media_server_ip):
        global request_id, server_ip
        redirect_message = ""
        request_id += 1
        server_ip = current_media_server_ip
        debug("\nRequest # %d  " % request_id + message.strip())
        # File request protocol message: requesting_host_ip;requested_file_id
        message_parsed = message.split(";", 2)
        requesting_host_ip = message_parsed[0]
        requested_file_id = int(message_parsed[1])

        if self.total_file_request_number % REPORT_INTERVAL == 0:
            debug(self.get_caching_statistics())

        lock_request_number.acquire()
        self.file_request_number[requested_file_id] += 1
        self.total_file_request_number += 1
        lock_request_number.release()
        hosts_having_this_file = self.get_hosts_having_this_file(requested_file_id)[
                                 :]  # Added [:] to prevent addressing
        switches_having_this_file = self.get_switches_having_this_file(requested_file_id)[:]
        # debug("hosts_having_this_file before %s" % str(hosts_having_this_file))

        if requesting_host_ip not in hosts_having_this_file:

            debug(requesting_host_ip + " shall cache file %d" % requested_file_id)
            if hosts_having_this_file or switches_having_this_file:
                lock_found.acquire()
                self.cache_found_at_another_host += 1 if hosts_having_this_file else 0
                self.cache_found_at_switch += 1 if switches_having_this_file else 0
                lock_found.release()
                file_size = self.file_sizes[requested_file_id]

                if ROUTE_SELECTION_ENERGY_AWARE:
                    # Select the source with minimum energy cost
                    chosen_source, source_type, lowest_distance, switches_shall_cache = self.select_source_energy_aware(
                        hosts_having_this_file,
                        switches_having_this_file,
                        requesting_host_ip, file_size)
                else:
                    # Consider minimum hop count for source selection
                    chosen_source, source_type, lowest_distance, switches_shall_cache = self.select_source_min_hop(
                        hosts_having_this_file,
                        switches_having_this_file,
                        requesting_host_ip, file_size)

                lock_taken.acquire()
                if source_type == SOURCE_SWITCH:
                    self.switch_selected_as_source += 1
                elif source_type == SOURCE_HOST:
                    self.host_selected_as_source += 1
                elif source_type == SOURCE_CONTENT_SERVER:
                    self.media_server_selected_as_source += 1
                elif source_type == SOURCE_NOT_AVAILABLE:
                    self.number_of_requests_connection_is_missing += 1
                lock_taken.release()
                if chosen_source == SOURCE_NOT_AVAILABLE:
                    return chosen_source, "SOURCE_NOT_AVAILABLE"
                if GENERATE_TRAFFIC:
                    if chosen_source.startswith("of"):
                        # This is a switch
                        chosen_source = switch_id_to_its_cache_host_ip(chosen_source)
                    redirect_message = message.strip() + ";" + str(file_size)
                    # sendFileThread = threading.Thread(target=redirectRequestToDevice,
                    #                                   args=(chosen_source, message, file_size))
                    # sendFileThread.setDaemon(True)
                    # sendFileThread.start()
            else:
                try:
                    lowest_distance, switches_visited = get_distance_and_switches_passed(current_media_server_ip,
                                                                                         requesting_host_ip)
                    lock_taken.acquire()
                    self.media_server_selected_as_source += 1
                    lock_taken.release()
                    file_size = self.file_sizes[requested_file_id]
                    redirect_message = message.strip() + ";" + str(file_size)
                    chosen_source = current_media_server_ip
                    candidate_id, lowest_cost, switches_shall_cache = self.switch_operator.estimate_energy_cost(
                        [[chosen_source, SOURCE_CONTENT_SERVER,
                          [self.switch_manager.get_id_by_of_name(switch) for switch in switches_visited]]],
                        file_size)
                    self.energy_cost_matrix.append(lowest_cost)
                    switches_shall_cache = [self.switch_manager.get_of_name_by_id(switch) for switch in
                                            switches_shall_cache]
                    if GENERATE_TRAFFIC:
                        pass
                        # file_size = str(self.file_sizes[requested_file_id])
                        # sendFileThread = threading.Thread(target=sendFile, args=(requesting_host_ip, file_size))
                        # sendFileThread.setDaemon(True)
                        # sendFileThread.start()
                except:
                    debug("It has no access to content server")
                    self.number_of_requests_connection_is_missing += 1
                    chosen_source = SOURCE_NOT_AVAILABLE
                    return chosen_source, "SOURCE_NOT_AVAILABLE"
            if CACHE_ON_HOST:
                self.cache_media_on_device(requesting_host_ip, requested_file_id)
            self.total_distance_taken += lowest_distance
            self.flow_hop_matrix.append(lowest_distance)
            self.transferred_data_kb += file_size
            # Cache on the switches on the route
            self.update_switch_caches(switches_shall_cache, requested_file_id)
            return chosen_source, redirect_message
        else:
            self.get_file_from_own_cache(requesting_host_ip, requested_file_id)
            self.energy_cost_matrix.append(0)
            self.flow_hop_matrix.append(0)
            if GENERATE_TRAFFIC:
                return SOURCE_OWN_CACHE, "200"
                # informHostIsAvailable(requesting_host_ip, requesting_host_ip)


def terminate_handler(signum, frame, current_media_server=media_server):
    debug({"file_request_number": current_media_server.total_file_request_number,
           "caching_mode_switch": CACHING_MODE_SWITCH,
           "caching_mode_host": CACHING_MODE_HOST,
           "cache_found_at_requester": current_media_server.cache_found_at_requester,
           "cache_found_at_switch": current_media_server.cache_found_at_switch,
           "cache_found_at_another_host": current_media_server.cache_found_at_another_host,
           "cache_taken_from_switch": current_media_server.switch_selected_as_source,
           "cache_taken_from_host": current_media_server.host_selected_as_source,
           "media_server_selected_as_source": current_media_server.media_server_selected_as_source,
           "total_distance_taken": current_media_server.total_distance_taken,
           "average_distance_taken": current_media_server.total_distance_taken / current_media_server.total_file_request_number if current_media_server.total_file_request_number != 0 else 0
           })
    sys.exit(0)


def get_file_request(accepted_socket):
    message = accepted_socket.recv(1024).decode()
    accepted_socket.close()
    media_server.process_file_request(message)


def listen_file_requests():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((server_ip, FILE_REQUEST_LISTEN_PORT))
    s.listen(25)
    while True:
        try:
            accepted_socket, address = s.accept()
            get_file_request(accepted_socket)
        except Exception as e:
            debug("Crash in listenFileRequests")
            debug(e)


def remove_depleted_switches(depleted_batteries):
    media_server.switch_operator.switch_mover.number_of_switches_alive -= len(depleted_batteries)
    media_server.switch_operator.switch_mover.operating_switches = np.setdiff1d(
        media_server.switch_operator.switch_mover.operating_switches, depleted_batteries)
    if media_server.switch_operator.switch_mover.content_server_switch_id in depleted_batteries:
        print("Content server switch is depleted")
        media_server.switch_operator.switch_mover.get_central_node()
    if media_server.switch_operator.switch_mover.number_of_switches_alive <= 0:
        os._exit(0)


def move_switches(interval=MOVE_EVENT_INTERVALS):
    current_time = 0
    while media_server.switch_operator.switch_mover.number_of_switches_alive:
        sleep(interval)
        current_time += interval
        media_server.switch_operator.drone_battery_manager.decrease_battery_fly()
        depleted_batteries = media_server.switch_operator.drone_battery_manager.check_for_depleted_batteries()
        if depleted_batteries is not None:
            remove_depleted_switches(depleted_batteries)
        media_server.switch_operator.switch_mover.move_switches_for_one_time_interval()
        if current_time % 10 == 0:
            media_server.switch_operator.select_caching_nodes()
            print(media_server.switch_operator.drone_battery_manager.battery_levels)


def auto_request_file(scale_of_exponential=10, host_number=NUMBER_OF_HOSTS, alfa_zipf_exponent=1.1,
                      number_of_files=NUMBER_OF_FILES):
    from random import randint
    global server_ip
    s = np.random.zipf(alfa_zipf_exponent, number_of_files * 10)
    random_file_selection_list = s[s < number_of_files + 1] - 1
    t = threading.currentThread()
    while getattr(t, "is_running", True):
        requesting_host_id = str(randint(1, host_number))
        requested_file_id = str(choice(random_file_selection_list))
        # requested_file_id = str(0)
        host_ip = host_id_to_ip(requesting_host_id)
        request_message = "{};{}".format(host_ip, requested_file_id)
        media_server.process_file_request(request_message, server_ip)
        # I assume request rate is Poisson Distribution so the time intervals are exponential distributions
        time_until_next_request = np.random.exponential(scale_of_exponential)
        sleep(time_until_next_request)


if __name__ == '__main__':
    # Run the server
    debug("Server is starting")
    server_ip = sys.argv[1]
    debug("server_ip " + server_ip)
    media_server = MediaServer()
    media_server.get_caching_statistics()
    debug("Server is awake")
    signal.signal(signal.SIGINT, terminate_handler)
    switch_mobility_thread = threading.Thread(target=move_switches)
    switch_mobility_thread.setDaemon(True)
    switch_mobility_thread.start()
    auto_request_file(REQUEST_INTERVAL, NUMBER_OF_HOSTS, ALPHA_ZIPF, NUMBER_OF_FILES)
