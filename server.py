import cv2
import socket

class UDP_server:
    def __init__(self):

        # buffer size for UDP communcation, each OS has its own buffer size, 
        # we overwrite the defult one
        self.BUFF_SIZE = 655536 
        self.PORT = 9999
        self.host_name = socket.gethostname()
        self.host_ip = socket.gethostbyname(self.host_name)

    def start_server(self):
        # we create socket object, assign adress family & socket type
        # SOCK_STREAM type is used for TCP connection 
        # SOCK_DGRAM type is used for UDP connection
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
            self.socket_address = (self.host_ip, self.PORT) 
            self.socket.bind(self.socket_address)
            print(f"Server listening on {self.socket_address}")
        except Exception as e:
            print(e)
            exit()

    def receive_data(self):
        pass

    def send_response(self):
        pass

    def close(self):
        pass

    def handle_errors(self):
        pass


if __name__ == '__main__':
    server = UDP_server()
    server.start_server()

    while True:
        pass

