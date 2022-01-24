import bisect
import logging
import pickle
import random

import settings as s
from actors.TrafficObserver import TrafficObserver
from actors.Vehicle import ConnectionStatus
from actors.constant import Color


def pick_random_location_for_bs(x_min=s.COORDINATE_LIMIT_X[0], x_max=s.COORDINATE_LIMIT_X[1],
                                y_min=s.COORDINATE_LIMIT_Y[0], y_max=s.COORDINATE_LIMIT_Y[1]):
    x = random.choice([x_min + 50, x_max - 50])
    y = random.randint(y_min + 50, y_max - 50)
    return x, y


def pick_coordinate_close_to_given_location(x, y):
    x = random.randint(x - 50, x + 50)
    y = random.randint(y - 50, y + 50)
    return x, y


def get_wait_time(start_time, end_time, period):
    time_passed = end_time - start_time
    logging.debug("Time spent on this step %f" % time_passed)
    time_to_wait = period - time_passed
    if time_to_wait < 0:
        logging.error("Missed deadline by %f" % -time_to_wait)
        time_to_wait = 0
    return time_to_wait


def rss_to_data_transfer_rate_in_kilobyte_per_s(rss):
    min_sensitivity = [
        (-90, 544),
        (-89, 812),
        (-88, 1000),
        (-87, 1170),
        (-84, 1540),
        (-82, 2110),
        (-78, 2920),
        (-74, 3360),
        (-72, 4360),
    ]
    satisfied_min_value = bisect.bisect_left(min_sensitivity, (rss,))
    if satisfied_min_value >= len(min_sensitivity):
        satisfied_min_value = len(min_sensitivity) - 1
    return min_sensitivity[satisfied_min_value][1]


def get_link_speed_by_rssi(rssi):
    return rss_to_data_transfer_rate_in_kilobyte_per_s(rssi - 91 - s.WIFI_NOISE_THRESHOLD)


def get_station_bw(given_time, sta, are_sharing_same_interface=0):
    sta_associated_ap_traffic_load = TrafficObserver.get_traffic_on_ap_interface(given_time,
                                                                                 sta.wintfs[0].associatedTo)
    rssi_sta = sta.wintfs[0].rssi
    sta_data_rate = get_link_speed_by_rssi(rssi_sta) / (sta_associated_ap_traffic_load + 1 + are_sharing_same_interface)
    logging.info(f"{sta.name} data_rate={sta_data_rate} ({sta.wintfs[0].associatedTo.node.name} shared by "
                 f"{sta_associated_ap_traffic_load + 1}"
                 f"+{are_sharing_same_interface})")
    return sta_data_rate


def get_cloud_bw():
    cloud_traffic_load = TrafficObserver.get_traffic_on_cloud_interface()
    # rssi_cloud = s.AP_AP_RSSI
    # cloud_data_rate = get_link_speed_by_rssi(rssi_cloud) / (cloud_traffic_load + 1)
    cloud_data_rate = 1000 / (cloud_traffic_load + 1)
    logging.info(f"Cloud data_rate={cloud_data_rate} (AP shared by {cloud_traffic_load + 1})")
    return cloud_data_rate


def get_estimated_tx_time_between_stations(given_time, sta1, sta2, task):
    src_ap_interface = sta1.wintfs[0].associatedTo
    dest_ap_interface = sta2.wintfs[0].associatedTo
    are_sharing_same_interface = 1 if src_ap_interface == dest_ap_interface else 0
    sta1_data_rate = get_station_bw(given_time, sta1, are_sharing_same_interface)
    sta2_data_rate = get_station_bw(given_time, sta2, are_sharing_same_interface)
    estimated_tx_time = task.size / min(sta1_data_rate, sta2_data_rate)
    logging.info(f"Estimated Task#{task.no} tx time: {estimated_tx_time} {sta1.name}->{sta2.name}")
    return estimated_tx_time


def get_estimated_tx_time_station_to_cloud(given_time, task):
    sta = task.owner.station
    sta_data_rate = get_station_bw(given_time, sta, 0)
    estimated_tx_time = task.size / min(sta_data_rate, get_cloud_bw())
    logging.info(f"Estimated Task#{task.no} tx time: {estimated_tx_time} {sta.name}->{Color.BLUE}Cloud{Color.ENDC}")
    return estimated_tx_time


def write_as_pickle(results, filename):
    with open(filename, 'wb') as handle:
        pickle.dump(results, handle, protocol=pickle.HIGHEST_PROTOCOL)


def read_pickle_file(filename):
    with open(filename, 'rb') as handle:
        return pickle.load(handle)


def get_settings_to_simulation_object():
    simulation_settings = {}

    with open('settings.py', 'r') as f:
        exec(f.read(), simulation_settings)
    if '__builtins__' in simulation_settings:
        del simulation_settings['__builtins__']

    return simulation_settings


def get_simulation_record(filename):
    return read_pickle_file(filename)


def get_solution(filename):
    return read_pickle_file(filename.replace("record", "solution") + "_solution")


def check_connection(role_name, vehicle):
    if vehicle.connection_status != ConnectionStatus.CONNECTED:
        logging.error(
            f"{role_name} {vehicle.sumo_id}({vehicle.station.name}) is "
            f"{vehicle.connection_status.name}. Skipping...")
        return False
    if vehicle.station.wintfs[0].associatedTo is None:
        logging.error(f"{role_name} {vehicle.sumo_id}({vehicle.station.name}) does not have "
                      f"associated AP. Skipping...")
        return False
    return True

if __name__ == '__main__':
    record = get_simulation_record(s.RECORD_FILE)
    ap_records = record.aps
