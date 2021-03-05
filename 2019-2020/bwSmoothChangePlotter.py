import re
import os
from time import sleep

import matplotlib.pyplot as plt

TARGET_BW = 500
INITIAL_BW = 200


def plotIperf(traces):
    for trace in traces:
        bw_list = []
        for line in open(trace[0], 'r'):
            matchObj = re.match(r'(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*),(.*)', line, re.M)

            if matchObj:
                bw = float(matchObj.group(9)) / 1000.0 / 1000.0 # MBit / s
                bw_list.append(bw)
        plt.plot(bw_list, label=trace[1])

    plt.legend()
    plt.title("Throughput Comparison")
    plt.ylabel("Throughput [MBit / s]")
    plt.xlabel("Time")
    plt.show()

def plotFromData():
    traces = []

    filename = 'iperfServer_hard.log'
    traces.append((filename, 'Hard'))

    # reset bw to initial value
    filename = 'iperfServer_smooth.log'
    traces.append((filename, 'Smooth'))

    # reset bw to initial value

    filename = 'iperfServer_nolimit.log'
    traces.append((filename, 'No limit'))


    plotIperf(traces)

if __name__ == '__main__':
    plotFromData()