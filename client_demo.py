from helpers.UDP_factory import UDP_client

if __name__ == "__main__":
    client = UDP_client("192.168.0.29", 9999)
    client.client_routine()
