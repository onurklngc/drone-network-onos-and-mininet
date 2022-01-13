import logging

import numpy as np
from bs4 import BeautifulSoup

import settings as s
from actors.Vehicle import VehicleMoment
from drone_movement import DroneMover

drone_id_close_to_bs = 0


def get_simulation_data():
    vehicle_based_data = {}
    time_based_data = {}
    with open(s.SUMO_SIMULATED_DATA_PATH, 'r') as f:
        file_data = f.read()

    bs_data = BeautifulSoup(file_data, "xml")
    points = bs_data.find_all('vehicle')
    for point in points:
        sumo_id = point.attrs['id']
        x = float(point.attrs['x'])
        y = float(point.attrs['y'])
        step = int(float(point.parent.attrs['time']))
        moment = VehicleMoment(sumo_id, step, x, y)
        if step not in time_based_data:
            time_based_data[step] = []
        if sumo_id not in vehicle_based_data:
            vehicle_based_data[sumo_id] = []
        time_based_data[step].append(moment)
        vehicle_based_data[sumo_id].append(moment)

    return vehicle_based_data, time_based_data


def get_closest_ap(drone_mover, x, y, z=1):
    point_location = np.array([x, y, z])
    point_to_ap_distances = np.zeros(shape=(drone_mover.number_of_drones_alive, 1))
    for i, drone_position in enumerate(drone_mover.drone_positions):
        point_to_ap_distances[i] = np.sqrt(
            np.sum((drone_position - point_location) ** 2, axis=0))

    closest_ap_index = int(np.argmin(point_to_ap_distances))
    distance = point_to_ap_distances[closest_ap_index][0]
    return closest_ap_index, distance


def get_distance(ap_location, x, y, z=1):
    point_location = np.array([x, y, z])
    return np.sqrt(np.sum((ap_location - point_location) ** 2, axis=0))


def get_associated_ap(drone_mover, v_moment, associated_ap):
    if associated_ap is not None:
        ap_location = drone_mover.drone_positions[associated_ap]
        distance = get_distance(ap_location, v_moment.x, v_moment.y)
        logging.debug(
            f"{v_moment.sumo_id}({v_moment.x},{v_moment.y}) distance to AP{associated_ap + 1}, "
            f"distance {distance:.1f} at time {v_moment.step}.")
        if distance > s.AP_GROUND_RANGE:
            v_moment.associated_ap = None
            return get_associated_ap(drone_mover, v_moment, v_moment.associated_ap)
        else:
            v_moment.associated_ap = associated_ap
    else:
        closest_ap_index, distance = get_closest_ap(drone_mover, v_moment.x, v_moment.y)
        if distance < s.AP_GROUND_RANGE - 10:
            logging.info(f"{v_moment.sumo_id}({v_moment.x},{v_moment.x}) is close to AP{closest_ap_index + 1},"
                        f" distance {distance:.1f} at time {v_moment.step}.")
            v_moment.associated_ap = closest_ap_index
        else:
            logging.info(
                f"{v_moment.sumo_id}({v_moment.x},{v_moment.x}) is not close enough to AP{closest_ap_index + 1},"
                f" distance {distance:.1f} at time {v_moment.step}.")
    return v_moment.associated_ap


def main():
    drone_mover = DroneMover()
    drone_mover.set_root_node_id(drone_id_close_to_bs)
    vehicle_data, time_data = get_simulation_data()
    for moments in vehicle_data.values():
        associated_ap = None
        for vehicle_moment in moments:
            associated_ap = get_associated_ap(drone_mover, vehicle_moment, associated_ap)
            logging.debug(vehicle_moment)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    main()
