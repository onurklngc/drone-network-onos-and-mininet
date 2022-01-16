import os
import socket
import sys

import settings
from actors.Simulation import Simulation

DEBUG = True
sta_ip = ""


def debug(msg):
    if DEBUG:
        if not sta_ip.startswith("192"):
            f = open('staLogs/%s.log' % sta_id, 'a+')
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
        s.connect((Simulation.task_assigner_host_ip, settings.TASK_REQUEST_LISTEN_PORT))
        s.sendall(message.encode('ascii'))
        s.close()
    except Exception as e:
        debug(e)


def host_ip_to_id(host_ip):
    tmp_host_id = host_ip.split(".")[-1]
    return int(tmp_host_id)


if __name__ == '__main__':
    # Run the host listeners
    sta_ip = sys.argv[1]
    sta_id = sta_ip.split(".")[-1]
    itg_rec_signal_port = int(sta_id) + 9000
    debug("Station ip is " + sta_ip)
    debug("Station is awake")
    simulation_id = sys.argv[2]
    while True:
        if settings.USE_IPERF:
            result = os.system("iperf -s -y C | tee -a logs_iperf/%s_%s.log" % (simulation_id, sta_id))
            debug("iperf -s: %d" % result)
        else:
            result = os.system("ITGRecv -Sp %d -a %s" % (itg_rec_signal_port, sta_ip))
            debug("ITGRecv %d" % result)
