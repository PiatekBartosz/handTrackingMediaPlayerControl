import subprocess
import time
from threading import Thread

# Function to call the uinput C program
def call_uinput_c_program():
    try:
        subprocess.run(['./uinput_c_program'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error calling uinput C program: {e}")

# Function to listen for key events
def key_listener():
    while True:
        key = input("Press a key ('q' to quit): ")
        if key == 'q':
            break

        # Call the uinput C program when a key is pressed
        call_uinput_c_program()

# Start a separate thread to listen for key events
listener_thread = Thread(target=key_listener)
listener_thread.start()

# Wait for the listener thread to finish
listener_thread.join()
