import logging
import os
import sys

if 'SUMO_HOME' not in os.environ:
    logging.warning("SUMO_HOME not in env, trying to add!")
    os.environ["SUMO_HOME"] = "/usr/share/sumo"

tools = os.path.join(os.environ["SUMO_HOME"], "tools")
sys.path.append(tools)

import traci


class SumoVehicle:
    sumo_id = None
    speed = None
    position = None
    angle = None
    type = None
    type_abbreviation = None
    route = None
    route_length = None
    current_route_index = 0
    role_object = None

    def __init__(self, name, speed=None, location=None, angle=None, vehicle_type=None, type_abbreviation=None,
                 route_length=None):
        self.sumo_id = name
        self.speed = speed
        self.position = location
        self.angle = angle
        self.type = vehicle_type
        self.type_abbreviation = type_abbreviation
        if route_length:
            self.route_length = route_length
        else:
            self.route = traci.vehicle.getRoute(name)
            self.route_length = len(self.route)
        self.current_route_index = 0

    def __repr__(self):
        return "{{\"sumo_id\":{}, \"speed\":{}, \"position\":{}," \
               " \"angle\":{}, \"type\":{}, " \
               "\"route\":{}/{}}}".format(self.sumo_id, self.speed, self.position,
                                          self.angle, self.type,
                                          self.current_route_index, self.route_length)

    def update_location(self, position, current_route_index):
        self.position = position
        self.current_route_index = current_route_index
        route_completion_ratio = current_route_index / self.route_length
        if self.role_object and route_completion_ratio > 0.85 and not self.role_object.is_leaving_soon:
            logging.info(f"{self.sumo_id} completed {100 * current_route_index / self.route_length:.0f}% of its route")
            self.role_object.is_leaving_soon = True
