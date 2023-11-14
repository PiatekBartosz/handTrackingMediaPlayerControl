from pynput import keyboard
import time

pressed_keys = set()

def on_press(key):
    try:
        print('Key {} pressed.'.format(key.char))
    except AttributeError:
        print('Special key {} pressed.'.format(key))
        pressed_keys.add(key)

def on_release(key):
    print('Key {} released.'.format(key))
    if key in pressed_keys:
        pressed_keys.remove(key)
        print('Media key {} pressed and released.'.format(key))

    if key == keyboard.Key.esc:
        # Stop listener
        return False

def media_key_test():
    print("Press and release some media keys (e.g., play/pause, volume up/down)...")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

if __name__ == "__main__":
    media_key_test()
