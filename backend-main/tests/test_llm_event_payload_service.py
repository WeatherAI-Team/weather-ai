from app.services.llm_event_payload_service import build_detection_event_payload


def test_build_detection_event_payload():
    yolo_result = {
        "objects": [
            {
                "label": "Gas_Trcuk",
                "confidence": 0.91,
                "dangerous": True,
                "bbox": [10, 20, 110, 220],
            },
            {
                "label": "cargo_truck",
                "confidence": 0.75,
                "dangerous": True,
                "bbox": [30, 40, 130, 240],
            },
        ],
        "dangerous_objects": [
            {
                "label": "Gas_Trcuk",
                "confidence": 0.91,
                "dangerous": True,
            }
        ],
        "max_confidence": 0.91,
    }

    risk_result = {
        "risk_score": 85,
        "risk_level": "DANGER",
        "alert_required": True,
        "score_filter_passed": True,
        "false_positive_possible": False,
    }

    final_alert = {
        "risk_level": "DANGER",
        "title": "호우 위험차량 감지",
        "admin_message": "관제센터 확인 필요",
        "driver_message": "감속하고 안전거리를 확보하세요.",
        "reason": "호우와 위험차량 동시 감지",
        "alert_required": True,
        "false_positive_suspected": False,
    }

    payload = build_detection_event_payload(
        weather_log_id=1,
        cctv_source_id=1,
        weather_type="호우",
        yolo_result=yolo_result,
        risk_result=risk_result,
        final_alert=final_alert,
    )

    print(payload)

    assert payload["weather_log_id"] == 1
    assert payload["cctv_source_id"] == 1
    assert payload["weather_type"] == "호우"
    assert payload["total_vehicle_count"] == 2
    assert payload["risk_vehicle_count"] == 1
    assert payload["main_vehicle_type"] == "Gas_Trcuk"
    assert payload["risk_score"] == 85
    assert payload["risk_level"] == "DANGER"
    assert payload["alert_required"] is True
    assert payload["score_filter_passed"] is True
    assert payload["event_status"] == "DETECTED"
    assert payload["detected_at"] is not None
    assert payload["created_at"] is not None
    assert payload["updated_at"] is not None