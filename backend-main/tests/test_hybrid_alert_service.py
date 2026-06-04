from app.services.hybrid_alert_service import run_hybrid_detection_flow


def test_hybrid_detection_flow_with_mock(monkeypatch):
    import app.services.hybrid_alert_service as hybrid

    monkeypatch.setattr(
        hybrid,
        "is_dangerous",
        lambda: (
            True,
            [
                {
                    "wrn_code": "R",
                    "wrn_name": "호우",
                    "level": "주의보",
                    "reg_id": "L1052500",
                    "tm_fc": "202605191600",
                }
            ],
        ),
    )

    monkeypatch.setattr(
        hybrid,
        "judge_weather_gate",
        lambda weather_summary: {
            "monitoring_required": True,
            "risk_level": "CAUTION",
            "reason": "호우 주의보로 모니터링 필요",
        },
    )

    monkeypatch.setattr(
        hybrid,
        "run_keras_first_detection",
        lambda image_path=None: {
            "stage": "keras",
            "used": False,
            "possible_risk": True,
            "confidence": None,
            "label": "skipped",
            "reason": "테스트",
        },
    )

    monkeypatch.setattr(
        hybrid,
        "run_yolo_detection",
        lambda image_path=None: {
            "stage": "yolo",
            "used": True,
            "dangerous_vehicle_detected": True,
            "objects": [
                {
                    "label": "Gas_Truck",
                    "confidence": 0.9,
                    "dangerous": True,
                    "bbox": [10, 20, 100, 200],
                }
            ],
            "dangerous_objects": [
                {
                    "label": "Gas_Truck",
                    "confidence": 0.9,
                    "dangerous": True,
                    "bbox": [10, 20, 100, 200],
                }
            ],
            "max_confidence": 0.9,
            "reason": "테스트",
        },
    )

    monkeypatch.setattr(
        hybrid,
        "generate_final_alert",
        lambda weather_data, detection_result: {
            "risk_level": "DANGER",
            "title": "호우 위험차량 감지",
            "admin_message": "관제센터 확인 필요",
            "driver_message": "감속하고 안전거리를 확보하세요.",
            "reason": "호우와 위험차량 동시 감지",
            "alert_required": True,
            "false_positive_suspected": False,
        },
    )

    if hasattr(hybrid, "save_detection_event_result"):
        monkeypatch.setattr(
            hybrid,
            "save_detection_event_result",
            lambda **kwargs: {
                "saved": True,
                "event_id": 1,
                "weather_log_id": 1,
                "object_count": 1,
            },
        )

    result = run_hybrid_detection_flow(
        image_path="test.jpg",
        cctv_source_id=1,
        weather_log_id=None,
    )

    print(result)

    assert result["alert_required"] is True
    assert result["cctv_source_id"] == 1
    assert result["risk_result"]["alert_required"] is True
    assert result["final_alert"]["title"] == "호우 위험차량 감지"