import numpy as np
import sys
import matplotlib.pyplot as plt
import math
import pickle
import pandas as pd
import scipy.io
import time

from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.axes_grid1 import make_axes_locatable

from numpy import linalg as LA
from scipy.spatial import Delaunay
from sklearn.neighbors import NearestNeighbors

def getRankedErrors_withKeypointMatches(_scores, rank = 1):
    
    _errors = []
    _errors_map = []
    
    for obj_meta, scores, kp_matches in _scores:

        adjusted_scores = scores[:,0]*scores[:,-1]/scores[:,1]

        if obj_meta[0] in np.argsort(adjusted_scores)[-rank:]:
            if np.isnan(adjusted_scores[obj_meta[0]]):
                _errors.append([
                    obj_meta[0],
                    1,
                    np.nan,
                    np.nan,
                    np.argsort(adjusted_scores)[-rank:][0]
                ])
            else:
                
                best_keypointMatches = kp_matches[np.argmax(adjusted_scores)]
                qry_kp = best_keypointMatches[1]
                ref_kp = best_keypointMatches[2]
                
                best_ref_kps, best_qry_kps  = get_best_kp_matches(
                    ref_kp, qry_kp
                )

                _errors.append([
                    obj_meta[0],
                    0,
                    LA.norm(np.mean(best_ref_kps, axis = 0) - obj_meta[2][:3]),
                    LA.norm(np.mean(ref_kp[:,:3], axis = 0) - obj_meta[2][:3]),
                    np.argsort(adjusted_scores)[-rank:][0]
                ])
        else:
            _errors.append([
                obj_meta[0],
                1,
                np.nan,
                np.nan,
                np.argsort(adjusted_scores)[-rank:][0]
            ])

    _errors = np.asarray(_errors)
    
    return _errors

def NN_matcher(partial_scores):
    
    t0 = time.time()
    
    errors = []
    #error_map = np.zeros((len(partial_scores), len(partial_scores)))    

    #print(qp_ratios.shape, qp_nn_idx.shape)
    #continue
    for i_o, scores in enumerate(partial_scores):
        
        obj_meta = scores[0]
        diff_ratios = scores[1]
        diff_indexs = scores[2]

        diff_nn = diff_indexs[:,:,0]

        scores_per_object = []

        for c_o, c_d in enumerate(diff_ratios.T):
            nns = diff_nn[:,c_o]
            unq, unq_ind = np.unique(nns[np.argsort(c_d)], return_index=True)
            unique_scores = c_d[np.argsort(c_d)][unq_ind]

            scores_per_object.append([
                len(unique_scores),
                1-np.mean(unique_scores)
            ])

        scores_per_object = np.asarray(scores_per_object)
        weighted_scores = np.multiply(scores_per_object[:,1],scores_per_object[:,0]/len(diff_ratios))

        #error_count[i_o,1] = np.amax(weighted_scores)
        #if i_o not in np.argsort(weighted_scores)[::-1][:1]: #!= i_o:
        if obj_meta[0] != np.argmax(weighted_scores): #!= i_o:
            errors.append([
                obj_meta[0], # object meta information
                1, #correct inter-space label or not
                np.nan, # distance from correct intra-spae label
                np.argmax(weighted_scores)
            ])
        else: # Correct inter-space label; then, check intra-space label.
            
            diff_scores = scores[3]
            local_keypoint_matches = scores[4]
            
            best_keypointMatches = local_keypoint_matches[np.argmax(weighted_scores)]
            qry_kp = best_keypointMatches[1]
            ref_kp = best_keypointMatches[2]

            best_ref_kps, best_qry_kps  = get_best_kp_matches(
                ref_kp, qry_kp, 
                diff_ratios[:,np.argmax(weighted_scores)]
            )
            
            errors.append([
                obj_meta[0],
                0,
                LA.norm(np.mean(best_ref_kps, axis = 0) - obj_meta[2][:3]),
                np.argmax(weighted_scores)
            ])

    errors = np.asarray(errors)
        
    return errors


def unique_nn_vote_count_with_ratio_scores_3_ForPartials(partial_scores):
    
    errors = []
    #error_map = np.zeros((len(partial_scores), len(partial_scores)))    

    #print(qp_ratios.shape, qp_nn_idx.shape)
    #continue
    for i_o, scores in enumerate(partial_scores):
        
        obj_meta = scores[0]
        diff_ratios = scores[1]
        diff_indexs = scores[2]
        #diff_scores = scores[3]

        diff_nn = diff_indexs[:,:,0]

        scores_per_object = []

        for c_o, c_d in enumerate(diff_ratios.T):
            nns = diff_nn[:,c_o]
            unq, unq_ind = np.unique(nns[np.argsort(c_d)], return_index=True)
            unique_scores = c_d[np.argsort(c_d)][unq_ind]

            scores_per_object.append([
                len(unique_scores),
                1-np.mean(unique_scores)
            ])

        scores_per_object = np.asarray(scores_per_object)
        weighted_scores = np.multiply(scores_per_object[:,1],scores_per_object[:,0]/len(diff_ratios))

        #error_count[i_o,1] = np.amax(weighted_scores)
        #if i_o not in np.argsort(weighted_scores)[::-1][:1]: #!= i_o:
        if obj_meta[0] != np.argmax(weighted_scores): #!= i_o:
            errors.append([
                obj_meta[0],
                1
            ])
        else:
            errors.append([
                obj_meta[0],
                0
            ])

    errors = np.asarray(errors)
        
    return errors

def nn_vote_count_0(g_scores):
    
    error_counts = []
    error_maps = []
    
    for i, g_score in enumerate(g_scores):
        qp_ratios = g_score[0]
        qp_nn_idx = g_score[1]
        
        error_count = np.zeros(len(qp_ratios))
        error_map = np.zeros((len(qp_ratios), len(qp_ratios)))

        for i_o, diff_ratios_per_object in enumerate(qp_ratios):

            m2 = np.bincount(np.argsort(diff_ratios_per_object,axis = 1)[:,:1].flatten()).argmax()
            if m2 != i_o:
                error_count[i_o] = 1

            error_map[i_o,m2] = 1

        error_counts.append(np.sum(error_count))
        error_maps.append(error_map)
        
    return np.asarray(error_counts), np.asarray(error_maps)
    

def nn_vote_count_with_ratio_scores_1(g_scores):
    
    error_counts = []
    error_maps = []

    for i, g_score in enumerate(g_scores):
        qp_ratios = g_score[0]
        qp_nn_idx = g_score[1]
        
        error_count = np.zeros((len(qp_ratios),2))
        error_map = np.zeros((len(qp_ratios), len(qp_ratios)))

        #print(qp_ratios.shape, qp_nn_idx.shape)
        #continue
        for i_o, diff_ratios_per_object in enumerate(qp_ratios):

            #print(diff_ratios_per_object.shape)
            sorted_ratios = np.sort(diff_ratios_per_object,axis = 1)[:,:1]
            sorted_indices = np.argsort(diff_ratios_per_object,axis = 1)[:,:1]
            votes = np.bincount(sorted_indices.flatten())
            #print(votes,np.argsort(votes)[::-1])
            #print(sorted_ratios.shape)#,sorted_ratios)
            #print(sorted_indices.shape)#,sorted_indices)

            vote_ratios = []
            for m_i, m_count in enumerate(votes):
                if m_count == 0:
                    vote_ratios.append(0)
                else:    
                    scores = np.nan_to_num(1 - np.mean(sorted_ratios[np.where(sorted_indices == m_i)]))
                    vote_ratios.append(scores)

            votes_weights = np.concatenate(
                (votes[:,np.newaxis],np.asarray(vote_ratios)[:,np.newaxis]),axis = 1
            )

            weighted_scores = np.multiply(votes_weights[:,1],votes_weights[:,0]/sorted_indices.size)
            #np.argsort(weighted_scores)[::-1]

            error_count[i_o,1] = np.amax(weighted_scores)
            #if i_o not in np.argsort(weighted_scores)[::-1][:1]: #!= i_o:
            if i_o != np.argmax(weighted_scores): #!= i_o:
                error_count[i_o,0] = 1

            error_map[i_o,np.argmax(weighted_scores)] = 1

        error_maps.append(error_map)                        
        error_counts.append(np.sum(error_count[:,0]))
        
    return np.asarray(error_counts), np.asarray(error_maps)



def nn_vote_count_with_distance_scores_2(g_scores):
    
    error_counts = []
    error_maps = []

    for i, g_score in enumerate(g_scores):
        qp_ratios = g_score[0]
        qp_nn_idx = g_score[1]
        
        if len(g_score) < 3:
            print("Needs to have qp_scores. Only got ratios and indeces.")
            return
        
        qp_scores = g_score[2]
        
        error_count = np.zeros((len(qp_ratios),2))
        error_map = np.zeros((len(qp_ratios), len(qp_ratios)))

        #print(qp_ratios.shape, qp_nn_idx.shape)
        #continue
        for i_o, diff_ratios_per_object in enumerate(qp_ratios):

            diff_scores = qp_scores[i_o][:,:,0]

            #print(diff_ratios_per_object.shape)
            sorted_ratios = np.sort(diff_ratios_per_object,axis = 1)[:,:1]
            sorted_ratio_indices = np.argsort(diff_ratios_per_object,axis = 1)[:,:1]
            sorted_scores_indices = diff_scores[:,sorted_ratio_indices][:,:1]

            votes = np.bincount(sorted_ratio_indices.flatten())
            #print(votes,np.argsort(votes)[::-1])
            #print(sorted_ratios.shape)#,sorted_ratios)
            #print(sorted_indices.shape)#,sorted_indices)

            vote_ratios = []
            for m_i, m_count in enumerate(votes):
                if m_count == 0:
                    vote_ratios.append(0)
                else:    
                    scores = np.nan_to_num(1 - np.mean(sorted_scores_indices[np.where(sorted_ratio_indices == m_i)]))
                    vote_ratios.append(scores)

            votes_weights = np.concatenate(
                (votes[:,np.newaxis],np.asarray(vote_ratios)[:,np.newaxis]),axis = 1
            )

            weighted_scores = np.multiply(votes_weights[:,1],votes_weights[:,0]/sorted_ratio_indices.size)
            #np.argsort(weighted_scores)[::-1]

            error_count[i_o,1] = np.amax(weighted_scores)
            #if i_o not in np.argsort(weighted_scores)[::-1][:1]: #!= i_o:
            if i_o != np.argmax(weighted_scores): #!= i_o:
                error_count[i_o,0] = 1

            error_map[i_o,np.argmax(weighted_scores)] = 1

        error_counts.append(np.sum(error_count[:,0]))
        error_maps.append(error_map)                        
        #print(" ",np.sum(error_count[:,0]),"errors")

    return np.asarray(error_counts), np.asarray(error_maps)


def unique_nn_vote_count_with_ratio_scores_3(g_scores):
    
    error_counts = []
    error_maps = []

    for i, g_score in enumerate(g_scores):
        qp_ratios = g_score[0]
        qp_nn_idx = g_score[1]
        
        error_count = np.zeros((len(qp_ratios),2))
        error_map = np.zeros((len(qp_ratios), len(qp_ratios)))    

        total_scores = []

        #print(qp_ratios.shape, qp_nn_idx.shape)
        #continue
        for i_o, diff_ratios_per_object in enumerate(qp_ratios):

            diff_nn = qp_nn_idx[i_o][:,:,0]

            scores_per_object = []

            for c_o, c_d in enumerate(diff_ratios_per_object.T):
                nns = diff_nn[:,c_o]
                unq, unq_ind = np.unique(nns[np.argsort(c_d)], return_index=True)
                unique_scores = c_d[np.argsort(c_d)][unq_ind]

                scores_per_object.append([
                    len(unique_scores),
                    1-np.mean(unique_scores)
                ])

            scores_per_object = np.asarray(scores_per_object)
            weighted_scores = np.multiply(scores_per_object[:,1],scores_per_object[:,0]/len(diff_ratios_per_object))

            total_scores.append(
                weighted_scores
            )
            #np.argsort(weighted_scores)[::-1]

            #error_count[i_o,1] = np.amax(weighted_scores)
            #if i_o not in np.argsort(weighted_scores)[::-1][:1]: #!= i_o:
            if i_o != np.argmax(weighted_scores): #!= i_o:
                error_count[i_o,0] = 1

            error_map[i_o,np.argmax(weighted_scores)] = 1

        error_counts.append(np.sum(error_count[:,0]))
        error_maps.append(error_map)      
        
    return np.asarray(error_counts), np.asarray(error_maps)



def unique_nn_vote_count_with_distance_scores_4(g_scores):
    
    error_counts = []
    error_maps = []


    for i, g_score in enumerate(g_scores):
        qp_ratios = g_score[0]
        qp_nn_idx = g_score[1]
        
        if len(g_score) < 3:
            print("Needs to have qp_scores. Only got ratios and indeces.")
            return
        
        qp_scores = g_score[2]
        
        error_count = np.zeros((len(qp_ratios),2))
        error_map = np.zeros((len(qp_ratios), len(qp_ratios)))    

        total_scores = []

        #print(qp_ratios.shape, qp_nn_idx.shape)
        #continue
        for i_o, diff_ratios_per_object in enumerate(qp_ratios):

            diff_nn = qp_nn_idx[i_o][:,:,0]
            diff_scores = qp_scores[i_o][:,:,0]

            scores_per_object = []

            for c_o, c_d in enumerate(diff_ratios_per_object.T):
                nns = diff_nn[:,c_o]
                scores = diff_scores[:,c_o]
                unq, unq_ind = np.unique(nns[np.argsort(c_d)], return_index=True)
                unique_scores = scores[np.argsort(scores)][unq_ind]

                scores_per_object.append([
                    len(unique_scores),
                    1-np.mean(unique_scores)
                ])

            scores_per_object = np.asarray(scores_per_object)
            weighted_scores = np.multiply(scores_per_object[:,1],scores_per_object[:,0]/len(diff_ratios_per_object))

            total_scores.append(
                weighted_scores
            )
            #np.argsort(weighted_scores)[::-1]

            #error_count[i_o,1] = np.amax(weighted_scores)
            #if i_o not in np.argsort(weighted_scores)[::-1][:1]: #!= i_o:
            if i_o != np.argmax(weighted_scores): #!= i_o:
                error_count[i_o,0] = 1

            error_map[i_o,np.argmax(weighted_scores)] = 1

        error_counts.append(np.sum(error_count[:,0]))
        error_maps.append(error_map)      
        #print(" ",np.sum(error_count[:,0]),"errors")
        
    return np.asarray(error_counts), np.asarray(error_maps)

def skip_diag_masking(A):
    return A[~np.eye(A.shape[0],dtype=bool)].reshape(A.shape[0],A.shape[1]-1,-1)

 
def get_best_kp_matches(
    ref_kp, qry_kp, 
    diff_ratios = [], 
    ratio_threshold = 0.9, 
    good_match_threshold = 0.95,
    combine = True
):
    
    best_ratio_inidices = [[],[]]
        
    while len(best_ratio_inidices[0]) == 0:
        
        if diff_ratios != []:# Get indices of pairs of matched descriptors gave the best ratio
            best_ratio_inidices = np.where(diff_ratios<ratio_threshold)

            # Get the corresponding kp pairs.
            best_ratio_qry_kp = qry_kp[best_ratio_inidices[0]][:,:3]
            best_ratio_ref_kp = ref_kp[best_ratio_inidices[0]][:,:3]
        else: 
            best_ratio_qry_kp = qry_kp[:,:3]
            best_ratio_ref_kp = ref_kp[:,:3]
            
        ratio_threshold += 0.01
        if ratio_threshold >= 1.0:
            #print(" Failed to get best matches.")
            return ref_kp[:,:3], qry_kp[:,:3]
    

    # Get only the unique ones among the reference kp pairs which can have duplicates.
    unq_ref_kp, unq_idx = np.unique(best_ratio_ref_kp,axis = 0, return_index=True)
    unq_qry_kp = best_ratio_qry_kp[unq_idx]

    # Then, prepare for checking the inter-kp vectors.
    diff_qry_kps = np.repeat(unq_qry_kp[np.newaxis],repeats = len(unq_qry_kp), axis = 0) - unq_qry_kp[:,np.newaxis,:]
    diff_ref_kps = np.repeat(unq_ref_kp[np.newaxis],repeats = len(unq_ref_kp), axis = 0) - unq_ref_kp[:,np.newaxis,:]

    try:
        unq_diff_qry_kps = skip_diag_masking(diff_qry_kps)
        unq_diff_ref_kps = skip_diag_masking(diff_ref_kps)
    except:
        return ref_kp, qry_kp

    # Compare inter-kp vectors using cosine similarity. 
    Norm_unq_diff_qry_kps = LA.norm(unq_diff_qry_kps, axis = -1)
    Norm_unq_diff_ref_kps = LA.norm(unq_diff_ref_kps, axis = -1)
    similarity_of_length = np.exp(-0.5*np.abs(Norm_unq_diff_qry_kps - Norm_unq_diff_ref_kps))
    similarity_of_angle = np.sum(np.multiply(unq_diff_qry_kps,unq_diff_ref_kps), axis = -1)/np.multiply(Norm_unq_diff_qry_kps,Norm_unq_diff_ref_kps)

    if combine:
        similarity_of_shape = np.multiply(similarity_of_length,similarity_of_angle)
    else:
        similarity_of_shape = similarity_of_angle

    # Good matches are those with cosine similarity near 1, e.g. cos_sim > 0.975
    good_matches = np.greater(
        np.abs(similarity_of_shape), 
        good_match_threshold*np.ones(similarity_of_shape.shape)
    )

    while np.max(np.count_nonzero(good_matches, axis = -1)) < 0.1*len(ref_kp):
        good_match_threshold = good_match_threshold - 0.05
        good_matches = np.greater(
            np.abs(similarity_of_shape), 
            good_match_threshold*np.ones(similarity_of_shape.shape)
        )

    # Get which of the kp-pairs give the most good matches
    good_matches_ref_kp = np.argmax(np.count_nonzero(good_matches, axis = -1))
    good_matches_kp_idx = np.insert(good_matches[good_matches_ref_kp],True,good_matches_ref_kp)
    good_matches_kp_idx.shape

    # Get corresponding indices of those with good kp matches
    for_plotting_idx = np.where(good_matches_kp_idx == True)[0]

    for_plotting_qry_kps = unq_qry_kp[for_plotting_idx]
    for_plotting_ref_kps = unq_ref_kp[for_plotting_idx]
        
    
    return for_plotting_ref_kps, for_plotting_qry_kps