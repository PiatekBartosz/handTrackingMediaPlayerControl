
"""
    Not working -> cannot import unput, maybe wrong python version?
"""


import time
from threading import Thread
from uinput import Device, EV_KEY, KEY_VOLUMEUP, KEY_VOLUMEDOWN, KEY_MUTE

# Define the mapping of regular keys to media keys
key_mapping = {
    'a': KEY_MUTE,
    'b': KEY_VOLUMEDOWN,
    'c': KEY_VOLUMEUP,
    # Add more key mappings as needed
}

# Function to handle key press and release
def handle_key(device, key, state):
    device.emit(key, state)
    time.sleep(0.1)  # Sleep for a short duration to avoid rapid key presses

# Function to listen for key events
def key_listener(device):
    while True:
        key = input("Press a key ('q' to quit): ")
        if key == 'q':
            break

        media_key = key_mapping.get(key)
        if media_key:
            handle_key(device, media_key, 1)  # Press
            handle_key(device, media_key, 0)  # Release

# Create a virtual input device
with Device([
        (EV_KEY, KEY_MUTE),
        (EV_KEY, KEY_VOLUMEDOWN),
        (EV_KEY, KEY_VOLUMEUP),
]) as device:

    # Start a separate thread to listen for key events
    listener_thread = Thread(target=key_listener, args=(device,))
    listener_thread.start()

    # Wait for the listener thread to finish
    listener_thread.join()

# Note: You may need to run this script with elevated privileges (e.g., using sudo) to create the virtual input device.
