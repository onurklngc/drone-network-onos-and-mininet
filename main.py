#!/usr/bin/python

"""UAVs providing network to vehicles."""
import logging
import random
import threading

from mininet.log import setLogLevel, info
from mininet.node import RemoteController, Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd, mesh
from mn_wifi.net import Mininet_wifi
from mn_wifi.wmediumdConnector import interference

import settings as s
from drone_movement import DroneMover
from drone_operator import DroneOperator
from sumo_traci import SumoManager



vehicle_to_mn_car = {}
unassociated_mn_cars = []

drone_id_to_ap = {}


def topology(drone_mover):
    "Create a network."
    new_net = Mininet_wifi(controller=RemoteController if s.IS_REMOTE_CONTROLLER else Controller,
                           link=wmediumd, wmediumd_mode=interference, mode="g", ac_method='ssf')

    info("*** Creating nodes\n")
    for car_id in range(s.NUM_OF_CARS):
        car = new_net.addStation('sta%d' % (car_id + 1), position=s.UNASSOCIATED_CAR_LOCATION,
                                 mac='00:00:00:00:00:' + hex(car_id + 1).split('x')[-1].zfill(2))
        unassociated_mn_cars.append(car)
    # During mn sta object to sumo vehicle association, pop method used to get next object so reverse list is taken
    unassociated_mn_cars.reverse()

    # for drone_id in range(s.NUM_OF_CARS):
    #     drone = new_net.addAccessPoint('drone%d' % (drone_id + 1), wlans=3,
    #                                ssid='ssid%s' % (drone_id + 1), channel=9, position='0,0,0')
    for drone_id in range(s.NUM_OF_DRONES):
        ap = new_net.addAccessPoint('ap%d' % (drone_id + 1), wlans=3, ssid='ssid%d' % (drone_id + 1), channel=9,
                                    position=",".join(str(v) for v in drone_mover.initial_drone_positions[drone_id]))
        drone_id_to_ap[drone_id] = ap

    # h1 = new_net.addHost('h%d' % 1, mac='00:10:00:00:00:' + hex(1).split('x')[-1].zfill(2))
    # h2 = new_net.addHost('h%d' % 2, mac='00:10:00:00:00:' + hex(2).split('x')[-1].zfill(2))
    # h3 = new_net.addHost('h%d' % 3, mac='00:10:00:00:00:' + hex(3).split('x')[-1].zfill(2))

    if s.IS_REMOTE_CONTROLLER:
        c0 = new_net.addController(name='c0',
                                   controller=RemoteController,
                                   ip='127.0.0.1',
                                   protocol='tcp',
                                   port=6653)
    else:
        c0 = new_net.addController(name='c0', port=6654)
    info("*** Configuring Propagation Model\n")
    new_net.setPropagationModel(model="logDistance", exp=3)

    info("*** Configuring wifi nodes\n")
    new_net.configureWifiNodes()
    for drone_id, ap in drone_id_to_ap.items():
        new_net.addLink(ap, intf='ap%d-wlan2' % (drone_id + 1), cls=mesh, ssid='mesh-ssid', channel=4, ht_cap='HT40+')

    # new_net.addLink(ap1, intf='ap1-wlan2', cls=mesh, ssid='mesh-ssid12', channel=4, ht_cap='HT40+')
    # new_net.addLink(ap2, intf='ap2-wlan2', cls=mesh, ssid='mesh-ssid12', channel=4, ht_cap='HT40+')
    # new_net.addLink(ap2, intf='ap2-wlan3', cls=mesh, ssid='mesh-ssid23', channel=4, ht_cap='HT40+')
    # new_net.addLink(ap3, intf='ap3-wlan2', cls=mesh, ssid='mesh-ssid23', channel=4, ht_cap='HT40+')
    # new_net.addLink(ap3, intf='ap3-wlan2', cls=mesh, ssid='mesh-ssid12', channel=4, ht_cap='HT40+')

    # new_net.addLink(h1, ap1, bw=100, delay='0ms')
    # new_net.addLink(h2, ap2, bw=100, delay='0ms')
    # new_net.addLink(h3, ap3, bw=100, delay='0ms')
    # for car_id, car in enumerate(new_net.cars):
    #     car.setIP('192.168.0.%s/24' % (car_id + 1), intf='%s-wlan0' % car.name)
    #     # new_net.addLink(car, ap1)

    info("*** Starting network\n")
    # new_net.plotGraph(max_x=1500, max_y=1000, min_x=0, min_y=-70)
    new_net.build()
    c0.start()
    for enb in new_net.aps:
        enb.start([c0])
    return new_net


def add_drones_as_poi_to_sumo():
    for ap in net.aps:
        ap_location = ap.getxyz()
        SumoManager.add_uav(ap.name, ap_location[0], ap_location[1])


def update_drone_locations_on_sumo():
    for ap in net.aps:
        ap_location = ap.getxyz()
        SumoManager.set_uav_location(ap.name, ap_location[0], ap_location[1])


def randomly_move_drones():
    for ap in net.aps:
        ap_location = ap.getxyz()
        new_ap_location = (p + random.randint(-20, 20) for p in ap_location)
        ap.setPosition(",".join(format(p, "10.3f") for p in new_ap_location))


def update_drone_locations_on_mn():
    drone_positions = drone_mover.get_drone_positions()
    for drone_id, ap in drone_id_to_ap.items():
        ap_location = drone_positions[drone_id]
        ap.setPosition(",".join(format(p, "10.3f") for p in ap_location))


def update_car_locations_on_mn(vehicle_data_list):
    for vehicle in vehicle_data_list:
        vehicle_sumo_id = vehicle.sumo_id
        vehicle_position_xyz = vehicle.position
        mn_car = vehicle_to_mn_car[vehicle_sumo_id]
        mn_car.setPosition(",".join(format(p, "10.3f") for p in vehicle_position_xyz))
        # mn_car.update_2d()


def update_car_locations_on_onos(mn_car, vehicle_position_xyz):
    geo_coordinates = SumoManager.get_geo_location(vehicle_position_xyz[0], vehicle_position_xyz[1])


def estimate_access_point_locations(vehicle_data_list):
    logging.debug(vehicle_data_list)


def disassociate_sumo_vehicles_leaving_area(leaving_vehicle_id_list):
    for vehicle_sumo_id in leaving_vehicle_id_list:
        car_to_be_unassociated = vehicle_to_mn_car.pop(vehicle_sumo_id, None)
        car_to_be_unassociated.setPosition(s.UNASSOCIATED_CAR_LOCATION)
        unassociated_mn_cars.append(car_to_be_unassociated)
        logging.info("Disassociating vehicle %s from mn car %s", vehicle_sumo_id, car_to_be_unassociated.name)


def associate_sumo_vehicles_with_mn_car_objects(vehicle_data_list):
    for vehicle in vehicle_data_list:
        if vehicle.sumo_id not in vehicle_to_mn_car:
            if unassociated_mn_cars:
                car_to_be_associated = unassociated_mn_cars.pop()
                vehicle_to_mn_car[vehicle.sumo_id] = car_to_be_associated
                logging.info("Associating vehicle %s with mn car %s", vehicle.sumo_id, car_to_be_associated.name)
                SumoManager.set_assigned_mn_object_name_vehicle(vehicle.sumo_id, car_to_be_associated.name)
            else:
                logging.error("No mn car object available to associate with vehicle %s", vehicle.sumo_id)


def simulate_sumo(sumo_manager):
    for step in range(s.NUM_OF_SIMULATION_STEPS):
        current_time = SumoManager.get_time()
        logging.info("Current time: %s seconds", current_time)
        drone_mover.move_drones_for_one_time_interval(current_time)
        update_drone_locations_on_mn()
        SumoManager.wait_simulation_step()
        logging.info("Step %s", step)
        served_vehicle_data_list, vehicles_just_left_area = sumo_manager.get_vehicle_data()
        disassociate_sumo_vehicles_leaving_area(vehicles_just_left_area)
        associate_sumo_vehicles_with_mn_car_objects(served_vehicle_data_list)
        estimate_access_point_locations(served_vehicle_data_list)
        update_car_locations_on_mn(served_vehicle_data_list)
        # randomly_move_drones()
        update_drone_locations_on_sumo()
        drone_operator.update_device_coordinates_on_controller()


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    setLogLevel(s.MN_WIFI_LOG_LEVEL.lower())
    drone_mover = DroneMover()
    drone_operator = DroneOperator(drone_mover)
    net = topology(drone_mover)
    manager = SumoManager()
    add_drones_as_poi_to_sumo()
    CLI(net)
    simulate_sumo(manager)
    # simulate_sumo_thread = threading.Thread(target=simulate_sumo, args=[manager])
    # simulate_sumo_thread.setDaemon(True)
    # simulate_sumo_thread.start()
    CLI(net)
    del manager
    net.stop()
