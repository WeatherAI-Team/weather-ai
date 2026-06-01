# app/services/detection_event_save_service.py

from datetime import datetime
from app import db
from app.repositories.detection_repo import DetectionRepository
from app.repositories.detection_object_repo import DetectionObjectRepository
from app.repositories.weather_log_repo import WeatherLogRepository
from app.services.llm_event_payload_service import build_detection_event_payload
from app.repositories.event_status_log_repo import EventStatusLogRepository
from app.services.kma_observation_service import get_latest_asos_observation

def _get_bbox_values(obj: dict):
    bbox = obj.get("bbox")

    if not bbox or len(bbox) < 4:
        return None, None, None, None

    x1, y1, x2, y2 = bbox

    return x1, y1, x2 - x1, y2 - y1


def _build_detection_object_payloads(event_id, yolo_result):
    payloads = []

    for obj in yolo_result.get("objects", []):

        payloads.append({
            "event_id": event_id,
            "vehicle_type": obj.get("label", "UNKNOWN"),
            "confidence": obj.get("confidence", 0),
            "created_at": datetime.utcnow(),
            "model_name": "YOLO",
            "is_risk_vehicle": obj.get("dangerous", False),
        })

    return payloads


def save_detection_event_result(
    cctv_source_id,
    weather_type,
    weather_alerts,
    yolo_result,
    risk_result,
    final_alert,
    image_url=None,
    weather_log_id=None,
    location_name=None,
    latitude=None,
    longitude=None,
    commit=True,
):
    detection_repo = DetectionRepository()
    detection_object_repo = DetectionObjectRepository()
    weather_log_repo = WeatherLogRepository()
    event_status_log_repo = EventStatusLogRepository()
    
    if weather_log_id:
        weather_log = weather_log_repo.find_by_id(weather_log_id)

        if weather_log is None:
            raise ValueError(f"weather_log_id={weather_log_id} 데이터가 없습니다.")

        if cctv_source_id is None:
            cctv_source_id = weather_log.cctv_source_id

        if not weather_type:
            weather_type = weather_log.weather_type

    else:
        observation = get_latest_asos_observation(
            latitude=latitude,
            longitude=longitude,
        )

        weather_log = weather_log_repo.create_weather_log({
            "cctv_source_id": cctv_source_id,
            "weather_type": weather_type or "UNKNOWN",
            "temperature": observation.get("temperature"),
            "precipitation": observation.get("precipitation"),
            "snowfall": observation.get("snowfall"),
            "visibility": observation.get("visibility"),
            "weather_risk_score": risk_result.get("risk_score", 0),
            "source": "KMA",
            "raw_data": {
                "alerts": weather_alerts,
                "observation": observation,
            },
            "created_at": datetime.utcnow(),
        })
    
    event_payload = build_detection_event_payload(
        weather_log_id=weather_log.id,
        cctv_source_id=cctv_source_id,
        weather_type=weather_type,
        yolo_result=yolo_result,
        risk_result=risk_result,
        final_alert=final_alert,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
    )

    event = detection_repo.create_detection_event(event_payload)

    db.session.flush()

    event_status_log_repo.create_initial_status_log(
        event_id=event.id,
        new_status=event_payload.get("event_status", "DETECTED"),
        memo="AI 탐지 이벤트 자동 생성",
    )
    
    object_payloads = _build_detection_object_payloads(
        event_id=event.id,
        yolo_result=yolo_result,
    )

    detection_object_repo.create_detection_objects(object_payloads)

    db.session.flush()

    result = {
        "saved": True,
        "event_id": event.id,
        "weather_log_id": weather_log.id,
        "object_count": len(object_payloads),
    }

    if commit:
        db.session.commit()
    else:
        db.session.rollback()

    return result