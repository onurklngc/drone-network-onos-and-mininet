import logging

import controller_utils
import settings as s
from actors.Simulation import Simulation
from ap_name_converter import AccessPointNameConverter
from drone_movement import DroneMover
from manage_vehicle_connections import set_vehicle_as_changing_network, set_vehicle_as_disconnected
from sumo_traci import convert_geo


class DroneOperator(object):
    drone_mover = None
    ap_name_converter = None
    drone_battery_manager = None
    latest_ap_metrics = {}
    latest_packet_numbers = {}

    def __init__(self, drone_mover=None, drone_battery_manager=None,
                 ap_name_converter=None):
        if drone_mover:
            self.drone_mover = drone_mover
        else:
            self.drone_mover = DroneMover()
        if drone_battery_manager:
            self.drone_battery_manager = drone_battery_manager
        if ap_name_converter:
            self.ap_name_converter = ap_name_converter
        else:
            self.ap_name_converter = AccessPointNameConverter()
        self.associated_ap = {}

    def get_ap_overheads(self):
        data = controller_utils.get_metrics()
        if "devices" not in data:
            print("Error while retrieving metrics:")
            print(data)
        for ap in data["devices"]:
            ap_id = self.ap_name_converter.get_id_by_of_name(ap["sumo_id"])
            latest_packet_number = sum(x.itervalues().next()["latest"] for x in ap["value"]["metrics"])
            if ap_id not in self.latest_packet_numbers:
                self.latest_packet_numbers[ap_id] = latest_packet_number
                continue
            previous_packet_number = self.latest_packet_numbers[ap_id]
            packet_difference = latest_packet_number - previous_packet_number
            self.drone_battery_manager.decrease_battery_process_packet(ap_id, packet_difference)
            self.latest_packet_numbers[ap_id] = latest_packet_number

    def update_device_coordinates_on_controller(self, net):
        current_info = controller_utils.get_network_configurations()
        if "devices" in current_info:
            drone_positions = self.drone_mover.get_drone_positions()
            for device_name, device_properties in current_info["devices"].items():
                device_id = self.ap_name_converter.get_id_by_of_name(device_name)
                if device_id < len(drone_positions):
                    x, y = drone_positions[device_id][:2]
                else:
                    bs = net.bs_map[device_id + 1]
                    x, y = bs.position[:2]
                if s.USE_LAT_LON:
                    y, x = convert_geo(x, y)
                current_info["devices"][device_name]["basic"] = {
                    "latitude": x,
                    "longitude": y,
                }

        controller_utils.post_network_configurations(current_info)
        return current_info

    def update_station_coordinates_on_controller(self, net):
        for station in net.stations:
            station_interface = station.wintfs[0]
            connected_ap_interface = station_interface.associatedTo
            if not station.is_used:
                if station.name in self.associated_ap and self.associated_ap[station.name]:
                    logging.info(f"{station.name} is gone, deleting host data from controller.")
                    controller_utils.delete_host_location(station_interface.mac)
                    self.associated_ap.pop(station.name)
                continue
            if not connected_ap_interface:
                logging.error(f"{station.name} is not connected to AP!")
                set_vehicle_as_disconnected(station.sumo_id)
                continue
            connected_ap = connected_ap_interface.node
            if station.name in self.associated_ap:
                if self.associated_ap[station.name] == connected_ap.name:
                    logging.debug(f"{station.name} is still connected to {connected_ap.name}")
                    continue
                else:
                    logging.info(f"{station.name} has changed AP, deleting availability.")
                    set_vehicle_as_changing_network(station.sumo_id)
                #     controller_utils.delete_host_location(station_interface.mac)

            logging.info(f"{station.name} is getting connected to {connected_ap.name}")
            ap_of_name = self.ap_name_converter.get_of_name_by_name(connected_ap.name)
            controller_utils.post_host_location(station_interface.ip, station_interface.mac, ap_of_name,
                                                friendly_name=f"{station.name}-{connected_ap.name}")
            self.associated_ap[station.name] = connected_ap.name

    def send_host_coordinates_on_controller(self, net):
        for host in net.hosts:
            if not host.intfs:
                logging.error(f"{host.name} is not connected to AP!")
                continue
            host_interface = host.intfs[0]
            ap_side_interface = host_interface.link.intf2
            connected_ap = host_interface.link.intf2.node
            logging.info(f"{host.name} is connected to {ap_side_interface.name}")
            ap_port = int(ap_side_interface.name.split("-eth")[-1])
            ap_of_name = self.ap_name_converter.get_of_name_by_name(connected_ap.name)
            controller_utils.post_host_location(host_interface.ip, host_interface.mac, ap_of_name,
                                                port=ap_port, friendly_name=f"{host.name}-{connected_ap.name}")
            self.associated_ap[host.name] = connected_ap.name
        logging.info(f"Informed the location of the following hosts: {net.hosts}")


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    drone_operator = DroneOperator()
    # drone_operator.get_drone_overheads()
    drone_operator.update_device_coordinates_on_controller(None)
