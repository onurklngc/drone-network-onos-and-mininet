import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "18"

simID = "L1"

fileName = "sims/%s/a.csv" % simID

simID2 = "L2"
fileName2 = "sims/%s/a.csv" % simID2

interval = 5

batteryLevels = np.transpose(np.genfromtxt(fileName, dtype=float, delimiter=','))
batteryLevels = np.clip(batteryLevels, 0, 50000)
batteryNum = batteryLevels.shape[0]
stepSize = batteryLevels.shape[1]
steps = np.arange(0, stepSize * interval, interval)

batteryLevels2 = np.transpose(np.genfromtxt(fileName2, dtype=float, delimiter=','))
batteryLevels2 = np.clip(batteryLevels2, 0, 50000)
batteryNum2 = batteryLevels2.shape[0]
stepSize2 = batteryLevels2.shape[1]
steps2 = np.arange(0, stepSize2 * interval, interval)


hfont = {'fontname':'Arial'}

legend_elements = [Line2D([0],[0], color='k',linestyle=':', lw=5, label='Configuration 4'),
                   Line2D([0],[0], color='k',linestyle='-', lw=5, label='Configuration 5',
                          markerfacecolor='g', markersize=15)]

fig, ax = plt.subplots()
ax.legend(handles=legend_elements, prop={'size': 35})
plt.grid()
ax.set_xlabel('time (s)',fontsize=25)
ax.set_ylabel('Residual energy level (mAh)',fontsize=25)
ax.set_xlim(0, 1070)
ax.set_ylim(0, 18000)

uavs= [0, 5, 10,13,18]

for index, battery in enumerate(batteryLevels):
    if index in uavs:
        plotFromFirstDataset = plt.plot(steps, battery, linestyle=':',lw=5)
        plt.plot(steps2, batteryLevels2[index],color=plotFromFirstDataset[0]._color, linestyle='-', lw=5)

# for index, battery in enumerate(battery_levels2):
#     if index in uavs:
#         plt.plot(steps2, battery, linestyle='-',lw=5)

plt.show()
