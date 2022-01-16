import bisect
import logging
import random

import settings as s
from actors.TrafficObserver import TrafficObserver


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


def get_station_bw(given_time, sta):
    sta_associated_ap_traffic_load = TrafficObserver.get_traffic_on_ap_interface(given_time,
                                                                                 sta.wintfs[0].associatedTo)
    rssi_sta = sta.wintfs[0].rssi
    sta_data_rate = get_link_speed_by_rssi(rssi_sta) / (sta_associated_ap_traffic_load + 1)
    logging.info(f"{sta.name} data_rate={sta_data_rate} (AP shared by {sta_associated_ap_traffic_load + 1})")
    return sta_data_rate


def get_cloud_bw():
    cloud_traffic_load = TrafficObserver.get_traffic_on_cloud_interface()
    rssi_cloud = s.AP_AP_RSSI
    cloud_data_rate = get_link_speed_by_rssi(rssi_cloud) / (cloud_traffic_load + 1)
    logging.info(f"Cloud data_rate={cloud_data_rate} (AP shared by {cloud_traffic_load + 1})")
    return cloud_data_rate


def get_estimated_tx_time_between_stations(given_time, sta1, sta2, task):
    sta1_data_rate = get_station_bw(given_time, sta1)
    sta2_data_rate = get_station_bw(given_time, sta2)
    estimated_tx_time = task.size / min(sta1_data_rate, sta2_data_rate)
    logging.info(f"Estimated task #{task.no} tx time: {estimated_tx_time}")
    return estimated_tx_time


def get_estimated_tx_time_station_to_cloud(given_time, task):
    sta = task.owner.station
    sta_data_rate = get_station_bw(given_time, sta)
    estimated_tx_time = task.size / min(sta_data_rate, get_cloud_bw())
    logging.info(f"Estimated task #{task.no} tx to cloud time: {estimated_tx_time}")
    return estimated_tx_time
