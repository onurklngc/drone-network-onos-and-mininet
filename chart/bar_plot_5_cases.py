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
only_cloud = []
for i in range(3):
    q_opt.append(float(values[i * 5]))
    adp.append(float(values[i * 5 + 1]))
    agg_1.append(float(values[i * 5 + 3]))
    agg_2.append(float(values[i * 5 + 2]))
    only_cloud.append(float(values[i * 5 + 4]))

plt.rcParams["font.size"] = "18"
plt.rcParams["font.family"] = "Times"

width = 0.18

# plot data in grouped manner of bar type
plt.bar(x - 2 * width, only_cloud, width, color=cb_color_cycle[4], edgecolor='black')
plt.bar(x - width, agg_1, width, color=cb_color_cycle[0], hatch='\\', edgecolor='black')
plt.bar(x, agg_2, width, color=cb_color_cycle[1], edgecolor='black')
plt.bar(x + width, adp, width, color=cb_color_cycle[2], hatch='/', edgecolor='black')
plt.bar(x + 2 * width, q_opt, width, color=cb_color_cycle[3], hatch='/', edgecolor='black')
plt.xticks(x, options)
plt.xlabel(x_label)
plt.ylabel(r'$\mathbb{D}$ (s)', size="24")
plt.legend(["Only-Cloud", 'AGG-1', 'AGG-2', 'ADP', 'Q-OPT'])
plt.grid()
plt.savefig("plots/SCENARIO.pdf", dpi=300, bbox_inches='tight')

plt.show()
