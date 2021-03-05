import controller_utils

from ap_name_converter import AccessPointNameConverter
from drone_movement import DroneMover


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

    def update_device_coordinates_on_controller(self):
        current_info = controller_utils.get_network_configurations()
        if "devices" in current_info:
            drone_positions = self.drone_mover.get_drone_positions()
            for device_name, device_properties in current_info["devices"].items():
                device_id = self.ap_name_converter.get_id_by_of_name(device_name)
                current_info["devices"][device_name]["basic"] = {
                    "latitude": drone_positions[device_id][0],
                    "longitude": drone_positions[device_id][1],
                }

        controller_utils.post_network_configurations(current_info)
        return current_info


if __name__ == '__main__':
    drone_operator = DroneOperator()
    # drone_operator.get_drone_overheads()
    drone_operator.update_device_coordinates_on_controller()
