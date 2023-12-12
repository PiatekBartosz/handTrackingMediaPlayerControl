from helpers.UDP_factory import UDP_server
from queue import Queue
from argparse import ArgumentParser
import threading
import socket

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--ip", help="Server ip",  type=str)
    parser.add_argument("-p", "--port", help="Server port", default=9999, type=int)
    args = parser.parse_args()

    if args.ip:
        server_ip = args.ip 
    else:
        # server_ip = "localhost"
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp_sock.connect(("9.9.9.9", 80))
        server_ip = tmp_sock.getsockname()[0]
        tmp_sock.close()

    if args.port:
        server_port = args.port
    else:
        server_port = 9999

    server = UDP_server(server_ip, server_port)
    server.start_server()

    # server thread
    server_thread = threading.Thread(target=server.client_handle)
    server_thread.start()

    # mediapipe thread
    mediapipe_thread = threading.Thread(target=server.mediapipe_handle)
    mediapipe_thread.start()

    # mediakeys thread
    server.recognizer.mediakeys_thread.start()
