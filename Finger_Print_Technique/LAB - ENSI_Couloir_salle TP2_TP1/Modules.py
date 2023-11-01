#This Python file is used as an API provider to Ensure phase 1 & 2 compilation:
#store (ID, Cood<x,y>, RSSij) info into a database. and compute the position. Using the provided function declared bellow:
#***func documentation::

import pywifi
import time
import sqlite3
import math


# Function to initialize the database connection
def initialize_database():
    conn = sqlite3.connect('wifi_fingerprints.db')
    cursor = conn.cursor()
    return conn, cursor

# Find wifi interface 
def find_wifi_interface():

    # Initialize Wi-Fi interface
    wifi = pywifi.PyWiFi()
    names = {}

    # List and display available Wi-Fi interfaces
    interfaces = wifi.interfaces()
    for i, interface in enumerate(interfaces):
        names[i]=interface
    return names[0]


#Print the content of the table to monitor updates 
def print_table_content(cursor, table_name):
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(f"The table '{table_name}' is empty.")
        else:
            print(f"Contents of the '{table_name}' table:")
            for row in rows:
                print(row)
    except Exception as e:
        print(f"An error occurred: {str(e)}")

#Remove the table labeled "table_name." This functionality is exclusively accessible to the administrator
#Note:delete_table feature is not included in the GUI. 
def delete_table(con,cur,table_name):
    try:
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        con.commit()
        print(f"The '{table_name}' table has been deleted.")
    except sqlite3.Error as e:
        print(f"An error occurred: {str(e)}")


# Function to scan and store fingerprints into database tables
def store_fingerprint(conn,cur,iface,Area_name,RP_location,RP_ID):
    iface.scan()
    time.sleep(2)  # Wait for a moment to allow scanning to complete
    RSSI_values = []
    scan_results = iface.scan_results()

    for network in scan_results:
        bssid = network.bssid
        ssid = network.ssid
        signal_strength = network.signal
        RSSI_values.append(signal_strength)
    # Convert the RSSI_values list to a string
    rssi_values_str = ', '.join(map(str, RSSI_values))

    # Create a table specific to the Area to store Wi-Fi fingerprints (if it doesn't exist)
    cur.execute(f'''CREATE TABLE IF NOT EXISTS {Area_name}
                  (location_x INTEGER ,location_y INTEGER , bssid TEXT, ssid TEXT, signal_strength TEXT, nom TEXT)''')
    conn.commit()
    
    cur.execute(f'''INSERT INTO {Area_name} (location_x, location_y, bssid, ssid, signal_strength, nom) 
                      VALUES (?, ?, ?, ?, ?, ?)''', (RP_location[0], RP_location[1], bssid, ssid, rssi_values_str, RP_ID))
    conn.commit()

# Function to scan and store fingerprints values for the current position  and loaded into an RSSI_vector 
def store_fingerprint_rssivector(Tag_name):
    rssi_vector = [] 
    iface = find_wifi_interface()
    iface.scan()
    time.sleep(2)  # Wait for a moment to allow scanning to complete
    scan_results = iface.scan_results()
    for network in scan_results:
        signal_strength = network.signal
        rssi_vector.append(signal_strength)
    print(f"Your Current Position Finger print:\n {Tag_name} : {rssi_vector}")
    return rssi_vector


# Compute the RSSI <distance> between two points (the current location and a reference point)

def euclidean_distance(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ValueError("Vector dimensions do not match")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(vec1, vec2))) #zip(vec1, vec2) = ((x1,y1),(x2,y2),...)
# Note: For two points if the two RSSI vector measurments mathces the function return 0.


# KNN_3NN algorithm
def kNN_3NN(cursor, table_name, mu_rssi_vector):
    distances = {} #Store position and distance pairs as following {(Px,Py):distance}
    cursor.execute(f"SELECT * FROM {table_name}")
    
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



