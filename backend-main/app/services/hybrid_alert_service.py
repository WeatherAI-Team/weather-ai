# app/services/hybrid_alert_service.py

from app.services.weather_service import is_dangerous
from app.services.gemma_service import judge_weather_gate, generate_final_alert
from app.services.keras_detection_service import run_keras_first_detection
from app.services.yolo_detection_service import run_yolo_detection
from app.services.risk_score_service import calculate_risk_score, _gate_monitoring_required
from app.services.detection_event_save_service import save_detection_event_result

def _build_weather_summary(alerts: list[dict]) -> str:
    unique = []

    seen = set()

    for alert in alerts:
        key = alert.get("wrn_code")

        if key in seen:
            continue

        seen.add(key)

        unique.append(
            f"{alert['wrn_name']} {alert['level']} 발령 "
            f"(구역: {alert['reg_id']}, 발표시각: {alert['tm_fc']})"
        )

    return ", ".join(unique)


def run_hybrid_alert_flow(
    image_path: str | None = None,
    cctv_source_id: int | None = None,
    weather_log_id: int | None = None,
) -> dict:
    """
    1. 기상청 API 기반 LLM Gate
    2. Keras 1차 탐지
    3. YOLO 2차 정밀 탐지
    4. 위험 점수 계산
    5. Gemma 최종 알림 생성
    """

    dangerous, alerts = is_dangerous()

    if not dangerous:
        return {
            "alert_required": False,
            "reason": "현재 위험 기상 특보 없음",
            "cctv_source_id": cctv_source_id,
            "weather_log_id": weather_log_id,
            "weather_alerts": [],
        }

    weather_summary = _build_weather_summary(alerts)

    # 1단계: LLM Gate
    gate_result = judge_weather_gate(weather_summary)

    monitoring_required = gate_result.get("monitoring_required", False)

    if isinstance(monitoring_required, str):
        monitoring_required = monitoring_required.lower() == "true"

    if not _gate_monitoring_required(gate_result):
        return {
            "alert_required": False,
            "reason": gate_result.get("reason", "LLM Gate에서 모니터링 불필요 판단"),
            "cctv_source_id": cctv_source_id,
            "weather_log_id": weather_log_id,
            "weather_summary": weather_summary,
            "weather_alerts": alerts,
            "gate_result": gate_result,
        }

    # 2단계: Keras 1차 탐지
    keras_result = run_keras_first_detection(image_path=image_path)

    # Keras 모델이 없거나 skipped이면 YOLO는 그대로 진행
    should_run_yolo = (
        keras_result.get("possible_risk", True)
        or keras_result.get("used") is False
    )

    if should_run_yolo:
        yolo_result = run_yolo_detection(image_path=image_path)
    else:
        yolo_result = {
            "stage": "yolo",
            "used": False,
            "dangerous_vehicle_detected": False,
            "objects": [],
            "dangerous_objects": [],
            "max_confidence": None,
            "reason": "Keras 1차 탐지에서 위험 가능성이 낮아 YOLO 정밀 탐지 생략",
        }

    # 3단계: 위험 점수 계산
    risk_result = calculate_risk_score(
        weather_alerts=alerts,
        gate_result=gate_result,
        keras_result=keras_result,
        yolo_result=yolo_result,
    )

    if not risk_result["alert_required"]:
        return {
            "alert_required": False,
            "reason": "위험 점수가 알림 기준 미만",
            "cctv_source_id": cctv_source_id,
            "weather_log_id": weather_log_id,
            "weather_summary": weather_summary,
            "weather_alerts": alerts,
            "gate_result": gate_result,
            "keras_result": keras_result,
            "yolo_result": yolo_result,
            "risk_result": risk_result,
        }

    detection_result = {
        "image_path": image_path,
        "cctv_source_id": cctv_source_id,
        "keras_result": keras_result,
        "yolo_result": yolo_result,
        "risk_result": risk_result,
        }

    weather_data = {
        "weather_log_id": weather_log_id,
        "summary": weather_summary,
        "alerts": alerts,
        "gate_result": gate_result,
    }
    
    # 4단계: Gemma 최종 알림 생성
    final_alert = generate_final_alert(
        weather_data=weather_data,
        detection_result=detection_result,
    )

    save_result = save_detection_event_result(
        cctv_source_id=cctv_source_id,
        weather_type=alerts[0]["wrn_name"] if alerts else "UNKNOWN",
        weather_alerts=alerts,
        yolo_result=yolo_result,
        risk_result=risk_result,
        final_alert=final_alert,
        image_url=image_path,
    )

    return {
        "alert_required": True,
        "cctv_source_id": cctv_source_id,
        "weather_log_id": weather_log_id,
        "weather_summary": weather_summary,
        "weather_alerts": alerts,
        "gate_result": gate_result,
        "keras_result": keras_result,
        "yolo_result": yolo_result,
        "risk_result": risk_result,
        "final_alert": final_alert,
        "save_result": save_result,
        }

def run_hybrid_detection_flow(
    image_path: str | None = None,
    cctv_source_id: int | None = None,
    weather_log_id: int | None = None,
) -> dict:
    return run_hybrid_alert_flow(
        image_path=image_path,
        cctv_source_id=cctv_source_id,
        weather_log_id=weather_log_id,
    )