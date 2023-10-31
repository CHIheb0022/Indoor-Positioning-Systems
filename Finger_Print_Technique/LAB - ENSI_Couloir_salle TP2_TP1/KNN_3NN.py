import math

def euclidean_distance(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ValueError("Vector dimensions do not match")
    
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(vec1, vec2)))

def kNN_3NN(cursor, mu_rssi_vector):
    distances = {} #Store position and distance pairs as following {(Px,Py):distance}
    cursor.execute("SELECT * FROM fingerprints")
    for fingerprint in cursor.fetchall():
        rssi_string = fingerprint[4]  # fingerprint[4] contains the RSSI values as a string
        rssi_values = [int(value.strip()) for value in rssi_string.split(',')] # Convert the given string into a list of integers
        distance = euclidean_distance(mu_rssi_vector, rssi_values)
        distances.update( { (fingerprint[0],fingerprint[1]) : distance } )  # Store location and distance
    
    # Sort the distances dictionary by values in ascending order
    sorted_distances = {k: v for k, v in sorted(distances.items(), key=lambda item: item[1])}

    # Convert the dictionary to a list of key-value pairs
    dict_items = list(sorted_distances.items()) # [((px,py),distance1),((qx,qy),distance2) ,.... ]
    
    # Select the top 3 nearest neighbors
    nearest_neighbors = dict_items[:3] 
    
    # Calculate the estimated location as a weighted average
    estimated_location = (0, 0)  # Initialize with (0, 0)
    total_weight = 0
    for location, distance in nearest_neighbors: # location is a tuple of the form of (Px,Py)
        weight = 1 / (distance + 0.01)  # Adding a small constant to avoid division by zero
        estimated_location = (
            estimated_location[0] + location[0] * weight,
            estimated_location[1] + location[1] * weight
        )
        total_weight += weight
    
    estimated_location = (
        estimated_location[0] / total_weight,
        estimated_location[1] / total_weight
    )
    
    return estimated_location
