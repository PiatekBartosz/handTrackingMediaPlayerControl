import pickle
import cv2

# Test for landmark recoginer

# STEP 1: Import the necessary modules.
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np


def draw_handmarks(frame, results) -> np.ndarray:
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


VisionRunningMode = mp.tasks.vision.RunningMode
base_options = python.BaseOptions(
    model_asset_path='/home/bartek/Programming/handTrackingMediaPlayerControl/test/hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options, running_mode=VisionRunningMode.IMAGE)

detector = vision.HandLandmarker.create_from_options(options)

with open("/home/bartek/Programming/handTrackingMediaPlayerControl/test/frame_data4.pickle", "rb") as f:
    frame_buffer = pickle.load(f)

while True:
    break_case = False
    for i in range(len(frame_buffer)):
        frame = frame_buffer[i][0]

        detection_result = detector.detect(frame)

        annotated_image = draw_handmarks(frame, detection_result)
        cv2_imshow(cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

        if cv2.waitKey(50) == ord('q'):
            break_case = True
            break

    if break_case:
        break


# 3# TEST for gesture recognizer
# with open("/home/bartek/Programming/handTrackingMediaPlayerControl/test/frame_data4.pickle", "rb") as f:
#     frame_buffer = pickle.load(f)

# with open("/home/bartek/Programming/handTrackingMediaPlayerControl/test/detection_data4.pickle", "rb") as f:
#     detection_buffer = pickle.load(f)

# while True:
#     break_case = False
#     for i in range(len(frame_buffer)):
#         frame = frame_buffer[i][0]
#         cv2.imshow("frame", frame)
#         if detection_buffer[i].gestures != []:
#             cv2.putText(frame, detection_buffer[i].gestures[0][0].category_name,
#                         (20, 200), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)

#             cv2.putText(frame, str(frame_buffer[i][1]),
#                         (50, 200), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 0), 2)


#         if cv2.waitKey(50) == ord('q'):
#             break_case = True
#             break

#     if break_case:
#         break
