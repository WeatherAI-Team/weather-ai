# app/services/keras_detection_service.py

import os
import requests
from dotenv import load_dotenv


load_dotenv()

# backend-ai FastAPI 서버 주소.
# 같은 서버에서 실행 중이면 127.0.0.1:8000 사용 가능.
# backend-ai가 별도 VM에 있으면 VM IP로 변경해야 한다.
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8000")

# backend-ai 서버 응답 대기 시간.
# AI 추론은 시간이 걸릴 수 있으므로 일반 API보다 길게 잡는다.
AI_SERVER_TIMEOUT = int(os.getenv("AI_SERVER_TIMEOUT", "120"))


def _to_ratio(value):
    """
    AI 서버에서 받은 confidence 값을 0~1 범위 비율로 변환한다.

    backend-ai 응답이 91.0처럼 퍼센트 값으로 올 수도 있고,
    0.91처럼 이미 비율 값으로 올 수도 있기 때문에
    Flask 쪽에서 통일된 형태로 맞춘다.
    """

    # 값이 없으면 그대로 None 반환
    if value is None:
        return None

    try:
        # 문자열/정수/실수 형태를 모두 float으로 변환 시도
        value = float(value)
    except Exception:
        # 숫자로 바꿀 수 없는 값이면 None 처리
        return None

    # 1보다 크면 91.0 같은 퍼센트 값으로 보고 100으로 나눔
    if value > 1:
        return round(value / 100, 4)

    # 이미 0~1 사이 값이면 그대로 사용
    return round(value, 4)


def run_keras_first_detection(image_path: str | None = None) -> dict:
    """
    Keras 1차 탐지 요청 함수.

    주의:
    Flask backend-main에서는 Keras 모델을 직접 로딩하거나 추론하지 않는다.
    실제 Keras 추론은 backend-ai FastAPI 서버가 담당한다.

    이 함수의 역할:
    1. backend-main에서 image_path를 받는다.
    2. backend-ai의 /detect/keras 엔드포인트로 HTTP 요청을 보낸다.
    3. backend-ai 응답을 hybrid_alert_service가 쓰기 쉬운 dict 형태로 정규화한다.
    """

    # 이미지 경로가 없으면 AI 서버에 요청하지 않고 skipped 형태로 반환한다.
    # possible_risk=True로 두는 이유:
    # Keras가 실행되지 않았다고 해서 전체 탐지 흐름을 중단하지 않고,
    # 필요하면 YOLO 단계로 넘어갈 수 있게 하기 위해서다.
    if not image_path:
        return {
            "stage": "keras",
            "used": False,
            "possible_risk": True,
            "confidence": None,
            "label": "no_image",
            "reason": "분석할 이미지 경로가 없어 Keras 1차 탐지를 건너뜀",
        }

    try:
        # backend-ai FastAPI 서버에 Keras 1차 탐지 요청.
        # 실제 모델 추론은 backend-ai에서 수행된다.
        response = requests.post(
        f"{AI_SERVER_URL}/api/ai/detect/keras",
        json={"image_path": image_path},
        timeout=AI_SERVER_TIMEOUT,
    )

        # 4xx/5xx 응답이면 예외 발생.
        # 예: AI 서버 다운, endpoint 없음, 이미지 읽기 실패 등
        response.raise_for_status()

        # backend-ai에서 받은 JSON 응답
        data = response.json()

        # backend-ai 응답 형식이 조금 달라도 대응하기 위해 여러 키를 확인한다.
        # possible_risk: 직접 위험 가능성 여부
        # is_danger: 악천후 여부
        # has_danger_car: 위험 차량 가능성 여부
        possible_risk = bool(
            data.get("possible_risk")
            or data.get("is_danger")
            or data.get("has_danger_car")
        )

        # hybrid_alert_service.py에서 사용할 표준 형태로 반환한다.
        return {
            # 현재 단계 이름
            "stage": "keras",

            # backend-ai Keras 요청이 실제로 수행되었는지 여부
            "used": True,

            # Keras 1차 판단 기준 위험 가능성
            "possible_risk": possible_risk,

            # 기상 분류 confidence를 0~1 비율로 정규화
            "confidence": _to_ratio(data.get("confidence")),

            # 대표 라벨.
            # backend-ai가 label을 주면 label 사용,
            # 없으면 weather 값을 사용,
            # 둘 다 없으면 unknown 처리
            "label": data.get("label") or data.get("weather") or "unknown",

            # backend-ai가 반환한 날씨 분류 결과
            "weather": data.get("weather"),

            # 악천후 여부
            "is_danger": data.get("is_danger"),

            # 위험 차량 가능성 여부
            "has_danger_car": data.get("has_danger_car"),

            # 위험 차량 confidence를 0~1 비율로 정규화
            "danger_confidence": _to_ratio(data.get("danger_confidence")),

            # 원본 응답 보존.
            # 디버깅이나 추후 필드 추가 시 유용하다.
            "raw_result": data,

            # 처리 결과 설명
            "reason": "backend-ai Keras 1차 탐지 완료",
        }

    except requests.RequestException as e:
        # AI 서버 요청 실패 시 전체 서비스가 죽지 않도록 fallback 반환.
        # possible_risk=True로 두어 YOLO/후속 단계가 필요 시 계속 진행될 수 있게 한다.
        return {
            "stage": "keras",
            "used": False,
            "possible_risk": True,
            "confidence": None,
            "label": "ai_server_error",
            "reason": f"backend-ai Keras 요청 실패: {e}",
        }