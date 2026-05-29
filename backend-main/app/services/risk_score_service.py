# app/services/risk_score_service.py


def _gate_monitoring_required(gate_result: dict) -> bool:
    value = gate_result.get("monitoring_required", False)

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() == "true"

    raw_message = gate_result.get("raw_message", "")

    if isinstance(raw_message, str):
        lowered = raw_message.lower()
        return "monitoring_required" in lowered and "true" in lowered

    return False


def calculate_risk_score(
    weather_alerts: list[dict],
    gate_result: dict,
    keras_result: dict | None = None,
    yolo_result: dict | None = None,
) -> dict:
    score = 0
    reasons = []

    keras_result = keras_result or {}
    yolo_result = yolo_result or {}

    for alert in weather_alerts:
        wrn_name = alert.get("wrn_name")
        level = alert.get("level")

        if level == "경보":
            score += 30
            reasons.append(f"{wrn_name} 경보 발령")
        elif level == "주의보":
            score += 20
            reasons.append(f"{wrn_name} 주의보 발령")

    monitoring_required = _gate_monitoring_required(gate_result)

    if isinstance(monitoring_required, str):
        monitoring_required = monitoring_required.lower() == "true"

    if monitoring_required:
        score += 10
        reasons.append("Gemma Gate에서 모니터링 필요 판단")

    if keras_result.get("possible_risk"):
        score += 10
        reasons.append("Keras 1차 탐지에서 위험 가능성 감지")

    if yolo_result.get("dangerous_vehicle_detected"):
        score += 30
        reasons.append("YOLO 정밀 탐지에서 위험 차량 감지")

    yolo_conf = yolo_result.get("max_confidence")

    if isinstance(yolo_conf, float):
        if yolo_conf >= 0.85:
            score += 10
        elif yolo_conf >= 0.65:
            score += 5

    score = min(score, 100)

    if score >= 80:
        risk_level = "DANGER"
    elif score >= 60:
        risk_level = "CAUTION"
    elif score >= 30:
        risk_level = "NORMAL"
    else:
        risk_level = "LOW"

    false_positive_possible = False

    if yolo_result.get("dangerous_vehicle_detected") and yolo_conf is not None and yolo_conf < 0.55:
        false_positive_possible = True
        reasons.append("YOLO 신뢰도가 낮아 오탐 가능성 있음")

    alert_required = score >= 60 and monitoring_required

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "alert_required": alert_required,
        "false_positive_possible": false_positive_possible,
        "score_filter_passed": score >= 60,
        "reasons": reasons,
    }