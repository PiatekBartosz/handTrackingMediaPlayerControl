import time
import pyautogui
from threading import Thread

# Define the mapping of regular keys to media keys
key_mapping = {
    'a': 'volumemute',
    'b': 'volumedown',
    'c': 'volumeup',
    # Add more key mappings as needed
}

# Function to press and release a media key
def press_and_release_media_key(media_key):
    pyautogui.press(media_key)
    time.sleep(0.1)  # Sleep for a short duration to avoid rapid key presses

# Function to listen for key events
def key_listener():
    while True:
        key = input("Press a key ('q' to quit): ")
        if key == 'q':
            break

        media_key = key_mapping.get(key)
        if media_key:
            press_and_release_media_key(media_key)

# Start a separate thread to listen for key events
listener_thread = Thread(target=key_listener)
listener_thread.start()

# Wait for the listener thread to finish
listener_thread.join()
