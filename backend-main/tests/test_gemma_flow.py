import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from app.services.gemma_service import judge_weather_gate, generate_final_alert


pytestmark = pytest.mark.skipif(
    not os.getenv("HF_TOKEN"),
    reason="HF_TOKEN이 없어서 Gemma 연동 테스트를 건너뜀"
)


def test_judge_weather_gate():
    weather_data = "호우 주의보 발령, 강풍 주의보 발령, 구역 L1052500"

    gate_result = judge_weather_gate(weather_data)

    print("Gate 결과:", gate_result)

    assert isinstance(gate_result, dict)
    assert "monitoring_required" in gate_result
    assert "risk_level" in gate_result
    assert "reason" in gate_result

    assert isinstance(gate_result["monitoring_required"], bool)
    assert gate_result["risk_level"] in ["LOW", "NORMAL", "CAUTION", "DANGER"]


def test_generate_final_alert():
    weather_data = {
        "alerts": "호우 주의보 발령, 강풍 주의보 발령, 구역 L1052500"
    }

    detection_result = {
        "camera_id": "CCTV-001",
        "location": "테스트 고속도로 구간",
        "objects": [
            {
                "label": "tank_lorry",
                "name": "탱크로리",
                "confidence": 0.87
            }
        ]
    }

    final_result = generate_final_alert(weather_data, detection_result)

    print("최종 알림 결과:", final_result)

    assert isinstance(final_result, dict)

    assert "risk_level" in final_result
    assert "title" in final_result
    assert "admin_message" in final_result
    assert "driver_message" in final_result
    assert "reason" in final_result
    assert "alert_required" in final_result
    assert "false_positive_suspected" in final_result

    assert final_result["risk_level"] in ["LOW", "NORMAL", "CAUTION", "DANGER"]
    assert isinstance(final_result["title"], str)
    assert isinstance(final_result["admin_message"], str)
    assert isinstance(final_result["driver_message"], str)
    assert isinstance(final_result["reason"], str)
    assert isinstance(final_result["alert_required"], bool)
    assert isinstance(final_result["false_positive_suspected"], bool)

    assert len(final_result["title"]) > 0
    assert len(final_result["admin_message"]) > 0
    assert len(final_result["driver_message"]) > 0