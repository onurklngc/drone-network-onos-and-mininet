import logging
import os
import random
import sys

import webcolors

import settings as s

if 'SUMO_HOME' not in os.environ:
    logging.warn("SUMO_HOME not in env, trying to add!")
    os.environ["SUMO_HOME"] = "/usr/share/sumo"

tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

import traci


class Vehicle(object):
    sumo_id = None
    speed = None
    position = None
    angle = None
    type = None

    def __init__(self, name, speed=None, location=None, angle=None, vehicle_type=None):
        self.sumo_id = name
        self.speed = speed
        self.position = location
        self.angle = angle
        self.type = vehicle_type

    def __repr__(self):
        return "{{\"sumo_id\":{}, \"speed\":{}, \"position\":{}, \"angle\":{}, \"type\":{}}}".format(self.sumo_id,
                                                                                                     self.speed,
                                                                                                     self.position,
                                                                                                     self.angle,
                                                                                                     self.type)


def get_vehicle_data(code):
    return s.VEHICLE_TYPE_PROPERTIES.get(code)


def select_vehicle_class():
    lucky_category_symbol = random.choice(s.VEHICLE_CATEGORY_DISTRIBUTION)
    return get_vehicle_data(lucky_category_symbol)


def remove_vehicle_prefix(name):
    if name.startswith(s.VEHICLE_PREFIX):
        return name[len(s.VEHICLE_PREFIX):]
    return name


class SumoManager(object):
    vehicles_being_served = []

    def __init__(self):
        logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
        sumo_cmd = [s.SUMO_BINARY, "-c", s.SUMO_CFG_PATH, "-d", str(s.SIMULATION_DELAY), "--time-to-teleport", "-1"]
        if s.START_SIMULATION_DIRECTLY:
            sumo_cmd.append("-S")
        traci.start(sumo_cmd)
        logging.info("Sumo Manager is initialized.")

    def __del__(self):
        traci.close()
        logging.info("Sumo Manager is destroyed.")

    def prepare_car(self, vehicle_id):
        if len(self.vehicles_being_served) < s.NUM_OF_CARS:
            new_vehicle_class = select_vehicle_class()
        else:
            logging.warn("Skipped car selection due to overload, assigning private")
            new_vehicle_class = get_vehicle_data("P")
        traci.vehicle.setVehicleClass(vehicle_id, new_vehicle_class["type"])
        traci.vehicle.setShapeClass(vehicle_id, new_vehicle_class["shape"])
        color_tuple = webcolors.name_to_rgb(new_vehicle_class["color"]) + (255,)
        traci.vehicle.setColor(vehicle_id, color_tuple)
        if new_vehicle_class["type"] != "private":
            self.vehicles_being_served.append(vehicle_id)
            traci.gui.toggleSelection(vehicle_id)
            if s.HIGHLIGHT_CARS:
                traci.vehicle.highlight(vehicle_id, size=40, color=color_tuple, type=255)

    def get_vehicle_data(self):
        vehicle_data_list = []
        id_list = traci.vehicle.getIDList()
        vehicles_just_left_area = self.get_vehicles_just_left_area(id_list)
        for vehicle_id in vehicles_just_left_area:
            self.remove_vehicles_from_being_served(vehicle_id)
        for vehicle_id in id_list:
            vehicle_class = traci.vehicle.getVehicleClass(vehicle_id)
            if vehicle_class == s.DEFAULT_VEHICLE_CLASS:
                self.prepare_car(vehicle_id)
            if vehicle_id in self.vehicles_being_served:
                vehicle_speed = traci.vehicle.getSpeed(vehicle_id)
                vehicle_position = traci.vehicle.getPosition3D(vehicle_id)
                vehicle_angle = traci.vehicle.getAngle(vehicle_id)
                logging.debug("Vehicle %s(%s) is at %s", vehicle_id, vehicle_class, vehicle_position)
                vehicle_data_list.append(Vehicle(vehicle_id, vehicle_speed, vehicle_position,
                                                 vehicle_angle, vehicle_class))
            else:
                logging.debug("Skipping vehicle %s(%s)", vehicle_id, vehicle_class)
        return vehicle_data_list, vehicles_just_left_area

    def remove_vehicles_from_being_served(self, vehicle_id):
        self.vehicles_being_served.remove(vehicle_id)

    def get_vehicles_just_left_area(self, id_list_of_vehicles_on_area):
        vehicles_just_left_area = []
        for vehicle_sumo_id in self.vehicles_being_served:
            if vehicle_sumo_id not in id_list_of_vehicles_on_area:
                vehicles_just_left_area.append(vehicle_sumo_id)
        return vehicles_just_left_area

    @staticmethod
    def wait_simulation_step():
        traci.simulationStep()

    @staticmethod
    def add_uav(uav_id, x, y):
        traci.poi.add(uav_id, x, y, (255, 255, 255, 255), width=10, height=10,
                      imgFile="/home/onur/Pictures/a.png", poiType="uav", layer=5)
        traci.poi.setParameter(uav_id, "mn-data", uav_id)
        traci.gui.toggleSelection(uav_id, objType="poi")

    @staticmethod
    def set_uav_location(uav_id, x, y):
        traci.poi.setPosition(uav_id, x, y)

    @staticmethod
    def get_geo_location(x, y):
        return traci.simulation.convertGeo(x, y)

    @staticmethod
    def set_assigned_mn_object_name_vehicle(vehicle_id, mn_data):
        traci.vehicle.setParameter(vehicle_id, "mn-data", mn_data)

    @staticmethod
    def set_assigned_mn_object_name_poi(poi_id, mn_data):
        traci.poi.setParameter(poi_id, "mn-data", mn_data)

    @staticmethod
    def get_time():
        return traci.simulation.getTime()


if __name__ == '__main__':
    manager = SumoManager()
    for step in range(s.NUM_OF_SIMULATION_STEPS):
        SumoManager.wait_simulation_step()
        logging.debug("Step %s", step)
        logging.info(manager.get_vehicle_data())
    del manager
