import cv2
import numpy as np
import base64
import socket
import imutils
import time
import logging
from queue import Queue
from .mediapipe_recognizer import MediapipeGestureRecoginzer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


class UDP_factory:
    BUFF_SIZE = 65536

    def __init__(self, ip: str, port: int) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ip = ip
        self.port = port
        self.socket = None
        self.running = False

    def close(self) -> None:
        self.logger.info("Closing socket")
        if self.socket:
            self.socket.close()
        self.running = False

    def _encode_opencv_frame(self, frame: np.ndarray) -> bytes:
        _, jpg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return base64.b64encode(jpg)

    def _decode_opencv_frame(self, data: bytes) -> np.ndarray:
        decoded = base64.b64decode(data)
        npdata = np.frombuffer(decoded, dtype=np.uint8)
        return cv2.imdecode(npdata, cv2.IMREAD_COLOR)


class UDP_client(UDP_factory):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_RCVBUF,
            self.BUFF_SIZE
        )

        self.running = True
        self.logger.info(f"Client started -> {ip}:{port}")

    def client_routine(self) -> None:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not cap.isOpened():
            self.logger.error("Camera failed to open")
            return

        cap.set(cv2.CAP_PROP_FPS, 20)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

        prev_time = time.time()

        while True:
            ret, frame = cap.read()

            if not ret:
                self.logger.error("Frame capture failed")
                self.close()
                break

            frame = imutils.resize(frame, width=400)
            frame_raw = frame.copy()

            now = time.time()
            dt = now - prev_time
            prev_time = now

            fps = int(1 / dt) if dt > 0 else 0

            self._show_fps(frame, fps, dt)
            cv2.imshow("Client side", frame)

            self._send_data(frame_raw)

            self.logger.debug(f"Frame sent to {self.ip}:{self.port}")

            if cv2.waitKey(1) == ord("q"):
                self.close()
                break

    def _show_fps(self, frame, fps: int, dt: float) -> None:
        cv2.putText(frame, f"FPS: {fps}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, f"FrameTime: {dt:.3f}s", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def _send_data(self, frame: np.ndarray) -> None:
        encoded = self._encode_opencv_frame(frame)
        self.socket.sendto(encoded, (self.ip, self.port))


class UDP_server(UDP_factory):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)

        self.logger = logging.getLogger(self.__class__.__name__)
        self.recognizer = MediapipeGestureRecoginzer()
        self.queue = Queue(maxsize=1)

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_RCVBUF,
            self.BUFF_SIZE
        )

        self.logger.info("Server initialized")

    def start_server(self) -> None:
        self.socket.bind((self.ip, self.port))
        self.running = True
        self.logger.info(f"Server listening on {self.ip}:{self.port}")

    def _receive_data(self) -> np.ndarray:
        packet, _ = self.socket.recvfrom(self.BUFF_SIZE)
        return self._decode_opencv_frame(packet)

    def client_handle(self) -> None:
        while True:
            if not self.running:
                continue

            frame = self._receive_data()

            if frame is not None:
                self.enqueue(frame)

    def mediapipe_handle(self) -> None:
        prev_time = time.time()
        total_delta_x = 0

        while True:
            if not self.running:
                continue

            if self.queue.empty():
                continue

            frame = self.queue.get()
            results, frame_landmarks = self.recognizer.recognize_gesture(frame)

            if results.gestures:
                gesture = results.gestures[0][0].category_name

                if gesture == "Pointing_Up":
                    buffer = []
                    t_prev = time.time()

                    while len(buffer) < 22:
                        f = self.queue.get()
                        t_now = time.time()
                        buffer.append((f, t_now - t_prev))
                        t_prev = t_now

                    total_delta_x = 0
                    prev_x = 0

                    for i, (frm, _) in enumerate(buffer):
                        res, _ = self.recognizer.recognize_handmarks(frm)

                        if res.hand_landmarks:
                            x = res.hand_landmarks[0][8].x / 400.0 - 0.5

                            if i > 0:
                                total_delta_x += x - prev_x

                            prev_x = x

                    swipe = "swipe_right" if total_delta_x < 0 else "swipe_left"
                    self.recognizer.mediakeys_thread.gesture_queue.put(swipe)

                elif gesture != "None":
                    self.recognizer.mediakeys_thread.gesture_queue.put(gesture)

            now = time.time()
            dt = now - prev_time
            prev_time = now

            fps = int(1 / dt) if dt > 0 else 0

            if frame is not None:
                self._show_fps(frame, fps, dt)
                cv2.imshow("Server side", frame)

            if frame_landmarks is not None:
                self._show_fps(frame_landmarks, fps, dt)

                if total_delta_x != 0:
                    name = "swipe right" if total_delta_x < 0 else "swipe left"
                    cv2.putText(frame_landmarks, name, (20, 270),
                                cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow("Server side with landmarks", frame_landmarks)

            if cv2.waitKey(50) == ord("q"):
                self.close()
                break

    def _show_fps(self, frame, fps: int, dt: float) -> None:
        cv2.putText(frame, f"FPS: {fps}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.putText(frame, f"FrameTime: {dt:.3f}s", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def enqueue(self, item: np.ndarray) -> None:
        if self.queue.full():
            return
        self.queue.put(item)