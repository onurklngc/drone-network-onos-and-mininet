import logging

import matplotlib.pyplot as plt
import numpy as np

from chart.utils import get_multiple_files, get_specific_tasks, get_system_delays, get_completed_task_deadlines, \
    get_penalties

# fm = font_manager.json_load(os.path.expanduser("~/.cache/matplotlib/fontlist-v300.json"))

file_paths = {
    "Adaptive": "/home/onur/Coding/projects/sdnCaching/results/request_interval/adaptive",
    "Aggressive": "/home/onur/Coding/projects/sdnCaching/results/request_interval/aggressive",
    "Aggressive-Wait": "/home/onur/Coding/projects/sdnCaching/results/request_interval/aggressive-wait",
}

file_name = "situation-158206676.pkl"
time_in_sec = 1080
# plt.rcParams['font.family'] = ['serif']
# plt.rcParams['font.serif'] = ['Times New Roman']
plt.rcParams["font.size"] = "24"


# energy_costs = results[time_in_sec]['energy_cost_matrix']
# hop_counts = results[time_in_sec]['flow_hop_matrix']
# steps = np.arange(0, len(energy_costs))


def get_moving_avg_array_skip_zeros(sequence, n=10):
    it = iter(sequence)
    moving_avg_array = []
    window = ()
    for i in range(n):
        nextCost = next(it)
        if nextCost == 0:
            moving_avg_array.append(moving_avg_array[-1])
            continue
        window += (nextCost,)
        moving_avg_array.append(np.mean(window))
    for elem in it:
        if elem == 0:
            moving_avg_array.append(moving_avg_array[-1])
            continue
        window = window[1:] + (elem,)
        moving_avg_array.append(np.mean(window))
    return moving_avg_array


def plot_graph(tasks):
    system_delays = get_system_delays(tasks)
    deadlines = get_completed_task_deadlines(tasks)
    penalties = get_penalties(tasks)

    steps = np.arange(0, len(system_delays))

    sliding_window = get_moving_avg_array_skip_zeros(system_delays)

    fig, (ax1, ax2) = plt.subplots(2, )
    fig.subplots_adjust(hspace=0.3)
    ax1.set_xlabel('Task ID', fontsize=25)
    ax1.set_ylabel('System delay (s)', fontsize=25)

    ax1b = ax1.twinx()
    color = 'tab:orange'
    ax1b.set_ylabel('Deadline', color=color)  # we already handled the x-label with ax1
    lns1 = ax1b.scatter(steps, deadlines, marker="o", color=color, label='Deadline')
    ax1b.tick_params(axis='y', labelcolor=color)
    ax1b.set_ylim(0, 400)

    lns2 = ax1.scatter(steps, system_delays, lw=1, color="green", label="System delay (s)")
    lns3 = ax1.plot(steps, sliding_window, lw=2, color="blue", label="Moving average of system delays(n=10)")

    fig.legend(loc='upper right', edgecolor="black", bbox_to_anchor=(0.91, 1))
    # ax1.legend(loc='upper right', edgecolor="black")  # ,facecolor="wheat")
    ax1.set_xlim(0, len(system_delays))
    ax1.set_ylim(0, 400)
    ax1.grid()
    negatives_removed_penalties = [penalty for penalty in penalties if penalty >= 0]
    ax2.hist(negatives_removed_penalties, bins=16, facecolor='g', alpha=0.75, orientation="horizontal",
             weights=np.ones_like(negatives_removed_penalties) / float(len(negatives_removed_penalties)))
    ax2.set_ylabel('System delay (s)', fontsize=25)
    ax2.set_xlabel('Frequency', fontsize=25)
    ax2.set_ylim(0, 300)
    # ax2.set_xlim(0, 0.1)
    ax2.grid()
    fig.subplots_adjust(bottom=0.11, top=0.77, left=0.12, right=0.90,
                        wspace=0.2, hspace=0.4)
    plt.show()


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, "INFO"), format="%(asctime)s %(levelname)s -> %(message)s")
    result_data = get_multiple_files(file_paths)
    adaptive_tasks = get_specific_tasks(result_data, "Adaptive", "15")
    adaptive_tasks.sort(key=lambda x: x.no)
    plot_graph(adaptive_tasks)
    adaptive_tasks = get_specific_tasks(result_data, "Adaptive", "10")
    adaptive_tasks.sort(key=lambda x: x.no)
    plot_graph(adaptive_tasks)
    # aggressive_tasks = get_specific_tasks(result_data, "Aggressive", "5")
    # adaptive_tasks.sort(key=lambda x: x.no)
    #
    #
    # aggressive_queue_tasks = get_specific_tasks(result_data, "Aggressive-Wait", "5")
    # adaptive_tasks.sort(key=lambda x: x.no)