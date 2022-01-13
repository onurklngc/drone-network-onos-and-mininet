import controller_utils
from sumo_traci import convert_geo


def update_car_locations_on_onos(sumo_manager, mn_car, vehicle_position_xyz):
    geo_coordinates = sumo_manager.get_geo_location(vehicle_position_xyz[0], vehicle_position_xyz[1])


def update_device_coordinates_on_onos(net):
    current_info = controller_utils.get_network_configurations()
    if "devices" in current_info:
        pass
        for device_name, device_properties in current_info["devices"].items():
            lon, lat = convert_geo(0, 0)
            current_info["devices"][device_name]["basic"] = {
                "latitude": lat,
                "longitude": lon,
            }

    controller_utils.post_network_configurations(current_info)
    return current_info
