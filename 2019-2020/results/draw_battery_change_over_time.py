import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "18"

sim_id = "156889582-0.1-0.2-0.7"

# file_name = "sims/%s/a.csv" % sim_id
file_name = "%s.csv" % sim_id

sim_id2 = "156838291-0.1-0.2-0.7"
# file_name2 = "sims/%s/a.csv" % sim_id2
file_name2 = "%s.csv" % sim_id2

interval = 5

battery_levels = np.transpose(np.genfromtxt(file_name, dtype=float, delimiter=','))
battery_levels = np.clip(battery_levels, 0, 500000)
battery_num = battery_levels.shape[0]
step_size = battery_levels.shape[1]
steps = np.arange(0, step_size * interval, interval)

battery_levels2 = np.transpose(np.genfromtxt(file_name2, dtype=float, delimiter=','))
battery_levels2 = np.clip(battery_levels2, 0, 500000)
batteryNum2 = battery_levels2.shape[0]
stepSize2 = battery_levels2.shape[1]
steps2 = np.arange(0, stepSize2 * interval, interval)


hfont = {'fontname':'Arial'}

legend_elements = [Line2D([0],[0], color='k',linestyle=':', lw=5, label='Configuration 3'),
                   Line2D([0],[0], color='k',linestyle='-', lw=5, label='Configuration 5',
                          markerfacecolor='g', markersize=15)]

fig, ax = plt.subplots()
ax.legend(handles=legend_elements, prop={'size': 35})
plt.grid()
ax.set_xlabel('time (s)',fontsize=25)
ax.set_ylabel('Residual energy level (J)',fontsize=25)
ax.set_xlim(0, 1200)
ax.set_ylim(0, 250000)

uavs= [4,5,11, 14, 13]

for index, battery in enumerate(battery_levels):
    if index in uavs:
        plotFromFirstDataset = plt.plot(steps, battery, linestyle=':',lw=5)
        plt.plot(steps2, battery_levels2[index], color=plotFromFirstDataset[0]._color, linestyle='-', lw=5, label=index)

# for index, battery in enumerate(battery_levels2):
#     if index in uavs:
#         plt.plot(steps2, battery, linestyle='-',lw=5)
# plt.legend(loc="upper right", bbox_to_anchor=(1.01, 1.175), ncol=2)
plt.show()
