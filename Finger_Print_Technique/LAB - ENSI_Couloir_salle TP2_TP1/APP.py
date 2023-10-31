#Next enhancment :
# The pop out window showing the postion: how to improve the design
# Area mangment: we can get ride of the new area button and make it a text form 
# expand the data base to accept more than one Table (one table per area)
# Fuse the where am i ? button with the Compute position button
# Separate the scan area frame from the rest of the parameters  
# Modularity and integrity (function and modules responsability mangments)
# Log file configuration to track data base infos   

import tkinter as tk
from tkinter import messagebox
import Modules as md



#Data base intialization
conn, cur = md.initialize_database()

#RSSI Vector intitialization 
Rssi_vector = []



def scan():
    x_position = entry_x.get()
    y_position = entry_y.get()
    nom = entry_id.get()
    iface = md.find_wifi_interface()
    location = [x_position, y_position]
    md.store_fingerprint(conn, cur, iface, location, nom)
    # Print table content after each update
    md.print_table_content(conn, cur, "fingerprints")
    
    

def compute_position(Cursor,rssi_vect:list):
    position = md.kNN_3NN(Cursor, rssi_vect) 
    # Show the computed position to the user
    messagebox.showinfo("Computed Position", f"Your position is: {position}")


def cancel():
    status_label.config(text="Data collection canceled")
    # Close the database connection when done
    conn.close()
    # Print to console APP termination
    print("Fingerprint Data collection or/and Posiotioning canceled") 
    root.destroy()  # Close the GUI window




# Create the main window
root = tk.Tk()
root.title("Wi-Fi Fingerprinting Data Collection")

# Set the initial window size
root.geometry("400x580")  # Width x Height

# Label at the top
top_label = tk.Label(root, text="Enter Parameters", font=("Helvetica", 16))
top_label.pack(pady=20, padx=10)  # Add padding and x-padding for spacing

# Create a frame for data entry
data_frame = tk.Frame(root)
data_frame.pack(padx=20, pady=40)

# Label and entry for x position
x_label = tk.Label(data_frame, text="X:", font=("Helvetica", 12), fg="blue")
x_label.grid(row=2, column=0, padx=10, pady=5)
entry_x = tk.Entry(data_frame, font=("Helvetica", 12))
entry_x.grid(row=2, column=1, padx=10, pady=5)

# Label and entry for y position
y_label = tk.Label(data_frame, text="Y:", font=("Helvetica", 12), fg="blue")
y_label.grid(row=3, column=0, padx=10, pady=5)
entry_y = tk.Entry(data_frame, font=("Helvetica", 12))
entry_y.grid(row=3, column=1, padx=10, pady=5)

# Label and entry for ID
id_label = tk.Label(data_frame, text="ID:", font=("Helvetica", 12), fg="blue")
id_label.grid(row=1, column=0, padx=10, pady=5)
entry_id = tk.Entry(data_frame, font=("Helvetica", 12))
entry_id.grid(row=1, column=1, padx=10, pady=5)

# Button to launch the scan and store data
scan_button = tk.Button(data_frame, text="Launch Scan", command=scan, font=("Helvetica", 14), bg="green", fg="white")
scan_button.grid(row=4, padx=15, pady=10)

# Button to compute position
compute_position_button = tk.Button(data_frame, text="Compute Position", command= lambda : compute_position(cur,Rssi_vector), font=("Helvetica", 14), bg="blue", fg="white")
compute_position_button.grid(row=6, padx=15, pady=10)

# Button to  Search for the current position --- collect current position RSSI's
Current_Position_button = tk.Button(data_frame, text="Where AM I ?", command= lambda : md.store_fingerprint_rssivector(Rssi_vector), font=("Helvetica", 14), bg="gray", fg="white")
Current_Position_button.grid(row=5, padx=15, pady=10)

# Button to discover another area 
New_Area_button = tk.Button(data_frame, text="New Area", command=lambda : md.delete_data(conn,cur), font=("Helvetica", 14), bg="orange", fg="white")
New_Area_button.grid(row=7, padx=15, pady=10)

# Button to cancel the operation
cancel_button = tk.Button(root, text="Cancel", command=cancel, font=("Helvetica", 14), bg="red", fg="white")
cancel_button.pack(pady=20)

# Label to display status
status_label = tk.Label(root, text="", font=("Helvetica", 12))
status_label.pack()

# Start the GUI main loop
root.mainloop()

# Close the database connection when done
conn.close()

