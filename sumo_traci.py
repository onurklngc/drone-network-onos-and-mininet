import logging
import os
import random
import sys
import time

import webcolors

import settings as s
from actors.SumoVehicle import SumoVehicle
from drone_movement import DroneMover
from utils import get_wait_time, pick_coordinate_close_to_given_location

if 'SUMO_HOME' not in os.environ:
    logging.warning("SUMO_HOME not in env, trying to add!")
    os.environ["SUMO_HOME"] = "/usr/share/sumo"

tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

import traci

current_step = 0


def get_vehicle_data(code):
    return s.VEHICLE_TYPE_PROPERTIES.get(code)


def select_vehicle_class(vehicle_id=None, vehicle_records=None):
    if vehicle_records:
        category_symbol = vehicle_records[vehicle_id].type_abbreviation
    else:
        category_symbol = random.choice(s.VEHICLE_CATEGORY_DISTRIBUTION)
    return get_vehicle_data(category_symbol)


def remove_vehicle_prefix(name):
    if name.startswith(s.VEHICLE_PREFIX):
        return name[len(s.VEHICLE_PREFIX):]
    return name


def convert_geo(x, y):
    return traci.simulation.convertGeo(x, y)


class SumoManager(object):
    vehicles = {}
    car_entry_time = {}
    car_duration = {}
    vehicles_being_served = []
    vehicles_not_being_served = []
    vehicle_records = None

    def __init__(self, vehicle_records=None):
        sumo_cmd = [s.SUMO_BINARY, "-c", s.SUMO_CFG_PATH, "-d", str(s.SUMO_DELAY), "--time-to-teleport", "-1"]
        if not s.USE_RANDOM_SUMO_SEED:
            sumo_cmd.extend(["--seed", str(s.SUMO_SEED_TO_USE)])

        if s.START_SIMULATION_DIRECTLY:
            sumo_cmd.append("-S")
        traci.start(sumo_cmd)

        if vehicle_records:
            self.vehicle_records = vehicle_records
        logging.info("Sumo Manager is initialized.")

    def __del__(self):
        traci.close()
        logging.info("Sumo Manager is destroyed.")

    def prepare_car(self, vehicle_id):
        if len(self.vehicles_being_served) < s.NUMBER_OF_STATIONS:
            new_vehicle_class = select_vehicle_class(vehicle_id=vehicle_id, vehicle_records=self.vehicle_records)
        else:
            logging.warning("Skipped car selection due to overload, assigning private")
            new_vehicle_class = get_vehicle_data("P")
        traci.vehicle.setVehicleClass(vehicle_id, new_vehicle_class["type"])
        traci.vehicle.setShapeClass(vehicle_id, new_vehicle_class["shape"])
        color_tuple = webcolors.name_to_rgb(new_vehicle_class["color"]) + (255,)
        traci.vehicle.setColor(vehicle_id, color_tuple)
        if new_vehicle_class["type"] != "private":
            self.vehicles_being_served.append(vehicle_id)
            self.vehicles[vehicle_id] = SumoVehicle(vehicle_id, vehicle_type=new_vehicle_class["type"],
                                                    type_abbreviation=new_vehicle_class["type_abbreviation"])
            traci.gui.toggleSelection(vehicle_id)
            if s.HIGHLIGHT_CARS:
                traci.vehicle.highlight(vehicle_id, size=400, color=color_tuple, type=255)
        else:
            self.vehicles_not_being_served.append(vehicle_id)
        return new_vehicle_class

    def get_vehicle_states(self):
        vehicle_data_list = []
        id_list = traci.vehicle.getIDList()
        vehicles_just_left_area = self.get_vehicles_just_left_area(id_list)
        for vehicle_id in vehicles_just_left_area:
            self.remove_vehicles_from_being_served(vehicle_id)
        for vehicle_id in id_list:
            if vehicle_id in self.vehicles_not_being_served:
                logging.debug("Skipping vehicle %s", vehicle_id)
                continue
            elif vehicle_id in self.vehicles_being_served:
                vehicle = self.vehicles[vehicle_id]
                position = traci.vehicle.getPosition3D(vehicle_id)
                current_route_index = traci.vehicle.getRouteIndex(vehicle_id)
                vehicle.update_location(position, current_route_index)
                # vehicle.speed = traci.vehicle.getSpeed(vehicle_id)
                # vehicle.angle = traci.vehicle.getAngle(vehicle_id)

                logging.debug("Vehicle %s(%s) is at %d,%d", vehicle_id, vehicle.type_abbreviation,
                              vehicle.position[0], vehicle.position[1])
                vehicle_data_list.append(vehicle)
            else:
                self.prepare_car(vehicle_id)
                self.car_entry_time[vehicle_id] = current_step
        return vehicle_data_list, vehicles_just_left_area

    def remove_vehicles_from_being_served(self, vehicle_id):
        self.vehicles_being_served.remove(vehicle_id)

    def get_vehicles_just_left_area(self, id_list_of_vehicles_on_area):
        vehicles_just_left_area = []
        for vehicle_sumo_id in self.vehicles_being_served:
            if vehicle_sumo_id not in id_list_of_vehicles_on_area:
                vehicles_just_left_area.append(vehicle_sumo_id)
                self.car_duration[vehicle_sumo_id] = current_step - self.car_entry_time[vehicle_sumo_id]
        return vehicles_just_left_area

    @staticmethod
    def wait_simulation_step():
        traci.simulationStep()

    @staticmethod
    def move_simulation_to_step(step):
        traci.simulationStep(step=step)

    @staticmethod
    def add_uav(uav_id, x, y, current_time=0):
        traci.poi.add(uav_id, x, y, (255, 255, 255, 255), width=2, height=2,
                      imgFile="images/drone.png", poiType="uav", layer=5)
        traci.poi.setParameter(uav_id, "mn-data", uav_id)
        traci.gui.toggleSelection(uav_id, objType="poi")
        if s.HIGHLIGHT_AP_RANGE:
            color_tuple = webcolors.name_to_rgb("yellow") + (255,)
            traci.poi.highlight(uav_id, size=s.AP_GROUND_RANGE, color=color_tuple, alphaMax=255, duration=99999,
                                type=255)

    @staticmethod
    def add_bs(bs_id, x, y):
        traci.poi.add(bs_id, x, y, (255, 255, 255, 255), width=4, height=6,
                      imgFile="images/bs.png", poiType="bs", layer=4)
        traci.poi.setParameter(bs_id, "mn-data", bs_id)
        traci.gui.toggleSelection(bs_id, objType="poi")
        if s.HIGHLIGHT_AP_RANGE:
            color_tuple = webcolors.name_to_rgb("blue") + (255,)
            traci.poi.highlight(bs_id, size=s.BS_GROUND_RANGE, color=color_tuple, alphaMax=150, duration=99999,
                                type=255)

    @staticmethod
    def set_uav_location(uav_id, x, y, current_time=0):
        traci.poi.setPosition(uav_id, x, y)
        if s.HIGHLIGHT_AP_RANGE and not current_time % 5:
            color_tuple = webcolors.name_to_rgb("yellow") + (255,)
            traci.poi.highlight(uav_id, size=s.AP_GROUND_RANGE, color=color_tuple, alphaMax=255, duration=99999,
                                type=255)

    @staticmethod
    def get_geo_location(x, y):
        return traci.simulation.convert_geo(x, y)

    @staticmethod
    def set_assigned_mn_object_name_vehicle(vehicle_id, mn_data):
        traci.vehicle.setParameter(vehicle_id, "mn-data", mn_data)

    @staticmethod
    def set_assigned_mn_object_name_poi(poi_id, mn_data):
        traci.poi.setParameter(poi_id, "mn-data", mn_data)

    @staticmethod
    def get_time():
        return int(traci.simulation.getTime())


if __name__ == '__main__':
    s.SUMO_DELAY = 100
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    manager = SumoManager()
    drone_mover = DroneMover()
    drone_id_close_to_bs = random.randint(0, s.NUMBER_OF_DRONES - 1)
    drone_mover.set_root_node_id(drone_id_close_to_bs)
    drone_position_close_to_bs = drone_mover.initial_drone_positions[drone_id_close_to_bs]
    bs_location = pick_coordinate_close_to_given_location(drone_position_close_to_bs[0], drone_position_close_to_bs[1])
    manager.add_bs("bs", *bs_location)
    for index, position in enumerate(drone_mover.initial_drone_positions):
        manager.add_uav("ap%d" % (index + 1), position[0], position[1])
    manager.move_simulation_to_step(s.SKIPPED_STEPS)
    for step in range(s.SIMULATION_DURATION - s.SKIPPED_STEPS + 1):
        step_start_time = time.time()
        current_step = step
        SumoManager.wait_simulation_step()
        logging.debug("Step %s", step)
        drone_mover.move_drones_figure8(current_step)
        for index, position in enumerate(drone_mover.drone_positions):
            manager.set_uav_location("ap%d" % (index + 1), position[0], position[1], step)
        vehicle_data = manager.get_vehicle_states()
        step_end_time = time.time()
        get_wait_time(step_start_time, step_end_time, 1)
    print(manager.car_duration)
    print(sum(manager.car_duration.values()) / len(manager.car_duration.values()))
    del manager
