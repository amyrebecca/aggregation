__author__ = 'ggdhines'
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cbook as cbook
import six
from matplotlib import colors
import math

class DivisiveKmeans_2:
    def __init__(self, min_samples):
        self.min_samples = min_samples

    def __fix__(self,centers,clusters,pts,user_list,threshold,f_name=None):
        while True:
            relations = self.calc_relations(centers,clusters,pts,user_list,threshold)
            if relations == []:
                break

            overlap = relations[0][1]



            c1_index = relations[0][2]
            c2_index = relations[0][3]

            #make sure to pop in the right order so else the indices will get messed up
            if c2_index > c1_index:
                cluster_1 = clusters.pop(c2_index)
                cluster_2 = clusters.pop(c1_index)

                cent_1 = centers.pop(c2_index)
                cent_2 = centers.pop(c1_index)
            else:
                cluster_1 = clusters.pop(c1_index)
                cluster_2 = clusters.pop(c2_index)

                cent_1 = centers.pop(c1_index)
                cent_2 = centers.pop(c2_index)

            # image_file = cbook.get_sample_data(f_name)
            # image = plt.imread(image_file)
            # fig, ax = plt.subplots()
            # im = ax.imshow(image)
            #
            # plt.plot((cent_1[0],cent_2[0]),(cent_1[1],cent_2[1]),'.',color='yellow')
            #
            # plt.show()

            if overlap != []:
                assert(len(overlap) == 1)
                overlap_user = overlap[0]
                p1 = [p for p in cluster_1 if user_list[pts.index(p)] == overlap_user][0]
                p2 = [p for p in cluster_2 if user_list[pts.index(p)] == overlap_user][0]

                #we need to merge these two points so first remove them from the list
                #both the overall list and the two for the individual clusters
                cluster_1.remove(p1)
                cluster_2.remove(p2)
                p1_index = pts.index(p1)
                p2_index = pts.index(p2)
                #since each user may have multiple points in the list we need to remove by index and not by value
                if p2_index > p1_index:
                    pts.pop(p2_index)
                    user_list.pop(p2_index)
                    pts.pop(p1_index)
                    user_list.pop(p1_index)
                else:
                    pts.pop(p1_index)
                    user_list.pop(p1_index)
                    pts.pop(p2_index)
                    user_list.pop(p2_index)

                avg_pt = ((p1[0]+p2[0])/2.,(p1[1]+p2[1])/2.)
                pts.append(avg_pt)
                user_list.append(overlap_user)

                new_cluster = cluster_1[:]
                new_cluster.extend(cluster_2)
                new_cluster.append(avg_pt)
                clusters.append(new_cluster)

                #and update the center
                X,Y = zip(*new_cluster)
                centers.append((np.mean(X),np.mean(Y)))

            else:
                new_cluster = cluster_1[:]
                new_cluster.extend(cluster_2)
                clusters.append(new_cluster)

                #and update the center
                X,Y = zip(*new_cluster)
                centers.append((np.mean(X),np.mean(Y)))

        return centers,clusters

    def calc_relations(self,centers,clusters,pts,user_list,threshold):
        relations = []
        for c1_index in range(len(clusters)):
            for c2_index in range(c1_index+1,len(clusters)):
                c1 = centers[c1_index]
                c2 = centers[c2_index]

                dist = math.sqrt((c1[0]-c2[0])**2+(c1[1]-c2[1])**2)
                users_1 = [user_list[pts.index(pt)] for pt in clusters[c1_index]]
                users_2 = [user_list[pts.index(pt)] for pt in clusters[c2_index]]

                overlap = [u for u in users_1 if u in users_2]
                #print (len(overlap),dist)

                #print (len(overlap),dist)
                if (len(overlap) <= 1) and (dist <= threshold):
                    relations.append((dist,overlap,c1_index,c2_index))

        relations.sort(key= lambda x:x[0])
        relations.sort(key= lambda x:len(x[1]))

        return relations


    def fit2(self, markings,user_ids,jpeg_file=None,debug=False):
        #check to see if we need to split at all, i.e. there might only be one animal in total

        total = 0

        if len(user_ids) == len(list(set(user_ids))):
            #do these points meet the minimum threshold value?
            if len(markings) >= self.min_samples:
                X,Y = zip(*markings)
                cluster_centers = [(np.mean(X),np.mean(Y)), ]
                end_clusters = [markings,]
                if debug:
                    return cluster_centers, end_clusters
                else:
                    return cluster_centers
            else:
                if debug:
                    return [], []
                else:
                    return []

        clusters_to_go = []
        clusters_to_go.append((markings,user_ids,1))

        end_clusters = []
        cluster_centers = []

        colors_ = list(six.iteritems(colors.cnames))


        while True:
            #if we have run out of clusters to process, break (hopefully done :) )
            if clusters_to_go == []:
                break
            m_,u_,num_clusters = clusters_to_go.pop(-1)

            if jpeg_file is not None:
                image_file = cbook.get_sample_data(jpeg_file)
                image = plt.imread(image_file)
                fig, ax = plt.subplots()
                im = ax.imshow(image)

                X,Y = zip(*markings)
                #X = [1.875 *x for x in X]
                #Y = [1.875 *y for y in Y]
                plt.plot(X,Y,'.',color="blue")

                X,Y = zip(*m_)
                #X = [1.875 *x for x in X]
                #Y = [1.875 *y for y in Y]
                plt.plot(X,Y,'.',color="red")
                plt.show()

            #increment by 1
            while True:
                num_clusters += 1

                try:
                    kmeans = KMeans(init='k-means++', n_clusters=num_clusters, n_init=10).fit(m_)
                    total += 1
                except ValueError:
                    #all of these are noise - since we can't actually separate them
                    break

                labels = kmeans.labels_
                unique_labels = set(labels)
                temp_end_clusters = []
                #temp_clusters_to_go = []
                temp_cluster_centers = []

                temp_pts = []
                temp_users = []

                #search through to find if at least one cluster does not need to be broken down any further
                final_cluster = []
                for k in unique_labels:
                    users = [ip for index,ip in enumerate(u_) if labels[index] == k]
                    points = [pt for index,pt in enumerate(m_) if labels[index] == k]
                    assert(users != [])

                    #noise counts as a "final" cluster
                    if len(points) < self.min_samples:
                        final_cluster.append(True)
                        continue

                    if len(set(users)) == len(users):
                        temp_end_clusters.append(points)
                        X,Y = zip(*points)
                        temp_cluster_centers.append((np.mean(X),np.mean(Y)))
                        #print "==---"
                    else:
                        temp_pts.extend(points)
                        temp_users.extend(users)


                if temp_end_clusters != []:
                    end_clusters.extend(temp_end_clusters)
                    cluster_centers.extend(temp_cluster_centers)

                    #these points still need to be divided further
                    clusters_to_go.append((temp_pts,temp_users,1))

                    break
        print total
        for c in end_clusters:
            assert(len(c) >= self.min_samples)

        if debug:
            return cluster_centers, end_clusters,None
        else:
            return cluster_centers
