import logging

from actors.Simulation import Simulation
from actors.TrafficObserver import TrafficObserver
from actors.Vehicle import ProcessorVehicle, ConnectionStatus


def add_to_connecting_vehicles(vehicle):
    Simulation.connecting_vehicles[vehicle.sumo_id] = vehicle
    Simulation.all_vehicles[vehicle.sumo_id] = vehicle
    logging.info(f"Processor vehicle is setting up to network connection: {vehicle.sumo_id}")


def add_to_connected_vehicles(vehicle):
    Simulation.connecting_vehicles.pop(vehicle.sumo_id)
    vehicle.connection_status = ConnectionStatus.CONNECTED
    if isinstance(vehicle, ProcessorVehicle):
        Simulation.task_organizer.add_to_available_task_processors(vehicle)
        vehicle.iperf_server_process = vehicle.station.popen(f"iperf -s -y C")
    else:
        Simulation.task_generator.add_to_available_task_generators(vehicle)


def set_vehicle_as_left(sumo_id):
    vehicle = Simulation.all_vehicles[sumo_id]
    if vehicle.connection_status == ConnectionStatus.CONNECTED:
        if isinstance(vehicle, ProcessorVehicle):
            Simulation.task_organizer.remove_from_available_task_processors(sumo_id)
        else:
            Simulation.task_generator.remove_task_generator(sumo_id)
    else:
        Simulation.connecting_vehicles.pop(sumo_id)
    vehicle.leave(Simulation.current_time)
    TrafficObserver.reset_traffic_on_sta(vehicle.station.name)
    Simulation.task_organizer.handle_vehicle_departure(vehicle)


def set_vehicle_as_changing_network(sumo_id):
    vehicle = Simulation.all_vehicles[sumo_id]
    if vehicle.connection_status == ConnectionStatus.CONNECTED:
        if isinstance(vehicle, ProcessorVehicle):
            Simulation.task_organizer.remove_from_available_task_processors(sumo_id)
        else:
            Simulation.task_generator.remove_task_generator(sumo_id)
        vehicle.set_as_connecting()
        add_to_connecting_vehicles(vehicle)
    elif vehicle.connection_status == ConnectionStatus.CONNECTING:
        return


def set_vehicle_as_disconnected(sumo_id):
    vehicle = Simulation.all_vehicles[sumo_id]
    if vehicle.connection_status == ConnectionStatus.CONNECTED:
        if isinstance(vehicle, ProcessorVehicle):
            Simulation.task_organizer.remove_from_available_task_processors(sumo_id)
        else:
            Simulation.task_generator.remove_task_generator(sumo_id)
    elif vehicle.connection_status == ConnectionStatus.CONNECTING:
        Simulation.connecting_vehicles.pop(sumo_id)
    vehicle.set_as_disconnected()
