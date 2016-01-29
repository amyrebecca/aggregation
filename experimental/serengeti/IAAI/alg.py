#!/usr/bin/env python
__author__ = 'greg'
from nodes import setup, speciesList
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats.stats import pearsonr

numUser = [5,10,15,20,25]
algPercent = []
currPercent = []

for i in numUser:
    print i
    algPercent.append([])
    currPercent.append([])
    for j in range(20):
        photos,users = setup(tau=1)

        for p in photos.values():
            p.__sample__(i)
        for u in users.values():
            u.__prune__()

        #initialize things using majority voting
        for p in photos.values():
            p.__majorityVote__()

        for k in range(1):
            #estimate the user's "correctness"
            for u in users.values():
                for s in speciesList:
                    u.__speciesCorrect__(s,beta=0.01)

            for p in photos.values():
                p.__weightedMajorityVote__()

        correct = 0
        total = 0.
        for p in photos.values():
            if p.__goldStandardCompare__():
                correct += 1
            total += 1

        algPercent[-1].append(correct/total)

        # for p in photos.values():
        #     p.__currAlg__()
        #
        # correct = 0
        # total = 0.
        # for p in photos.values():
        #     if p.__goldStandardCompare__():
        #         correct += 1
        #     total += 1
        #
        # currPercent[-1].append(correct/total)

meanValues = [np.mean(p)*100 for p in algPercent]
std = [np.std(p)*100 for p in algPercent]
plt.errorbar(numUser, meanValues, yerr=std,fmt="-o",color="black")

#meanValues = [np.mean(p) for p in currPercent]
#std = [np.std(p) for p in currPercent]
#plt.errorbar(numUser, meanValues, yerr=std)
plt.plot([5,25],[96.4,96.4],"--", color="grey")

#plt.legend(("Our Algorithm","Current Algorithm"), "lower right")
plt.xlabel("Number of Users per Photo")
plt.ylabel("Accuracy (%)")

plt.xlim((4,26))
plt.ylim((93,100))
plt.show()

