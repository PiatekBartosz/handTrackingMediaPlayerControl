import cv2
import mediapipe as mp
import numpy as np
import time


class MediapipeRecoginzer:
    COLOR = [
        (0, 0, 255),   # Red
        (0, 128, 255), # Orange
        (0, 255, 255), # Yellow
        (0, 255, 0),   # Green
        (255, 128, 0), # Light Blue
        (255, 0, 0),   # Blue
        (255, 0, 128), # Purple
        (128, 0, 255), # Pink
        (0, 0, 128),   # Dark Red
        (0, 128, 128), # Dark Orange
        (0, 255, 128), # Dark Yellow
        (0, 128, 0),   # Dark Green
        (128, 128, 0), # Olive
        (128, 0, 128), # Dark Purple
        (128, 0, 0),   # Dark Blue
        (128, 0, 64),  # Dark Pink
        (64, 0, 128),  # Light Purple
        (64, 0, 0),    # Dark Brown
        (192, 192, 192), # Light Grey
        (128, 128, 128), # Grey
        (220, 220, 220)  # White
    ]

    def __init__(self):
        self.running = False    
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils

        self.BaseOptions = mp.tasks.BaseOptions
        self.GestureRecognizer = mp.tasks.vision.GestureRecognizer
        self.GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        self.VisionRunningMode = mp.tasks.vision.RunningMode

        self.options = self.GestureRecognizerOptions(
            base_options=self.BaseOptions(model_asset_path='model/gesture_recognizer.task'),
            running_mode=self.VisionRunningMode.IMAGE)

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def draw_handmarks_and_gesture(self, frame, results) -> np.ndarray:
        if results.hand_landmarks == []:
            return frame

        h, w, _ = frame.shape
        landmarks_points = []
        landmarks_list = results.hand_landmarks[0]
        
        if results.gestures:
            gesture = results.gestures[0][0].category_name
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
            cv2.line(frame, landmarks_points[i], landmarks_points[i+1], connection_color, 2)
        
        # draw palm
        cv2.line(frame, landmarks_points[0], landmarks_points[5], connection_color, 2)
        cv2.line(frame, landmarks_points[0], landmarks_points[17], connection_color, 2)
        for i in range(5, 17, 4):
            cv2.line(frame, landmarks_points[i], landmarks_points[i+4], connection_color, 2)

        # draw fingers
        for i in range(5, 21, 4):
            for j in range(3):
                cv2.line(frame, landmarks_points[i+j], landmarks_points[i+j+1], connection_color, 2)

        # print gesture name
        if gesture != None:
            cv2.putText(frame, gesture, (20, 60), cv2.FONT_HERSHEY_COMPLEX, 1, self.COLOR[3], 2)

        return frame
            

    def recognize(self, frame) -> np.ndarray:
        print("test")
        with self.GestureRecognizer.create_from_options(self.options) as recognizer:
            # TODO change SRGB if bad cofdance
            mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)
            results = recognizer.recognize(mp_frame)
            frame_with_landmarks = self.draw_handmarks_and_gesture(frame, results)
            return frame_with_landmarks