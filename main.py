import mediapipe as mp
import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from pynput.keyboard import Key, Controller
from time import sleep

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

keyboard = Controller()

# load gesture model
model = load_model('model')

# load class names
f = open('model/gesture_names')
class_names = f.read().split('\n')
f.close()
print(class_names)


cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    model_complexity=0, min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            print("Empty camera frame")
            continue

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        gesture = ''
        prev = ''
        id = None

        if results.multi_hand_landmarks:
            landmarks = []
            for hand_landmark in results.multi_hand_landmarks:
                for lm in hand_landmark.landmark:
                    lmx = int(lm.x * frame.shape[0])
                    lmy = int(lm.y * frame.shape[1])
                    landmarks.append([lmx, lmy])

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmark,
                    mp_hands.HAND_CONNECTIONS
                )

                # predict gesture
                prediction = model.predict([landmarks])

                # get ID
                id = np.argmax(prediction)
                if id > 0 and id < len(class_names):
                    gesture = class_names[id]

        frame = cv2.flip(frame, 1)

        if id:
            # volume up
            if id == 2:
                keyboard.press(Key.media_volume_up)
                keyboard.release(Key.media_volume_up)

            # volume down
            if id == 3:
                keyboard.press(Key.media_volume_down)
                keyboard.release(Key.media_volume_down)

            # play/pause
            if id == 8:
                keyboard.press(Key.media_play_pause)
                keyboard.release(Key.media_play_pause)
                sleep(0.5)

            # mute
            if id == 1:
                keyboard.press(Key.media_volume_mute)
                keyboard.release(Key.media_volume_mute)
                sleep(0.5)

        cv2.putText(frame, gesture, (20, 20), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2, cv2.LINE_AA)

        cv2.imshow("Cam", frame)

        if cv2.waitKey(1) == ord("q"):
            break


cap.release()

