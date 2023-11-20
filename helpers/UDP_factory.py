import cv2
import numpy as np
import base64
import socket
import imutils
from queue import Queue

class UDP_factory:
    BUFF_SIZE = 655536

    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port
        self.socket = None
        self.running = False

    # public methods
    def close(self) -> None:
        self.running = False
        self.socket.close()

    # private methods
    def _encode_opencv_frame(self, data_to_encode: np.ndarray) -> bytes:
        # encode opencv from into JPG file and then later into base64 format
        _, jpg_data = cv2.imencode(".jpg", data_to_encode,[cv2.IMWRITE_JPEG_QUALITY,80])
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
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
            self.running = True
        except Exception as e:
            raise(e)

    # thread routine
    def client_routine(self) -> None:
        cap = cv2.VideoCapture(0)

        while True:
            ret, frame = cap.read()

            if not ret:
                self.close()
                break

            frame = imutils.resize(frame, width=400) 
            cv2.imshow("Client side", frame)

            # resize the image so that it fits UDP communcation data size
            self._send_data(frame)
            print(f"Frame send on {self.ip}:{self.port}")
            
            if cv2.waitKey(1) == ord("q"):
                self.close()
                break
            

    def _send_data(self, data: np.ndarray) -> None:
        encoded_data = self._encode_opencv_frame(data)
        self.socket.sendto(encoded_data, (self.ip, self.port))
        

class UDP_server(UDP_factory):
    def __init__(self, ip: str, port: int) -> None:
        super().__init__(ip, port)
        self.queue = Queue(maxsize=10)
        
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
        except Exception as e: raise(e)

    def _receive_data(self) -> np.ndarray:
        packet, _ = self.socket.recvfrom(self.BUFF_SIZE)
        return self._decode_opencv_frame(packet)

    def start_server(self) -> None:
        try:
            self.socket.bind((self.ip, self.port))
            print(f"Server listening on {self.ip}:{self.port}")
            self.running = True
        except Exception as e:
            raise(e)

    # threadroutine
    def client_handle(self) -> None:
        while True:
            if self.running:
                frame = self._receive_data()
                cv2.imshow("Server side", frame)
                if cv2.waitKey(1) == ord("q"):
                    self.close()
                    break

    def enqueue(self, item: np.ndarray) -> None:
        if self.queue.full:
            self.queue.get()
        self.queue.put(item)

    def dequeue(self):
        return self.queue.get()
        
