import matplotlib.pyplot as plt
import numpy as np

from chart.constant import cb_color_cycle
from sim_data import *

SCENARIO = "request"
values = easy_settings[SCENARIO]["values"].split("\t")
options = easy_settings[SCENARIO]["case_names"]
x_label = easy_settings[SCENARIO]["x_label"]
# create data
x = np.arange(3)
q_opt = []
adp = []
agg_1 = []
agg_2 = []
for i in range(3):
    q_opt.append(float(values[i * 4]))
    adp.append(float(values[i * 4 + 1]))
    agg_1.append(float(values[i * 4 + 3]))
    agg_2.append(float(values[i * 4 + 2]))

plt.rcParams["font.size"] = "36"
plt.rcParams["font.family"] = "Times"

width = 0.2

# plot data in grouped manner of bar type
plt.bar(x - 3 * width / 2, agg_1, width, color=cb_color_cycle[0])
plt.bar(x - width / 2, agg_2, width, color=cb_color_cycle[1], hatch='\\')
plt.bar(x + width / 2, adp, width, color=cb_color_cycle[2])
plt.bar(x + 3 * width / 2, q_opt, width, color=cb_color_cycle[3], hatch='/')
plt.xticks(x, options)
plt.xlabel(x_label)
plt.ylabel(r'$\mathbb{D}$ (s)', size="50")
plt.legend(['AGG-1', 'AGG-2', 'ADP', 'Q-OPT'])
plt.grid()
plt.show()
