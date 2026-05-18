import os
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
import urllib.request
from pathlib import Path
from pynput.keyboard import Key, Controller
import threading
from queue import Queue, Empty
from collections import defaultdict

# ---------------------------------------------------------------------------
# Automatyczne pobieranie modeli MediaPipe
# ---------------------------------------------------------------------------

_MODEL_DIR = Path(__file__).resolve().parent.parent / "model"

_MODEL_URLS = {
    "gesture_recognizer.task": (
        "https://storage.googleapis.com/mediapipe-models/"
        "gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
    ),
    "hand_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/"
        "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    ),
}


def _ensure_model(filename: str) -> str:
    """Zwraca ścieżkę do pliku modelu, pobierając go jeśli nie istnieje."""
    _MODEL_DIR.mkdir(exist_ok=True)
    dest = _MODEL_DIR / filename
    if not dest.exists():
        url = _MODEL_URLS[filename]
        print(f"[MediaPipe] Pobieranie modelu {filename} ...", flush=True)

        def _progress(count, block, total):
            if total > 0:
                pct = min(int(count * block * 100 / total), 100)
                print(f"\r[MediaPipe] {filename}: {pct}%", end="", flush=True)

        urllib.request.urlretrieve(url, dest, reporthook=_progress)
        size_mb = dest.stat().st_size / 1_048_576
        print(f"\r[MediaPipe] Pobrano {filename} ({size_mb:.1f} MB)    ")
    return str(dest)


class GestureMetrics:
    """Tracks per-gesture confidence scores and frame-level detection rates."""

    _COL = 58  # table width

    def __init__(self):
        self._lock = threading.Lock()
        self.frames_total: int = 0
        self.frames_with_hand: int = 0
        self.actions_sent: int = 0
        self._session_start: float = time.time()
        # name -> {"count", "conf_sum", "conf_min", "conf_max"}
        self._stats: dict = defaultdict(lambda: {
            "count": 0, "conf_sum": 0.0, "conf_min": 1.0, "conf_max": 0.0
        })
        self._reporter_running: bool = False

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def record_frame(self, has_hand: bool) -> None:
        with self._lock:
            self.frames_total += 1
            if has_hand:
                self.frames_with_hand += 1

    def record_gesture(self, name: str, confidence: float) -> None:
        with self._lock:
            s = self._stats[name]
            s["count"] += 1
            s["conf_sum"] += confidence
            s["conf_min"] = min(s["conf_min"], confidence)
            s["conf_max"] = max(s["conf_max"], confidence)

    def record_action(self) -> None:
        with self._lock:
            self.actions_sent += 1

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def hand_detection_rate(self) -> float:
        return self.frames_with_hand / self.frames_total if self.frames_total else 0.0

    @property
    def session_duration(self) -> float:
        return time.time() - self._session_start

    # ------------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------------

    def _build_table(self, ts: str = "") -> str:
        w = self._COL
        dur = self.session_duration
        lines = [
            "=" * w,
            "  GESTURE RECOGNITION METRICS",
            "=" * w,
        ]
        if ts:
            lines.append(f"  Timestamp        : {ts}")
        lines += [
            f"  Czas sesji       : {int(dur // 60):02d}:{int(dur % 60):02d}",
            f"  Klatki           : {self.frames_total}",
            f"  Ręka wykryta     : {self.frames_with_hand}  ({self.hand_detection_rate * 100:.1f}%)",
            f"  Akcje wysłane    : {self.actions_sent}",
            "-" * w,
            f"  {'Gest':<22} {'Ilość':>5}  {'Śr.':>6}  {'Min':>6}  {'Max':>6}",
            "-" * w,
        ]
        with self._lock:
            gesture_rows = [
                (name, s) for name, s in sorted(self._stats.items())
                if name != "None"
            ]
        if gesture_rows:
            for name, s in gesture_rows:
                avg = s["conf_sum"] / s["count"] if s["count"] else 0.0
                lines.append(
                    f"  {name:<22} {s['count']:>5}"
                    f"  {avg * 100:>5.1f}%  {s['conf_min'] * 100:>5.1f}%  {s['conf_max'] * 100:>5.1f}%"
                )
        else:
            lines.append("  (brak danych)")
        lines.append("=" * w)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Console live reporter
    # ------------------------------------------------------------------

    def start_console_reporter(self, interval: float = 5.0) -> None:
        """Starts a daemon thread that reprints stats to the console every `interval` seconds."""
        self._reporter_running = True

        def _loop():
            while self._reporter_running:
                time.sleep(interval)
                if not self._reporter_running:
                    break
                os.system("cls" if os.name == "nt" else "clear")
                print(self._build_table(ts=time.strftime("%H:%M:%S")))
                print(f"\n  [Odświeżanie co {interval:.0f}s — Ctrl+C aby zatrzymać]\n")

        t = threading.Thread(target=_loop, daemon=True, name="MetricsReporter")
        t.start()

    def stop_console_reporter(self) -> None:
        self._reporter_running = False

    # ------------------------------------------------------------------
    # Final output
    # ------------------------------------------------------------------

    def print_summary(self) -> None:
        """Prints the final metrics table to stdout."""
        print("\n" + self._build_table(ts=time.strftime("%Y-%m-%d %H:%M:%S")))

    def save_to_file(self, path: str = "stats.txt") -> None:
        """Saves the final metrics table to a text file."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        content = self._build_table(ts=ts)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        print(f"[INFO] Statystyki zapisane do: {path}")


class KeypressThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.gesture_queue = Queue(1)
        self.keyborad_controller = Controller()
        self.key_pressed = False
        self.running = True
        self.daemon = True  # exits automatically when main thread ends

    def run(self):
        while self.running:
            try:
                gesture = self.gesture_queue.get(timeout=0.2)
            except Empty:
                continue

            if gesture == "swipe_right":
                key = Key.media_next
            elif gesture == "swipe_left":
                key = Key.media_previous
            elif gesture == "Closed_Fist":
                key = Key.media_play_pause
            elif gesture == "Thumb_Up":
                key = Key.media_volume_up
            elif gesture == "Thumb_Down":
                key = Key.media_volume_down
            else:
                continue

            self.keyborad_controller.press(key)
            self.key_pressed = True
            time.sleep(0.5)
            self.keyborad_controller.release(key)
            self.key_pressed = False


class MediapipeGestureRecoginzer:
    COLOR = [
        (0, 0, 255),   # Red
        (0, 128, 255),  # Orange
        (0, 255, 255),  # Yellow
        (0, 255, 0),   # Green
        (255, 128, 0),  # Light Blue
        (255, 0, 0),   # Blue
        (255, 0, 128),  # Purple
        (128, 0, 255),  # Pink
        (0, 0, 128),   # Dark Red
        (0, 128, 128),  # Dark Orange
        (0, 255, 128),  # Dark Yellow
        (0, 128, 0),   # Dark Green
        (128, 128, 0),  # Olive
        (128, 0, 128),  # Dark Purple
        (128, 0, 0),   # Dark Blue
        (128, 0, 64),  # Dark Pink
        (64, 0, 128),  # Light Purple
        (64, 0, 0),    # Dark Brown
        (192, 192, 192),  # Light Grey
        (128, 128, 128),  # Grey
        (220, 220, 220)  # White
    ]

    def __init__(self):
        self.running = False

        # Gesture recognizer model #############################################
        self.BaseOptions = mp.tasks.BaseOptions
        self.GestureRecognizer = mp.tasks.vision.GestureRecognizer
        self.GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
        self.VisionRunningMode = mp.tasks.vision.RunningMode

        self.gesture_options = self.GestureRecognizerOptions(
            base_options=self.BaseOptions(
                model_asset_path=_ensure_model("gesture_recognizer.task")),
            running_mode=self.VisionRunningMode.IMAGE)

        # Hand landmarks recognizer model ######################################
        VisionRunningMode = mp.tasks.vision.RunningMode
        base_options = python.BaseOptions(
            model_asset_path=_ensure_model("hand_landmarker.task"))
        self.hand_options = vision.HandLandmarkerOptions(
            base_options=base_options, running_mode=VisionRunningMode.IMAGE)

        # Keyboard control #####################################################
        self.mediakeys_thread = KeypressThread()

        # Metrics ##############################################################
        self.metrics = GestureMetrics()

    def start(self):
        self.running = True
        self.mediakeys_thread.start()

    def stop(self):
        self.mediakeys_thread.join()
        self.running = False

    def draw_handmarks(self, frame, results) -> np.ndarray:
        if results.hand_landmarks == []:
            return frame

        h, w, _ = frame.shape
        landmarks_points = []
        landmarks_list = results.hand_landmarks[0]

        # draw points for landmarks
        for idx, item in enumerate(landmarks_list):
            # convert normalized value to point on a frame
            x_frame = int(item.x * w)
            y_frame = int(item.y * h)
            landmarks_points.append((x_frame, y_frame))
            cv2.circle(frame, (x_frame, y_frame), 3, self.COLOR[idx], 2)

        # connect points
        connection_color = (20, 20, 20)
        # draw thumb -> landmarks <0, 4>
        for i in range(0, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+1], connection_color, 2)

        # draw palm
        cv2.line(frame, landmarks_points[0],
                landmarks_points[5], connection_color, 2)
        cv2.line(frame, landmarks_points[0],
                landmarks_points[17], connection_color, 2)
        for i in range(5, 17, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+4], connection_color, 2)

        # draw fingers
        for i in range(5, 21, 4):
            for j in range(3):
                cv2.line(
                    frame, landmarks_points[i+j], landmarks_points[i+j+1], connection_color, 2)
        return frame

    def draw_handmarks_and_gesture(self, frame, results) -> np.ndarray:
        if results.hand_landmarks == []:
            return frame

        h, w, _ = frame.shape
        landmarks_points = []
        landmarks_list = results.hand_landmarks[0]

        if results.gestures:
            gesture = results.gestures[0][0].category_name
            # TODO classify gesture

        else:
            gesture = None

        # draw points for landmarks
        for idx, item in enumerate(landmarks_list):
            # convert normalized value to point on a frame
            x_frame = int(item.x * w)
            y_frame = int(item.y * h)
            landmarks_points.append((x_frame, y_frame))
            cv2.circle(frame, (x_frame, y_frame), 3, self.COLOR[idx], 2)

        # connect points
        connection_color = (20, 20, 20)
        # draw thumb -> landmarks <0, 4>
        for i in range(0, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+1], connection_color, 2)

        # draw palm
        cv2.line(frame, landmarks_points[0],
                 landmarks_points[5], connection_color, 2)
        cv2.line(frame, landmarks_points[0],
                 landmarks_points[17], connection_color, 2)
        for i in range(5, 17, 4):
            cv2.line(
                frame, landmarks_points[i], landmarks_points[i+4], connection_color, 2)

        # draw fingers
        for i in range(5, 21, 4):
            for j in range(3):
                cv2.line(
                    frame, landmarks_points[i+j], landmarks_points[i+j+1], connection_color, 2)

        # print gesture name
        if gesture != None:
            cv2.putText(frame, gesture, (20, 200),
                        cv2.FONT_HERSHEY_COMPLEX, 1, self.COLOR[3], 2)

        return frame

    def recognize_gesture(self, frame):
        frame_cpy = frame.copy()
        frame_cpy_inverted_channels = cv2.cvtColor(
            frame_cpy, cv2.COLOR_BGR2RGB)
        with self.GestureRecognizer.create_from_options(self.gesture_options) as recognizer:
            mp_frame = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=frame_cpy_inverted_channels)
            results = recognizer.recognize(mp_frame)

            has_hand = bool(results.hand_landmarks)
            self.metrics.record_frame(has_hand)
            if results.gestures:
                cat = results.gestures[0][0]
                self.metrics.record_gesture(cat.category_name, cat.score)

            frame_with_landmarks = self.draw_handmarks_and_gesture(
                frame_cpy, results)
            return results, frame_with_landmarks

    def recognize_handmarks(self, frame):
        frame_cpy = frame.copy()
        frame_cpy_inverted_channels = cv2.cvtColor(
            frame_cpy, cv2.COLOR_BGR2RGB)
        with vision.HandLandmarker.create_from_options(self.hand_options) as hand_landmarks:
            mp_frame = mp.Image(
                image_format=mp.ImageFormat.SRGB, data=frame_cpy_inverted_channels)
            results = hand_landmarks.detect(mp_frame)
            frame_with_landmarks = self.draw_handmarks(frame_cpy, results)
            return results, frame_with_landmarks
