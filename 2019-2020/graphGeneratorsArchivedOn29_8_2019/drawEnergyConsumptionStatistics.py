import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "18"

fileName = "energyConsumption/10.npy"

energyConsumptionStatistics = np.load(fileName)

labels = ['Fly', 'Tx', 'Read', 'Write']

# Data
r = [a for a in range(energyConsumptionStatistics.shape[0])]
raw_data = {'greenBars': energyConsumptionStatistics[:,0], 'orangeBars': energyConsumptionStatistics[:,1], 'blueBars': energyConsumptionStatistics[:,2],
            'redBars': energyConsumptionStatistics[:,3]}
df = pd.DataFrame(raw_data)

# From raw value to percentage
totals = [i + j + k + l for i, j, k, l in zip(df['greenBars'], df['orangeBars'], df['blueBars'], df['redBars'])]
greenBars = [i / j * 100 for i, j in zip(df['greenBars'], totals)]
orangeBars = [i / j * 100 for i, j in zip(df['orangeBars'], totals)]
blueBars = [i / j * 100 for i, j in zip(df['blueBars'], totals)]
redBars = [i / j * 100 for i, j in zip(df['redBars'], totals)]

# plot
barWidth = 0.85
names = [str(a) for a in r]
# Create green Bars
plt.bar(r, greenBars, color='#b5ffb9', edgecolor='white', width=barWidth)
# Create orange Bars
plt.bar(r, orangeBars, bottom=greenBars, color='#f9bc86', edgecolor='white', width=barWidth)
# Create blue Bars
plt.bar(r, blueBars, bottom=[i + j for i, j in zip(greenBars, orangeBars)], color='#a3acff', edgecolor='white',
        width=barWidth)
# Create red Bars
plt.bar(r, redBars, bottom=[i + j + k for i, j, k in zip(greenBars, orangeBars, blueBars)], color='red',
        edgecolor='white',
        width=barWidth)
plt.legend(labels,loc='lower right')
# Custom x axis
plt.xticks(r, names)
plt.xlabel("UAV ID")

# Show graphic
plt.show()
