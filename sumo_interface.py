import logging

import settings as s
from actors.Record import VehicleRecord, ApMoment, ApRecord
from actors.Simulation import Simulation
from actors.Vehicle import ProcessorVehicle, TaskGeneratorVehicle
from manage_vehicle_connections import add_to_connecting_vehicles, set_vehicle_as_left

unassociated_mn_stations = []


def add_to_unassociated_mn_stations(mn_car):
    unassociated_mn_stations.append(mn_car)


def reverse_unassociated_mn_stations():
    unassociated_mn_stations.reverse()


def add_aps_as_poi_to_sumo(net, sumo_manager):
    for ap in net.aps:
        ap_location = ap.getxyz()
        if ap.name.startswith("bs"):
            bs_id = int(ap.name[len(s.AP_NAME_PREFIX):]) - s.BS_ID_OFFSET
            sumo_manager.add_bs(s.AP_NAME_PREFIX + str(bs_id), ap_location[0], ap_location[1])
        else:
            sumo_manager.add_uav(ap.name, ap_location[0], ap_location[1])
            Simulation.record.aps[ap.name] = ApRecord(ap.name)


def update_drone_locations_on_sumo(net, sumo_manager):
    for ap in net.aps:
        ap_location = ap.getxyz()
        if not ap.name.startswith("bs"):
            sumo_manager.set_uav_location(ap.name, ap_location[0], ap_location[1], Simulation.current_time)
            Simulation.record.aps[ap.name].add_moment(ApMoment(ap.name, Simulation.current_time,
                                                               ap_location[0], ap_location[1], ap_location[2]))


def disassociate_sumo_vehicles_leaving_area(leaving_vehicle_id_list, vehicle_to_mn_sta):
    for vehicle_sumo_id in leaving_vehicle_id_list:
        sta_to_be_disassociated = vehicle_to_mn_sta.pop(vehicle_sumo_id, None)
        sta_to_be_disassociated.is_used = False
        sta_to_be_disassociated.sumo_id = None
        unassociated_mn_stations.append(sta_to_be_disassociated)
        set_vehicle_as_left(vehicle_sumo_id)
        Simulation.record.vehicles[vehicle_sumo_id].departure_time = Simulation.current_time
        sta_to_be_disassociated.setPosition(s.UNASSOCIATED_CAR_LOCATION)
        logging.info("Disassociated vehicle %s from mn car %s", vehicle_sumo_id, sta_to_be_disassociated.name)


def add_vehicle(sumo_vehicle, sta_to_be_associated, current_time):
    vehicle_record = VehicleRecord(sumo_vehicle.sumo_id, sta_to_be_associated.name, sumo_vehicle.type_abbreviation,
                                   current_time)
    Simulation.record.vehicles[sumo_vehicle.sumo_id] = vehicle_record
    if sumo_vehicle.type_abbreviation in s.PROCESSOR_VEHICLE_TYPES:
        vehicle = ProcessorVehicle(sumo_vehicle, sta_to_be_associated, current_time)
    else:
        vehicle = TaskGeneratorVehicle(sumo_vehicle, sta_to_be_associated, current_time)
    add_to_connecting_vehicles(vehicle)


def associate_sumo_vehicles_with_mn_stations(current_time, sumo_manager, vehicle_data_list, vehicle_to_mn_sta):
    for sumo_vehicle in vehicle_data_list:
        if sumo_vehicle.sumo_id not in vehicle_to_mn_sta:
            if unassociated_mn_stations:
                sta_to_be_associated = unassociated_mn_stations.pop()
                sta_to_be_associated.is_used = True
                sta_to_be_associated.sumo_id = sumo_vehicle.sumo_id
                vehicle_to_mn_sta[sumo_vehicle.sumo_id] = sta_to_be_associated
                add_vehicle(sumo_vehicle, sta_to_be_associated, current_time)
                logging.info("Associating vehicle %s with mn car %s", sumo_vehicle.sumo_id, sta_to_be_associated.name)
                sumo_manager.set_assigned_mn_object_name_vehicle(sumo_vehicle.sumo_id, sta_to_be_associated.name)
            else:
                logging.error("No mn car object available to associate with vehicle %s", sumo_vehicle.sumo_id)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
