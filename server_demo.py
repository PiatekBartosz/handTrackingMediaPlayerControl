from helpers.UDP_factory import UDP_server
from argparse import ArgumentParser
import threading
import socket
import time

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--ip", help="Server ip", default="localhost", type=str)
    parser.add_argument("-p", "--port", help="Server port", default=9999, type=int)
    args = parser.parse_args()

    if args.ip:
        server_ip = args.ip
    else:
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp_sock.connect(("9.9.9.9", 80))
        server_ip = tmp_sock.getsockname()[0]
        tmp_sock.close()

    server_port = args.port if args.port else 9999

    server = UDP_server(server_ip, server_port)
    server.start_server()

    server_thread = threading.Thread(target=server.client_handle)
    mediapipe_thread = threading.Thread(target=server.mediapipe_handle)

    server_thread.start()
    mediapipe_thread.start()
    server.recognizer.mediakeys_thread.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")

        server.running = False

        if hasattr(server, "sock"):
            server.sock.close()

        server_thread.join()
        mediapipe_thread.join()

        if server.recognizer.mediakeys_thread.is_alive():
            server.recognizer.mediakeys_thread.join()

        print("[INFO] Server stopped cleanly.")