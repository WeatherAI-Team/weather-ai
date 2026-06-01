# app/services/cctv_gate_service.py

import time
from app.services.weather_service import is_dangerous, build_weather_summary
from app.services.gemma_service import judge_weather_gate

_GATE_CACHE = {
    "checked_at": 0,
    "result": None,
}

GATE_CACHE_SECONDS = 600


def get_cctv_monitoring_gate() -> dict:
    now = time.time()

    if (
        _GATE_CACHE["result"] is not None
        and now - _GATE_CACHE["checked_at"] < GATE_CACHE_SECONDS
    ):
        return {
            **_GATE_CACHE["result"],
            "cached": True,
        }

    try:
        dangerous, alerts = is_dangerous()
    except Exception as e:
        result = {
            "monitoring_required": False,
            "risk_level": "NORMAL",
            "reason": f"기상청 API 조회 실패로 CCTV AI 감시를 대기합니다: {e}",
            "weather_summary": "",
            "weather_alerts": [],
            "gate_result": {
                "monitoring_required": False,
                "risk_level": "NORMAL",
                "reason": "기상청 API 조회 실패",
            },
        }

        _GATE_CACHE["checked_at"] = now
        _GATE_CACHE["result"] = result
        return {**result, "cached": False}

    if not dangerous or not alerts:
        result = {
            "monitoring_required": False,
            "risk_level": "NORMAL",
            "reason": "현재 기상청 위험 특보가 없어 CCTV AI 감시를 대기합니다.",
            "weather_summary": "",
            "weather_alerts": [],
            "gate_result": {
                "monitoring_required": False,
                "risk_level": "NORMAL",
                "reason": "현재 위험 기상 특보 없음",
            },
        }

        _GATE_CACHE["checked_at"] = now
        _GATE_CACHE["result"] = result
        return {**result, "cached": False}

    try:
        weather_summary = build_weather_summary(alerts[0])
    except Exception:
        weather_summary = str(alerts[0])

    try:
        gate_result = judge_weather_gate(weather_summary)
    except Exception as e:
        result = {
            "monitoring_required": False,
            "risk_level": "CAUTION",
            "reason": f"Gemma Gate 판단 실패로 CCTV AI 감시를 대기합니다: {e}",
            "weather_summary": weather_summary,
            "weather_alerts": alerts,
            "gate_result": {
                "monitoring_required": False,
                "risk_level": "CAUTION",
                "reason": "Gemma Gate 판단 실패",
            },
        }

        _GATE_CACHE["checked_at"] = now
        _GATE_CACHE["result"] = result
        return {**result, "cached": False}

    monitoring_required = gate_result.get("monitoring_required", False)

    if isinstance(monitoring_required, str):
        monitoring_required = monitoring_required.lower() == "true"

    result = {
        "monitoring_required": monitoring_required,
        "risk_level": gate_result.get("risk_level", "CAUTION"),
        "reason": gate_result.get("reason", "Gemma Gate 판단 완료"),
        "weather_summary": weather_summary,
        "weather_alerts": alerts,
        "gate_result": gate_result,
    }

    _GATE_CACHE["checked_at"] = now
    _GATE_CACHE["result"] = result

    return {**result, "cached": False}