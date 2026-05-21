import os
from dotenv import load_dotenv
from .weather_service import is_dangerous
from .gemma_service import generate_alert_message

load_dotenv()

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
        weather_summary = f"{alert['wrn_name']} {alert['level']} 발령 (구역: {alert['reg_id']})"
        try:
            message = generate_alert_message(weather_summary)
        except Exception as e:
            print(f"[Gemma 오류] 기본 메시지 사용: {e}")
            message = f"{alert['wrn_name']} {alert['level']} 발령, 도로 상황 모니터링 필요"

        event_data = {
            "type": alert["wrn_name"],
            "risk_level": 8 if alert["level"] == "경보" else 6,
            "message": message,
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