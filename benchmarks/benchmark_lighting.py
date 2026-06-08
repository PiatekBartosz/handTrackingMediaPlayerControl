import sys
import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
from collections import defaultdict
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from helpers.mediapipe_recognizer import _ensure_model

logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level:<8} | {message}")

GESTURES         = ["Thumb_Up", "Thumb_Down", "Closed_Fist"]
BRIGHTNESS_STEPS = list(range(-100, 101, 25))  # beta from -100 to +100

DATASET_DIR = Path(__file__).resolve().parent / "dataset"
OUTPUT_DIR  = Path(__file__).resolve().parent / "results"


def _adjust_brightness(img: np.ndarray, beta: int) -> np.ndarray:
    return cv2.convertScaleAbs(img, alpha=1.0, beta=beta)


def run() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    if not DATASET_DIR.exists():
        logger.error(f"Dataset not found: {DATASET_DIR}")
        logger.info("Run first: uv run benchmarks/collect_dataset.py")
        sys.exit(1)

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(
            model_asset_path=_ensure_model("gesture_recognizer.task")),
        running_mode=mp.tasks.vision.RunningMode.IMAGE,
    )

    # results[gesture][beta] = list of confidence scores (0.0 on misclassification)
    results:  dict[str, dict[int, list[float]]] = {g: defaultdict(list) for g in GESTURES}
    accuracy: dict[str, dict[int, float]]       = {g: {} for g in GESTURES}

    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        for gesture in GESTURES:
            images = sorted((DATASET_DIR / gesture).glob("*.jpg"))
            if not images:
                logger.warning(f"No images for {gesture}, skipping")
                continue

            logger.info(f"Testing gesture: {gesture} ({len(images)} images)")

            for beta in BRIGHTNESS_STEPS:
                correct = 0
                for img_path in images:
                    img = cv2.imread(str(img_path))
                    if img is None:
                        continue

                    modified  = _adjust_brightness(img, beta)
                    img_rgb   = cv2.cvtColor(modified, cv2.COLOR_BGR2RGB)
                    mp_frame  = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                    res       = recognizer.recognize(mp_frame)

                    if res.gestures and res.gestures[0][0].category_name == gesture:
                        correct += 1
                        results[gesture][beta].append(res.gestures[0][0].score)
                    else:
                        results[gesture][beta].append(0.0)

                n   = len(images)
                acc = correct / n if n else 0.0
                accuracy[gesture][beta] = acc
                avg = np.mean(results[gesture][beta]) if results[gesture][beta] else 0.0
                logger.debug(f"beta={beta:+4d}  accuracy={acc*100:5.1f}%  avg_confidence={avg*100:5.1f}%")

    _save_plot(results, accuracy)
    _save_report(results, accuracy)


def _save_plot(
    results:  dict[str, dict[int, list[float]]],
    accuracy: dict[str, dict[int, float]],
) -> None:
    colors  = {"Thumb_Up": "#e05252", "Thumb_Down": "#5294e0", "Closed_Fist": "#52c05a"}
    markers = {"Thumb_Up": "o",       "Thumb_Down": "s",       "Closed_Fist": "^"}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle("Effect of image brightness on gesture classification", fontsize=13)

    for gesture in GESTURES:
        if not accuracy[gesture]:
            continue
        betas = sorted(accuracy[gesture])
        accs  = [accuracy[gesture][b] * 100 for b in betas]
        confs = [np.mean(results[gesture][b]) * 100 for b in betas]

        for ax, data in ((ax1, accs), (ax2, confs)):
            ax.plot(betas, data, marker=markers[gesture], color=colors[gesture],
                    label=gesture, linewidth=2, markersize=6)

    for ax, title, ylabel in [
        (ax1, "Classification accuracy",         "Accuracy [%]"),
        (ax2, "Average classification confidence", "Confidence [%]"),
    ]:
        ax.set_title(title)
        ax.set_xlabel("Brightness offset (beta)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(BRIGHTNESS_STEPS)
        ax.set_ylim(0, 105)
        ax.axvline(0, color="gray", linestyle="--", linewidth=1, alpha=0.6)
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = OUTPUT_DIR / "benchmark_lighting.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    logger.success(f"Plot saved: {out}")


def _save_report(
    results:  dict[str, dict[int, list[float]]],
    accuracy: dict[str, dict[int, float]],
) -> None:
    out = OUTPUT_DIR / "benchmark_lighting.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("LIGHTING BENCHMARK\n")
        f.write("=" * 60 + "\n")
        f.write(f"  {'Gesture':<15} {'Beta':>6}  {'Accuracy':>9}  {'Avg confidence':>14}\n")
        f.write("-" * 60 + "\n")
        for gesture in GESTURES:
            for beta in sorted(accuracy.get(gesture, {})):
                acc  = accuracy[gesture][beta] * 100
                conf = np.mean(results[gesture][beta]) * 100 if results[gesture][beta] else 0.0
                f.write(f"  {gesture:<15} {beta:>+6}  {acc:>8.1f}%  {conf:>13.1f}%\n")
        f.write("=" * 60 + "\n")
    logger.success(f"Report saved: {out}")


if __name__ == "__main__":
    run()
