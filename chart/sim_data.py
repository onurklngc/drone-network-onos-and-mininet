# 5-Optimum	5-Adaptive	5-Aggressive	5-Aggressive-Wait	10-Optimum	10-Adaptive	10-Aggressive	10-Aggressive-Wait	15-Optimum	15-Adaptive	15-Aggressive	15-Aggressive-Wait
REQUEST_INTERVAL_PENALTY = "14.19	59.22	66.43	67.29	5.78	28.9	29.67	30.84	5.36	11.23	16.12	15.41"
REQUEST_INTERVAL_CASES = ['5', '10', '15']
REQUEST_INTERVAL_X_LABEL = "Request Interval (s)"

VEHICLE_SPEED = "7.23	14.87	20.07	20.76	5.78	28.9	29.67	30.84	7.12	25.79	28.09	32.98"
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
    "process": {
        "values": PROCESS_SPEED,
        "case_names": PROCESS_SPEED_CASES,
        "x_label": PROCESS_SPEED_X_LABEL
    }
}
