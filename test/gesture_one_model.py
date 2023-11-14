import mediapipe as mp 
import numpy as np
import cv2
import time
from pynput.keyboard import Key, Controller

colors = [
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

def draw_handmarks_and_gesture(frame, results):
    h, w, _ = frame.shape
    black_color = (0, 0, 0)
    dots_colors = []
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
        cv2.circle(frame, (x_frame, y_frame), 3, colors[idx], 2)

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
        cv2.putText(frame, gesture, (20, 60), cv2.FONT_HERSHEY_COMPLEX, 1, colors[3], 2)

cap = cv2.VideoCapture(0)

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

BaseOptions = mp.tasks.BaseOptions
GestureRecognizer = mp.tasks.vision.GestureRecognizer
GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = GestureRecognizerOptions(
    base_options=BaseOptions(model_asset_path='model/gesture_recognizer.task'),
    running_mode=VisionRunningMode.IMAGE)

# variables for calculating FPS
prev_frame = 0
new_frame = 0

# this function is responsible creating a threaded method in MediaKeyController class
def threaded(fn):
    def wrapper(*args, **kwargs):
        th = threading.Thread(target=fn, args=args, kwargs=kwargs)
        thread.start()
        return thread
    return wrapper

class MediaKeyController:
    MEDIA_KEY_PAUSE_DELAY = 20
    GESTURE_RECOGNITION_MIN_TIME = 50

    def __init__(self):
        self.keyboard = Controller()  
        self.gesture_time = 0 
        self.toggle_time = 0 
        self.prev_time = time.time()

    def gesure_recognize(self, gesture):
        if gesture == "Closed_Fist":
            self.gesture_time += time.time() - self.prev_time 
            if self.gesture_time > self.GESTURE_RECOGNITION_MIN_TIME: 
                self._toggle()
                self.gesture_time = 0
        else:
            self.gesture_time = 0

    @threaded 
    def _toggle(self):
        self.keyboard.press(Key.media_play_pause)
        time.sleep(0.2)
        self.keyboard.release(Key.media_play_pause)

media_key_controller = MediaKeyController()

with GestureRecognizer.create_from_options(options) as recognizer:
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Empty camera frame")
            break

        mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

        results = recognizer.recognize(mp_frame)

        if results.hand_landmarks != []:
            # for hand_landmark in results.hand_landmarks:
            draw_handmarks_and_gesture(frame, results)

        # calculate FPS
        new_frame = time.time()
        fps = str(int(1/(new_frame - prev_frame)))
        prev_frame = new_frame

        # draw FPS
        cv2.putText(frame, fps, (frame.shape[1] - 50, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3, cv2.LINE_AA)

        cv2.imshow("frame", frame)

        if cv2.waitKey(1) == ord('q'):
            break

cv2.destroyAllWindows()