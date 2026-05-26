
import os
from dotenv import load_dotenv

load_dotenv()

YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "best.pt")
YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", "0.25"))

DANGEROUS_VEHICLE_LABELS = {
    "25t_truck",
    "cargo_truck",
    "Gas_Trcuk",
    "RMC",
}

_model = None


def _load_yolo_model():
    global _model

    if _model is not None:
        return _model

    try:
        from ultralytics import YOLO
        _model = YOLO(YOLO_MODEL_PATH)
        return _model

    except Exception as e:
        raise RuntimeError(f"YOLO 모델 로딩 실패: {e}") from e


def run_yolo_detection(image_path: str | None = None) -> dict:
    """
    2차 정밀 탐지 단계.
    YOLO로 위험 차량 여부를 정밀 탐지한다.
    """

    if not image_path or not os.path.exists(image_path):
        return {
            "stage": "yolo",
            "used": False,
            "dangerous_vehicle_detected": False,
            "objects": [],
            "dangerous_objects": [],
            "max_confidence": None,
            "reason": "분석할 이미지 경로가 없어 YOLO 탐지를 건너뜀",
        }

    model = _load_yolo_model()

    try:
        results = model(image_path, conf=YOLO_CONF_THRESHOLD, verbose=False)

        objects = []
        max_confidence = 0.0

        for result in results:
            names = result.names

            if result.boxes is None:
                continue

            for box in result.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = names.get(cls_id, str(cls_id))

                xyxy = box.xyxy[0].tolist()

                max_confidence = max(max_confidence, conf)

                objects.append({
                    "label": label,
                    "name": label,
                    "confidence": round(conf, 4),
                    "bbox": [round(v, 2) for v in xyxy],
                    "dangerous": label in DANGEROUS_VEHICLE_LABELS,
                })

        dangerous_objects = [
            obj for obj in objects
            if obj["dangerous"]
        ]

        return {
            "stage": "yolo",
            "used": True,
            "dangerous_vehicle_detected": len(dangerous_objects) > 0,
            "objects": objects,
            "dangerous_objects": dangerous_objects,
            "max_confidence": round(max_confidence, 4) if objects else None,
            "reason": "YOLO 정밀 탐지 완료",
        }

    except Exception as e:
        print(f"[YOLO] 정밀 탐지 실패: {e}")

        return {
            "stage": "yolo",
            "used": False,
            "dangerous_vehicle_detected": False,
            "objects": [],
            "max_confidence": None,
            "reason": f"YOLO 정밀 탐지 실패: {e}",
        }