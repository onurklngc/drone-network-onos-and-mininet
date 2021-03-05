# MAIN
LOG_LEVEL = "INFO"
MN_WIFI_LOG_LEVEL = "DEBUG"
NUM_OF_DRONES = 4
NUM_OF_CARS = 10
IS_REMOTE_CONTROLLER = True

# MOVEMENT
RANDOM_DRONE_MOVEMENT = False
FIGURE_8_DRONE_MOVEMENT = True
FIGURE_8_ALPHA_VAR = 10
FIGURE_8_PERIOD = 20
COORDINATE_LIMIT_X = (400, 2000)
COORDINATE_LIMIT_Y = (200, 1200)
UNASSOCIATED_CAR_LOCATION = "-100,-100,0"
AVERAGE_HEIGHT = 20
HEIGHT_DEVIATION = 5

# SUMO TRACI
SUMO_BINARY = "sumo-gui"
SUMO_CFG_PATH = "/home/onur/Sumo/2020-10-05-00-23-21/osm.sumocfg"
VEHICLE_PREFIX = "veh"
NUM_OF_SIMULATION_STEPS = 500
START_SIMULATION_DIRECTLY = True
SIMULATION_DELAY = 1000  # in ms
VEHICLE_CATEGORY_DISTRIBUTION = ['E'] * 2 + ['T'] * 5 + ['B'] * 3 + ['P'] * 10
DEFAULT_VEHICLE_CLASS = "passenger"
HIGHLIGHT_CARS = True
VEHICLE_TYPE_PROPERTIES = {
    "E": {"type": "emergency", "shape": "emergency", "color": "white"},
    "A": {"type": "authority", "shape": "authority", "color": "purple"},
    "V": {"type": "vip", "shape": "vip", "color": "magenta"},
    "B": {"type": "bus", "shape": "bus", "color": "cyan"},
    "T": {"type": "truck", "shape": "truck", "color": "red"},
    "P": {"type": "private", "shape": "passenger/sedan", "color": "pink"},
}

# Controller
MININET_IP = "127.0.0.1"

# ENERGY
INITIAL_DRONE_BATTERY_CAPACITY = 187545.6  # Joule(Ws) 0.8 * 65.12Wh=4.4Ah@14.8V %20 Reserved
POWER_FLY = 174.34  # Watt INITIAL_DRONE_BATTERY_CAPACITY/(22.41*60)sec
# Flight time is 17.93 if 20% reserved.
POWER_TX = 5  # Watt
POWER_WRITE = 2.34375e-05  # per Kb 3V*0.2A=0.6W/ 25MBbps
POWER_READ = 7.8125e-06  # per Kb # 1V*0.2A=0.2W/ 25MBps
POWER_PROCESS_PACKET = 7.8125e-06 * 1500

# OTHER
NUM_OF_DRONES_PER_ROW = 2
NUM_OF_DRONES_PER_COLUMN = 2
CONTROLLER_IP = "127.0.0.1"