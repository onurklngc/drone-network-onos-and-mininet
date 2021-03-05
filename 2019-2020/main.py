#!/usr/bin/sudo python

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.log import setLogLevel
from mininet.node import OVSKernelSwitch, RemoteController, CPULimitedHost
from mininet.cli import CLI
from mininet.link import TCLink
import os
import threading
import numpy as np
from random import randint, choice
from time import sleep

from intent_manager import IntentManager
from link_manager import LinkManager
from settings import *
import subprocess
import socket
import re
from switch_movement import SwitchMover
from media_server import MediaServer
from energy_management import BatteryCapacityLogger
from switch_operations import SwitchOperator
import traceback
import time
import json
import shutil
import pickle
from process_cleaner import stop_children_processes

switch_mover = None
media_server = None
media_server_info = {}
drone_battery_manager = None
link_manager = None
intent_manager = None
processes = []
link_options_host2switch = dict(bw=54 / DATA_SCALING, delay='100us', loss=0.01, max_queue_size=1000, use_htb=True)
link_options_switch2switch = dict(bw=100 / DATA_SCALING, delay='100us', loss=0.01, max_queue_size=1000, use_htb=True)
# linkOptionsMediaServer2Switch = dict(bw=100, delay='0ms', loss=0.01, max_queue_size=100000, use_htb=True)
link_options_switch_dummy_host2switch = dict(bw=1000 / DATA_SCALING, delay='0', loss=0, max_queue_size=1000,
                                             use_htb=True)
listen_host_availability_thread = None
request_file_thread = None
switch_mobility_thread = None
busy_hosts = []
switch_name_id_table = {}
switch_id_name_table = {}
links_h2s = []
links_s2s = {}
current_links = []
current_time = 0
requests_from_depleted_drones = 0
simulation_id = str(int(time.time() // 10))

simulation_snapshot = {"settings": {}}

with open('settings.py', 'r') as f:
    exec (f.read(), simulation_snapshot["settings"])
if '__builtins__' in simulation_snapshot["settings"]:
    del simulation_snapshot["settings"]['__builtins__']


def debug(msg):
    if PRINT_DUMMY_MESSAGES:
        print(msg)


def print_link_changes(message):
    if PRINT_LINK_CHANGES:
        print(message)


class InbandController(RemoteController):

    def checkListening(self):
        if self.port is None:
            self.port = 6633
        return


class DroneTopology(Topo):
    def build(self, s=NUMBER_OF_SWITCHES, n=NUMBER_OF_HOSTS_PER_SWITCH):
        global switch_name_id_table
        switches = []
        host_number = 1
        for sw in range(s):
            new_switch = self.addSwitch('s%d' % (sw + 1))
            cache_host_in_switch = self.addHost('hs%d' % (sw + 1),
                                                mac='00:00:00:00:%s:00' % hex(sw + 1).split('x')[-1].zfill(2),
                                                ip='10.0.%d.1/16' % (sw + 1),
                                                cpu=.5 / (s * n)
                                                )
            self.addLink(cache_host_in_switch, new_switch, **link_options_switch_dummy_host2switch)
            switch_name_id_table['s%d' % (sw + 1)] = sw
            switch_id_name_table[sw] = 's%d' % (sw + 1)
            for h in range(n):
                host = self.addHost('h%d' % host_number,
                                    cpu=.30 / (s * n),
                                    mac='00:00:00:00:00:' + hex(host_number).split('x')[-1].zfill(2))
                host_number += 1
                self.addLink(host, new_switch, bw=switch_mover.switch2host_link_capacities[sw] / DATA_SCALING,
                             delay='0',
                             loss=0,
                             max_queue_size=10000, use_htb=True)
            switches.append(new_switch)

        for link in switch_mover.active_link_pair_capacity_table:
            # pair = "{}-{}".format(switch_id_name_table[link[0]], switch_id_name_table[link[1]])
            self.addLink(switch_id_name_table[link[0]], switch_id_name_table[link[1]], bw=100 / DATA_SCALING,
                         delay='0ms',
                         loss=0,
                         max_queue_size=10000, use_htb=True)
        # serverNode = self.addHost('msrv', mac='00:00:00:00:00:FF', ip='10.0.200.200/8')
        # self.addLink(serverNode, switch_id_name_table[switch_mover.content_server_switch_id],
        # **linkOptionsMediaServer2Switch)


def wait_exponentially(scale_of_exponential):
    time_until_next_request = np.random.exponential(scale_of_exponential)
    sleep(time_until_next_request)


def request_file(scale_of_exponential=REQUEST_INTERVAL, host_number=NUMBER_OF_HOSTS, alpha_zipf_exponent=1.1,
                 number_of_files=NUMBER_OF_FILES):
    global requests_from_depleted_drones
    s = np.random.zipf(alpha_zipf_exponent, number_of_files * 10)
    random_file_selection_list = s[s < number_of_files + 1] - 1
    t = threading.currentThread()
    flow_id = 0
    while getattr(t, "is_running", True):
        # start = time.time()
        requesting_host_id = randint(1, host_number)
        if requesting_host_id - 1 in drone_battery_manager.depleted_battery_ids:
            requests_from_depleted_drones += 1
            wait_exponentially(scale_of_exponential)
            continue
        requested_file_id = str(choice(random_file_selection_list))
        # File request protocol message: requesting_host_ip;requested_file_id

        try:
            host = net.get("h%d" % requesting_host_id)
            host_ip = host.IP()

            if DISABLE_MULTIPLE_REQUESTS_FROM_SAME_HOST and host_ip in busy_hosts:
                debug("h%d already requested a file" % requesting_host_id)
                continue
            else:
                debug("%d: h%s requests file %s" % (flow_id, requesting_host_id, requested_file_id))
            if DISABLE_MULTIPLE_REQUESTS_FROM_SAME_HOST and GENERATE_TRAFFIC:
                busy_hosts.append(host_ip)
            request_message = "{};{}".format(host_ip, requested_file_id)
            media_source_node_ip, redirect_message = media_server.process_file_request(request_message,
                                                                                       media_server_info["ip"])
            if media_source_node_ip in [SOURCE_OWN_CACHE, SOURCE_NOT_AVAILABLE]:
                if DISABLE_MULTIPLE_REQUESTS_FROM_SAME_HOST:
                    busy_hosts.remove(host_ip)
                wait_exponentially(scale_of_exponential)
                continue
            # debug(request_message)

            # host.cmd("echo '{};{}' | nc {} {} -w 0.5 &> /dev/null &".format(redirect_message, flow_id,
            # media_source_node_ip, str(FILE_REQUEST_LISTEN_PORT)))
            if ONOS_INTENT_ADD_MODE:
                intent_manager.create_host_2_host_intent(host_ip, media_source_node_ip)
            host.cmd("echo '{};{}' >/dev/tcp/{}/{} &".format(redirect_message, flow_id, media_source_node_ip,
                                                             str(FILE_REQUEST_LISTEN_PORT)))

            flow_id += 1
            # debug(result)
            # I assume request rate is Poisson Distribution so the time intervals are exponential distributions
            # end = time.time()
            # print(end - start)
            wait_exponentially(scale_of_exponential)
        except Exception as e:
            print(traceback.format_exc())
            print(e)
            print(media_server_info)


# def moveHosts(host_number=NUMBER_OF_HOSTS, switch_number=NUMBER_OF_SWITCHES, interval=MOVE_EVENT_INTERVALS):
#     while True:
#         try:
#             movingHostID = randint(1, host_number)
#             newSwitchID = randint(1, switch_number)
#             host = net.get("h%d" % movingHostID)
#             switch = net.get("s%d" % newSwitchID)
#             host.deleteIntfs()
#             print ("Host %d hand over to %d " % (movingHostID, newSwitchID))
#             sleep(interval / 2)
#             net.addLink(host, switch, **link_options_host2switch)
#             sleep(interval / 2)
#         except Exception as e:
#             print(traceback.format_exc())
#             print (e)


def update_links_h2s():
    for switchID, new_link_capacity in enumerate(switch_mover.switch2host_link_capacities):
        previous_link_capacity = links_h2s[switchID][1]
        if previous_link_capacity != new_link_capacity:
            interface = links_h2s[switchID][0]
            interface.config(bw=new_link_capacity / DATA_SCALING, smooth_change=True)
            links_h2s[switchID][1] = new_link_capacity
            print_link_changes(
                "H2S {} capacity has changed from {} to {}".format(switchID, previous_link_capacity, new_link_capacity))


def update_links_s2s():
    new_link_capacities_s2s = {}
    new_links = []
    for link in switch_mover.active_link_pair_capacity_table:
        sw1 = switch_id_name_table[link[0]]
        sw2 = switch_id_name_table[link[1]]
        new_capacity = link[2]
        pair = "{}-{}".format(sw1, sw2)
        if sw1 == sw2:
            print("Link to itself: %s" % sw1)
            print("Operating switches:")
            print(switch_mover.operating_switches)
            print("Neighbors:")
            print(switch_mover.neighbors)
            print("Active link table:")
            print(switch_mover.active_link_pair_capacity_table)
            continue
        new_link_capacities_s2s[pair] = new_capacity
        new_links.append(pair)
        # Check link exists
        if pair in links_s2s:
            if not links_s2s[pair][3]:
                # Link was down, make link up
                interface1 = links_s2s[pair][1][0]
                interface2 = links_s2s[pair][1][1]
                if links_s2s[pair][2] != new_capacity:
                    # Apply the new bw
                    interface1.config(bw=new_capacity / DATA_SCALING, smooth_change=True)
                    print_link_changes(
                        "{} capacity has changed from {} to {}".format(pair, links_s2s[pair][2], new_capacity))
                net.get(sw1).attach(interface1)
                print_link_changes("{} is up".format(pair))
                if ONOS_LINK_ADD_MODE:
                    link_manager.send_two_way_link_to_controller(interface1.sumo_id, interface2.sumo_id)
        else:
            # Create the link
            try:
                net.addLink(sw1, sw2, bw=100 / DATA_SCALING)
            except Exception as e:
                print(traceback.format_exc())
                print (e)

            interfaces = net.get(sw1).connectionsTo(net.get(sw2))[0]
            interface1 = interfaces[0]
            interface2 = interfaces[1]
            net.get(sw1).attach(interface1)
            net.get(sw2).attach(interface2)
            links_s2s[pair] = [sw1, interfaces, new_capacity, True]
            print_link_changes("{} is created.".format(pair))
            if ONOS_LINK_ADD_MODE:
                link_manager.send_two_way_link_to_controller(interface1.sumo_id, interface2.sumo_id)

    for previously_active_link in current_links:
        # From the previous time slot, check the link changes one by one
        if previously_active_link in new_link_capacities_s2s:
            # Link continues to operate
            previous_capacity = links_s2s[previously_active_link][2]
            new_capacity = new_link_capacities_s2s[previously_active_link]
            if previous_capacity != new_capacity:
                # Link capacity has changed.
                interface1 = links_s2s[previously_active_link][1][0]
                interface1.config(bw=new_capacity / DATA_SCALING, smooth_change=True)
                print_link_changes(
                    "{} capacity has changed from {} to {}".format(previously_active_link, previous_capacity,
                                                                   new_capacity))
            else:
                print_link_changes("{}-> Alles gut.".format(previously_active_link))
        else:
            # Link is down
            links_s2s[previously_active_link][3] = False
            interfaces = links_s2s[previously_active_link][1]
            interface1 = interfaces[0]
            interface2 = interfaces[1]
            if ONOS_LINK_ADD_MODE:
                link_manager.delete_two_way_link_from_controller(interface1.sumo_id, interface2.sumo_id)
            net.get(links_s2s[previously_active_link][0]).detach(interface1)
            print_link_changes("{} is down".format(previously_active_link))

    # Save the new link pairs
    current_links[:] = new_links


def update_links():
    update_links_h2s()
    update_links_s2s()


def remove_depleted_switches(depleted_batteries):
    switch_mover.number_of_switches_alive -= len(depleted_batteries)
    switch_mover.operating_switches = np.setdiff1d(switch_mover.operating_switches, depleted_batteries)
    for switch in depleted_batteries:
        net.get(switch_id_name_table[switch]).stop()
    if switch_mover.number_of_switches_alive <= 0:
        terminate_simulation()
        return
    if switch_mover.content_server_switch_id in depleted_batteries:
        print("Content server switch is depleted")
        global media_server_info
        switch_mover.get_central_node()
        media_server_dummy_host_name = "h" + switch_id_name_table[switch_mover.content_server_switch_id]
        media_server_info = {"node": net.get(media_server_dummy_host_name),
                             "ip": net.get(media_server_dummy_host_name).IP(),
                             "id": switch_mover.content_server_switch_id}


def save_simulation_snapshot_to_file(data_time, file_name=None):
    if file_name is None:
        file_name = "resultsV2/situation-%s.pkl" % simulation_id
    simulation_snapshot[data_time] = {"links": switch_mover.active_link_pair_capacity_table[:],
                                      "content_server": switch_mover.content_server_switch_id,
                                      "battery_levels": np.copy(drone_battery_manager.battery_levels),
                                      "media_server_logs": media_server.get_caching_statistics(),
                                      "requests_from_depleted_drones": requests_from_depleted_drones,
                                      "caching_switches": switch_operator.caching_switches[:],
                                      "cached_switches": switch_operator.cached_switches[:],
                                      "depleted_battery_ids": np.copy(drone_battery_manager.depleted_battery_ids),
                                      "energy_consumption_statistics": np.copy(
                                          drone_battery_manager.energy_consumption_statistics),
                                      "energy_cost_matrix": media_server.energy_cost_matrix[:],
                                      "flow_hop_matrix": media_server.flow_hop_matrix[:],
                                      }
    with open(file_name, 'wb+') as handle:
        pickle.dump(simulation_snapshot, handle, protocol=pickle.HIGHEST_PROTOCOL)


def move_switches(interval=MOVE_EVENT_INTERVALS):
    global current_time
    t = threading.currentThread()
    print("Time is %d." % (current_time / 60))
    # try:
    #     os.remove("batteryLevelsSpecific.csv")
    # except:
    #     traceback
    # drone_battery_manager.printProportionalBatteryLevelsToFile("batteryLevelsSpecific.csv", (current_time / 60))
    # switch_mover.printLinksToFile("links/links_%d" % (current_time / 60))
    save_simulation_snapshot_to_file(current_time)
    while switch_mover.number_of_switches_alive and getattr(t, "is_running", True):
        sleep(interval)
        current_time += interval
        drone_battery_manager.decrease_battery_fly()
        switch_operator.get_switch_overheads()
        depleted_batteries = drone_battery_manager.check_for_depleted_batteries()
        if depleted_batteries:
            remove_depleted_switches(depleted_batteries)
        switch_mover.move_switches_for_one_time_interval(current_time)
        switch_operator.update_device_coordinates_on_controller()
        update_links()
        if current_time % 60 == 0:
            "Caching host placement time"
            switch_operator.select_caching_nodes()
            # switch_mover.printLinksToFile("links/links_%d" % (current_time / 60))
            # drone_battery_manager.printProportionalBatteryLevelsToFile("batteryLevelsSpecific.csv",(current_time/60))
            # drone_battery_manager.printEnergyConsumptionStatisticsToFile(current_time / 60)
            save_simulation_snapshot_to_file(current_time)
            print(drone_battery_manager.battery_levels)
            print("Time is %d." % (current_time / 60))


def get_host_availability(accepted_socket):
    message = accepted_socket.recv(1024).decode()
    accepted_socket.close()
    print(message)
    if ONOS_INTENT_ADD_MODE:
        message_parsed = message.split(";", 3)
        src_ip = message_parsed[0]
        dst_ip = message_parsed[1]
        intent_manager.delete_host_2_host_intent(src_ip, dst_ip)
    if DISABLE_MULTIPLE_REQUESTS_FROM_SAME_HOST:

        try:
            busy_hosts.remove(dst_ip)
        except Exception as e:
            print(traceback.format_exc())
            print (e)


def listen_host_availability():
    t = threading.currentThread()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((MININET_IP, HOST_AVAILABILITY_LISTEN_PORT))
    s.listen(5)
    while getattr(t, "is_running", True):
        # print("...ABC...")
        accepted_socket, address = s.accept()
        try:
            if not getattr(t, "is_running", True):
                return
            get_host_availability(accepted_socket)
        except Exception as e:
            print(traceback.format_exc())
            print(e)


def get_initial_link_objects():
    global media_server_info
    print(switch_mover.active_link_pair_capacity_table)
    media_server_dummy_host_name = "h" + switch_id_name_table[switch_mover.content_server_switch_id]
    media_server_info = {"node": net.get(media_server_dummy_host_name),
                         "ip": net.get(media_server_dummy_host_name).IP(),
                         "id": switch_mover.content_server_switch_id}
    drone_battery_manager.add_extra_battery(switch_mover.content_server_switch_id)
    for switchID, linkCapacity in enumerate(switch_mover.switch2host_link_capacities):
        switch_name = switch_id_name_table[switchID]
        interface = net.get(switch_name).intf()
        links_h2s.append([interface, linkCapacity])
    for link in switch_mover.active_link_pair_capacity_table:
        sw1 = switch_id_name_table[link[0]]
        sw2 = switch_id_name_table[link[1]]
        capacity = link[2]
        interfaces = net.get(sw1).connectionsTo(net.get(sw2))[0]
        interface1 = interfaces[0]
        interface2 = interfaces[1]
        # Initialize link with high value then set one side real value which is bottleneck for the whole link
        interface1.config(bw=capacity / DATA_SCALING, smooth_change=True)
        pair = "{}-{}".format(sw1, sw2)
        links_s2s[pair] = [sw1, interfaces, capacity, True]
        current_links.append(pair)
        if ONOS_LINK_ADD_MODE:
            link_manager.send_two_way_link_to_controller(interface1.sumo_id, interface2.sumo_id)


def initialize_network():
    # Tell mininet to print information
    setLogLevel(MININET_LOG_LEVEL)
    "Create drone network"
    topology = DroneTopology()
    mininet_network = Mininet(topo=topology, controller=RemoteController('main_controller', ip='127.0.0.1', port=6653),
                              switch=OVSKernelSwitch, host=CPULimitedHost, link=TCLink)
    return mininet_network


def start_network():
    global request_file_thread, listen_host_availability_thread, switch_mobility_thread
    # c1 = network.addController('c0', controller=RemoteController, ip=CONTROLLER_IP)
    # Add internet connection
    net.addNAT().configDefault()
    net.start()

    listen_host_availability_thread = threading.Thread(target=listen_host_availability)
    listen_host_availability_thread.setDaemon(True)
    listen_host_availability_thread.start()

    # CLI(net)
    get_initial_link_objects()
    CLI(net)
    # mediaServerIP = network.get("msrv").IP()
    # debug("mediaServerIP %s" % mediaServerIP)
    for h in net.hosts:
        h.popen("ping -c 1 10.0.0.1")
        if re.match(r"h[0-9]+", h.sumo_id):
            # itg_rec_signal_port = int(h.sumo_id[1:]) + 9000
            # processes.append(h.popen('ITGRecv -Sp %d -a %s' % (itg_rec_signal_port, h.IP())))
            if GENERATE_TRAFFIC:
                processes.append(h.popen('python streamer_host.py %s %s' % (h.IP(), simulation_id)))
        elif re.match(r"hs[0-9]+", h.sumo_id):
            if GENERATE_TRAFFIC:
                processes.append(h.popen('python streamer_host.py %s %s' % (h.IP(), simulation_id)))
    CLI(net)
    # hostMobilityThread = threading.Thread(target=moveHosts, kwargs={"host_number": NUMBER_OF_HOSTS,
    #                                                                 "switch_number": NUMBER_OF_SWITCHES,
    #                                                                 "interval": MOVE_EVENT_INTERVALS})
    # hostMobilityThread.setDaemon(True)
    # hostMobilityThread.start()
    switch_mobility_thread = threading.Thread(target=move_switches)
    switch_mobility_thread.setDaemon(True)
    switch_mobility_thread.start()

    request_file_thread = threading.Thread(target=request_file,
                                           kwargs={"scale_of_exponential": REQUEST_INTERVAL,
                                                   "host_number": NUMBER_OF_HOSTS,
                                                   "alpha_zipf_exponent": ALPHA_ZIPF,
                                                   "number_of_files": NUMBER_OF_FILES})
    request_file_thread.setDaemon(True)
    request_file_thread.start()

    debug(links_s2s)
    debug(links_h2s)


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def terminate_simulation():
    print("We are done!!")
    save_simulation_snapshot_to_file(current_time)
    report = media_server.get_caching_statistics()
    report["requests_from_depleted_drones"] = requests_from_depleted_drones
    report["current_time"] = current_time
    print(report)
    results_path = "results/%s" % simulation_id
    result_file = os.path.join(results_path, "result.json")
    if not os.path.isfile(result_file):
        os.makedirs(results_path)
        with open(result_file, "w+") as outfile:
            json.dump(report, outfile)
        subprocess.call(['chmod', '-R', '777', 'results'])
    try:
        listen_host_availability_thread.is_running = False
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    try:
        request_file_thread.is_running = False
    except Exception as e:
        print(traceback.format_exc())
        print(e)
    try:
        switch_mobility_thread.is_running = False
    except Exception as e:
        print(traceback.format_exc())
        print(e)


if __name__ == '__main__':
    stop_children_processes(processes)

    link_manager = LinkManager()
    intent_manager = IntentManager()
    switch_mover = SwitchMover()
    drone_battery_manager = BatteryCapacityLogger()
    switch_operator = SwitchOperator(switch_mover, drone_battery_manager)
    media_server = MediaServer(switch_operator)

    net = initialize_network()
    start_network()

    CLI(net)
    terminate_simulation()

    stop_children_processes(processes)
    net.stop()
