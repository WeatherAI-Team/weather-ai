from app.services.risk_score_service import calculate_risk_score


def test_calculate_risk_score_with_weather_and_dangerous_vehicle():
    weather_alerts = [
        {
            "wrn_name": "호우",
            "level": "주의보",
        }
    ]

    gate_result = {
        "monitoring_required": True,
        "risk_level": "CAUTION",
        "reason": "호우 주의보로 모니터링 필요",
    }

    keras_result = {
        "possible_risk": True,
        "confidence": 0.8,
    }

    yolo_result = {
        "dangerous_vehicle_detected": True,
        "max_confidence": 0.87,
        "objects": [
            {"label": "Gas_Truck", "confidence": 0.87}
        ],
        "dangerous_objects": [
            {"label": "Gas_Truck", "confidence": 0.87}
        ],
    }

    result = calculate_risk_score(
        weather_alerts=weather_alerts,
        gate_result=gate_result,
        keras_result=keras_result,
        yolo_result=yolo_result,
    )

    print(result)

    assert result["risk_score"] >= 60
    assert result["risk_level"] in ["CAUTION", "DANGER"]
    assert result["alert_required"] is True
    assert result["score_filter_passed"] is True