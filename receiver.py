import os
import socket
import sys
import threading
from subprocess import check_output

import settings as s

DEBUG = True
host_ip = ""


def debug(msg):
    if DEBUG:
        if not host_ip.startswith("192"):
            f = open('hostLogs/%s.log' % host_id, 'a+')
            f.write(str(msg) + "\n")
            f.close()
        else:
            print(msg)


def inform_station_is_available(sender_ip, tmp_host_ip, flow_id):
    message = "{};{};{}".format(sender_ip, tmp_host_ip, flow_id)
    debug("Inform %s" % message)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect((MININET_IP, HOST_AVAILABILITY_LISTEN_PORT))
        s.sendall(message.encode('ascii'))
        s.close()
    except Exception as e:
        debug(e)


def host_ip_to_id(host_ip):
    tmp_host_id = host_ip.split(".")[-1]
    return int(tmp_host_id)



def send_file(requesting_host_ip, car_type, requested_file_size, flow_id):

    if s.USE_IPERF:
        command = "iperf -c {0} -n {1}KB -f KB".format(requesting_host_ip, requested_file_size).split()
        res = check_output(command)
        # res = os.system(
        #     "iperf -c {0} -n {1}KB -f KB".format(
        #         requesting_host_ip,
        #         requested_file_size,
        #     )
        # )
    else:
        destination_host_id = host_ip_to_id(requesting_host_ip)
        res = os.system(
            "ITGSend -a {0} -T TCP -C 100000 -c 1408 -k {1} -L {2} TCP -l {3}/{4}.log -Sdp {5} -rp {7} -j 1 -poll".format(
                requesting_host_ip,
                requested_file_size,
                ITG_LOG_SERVER_IP,
                ITG_SENDER_LOG_PATH,
                host_id,
                destination_host_id + 9000,
                destination_host_id + 9200,
                destination_host_id + 9400
            )
        )

    # result = os.system(
    #     "ITGSend -a {0} -T TCP -C 10000  -c 1408 -k {1} -L {2} TCP -X {2} TCP -l logsS/{3}.log -x logsR/{3}.log".format(
    #         requesting_host_ip, requested_file_size,
    #         ITG_LOG_SERVER_IP, host_id))
    debug("sendFile result: %s" % str(res))
    inform_station_is_available(host_ip, requesting_host_ip, flow_id)


def get_file_request(accepted_socket, address):
    message = accepted_socket.recv(1024).decode()
    debug(message)
    accepted_socket.close()
    # File request protocol message: requesting_host_ip;requested_file_id;requested_file_size
    message_parsed = message.split(";", 3)
    requesting_host_ip = message_parsed[0]
    requested_file_id = int(message_parsed[1])
    requested_file_size = message_parsed[2].strip()
    flow_id = message_parsed[3]
    send_file(requesting_host_ip, requested_file_id, requested_file_size, flow_id)


def listen_file_requests():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host_ip, FILE_REQUEST_LISTEN_PORT))
    s.listen(5)
    while True:
        accepted_socket, address = s.accept()
        get_file_request_thread = threading.Thread(target=get_file_request, args=(accepted_socket, address))
        get_file_request_thread.setDaemon(True)
        get_file_request_thread.start()


if __name__ == '__main__':
    # Run the host listeners
    host_ip = sys.argv[1]
    host_id = host_ip.split(".")[-1]
    itg_rec_signal_port = int(host_id) + 9000
    debug("Station ip is " + host_ip)
    debug("Station is awake")
    listen_file_requests_thread = threading.Thread(target=listen_file_requests)
    listen_file_requests_thread.setDaemon(True)
    listen_file_requests_thread.start()
    simulation_id = sys.argv[2]
    while True:
        if s.USE_IPERF:
            result = os.system("iperf -s -y C | tee -a logs_iperf/%s_%s.log" % (simulation_id, host_id))
            debug("iperf -s: %d" % result)
        else:
            result = os.system("ITGRecv -Sp %d -a %s" % (itg_rec_signal_port, host_ip))
            debug("ITGRecv %d" % result)
