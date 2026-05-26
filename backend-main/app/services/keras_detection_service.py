# app/services/keras_detection_service.py

import os
from dotenv import load_dotenv

load_dotenv()

KERAS_MODEL_PATH = os.getenv("KERAS_MODEL_PATH")
KERAS_RISK_THRESHOLD = float(os.getenv("KERAS_RISK_THRESHOLD", "0.6"))
KERAS_INPUT_SIZE = tuple(
    map(int, os.getenv("KERAS_INPUT_SIZE", "224,224").split(","))
)

_model = None


def _load_keras_model():
    """
    Keras 모델 지연 로딩.
    모델 파일이 없거나 tensorflow가 없으면 예외 대신 None 처리.
    """
    global _model

    if _model is not None:
        return _model

    if not KERAS_MODEL_PATH:
        return None

    if not os.path.exists(KERAS_MODEL_PATH):
        return None

    try:
        from tensorflow.keras.models import load_model
        _model = load_model(KERAS_MODEL_PATH)
        return _model

    except Exception as e:
        print(f"[Keras] 모델 로딩 실패: {e}")
        return None


def run_keras_first_detection(image_path: str | None = None) -> dict:
    """
    1차 경량 탐지 단계.
    실제 Keras 모델이 없으면 skipped로 반환해서 전체 흐름이 죽지 않게 한다.
    """

    model = _load_keras_model()

    if model is None:
        return {
            "stage": "keras",
            "used": False,
            "possible_risk": True,
            "confidence": None,
            "label": "skipped",
            "reason": "Keras 모델이 없어 1차 탐지를 건너뜀",
        }

    if not image_path or not os.path.exists(image_path):
        return {
            "stage": "keras",
            "used": False,
            "possible_risk": True,
            "confidence": None,
            "label": "no_image",
            "reason": "분석할 이미지 경로가 없어 1차 탐지를 건너뜀",
        }

    try:
        import numpy as np
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        image = image.resize(KERAS_INPUT_SIZE)

        arr = np.array(image) / 255.0
        arr = np.expand_dims(arr, axis=0)

        pred = model.predict(arr, verbose=0)

        # 이진 분류 sigmoid 기준
        if pred.shape[-1] == 1:
            confidence = float(pred[0][0])
            possible_risk = confidence >= KERAS_RISK_THRESHOLD
            label = "risk" if possible_risk else "normal"

        # 다중 분류 softmax 기준
        else:
            idx = int(np.argmax(pred[0]))
            confidence = float(pred[0][idx])

            class_names = os.getenv(
                "KERAS_CLASS_NAMES",
                "normal,risk"
            ).split(",")

            label = class_names[idx] if idx < len(class_names) else str(idx)
            possible_risk = label.lower() != "normal" and confidence >= KERAS_RISK_THRESHOLD

        return {
            "stage": "keras",
            "used": True,
            "possible_risk": possible_risk,
            "confidence": confidence,
            "label": label,
            "reason": "Keras 1차 탐지 완료",
        }

    except Exception as e:
        print(f"[Keras] 1차 탐지 실패: {e}")

        return {
            "stage": "keras",
            "used": False,
            "possible_risk": True,
            "confidence": None,
            "label": "error",
            "reason": f"Keras 1차 탐지 실패: {e}",
        }