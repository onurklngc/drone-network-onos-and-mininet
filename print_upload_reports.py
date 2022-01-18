import logging
import time

from results import get_latest_simulation_file, get_simulation_results

RESULT_FILENAME = ""
SWITCH_TO_LATEST_SIMULATION = True
displayed_task_identifiers = []


def print_upload_reports(sim_results):
    global displayed_task_identifiers
    upload_reports = sim_results['upload_outputs']
    for task_identifier, upload_report in upload_reports.items():
        if task_identifier not in displayed_task_identifiers:
            logging.info(f"{task_identifier}\n{upload_report.decode()}")
        displayed_task_identifiers.append(task_identifier)


def tail_upload_reports(filename):
    global displayed_task_identifiers
    while True:
        if SWITCH_TO_LATEST_SIMULATION:
            latest_filename = get_latest_simulation_file()
            if filename != latest_filename:
                filename = latest_filename
                displayed_task_identifiers = []
        sim_results = get_simulation_results(filename)
        print_upload_reports(sim_results)
        time.sleep(5)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    if RESULT_FILENAME:
        result_file_to_view = RESULT_FILENAME
    else:
        result_file_to_view = get_latest_simulation_file()
    results = get_simulation_results(result_file_to_view)
    print_upload_reports(results)
    input("Press Enter to continue...")
    tail_upload_reports(result_file_to_view)
