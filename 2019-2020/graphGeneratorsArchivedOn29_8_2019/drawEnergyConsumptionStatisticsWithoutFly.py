import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "18"
fig, ax = plt.subplots()
fileName = "energyConsumption/10.npy"

energyConsumptionStatistics = np.load(fileName)

labels = ['Tx', 'Read', 'Write']

# Data
r = [a for a in range(energyConsumptionStatistics.shape[0])]
raw_data = {'fly': energyConsumptionStatistics[:,0], 'tx': energyConsumptionStatistics[:,1], 'read': energyConsumptionStatistics[:,2],
            'write': energyConsumptionStatistics[:,3]}
df = pd.DataFrame(raw_data)

# From raw value to percentage
totals = [i + j + k for i, j, k in zip(df['tx'], df['read'], df['write'])]
greenBars = [i / j * 100 for i, j in zip(df['tx'], totals)]
redBars = [i / j * 100 for i, j in zip(df['read'], totals)]
blueBars = [i / j * 100 for i, j in zip(df['write'], totals)]
# redBars = [i / j * 100 for i, j in zip(df['fly'], totals)]


def autolabel(rects):
    """
    Attach a text label above each bar displaying its height
    """
    for rect in rects:
        height = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., 1.05*height,
                '%d' % int(height),
                ha='center', va='bottom')



# plot
barWidth = 0.85
names = [str(a) for a in r]
# Create green Bars
greenBarObject= plt.bar(r, greenBars, color='#b5ffb9', edgecolor='white', width=barWidth)
# Create orange Bars
orangeBarObject= plt.bar(r, redBars, bottom=greenBars, color='red', edgecolor='white', width=barWidth)
# Create blue Bars
blueBarObject= plt.bar(r, blueBars, bottom=[i + j for i, j in zip(greenBars, redBars)], color='#a3acff', edgecolor='white',
                       width=barWidth)

# autolabel(green_bar_object)
# autolabel(orange_bar_object)
# autolabel(blue_bar_object)
plt.legend(labels,loc='lower right')

# Custom x axis
plt.xticks(r, names)
plt.xlabel("UAV ID")

# Show graphic
plt.show()
