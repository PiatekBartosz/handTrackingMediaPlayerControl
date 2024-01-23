from helpers.UDP_factory import UDP_client
import argparse
import socket

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="Pass ip of the server",  type=str)
    parser.add_argument("-p", "--port", help="Pass port of the server", default=9999, type=int)
    args = parser.parse_args()

    if args.ip:
        client_ip = args.ip 
    else:
        tmp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        tmp_sock.connect(("9.9.9.9", 80))
        client_ip = tmp_sock.getsockname()[0]
        tmp_sock.close()

    if args.port:
        client_port = args.port
    else:
        client_port = 9999

    client = UDP_client(client_ip, client_port)
    client.client_routine()
