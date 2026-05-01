from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    try:
        import torch
        from roboflow import Roboflow
        from ultralytics import YOLO
    except ImportError as exc:
        raise SystemExit("Install ML dependencies first: pip install -r requirements-ml.txt") from exc

    api_key = os.getenv("ROBOFLOW_API_KEY")
    if not api_key:
        raise SystemExit("Set ROBOFLOW_API_KEY before running this script.")

    os.makedirs("data/weapon", exist_ok=True)
    os.makedirs("codex", exist_ok=True)

    rf = Roboflow(api_key=api_key)
    project = rf.workspace("weopon-detection").project("weapon-detection-using-yolov8")
    dataset = project.version(1).download("yolov8", location="data/weapon")

    model = YOLO("yolov8n.pt")
    results = model.train(
        data=f"{dataset.location}/data.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        lr0=0.001,
        lrf=0.1,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        augment=True,
        mosaic=1.0,
        flipud=0.3,
        fliplr=0.5,
        degrees=10,
        patience=15,
        save=True,
        project="runs/weapon",
        name="train",
        device="0" if torch.cuda.is_available() else "cpu",
    )

    best_pt = "runs/weapon/train/weights/best.pt"
    shutil.copy(best_pt, "codex/weapon_best.pt")
    print(f"mAP50: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print("Saved codex/weapon_best.pt")

    val_model = YOLO("codex/weapon_best.pt")
    val_results = val_model.val(data=f"{dataset.location}/data.yaml")
    print(f"Validation mAP50: {val_results.box.map50:.3f}")
    print(f"Precision: {val_results.box.mp:.3f}")
    print(f"Recall: {val_results.box.mr:.3f}")


if __name__ == "__main__":
    main()
