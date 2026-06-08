import sys
import time
import argparse
import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from helpers.mediapipe_recognizer import _ensure_model

logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level:<8} | {message}")

N_WARMUP  = 10    # initial iterations discarded (JIT warm-up)
N_RUNS    = 100
FRAME_W   = 400
FRAME_H   = 300

OUTPUT_DIR = Path(__file__).resolve().parent / "results"


def _synthetic_frame() -> np.ndarray:
    # grayscale gradient — minimal input for timing without camera data
    frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
    for x in range(FRAME_W):
        frame[:, x, :] = int(x / FRAME_W * 220)
    return frame


def _stats(data: list[float]) -> tuple[float, float, float, float, float, float]:
    a = np.array(data)
    return float(a.mean()), float(np.median(a)), float(a.std()), \
           float(a.min()), float(a.max()), float(np.percentile(a, 95))


def run(image_path: str | None = None) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    if image_path:
        frame_bgr = cv2.imread(image_path)
        if frame_bgr is None:
            logger.error(f"Cannot load image: {image_path}")
            sys.exit(1)
        frame_bgr = cv2.resize(frame_bgr, (FRAME_W, FRAME_H))
        logger.info(f"Input image: {image_path}")
    else:
        frame_bgr = _synthetic_frame()
        logger.info("Input image: synthetic (use --image for a real frame)")

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=_ensure_model("gesture_recognizer.task")),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
    )

    times_pre = []   # preprocessing: BGR->RGB + mp.Image creation
    times_inf = []   # gesture recognition only
    times_e2e = []   # end-to-end total

    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        # warm-up — first calls are slower due to JIT caching
        for _ in range(N_WARMUP):
            img_rgb  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            recognizer.recognize(mp_frame)

        logger.info(f"Running {N_RUNS} iterations...")

        for _ in range(N_RUNS):
            t0       = time.perf_counter()
            img_rgb  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
            t1       = time.perf_counter()
            recognizer.recognize(mp_frame)
            t2       = time.perf_counter()

            times_pre.append((t1 - t0) * 1000)
            times_inf.append((t2 - t1) * 1000)
            times_e2e.append((t2 - t0) * 1000)

    _print_stats(times_pre, times_inf, times_e2e)
    _save_plot(times_pre, times_inf, times_e2e)
    _save_report(times_pre, times_inf, times_e2e, image_path)


def _print_stats(
    times_pre: list[float],
    times_inf: list[float],
    times_e2e: list[float],
) -> None:
    rows = [
        ("Preprocessing", _stats(times_pre)),
        ("Recognition",   _stats(times_inf)),
        ("Total (E2E)",   _stats(times_e2e)),
    ]
    w = 68
    print()
    print("=" * w)
    print("  LATENCY BENCHMARK  [ms]")
    print("=" * w)
    print(f"  {'Stage':<20} {'Avg':>6}  {'Med':>6}  {'Std':>6}  {'Min':>6}  {'Max':>6}  {'P95':>6}")
    print("-" * w)
    for label, (avg, med, std, mn, mx, p95) in rows:
        print(f"  {label:<20} {avg:>6.2f}  {med:>6.2f}  {std:>6.2f}  {mn:>6.2f}  {mx:>6.2f}  {p95:>6.2f}")
    print("=" * w)
    print(f"\n  Estimated throughput: ~{1000 / _stats(times_e2e)[0]:.1f} fps\n")


def _save_plot(
    times_pre: list[float],
    times_inf: list[float],
    times_e2e: list[float],
) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    fig.suptitle(f"Processing time distribution (n={N_RUNS})", fontsize=12)

    for ax, data, label, color in zip(
        axes,
        [times_pre, times_inf, times_e2e],
        ["Preprocessing", "Recognition", "Total"],
        ["#5294e0", "#e05252", "#52c05a"],
    ):
        ax.hist(data, bins=20, color=color, edgecolor="white", alpha=0.85)
        avg = np.mean(data)
        ax.axvline(avg, color="black", linestyle="--", linewidth=1.5,
                   label=f"Avg {avg:.2f} ms")
        ax.set_title(label)
        ax.set_xlabel("Time [ms]")
        ax.set_ylabel("Sample count")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "benchmark_latency.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[OK] Plot saved:   {out}")


def _save_report(
    times_pre:  list[float],
    times_inf:  list[float],
    times_e2e:  list[float],
    image_path: str | None,
) -> None:
    rows = [
        ("Preprocessing", _stats(times_pre)),
        ("Recognition",   _stats(times_inf)),
        ("Total (E2E)",   _stats(times_e2e)),
    ]
    w   = 68
    out = OUTPUT_DIR / "benchmark_latency.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("LATENCY BENCHMARK\n")
        f.write("=" * w + "\n")
        f.write(f"Runs: {N_RUNS}  |  Warm-up: {N_WARMUP}\n")
        f.write(f"Image: {image_path or 'synthetic'}  |  Resolution: {FRAME_W}x{FRAME_H}\n")
        f.write("-" * w + "\n")
        f.write(f"  {'Stage':<20} {'Avg':>6}  {'Med':>6}  {'Std':>6}  {'Min':>6}  {'Max':>6}  {'P95':>6}\n")
        f.write("-" * w + "\n")
        for label, (avg, med, std, mn, mx, p95) in rows:
            f.write(f"  {label:<20} {avg:>6.2f}  {med:>6.2f}  {std:>6.2f}  {mn:>6.2f}  {mx:>6.2f}  {p95:>6.2f}\n")
        f.write("=" * w + "\n")
        f.write(f"Estimated throughput: ~{1000 / _stats(times_e2e)[0]:.1f} fps\n")
    print(f"[OK] Report saved: {out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", type=str, default=None,
                        help="Path to a gesture image (default: synthetic frame)")
    args = parser.parse_args()
    run(args.image)
