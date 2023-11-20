import cv2
import socket
import numpy as np
import base64

class UDP_server:
    def __init__(self):

        # buffer size for UDP communcation, each OS has its own buffer size, 
        # we overwrite the default one
        self.BUFF_SIZE = 655536 
        self.PORT = 9999
        self.host_name = socket.gethostname()
        # self.host_ip = socket.gethostbyname(self.host_name)
        self.host_ip = "localhost"
        self.client_connected = False
        self.server_socket = None
        self.socket_address = None

    def start_server(self):
        # we create socket object, assign adress family & socket type
        # SOCK_STREAM type is used for TCP connection 
        # SOCK_DGRAM type is used for UDP connection
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
            self.socket_address = (self.host_ip, self.PORT) 
            self.server_socket.bind(self.socket_address)
            print(f"Server listening on {self.socket_address}")
        except Exception as e:
            print(e)
            exit()

    def client_handle(self):
        while True:
            frame = self.receive_data()
            
            cv2.imshow("Server side", frame)
           
            if cv2.waitKey(1) == ord("q"):
                break

    def receive_data(self):
        packet, _ = self.server_socket.recvfrom(self.BUFF_SIZE)
        return self.decode_opencv_frame(packet)

    def send_response(self):
        # TODO
        pass

    def close(self):
        self.server_socket.close()

    def handle_errors(self):
        # TODO handle errors
        pass

    def encode_opencv_frame(self, data_to_encode):
        # encode opencv from into JPG file and then later into binary data
        _, jpg_data = cv2.imencode(".jpg", data_to_encode)
        binary_data = jpg_data.tobytes()
        return binary_data

    def decode_opencv_frame(self, packet):
        # decode binary data into opencv frame
        data = base64.b64decode(packet, ' /')
        npdata = np.fromstring(data, dtype=np.uint8)
        frame = cv2.imdecode(npdata, 1)
        return frame


if __name__ == '__main__':
    server = UDP_server()
    server.start_server()
    server.client_handle()

