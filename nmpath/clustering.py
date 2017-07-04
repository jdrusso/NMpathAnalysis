'''
Created on June 29, 2017

@author: esuarez
'''
import numpy as np
from auxfunctions import pops_from_tmatrix, check_tmatrix, random_markov_matrix
from mfpt import mfpts_matrix, min_commute_time, _max_commute_time
import copy
import operator


def merge_microstates_in_tmatrix(transition_matrix, ms1, ms2):
    '''Merge two microstates (ms1 and ms2) in the transition matrix, i.e.,
    returns the transition matrix that we would obtain if the microstates where
    merged befored the estimation of the transition matrix. The transition
    matrix is expected to be a square numpy array'''

    check_tmatrix(transition_matrix)  # it is a valid t_matrix?

    p = pops_from_tmatrix(transition_matrix)
    size = len(transition_matrix)
    final_tmatrix = np.copy(transition_matrix)

    # sum of the columns with indexes ms1 and ms2
    # and saved in the index state1.
    for k in range(size):
        final_tmatrix[k, ms1] += final_tmatrix[k, ms2]

    # weighted sum of the rows
    for k in range(size):
        if (p[ms1] + p[ms2]) != 0.0:
            final_tmatrix[ms1, k] = (p[ms1] * final_tmatrix[ms1, k] +
                                     p[ms2] * final_tmatrix[ms2, k]) / \
                (p[ms1] + p[ms2])

    final_tmatrix = np.delete(final_tmatrix, ms2, axis=1)
    final_tmatrix = np.delete(final_tmatrix, ms2, axis=0)

    return final_tmatrix


def kinetic_clustering_from_tmatrix(transition_matrix, n_clusters=2,
                                    t_cut=float('inf'), ini_clusters=None,
                                    verbose=False):
    """Hierarchical agglomeratice kinetic clustering from the commute matrix
    (MFPTs in both directions). On each step, the matrix is recalculated.
    """
    # Check for consistency
    check_tmatrix(transition_matrix)  # it is a valid t_matrix?
    if n_clusters < 2:
        raise ValueError("The final number of clusters should be "
                         "greater than 2")

    n_states = len(transition_matrix)

    new_tmatrix = copy.copy(transition_matrix)

    if ini_clusters is None:
        clusters = [[i] for i in range(n_states)]
    else:
        clusters = copy.copy(ini_clusters)

    mfpt_M = mfpts_matrix(transition_matrix)
    t_min, i_min, j_min = min_commute_time(mfpt_M)
    t_max, i_max, j_max = _max_commute_time(mfpt_M)

    if verbose:
        print("Number of clusters: ", end=" ")

    while (t_min < t_cut) and (len(clusters) > n_clusters):

        # Merging clusters, we are going to merge the smallest
        # into the biggest but that is not necessary
        if len(clusters[i_min]) > len(clusters[j_min]):
            clusters[i_min] += clusters[j_min]
            del clusters[j_min]
            new_tmatrix = merge_microstates_in_tmatrix(new_tmatrix,
                                                       i_min, j_min)
        else:
            clusters[j_min] += clusters[i_min]
            del clusters[i_min]
            new_tmatrix = merge_microstates_in_tmatrix(new_tmatrix,
                                                       j_min, i_min)

        if verbose:
            print(len(clusters), end=" ")

        # Merge states in the t_matrix

        # recalculate
        mfpt_M = mfpts_matrix(new_tmatrix)
        t_min, i_min, j_min = min_commute_time(mfpt_M)
        t_max, i_max, j_max = _max_commute_time(mfpt_M)

    return clusters, t_min, t_max, new_tmatrix


def biggest_clusters_indexes(clusters, n_pick=2):
    '''Pick the n_pick biggest clusters in a list of lists where the inner
    lists are group of indexes (clusters)'''

    n_clusters = len(clusters)

    indexes = [i for i in range(n_clusters)]
    len_cluster = [len(c) for c in clusters]

    len_c_sorted, indexes_sorted = zip(*sorted(zip(len_cluster, indexes),
                                               key=operator.itemgetter(0),
                                               reverse=True))

    return indexes_sorted[0:n_pick]


if __name__ == "__main__":
    T = random_markov_matrix(20)

    clusters, t_min, t_max, new_tmatrix = kinetic_clustering_from_tmatrix(T, 5)

    print(biggest_clusters_indexes(clusters))
    print(clusters)

    clusters = [[1], [2, 3], [1, 2, 3], [0], [1, 2, 3, 4, 5, 6]]

    print(biggest_clusters_indexes(clusters, n_pick=3))
    print(clusters)