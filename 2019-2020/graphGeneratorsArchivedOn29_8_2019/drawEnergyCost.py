import matplotlib.pyplot as plt
import pickle
import numpy as np
plt.rcParams["font.family"] = "Arial"
plt.rcParams["font.size"] = "18"

fileName = "energyCostArray/1.csv"

with open(fileName, 'rb') as fp:
    energyCosts = pickle.load(fp)

steps = np.arange(0, len(energyCosts))


def getMovingAvgArray(sequence, n=10):
    it = iter(sequence)
    movingAvgArray = []
    window = ()
    for i in range(n):
        window += (next(it),)
        movingAvgArray.append(np.mean(window))
    for elem in it:
        window = window[1:] + (elem,)
        movingAvgArray.append(np.mean(window))
    return movingAvgArray


slidingWindow = getMovingAvgArray(energyCosts)

fig, (ax1, ax2) = plt.subplots(2, )
fig.subplots_adjust(hspace =0.3)
ax1.set_xlabel('Request ID', fontsize=25)
ax1.set_ylabel('Energy cost (J)', fontsize=25)
# ax.set_xlim(0, 1070)
# ax.set_ylim(0, 18000)

ax1.scatter(steps, energyCosts, lw=1, label="Energy cost of the flow")
ax1.plot(steps, slidingWindow, lw=1, color="red", label="Moving Average(n=10)")
ax1.legend(loc='upper right', edgecolor="black")  # ,facecolor="wheat")
ax1.set_xlim(0, 1000)
ax1.set_ylim(0, 1000)
ax1.grid()
ax2.hist(energyCosts, bins="auto", density=True, facecolor='g', alpha=0.75, orientation="horizontal")
ax2.set_ylabel('Energy cost (J)', fontsize=25)
ax2.set_xlabel('Frequency', fontsize=25)
ax2.set_ylim(0, 1000)
# ax2.set_xlim(0, 0.1)

ax2.grid()

plt.show()
