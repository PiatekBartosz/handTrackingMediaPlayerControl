# import cv2 
import socket
import argparse
from time import sleep

class UDP_client:
    def __init__(self) -> None:
        self.text_message = b"Test message"
    
        # buffer size for UDP communcation, each OS has its own buffer size, 
        # we overwrite the defult one
        self.BUFF_SIZE = 655536 
        self.PORT = 9999

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)        


    def run(self) -> None:
        while True:
            self.send_str(self.send_message)
            sleep(100)

    def send_message(self, message) -> None:
        if isinstance(message, bytes):
            bytes(message)

        self.client_socket.sendto(message, (self.host_ip, self.PORT))
        

if __name__ == "__main__":

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="Pass ip of the server", default=socket.gethostbyname, 
                        type=str)
    parser.add_argument("-p", "--port", help="Pass port of the server", default=9999, type=int)
    args = parser.parse_args()

    client = UDP_client()
    client.run()
