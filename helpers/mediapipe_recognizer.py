import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from pynput.keyboard import Key, Controller
import threading
from queue import Queue


class KeypressThread(threading.Thread):
    def __init__(self):
        self.gesture_queue = Queue(1)
        self.keyborad_controller = Controller()
        self.key_pressed = False
        super().__init__()

    def run(self):
        while True:
            if not self.gesture_queue.empty():
                gesture = self.gesture_queue.get()

                if gesture == "swipe_right":
                    key = Key.media_next
                elif gesture == "swipe_left":
                    key = Key.media_previous
                elif gesture == "Closed_Fist":
                    key = Key.media_play_pause
                elif gesture == "Thumb_Up":
                    key = Key.media_volume_up
                elif gesture == "Thumb_Down":
                    key = Key.media_volume_down
                else:
                    continue


                self.keyborad_controller.press(key)
                self.key_pressed = True
                time.sleep(0.5)
                self.keyborad_controller.release(key)
                self.key_pressed = False
            time.sleep(0.5)


class MediapipeGestureRecoginzer:
    COLOR = [
        (0, 0, 255),   # Red
        (0, 128, 255),  # Orange
        (0, 255, 255),  # Yellow
        (0, 255, 0),   # Green
        (255, 128, 0),  # Light Blue
        (255, 0, 0),   # Blue
        (255, 0, 128),  # Purple
        (128, 0, 255),  # Pink
        (0, 0, 128),   # Dark Red
        (0, 128, 128),  # Dark Orange
        (0, 255, 128),  # Dark Yellow
        (0, 128, 0),   # Dark Green
        (128, 128, 0),  # Olive
        (128, 0, 128),  # Dark Purple
        (128, 0, 0),   # Dark Blue
        (128, 0, 64),  # Dark Pink
        (64, 0, 128),  # Light Purple
        (64, 0, 0),    # Dark Brown
        (192, 192, 192),  # Light Grey
        (128, 128, 128),  # Grey
        (220, 220, 220)  # White
    ]

    def __init__(self):
        self.running = False
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        # Gesture recognizer model #############################################
        self.BaseOptions = mp.tasks.BaseOptions
        self.GestureRecognizer = mp.tasks.vision.GestureRecognizer
        self.GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        self.VisionRunningMode = mp.tasks.vision.RunningMode

        self.gesture_options = self.GestureRecognizerOptions(
            base_options=self.BaseOptions(
                model_asset_path=r'model/gesture_recognizer.task'),
            running_mode=self.VisionRunningMode.IMAGE)

        # Hand landmarks recognizer model ######################################
        VisionRunningMode = mp.tasks.vision.RunningMode
        base_options = python.BaseOptions(
            model_asset_path=r'model/hand_landmarker.task')
        self.hand_options = vision.HandLandmarkerOptions(
            base_options=base_options, running_mode=VisionRunningMode.IMAGE)

        # Keyboard control #####################################################

        self.mediakeys_thread = KeypressThread()

    def start(self):
        self.running = True
        self.mediakeys_thread.start()

    def stop(self):
        self.mediakeys_thread.join()
        self.running = False

    def draw_handmarks(self, frame, results) -> np.ndarray:
        if results.hand_landmarks == []:
            return frame

        h, w, _ = frame.shape
        landmarks_points = []
        landmarks_list = results.hand_landmarks[0]

        # draw points for landmarks
        for idx, item in enumerate(landmarks_list):
            # convert normalized value to point on a frame
            x_frame = int(item.x * w)
            y_frame = int(item.y * h)
            landmarks_points.append((x_frame, y_frame))
            cv2.circle(frame, (x_frame, y_frame), 3, self.COLOR[idx], 2)

        # connect points
        connection_color = (20, 20, 20)
        # draw thumb -> landmarks <0, 4>
        for i in range(0, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+1], connection_color, 2)

        # draw palm
        cv2.line(frame, landmarks_points[0],
                landmarks_points[5], connection_color, 2)
        cv2.line(frame, landmarks_points[0],
                landmarks_points[17], connection_color, 2)
        for i in range(5, 17, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+4], connection_color, 2)

        # draw fingers
        for i in range(5, 21, 4):
            for j in range(3):
                cv2.line(
                    frame, landmarks_points[i+j], landmarks_points[i+j+1], connection_color, 2)
        return frame

    def draw_handmarks_and_gesture(self, frame, results) -> np.ndarray:
        if results.hand_landmarks == []:
            return frame

        h, w, _ = frame.shape
        landmarks_points = []
        landmarks_list = results.hand_landmarks[0]

        if results.gestures:
            gesture = results.gestures[0][0].category_name
            # TODO classify gesture

        else:
            gesture = None

        # draw points for landmarks
        for idx, item in enumerate(landmarks_list):
            # convert normalized value to point on a frame
            x_frame = int(item.x * w)
            y_frame = int(item.y * h)
            landmarks_points.append((x_frame, y_frame))
            cv2.circle(frame, (x_frame, y_frame), 3, self.COLOR[idx], 2)

        # connect points
        connection_color = (20, 20, 20)
        # draw thumb -> landmarks <0, 4>
        for i in range(0, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+1], connection_color, 2)

        # draw palm
        cv2.line(frame, landmarks_points[0],
                 landmarks_points[5], connection_color, 2)
        cv2.line(frame, landmarks_points[0],
                 landmarks_points[17], connection_color, 2)
        for i in range(5, 17, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+4], connection_color, 2)

        # draw fingers
        for i in range(5, 21, 4):
            for j in range(3):
                cv2.line(
                    frame, landmarks_points[i+j], landmarks_points[i+j+1], connection_color, 2)

        # print gesture name
        if gesture != None:
            cv2.putText(frame, gesture, (20, 200),
                        cv2.FONT_HERSHEY_COMPLEX, 1, self.COLOR[3], 2)

        return frame

    def recognize_gesture(self, frame):
        frame_cpy = frame.copy()
        frame_cpy_inverted_channels = cv2.cvtColor(
            frame_cpy, cv2.COLOR_BGR2RGB)
        with self.GestureRecognizer.create_from_options(self.gesture_options) as recognizer:
            mp_frame = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=frame_cpy_inverted_channels)
            results = recognizer.recognize(mp_frame)

            frame_with_landmarks = self.draw_handmarks_and_gesture(
                frame_cpy, results)
            return results, frame_with_landmarks

    def recognize_handmarks(self, frame):
        frame_cpy = frame.copy()
        frame_cpy_inverted_channels = cv2.cvtColor(
            frame_cpy, cv2.COLOR_BGR2RGB)
        with vision.HandLandmarker.create_from_options(self.hand_options) as hand_landmarks:
            mp_frame = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=frame_cpy_inverted_channels)
            results = hand_landmarks.detect(mp_frame)
            frame_with_landmarks = self.draw_handmarks(frame_cpy, results)
            return results, frame_with_landmarks
