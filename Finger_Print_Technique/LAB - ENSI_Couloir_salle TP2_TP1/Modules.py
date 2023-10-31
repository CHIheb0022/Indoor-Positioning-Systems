#This Python file is used as an API provider to Ensure phase 1 & 2 compilation:
#store (ID, Cood<x,y>, RSSij) info into a database. and compute the position. Using the provided function declared bellow:
#***func documentation::

import pywifi
import time
import sqlite3
import math

# Custom exception for when the interface is not found
class InterfaceNotFoundError(Exception):
    pass

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

find_wifi_interface()

#Print the content of the table to monitor updates 
def print_table_content(conn, cursor, table_name):
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

#Delete the fingerprint table (to make it empty in order to store another spot measurement for example: cours,un autre couloire)
def delete_data(conn, cursor):
    try:
        # Get a list of table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cursor.fetchall()
        
        # Iterate through the table names and delete each table
        for table in table_names:
            table_name = table[0]
            cursor.execute(f"DELETE FROM {table_name};")
            conn.commit()
            print(f"All records in the '{table_name}' table have been deleted.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Initialize Wi-Fi interface
def initialize_wifi_interface(interface_name):
    
    wifi = pywifi.PyWiFi()
    # Initialize the selected Wi-Fi interface
    iface = None
    
    #debug
    print (interface_name,'\n')
    for interface in wifi.interfaces():
        print (interface.name(), '\n')
    
    for interface in wifi.interfaces():
        if interface_name == interface.name():
            iface = interface
            break
    if iface is None:
        raise InterfaceNotFoundError(f"Interface '{interface_name}' not found. Make sure the interface exists.")

# Function to scan and store fingerprints into database table
def store_fingerprint(conn,cur,iface ,location,nom):
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
    
    cur.execute('''INSERT INTO fingerprints (location_x, location_y, bssid, ssid, signal_strength, nom) 
                      VALUES (?, ?, ?, ?, ?, ?)''', (location[0], location[1], bssid, ssid, rssi_values_str, nom))
    conn.commit()

# Function to scan and store fingerprints values for the current position  and loaded into an RSSI_vector 
def store_fingerprint_rssivector(rssi_vector:list):
    iface = find_wifi_interface()
    iface.scan()
    time.sleep(2)  # Wait for a moment to allow scanning to complete
    scan_results = iface.scan_results()
    for network in scan_results:
        signal_strength = network.signal
        rssi_vector.append(signal_strength)
    print(rssi_vector)



# Function to initialize the database connection
def initialize_database():
    conn = sqlite3.connect('wifi_fingerprints.db')
    cursor = conn.cursor()
    # Create a table to store Wi-Fi fingerprints (if it doesn't exist)
    cursor.execute('''CREATE TABLE IF NOT EXISTS fingerprints
                  (location_x INTEGER ,location_y INTEGER , bssid TEXT, ssid TEXT, signal_strength TEXT, nom TEXT)''')
    conn.commit()
    return conn, cursor


# Compute the RSSI <distance> between two points (the current location and a reference point)
# For two points if the two RSSI vector measurments mathces the function return 0.
def euclidean_distance(vec1, vec2):
    if len(vec1) != len(vec2):
        raise ValueError("Vector dimensions do not match")
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(vec1, vec2))) #zip(vec1, vec2) = ((x1,y1),(x2,y2),...)


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



