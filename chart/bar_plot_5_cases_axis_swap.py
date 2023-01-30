import matplotlib.pyplot as plt
import numpy as np

from chart.constant import cb_color_cycle
from sim_data import *

# SCENARIO = "vehicle_v6"
SCENARIO = "request"
ANNOTATE_TEXT_SIZE = 15

values = easy_settings[SCENARIO]["values"].split("\t")
options = easy_settings[SCENARIO]["case_names"]
y_label = easy_settings[SCENARIO]["x_label"]
# create data
y = np.arange(3)
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

plt.rcParams["font.size"] = "20"
plt.rcParams["font.family"] = "Times"

width = 0.18

# plot data in grouped manner of bar type
plt.barh(y + 2 * width, q_opt, width, color=cb_color_cycle[3], hatch='/', edgecolor='black')
plt.annotate(f"{q_opt[0]:.1f}", (q_opt[0], y[0] + 1.65 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.annotate(f"{q_opt[1]:.1f}", (q_opt[1], y[1] + 1.65 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.annotate(f"{q_opt[2]:.1f}", (q_opt[2], y[2] + 1.65 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.barh(y + width, adp, width, color=cb_color_cycle[2], hatch='/', edgecolor='black')
for i, value_text in enumerate(adp):
    plt.annotate(f"{value_text:.1f}", (adp[i], y[i] + 0.65 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.barh(y, agg_2, width, color=cb_color_cycle[1], edgecolor='black')
plt.annotate(f"{agg_2[0]:.1f}", (agg_2[0], y[0] - 0.35 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.annotate(f"{agg_2[1]:.1f}", (agg_2[1], y[1] - 0.35 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.annotate(f"{agg_2[2]:.1f}", (agg_2[2], y[2] - 0.35 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.barh(y - width, agg_1, width, color=cb_color_cycle[0], hatch='\\', edgecolor='black')
for i, value_text in enumerate(agg_1):
    plt.annotate(f"{value_text:.1f}", (agg_1[i], y[i] - 1.35 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.barh(y - 2 * width, only_cloud, width, color=cb_color_cycle[4], edgecolor='black')
plt.annotate(f"{only_cloud[0]:.1f}", (only_cloud[0], y[0] - 2.35 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.annotate(f"{only_cloud[1]:.1f}", (only_cloud[1], y[1] - 2.35 * width), fontsize=ANNOTATE_TEXT_SIZE)
plt.annotate(f"{only_cloud[2]:.1f}", (only_cloud[2], y[2] - 2.35 * width), fontsize=ANNOTATE_TEXT_SIZE)

plt.yticks(y, options)
plt.tick_params(axis='y',direction='out', length=2, width=0, grid_alpha=0.5)

plt.ylabel(y_label)
plt.xlabel(r'$\mathbb{D}$ (s)', size="16")
# plt.legend(['Q-OPT', 'ADP', 'AGG-2', 'AGG-1', 'Only-Cloud'], loc='upper left', edgecolor="black",
#            bbox_to_anchor=(0.114, 0.9), fontsize=12)
plt.legend(['Q-OPT', 'ADP', 'AGG-2', 'AGG-1', 'Only-Cloud'], edgecolor="black", fontsize=11)
plt.xlim(0, 100)
plt.grid(axis="x", alpha=0.4)
plt.savefig(f"plots/{SCENARIO}_vs_objective_function.pdf", dpi=300, bbox_inches='tight')

plt.show()
