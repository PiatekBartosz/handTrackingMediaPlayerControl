from helpers.UDP_factory import UDP_server

if __name__ == "__main__":
    server = UDP_server("192.168.0.29", 9999)
    server.start_server()
    server.client_handle()