# import cv2 
import socket
import argparse
from time import sleep

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


    def run(self) -> None:
        while True:
            self.send_message(self.test_mesasge)

    def send_message(self, message) -> None:
        if isinstance(message, str):
            message = message.encode('utf-8')

        self.client_socket.sendto(message, (self.host_ip, self.PORT))
        

if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="Pass ip of the server", default='localhost', 
                        type=str)
    parser.add_argument("-p", "--port", help="Pass port of the server", default=9999, type=int)
    args = parser.parse_args()

    client = UDP_client(args)
    client.run()
