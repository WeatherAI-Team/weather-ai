# app/services/detection_event_save_service.py

from datetime import datetime
from app import db
from app.repositories.detection_repo import DetectionRepository
from app.repositories.detection_object_repo import DetectionObjectRepository
from app.repositories.weather_log_repo import WeatherLogRepository
from app.services.llm_event_payload_service import build_detection_event_payload


def _get_bbox_values(obj: dict):
    bbox = obj.get("bbox")

    if not bbox or len(bbox) < 4:
        return None, None, None, None

    x1, y1, x2, y2 = bbox

    return x1, y1, x2 - x1, y2 - y1


def _build_detection_object_payloads(event_id, yolo_result, image_url=None):
    payloads = []

    for obj in yolo_result.get("objects", []):
        bbox_x, bbox_y, bbox_width, bbox_height = _get_bbox_values(obj)

        payloads.append({
            "event_id": event_id,
            "vehicle_type": obj.get("label", "UNKNOWN"),
            "confidence": obj.get("confidence", 0),
            "bbox_x": bbox_x,
            "bbox_y": bbox_y,
            "bbox_width": bbox_width,
            "bbox_height": bbox_height,
            "frame_index": obj.get("frame_index"),
            "image_url": image_url,
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
    commit=True,
):
    detection_repo = DetectionRepository()
    detection_object_repo = DetectionObjectRepository()
    weather_log_repo = WeatherLogRepository()

    weather_log = weather_log_repo.create_weather_log({
        "cctv_source_id": cctv_source_id,
        "weather_type": weather_type or "UNKNOWN",
        "temperature": None,
        "precipitation": None,
        "snowfall": None,
        "visibility": None,
        "weather_risk_score": risk_result.get("risk_score", 0),
        "source": "KMA",
        "raw_data": {
            "alerts": weather_alerts,
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
    )

    event = detection_repo.create_detection_event(event_payload)

    object_payloads = _build_detection_object_payloads(
        event_id=event.id,
        yolo_result=yolo_result,
        image_url=image_url,
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