#!/usr/bin/env python
from __future__ import print_function
import csv
import pymongo
from itertools import chain, combinations
import shutil
import os
import sys
sys.path.append("/home/ggdhines/github/pyIBCC/python")
import ibcc


def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

class IBCC:
    def __init__(self):
        self.client = pymongo.MongoClient()
        self.db = self.client['serengeti_2014-05-13']

        self.species_groups = [["gazelleThomsons","gazelleGrants"],]
        self.speciesList = ['elephant','zebra','warthog','impala','buffalo','wildebeest','gazelleThomsons','dikDik','giraffe','gazelleGrants','lionFemale','baboon','hippopotamus','ostrich','human','otherBird','hartebeest','secretaryBird','hyenaSpotted','mongoose','reedbuck','topi','guineaFowl','eland','aardvark','lionMale','porcupine','koriBustard','bushbuck','hyenaStriped','jackal','cheetah','waterbuck','leopard','reptiles','serval','aardwolf','vervetMonkey','rodents','honeyBadger','batEaredFox','rhinoceros','civet','genet','zorilla','hare','caracal','wildcat']

        self.cutoff = 5

        self.user_list = None
        self.subject_list = None

    def __csv_in__(self):
        #check to see if this collection already exists (for this particular cutoff) - if so, skip
        db = self.client["system"]
        collection = db["namespace"]

        if ('merged_classifications'+str(self.cutoff)) in self.db.collection_names():
            print("mongoDB collection already exists")
            return

        reader = csv.reader(open("/home/ggdhines/Databases/serengeti/goldFiltered.csv", "rb"), delimiter=",")
        next(reader, None)

        curr_name = None
        curr_id = None
        species_list = []


        collection = self.db['merged_classifications'+str(self.cutoff)]

        zooniverse_id_count = {}

        count = 0

        for row in reader:
            user_name = row[1]
            subject_zooniverse_id = row[2]
            species = row[11]

            if (user_name != curr_name) or (subject_zooniverse_id != curr_id):
                if not(curr_name is None):
                    if curr_id in zooniverse_id_count:
                        zooniverse_id_count[curr_id] += 1
                    else:
                        zooniverse_id_count[curr_id] = 1

                    if zooniverse_id_count[curr_id] <= self.cutoff:
                        count += 1
                        document = {"user_name": curr_name, "subject_zooniverse_id": curr_id, "species_list": species_list}
                        collection.insert(document)

                curr_name = user_name[:]
                species_list = []
                curr_id = subject_zooniverse_id[:]

            species_list.append(species)

        document = {"user_name": curr_name, "subject_zooniverse_id": curr_id, "species_list": species_list}
        collection.insert(document)

    def __createConfigFile(self,counter,numClasses):
        f = open("/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+"config.py",'wb')
        print("import numpy as np\nscores = np.array("+str(range(numClasses))+")", file=f)
        print("nScores = len(scores)", file=f)
        print("nClasses = "+str(numClasses),file=f)
        print("inputFile = '/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+".in'", file=f)
        print("outputFile =  '/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+".out'", file=f)
        print("confMatFile = '/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+".mat'", file=f)
        print("alpha0 = np.array([[2, 1, 1, 1], [1, 2, 1, 1], [1, 1, 2, 1], [1, 1, 1, 2]])", file=f)
        print("nu0 = np.array([25.0, 25.0, 25.0, 25.0])", file=f)
        f.close()

    def __analyze_results__(self):
        #read in the experts' classifications
        try:
            f = open("NA.csv", 'rb')
        except IOError:
            f = open("/home/ggdhines/Databases/serengeti/expert_classifications_raw.csv", "rU")

        reader = csv.reader(f, delimiter=",")
        next(reader, None)
        expertClassifications = {}

        for row in reader:
            photoStr = row[2]
            speciesStr = row[12]

            subjectID = self.subject_list.index(photoStr)

            #is this the first time we've encountered this photo?
            if not(subjectID in expertClassifications):
                expertClassifications[subjectID] = []

            #add an species if ANY of the experts tag it, for the most part photos are only classified by one
            #expert, so shouldn't be a problem
            if not(speciesStr in expertClassifications[subjectID]):
                expertClassifications[subjectID].append(speciesStr)


        #to save having to repeatedly read through the experts' classifications, read them all in now
        classificationReader = csv.reader(open('/home/ggdhines/Databases/serengeti/expert_classifications_raw.csv', 'rU'), delimiter=',')
        next(classificationReader, None)
        for row in classificationReader:
            photoID = row[2]
            photoIndex = self.photoMappings.index(photoID)
            species = row[12]

        #start off by assuming that we have classified all photos correctly
        correct_classification = [True for i in range(len(expertClassifications.keys()))]

        counter = -1

        #go through each of the species groups, get the user predictions and compare them to the experts' predictions
        for speciesGroup in self.species_groups:
            #find all of the possible subgroups
            required_l = list(powerset(speciesGroup))
            prohibited_l = [[s for s in speciesGroup if not(s in r)] for r in required_l]

            #open up the prediction file corresponding to the next species group
            counter += 1
            ibcc_output_reader = csv.reader(open("/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+".out","rb"), delimiter=" ")

            #go through each of the prediction
            for row in ibcc_output_reader:
                assert(len(row) == (len(required_l)+1))

                #get the subject ID and the predictions
                subjectID = int(float(row[0]))
                predictions = [float(r) for r in row[1:]]
                predicted_class = predictions.index(max(predictions))

            counter += 1

            #read in each of the aggregated user classification and compare them to the expert classification
            #for each photo, find out which subgroup the experts classified the photo as containing

            for subjectID in range(self.subject_list):
                classification = expertClassifications[subjectID]

                meet_required = [sorted(list(set(classification).intersection(r))) == sorted(list(r)) for r in required_l]
                meet_prohibited = [tuple(set(classification).intersection(p)) == () for p in prohibited_l]

                meet_overall = [r and p for (r, p) in zip(meet_required, meet_prohibited)]
                assert(sum([1. for o in meet_overall if o]) == 1)

                expert_id = meet_overall.index(True)


    def __runIBCC__(self):
        collection = self.db['merged_classifications'+str(self.cutoff)]

        self.user_list = []
        self.subject_list = []

        shutil.rmtree("/home/ggdhines/Databases/serengeti/ibcc")
        os.makedirs("/home/ggdhines/Databases/serengeti/ibcc")

        counter = -1

        for speciesGroup in self.species_groups:
            required_l = list(powerset(speciesGroup))
            prohibited_l = [[s for s in speciesGroup if not(s in r)] for r in required_l]

            counter += 1

            self.__createConfigFile(counter,len(required_l))
            ibcc_input_file = open("/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+".in","wb")


            for document in collection.find():
                user_name = document["user_name"]
                subject_zooniverse_id = document["subject_zooniverse_id"]
                user_species_list = document["species_list"]

                #IBCC requires an int ID for both user and subject - so convert
                if user_name in self.user_list:
                    userID = self.user_list.index(user_name)
                else:
                    self.user_list.append(user_name)
                    userID = len(self.user_list)-1

                if subject_zooniverse_id in self.subject_list:
                    subjectID = self.subject_list.index(subject_zooniverse_id)
                else:
                    self.subject_list.append(subject_zooniverse_id)
                    subjectID = len(self.subject_list)-1

                #which class does this classification count as?
                meet_required = [sorted(list(set(user_species_list).intersection(r))) == sorted(list(r)) for r in required_l]
                meet_prohibited = [tuple(set(user_species_list).intersection(p)) == () for p in prohibited_l]
                meet_overall = [r and p for (r, p) in zip(meet_required, meet_prohibited)]
                assert(sum([1. for o in meet_overall if o]) == 1)

                class_id = meet_overall.index(True)
                print(str(userID) + "," + str(subjectID) + "," + str(class_id), file=ibcc_input_file)

            ibcc_input_file.close()

            #now run IBCC
            ibcc.runIbcc("/home/ggdhines/Databases/serengeti/ibcc/"+str(counter)+"config.py")

f = IBCC()
#f.__csv_in__()
#f.__IBCCoutput__([["gazelleThomsons","gazelleGrants"],])
f.__runIBCC__()