import sys
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

GESTURES      = ["Thumb_Up", "Thumb_Down", "Closed_Fist"]
NO_DETECTION  = "No detection"

DATASET_DIR = Path(__file__).resolve().parent / "dataset"
OUTPUT_DIR  = Path(__file__).resolve().parent / "results"


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

    # extra column/row for frames where no gesture was detected
    all_labels = GESTURES + [NO_DETECTION]
    label_idx  = {lbl: i for i, lbl in enumerate(all_labels)}
    cm         = np.zeros((len(all_labels), len(all_labels)), dtype=int)
    total      = 0
    correct    = 0

    with mp.tasks.vision.GestureRecognizer.create_from_options(options) as recognizer:
        for true_gesture in GESTURES:
            images = sorted((DATASET_DIR / true_gesture).glob("*.jpg"))
            if not images:
                logger.warning(f"No images for {true_gesture}, skipping")
                continue

            logger.info(f"Classifying: {true_gesture} ({len(images)} images)...")

            for img_path in images:
                img = cv2.imread(str(img_path))
                if img is None:
                    continue

                img_rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                mp_frame = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
                res      = recognizer.recognize(mp_frame)

                # gestures outside the test set are treated as no detection
                predicted = res.gestures[0][0].category_name if res.gestures else NO_DETECTION
                if predicted not in label_idx:
                    predicted = NO_DETECTION

                cm[label_idx[true_gesture]][label_idx[predicted]] += 1
                total   += 1
                correct += predicted == true_gesture

            logger.success(f"Done: {true_gesture}")

    overall_acc = correct / total * 100 if total else 0.0
    logger.success(f"Overall accuracy: {correct}/{total}  ({overall_acc:.1f}%)")

    print(f"  {'Gesture':<15} {'Correct':>9}  {'Total':>7}  {'Accuracy':>9}")
    print("  " + "-" * 46)
    for gesture in GESTURES:
        i         = label_idx[gesture]
        n_total   = int(cm[i].sum())
        n_correct = int(cm[i][i])
        acc       = n_correct / n_total * 100 if n_total else 0.0
        print(f"  {gesture:<15} {n_correct:>9}  {n_total:>7}  {acc:>8.1f}%")

    _save_plot(cm, all_labels)
    _save_report(cm, all_labels, correct, total, overall_acc)


def _save_plot(cm: np.ndarray, labels: list[str]) -> None:
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)

    ax.set(
        xticks=np.arange(len(labels)),
        yticks=np.arange(len(labels)),
        xticklabels=labels,
        yticklabels=labels,
        title="Confusion matrix — gesture classification",
        ylabel="True gesture",
        xlabel="Predicted gesture",
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    thresh = cm.max() / 2.0
    for i in range(len(labels)):
        for j in range(len(labels)):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black", fontsize=12)

    plt.tight_layout()
    out = OUTPUT_DIR / "benchmark_confusion.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    logger.success(f"Confusion matrix saved: {out}")


def _save_report(
    cm:          np.ndarray,
    labels:      list[str],
    correct:     int,
    total:       int,
    overall_acc: float,
) -> None:
    n   = len(labels)
    col = 16
    out = OUTPUT_DIR / "benchmark_confusion.txt"
    with open(out, "w", encoding="utf-8") as f:
        f.write("CONFUSION MATRIX\n")
        f.write("=" * 60 + "\n")
        f.write(f"Overall accuracy: {correct}/{total} ({overall_acc:.1f}%)\n")
        f.write("-" * 60 + "\n")
        f.write(" " * col + "".join(f"{lbl[:col]:>{col}}" for lbl in labels) + "\n")
        f.write("-" * (col * (n + 1)) + "\n")
        for i, lbl in enumerate(labels):
            f.write(f"{lbl:<{col}}" + "".join(f"{cm[i,j]:>{col}}" for j in range(n)) + "\n")
        f.write("=" * 60 + "\n")
    logger.success(f"Report saved: {out}")


if __name__ == "__main__":
    run()
