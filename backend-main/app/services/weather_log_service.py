# app/services/weather_log_service.py

from app.repositories.weather_log_repo import WeatherLogRepository
from datetime import datetime



def create_weather_log_from_alerts(
    cctv_source_id,
    weather_type,
    weather_alerts,
    weather_risk_score=0,
):
    repo = WeatherLogRepository()

    return repo.create_weather_log({
        "cctv_source_id": cctv_source_id,
        "weather_type": weather_type or "UNKNOWN",
        "temperature": None,
        "precipitation": None,
        "snowfall": None,
        "visibility": None,
        "weather_risk_score": weather_risk_score,
        "source": "KMA",
        "raw_data": {
            "alerts": weather_alerts,
        },
        "created_at": datetime.utcnow(),
    })

WEATHER_TYPE_LABELS = {
    "HEAVY_RAIN": "폭우",
    "RAIN": "비",
    "FOG": "안개",
    "SNOW": "폭설",
    "HEAVY_SNOW": "폭설",
    "CLEAR": "맑음",
}


def _to_weather_name(weather_type: str | None) -> str:
    if not weather_type:
        return "UNKNOWN"

    return WEATHER_TYPE_LABELS.get(weather_type, weather_type)


def _to_alert_level(weather_risk_score: int | None) -> str:
    score = weather_risk_score or 0

    if score >= 80:
        return "경보"

    if score >= 50:
        return "주의보"

    return "관심"


def weather_log_to_dict(weather_log) -> dict | None:
    if weather_log is None:
        return None

    weather_name = _to_weather_name(weather_log.weather_type)
    level = _to_alert_level(weather_log.weather_risk_score)

    return {
        "weather_log_id": weather_log.id,
        "cctv_source_id": weather_log.cctv_source_id,
        "weather_type": weather_log.weather_type,
        "weather_name": weather_name,
        "level": level,
        "temperature": float(weather_log.temperature) if weather_log.temperature is not None else None,
        "precipitation": float(weather_log.precipitation) if weather_log.precipitation is not None else None,
        "snowfall": float(weather_log.snowfall) if weather_log.snowfall is not None else None,
        "visibility": float(weather_log.visibility) if weather_log.visibility is not None else None,
        "weather_risk_score": weather_log.weather_risk_score,
        "source": weather_log.source,
        "raw_data": weather_log.raw_data,
        "created_at": weather_log.created_at.isoformat() if weather_log.created_at else None,
    }


def build_weather_summary_from_log(weather_log_data: dict) -> str:
    weather_name = weather_log_data.get("weather_name", "UNKNOWN")
    level = weather_log_data.get("level", "관심")
    risk_score = weather_log_data.get("weather_risk_score", 0)
    visibility = weather_log_data.get("visibility")
    precipitation = weather_log_data.get("precipitation")
    snowfall = weather_log_data.get("snowfall")
    temperature = weather_log_data.get("temperature")

    return (
        f"{weather_name} {level} 상황 "
        f"(위험점수: {risk_score}, "
        f"가시거리: {visibility}, "
        f"강수량: {precipitation}, "
        f"적설량: {snowfall}, "
        f"기온: {temperature})"
    )


def build_alert_from_weather_log(weather_log_data: dict) -> dict:
    return {
        "wrn_code": weather_log_data.get("weather_type", "UNKNOWN"),
        "wrn_name": weather_log_data.get("weather_name", "UNKNOWN"),
        "level": weather_log_data.get("level", "관심"),
        "reg_id": str(weather_log_data.get("cctv_source_id") or "UNKNOWN"),
        "tm_fc": weather_log_data.get("created_at") or "",
    }


def get_weather_context_from_db(
    weather_log_id: int | None = None,
    cctv_source_id: int | None = None,
) -> dict | None:
    repo = WeatherLogRepository()

    if weather_log_id:
        weather_log = repo.find_by_id(weather_log_id)
    elif cctv_source_id:
        weather_log = repo.find_latest_by_cctv_source_id(cctv_source_id)
    else:
        weather_log = repo.find_latest()

    weather_log_data = weather_log_to_dict(weather_log)

    if not weather_log_data:
        return None

    summary = build_weather_summary_from_log(weather_log_data)
    alert = build_alert_from_weather_log(weather_log_data)

    return {
        "weather_log_id": weather_log_data["weather_log_id"],
        "cctv_source_id": weather_log_data["cctv_source_id"],
        "weather_log": weather_log_data,
        "summary": summary,
        "alerts": [alert],
    }