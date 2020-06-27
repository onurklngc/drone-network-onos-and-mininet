from numpy import genfromtxt
import pandas as pd
import os, shutil

simName = "5"

base_dir = "iperf/%s" % simName
outputFile = os.path.join(base_dir, 'all.csv')

if not os.path.isfile(outputFile):
    files = [os.path.join(base_dir, fileName) for fileName in os.listdir(base_dir)]
    with open(outputFile, 'wb') as wfd:
        for f in files:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd, wfd)

df = pd.read_csv(outputFile, header=None)
means = df.mean()
sums = df.sum()
print("Througput mean is: %f" % means[8])
print("Log amount: %d" % df.shape[0])
print("Total data: %d" % sums[7])
# with open("sims/%s/result.json" %simName) as f:
#     jsondata=json.load(f)
# with open("sims/%s/result.csv" %simName, 'w') as f:
#     for key in jsondata.keys():
#         f.write("%s,%s\n"%(key,jsondata[key]))
