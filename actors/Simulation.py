import logging

import settings as s
from actors.TaskGenerator import TaskGenerator
from actors.TaskOrganizer import TaskOrganizer
from actors.Vehicle import ProcessorVehicle, ConnectionStatus
from task_dispatcher import send_task_request_to_task_assigner


class Simulation:
    current_time = 0
    end_time = s.SIMULATION_DURATION
    drone_id_close_to_bs = None
    bs_host = None
    nat_host = None
    task_assigner_host = None
    task_assigner_host_ip = None
    task_organizer = TaskOrganizer()
    task_generator = TaskGenerator()
    all_vehicles = {}
    connecting_vehicles = {}
    tasks = []

    @staticmethod
    def set_task_assigner(host):
        Simulation.task_assigner_host_ip = host.intfs[0].ip
        Simulation.task_assigner_host = host

    @staticmethod
    def handle_tasks():
        if Simulation.current_time < s.TASK_GENERATION_START_TIME:
            return
        new_tasks = Simulation.task_generator.generate_new_tasks(Simulation.current_time)
        for task in new_tasks:
            Simulation.tasks.append(task)
            Simulation.task_organizer.add_task(Simulation.current_time, task)
            send_task_request_to_task_assigner(Simulation.task_assigner_host_ip, task)
        Simulation.task_organizer.handle_tasks(Simulation.current_time)

    @staticmethod
    def add_to_connecting_vehicles(vehicle):
        Simulation.connecting_vehicles[vehicle.sumo_id] = vehicle
        Simulation.all_vehicles[vehicle.sumo_id] = vehicle
        logging.info(f"Processor vehicle is setting up to network connection: {vehicle.sumo_id}")

    @staticmethod
    def add_to_connected_vehicles(vehicle):
        Simulation.connecting_vehicles.pop(vehicle.sumo_id)
        vehicle.connection_status = ConnectionStatus.CONNECTED
        if isinstance(vehicle, ProcessorVehicle):
            Simulation.task_organizer.add_to_available_task_processors(vehicle)
        else:
            Simulation.task_generator.add_to_available_task_generators(vehicle)

    @staticmethod
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

    @staticmethod
    def set_vehicle_as_changing_network(sumo_id):
        vehicle = Simulation.all_vehicles[sumo_id]
        if vehicle.connection_status == ConnectionStatus.CONNECTED:
            if isinstance(vehicle, ProcessorVehicle):
                Simulation.task_organizer.remove_from_available_task_processors(sumo_id)
            else:
                Simulation.task_generator.remove_task_generator(sumo_id)
            vehicle.set_as_connecting()
            Simulation.add_to_connecting_vehicles(vehicle)
        elif vehicle.connection_status == ConnectionStatus.CONNECTING:
            return

    @staticmethod
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
