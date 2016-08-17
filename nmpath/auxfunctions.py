'''
Created on Jul 29, 2016

'''
import numpy as np
from math import log
import operator
from copy import deepcopy

def euclidean_distance(x,y):
    'Returns the euclidean distance between two vectors/scalars.'
    x = np.array(x); y = np.array(y)
    return np.sqrt(np.dot((x-y).T,(x-y)))


def reverse_sort_lists(list_1,list_2):
    '''Reverse sorting two list based on the first one.
    Returns both list.
    '''
    list_1_sorted, list_2_sorted = zip(*sorted(zip(list_1, list_2), \
                                        key=operator.itemgetter(0), \
                                        reverse=True))
    return list_1_sorted, list_2_sorted
    

def weighted_choice(list_, weights = None):
    '''Selects/returns an element from a list with probability 
    given by the a list of weights.
    '''
    
    size = len(list_)
    if weights is not None:
        assert(size == len(weights))
    
    if weights is None:
        probs = np.array([1/float(size) for i in range(size)])
    else:
        probs = np.array(weights)/sum(weights) # just in case
    
    rand = np.random.random()
    
    _sum = 0
    for i in range(size):
        if _sum <= rand < _sum + probs[i]:
            choice = i
            break
        else:
            _sum += probs[i]
    
    return list_[choice]


def get_shape(trajectory):
    '''Returns the shape of a trajectory array
    through the tuple (n_snapshots, n_variables)
    '''
    shape = trajectory.shape
    
    if len(shape) == 1:
        n_snapshots = shape[0] 
        n_variables =1
        if n_variables == 0:
            raise Exception('The shape {} of the trajectory/array given is not as expected'.format(shape))
    elif len(shape) == 2:
        n_snapshots = shape[0]
        n_variables = shape[1]
    else: 
        raise Exception('The shape {} of the trajectory/array given is not as expected'.format(shape))

    return n_snapshots, n_variables


def num_of_nonzero_elements(my_vector):
    '''Returns the number of non-zero elements in a vector
    '''
    counter = 0
    for element in my_vector:
        if element != 0:
            counter += 1
    return counter 


def normalize_markov_matrix(transition_matrix):
    '''Transform a matrix of positive elements to a markov-like
    matrix by divding each row by the sum of the elements of the
    row.
    '''
    t_matrix = np.array(transition_matrix,dtype=np.float64)

    n_states = len(t_matrix)
    assert(n_states == len(t_matrix[0]))
    
    for i in range(n_states):
        if (t_matrix[i,:] < 0).any():
            raise ValueError('All the elements in the input matrix must be non-negative')
        t_matrix[i,:] = normalize(t_matrix[i,:])
        # sum_ = sum(t_matrix[i,:])
        
        # if sum_ != 0.0:
        #     for j in range(n_states):
        #         t_matrix[i,j] = t_matrix[i,j]/sum_

    return t_matrix


def normalize(my_vector):
    '''Normalize a vector dividing each element by the total sum
    of all its elements
    '''
    my_vector = np.array(my_vector)
    size = len(my_vector)

    sum_ = sum(my_vector)
    if sum_ != 0.0:
        for i in range(size):
            my_vector[i] = my_vector[i] / sum_
    return my_vector


def random_markov_matrix(n_states=5):
    '''Returns a random transition markov matrix
    '''
    t_matrix = np.random.random((n_states,n_states))
    return normalize_markov_matrix(t_matrix)


def pops_from_tmatrix(transition_matrix):
    '''Returns the eigen values and eigen vectors of the transposed
    transition matrix

    input: ndarray with shape = (n_states, n_states)

    output: 
    '''
    t_matrix = deepcopy(transition_matrix)

    n_states = len(t_matrix)
    assert(n_states == len(t_matrix[0]))

    #Cleanning the transition matrix
    #--------------------------------
    #Removing the non-visited states and absorbing states
    removed_states = []
    for index in range(n_states-1,-1,-1):
        if not any(t_matrix[index]): #non-visited
            t_matrix = np.delete(t_matrix, index, axis=1)
            t_matrix = np.delete(t_matrix, index, axis=0)
            removed_states.append(index)
        elif t_matrix[index,index] == 1.: #absorbing state
            if not all([ t_matrix[index,j] == 0.0 for j in range(n_states) if j != index ]):
                raise ValueError('The sum of the elements in a row of the transition matrix must be one')
            t_matrix = np.delete(t_matrix, index, axis=1)
            t_matrix = np.delete(t_matrix, index, axis=0)
            removed_states.append(index)

    #Renormalizing just in case 
    t_matrix = normalize_markov_matrix(t_matrix)

    #Computing
    eig_vals, eig_vecs = np.linalg.eig(t_matrix.T)
    eig_vecs = eig_vecs.T # for convinience, now every row is an eig_vector

    eig_vals_close_to_one = np.isclose(eig_vals,1.0, atol=1e-8)
    real_eig_vecs = [not np.iscomplex(row).any() for row in eig_vecs]

    ss_solution = np.zeros(n_states) # steady-state solution
    for is_close_to_one, is_real, eigv in zip(eig_vals_close_to_one, real_eig_vecs, eig_vecs):
        if is_close_to_one and is_real and \
            num_of_nonzero_elements(eigv) > num_of_nonzero_elements(ss_solution) and\
            ((eigv <= 0).all() or (eigv >= 0).all()):
            ss_solution = eigv

    if (ss_solution == 0.0).all():
        raise Exception('No steady-state solution found for the given transition matrix')

    ss_solution = normalize(ss_solution).real

    # Now we have to insert back in the solution, the missing
    # elements with zero probabilities
    for index in removed_states:
        ss_solution = np.insert(ss_solution, index, 0.0)

    return ss_solution


def markov_mfpts_from_fluxes(transition_matrix, stateA, stateB):
    '''Computes the mean first passage times for systems with no absorbing 
    states A and B from the transtion matrix
    '''
    transition_matrix = np.array(transition_matrix)
     
    n_states = len(transition_matrix)
     
    #pseudo non-markovian matrix (auxiliar_matrix)
    auxiliar_matrix = np.zeros((2*n_states,2*n_states))
     
    for i in range(2*n_states):
        for j in range(2*n_states):
            auxiliar_matrix[i,j] = transition_matrix[int(i/2),int[j/2]]
     
    for i in range(n_states):
        for j in range(n_states):
            if (i in stateB) or (j in stateB):
                auxiliar_matrix[2*i,2*j] = 0.0
            if (i in stateA) or (j in stateA):
                auxiliar_matrix[2*i+1,2*j+1] = 0.0
            if (not (j in stateA)) or (i in stateA):
                auxiliar_matrix[2*i+1,2*j] = 0.0
            if (not (j in stateB)) or (i in stateB):
                auxiliar_matrix[2*i,2*j+1] = 0.0
                  
    # Is going to return a MARKOVIAN mfpt since the auxiliar
    # matrix was build from a markovian matrix 
    return nonmarkov_mfpt_from_fluxes(auxiliar_matrix, stateA, stateB)
 

def nonmarkov_mfpts_from_fluxes(nm_transition_matrix, stateA, stateB):
     
    labeled_pops = pops_from_tmatrix(nm_transition_matrix)
     
    fluxAB = 0
     
    for i in range(0, 2*n_states, 2):
        for j in range(2*n_states):
            if int(j/2) in stateB:
                fluxAB += labeled_pops[i] * nm_transition_matrix[i,j]
     



if __name__ == '__main__':
    #k= np.array([[1,2],[2,3]])
    k = random_markov_matrix(5)

    pops = pops_from_tmatrix(k)

    print(pops)
