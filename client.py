import cv2 
import socket
import argparse
from time import sleep
import numpy as np
import base64
# import imutils

class UDP_client:
    def __init__(self, args) -> None:
        self.test_mesasge = b"Test message"
        self.host_ip = args.ip

        # buffer size for UDP communcation, each OS has its own buffer size, 
        # we overwrite the defult one
        self.BUFF_SIZE = 655536 
        self.PORT = args.port

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)

    def run(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret,frame = cap.read()
            # frame = imutils.resize(frame,width=400) # optional frame resize
            if not ret:
                break            

            cv2.imshow("Client", frame)
            self.send_data(frame)
            print(f"Frame sent on {self.host_ip}:{self.PORT}")
            if cv2.waitKey(1) == ord("q"):
                break

    def send_data(self, data):
        encoded_data = self.encode_opencv_frame(data)
        self.client_socket.sendto(encoded_data, (self.host_ip, self.PORT))

    def receive_data(self):
        # TODO
        pass

    def close_connection(self):
        self.client_socket.close()

    def handle_errors(self):
        # TODO
        pass

    def encode_opencv_frame(self, data_to_encode):
        # encode opencv from into JPG file and then later into base64 format
        _, jpg_data = cv2.imencode(".jpg", data_to_encode,[cv2.IMWRITE_JPEG_QUALITY,80])
        base64message = base64.b64encode(jpg_data)
        return base64message

    def decode_opencv_frame(self, packet):
        # decode binary data into opencv frame
        data = base64.b64decode(packet, ' /')
        npdata = np.fromstring(data, dtype=np.uint8)
        frame = cv2.imdecode(npdata, 1)
        return frame

    def is_opencv_frame(self, item):
        if isinstance(item, np.ndarray):
            if len(item.shape) == 2 or (len(item.shape) == 3 and item.shape[2] in [1, 3, 4]):
                return True
        return False


if __name__ == "__main__":
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="Pass ip of the server", default='localhost', 
                        type=str)
    parser.add_argument("-p", "--port", help="Pass port of the server", default=9999, type=int)
    args = parser.parse_args()

    client = UDP_client(args)
    client.run()
