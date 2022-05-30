import glob
import logging
import os
import subprocess


def recover_multiple_files(folder_path):
    data_obtained = {}
    processes = {}
    list_of_folders = glob.glob(folder_path + "/*")
    for folder_path in list_of_folders:
        list_of_sub_folders = glob.glob(folder_path + "/*")
        for sub_folder_path in list_of_sub_folders:
            list_of_files = glob.glob(sub_folder_path + "/*")
            for file_path in list_of_files:
                if "slow" not in file_path and "fast" not in file_path:
                # if "slow" in file_path:
                # if "fast" in file_path:
                # if "lambda5" in file_path:
                    command = f"python recover_solutions.py --record-file {file_path}"
                    try:
                        # process = subprocess.Popen(command.split(" "), stdout=subprocess.DEVNULL)
                        process = subprocess.Popen(command.split(" "), stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
                        processes[process.pid] = process
                    except Exception as e:
                        logging.exception(f"Error for: {command} ,{e}")
                # print(result)
    for process in processes.values():
        result = process.wait()
        command = ' '.join(process.args)
        output = process.communicate()
        if process.returncode != 0:
            logging.info(f"Error on {command}. Output: {output}")
        else:
            logging.info(f"Completed {command}. Output: {output}")




if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    recover_multiple_files("records")
