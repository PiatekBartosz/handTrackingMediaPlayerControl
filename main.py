import mediapipe as mp
import cv2

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

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

        if results.multi_hand_landmarks:
            for hand_landmark in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmark,
                    mp_hands.HAND_CONNECTIONS
                )

        frame = cv2.flip(frame, 1)

        cv2.imshow("Cam", frame)

        if cv2.waitKey(1) == ord("q"):
            break


cv2.DestroyAllWindows()
cap.release()

