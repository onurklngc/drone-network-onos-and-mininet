import logging

from actors.Vehicle import ConnectionStatus


class VehicleMoment:
    sumo_id = None
    moment_time = None
    x = None
    y = None
    associated_ap = None
    rssi = None
    connection_status = ConnectionStatus.DISCONNECTED

    def __init__(self, sumo_id, moment_time, x, y, associated_ap=None):
        self.sumo_id = sumo_id
        self.moment_time = moment_time
        self.x = x
        self.y = y
        self.associated_ap = associated_ap

    def set_associated_ap(self, ap_name, rssi):
        self.associated_ap = ap_name
        self.rssi = rssi

    def set_connection_status(self, connection_status):
        self.connection_status = connection_status

    def __repr__(self) -> str:
        return f"{self.sumo_id}|moment time:{self.moment_time}|x:{self.x}|y:{self.y}| ap:{self.associated_ap}"


class ApMoment:
    name = None
    moment_time = None
    x = None
    y = None
    z = None
    associated_stations = None

    def __init__(self, name, moment_time, x, y, z, associated_stations=None):
        self.name = name
        self.moment_time = moment_time
        self.x = x
        self.y = y
        self.z = z
        self.associated_stations = associated_stations

    def __repr__(self) -> str:
        return f"{self.name}|moment time:{self.moment_time}|x:{self.x}|y:{self.y}|z:{self.z} |" \
               f" associated stations:{self.associated_stations}"

    def add_station(self, station):
        if self.associated_stations:
            self.associated_stations.append(station)
        else:
            self.associated_stations = [station]


class TaskRecord:
    no = 0
    owner_sumo_id = None
    start_time = None
    priority = None
    size = None
    deadline = None

    def __init__(self, no, start_time, owner_sumo_id, priority, size, deadline):
        self.no = no
        self.start_time = start_time
        self.owner_sumo_id = owner_sumo_id
        self.priority = priority
        self.size = size
        self.deadline = deadline

    def __repr__(self) -> str:
        return f"#{self.no}({self.owner_sumo_id}) start:{self.start_time} deadline:{self.deadline} " \
               f"priority:{self.priority} size:{self.size}"


class VehicleRecord:
    sumo_id = None
    sta_name = None
    entry_time = None
    departure_time = None
    no_new_task_start_time = None
    moments = {}
    type_abbreviation = None

    def __init__(self, sumo_id, sta_name, type_abbreviation=None, entry_time=None):
        self.sumo_id = sumo_id
        self.sta_name = sta_name
        self.moments = {}
        self.type_abbreviation = type_abbreviation
        self.entry_time = entry_time

    def __repr__(self) -> str:
        return f"{self.sumo_id}({self.sta_name}) entry:{self.entry_time} departure:{self.departure_time} " \
               f"noTaskAfter:{self.no_new_task_start_time}"

    def add_moment(self, moment):
        self.moments[moment.moment_time] = moment

    def update_moment_connection_status(self, moment_time, status):
        if moment_time in self.moments:
            self.moments[moment_time].set_connection_status(status)

    def get_moment(self, moment_time):
        try:
            return self.moments[moment_time]
        except Exception as e:
            logging.exception(e)


class ApRecord:
    name = None
    moments = {}

    def __init__(self, name):
        self.name = name
        self.moments = {}

    def add_moment(self, moment):
        self.moments[moment.moment_time] = moment

    def get_moment(self, moment_time):
        return self.moments[moment_time]

    def add_station(self, moment_time, station):
        self.moments[moment_time].add_station(station)


class SimulationRecord:
    simulation_id = None
    real_life_start_time = None
    sim_start_time = None
    sim_end_time = None
    vehicles = None
    tasks = None
    aps = None

    def __init__(self, simulation_id, real_life_start_time, sim_start_time, sim_end_time):
        self.simulation_id = simulation_id
        self.real_life_start_time = real_life_start_time
        self.sim_start_time = sim_start_time
        self.sim_end_time = sim_end_time
        self.vehicles = {}
        self.tasks = {}
        self.aps = {}
