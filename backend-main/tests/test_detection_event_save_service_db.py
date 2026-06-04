from app import create_app
from app.services.detection_event_save_service import save_detection_event_result


def test_save_detection_event_result_db_rollback():
    app = create_app()

    with app.app_context():
        yolo_result = {
            "objects": [
                {
                    "label": "Gas_Truck",
                    "confidence": 0.91,
                    "dangerous": True,
                    "bbox": [10, 20, 110, 220],
                }
            ],
            "dangerous_objects": [
                {
                    "label": "Gas_Truck",
                    "confidence": 0.91,
                    "dangerous": True,
                    "bbox": [10, 20, 110, 220],
                }
            ],
            "max_confidence": 0.91,
            "dangerous_vehicle_detected": True,
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

        result = save_detection_event_result(
            cctv_source_id=None,
            weather_type="호우",
            weather_alerts=[
                {
                    "wrn_code": "R",
                    "wrn_name": "호우",
                    "level": "주의보",
                    "reg_id": "L1052500",
                    "tm_fc": "202605191600",
                }
            ],
            yolo_result=yolo_result,
            risk_result=risk_result,
            final_alert=final_alert,
            image_url="test.jpg",
            commit=False,
        )

        print(result)

        assert result["saved"] is True
        assert result["event_id"] is not None
        assert result["weather_log_id"] is not None
        assert result["object_count"] == 1