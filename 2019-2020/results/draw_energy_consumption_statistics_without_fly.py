import matplotlib.pyplot as plt
import pandas as pd
import pickle

file_name = "situation-158213001.pkl"
current_time = 0
time_in_sec = 660

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "32"
fig, ax = plt.subplots()

with open(file_name, 'rb') as handle:
    results = pickle.load(handle)
# energy_consumption_statistics = np.load(file_name)
energy_consumption_statistics = results[time_in_sec]['energy_consumption_statistics']


labels = ['Tx', 'Write', 'Read']

# Data
r = [a for a in range(energy_consumption_statistics.shape[0])]
raw_data = {'fly': energy_consumption_statistics[:, 0], 'tx': energy_consumption_statistics[:, 1],
            'read': energy_consumption_statistics[:, 2],
            'write': energy_consumption_statistics[:, 3]}
df = pd.DataFrame(raw_data)

# From raw value to percentage
totals = [i + j + k for i, j, k in zip(df['tx'], df['read'], df['write'])]
tx_bars = [i / j * 100 for i, j in zip(df['tx'], totals)]
read_bars = [i / j * 100 for i, j in zip(df['read'], totals)]
write_bars = [i / j * 100 for i, j in zip(df['write'], totals)]


# redBars = [i / j * 100 for i, j in zip(df['fly'], totals)]


def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width() / 2., 1.05 * height,
                '%d' % int(height),
                ha='center', va='bottom')


# plot
bar_width = 0.85
names = [str(a) for a in r]
# Create green Bars
green_bar_object = plt.bar(r, tx_bars, color='#a3acff', width=bar_width)
# Create orange Bars
orange_bar_object = plt.bar(r, write_bars, bottom=tx_bars, color='#b5ffb9', width=bar_width)
# Create blue Bars
blue_bar_object = plt.bar(r, read_bars, bottom=[i + j for i, j in zip(tx_bars, write_bars)], color='red', width=bar_width)

# autolabel(green_bar_object)
# autolabel(orange_bar_object)
# autolabel(blue_bar_object)
plt.legend(labels, loc='upper right', ncol=4, bbox_to_anchor=(1.015, 1.175))
fig.subplots_adjust(bottom=0.13, top=0.88, left=0.05, right=0.9,
                    wspace=0.02, hspace=0.02)
# Custom x axis
plt.xticks(r, names)
plt.xlabel("UAV ID")

# Show graphic
plt.show()
