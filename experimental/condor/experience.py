#!/usr/bin/env python
__author__ = 'greghines'
import numpy as np
import os
import pymongo
import sys
import cPickle as pickle
import bisect
import csv
import matplotlib.pyplot as plt
import random
import math
import urllib
import matplotlib.cbook as cbook
from IPy import IP
from scipy.stats.stats import pearsonr

def index(a, x):
    'Locate the leftmost value exactly equal to x'
    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    raise ValueError

if os.path.exists("/home/ggdhines"):
    sys.path.append("/home/ggdhines/PycharmProjects/reduction/experimental/clusteringAlg")
    sys.path.append("/home/ggdhines/PycharmProjects/reduction/experimental/classifier")
else:
    sys.path.append("/home/greg/github/reduction/experimental/clusteringAlg")
    sys.path.append("/home/greg/github/reduction/experimental/classifier")
#from divisiveDBSCAN import DivisiveDBSCAN
from divisiveDBSCAN_multi import DivisiveDBSCAN
from divisiveKmeans import DivisiveKmeans
from iterativeEM import IterativeEM

if os.path.exists("/home/ggdhines"):
    base_directory = "/home/ggdhines"
else:
    base_directory = "/home/greg"

client = pymongo.MongoClient()
db = client['condor_2014-11-23']
classification_collection = db["condor_classifications"]
subject_collection = db["condor_subjects"]
user_collection = db["condor_users"]


def individual_confusion(individual_votes,plurality_results):
    confusion_results = []
    for u_index,a_index,a_type in individual_votes:
        while len(confusion_results) < (u_index+1):
            confusion_results.append([[0. for i in range(len(animals))] for j in range(len(animals))])

        plurality = plurality_results[a_index]
        confusion_results[u_index][a_type][plurality] += 1

    for conf_index in range(len(confusion_results)):
        for row_index in range(len(animals)):
            #if greater than zero
            if max(confusion_results[conf_index][row_index]) > 0:
                row = confusion_results[conf_index][row_index]
                confusion_results[conf_index][row_index] = [c/sum(row) for c in row]

    return confusion_results



big_userList = []
big_subjectList = []
animal_count = 0

f = open(base_directory+"/Databases/condor_ibcc.csv","wb")
f.write("a,b,c\n")
alreadyDone = []
animals_in_image = {}
animal_index = -1
global_user_list = []
animal_to_image = []
zooniverse_list = []
condor_votes = {}
animal_votes = []
#subject_vote = {}
results = []
gold_values = {}

to_sample_from = list(subject_collection.find({"state":"complete"}))
#to_sample_from2 = list(subject_collection.find({"classification_count":1,"state":"active"}))

votes = []

sample = random.sample(to_sample_from,500)
#sample.extend(random.sample(to_sample_from2,1000))
# for subject_index,subject in enumerate(sample):
#     print "== " + str(subject_index)
#     zooniverse_id = subject["zooniverse_id"]
#     for user_index,classification in enumerate(classification_collection.find({"subjects.zooniverse_id":zooniverse_id})):
#         if "user_name" in classification:
#             user = classification["user_name"]
#         else:
#             user = classification["user_ip"]
#
#         try:
#             tt = index(big_userList,user)
#         except ValueError:
#             bisect.insort(big_userList,user)
#print [subject["zooniverse_id"] for subject in sample]
animals = ["condor","turkeyVulture","goldenEagle","raven","coyote"]

#zooniverse_list = [u'ACW00009f3', u'ACW0002spl', u'ACW0000srp', u'ACW0000vmr', u'ACW000162q', u'ACW00046vx', u'ACW0000ksg', u'ACW00007kj', u'ACW0000mh3', u'ACW0004qkl', u'ACW0000k83', u'ACW00005d6', u'ACW0001b1v', u'ACW0000dmx', u'ACW0001hea', u'ACW0000ii0', u'ACW00048k0', u'ACW0001vyr', u'ACW00004ct', u'ACW0000c90', u'ACW00015nn', u'ACW0000umz', u'ACW00001x7', u'ACW0000bxy', u'ACW00000qt', u'ACW0000u40', u'ACW0001oqg', u'ACW0000tku', u'ACW0003lrk', u'ACW0002fz4', u'ACW00017yd', u'ACW0000o8o', u'ACW0000sj7', u'ACW0000w7i', u'ACW0000wtm', u'ACW0004isy', u'ACW0000g9s', u'ACW00008vi', u'ACW0000n2y', u'ACW0000fny', u'ACW0000cas', u'ACW0000q9x', u'ACW000148e', u'ACW0000vvf', u'ACW0000piz', u'ACW000133j', u'ACW0000obu', u'ACW0000tl4', u'ACW0000kpg', u'ACW0002fi4', u'ACW0001rcw', u'ACW00015t1', u'ACW0003czs', u'ACW0003wzn', u'ACW00006us', u'ACW0000jtg', u'ACW00009xd', u'ACW0000dki', u'ACW0001wos', u'ACW00011mv', u'ACW0000rqu', u'ACW00022q0', u'ACW0000egm', u'ACW00006pi', u'ACW0000vkc', u'ACW0000n68', u'ACW00013tw', u'ACW00001rj', u'ACW0000hiw', u'ACW0000hwo', u'ACW00038ee', u'ACW0000a8s', u'ACW0000t7i', u'ACW0002avi', u'ACW0000uou', u'ACW000089l', u'ACW0000wla', u'ACW00007wj', u'ACW00019kf', u'ACW0000ihd', u'ACW00007uk', u'ACW0000gk2', u'ACW0002mvd', u'ACW0000k0r', u'ACW0002345', u'ACW0002nv4', u'ACW00013fg', u'ACW0001311', u'ACW00011am', u'ACW000048d', u'ACW0000f8f', u'ACW00008ib', u'ACW0000ccd', u'ACW00015li', u'ACW00031rs', u'ACW0000my8', u'ACW0001bb1', u'ACW0002psg', u'ACW0000pqn', u'ACW0000z26']

for subject_index,subject in enumerate(sample):
    print subject_index
    zooniverse_id = subject["zooniverse_id"]
#for subject_index,zooniverse_id in enumerate(zooniverse_list):
    #print subject_index
    annotation_list = []
    user_list = []
    animal_list = []
    #local_users = []
    labelled = []

    for user_index,classification in enumerate(classification_collection.find({"subjects.zooniverse_id":zooniverse_id})):
        try:
            mark_index = [ann.keys() for ann in classification["annotations"]].index(["marks",])
            markings = classification["annotations"][mark_index].values()[0]

            if "user_name" in classification:
                user = classification["user_name"]
            else:
                user = classification["user_ip"]
            found_condor = False

            for animal in markings.values():
                scale = 1.875
                x = scale*float(animal["x"])
                y = scale*float(animal["y"])

                animal_type = animal["animal"]
                if not(animal_type in ["carcassOrScale","carcass","other",""]):
                    annotation_list.append((x,y))
                    #print annotation_list
                    user_list.append(user)
                    animal_list.append(animal_type)
                    if not(user in global_user_list):
                        global_user_list.append(user)
                    #local_users.append(user)


                    labelled.append("label" in animal)


        except (ValueError,KeyError):
            pass

    #if there were any markings on the image, use divisive kmeans to cluster the points so that each
    #cluster represents an image
    if annotation_list != []:
        user_identified,clusters = DivisiveKmeans(3).fit2(annotation_list,user_list,debug=True)

        #fix split clusters if necessary
        if user_identified != []:
            user_identified,clusters = DivisiveKmeans(3).__fix__(user_identified,clusters,annotation_list,user_list,200)

            for center,c in zip(user_identified,clusters):
                animal_index += 1
                animal_votes.append([])
                animal_to_image.append(zooniverse_id)

                if not(zooniverse_id in animals_in_image):
                    animals_in_image[zooniverse_id] = [animal_index]
                else:
                    animals_in_image[zooniverse_id].append(animal_index)

                results.append((zooniverse_id,center))
                # if sum([1 for pt in c if labelled[annotation_list.index(pt)]])/float(len(c)) > 0.75:
                #     gold_values[animal_index] = 0
                #     print '**'

                for pt in c:

                    pt_index = annotation_list.index(pt)
                    user_index = global_user_list.index(user_list[pt_index])
                    animal_type = animal_list[annotation_list.index(pt)]

                    votes.append((user_index,animal_index,animals.index(animal_type)))
                    animal_votes[-1].append(animals.index(animal_type))

plurality_vote = [v[np.argmax(v)] for v in animal_votes]

record = {}

for user_index,animal_index,animal_type in votes:
    user_id = global_user_list[user_index]

    zooniverse_id = animal_to_image[animal_index]
    plurality_result = plurality_vote[animal_index]

    if not(user_id in record):
        record[user_id] = {}

    if not(zooniverse_id in record[user_id]):
        record[user_id][zooniverse_id] = []

    if (plurality_result == 0) or (animal_type == 0):
        if (animal_type == plurality_result):
            record[user_id][zooniverse_id].append(1)
        else:
            record[user_id][zooniverse_id].append(0)

X = []
Y = []

for user_id in record:
    ability = np.mean([np.mean(r) for r in record[user_id].values()])

    try:
        IP(user_id)
        user = user_collection.find_one({"ip":user_id})
    except ValueError:
        user = user_collection.find_one({"name":user_id})

    try:
        count = user["classification_count"]

    except (TypeError,KeyError):
        print user
        continue

    X.append(count)
    Y.append(ability)

print pearsonr(X,Y)

plt.plot(X,Y,'.')
plt.xscale('log')
plt.ylim((-0.05,1.05))
plt.show()