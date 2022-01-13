# MAIN
SIMULATION_DURATION = 450
TASK_GENERATION_START_TIME = 150
TASK_GENERATION_END_TIME = 400
TASK_GENERATION_INTERVAL = 3
TASK_SIZE = (40, 60)
DEADLINE = (50, 120)
LOG_LEVEL = "INFO"
# LOG_LEVEL = "DEBUG"
MN_WIFI_LOG_LEVEL = "INFO"
NUMBER_OF_DRONES = 9
NUMBER_OF_STATIONS = 20
IS_REMOTE_CONTROLLER = True

# RANDOMNESS CONTROL
USE_RANDOM_SUMO_SEED = False
SUMO_SEED_TO_USE = 1
SELECT_RANDOM_DRONE_FOR_BS_CONNECTION = False
DRONE_ID_CLOSE_TO_BS = 0

# MOVEMENT
RANDOM_DRONE_MOVEMENT = False
FIGURE_8_DRONE_MOVEMENT = True
FIGURE_8_ALPHA_VAR = 10
FIGURE_8_PERIOD = 20
COORDINATE_LIMIT_X = (0, 1500)
COORDINATE_LIMIT_Y = (-150, 1350)
UNASSOCIATED_CAR_LOCATION = "-9999,-9999,1"
AVERAGE_HEIGHT = 100
BS_HEIGHT = 10
HEIGHT_DEVIATION = 3

# SUMO TRACI
SKIPPED_STEPS = 140
IS_REAL_TIME = False
SUMO_BINARY = "sumo-gui"
# SUMO_CFG_PATH = "/home/onur/Coding/projects/sdnCaching/configs/besiktas-2-satellite/osm.sumocfg"
SUMO_CFG_PATH = "/home/onur/Coding/projects/sdnCaching/configs/besiktas-2/osm.sumocfg"
SUMO_SIMULATED_DATA_PATH = "/home/onur/Coding/projects/sdnCaching/configs/besiktas/sumo_results.xml"
VEHICLE_PREFIX = "veh"
START_SIMULATION_DIRECTLY = True
SUMO_DELAY = 1  # in ms
SIMULATION_STEP_DELAY = 1000  # in ms
VEHICLE_CATEGORY_DISTRIBUTION = ['E'] * 5 + ['T'] * 4 + ['A'] * 3 + ['B'] * 1 + ['P'] * 3
DEFAULT_VEHICLE_CLASS = "passenger"
HIGHLIGHT_CARS = False
HIGHLIGHT_AP_RANGE = True
PROCESSOR_VEHICLE_TYPES = ["A", "B"]
TASK_GENERATOR_VEHICLE_TYPES = ["E", "T"]
VEHICLE_TYPE_PROPERTIES = {
    # Task generators
    "E": {"type": "emergency", "shape": "emergency", "color": "red",
          "priority": 0.7, "type_abbreviation": "E"},
    "T": {"type": "emergency", "shape": "firebrigade", "color": "red",
          "priority": 0.3, "type_abbreviation": "T"},
    # Processors
    "A": {"type": "trailer", "shape": "truck/semitrailer", "color": "purple",
          "process_speed": 25, "queue_size": 250, "type_abbreviation": "A"},
    "B": {"type": "bus", "shape": "bus", "color": "cyan",
          "process_speed": 15, "queue_size": 150, "type_abbreviation": "B"},
    # Other
    "V": {"type": "vip", "shape": "vip", "color": "magenta", "type_abbreviation": "V"},
    "P": {"type": "private", "shape": "passenger/sedan", "color": "pink", "type_abbreviation": "P"},
}
# WIFI
WIFI_NOISE_THRESHOLD = -75
AP_AP_RANGE = 450
AP_GROUND_RANGE = 320  # 336 * cos(17.6)
# POWER
ANTENNA_GAIN = 3
DRONE_AP_TX_POWER = 27
DRONE_MESH_TX_POWER = 14
BS_MESH_TX_POWER = 15
VEHICLE_TX_POWER = 27

# CONTROLLER
MININET_IP = "127.0.0.1"
UPDATE_SW_LOCATIONS_ON_ONOS = False
USE_LAT_LON = False

# TRAFFIC
GENERATE_TRAFFIC = True
USE_IPERF = False
DITG_CONTROL_PORTS = []

# CLOUD
CLOUD_PROCESSOR_SPEED = 250
CLOUD_PROBABILITY_BY_POOL_SIZE = {
    0: 0,
    3: 0.2,
    7: 0.7,
    10: 0.9
}

# COMMUNICATION
TASK_ASSIGNER_SERVER = "NAT"  # BS_HOST, NAT, CONTROLLER_HOST
TASK_REQUEST_LISTEN_PORT = 8701

# OTHER
NUMBER_OF_DRONES_PER_ROW = 3
NUMBER_OF_DRONES_PER_COLUMN = 3
CONTROLLER_IP = "127.0.0.1"
AP_NAME_PREFIX = "ap"
BS_NAME_PREFIX = "bs"
BS_ID_OFFSET = 100
CONTROLLER_HOST_ID = 255
BS_GROUND_RANGE = 100
BS_GROUND_ANTENNA_GAIN = -5
BS_GROUND_TX_POWER = 1
BS_TX_POWER = 1
ADD_DRONE_MN_HOST = False
PLOT_MININET_GRAPH = False

# CONFIGS BELOW ARE NOT USED
# ENERGY
INITIAL_DRONE_BATTERY_CAPACITY = 187545.6  # Joule(Ws) 0.8 * 65.12Wh=4.4Ah@14.8V %20 Reserved
POWER_FLY = 174.34  # Watt INITIAL_DRONE_BATTERY_CAPACITY/(22.41*60)sec
# Flight time is 17.93 if 20% reserved.
POWER_TX = 5  # Watt
POWER_WRITE = 2.34375e-05  # per Kb 3V*0.2A=0.6W/ 25MBbps
POWER_READ = 7.8125e-06  # per Kb # 1V*0.2A=0.2W/ 25MBps
POWER_PROCESS_PACKET = 7.8125e-06 * 1500
