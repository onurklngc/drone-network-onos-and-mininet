#!/usr/bin/python

import os
import subprocess
import traceback
from signal import SIGINT, SIGTERM


def kill_process(name, ps_parameter, signal_type):
    p = subprocess.Popen(['ps', '-' + ps_parameter], stdout=subprocess.PIPE)
    out, err = p.communicate()
    for line in out.splitlines():
        line = line.decode()
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
        kill_process('main_v2', 'ax', signalType)
        kill_process('sumo-gui', 'ax', signalType)
        kill_process('xterm', 'ax', signalType)
        kill_process('ITG', 'ax', signalType)


if __name__ == '__main__':
    stop_children_processes([])
    p = subprocess.call(['mn', '-c'])
