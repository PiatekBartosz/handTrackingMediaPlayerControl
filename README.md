# Hand Gesture Media Player Control

## Description

A Python application that lets you control a media player remotely using hand gesture recognition. The server processes the camera feed from the client and sends the corresponding media key presses.

Supported gestures:

| Gesture | Action |
|---------|--------|
| Pointing Up + swipe right | Next track |
| Pointing Up + swipe left | Previous track |
| Closed Fist | Play / pause |
| Thumb Up | Volume up |
| Thumb Down | Volume down |

## Prerequisites

- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — package manager

> **MediaPipe models** are downloaded automatically on the first server run. You can also download them manually with `uv run download_models.py`.

---

## Option 1 — run with uv (development mode)

### 1. Install uv

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Install dependencies

In the project directory run:

```bash
uv sync
```

uv automatically creates a virtual environment and installs all dependencies from `pyproject.toml`.

### 3. Start the server

```bash
uv run server_demo.py
```

Optionally with a custom IP and port:

```bash
uv run server_demo.py --ip 192.168.1.10 --port 9999
```

### 4. Start the client (in a separate terminal)

```bash
uv run client_demo.py
```

Optionally pointing at the server address:

```bash
uv run client_demo.py --ip 192.168.1.10 --port 9999
```

> **Note:** server and client must be run in separate terminals.

Pressing **Ctrl+C** on the server will shut it down cleanly and save gesture session statistics to `stats.txt`.

---

## Option 2 — install from a wheel package

### 1. Build the package

```bash
# Windows
build.bat

# macOS / Linux
chmod +x build.sh
./build.sh
```

The `.whl` file will be generated in the `dist/` folder.

### 2. Install the package

```bash
pip install dist/hand_tracking_media_player_control-0.1.0-*.whl
```

Or using uv:

```bash
uv pip install dist/hand_tracking_media_player_control-0.1.0-*.whl
```

### 3. Run the scripts

After installing the package, run the scripts from the project directory (models are downloaded automatically on first start):

```bash
python server_demo.py
python client_demo.py
```

---

## Benchmarks

The `benchmarks/` folder contains scripts for evaluating the gesture recognizer. Before running the confusion matrix or lighting benchmarks you need to collect a labelled dataset first.

### 1. Collect dataset

Opens the webcam and records 40 frames per gesture (Thumb_Up, Thumb_Down, Closed_Fist). Repeat for each gesture when prompted.

```bash
uv run benchmarks/collect_dataset.py
```

### 2. Run benchmarks

```bash
uv run benchmarks/benchmark_confusion.py   # accuracy and confusion matrix
uv run benchmarks/benchmark_lighting.py    # accuracy vs. brightness offset
uv run benchmarks/benchmark_latency.py     # processing time statistics
```

Results (PNG plots + TXT reports) are saved to `benchmarks/results/`.

---

## Project structure

```
handTrackingMediaPlayerControl/
├── helpers/
│   ├── __init__.py
│   ├── UDP_factory.py              # UDP client and server classes
│   └── mediapipe_recognizer.py     # MediaPipe gesture recognition + session metrics
├── benchmarks/
│   ├── collect_dataset.py          # Webcam dataset collection tool
│   ├── benchmark_confusion.py      # Confusion matrix benchmark
│   ├── benchmark_lighting.py       # Lighting robustness benchmark
│   ├── benchmark_latency.py        # Latency benchmark
│   ├── dataset/                    # Captured gesture images (git-ignored)
│   └── results/                    # Benchmark outputs — plots and reports (git-ignored)
├── model/                          # Created automatically on first run (git-ignored)
│   ├── gesture_recognizer.task
│   └── hand_landmarker.task
├── server_demo.py                  # Server entry point
├── client_demo.py                  # Client entry point
├── download_models.py              # Manual model download script
├── pyproject.toml                  # Project config and dependencies
├── build.bat                       # Build script (Windows)
└── build.sh                        # Build script (macOS/Linux)
```
