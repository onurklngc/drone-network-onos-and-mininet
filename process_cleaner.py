#!/usr/bin/python

import os
import subprocess
from signal import SIGINT, SIGTERM, SIGKILL
import traceback


def kill_process(name, ps_parameter, signal_type):
    p = subprocess.Popen(['ps', '-' + ps_parameter], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        if name in line:
            print(line)
            try:
                pid = int(line.split(None, 1)[0])
                os.kill(pid, signal_type)
            except Exception as e:
                print(traceback.format_exc())
                print (e)


def stop_children_processes(processes):
    for p in processes:
        p.send_signal(SIGINT)
    for signalType in [SIGINT, SIGTERM, 9]:
        kill_process('iperf', 'A', signalType)
        kill_process('ITGRecv', 'A', signalType)
        kill_process('ITGSend', 'A', signalType)
        kill_process('media_server', 'x', signalType)
        kill_process('streamer_host', 'x', signalType)
        os.system("pkill ITGRecv")
        os.system("pkill ITGSend")
        os.system("pkill iperf")


if __name__ == '__main__':
    stop_children_processes()
