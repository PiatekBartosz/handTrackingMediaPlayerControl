import sys
import cv2
import time
from pathlib import Path
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level:<8} | {message}")

GESTURES     = ["Thumb_Up", "Thumb_Down", "Closed_Fist"]
N_FRAMES     = 40
COUNTDOWN    = 3       # seconds before capture starts
INTERVAL_MS  = 150     # ms between consecutive frames

DATASET_DIR = Path(__file__).resolve().parent / "dataset"


def _put_text(frame, lines: list[tuple[str, tuple, float, int]]) -> None:
    # dark outline + white text for readability on any background
    for text, pos, scale, thickness in lines:
        cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                    scale, (0, 0, 0), thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, text, pos, cv2.FONT_HERSHEY_SIMPLEX,
                    scale, (255, 255, 255), thickness, cv2.LINE_AA)


def collect() -> None:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error("Cannot open camera.")
        sys.exit(1)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    for gesture in GESTURES:
        gesture_dir = DATASET_DIR / gesture
        gesture_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Prepare gesture: {gesture} — press SPACE to start, Q to quit")

        # waiting phase — user positions their hand
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            _put_text(frame, [
                (f"Gesture: {gesture}", (20, 50), 1.2, 2),
                ("Press SPACE to start", (20, 100), 0.7, 1),
                ("Q = quit", (20, 140), 0.6, 1),
            ])
            cv2.imshow("Dataset collection", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord(" "):
                break
            if key == ord("q"):
                cap.release()
                cv2.destroyAllWindows()
                logger.info("Stopped by user.")
                sys.exit(0)

        # countdown before capture
        deadline = time.time() + COUNTDOWN
        while time.time() < deadline:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            remaining = int(deadline - time.time()) + 1
            _put_text(frame, [
                (f"Gesture: {gesture}", (20, 50), 1.2, 2),
                (f"Starting in: {remaining}", (20, 110), 2.0, 3),
            ])
            cv2.imshow("Dataset collection", frame)
            cv2.waitKey(1)

        # frame capture loop
        saved = 0
        last_capture = 0.0
        logger.info(f"Capturing {N_FRAMES} frames for '{gesture}'...")

        while saved < N_FRAMES:
            ret, frame = cap.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)
            now = time.time()

            if now - last_capture >= INTERVAL_MS / 1000.0:
                cv2.imwrite(str(gesture_dir / f"{saved:03d}.jpg"), frame)
                saved += 1
                last_capture = now

            _put_text(frame, [
                (f"Gesture: {gesture}", (20, 50), 1.2, 2),
                (f"Saved: {saved}/{N_FRAMES}", (20, 100), 0.8, 1),
            ])
            # progress bar
            bar_w = int(560 * saved / N_FRAMES)
            cv2.rectangle(frame, (40, 440), (600, 465), (80, 80, 80), -1)
            cv2.rectangle(frame, (40, 440), (40 + bar_w, 465), (0, 200, 80), -1)
            cv2.imshow("Dataset collection", frame)
            cv2.waitKey(1)

        logger.success(f"Saved {saved} frames -> {gesture_dir}")

    cap.release()
    cv2.destroyAllWindows()
    logger.success(f"Dataset saved to: {DATASET_DIR}")


if __name__ == "__main__":
    collect()
