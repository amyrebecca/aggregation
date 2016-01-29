#!/usr/bin/env python
__author__ = 'greghines'
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import csv
import sys
import os
import pymongo
import urllib
import matplotlib.cbook as cbook
import math
from PIL import Image

client = pymongo.MongoClient()
db = client['penguin_2014-09-27']
collection = db["penguin_classifications"]
collection2 = db["penguin_subjects"]

zooniverse_id = None
t = 0

if os.path.exists("/home/ggdhines"):
    base_directory = "/home/ggdhines"
else:
    base_directory = "/home/greg"


def matchPoints(pts_gold,pts_user):
    user_to_gold_mapping = [[] for i in range(len(pts_gold))]
    for i_user,p in enumerate(pts_user):
        minimum_distance = float("inf")
        bestPoint = None
        for i_gold,p2 in enumerate(pts_gold):
            dist = math.sqrt((p[0]-p2[0])**2+ (p[1]-p2[1])**2)
            if dist < minimum_distance:
                bestPoint = i_gold
                minimum_distance = dist

        if bestPoint is not None:
            user_to_gold_mapping[bestPoint].append(i_user)

    gold_to_user_mapping = [[] for i in range(len(pts_user))]
    for i_gold,p in enumerate(pts_gold):
        minimum_distance = float("inf")
        bestPoint = None
        for i_user,p2 in enumerate(pts_user):

            dist = math.sqrt((p[0]-p2[0])**2+ (p[1]-p2[1])**2)
            if dist < minimum_distance:
                bestPoint = i_user
                minimum_distance = dist

        if bestPoint is not None:
            gold_to_user_mapping[bestPoint].append(i_gold)

    return user_to_gold_mapping,gold_to_user_mapping

step =0.25
epsilon_range = np.arange(1,200.01,step)#range(4,51,1)
points_range = [1,2,3,4,5,6,7,8,9]

def createRanges(pts):
    X_ = np.array(pts)
    db_ = DBSCAN(eps=step+0.05, min_samples=1).fit(X_)
    labels = db_.labels_

    ranges = []
    for k in set(labels):
        class_member_mask = (labels == k)
        xy = X_[class_member_mask]

        epsilon_l,minPts = zip(*list(X_[class_member_mask]))
        epsilon_min,epsilon_max = min(epsilon_l),max(epsilon_l)

        assert(min(minPts) == max(minPts))
        ranges.append((minPts[0],epsilon_min,epsilon_max))


    return ranges


def dbscan_search(pts_gold,pts_user,iteration):
    print len(pts_gold)
    #print "===="
    X_ = np.array(pts_user)
    matchings = {}
    numClusters = {}
    for epsilon in epsilon_range: #[5,10,15,20,25,30,35,40,45,50]:
        sys.stdout.write("\r%f" % epsilon)
        sys.stdout.flush()
        for min_num_points in points_range:
            db_ = DBSCAN(eps=epsilon, min_samples=min_num_points).fit(X_)

            labels_ = db_.labels_
            unique_labels_ = set(labels_)

            cluster_centers = []



            for k in unique_labels_:
                class_member_mask = (labels_ == k)
                xy = X_[class_member_mask]
                if k != -1:
                    xSet,ySet = zip(*list(X_[class_member_mask]))
                    x = np.mean(xSet)
                    y = np.mean(ySet)
                    cluster_centers.append((x,y))

            matchings[(epsilon,min_num_points)] = matchPoints(pts_gold,cluster_centers)
            numClusters[(epsilon,min_num_points)] = len(cluster_centers)
            #print str(len(cluster_centers)) + " ",
    print

    good_points = []
    for epsilon in epsilon_range: #[5,10,15,20,25,30,35,40,45,50]:
        for min_num_points in points_range:
            if abs(numClusters[(epsilon,min_num_points)] - len(pts_gold)) <= 1:
                # print (epsilon,min_num_points)
                # print matchings[(epsilon,min_num_points)][0]
                # print matchings[(epsilon,min_num_points)][1]
                #plt.plot(epsilon,min_num_points,'.',color='green')
                good_points.append((epsilon,min_num_points))

    if iteration == 1:
        ranges = createRanges(good_points)

        for p,epsilon_min,epsilon_max in ranges:
            #print p,epsilon_min,epsilin_max
            plt.plot((epsilon_min,epsilon_max),(p,p),color="blue")
            plt.plot((epsilon_min),(p),'o',color="blue")
            plt.plot((epsilon_max),(p),'o',color="blue")

        plt.ylim([0,10])
        plt.show()
    return good_points

overall_good_points = []
toSkip = ["APZ0002p7b","APZ0003261"]
overall_ranges = {}
with open(base_directory + "/Databases/penguin_expert.csv") as f:
    i = 0
    for l in f.readlines():

        user_markings = []
        user_ips = []
        zooniverse_id,gold_standard_pts = l[:-1].split("\t")
        adult_goldstandard,chick_goldstandard = gold_standard_pts.split(":")

        offset = 0
        scale = 1
        if adult_goldstandard == "":
            goldPts = []
        else:
            goldPts =  [(int(p.split(",")[0])/scale-offset,int(p.split(",")[1])/scale-offset) for p in adult_goldstandard.split(";")]

        if chick_goldstandard != "":
            goldPts.extend([(int(p.split(",")[0])/scale-offset,int(p.split(",")[1])/scale-offset) for p in chick_goldstandard.split(";")])


        r = collection2.find_one({"zooniverse_id":zooniverse_id})

        classification_count = r["classification_count"]

        #if zooniverse_id in toSkip:
        #    print "skipping"
        #    continue



        #print zooniverse_id,len(gold_standard_pts.split(";")),classification_count
        original_x,original_y = r["metadata"]["original_size"]["width"],r["metadata"]["original_size"]["height"]
        #print zooniverse_id

        #if zooniverse_id in ["APZ0002p2o","APZ0002p33"]:
        #    continue

        #if classification_count < 8:
            #print "not enough classifications"
        #    continue

        #if i == 5:
        #    break

        #print zooniverse_id


        object_id= str(r["_id"])
        url = r["location"]["standard"]
        image_path = base_directory+"/Databases/penguins/images/"+object_id+".JPG"
        #print object_id



        if not(os.path.isfile(image_path)):
            urllib.urlretrieve(url, image_path)

        im=Image.open(image_path)
        new_x,new_y =  im.size
        scale = original_x/float(new_x)
        #print scale,original_y/float(new_y)
        path = r["metadata"]["path"]

        if not("LOCKb" in path):
            continue
        print path
        if len(gold_standard_pts.split(";")) > 30:
            print "too many points"
            continue
        i += 1
        assert math.fabs(scale - original_y/float(new_y)) <= 0.02
        #goldPts =  [(int(p.split(",")[0])/scale,int(p.split(",")[1])/scale) for p in gold_standard_pts.split(";")[:-1]]

        #image_file = cbook.get_sample_data(base_directory + "/Databases/penguins/images/"+object_id+".JPG")
        #image = plt.imread(image_file)
        #fig, ax = plt.subplots()
        #im = ax.imshow(image)

        #x,y = zip(*goldPts)
        #plt.plot(x,y,'.',color='blue')

        #load volunteer classifications
        numClicks = []
        mostClicks = 0
        xy_overall = None

        for r in collection.find({"subjects" : {"$elemMatch": {"zooniverse_id":zooniverse_id}}}):
            n = 0
            xy_list = []
            try:
                if isinstance(r["annotations"][1]["value"],dict):
                    for marking in r["annotations"][1]["value"].values():
                        if marking["value"] == "adult":
                            x,y = (float(marking["x"]),float(marking["y"]))
                            user_markings.append((x,y))
            except KeyError:
                print r["annotations"]




        # image_file = cbook.get_sample_data(base_directory + "/Databases/penguins/images/"+object_id+".JPG")
        # image = plt.imread(image_file)
        # fig, ax = plt.subplots()
        # im = ax.imshow(image)
        # #x,y = zip(*xy_overall)
        # #plt.plot(x,y,'.',color='blue')
        # x,y = zip(*goldPts)
        # plt.plot(x,y,'.',color='green')
        # plt.show()

        overall_good_points.extend(dbscan_search(goldPts,user_markings,i))
        X_ = np.array(overall_good_points)
        db_ = DBSCAN(eps=0.01, min_samples=i).fit(X_)
        print "=== " + str(sorted(db_.labels_)[-1])

        if i == 5:
            break


        # if overallGoodPts is None:
        #     overallGoodPts = goodPts[:]
        # else:
        #     #print goodPts
        #     overallGoodPts = [p for p in goodPts if p in overallGoodPts]
        # print overallGoodPts
        # #break
        # X = np.array(userPts)
        # db = DBSCAN(eps=15, min_samples=2).fit(X)
        #
        # labels = db.labels_
        # unique_labels = set(labels)
        #
        # for k in unique_labels:
        #     class_member_mask = (labels == k)
        #     xy = X[class_member_mask]
        #     if k != -1:
        #         xSet,ySet = zip(*list(X[class_member_mask]))
        #         x = np.mean(xSet)
        #         y = np.mean(ySet)
        #         plt.plot(x, y, '.', color="green")
        #
        # plt.plot(x,y,'.',color='green')
        # plt.show()
        #break
        #t += 1
            # for p in pts.split(";")[:-1]:
            #     x,y = p.split(",")
            #     gold_standard_pts.append((int(x),int(y)))
            # break


# print zooniverse_id
#
# r = collection2.find_one({"zooniverse_id":zooniverse_id})
# print r
#
# for r in collection.find({"subjects" : {"$elemMatch": {"zooniverse_id":zooniverse_id}}}):
#     print r
