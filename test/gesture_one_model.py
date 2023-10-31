import mediapipe as mp 
import numpy as np
import cv2
from mediapipe import ImageFormat

cap = cv2.VideoCapture(0)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path='model/gesture_recognizer.task'),
    running_mode=VisionRunningMode.IMAGE)

with GestureRecognizer.create_from_options(options) as recognizer:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Empty camera frame")
            continue

        mp_frame = mp.Image(image_format=ImageFormat.SRGB, data=frame)

        # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = recognizer.recognize(mp_frame)

        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if results.hand_landmarks:
            landmarks = []
            # iterate over "hands"
            for hand_landmark in results.hand_landmarks:

                # iterate over landmark    
                for i in range(len(hand_landmark)):
                    lmx = int(hand_landmark[i].x * frame.shape[0])
                    lmy = int(hand_landmark[i].y * frame.shape[1])
                    landmarks.append([lmx, lmy])

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmark,
                    mp_hands.HAND_CONNECTIONS
                )

                # # predict gesture
                # prediction = model.predict([landmarks])

                # # get ID
                # id = np.argmax(prediction)
                # if id > 0 and id < len(class_names):
                #     gesture = class_names[id]

        frame = cv2.flip(frame, 1)

        cv2.imshow("frame", frame)

        if cv2.waitKey(1) == ord('q'):
            break

cv2.destroyAllWindows()