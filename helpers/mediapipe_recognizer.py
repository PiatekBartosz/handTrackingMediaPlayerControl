import cv2

class MediapipeRecoginzer:
    COLOR = [
        (0, 0, 255),   # Red
        (0, 128, 255), # Orange
        (0, 255, 255), # Yellow
        (0, 255, 0),   # Green
        (255, 128, 0), # Light Blue
        (255, 0, 0),   # Blue
        (255, 0, 128), # Purple
        (128, 0, 255), # Pink
        (0, 0, 128),   # Dark Red
        (0, 128, 128), # Dark Orange
        (0, 255, 128), # Dark Yellow
        (0, 128, 0),   # Dark Green
        (128, 128, 0), # Olive
        (128, 0, 128), # Dark Purple
        (128, 0, 0),   # Dark Blue
        (128, 0, 64),  # Dark Pink
        (64, 0, 128),  # Light Purple
        (64, 0, 0),    # Dark Brown
        (192, 192, 192), # Light Grey
        (128, 128, 128), # Grey
        (220, 220, 220)  # White
    ]

    def __init__(self, shared_queue):
        self.shared_queue = shared_queue  
        self.running = False    

    # thread routine
    def mediapipe_routine(self):
        while True:
            