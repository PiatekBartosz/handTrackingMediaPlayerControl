import sys
import threading
import socket
import time
from argparse import ArgumentParser
from loguru import logger
from helpers.UDP_factory import UDP_server

if __name__ == "__main__":
    logger.remove()
    logger.add(sys.stderr, format="{time:HH:mm:ss} | {level:<8} | {message}")
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

    server_thread = threading.Thread(target=server.client_handle, daemon=True)
    mediapipe_thread = threading.Thread(target=server.mediapipe_handle, daemon=True)

    server_thread.start()
    mediapipe_thread.start()
    server.recognizer.mediakeys_thread.start()
    server.recognizer.metrics.start_console_reporter(interval=5.0)

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")

        server.running = False
        server.recognizer.mediakeys_thread.running = False
        server.recognizer.metrics.stop_console_reporter()
        server.socket.close()

        server_thread.join(timeout=3)
        mediapipe_thread.join(timeout=3)

        server.recognizer.metrics.print_summary()
        server.recognizer.metrics.save_to_file("stats.txt")
        logger.success("Server stopped cleanly.")