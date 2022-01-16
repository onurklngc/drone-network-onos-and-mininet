import logging
import random

from mininet.log import info
from mininet.node import RemoteController, Controller
from mn_wifi.link import wmediumd, mesh
from mn_wifi.mobility import Mobility
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

import settings as s
from actors.Simulation import Simulation
from link_manager import LinkManager
from manage_vehicle_connections import add_to_connected_vehicles, set_vehicle_as_disconnected
from sumo_interface import add_to_unassociated_mn_stations, reverse_unassociated_mn_stations
from utils import pick_coordinate_close_to_given_location

drone_aps = {}
drone_hosts = {}
vehicle_to_mn_sta = {}
medium_id = 100
PERMITTED_5GHZ_CHANNELS = [36, 40, 44, 48, 149, 153, 157]
next_channel_index = 0


def randomly_move_drones(net):
    for ap in net.aps:
        ap_location = ap.getxyz()
        new_ap_location = (p + random.randint(-20, 20) for p in ap_location)
        ap.setPosition(",".join(format(p, "10.3f") for p in new_ap_location))


def update_drone_locations_on_mn(drone_mover):
    drone_positions = drone_mover.get_drone_positions()
    for drone_id, ap in drone_aps.items():
        ap_location = drone_positions[drone_id]
        ap.setPosition(",".join(format(p, "10.3f") for p in ap_location))


def update_station_locations_on_mn(vehicle_data_list):
    for sumo_vehicle in vehicle_data_list:
        vehicle_sumo_id = sumo_vehicle.sumo_id
        vehicle_position_xyz = sumo_vehicle.position
        mn_sta = vehicle_to_mn_sta[vehicle_sumo_id]
        mn_sta.setPosition(",".join(format(p, "10.3f") for p in vehicle_position_xyz))
        # sta_ap_distance = mn_sta.get_distance_to(mn_sta.wintfs[0].associatedTo.node)
        # if mn_sta.wintfs[0].associatedTo and s.AP_GROUND_RANGE < sta_ap_distance:
        #     mn_sta.wintfs[0].disconnect_pexec(mn_sta.wintfs[0].associatedTo)
        #     logging.error("Disconnecting station from AP since they are %d meter far away." % sta_ap_distance)
        # mn_car.update_2d() # Mathplotlib is bugged.


def add_ap_ap_links(net, drone_ap_by_id, drone_mover, link_manager):
    global medium_id, next_channel_index
    mesh_links = {}
    drone_mover.select_links()
    neighbors = drone_mover.get_neighbors()
    for drone_id, drone_neighbors in neighbors.items():
        for neighbor_index, neighbor_id in enumerate(drone_neighbors):
            id_ordering = (neighbor_id + 1, drone_id + 1) if drone_id > neighbor_id else (drone_id + 1, neighbor_id + 1)
            mesh_name = "ap%d-ap%d" % id_ordering
            intf_name = 'ap%d-wlan%d' % (drone_id + 1, neighbor_index + 2)
            next_channel_index = (drone_id + neighbor_id) % len(PERMITTED_5GHZ_CHANNELS)
            net.addLink(drone_ap_by_id[drone_id], intf=intf_name, cls=mesh,
                        ssid=mesh_name, mode="ac", channel=PERMITTED_5GHZ_CHANNELS[next_channel_index],
                        txpower=s.DRONE_AP_TX_POWER)
            logging.info("Adding %s for %s" % (mesh_name, intf_name))
            if id_ordering in mesh_links:
                mesh_links[id_ordering].append(intf_name.replace("-wlan", "-mp"))
            else:
                mesh_links[id_ordering] = [intf_name.replace("-wlan", "-mp")]

    for mesh_link_pair in mesh_links.values():
        link_manager.send_two_way_link_to_controller(*mesh_link_pair)
        for interface in mesh_link_pair:
            net.getNodeByName(interface.split("-")[0]).setMediumId(medium_id, intf=interface)
        medium_id += 1


def configure_tx_powers(new_net, drone_ap_by_id):
    for drone_ap in drone_ap_by_id.values():
        drone_ap.setTxPower(s.DRONE_AP_TX_POWER, intf='%s-wlan1' % drone_ap.name)
    for station in new_net.stations:
        station.setTxPower(s.VEHICLE_TX_POWER)


def add_bs(net, bs_location, bs_id=s.BS_ID_OFFSET):
    bs = net.addAccessPoint('%s%d' % (s.BS_NAME_PREFIX, bs_id), wlans=2, ssid='ssid-bs',
                            mode="g", channel=11, protocols='OpenFlow13', antennaGain=s.ANTENNA_GAIN,
                            position="{},{},{}".format(*bs_location, s.BS_HEIGHT))
    Simulation.bs_host = net.addHost('bs%d' % bs_id, mac='FF:00:00:00:00:00')
    net.bs_map[bs_id] = bs
    return bs, Simulation.bs_host


def add_bs_links(net, bs, bs_host, ap, link_manager):
    global medium_id
    net.addLink(bs, intf='%s-wlan2' % bs.name, cls=mesh, ssid='mesh-bs',
                mode="ac", channel=PERMITTED_5GHZ_CHANNELS[next_channel_index], txpower=s.BS_MESH_TX_POWER)
    net.addLink(ap, intf='%s-wlan5' % ap.name, cls=mesh, ssid='mesh-bs', mode="ac",
                channel=PERMITTED_5GHZ_CHANNELS[next_channel_index],
                txpower=s.DRONE_AP_TX_POWER)
    net.addLink(bs_host, bs, bw=100, delay='0ms')
    link_manager.send_two_way_link_to_controller('%s-mp5' % ap.name, '%s-mp2' % bs.name)
    bs.setAntennaGain(s.BS_GROUND_ANTENNA_GAIN, intf='%s-wlan1' % bs.name)
    bs.setTxPower(s.BS_GROUND_TX_POWER, intf='%s-wlan1' % bs.name)
    bs.setMediumId(medium_id, intf='%s-mp2' % bs.name)
    ap.setMediumId(medium_id, intf='%s-mp5' % ap.name)
    medium_id += 1


def add_controller_host_link(net, controller_host):
    ap_hosting_controller = drone_aps[s.CONTROLLER_AP_ID]
    net.addLink(controller_host, ap_hosting_controller, bw=100, delay='0ms')


def create_topology(drone_mover):
    "Create a network."
    Mobility.real_range_coefficient = s.REAL_LIFE_RANGE_COEFFICIENT
    new_net = Mininet_wifi(controller=RemoteController if s.IS_REMOTE_CONTROLLER else Controller,
                           link=wmediumd, wmediumd_mode=interference, noise_th=s.WIFI_NOISE_THRESHOLD)

    info("*** Creating nodes\n")
    if s.SELECT_RANDOM_DRONE_FOR_BS_CONNECTION:
        Simulation.drone_id_close_to_bs = random.randint(0, s.NUMBER_OF_DRONES - 1)
    else:
        Simulation.drone_id_close_to_bs = s.DRONE_ID_CLOSE_TO_BS
    drone_mover.set_root_node_id(Simulation.drone_id_close_to_bs)
    drone_position_close_to_bs = drone_mover.initial_drone_positions[Simulation.drone_id_close_to_bs]
    bs_location = pick_coordinate_close_to_given_location(drone_position_close_to_bs[0], drone_position_close_to_bs[1])

    for sta_id in range(s.NUMBER_OF_STATIONS):
        sta = new_net.addStation('sta%d' % (sta_id + 1), position=s.UNASSOCIATED_CAR_LOCATION,
                                 antennaGain=s.ANTENNA_GAIN,
                                 mac='00:00:00:00:00:' + hex(sta_id + 1).split('x')[-1].zfill(2))
        add_to_unassociated_mn_stations(sta)
        # sta.setPosition("%d,%d,1" % (drone_mover.initial_drone_positions[sta_id][0] - 5,
        #                              drone_mover.initial_drone_positions[sta_id][1] - 5))
        sta.is_used = False

    new_net.bs_map = {}
    bs, bs_host = add_bs(new_net, bs_location)

    for drone_id in range(s.NUMBER_OF_DRONES):
        no_of_wlans = 4 if Simulation.drone_id_close_to_bs != drone_id else 5
        ap = new_net.addAccessPoint('ap%d' % (drone_id + 1), wlans=no_of_wlans, ssid='ssid%d' % (drone_id + 1),
                                    channel=(drone_id + 1) % 11, ht_cap='HT40+', protocols='OpenFlow13',
                                    antennaGain=s.ANTENNA_GAIN,
                                    position=",".join(str(v) for v in drone_mover.initial_drone_positions[drone_id]))
        drone_aps[drone_id] = ap
        if s.ADD_DRONE_MN_HOST:
            drone_host = new_net.addHost('h%d' % (drone_id + 1), mac='00:10:00:00:00:' +
                                                                     hex(drone_id + 1).split('x')[-1].zfill(2))
            drone_hosts[drone_id] = drone_host

        if drone_id == s.CONTROLLER_AP_ID:
            Simulation.controller_host = new_net.addHost('ch%d' % (s.CONTROLLER_AP_ID + 1),
                                                         mac='03:00:00:00:00:' + hex(s.CONTROLLER_AP_ID).split(
                                                             'x')[-1].zfill(2))

    # During mn sta object to sumo vehicle association, pop method used to get next object so reverse list is taken
    reverse_unassociated_mn_stations()

    if s.IS_REMOTE_CONTROLLER:
        c0 = new_net.addController(name='c0',
                                   controller=RemoteController,
                                   ip='127.0.0.1',
                                   protocol='tcp',
                                   port=6653)
    else:
        c0 = new_net.addController(name='c0', port=6654)
    info("*** Configuring Propagation Model\n")
    new_net.setPropagationModel(model="losNlosMixture", exp=2, uav_default_height=s.AVERAGE_HEIGHT)

    logging.info("*** Configuring wifi nodes\n")
    new_net.configureWifiNodes()
    link_manager = LinkManager()
    add_bs_links(new_net, bs, bs_host, drone_aps[Simulation.drone_id_close_to_bs], link_manager)
    add_ap_ap_links(new_net, drone_aps, drone_mover, link_manager)
    add_controller_host_link(new_net, Simulation.controller_host)
    configure_tx_powers(new_net, drone_aps)

    if s.ADD_DRONE_MN_HOST:
        for drone_id, host in drone_hosts.items():
            new_net.addLink(host, drone_aps[drone_id], bw=100, delay='0ms')

    info("*** Starting network\n")
    if s.PLOT_MININET_GRAPH:
        new_net.plotGraph(max_x=2000, max_y=2000, min_x=-500, min_y=-500)
    new_net.build()
    nat_host = new_net.addNAT(linkTo=bs.name)
    nat_host.configDefault()
    Simulation.set_nat_host(nat_host)
    if s.TASK_ASSIGNER_SERVER == "NAT":
        Simulation.set_task_assigner(Simulation.nat_host)
    elif s.TASK_ASSIGNER_SERVER == "CONTROLLER_HOST":
        Simulation.set_task_assigner(Simulation.controller_host)
    elif s.TASK_ASSIGNER_SERVER == "BS_HOST":
        Simulation.set_task_assigner(Simulation.bs_host)

    c0.start()

    for ap in new_net.aps:
        ap.start([c0])

    # for station in new_net.stations:
    #     station.popen("ping %s" % Simulation.task_assigner_host_ip)

    return new_net


def check_station_connections():
    for vehicle in Simulation.connecting_vehicles.copy().values():
        sta = vehicle.station
        if sta.wintfs[0].associatedTo:
            ap_intf = sta.wintfs[0].associatedTo
            link_connection_output = sta.cmd(f"iw dev {sta.wintfs[0].name} link")
            if "Not connected" in link_connection_output:
                logging.debug(f"{sta} is not connected to {ap_intf} contrary to config. "
                              f"Shall try to connect again.")
                # sta.popen(f"iw dev {sta.wintfs[0].name} scan && "
                #           f"iw dev {sta.wintfs[0].name} connect {ap_intf.ssid} {ap_intf.mac}")
                # sta.wintfs[0].iwconfig_connect(sta.wintfs[0].associatedTo)
                sta.wintfs[0].pexec(
                    'iw dev {} connect {} {}'.format(sta.wintfs[0].name, sta.wintfs[0].associatedTo.ssid,
                                                     sta.wintfs[0].associatedTo.mac))
            else:
                logging.info(f"{sta} is finally connected to {ap_intf}")
                add_to_connected_vehicles(vehicle)
        else:
            logging.error(f"{sta} lost its network access even before connecting.")
            set_vehicle_as_disconnected(vehicle.sumo_id)
