import matplotlib.pyplot as plt
import pandas as pd
import pickle

file_name = "situation-158218302.pkl"
current_time = 0
time_in_sec = 1080
time_in_sec = 600

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "32"
fig, ax = plt.subplots()

with open(file_name, 'rb') as handle:
    results = pickle.load(handle)
# energy_consumption_statistics = np.load(file_name)
energy_consumption_statistics = results[time_in_sec]['energy_consumption_statistics']

labels = ['Fly', 'Tx', 'Write', 'Read']

# Data
r = [a for a in range(energy_consumption_statistics.shape[0])]
raw_data = {'fly': energy_consumption_statistics[:, 0], 'tx': energy_consumption_statistics[:, 1],
            'read': energy_consumption_statistics[:, 2],
            'write': energy_consumption_statistics[:, 3]}
df = pd.DataFrame(raw_data)

# From raw value to percentage
totals = [i + j + k + l for i, j, k, l in zip(df['tx'], df['read'], df['write'], df['fly'])]
tx_bars = [i / j * 100 for i, j in zip(df['tx'], totals)]
read_bars = [i / j * 100 for i, j in zip(df['read'], totals)]
write_bars = [i / j * 100 for i, j in zip(df['write'], totals)]
fly_bars = [i / j * 100 for i, j in zip(df['fly'], totals)]

# plot
bar_width = 0.85
names = [str(a) for a in r]
# Create orange Bars
plt.bar(r, fly_bars, color='#e07604', width=bar_width)
# Create blue Bars
plt.bar(r, tx_bars, bottom=fly_bars, color='#a3acff', width=bar_width)
# Create green Bars
plt.bar(r, write_bars, bottom=[i + j for i, j in zip(tx_bars, fly_bars)], color='#b5ffb9',
        width=bar_width)
# Create red Bars
plt.bar(r, read_bars, bottom=[i + j + k for i, j, k in zip(tx_bars, fly_bars, write_bars)], color='red',
        width=bar_width)
plt.legend(labels, loc='upper right', ncol=4, bbox_to_anchor=(1.015, 1.175))
fig.subplots_adjust(bottom=0.13, top=0.88, left=0.05, right=0.9,
                    wspace=0.02, hspace=0.02)
# Custom x axis
plt.xticks(r, names)
plt.xlabel("UAV ID")

# Show graphic
plt.show()
