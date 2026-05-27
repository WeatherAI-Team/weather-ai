import os
import requests
from dotenv import load_dotenv


load_dotenv()


AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8000")

AI_SERVER_TIMEOUT = int(os.getenv("AI_SERVER_TIMEOUT", "120"))


# YOLO 모델이 탐지하는 차량 클래스 중
# 시스템에서 위험 차량으로 판단할 클래스 목록.
#

DANGEROUS_VEHICLE_LABELS = {
    "25t_truck",
    "cargo_truck",
    "Gas_Trcuk",
    "RMC",
}


def _to_ratio(value):
    """
    AI 서버에서 받은 confidence 값을 0~1 범위 비율로 변환한다.

    backend-ai 응답이 91.0처럼 퍼센트 값으로 올 수도 있고,
    0.91처럼 이미 비율 값으로 올 수도 있기 때문에
    backend-main에서 통일된 형태로 맞춘다.
    """

    # 값이 없으면 None 반환
    if value is None:
        return None

    try:
        # 문자열/정수/실수 형태를 모두 float으로 변환 시도
        value = float(value)
    except Exception:
        # 숫자로 변환할 수 없는 값이면 None 처리
        return None

    # 1보다 크면 91.0 같은 퍼센트 값으로 보고 100으로 나눔
    if value > 1:
        return round(value / 100, 4)

    # 이미 0~1 사이 값이면 그대로 사용
    return round(value, 4)


def _normalize_yolo_objects(data: dict) -> list[dict]:
    """
    backend-ai 응답을 backend-main에서 사용하는 표준 objects 형식으로 변환한다.

    backend-ai 응답은 상황에 따라 아래처럼 올 수 있다.

    1. objects:
       [
         {"label": "Gas_Truck", "confidence": 0.91, "bbox": [...]}
       ]

    2. yolo_boxes:
       [
         {"class_name": "Gas_Trcuk", "confidence": 91.0, "box_coords": [...]}
       ]

    이 함수는 두 형식을 모두 받아서 아래 형식으로 통일한다.

    {
        "label": 차량 클래스명,
        "name": 차량 클래스명,
        "confidence": 0~1 범위 신뢰도,
        "bbox": 바운딩박스 좌표,
        "dangerous": 위험 차량 여부
    }
    """

    # 먼저 backend-ai가 objects라는 이름으로 객체 목록을 주는지 확인
    raw_objects = data.get("objects")

    # objects가 없으면 기존 AI 서버 응답 형식인 yolo_boxes를 사용
    if raw_objects is None:
        raw_objects = data.get("yolo_boxes", [])

    objects = []

    for obj in raw_objects:
        # backend-ai 응답에서 클래스명을 가져온다.
        # 응답 형식이 label, name, class_name 중 무엇이든 대응할 수 있게 한다.
        label = (
            obj.get("label")
            or obj.get("name")
            or obj.get("class_name")
            or "UNKNOWN"
        )

        # backend-ai 응답에서 바운딩박스 좌표를 가져온다.
        # bbox, box_coords, box 중 어떤 키로 와도 처리한다.
        bbox = (
            obj.get("bbox")
            or obj.get("box_coords")
            or obj.get("box")
        )

        # confidence를 0~1 비율로 정규화한다.
        confidence = _to_ratio(obj.get("confidence"))

        # backend-main의 risk_score_service, payload_service에서 쓰기 쉬운 형식으로 변환
        objects.append({
            "label": label,
            "name": label,
            "confidence": confidence if confidence is not None else 0,
            "bbox": bbox,
            "dangerous": label in DANGEROUS_VEHICLE_LABELS,
        })

    return objects


def run_yolo_detection(image_path: str | None = None) -> dict:
    """
    YOLO 2차 정밀 탐지 요청 함수.

    주의:
    Flask backend-main에서는 YOLO 모델을 직접 로딩하거나 추론하지 않는다.
    실제 YOLO 추론은 backend-ai FastAPI 서버가 담당한다.

    이 함수의 역할:
    1. backend-main에서 image_path를 받는다.
    2. backend-ai의 /detect/yolo 엔드포인트로 HTTP 요청을 보낸다.
    3. backend-ai 응답을 hybrid_alert_service가 쓰기 쉬운 dict 형태로 정규화한다.
    """

    # 이미지 경로가 없으면 AI 서버에 요청하지 않고 skipped 형태로 반환한다.
    if not image_path:
        return {
            "stage": "yolo",
            "used": False,
            "dangerous_vehicle_detected": False,
            "objects": [],
            "dangerous_objects": [],
            "max_confidence": None,
            "reason": "분석할 이미지 경로가 없어 YOLO 탐지를 건너뜀",
        }

    try:
        # backend-ai FastAPI 서버에 YOLO 정밀 탐지 요청.
        # 실제 YOLO 모델 추론은 backend-ai에서 수행된다.
        response = requests.post(
            f"{AI_SERVER_URL}/detect/yolo",
            json={
                "image_path": image_path,
            },
            timeout=AI_SERVER_TIMEOUT,
        )

        # 4xx/5xx 응답이면 예외 발생.
        # 예: AI 서버 다운, endpoint 없음, 이미지 경로 문제 등
        response.raise_for_status()

        # backend-ai에서 받은 JSON 응답
        data = response.json()

        # backend-ai 응답을 backend-main 표준 objects 형식으로 변환
        objects = _normalize_yolo_objects(data)

        # 위험 차량으로 분류된 객체만 따로 추출
        dangerous_objects = [
            obj for obj in objects
            if obj["dangerous"]
        ]

        # 전체 객체 confidence 중 가장 높은 값 계산
        confidence_values = [
            obj["confidence"]
            for obj in objects
            if obj.get("confidence") is not None
        ]

        max_confidence = max(confidence_values) if confidence_values else None

        # hybrid_alert_service.py에서 사용할 표준 형태로 반환
        return {
            # 현재 단계 이름
            "stage": "yolo",

            # backend-ai YOLO 요청이 실제로 수행되었는지 여부
            "used": True,

            # 위험 차량이 하나 이상 감지되었는지 여부
            "dangerous_vehicle_detected": len(dangerous_objects) > 0,

            # 전체 탐지 객체 목록
            "objects": objects,

            # 위험 차량 객체 목록
            "dangerous_objects": dangerous_objects,

            # 탐지 객체 중 최대 confidence
            "max_confidence": max_confidence,

            # 원본 응답 보존.
            # 디버깅이나 backend-ai 응답 형식 변경 대응에 유용하다.
            "raw_result": data,

            # 처리 결과 설명
            "reason": "backend-ai YOLO 정밀 탐지 완료",
        }

    except requests.RequestException as e:
        # AI 서버 요청 실패 시 전체 Flask 서비스가 죽지 않도록 fallback 반환.
        return {
            "stage": "yolo",
            "used": False,
            "dangerous_vehicle_detected": False,
            "objects": [],
            "dangerous_objects": [],
            "max_confidence": None,
            "reason": f"backend-ai YOLO 요청 실패: {e}",
        }