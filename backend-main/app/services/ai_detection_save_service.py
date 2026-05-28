# app/services/ai_detection_save_service.py

from datetime import datetime

from app.services.detection_event_save_service import save_detection_event_result


DANGEROUS_VEHICLE_LABELS = {
    "25t_truck",
    "cargo_truck",
    "Gas_Trcuk",
    "RMC",
}


WEATHER_NAME_MAP = {
    "heavy_rain": "폭우",
    "rain": "비",
    "snow": "폭설",
    "fog": "안개",
    "clear": "맑음",
    "HEAVY_RAIN": "폭우",
    "RAIN": "비",
    "SNOW": "폭설",
    "FOG": "안개",
    "CLEAR": "맑음",
}

def _normalize_weather_type(weather: str | None) -> str:
    if not weather:
        return "UNKNOWN"

    value = str(weather).upper()

    if value == "HEAVY_RAIN":
        return "HEAVY_RAIN"

    if value == "RAIN":
        return "RAIN"

    if value == "SNOW":
        return "SNOW"

    if value == "FOG":
        return "FOG"

    if value == "CLEAR":
        return "CLEAR"

    return value

def _to_ratio(value):
    if value is None:
        return 0

    try:
        value = float(value)
    except Exception:
        return 0

    if value > 1:
        return round(value / 100, 4)

    return round(value, 4)


def _normalize_yolo_result(ai_result: dict) -> dict:
    yolo_boxes = ai_result.get("yolo_boxes") or []

    objects = []

    for box in yolo_boxes:
        label = (
            box.get("class_name")
            or box.get("label")
            or box.get("name")
            or "UNKNOWN"
        )

        confidence = _to_ratio(box.get("confidence"))

        obj = {
            "label": label,
            "name": label,
            "confidence": confidence,
            "bbox": box.get("box_coords") or box.get("bbox"),
            "dangerous": label in DANGEROUS_VEHICLE_LABELS,
        }

        objects.append(obj)

    dangerous_objects = [
        obj for obj in objects
        if obj["dangerous"]
    ]

    max_confidence = max(
        [obj["confidence"] for obj in objects],
        default=None,
    )

    return {
        "stage": "yolo",
        "used": True,
        "dangerous_vehicle_detected": len(dangerous_objects) > 0,
        "objects": objects,
        "dangerous_objects": dangerous_objects,
        "max_confidence": max_confidence,
        "raw_result": ai_result,
        "reason": "프론트 AI 탐지 결과 기반 저장",
    }


def _build_weather_alerts(ai_result: dict, cctv_source_id=None) -> list[dict]:
    weather = ai_result.get("weather") or "UNKNOWN"
    weather_type = _normalize_weather_type(weather)
    weather_name = WEATHER_NAME_MAP.get(weather, WEATHER_NAME_MAP.get(weather_type, weather_type))

    is_danger = bool(ai_result.get("is_danger"))

    return [
        {
            "wrn_code": weather_type,
            "wrn_name": weather_name,
            "level": "경보" if is_danger else "관심",
            "reg_id": str(cctv_source_id) if cctv_source_id else "UNKNOWN",
            "tm_fc": datetime.utcnow().isoformat(),
        }
    ]

def _build_risk_result(ai_result: dict, yolo_result: dict) -> dict:
    score = 0
    reasons = []

    if ai_result.get("is_danger"):
        score += 30
        reasons.append("AI 날씨 탐지에서 위험 기상 감지")

    if yolo_result.get("dangerous_vehicle_detected"):
        score += 40
        reasons.append("AI 차량 탐지에서 위험 차량 감지")

    max_confidence = yolo_result.get("max_confidence")

    if max_confidence is not None:
        if max_confidence >= 0.85:
            score += 10
            reasons.append("위험 차량 탐지 신뢰도 높음")
        elif max_confidence >= 0.65:
            score += 5
            reasons.append("위험 차량 탐지 신뢰도 보통 이상")

    score = min(score, 100)

    if score >= 80:
        risk_level = "DANGER"
    elif score >= 60:
        risk_level = "CAUTION"
    elif score >= 30:
        risk_level = "NORMAL"
    else:
        risk_level = "LOW"

    alert_required = score >= 60

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "alert_required": alert_required,
        "score_filter_passed": score >= 60,
        "false_positive_possible": False,
        "reasons": reasons,
    }


def _build_final_alert(ai_result: dict, risk_result: dict, yolo_result: dict) -> dict:
    weather = ai_result.get("weather") or "UNKNOWN"
    weather_name = WEATHER_NAME_MAP.get(weather, weather)

    dangerous_objects = yolo_result.get("dangerous_objects") or []
    vehicle_type = (
        dangerous_objects[0].get("label")
        if dangerous_objects
        else "위험 차량"
    )

    return {
        "risk_level": risk_result.get("risk_level", "CAUTION"),
        "title": f"{weather_name} 상황 위험 차량 감지",
        "admin_message": (
            f"{weather_name} 상황에서 {vehicle_type} 차량이 감지되었습니다. "
            "관제센터 모니터링이 필요합니다."
        ),
        "driver_message": "위험 기상 및 위험 차량 감지. 감속하고 안전거리를 확보하세요.",
        "reason": ", ".join(risk_result.get("reasons", [])) or "AI 탐지 결과 기반 저장",
        "alert_required": risk_result.get("alert_required", False),
        "false_positive_suspected": risk_result.get("false_positive_possible", False),
    }


def save_ai_detection_result(data: dict) -> dict:
    ai_result = data.get("ai_result") or {}

    # 중요:
    # cctv_source_id는 실제 cctv_sources.id일 때만 넣어야 한다.
    # 프론트의 selectedCctv + 1은 DB FK와 맞지 않을 수 있으므로 기본은 None 권장.
    cctv_source_id = data.get("cctv_source_id")
    weather_log_id = data.get("weather_log_id")
    image_url = data.get("image_url")

    weather = ai_result.get("weather") or "UNKNOWN"
    weather_type = _normalize_weather_type(weather)
    weather_name = WEATHER_NAME_MAP.get(weather, WEATHER_NAME_MAP.get(weather_type, weather_type))

    yolo_result = _normalize_yolo_result(ai_result)
    weather_alerts = _build_weather_alerts(ai_result, cctv_source_id)
    risk_result = _build_risk_result(ai_result, yolo_result)
    final_alert = _build_final_alert(ai_result, risk_result, yolo_result)

    return save_detection_event_result(
        cctv_source_id=cctv_source_id,
        weather_type=weather_type,
        weather_alerts=weather_alerts,
        yolo_result=yolo_result,
        risk_result=risk_result,
        final_alert=final_alert,
        image_url=image_url,
        weather_log_id=weather_log_id,
    )