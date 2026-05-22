from flask import Blueprint, jsonify, current_app

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
        alerts = check_and_generate_alerts() or []

        return jsonify({
            "success": True,
            "dangerous": len(alerts) > 0,
            "alerts": alerts,
        }), 200

    except Exception:
        current_app.logger.exception("기상 알림 생성 중 오류 발생")

        return jsonify({
            "success": False,
            "message": "기상 알림 처리 중 오류가 발생했습니다.",
        }), 500