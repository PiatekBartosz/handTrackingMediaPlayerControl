import sys
import argparse
import socket
from loguru import logger
from helpers.UDP_factory import UDP_client

logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level:<8} | {message}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="Pass ip of the server", default="localhost", type=str)
    parser.add_argument("-p", "--port", help="Pass port of the server", default=9999, type=int)
    args = parser.parse_args()

    if args.ip:
        client_ip = args.ip
    else:
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp_sock.connect(("9.9.9.9", 80))
        client_ip = tmp_sock.getsockname()[0]
        tmp_sock.close()

    client_port = args.port if args.port else 9999

    client = UDP_client(client_ip, client_port)

    try:
        client.client_routine()

    except KeyboardInterrupt:
        logger.info("Client shutting down...")

        if hasattr(client, "running"):
            client.running = False

        if hasattr(client, "sock"):
            client.sock.close()

        logger.info("Client stopped.")
