# app/services/ai_detection_save_service.py

from datetime import datetime, timezone, timedelta 
import os
import subprocess
from app.services.detection_event_save_service import save_detection_event_result
from app.services.gemma_service import generate_final_alert
from app.services.alert_save_service import save_alert_to_db

YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", "0.65"))

ALLOWED_WEATHER_TYPES = {
    "HEAVY_RAIN",
    "HEAVY_SNOW",
    "RAIN",
    "SNOW",
    "FOG",
    "CLEAR",
    "UNKNOWN",
}

def _to_int_or_none(value, field_name: str):
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} 값이 올바르지 않습니다.")


def _to_float_or_none(value, field_name: str):
    if value is None or value == "":
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} 값이 올바르지 않습니다.")


def _validate_ai_result(ai_result):
    if not isinstance(ai_result, dict):
        raise ValueError("ai_result 형식이 올바르지 않습니다.")

    yolo_boxes = ai_result.get("yolo_boxes", [])

    if yolo_boxes is None:
        yolo_boxes = []

    if not isinstance(yolo_boxes, list):
        raise ValueError("yolo_boxes 형식이 올바르지 않습니다.")

    weather_type = _normalize_weather_type(ai_result.get("weather"))

    if weather_type not in ALLOWED_WEATHER_TYPES:
        raise ValueError("weather 값이 올바르지 않습니다.")

    return yolo_boxes

# 한국 시간은 UTC보다 9시간 빨라.
KST = timezone(timedelta(hours=9))


def kst_now():
    # 현재 한국 시간을 가져와.
    # DB 컬럼이 timezone 없는 DateTime이라서 timezone 정보는 제거해.
    return datetime.now(KST).replace(tzinfo=None)

DANGEROUS_VEHICLE_LABELS = {
    "25t_truck",
    "cargo_truck",
    "Gas_Truck",
    "gas_truck",
    "RMC",
    "rmc",
}

VEHICLE_NAME_MAP = {
    "RMC": "레미콘",    
    "rmc": "레미콘",
    "gas_truck": "탱크로리",
    "Gas_Truck":  "탱크로리",
    "cargo_truck": "카고트럭",
    "25t_truck":  "카고트럭",
}

WEATHER_NAME_MAP = {
    "heavy_rain": "폭우",
    "heavy_snow": "폭설",
    "rain": "비",
    "snow": "폭설",
    "fog": "안개",
    "clear": "맑음",
    "HEAVY_RAIN": "폭우",
    "HEAVY_SNOW": "폭설",
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
        if not isinstance(box, dict):
            continue

        label = (
            box.get("class_name")
            or box.get("label")
            or box.get("name")
            or "UNKNOWN"
        )

        confidence = _to_ratio(box.get("confidence"))
        vehicle_name = VEHICLE_NAME_MAP.get(label, label)

        is_dangerous = (
            label in DANGEROUS_VEHICLE_LABELS
            and confidence >= YOLO_CONF_THRESHOLD
        )

        obj = {
            "label": label,
            "name": vehicle_name,
            "vehicle_name": vehicle_name,
            "confidence": confidence,
            "bbox": box.get("box_coords") or box.get("bbox"),
            "dangerous": is_dangerous,
        }

        objects.append(obj)

    dangerous_objects = [
        obj for obj in objects
        if obj["dangerous"]
    ]

    representative_vehicle = _pick_representative_vehicle(ai_result)
    representative_vehicle_name = VEHICLE_NAME_MAP.get(
        representative_vehicle,
        representative_vehicle,
    )

    objects.sort(
        key=lambda obj: 0 if obj.get("label") == representative_vehicle else 1
    )

    dangerous_objects.sort(
        key=lambda obj: 0 if obj.get("label") == representative_vehicle else 1
    )

    max_confidence = max(
        [obj["confidence"] for obj in objects],
        default=None,
    )

    return {
        "stage": "yolo",
        "used": True,
        "dangerous_vehicle_detected": len(dangerous_objects) > 0,
        "representative_vehicle": representative_vehicle,
        "representative_vehicle_name": representative_vehicle_name,
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
            "tm_fc": kst_now().isoformat(),
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
        if max_confidence >= 0.80:
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
    if dangerous_objects:
        first_object = dangerous_objects[0]
        vehicle_type = (
            first_object.get("vehicle_name")
            or first_object.get("name")
            or first_object.get("label")
            or "위험 차량"
        )
    else:
        vehicle_type = "위험 차량"

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

def _build_gemma_weather_data(
    ai_result: dict,
    weather_type: str,
    weather_name: str,
    weather_alerts: list[dict],
) -> dict:
    return {
        "weather_type": weather_type,
        "weather_name": weather_name,
        "weather_alerts": weather_alerts,
        "ai_weather_result": {
            "weather": ai_result.get("weather"),
            "confidence": ai_result.get("confidence"),
            "is_danger": ai_result.get("is_danger"),
        },
    }


def _build_gemma_detection_result(
    yolo_result: dict,
    risk_result: dict,
) -> dict:
    dangerous_objects = []

    for obj in yolo_result.get("dangerous_objects", []):
        dangerous_objects.append({
            "label": obj.get("label"),
            "vehicle_name": obj.get("vehicle_name") or obj.get("name"),
            "confidence": obj.get("confidence"),
        })

    return {
        "yolo_result": {
            "dangerous_vehicle_detected": yolo_result.get("dangerous_vehicle_detected"),
            "representative_vehicle": yolo_result.get("representative_vehicle"),
            "representative_vehicle_name": yolo_result.get("representative_vehicle_name"),
            "dangerous_objects": dangerous_objects,
            "max_confidence": yolo_result.get("max_confidence"),
        },
        "risk_result": risk_result,
        "instruction": (
            "representative_vehicle_name 값을 최종 차량 종류로 사용하세요. "
            "vehicle_name 값을 그대로 사용하세요. "
            "RMC는 레미콘이며 탱크로리가 아닙니다. "
            "차량 종류를 추측하거나 바꾸지 마세요."
        ),
    }

def _generate_final_alert_with_gemma_or_fallback(
    ai_result: dict,
    weather_type: str,
    weather_name: str,
    weather_alerts: list[dict],
    risk_result: dict,
    yolo_result: dict,
) -> dict:
    if not risk_result.get("alert_required"):
        return _build_final_alert(ai_result, risk_result, yolo_result)

    try:
        weather_data = _build_gemma_weather_data(
            ai_result=ai_result,
            weather_type=weather_type,
            weather_name=weather_name,
            weather_alerts=weather_alerts,
        )

        detection_result = _build_gemma_detection_result(
            yolo_result=yolo_result,
            risk_result=risk_result,
        )

        final_alert = generate_final_alert(
            weather_data=weather_data,
            detection_result=detection_result,
        )
        vehicle_name = yolo_result.get("representative_vehicle_name") or "위험 차량"
        risk_level = risk_result.get("risk_level") or final_alert.get("risk_level", "CAUTION")
        final_alert["risk_level"] = risk_level

        prefix = "긴급" if risk_level == "DANGER" else "주의"

        # ✅ Gemma가 차량명을 잘못 추측해도 최종 저장/팝업 제목은 대표 차량 기준으로 고정
        final_alert["title"] = f"[{prefix}] {weather_name} {vehicle_name} 위험 탐지"

        # ✅ 메시지에도 대표 차량명 강제 반영
        if "admin_message" not in final_alert or "탱크로리" in final_alert.get("admin_message", "") or "LPG" in final_alert.get("admin_message", ""):
            final_alert["admin_message"] = (
                f"{weather_name} 상황에서 {vehicle_name} 차량이 감지되었습니다. "
                "관제센터 모니터링이 필요합니다."
            )

        if "driver_message" not in final_alert:
            final_alert["driver_message"] = (
                f"{weather_name} 상황입니다. 감속 운행하고 안전거리를 확보하십시오."
            )

        if "reason" not in final_alert or "탱크로리" in final_alert.get("reason", "") or "LPG" in final_alert.get("reason", ""):
            final_alert["reason"] = (
                f"AI 날씨 탐지에서 {weather_name}가 감지되었고, "
                f"AI 차량 탐지에서 {vehicle_name} 차량이 대표 위험 차량으로 감지되었습니다."
            )

        final_alert["alert_required"] = risk_result.get("alert_required", False)
        final_alert["false_positive_suspected"] = risk_result.get("false_positive_possible", False)

        return final_alert

    except Exception as e:
        print(f"[Gemma 오류] 기본 알림 문구 사용: {e}")
        return _build_final_alert(ai_result, risk_result, yolo_result)

def save_ai_detection_result(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError("요청 데이터 형식이 올바르지 않습니다.")

    ai_result = data.get("ai_result")

    _validate_ai_result(ai_result)

    # 중요:
    # cctv_source_id는 실제 cctv_sources.id일 때만 넣어야 한다.
    # 프론트의 selectedCctv + 1은 DB FK와 맞지 않을 수 있으므로 기본은 None 권장.
    cctv_source_id = _to_int_or_none(data.get("cctv_source_id"), "cctv_source_id")
    weather_log_id = _to_int_or_none(data.get("weather_log_id"), "weather_log_id")
    image_url = data.get("image_url")
    stream_url = data.get("stream_url")

    location_name = data.get("cctv_name")
    latitude = _to_float_or_none(data.get("latitude"), "latitude")
    longitude = _to_float_or_none(data.get("longitude"), "longitude")

    weather = ai_result.get("weather") or "UNKNOWN"
    weather_type = _normalize_weather_type(weather)
    weather_name = WEATHER_NAME_MAP.get(weather, WEATHER_NAME_MAP.get(weather_type, weather_type))

    yolo_result = _normalize_yolo_result(ai_result)
    weather_alerts = _build_weather_alerts(ai_result, cctv_source_id)
    risk_result = _build_risk_result(ai_result, yolo_result)

    final_alert = _generate_final_alert_with_gemma_or_fallback(
        ai_result=ai_result,
        weather_type=weather_type,
        weather_name=weather_name,
        weather_alerts=weather_alerts,
        risk_result=risk_result,
        yolo_result=yolo_result,
    )

    save_result = save_detection_event_result(
        cctv_source_id=cctv_source_id,
        weather_type=weather_type,
        weather_alerts=weather_alerts,
        yolo_result=yolo_result,
        risk_result=risk_result,
        final_alert=final_alert,
        image_url=image_url,
        weather_log_id=weather_log_id,
        location_name=location_name,
        latitude=latitude,
        longitude=longitude,
    )

    alert_save_result = None
    clip_url = None

    if final_alert.get("alert_required"):
        alert_save_result = save_alert_to_db(
            event_id=save_result.get("event_id"),
            final_alert=final_alert,
            weather_type=weather_type,
            risk_score=risk_result.get("risk_score", 0),
        )
        if stream_url and save_result.get("event_id"):
            clip_url = _save_hls_clip(stream_url, save_result["event_id"])
            if clip_url:
                from app.models.event_clip import EventClip
                from app.extensions import db
                try:
                    clip = EventClip(event_id=save_result["event_id"], clip_url=clip_url)
                    db.session.add(clip)
                    db.session.commit()
                    print(f"[DB] event_clips 저장 완료: {clip_url}")
                except Exception as e:
                    db.session.rollback()
                    print(f"[DB] event_clips 저장 실패: {e}")

    return {
        **save_result,
        "alert_save_result": alert_save_result,
        "clip_url": clip_url,
    }
            
def _pick_representative_vehicle(ai_result: dict) -> str:
    detected_vehicle = ai_result.get("detected_vehicle")

    # backend-ai가 이미 최종 대표 차종을 계산해서 넘긴 경우 우선 사용

    if isinstance(detected_vehicle, str) and detected_vehicle.strip():
        return detected_vehicle.split("(")[0].strip()

    boxes = ai_result.get("yolo_boxes") or []

    if not boxes:
        return "UNKNOWN"

    grouped = {}

    for box in boxes:
        if not isinstance(box, dict):
            continue

        class_name = (
            box.get("class_name")
            or box.get("label")
            or "UNKNOWN"
        )

        confidence = _to_ratio(box.get("confidence"))

        if class_name not in grouped:
            grouped[class_name] = {
                "count": 0,
                "max_confidence": 0,
                "sum_confidence": 0,
            }

        grouped[class_name]["count"] += 1
        grouped[class_name]["sum_confidence"] += confidence
        grouped[class_name]["max_confidence"] = max(
            grouped[class_name]["max_confidence"],
            confidence,
        )

    # 1순위: 많이 나온 차종
    # 2순위: 최고 신뢰도 높은 차종
    if not grouped:
        return "UNKNOWN"

    representative = max(
        grouped.items(),
        key=lambda item: (
            item[1]["count"],
            item[1]["max_confidence"],
        ),
    )[0]

    return representative
def _save_hls_clip(stream_url: str, event_id: int) -> str | None:
    """AI 서버에 요청해서 HLS 3초 클립 저장"""
    import requests as req
    from app.services.cctv_service import is_trusted_stream_url
    from app.services.ai_client_auth import AI_SERVER_HEADERS

    if not is_trusted_stream_url(stream_url):
        print(f"[CLIP] 허용되지 않은 stream_url이라 클립 저장을 건너뜀: {stream_url}")
        return None

    try:
        ai_url = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8000")
        res = req.post(
            f"{ai_url}/api/ai/clip/save",
            json={"stream_url": stream_url},
            headers=AI_SERVER_HEADERS,
            timeout=20,
        )
        data = res.json()
        if data.get("success"):
            print(f"[CLIP] AI 서버 클립 저장 완료: {data['clip_path']}")
            return data["clip_path"]
        else:
            print(f"[CLIP] AI 서버 클립 저장 실패: {data.get('message')}")
            return None
    except Exception as e:
        print(f"[CLIP] AI 서버 호출 오류: {e}")
        return None
