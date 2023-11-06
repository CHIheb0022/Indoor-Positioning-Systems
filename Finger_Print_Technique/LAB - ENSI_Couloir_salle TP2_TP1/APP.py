import tkinter as tk
from tkinter import messagebox
import Modules as md
import matplotlib.pyplot as plt 

#To access as an administrator
correct_login = "chiheb"
correct_password = "chiheb123"

##User guide##
print("\n\n/************User Guide***********/\n\n")

print("This finger-printing based localisation App Provide the following features:\n") 
print("1_ Define an indoor Enviorement:\n",
    " - Use the name of the area as a label for the Enviorement.\n",
    " - Record multiple reference points within this area (location,fingerprint).\n",
    " - Update reference Points within a spcific area.\n",
    " - By initilaizing the area you can record from scratch new reference points associated to this area \n")
print("2_ Get your Current Psition (after defining the enviorement):\n",
      " - Enter the area name you are at using the <Am at> text field\n",
      " - Identify your exact current position using the <Postion Tag> text field\n",
      " - Press the 'where am I' button to get the result\n")


#Data base intialization
conn, cur = md.initialize_database()


def admin_config():    
    #Log available Enviorements
    print("Available Enviorements:\n") 
    try:
        # Get a list of availabe tables in the database (each table represent an area = enviorement)
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cur.fetchall()
        table_list =[]
        # Iterate through the table names and print each table name 
        for table in table_names:
            print(table[0],"\n")
            table_list.append(table[0])
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    # Manage database
    while True:
        area_name = input("Choose an area name to display the recorded reference points within (or press Enter to exit):\n")
        if area_name == '':
            break  # Exit the loop if Enter is pressed

        if area_name in table_list:
            md.print_table_content(cur, area_name)
        else:
            print(f"The area '{area_name}' is not available in the database.\n")

    while True:
        table_name = input("Please provide the area name you want to delete (or press Enter to exit):\n")
        if table_name == '':
            break  # Exit the loop if Enter is pressed

        if table_name in table_list:
            respond = input(f"Are you sure you want to delete area '{table_name}' (Y/N):\n").strip().lower()
            if respond == 'y':
                md.delete_table(conn, cur, table_name)
            else:
                print("Deletion canceled.\n")
        else:
            print(f"The area '{table_name}' is not available in the database.\n")
    print("You can still use the App GUI") 

def scan():
    area_name = entry_Area.get()
    x_position = entry_x.get()
    y_position = entry_y.get()
    RP_ID = entry_id.get()
    iface = md.find_wifi_interface()
    location = [x_position, y_position]
    
    #Store RP data into the table representing the area
    md.store_fingerprint(conn, cur, iface, area_name, location, RP_ID)

    # Print table content after each update
    md.print_table_content(cur, area_name)

    # Create a figure to display the grid 
    fig, ax = plt.subplots(figsize=(8, 6))

    # Visulaize each RP once added to the table
    md.visualize_grid(cur,ax,area_name)


#Delete the fingerprints within a specific table (to update RPs)
def Delete_table_content():
    table_name = entry_Area.get()
    try: 
        cur.execute(f"DELETE FROM {table_name};")
        conn.commit()
        print(f"All records in the '{table_name}' table have been deleted.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")    


def compute_position():
    
    #Get area name   
    current_Area = entry_Am_at.get()
    
    #Get Position Tag 
    tag = entry_Position.get()
    
    #Current RSSI Vector
    current_rssi_vect = md.store_fingerprint_rssivector(tag)
    
    try:
        table_list = []
        # Get a list of table names
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = cur.fetchall()
        for table in table_names:
            table_list.append(table[0])

        if current_Area in table_list:
            # Create a pop-up message indicating the Computed Position as an info
            position = md.kNN_3NN(cur, current_Area, current_rssi_vect)
            info_text = f"\n\nYour exact current position is:\n\nX: {position[0]}, Y: {position[1]}"
            messagebox.showinfo(f"{tag} Computed Position", info_text)
        else:
            # Create a pop-up message indicating the issues as a warning
            warning_text = f"\n\nUnknown Area.\nPlease provide reference points for {current_Area} Area!"
            messagebox.showwarning(f"Unable to pinpoint your exact location due to the following error", warning_text)
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    #axes and figure variables 

    fig, ax = plt.subplots(figsize=(8, 6))
    
    #Visualize the grid
    md.visualize_grid(cur, ax, current_Area, position)   

def cancel():
    status_label.config(text="Data collection canceled")
    # Close the database connection when done
    conn.close()
    # Print to console APP termination
    print("Fingerprint Data collection or/and Posiotioning canceled") 
    root.destroy()  
# Close the GUI window




## Admin configuration ##

attempts=0
while attempts<=3:
    print("If you are willing to use the application as an administrator, please provide the login and password (if not, simply press Enter).\n")
    # Prompt the user for login and password
    entered_login = input("Enter login: ")
    entered_password = input("Enter password: ")

    
    if entered_login == '':
        print("You can still use the application's features through its graphical interface, as described above.") 
        break  # Exit the loop if Enter is pressed
    
    # Check if the entered login and password match the predefined values
    if entered_login == correct_login and entered_password == correct_password:
        print("Access granted. You are now in the admin section.")
        print("\n\n/************Admin section***********/\n\n")
        admin_config() 
    else:
        attempts+=1
        print("Access denied. Incorrect login or password.\n")
        print(f"You still have {3-attempts} attempts\n")
            

## GUI ##
# Create the main window
root = tk.Tk()
root.title("Positioning using Wi-Fi Fingerprint ")

# Set the initial window size
root.geometry("500x680")  # Width x Height

# Create a frame for Reference Point Collection
First_frame = tk.Frame(root)
First_frame.pack(padx=20, pady=40)

# Create a frame for Position detection
Second_frame = tk.Frame(root)
Second_frame.pack(padx=20, pady=40)  # Adjust the padding as needed

# Label For the First frame 
top_label = tk.Label(First_frame, text="Define Indoor Environnement", font=("Helvetica", 16))
top_label.grid(row=0, column=0, pady=10, padx=10)  # Add padding and x-padding for spacing


# Label For the second frame
top_label = tk.Label(Second_frame, text="Get current position", font=("Helvetica", 16))
top_label.grid(row=0, column=0, pady=10, padx=10)  # Add padding and x-padding for spacing

# Label and entry for Area Name
Area_label = tk.Label(First_frame, text="Area Name:", font=("Helvetica", 12), fg="blue")
Area_label.grid(row=1, column=0, padx=10, pady=5)
entry_Area = tk.Entry(First_frame, font=("Helvetica", 12))
entry_Area.grid(row=1, column=1, padx=10, pady=5)

# Label and entry for ID
id_label = tk.Label(First_frame, text="Reference Point ID:", font=("Helvetica", 12), fg="blue")
id_label.grid(row=2, column=0, padx=10, pady=5)
entry_id = tk.Entry(First_frame, font=("Helvetica", 12))
entry_id.grid(row=2, column=1, padx=10, pady=5)

# Label and entry for x position
x_label = tk.Label(First_frame, text="Position - X:", font=("Helvetica", 12), fg="blue")
x_label.grid(row=3, column=0, padx=10, pady=5)
entry_x = tk.Entry(First_frame, font=("Helvetica", 12))
entry_x.grid(row=3, column=1, padx=10, pady=5)

# Label and entry for y position
y_label = tk.Label(First_frame, text="Position - Y:", font=("Helvetica", 12), fg="blue")
y_label.grid(row=4, column=0, padx=10, pady=5)
entry_y = tk.Entry(First_frame, font=("Helvetica", 12))
entry_y.grid(row=4, column=1, padx=10, pady=5)

# Button to launch the scan and store data
scan_button = tk.Button(First_frame, text="Record Reference Point", command=scan, font=("Helvetica", 14), bg="green", fg="white")
scan_button.grid(row=5, padx=15, pady=10)

# Button to Re-initilize the table representing the area
scan_button = tk.Button(First_frame, text="Initialize Area", command=Delete_table_content, font=("Helvetica", 14), bg="gray", fg="white")
scan_button.grid(row=6, padx=15, pady=10)

# Label and entry for Area Name
Am_at_label = tk.Label(Second_frame, text="Am at:", font=("Helvetica", 12), fg="blue")
Am_at_label.grid(row=1, column=0, padx=10, pady=5)
entry_Am_at = tk.Entry(Second_frame, font=("Helvetica", 12))
entry_Am_at.grid(row=1, column=1, padx=10, pady=5)

# Label and entry for Position Tag
Position_label = tk.Label(Second_frame, text="Position Tag:", font=("Helvetica", 12), fg="blue")
Position_label.grid(row=2, column=0, padx=10, pady=5)
entry_Position = tk.Entry(Second_frame, font=("Helvetica", 12))
entry_Position.grid(row=2, column=1, padx=10, pady=5)

# Button to compute position
compute_position_button = tk.Button(Second_frame, text="Where Exactly ?", command= lambda : compute_position(), font=("Helvetica", 14), bg="blue", fg="white")
# or: compute_position_button = tk.Button(Second_frame, text="Where Exactly ?", command=compute_position, font=("Helvetica", 14), bg="blue", fg="white")
# in case you want to pass parameters to the handler function it's necessary to use lambda.
compute_position_button.grid(row=3, padx=15, pady=10)

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

