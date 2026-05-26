import os
from dotenv import load_dotenv
from .weather_service import is_dangerous, build_weather_summary
from .gemma_service import judge_weather_gate, generate_final_alert

load_dotenv()


def _is_monitoring_required(gate_result: dict) -> bool:
    value = gate_result.get("monitoring_required", False)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() == "true"

    raw_message = gate_result.get("raw_message", "")

    if isinstance(raw_message, str):
        lowered = raw_message.lower()
        if '"monitoring_required": true' in lowered:
            return True
        if "monitoring_required" in lowered and "true" in lowered:
            return True

    return False

def check_and_generate_alerts() -> list:
    dangerous, alerts = is_dangerous()

    if not dangerous:
        print("[날씨] 현재 악천후 없음")
        return []

    # 중복 제거
    seen = set()
    unique_alerts = []
    for alert in alerts:
        if alert["wrn_code"] not in seen:
            seen.add(alert["wrn_code"])
            unique_alerts.append(alert)

    results = []

    for alert in unique_alerts:
        weather_summary = build_weather_summary(alert)

        try:
            # 1단계: Gate 판단
            gate_result = judge_weather_gate(weather_summary)

            if not _is_monitoring_required(gate_result):
                print(f"[날씨 Gate] 알림 불필요: {gate_result}")
                continue

            # 현재는 차량 탐지 결과가 없으므로 기상 알림 전용 값으로 전달
            detection_result = {
                "vehicle_detected": False,
                "vehicle_type": None,
                "confidence": None,
                "source": "weather_alert_only",
            }

            weather_data = {
                "type": alert["wrn_name"],
                "level": alert["level"],
                "reg_id": alert["reg_id"],
                "tm_fc": alert["tm_fc"],
                "summary": weather_summary,
                "gate_result": gate_result,
            }

            # 2단계: 최종 알림 생성
            final_alert = generate_final_alert(
                weather_data=weather_data,
                detection_result=detection_result,
            )

            message = (
                final_alert.get("driver_message")
                or final_alert.get("admin_message")
                or f"{alert['wrn_name']} {alert['level']} 발령, 도로 상황 모니터링 필요"
            )


        except Exception as e:
            print(f"[Gemma 오류] 기본 메시지 사용: {e}")
            gate_result = {}
            final_alert = {}

            message = f"{alert['wrn_name']} {alert['level']} 발령, 도로 상황 모니터링 필요"

        event_data = {
            "type": alert["wrn_name"],
            "risk_level": 8 if alert["level"] == "경보" else 6,
            "message": message,
            "weather_level": alert["level"],
            "reg_id": alert["reg_id"],
            "tm_fc": alert["tm_fc"],
            "gate_result": gate_result,
            "final_alert": final_alert,
        }

        results.append(event_data)
        print(f"[날씨 알람] {message}")

    return results


def check_and_send_alerts(socketio=None) -> list:
    results = check_and_generate_alerts()

    if socketio:
        from ..socket_events import send_danger_alert
        for event_data in results:
            send_danger_alert(event_data)

    return results