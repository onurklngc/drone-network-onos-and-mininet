import matplotlib.pyplot as plt
import pickle
import numpy as np

file_name = "situation-158206676.pkl"
time_in_sec = 1080
time_in_sec = 660
plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "24"

with open(file_name, 'rb') as fp:
    results = pickle.load(fp)

energy_costs = results[time_in_sec]['energy_cost_matrix']
hop_counts = results[time_in_sec]['flow_hop_matrix']
steps = np.arange(0, len(energy_costs))


# def getMovingAvgArray(sequence, n=10):
#     it = iter(sequence)
#     movingAvgArray = []
#     window = ()
#     for i in range(n):
#         window += (next(it),)
#         movingAvgArray.append(np.mean(window))
#     for elem in it:
#         window = window[1:] + (elem,)
#         movingAvgArray.append(np.mean(window))
#     return movingAvgArray
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


sliding_window = get_moving_avg_array_skip_zeros(energy_costs)

fig, (ax1, ax2) = plt.subplots(2, )
fig.subplots_adjust(hspace=0.3)
ax1.set_xlabel('Request ID', fontsize=25)
ax1.set_ylabel('Energy cost (J)', fontsize=25)

ax1b = ax1.twinx()
color = 'tab:orange'
ax1b.set_ylabel('Hop count', color=color)  # we already handled the x-label with ax1
lns1 = ax1b.scatter(steps, hop_counts, marker="*", color=color, label='Hop count')
ax1b.tick_params(axis='y', labelcolor=color)
ax1b.set_ylim(0, 12)

lns2 = ax1.scatter(steps, energy_costs, lw=1, color="green", label="Energy cost of a flow (J)")
lns3 = ax1.plot(steps, sliding_window, lw=2, color="blue", label="Moving average of energy costs(n=10)")

fig.legend(loc='upper right', edgecolor="black", bbox_to_anchor=(0.91, 1))
# ax1.legend(loc='upper right', edgecolor="black")  # ,facecolor="wheat")
ax1.set_xlim(0, 930)
ax1.set_ylim(0, 1000)
ax1.grid()
zero_costs_removed_energy_costs = [cost for cost in energy_costs if cost != 0]
ax2.hist(zero_costs_removed_energy_costs, bins=16, facecolor='g', alpha=0.75, orientation="horizontal",
         weights=np.ones_like(zero_costs_removed_energy_costs) / float(len(zero_costs_removed_energy_costs)))
ax2.set_ylabel('Energy cost (J)', fontsize=25)
ax2.set_xlabel('Frequency', fontsize=25)
ax2.set_ylim(0, 1000)
# ax2.set_xlim(0, 0.1)
ax2.grid()
fig.subplots_adjust(bottom=0.11, top=0.77, left=0.12, right=0.90,
                    wspace=0.2, hspace=0.4)
plt.show()
