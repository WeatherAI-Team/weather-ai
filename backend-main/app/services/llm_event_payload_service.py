from datetime import datetime, timezone, timedelta
KST = timezone(timedelta(hours=9))

def build_detection_event_payload(
    weather_log_id,
    cctv_source_id,
    weather_type,
    yolo_result,
    risk_result,
    final_alert,
    location_name=None,
    latitude=None,
    longitude=None,
):
    now = datetime.now(KST).replace(tzinfo=None)

    yolo_result = yolo_result or {}
    risk_result = risk_result or {}
    final_alert = final_alert or {}


    objects = yolo_result.get("objects", [])
    dangerous_objects = yolo_result.get("dangerous_objects", [])

    total_vehicle_count = len(objects)
    risk_vehicle_count = len(dangerous_objects)
    normal_vehicle_count = max(total_vehicle_count - risk_vehicle_count, 0)

    main_vehicle_type = (
        dangerous_objects[0]["label"]
        if dangerous_objects
        else "UNKNOWN"
    )

    return {
        "cctv_source_id": cctv_source_id,
        "weather_log_id": weather_log_id,
        "event_title": final_alert.get("title", "위험 차량 감지"),
        "weather_type": weather_type or "UNKNOWN",
        "normal_vehicle_count": normal_vehicle_count,
        "risk_vehicle_count": risk_vehicle_count,
        "total_vehicle_count": total_vehicle_count,
        "traffic_density_score": min(total_vehicle_count * 10, 100),
        "main_vehicle_type": main_vehicle_type,
        "risk_score": risk_result.get("risk_score", 0),
        "risk_level": risk_result.get("risk_level", "LOW"),
        "event_status": "DETECTED",
        "llm_title": final_alert.get("title"),
        "llm_summary": final_alert.get("admin_message"),
        "llm_decision": final_alert.get("risk_level"),
        "llm_reason": final_alert.get("reason"),
        "location_name": location_name,
        "latitude": latitude,
        "longitude": longitude,
        "alert_required": final_alert.get("alert_required", False),
        "false_positive_suspected": final_alert.get("false_positive_suspected", False),
        "detection_confidence": yolo_result.get("max_confidence"),
        "score_filter_passed": risk_result.get("score_filter_passed", False),
        "time_type": "UNKNOWN",
        "model_name": "YOLO + Gemma",
        "detected_at": now,
        "created_at": now,
        "updated_at": now,
    }