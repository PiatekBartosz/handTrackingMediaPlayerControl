"""
Skrypt pobierający modele MediaPipe wymagane przez projekt.

Użycie:
    uv run download_models.py
    # lub
    python download_models.py
"""

import urllib.request
import os
import sys

MODELS = {
    "gesture_recognizer.task": (
        "https://storage.googleapis.com/mediapipe-models/"
        "gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task"
    ),
    "hand_landmarker.task": (
        "https://storage.googleapis.com/mediapipe-models/"
        "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
    ),
}

MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")


def download(name: str, url: str) -> None:
    dest = os.path.join(MODEL_DIR, name)

    if os.path.exists(dest):
        print(f"[POMIŃ]  {name} – już istnieje")
        return

    print(f"[POBIERZ] {name} ...", end=" ", flush=True)

    def progress(count, block_size, total_size):
        if total_size > 0:
            pct = int(count * block_size * 100 / total_size)
            print(f"\r[POBIERZ] {name} ... {min(pct, 100)}%", end="", flush=True)

    try:
        urllib.request.urlretrieve(url, dest, reporthook=progress)
        size_mb = os.path.getsize(dest) / 1_048_576
        print(f"\r[OK]     {name} ({size_mb:.1f} MB)")
    except Exception as exc:
        print(f"\r[BŁĄD]   {name}: {exc}")
        if os.path.exists(dest):
            os.remove(dest)
        sys.exit(1)


if __name__ == "__main__":
    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"Folder docelowy: {MODEL_DIR}\n")

    for model_name, model_url in MODELS.items():
        download(model_name, model_url)

    print("\nGotowe. Możesz teraz uruchomić serwer.")
