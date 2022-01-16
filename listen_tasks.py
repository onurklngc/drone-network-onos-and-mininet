import logging
import socket

import settings as s

number_of_tasks_received = 0


def get_task_request(accepted_socket):
    global number_of_tasks_received
    message = accepted_socket.recv(1024).decode()
    logging.info(f"Received task #{number_of_tasks_received}-> {message}")
    accepted_socket.send(f"Number of tasks received : {number_of_tasks_received}".encode())
    accepted_socket.close()
    number_of_tasks_received += 1
    # media_server.process_file_request(message)


def listen_task_requests():
    listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listening_socket.bind(("0.0.0.0", s.TASK_REQUEST_LISTEN_PORT))
    listening_socket.listen(5)
    while True:
        try:
            accepted_socket, address = listening_socket.accept()
            get_task_request(accepted_socket)
        except Exception as e:
            logging.error("Crash in listen_task_requests")
            logging.exception(e)


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, s.LOG_LEVEL), format="%(asctime)s %(levelname)s -> %(message)s")
    listen_task_requests()
