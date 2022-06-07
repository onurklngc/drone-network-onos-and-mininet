import logging


class TrafficObserver:
    traffic_count_on_sta = {}
    cloud_load = 0
    traffic_load_on_given_time = {}

    @staticmethod
    def increment_traffic_on_sta(sta_name):
        if sta_name in TrafficObserver.traffic_count_on_sta:
            TrafficObserver.traffic_count_on_sta[sta_name] += 1
        else:
            TrafficObserver.traffic_count_on_sta[sta_name] = 1
        logging.info(f"Traffic increased on {sta_name} to {TrafficObserver.traffic_count_on_sta[sta_name]}")

    @staticmethod
    def decrement_traffic_on_sta(sta_name):
        TrafficObserver.traffic_count_on_sta[sta_name] -= 1
        logging.info(f"Traffic decreased on {sta_name} to {TrafficObserver.traffic_count_on_sta[sta_name]}")

    @staticmethod
    def reset_traffic_on_sta(sta_name):
        logging.info("Traffic reset on %s" % sta_name)
        TrafficObserver.traffic_count_on_sta[sta_name] = 0

    @staticmethod
    def increment_traffic_on_cloud():
        TrafficObserver.cloud_load += 1
        logging.info("Cloud traffic increased to %d" % TrafficObserver.cloud_load)

    @staticmethod
    def decrement_traffic_on_cloud():
        TrafficObserver.cloud_load -= 1
        logging.info("Cloud traffic decreased to %d" % TrafficObserver.cloud_load)

    @staticmethod
    def get_traffic_on_sta(sta_name):
        if sta_name not in TrafficObserver.traffic_count_on_sta:
            TrafficObserver.traffic_count_on_sta[sta_name] = 0
        return TrafficObserver.traffic_count_on_sta[sta_name]

    @staticmethod
    def get_traffic_on_ap_interface(given_time, ap_interface):
        if given_time not in TrafficObserver.traffic_load_on_given_time:
            TrafficObserver.traffic_load_on_given_time[given_time] = {}
        if ap_interface.name not in TrafficObserver.traffic_load_on_given_time[given_time]:
            ap_load = 0
            for sta_interface in ap_interface.associatedStations:
                sta_name = sta_interface.node.name
                ap_load += TrafficObserver.get_traffic_on_sta(sta_name)
            TrafficObserver.traffic_load_on_given_time[given_time][ap_interface.name] = ap_load
        return TrafficObserver.traffic_load_on_given_time[given_time][ap_interface.name]

    @staticmethod
    def get_traffic_on_cloud_interface():
        return TrafficObserver.cloud_load
