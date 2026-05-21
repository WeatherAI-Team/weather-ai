from flask import Blueprint, jsonify

from app.services.weather_alert_service import check_and_generate_alerts

# 기상청 API 조회
# 위험 특보 있으면 Gemma 호출
# 최종 경고 메시지 반환

weather_alert_bp = Blueprint(
    "weather_alert",
    __name__,
    url_prefix="/api/weather-alert"
)


@weather_alert_bp.route("", methods=["GET"])
def get_weather_alert():
    try:
        alerts = check_and_generate_alerts()

        return jsonify({
            "success": True,
            "dangerous": len(alerts) > 0,
            "alerts": alerts,
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e),
            "dangerous": False,
            "alerts": [],
        }), 500