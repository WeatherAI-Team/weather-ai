from app.services.gemma_service import judge_weather_gate, generate_final_alert


weather_data = "호우 주의보 발령, 강풍 주의보 발령, 구역 L1052500"

print("===== LLM Gate 테스트 =====")
gate_result = judge_weather_gate(weather_data)
print(gate_result)


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

print("\n===== 최종 알림 테스트 =====")
final_result = generate_final_alert({"alerts": weather_data}, detection_result)
print(final_result)