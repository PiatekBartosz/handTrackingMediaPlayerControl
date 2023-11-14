from pynput import keyboard
from pynput.keyboard import Key, Controller

# Create a keyboard controller
keyboard_controller = Controller()

# Define the mapping of regular keys to media keys
key_mapping = {
    'a': Key.media_volume_mute,
    'b': Key.media_volume_down,
    'c': Key.media_volume_up,
    'd': Key.media_play_pause, 
    'e': Key.media_previous,
    'f': Key.media_next, 
    'g': Key.media
    # Add more key mappings as needed
}

# Function to handle key press
def on_press(key):
    try:
        # Map regular key to media key and simulate key press
        media_key = key_mapping.get(key.char)
        if media_key:
            keyboard_controller.press(media_key)
    except AttributeError:
        # Handle special keys (non-character keys)
        pass

# Function to handle key release
def on_release(key):
    try:
        # Map regular key to media key and simulate key release
        media_key = key_mapping.get(key.char)
        if media_key:
            keyboard_controller.release(media_key)
    except AttributeError:
        # Handle special keys (non-character keys)
        pass

# Set up the listener
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()
