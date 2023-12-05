import cv2
import numpy as np
import base64
import socket
import imutils
import time
from queue import Queue
from .mediapipe_recognizer import MediapipeRecoginzer
# only for debugging
import pickle


class UDP_factory:
    BUFF_SIZE = 655536

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.socket = None
        self.running = False

    # public methods
    def close(self) -> None:
        self.socket.close()
        self.running = False

    # private methods
    def _encode_opencv_frame(self, data_to_encode: np.ndarray) -> bytes:
        # encode opencv from into JPG file and then later into base64 format
        _, jpg_data = cv2.imencode(".jpg", data_to_encode, [
                                   cv2.IMWRITE_JPEG_QUALITY, 80])
        base64message = base64.b64encode(jpg_data)
        return base64message

    def _decode_opencv_frame(self, data_to_decode: bytes) -> np.ndarray:
        data = base64.b64decode(data_to_decode, ' /')
        npdata = np.fromstring(data, dtype=np.uint8)
        frame = cv2.imdecode(npdata, 1)
        return frame


class UDP_client(UDP_factory):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
            self.running = True
        except Exception as e:
            raise (e)

    # thread routine
    def client_routine(self) -> None:
        cap = cv2.VideoCapture(0)

        # doesn't work on Windows?
        cap.set(cv2.CAP_PROP_FPS, 20)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)

        prev_time = 0
        new_time = 0

        while True:
            ret, frame = cap.read()

            if not ret:
                self.close()
                break

            frame = imutils.resize(frame, width=400)
            frame_raw = frame.copy()

            # FPS counter
            new_time = time.time()
            frame_time = new_time - prev_time
            if frame_time > 0:
                FPS_count = 1 // frame_time
            else:
                FPS_count = -1
            prev_time = new_time

            self.show_FPS(frame, FPS_count, frame_time)
            cv2.imshow("Client side", frame)

            # resize the image so that it fits UDP communcation data size
            self._send_data(frame_raw)
            print(f"Frame send on {self.ip}:{self.port}")

            if cv2.waitKey(1) == ord("q"):
                self.close()
                break

    def show_FPS(self, frame, FPS_count: int, FrameTime: float) -> None:
        frame = cv2.putText(
            frame, f"FPS: {FPS_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        frame = cv2.putText(frame, f"FrameTime: {FrameTime:.2f}", (
            10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def _send_data(self, data: np.ndarray) -> None:
        encoded_data = self._encode_opencv_frame(data)
        self.socket.sendto(encoded_data, (self.ip, self.port))


class UDP_server(UDP_factory):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        self.recognizer = MediapipeRecoginzer()
        self.queue = Queue(maxsize=1)

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
        except Exception as e:
            raise (e)

    def _receive_data(self) -> np.ndarray:
        packet, _ = self.socket.recvfrom(self.BUFF_SIZE)
        return self._decode_opencv_frame(packet)

    def start_server(self) -> None:
        try:
            self.socket.bind((self.ip, self.port))
            print(f"Server listening on {self.ip}:{self.port}")
            self.running = True
        except Exception as e:
            raise (e)

    # threadroutine
    def client_handle(self) -> None:
        while True:
            if self.running:
                frame = self._receive_data()

                if frame is not None:
                    self.enqueue(frame)

    def mediapipe_handle(self) -> None:
        prev_time = 0
        new_time = 0
        while True:
            if self.running:
                if not self.queue.empty():
                    frame = self.queue.get()
                    results, frame_with_landmarks = self.recognizer.recognize(
                        frame)

                    if results.gestures != []:
                        gesture = results.gestures[0][0].category_name

                        if gesture == "Pointing_Up":
                            frame_buffer = []

                            prev_frame_timer = 0
                            next_frame_timer = 0

                            # TODO check if code viable
                            while len(frame_buffer) < 40:
                                next_frame_timer = time.time()
                                frame_buffer.append(
                                    (self.queue.get(), next_frame_timer - prev_frame_timer))

                                prev_frame_timer = next_frame_timer

                            detection_buffer = []

                            # detection of buffer
                            for tup in frame_buffer:
                                frame = tup[0]
                                results, frame_with_landmarks = self.recognizer.recognize(
                                    frame)
                                detection_buffer.append(results)

                            with open("frame_data.pickle", "wb") as f:
                                pickle.dump(frame_buffer, f)

                            with open("detection_data.pickle", "wb") as f:
                                pickle.dump(detection_buffer, f)

                            pass

                    # FPS counter
                    new_time = time.time()
                    frame_time = new_time - prev_time
                    if frame_time > 0:
                        FPS_count = 1 // frame_time
                    else:
                        FPS_count = -1
                    prev_time = new_time

                    if frame is not None:
                        self.show_FPS(frame, FPS_count, frame_time)
                        cv2.imshow("Server side", frame)

                    if frame_with_landmarks is not None:
                        self.show_FPS(frame_with_landmarks,
                                      FPS_count, frame_time)
                        cv2.imshow("Server side with landmarks",
                                   frame_with_landmarks)

                    if cv2.waitKey(50) == ord("q"):
                        self.close()
                        break

    def show_FPS(self, frame, FPS_count: int, FrameTime: float) -> None:
        frame = cv2.putText(
            frame, f"FPS: {FPS_count}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        frame = cv2.putText(frame, f"FrameTime: {FrameTime:.2f} ms", (
            10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def enqueue(self, item: np.ndarray) -> None:
        if self.queue.full():
            # self.queue.get()
            return
        self.queue.put(item)
