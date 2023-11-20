from helpers.UDP_factory import UDP_server
from helpers.mediapipe_recoginzer import MediapipeRecoginzer
from queue import Queue
import threading

def server_routine():
    server.server_handle

def mediapipe_routine():
    pass

if __name__ == "__main__":
    server = UDP_server("192.168.0.29", 9999)
    # TODO passing a method via arguments
    mediapipe = MediapipeRecoginzer(server.dequeue) 

    server.start_server()
    server_thread = threading.Thread(target=server_routine) 
    server_thread.start()
    
    mediapipe_thread = threading.Thread(target=mediapipe_routine)
    mediapipe_thread.start()
