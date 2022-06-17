# 5-Optimum	5-Adaptive	5-Aggressive	5-Aggressive-Wait   5-Only-Cloud  10-Optimum	10-Adaptive	10-Aggressive	10-Aggressive-Wait  10-Only-Cloud	15-Optimum	15-Adaptive	15-Aggressive	15-Aggressive-Wait  15-Only-Cloud
REQUEST_INTERVAL_PENALTY = "36.56	59.22	66.43	67.29	85.96	6.71	28.9	29.67	30.84	20.36	6.1	11.23	16.12	15.41	9.36"
REQUEST_INTERVAL_CASES = ['5', '10', '15']
REQUEST_INTERVAL_X_LABEL = "Request Interval (s)"

VEHICLE_SPEED = "7.23	14.87	20.07	20.76	5.78	28.9	29.67	30.84	7.12	25.79	28.09	32.98"
VEHICLE_SPEED_V2 = "7.23	14.87	20.07	20.76	5.78	28.9	29.67	30.84	7.12	25.79	28.09	32.98"
VEHICLE_SPEED_V6 = "5.51	28.71	33.22	36.63	47.31	10.08	41.35	47.03	49.35	63.66	30.69	66.15	73.14	72.29	71.04"
VEHICLE_SPEED_CASES = ['5', '20', '40']
VEHICLE_SPEED_X_LABEL = "Average Vehicle Speed (km/h)"

PROCESS_SPEED = "9.77	41.74	48.45	52.01	5.78	28.9	29.67	30.84	5.9	19.17	27.11	29.25"
PROCESS_SPEED_CASES = ['Slow', 'Medium', 'Fast']
PROCESS_SPEED_X_LABEL = "Processing Speed"

easy_settings = {
    "request": {
        "values": REQUEST_INTERVAL_PENALTY,
        "case_names": REQUEST_INTERVAL_CASES,
        "x_label": REQUEST_INTERVAL_X_LABEL
    },
    "vehicle": {
        "values": VEHICLE_SPEED,
        "case_names": VEHICLE_SPEED_CASES,
        "x_label": VEHICLE_SPEED_X_LABEL
    },
    "vehicle_v2": {
        "values": VEHICLE_SPEED_V2,
        "case_names": VEHICLE_SPEED_CASES,
        "x_label": VEHICLE_SPEED_X_LABEL
    },
    "vehicle_v6": {
        "values": VEHICLE_SPEED_V6,
        "case_names": VEHICLE_SPEED_CASES,
        "x_label": VEHICLE_SPEED_X_LABEL
    },
    "process": {
        "values": PROCESS_SPEED,
        "case_names": PROCESS_SPEED_CASES,
        "x_label": PROCESS_SPEED_X_LABEL
    }
}
