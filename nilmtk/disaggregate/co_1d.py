from nilmtk.utils import find_nearest

import pandas as pd
import itertools
import numpy as np
from sklearn import metrics
from sklearn.cluster import KMeans

MAX_POINT_THRESHOLD = 2000
MIN_POINT_THRESHOLD = 20


def transform_data(df_appliance):
    '''Subsamples if needed and converts to scikit-learn understandable format'''

    data_gt_10 = df_appliance[df_appliance > 10].values
    length = data_gt_10.size
    print length, "LENGTH"
    if length < MIN_POINT_THRESHOLD:
        status = False
        return np.zeros((2000, 1))
    else:
        status = True

    if length > MAX_POINT_THRESHOLD:
        # Subsample
        temp = data_gt_10[
            np.random.randint(0, len(data_gt_10), MAX_POINT_THRESHOLD)]
        return temp.reshape(MAX_POINT_THRESHOLD, 1)
    else:
        temp = data_gt_10
    return temp.reshape(length, 1)


def apply_clustering(X):
    '''Applies clusterin on reduced data, i.e. data where power is greater than threshold


    Returns
    -------
    centroids: list
        List
    '''

    '''
    print appliance_data, type(appliance_data)
    num_clus = -1
    sh = -1
    k_means_cluster_centers = {}
    k_means_labels = {}
    for n_clusters in range(1, 3):
        k_means = KMeans(init='k-means++',
                         n_clusters=n_clusters, n_jobs=-1)
        k_means.fit(appliance_data)
        k_means_labels[n_clusters] = k_means.labels_
        print k_means_labels
        k_means_cluster_centers[n_clusters] = k_means.cluster_centers_[0][0]
        print k_means_cluster_centers
        sh_n = metrics.silhouette_score(
            appliance_data, k_means_labels[n_clusters], metric='euclidean')
        if sh_n > sh:
            sh = sh_n
            num_clus = n_clusters
    '''
    '''Finds whether 2 or 3 gives better Silhouellete coefficient
    Whichever is higher serves as the number of clusters for that
    appliance'''
    num_clus = -1
    sh = -1
    k_means_labels = {}
    k_means_cluster_centers = {}
    k_means_labels_unique = {}
    # print X, type(X)
    for n_clusters in range(1, 3):

        try:
            k_means = KMeans(init='k-means++', n_clusters=n_clusters)
            print "Fitting %d" % n_clusters
            k_means.fit(X)

            k_means_labels[n_clusters] = k_means.labels_
            k_means_cluster_centers[n_clusters] = k_means.cluster_centers_
            print k_means_cluster_centers[n_clusters]
            k_means_labels_unique[n_clusters] = np.unique(k_means_labels)
            try:
                sh_n = metrics.silhouette_score(
                    X, k_means_labels[n_clusters], metric='euclidean')
                if sh_n > sh:
                    sh = sh_n
                    num_clus = n_clusters
            except Exception:
                print "I think ai here....\n"
                num_clus = n_clusters
        except Exception:
            print num_clus
            if num_clus > -1:
                return k_means_cluster_centers[num_clus]
            else:
                Returns np.array([0])
            print "here i am"

    return k_means_cluster_centers[num_clus]


def decode_co(length_sequence, centroids, appliance_list, states,
              residual_power):
    '''Decode a Combination Sequence and map K ^ N back to each of the K
    appliances

    Parameters
    ----------

    length_sequence:
        int, shape
    Length of the series for which decoding needs to be done

    centroids:
        dict, form:
            {appliance: [sorted list of power
                         in different states]}

    appliance_list:
        list, form:
            [appliance_i..., ]

    states:
        nd.array, Contains the state in overall combinations(K ^ N), i.e.
    at each time instance in [0, length_sequence] what is the state of overall
    system[0, K ^ N - 1]

    residual_power:
        nd.array
    '''

    co_states = {}
    co_power = {}
    total_num_combinations = 1
    for appliance in appliance_list:
        total_num_combinations *= len(centroids[appliance])

    for appliance in appliance_list:
        co_states[appliance] = np.zeros(length_sequence, dtype=np.int)
        co_power[appliance] = np.zeros(length_sequence)

    for i in range(length_sequence):
        factor = total_num_combinations
        for appliance in appliance_list:
            # assuming integer division (will cause errors in Python 3x)
            factor = factor // len(centroids[appliance])

            temp = int(states[i]) / factor
            co_states[appliance][i] = temp % len(centroids[appliance])
            co_power[appliance][i] = centroids[
                appliance][co_states[appliance][i]]

    return [co_states, co_power]


class CO_1d(object):

    def __init__(self):

        self.model = {}
        self.predictions = pd.DataFrame()

    def train(self, train_mains, train_appliances, cluster_algo='kmeans++',
              num_states=None):
        """Train using 1d CO. Places the learnt model in `model` attribute

        Attributes
        ----------

        train_mains : 1d Pandas series (indexed on DateTime) corresponding to an
            attribute of mains such as power_active, power_reactive etc.

        train_appliances : Pandas DataFrame (indexed on DateTime);
            Each attibute (column)
            is a series corresponding to an attribute of each appliance
            such as power_active. This attribute must be the same as
            that used by the mains

        cluster_algo : string, optional
            Clustering algorithm used for learning the states of the appliances

        num_states :  dict
            Dictionary corresponding to number of states for each appliance
            This can be passed by the user
        """

        centroids = {}
        print centroids
        for appliance in train_appliances:
            print "*" * 80
            print appliance
            print "*" * 80
            # Finding the points where power consumption is greater than 10
            gt_10 = {}
            gt_10[appliance] = transform_data(train_appliances[appliance])

            # Now for each appliance we find the clusters
            cluster_centers = apply_clustering(gt_10[appliance])
            flattened = cluster_centers.flatten()
            if 0 not in flattened.tolist():
                np.append(flattened, 0)
            sorted_list = np.sort(flattened)
            centroids[appliance] = sorted_list

        self.model = centroids
        return centroids

    def disaggregate(self, test_mains):
        appliance_list = [appliance for appliance in self.model]
        list_of_appliances_centroids = [self.model[appliance]
                                        for appliance in appliance_list]
        states_combination = list(itertools.product
                                  (*list_of_appliances_centroids))
        sum_combination = np.array(np.zeros(len(states_combination)))
        for i in range(0, len(states_combination)):
            sum_combination[i] = sum(states_combination[i])

        length_sequence = len(test_mains.values)
        states = np.zeros(length_sequence)
        residual_power = np.zeros(length_sequence)
        for i in range(length_sequence):
            [states[i], residual_power[i]] = find_nearest(
                sum_combination, test_mains.values[i])
        [predicted_states, predicted_power] = decode_co(length_sequence,
                                                        self.model, appliance_list, states, residual_power)
        self.predictions = pd.DataFrame(predicted_power)
