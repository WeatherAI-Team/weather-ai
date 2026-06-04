# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소들을 묶어주는 도구야.
# request는 사용자가 보낸 값을 읽을 때 써.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
# f-021 탐지 조회 결과 api 주소 담당 
from flask import Blueprint, request, jsonify
from flask import current_app
from app.services.hybrid_alert_service import run_hybrid_detection_flow
from app.services.ai_detection_save_service import save_ai_detection_result
from app.services.ai_service import analyze_video
from app import db
# 탐지 결과 기능을 처리하는 Service를 가져와.
from ..services.detection_service import DetectionService

# detection API 묶음을 만들어.
# 이 파일의 API 주소는 /api/detections 로 시작해.
detection_bp = Blueprint("detection", __name__, url_prefix="/api/detections")

# DetectionService를 만들어.
# 이제 API에서 탐지 결과 조회 기능을 사용할 수 있어.
detection_service = DetectionService()


@detection_bp.route("", methods=["GET"])
def get_detections():
    # 이 함수는 GET /api/detections 요청이 들어오면 실행돼.
    # 예: /api/detections?risk_level=high

    # alert_required는 주소에서 문자열로 들어와.
    # 예: ?alert_required=true
    alert_required = request.args.get("alert_required")

    # alert_required가 들어왔다면 문자열을 True/False로 바꿔줘.
    # "true"면 True, "false"면 False가 돼.
    if alert_required is not None:
        alert_required = alert_required.lower() == "true"

    # 사용자가 주소 뒤에 붙여서 보낸 검색 조건들을 읽어와.
    filters = {
        # 몇 번째 페이지를 볼지 정해.
        "page": request.args.get("page", 1, type=int),

        # 한 페이지에 몇 개를 보여줄지 정해.
        "per_page": request.args.get("per_page", 10, type=int),

        # 검색어를 받아.
        # 제목, 위치, LLM 요약 등에서 검색할 때 사용해.
        "keyword": request.args.get("keyword"),

        # 시작 날짜를 받아.
        # 이 날짜 이후의 탐지 결과만 볼 때 사용해.
        "start_date": request.args.get("start_date"),

        # 끝 날짜를 받아.
        # 이 날짜 이전의 탐지 결과만 볼 때 사용해.
        "end_date": request.args.get("end_date"),

        # 위치 이름을 받아.
        # 예: 강남대로
        "location_name": request.args.get("location_name"),

        # 날씨 종류를 받아.
        # 예: rain, snow
        "weather_type": request.args.get("weather_type"),

        # 위험도 단계를 받아.
        # 예: low, medium, high
        "risk_level": request.args.get("risk_level"),

        # 주요 차량 종류를 받아.
        # 예: heavy_truck
        "main_vehicle_type": request.args.get("main_vehicle_type"),

        # 이벤트 상태를 받아.
        # 예: pending, confirmed, resolved
        "event_status": request.args.get("event_status"),

        # 낮/밤 정보를 받아.
        # 예: day, night
        "time_type": request.args.get("time_type"),

        # 알림 필요 여부를 받아.
        "alert_required": alert_required
    }

    # Service에게 탐지 결과를 가져와 달라고 부탁해.
    result = detection_service.get_detections(filters)

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "탐지 결과 조회 성공",
        "data": result
    }), 200

@detection_bp.route("/analyze", methods=["POST"])
def analyze_detection():
    try:
        from app.services.weather_service import is_dangerous
        from app.services.weather_alert_service import _to_weather_type
        from app.services.gemma_service import judge_weather_gate, generate_final_alert
        from app.services.weather_log_service import create_weather_log_from_alerts
        from app.services.alert_save_service import save_alert_to_db

        # 1단계: 더미 날씨로 Gemma Gate 판단
        dangerous, alerts = is_dangerous()

        if not dangerous:
            return jsonify({
                "success": False,
                "message": "현재 악천후 없음, 탐지 중단",
            }), 200

        weather_summary = f"{alerts[0]['wrn_name']} {alerts[0]['level']} 발령"
        gate_result = judge_weather_gate(weather_summary)
        monitoring_required = gate_result.get("monitoring_required", False)

        if isinstance(monitoring_required, str):
            monitoring_required = monitoring_required.lower() == "true"

        if not monitoring_required:
            return jsonify({
                "success": False,
                "message": "Gemma Gate: 모니터링 불필요 판단",
                "gate_result": gate_result,
            }), 200

        # 2단계: 영상 파일 받아서 FastAPI로 전달
        
        if "file" not in request.files:
            return jsonify({
                "success": False,
                "message": "영상 파일이 필요합니다.",
            }), 400

        file = request.files["file"]

        from app.services.ai_service import analyze_video

        ai_result = analyze_video(
            file_storage=file,
            original_filename=file.filename,
        )

        # 3단계: weather_log DB 저장
        weather_type = _to_weather_type(alerts[0]["wrn_code"])
        weather_log = create_weather_log_from_alerts(
            cctv_source_id=None,
            weather_type=weather_type,
            weather_alerts=alerts,
            weather_risk_score=8 if alerts[0]["level"] == "경보" else 6,
        )

        # 4단계: YOLO 결과 정규화 및 Gemma 최종 알림 생성
        from app.services.ai_detection_save_service import (
            _normalize_yolo_result,
            _build_risk_result,
        )
        from app.services.detection_event_save_service import save_detection_event_result

        yolo_result = _normalize_yolo_result(ai_result)
        risk_result = _build_risk_result(ai_result, yolo_result)

        vehicle_name = yolo_result.get("representative_vehicle_name") or "위험 차량"
        vehicle_label = yolo_result.get("representative_vehicle") or "UNKNOWN"

        weather_data = {
            "type": alerts[0]["wrn_name"],
            "level": alerts[0]["level"],
            "summary": weather_summary,
            "gate_result": gate_result,
        }

        detection_result = {
            "vehicle_detected": ai_result.get("has_danger_car", False),
            "vehicle_type": vehicle_name,
            "representative_vehicle": vehicle_label,
            "representative_vehicle_name": vehicle_name,
            "confidence": ai_result.get("confidence"),
            "weather": ai_result.get("weather"),
            "danger_confidence": ai_result.get("danger_confidence"),
            "weather_counts": ai_result.get("weather_counts"),
            "risk_vehicle_count": len(ai_result.get("yolo_boxes", [])) if ai_result.get("yolo_boxes") else 0,
            "dangerous_objects": yolo_result.get("dangerous_objects", []),
            "instruction": (
                f"최종 차량 종류는 반드시 '{vehicle_name}'으로 사용하세요. "
                "RMC는 레미콘이며 탱크로리/LPG 가스차량이 아닙니다. "
                "차량 종류를 추측하거나 바꾸지 마세요."
            ),
        }

        final_alert = generate_final_alert(
            weather_data=weather_data,
            detection_result=detection_result,
        )

        risk_level = risk_result.get("risk_level") or final_alert.get("risk_level", "CAUTION")
        final_alert["risk_level"] = risk_level

        prefix = "긴급" if risk_level == "DANGER" else "주의"

        weather_code = weather_data.get("type") or ai_result.get("weather") or "위험 기상"

        WEATHER_NAME_MAP = {
            "heavy_rain": "폭우",
            "heavy_snow": "폭설",
            "HEAVY_RAIN": "폭우",
            "HEAVY_SNOW": "폭설",
            "rain": "비",
            "snow": "폭설",
            "fog": "안개",
            "clear": "맑음",
            "RAIN": "비",
            "SNOW": "폭설",
            "FOG": "안개",
            "CLEAR": "맑음",
        }

        weather_display_name = WEATHER_NAME_MAP.get(weather_code, weather_code)

        # Gemma가 차량명/날씨명을 잘못 만들더라도 최종 저장/팝업 제목은 보정값으로 고정
        final_alert["title"] = f"[{prefix}] {weather_display_name} {vehicle_name} 위험 탐지"

        final_alert["admin_message"] = (
            f"{weather_display_name} 상황에서 {vehicle_name} 차량이 감지되었습니다. "
            "관제센터 모니터링이 필요합니다."
        )

        if vehicle_name != "LPG 가스차량":
            wrong_words = ["탱크로리", "LPG", "가스차량", "유조차"]

            if any(word in final_alert.get("driver_message", "") for word in wrong_words):
                final_alert["driver_message"] = (
                    f"{weather_display_name} 상황입니다. "
                    "감속 운행하고 안전거리를 확보하십시오."
                )

            if any(word in final_alert.get("reason", "") for word in wrong_words):
                final_alert["reason"] = (
                    f"AI 날씨 탐지에서 {weather_display_name}가 감지되었고, "
                    f"AI 차량 탐지에서 {vehicle_name} 차량이 대표 위험 차량으로 감지되었습니다."
                )

        final_alert["alert_required"] = risk_result.get("alert_required", True)
        final_alert["false_positive_suspected"] = risk_result.get("false_positive_possible", False)

        # 4.5단계: backend-main에서 detection_events 저장 후 event_id 확보
        from app.services.ai_detection_save_service import (
            _normalize_yolo_result,
            _build_risk_result,
        )
        from app.services.detection_event_save_service import save_detection_event_result

        yolo_result = _normalize_yolo_result(ai_result)
        risk_result = _build_risk_result(ai_result, yolo_result)

        event_save_result = save_detection_event_result(
            cctv_source_id=None,
            weather_type=weather_type,
            weather_alerts=alerts,
            yolo_result=yolo_result,
            risk_result=risk_result,
            final_alert=final_alert,
            weather_log_id=weather_log.id,
            location_name="업로드 영상",
            latitude=None,
            longitude=None,
        )

        event_id = event_save_result.get("event_id")

        # 5단계: admin_boards + notifications DB 저장
        alert_save_result = save_alert_to_db(
            event_id=event_id,
            final_alert=final_alert,
            weather_type=weather_type,
            risk_score=risk_result.get("risk_score", 0),
        )

        # 6단계: event_clips 저장
        from app.models.event_clip import EventClip

        clip_path = ai_result.get("clip_path")
        if clip_path and event_id:
            try:
                clip = EventClip(
                    event_id=event_id,
                    clip_url=clip_path,
                )
                db.session.add(clip)
                db.session.commit()
                print(f"[DB] event_clips 저장 완료: {clip_path}")
            except Exception as e:
                db.session.rollback()
                print(f"[DB] event_clips 저장 실패: {e}")
        
        return jsonify({
            "success": True,
            "message": "탐지 분석 완료",
            "data": {
                "gate_result": gate_result,
                "ai_result": ai_result,
                "final_alert": final_alert,
                "weather_log_id": weather_log.id,
                "event_id": event_id,
                "event_save_result": event_save_result,
                "alert_save_result": alert_save_result,
            },
        }), 200
    
    except Exception:
        current_app.logger.exception("탐지 분석 중 오류 발생")
        return jsonify({
            "success": False,
            "message": "탐지 분석 처리 중 오류가 발생했습니다.",
        }), 500

@detection_bp.route("/save-result", methods=["POST"])
def save_detection_result():
    try:
        data = request.get_json() or {}

        result = save_ai_detection_result(data)

        return jsonify({
            "success": True,
            "message": "AI 탐지 결과 저장 성공",
            "data": result,
        }), 200

    except Exception:
        db.session.rollback()
        current_app.logger.exception("AI 탐지 결과 저장 중 오류 발생")

        return jsonify({
            "success": False,
            "message": "AI 탐지 결과 저장 중 오류가 발생했습니다.",
        }), 500
        
@detection_bp.route("/<int:detection_id>", methods=["GET"])
def get_detection_detail(detection_id):
    # 이 함수는 GET /api/detections/<id> 요청이 들어오면 실행돼.
    # 예: /api/detections/1 로 접속하면 detection_id에는 1이 들어와.

    # Service에게 해당 id의 탐지 이벤트를 가져와 달라고 부탁해.
    result = detection_service.get_detection_detail(detection_id)

    # 만약 result가 None이면 해당 id의 데이터가 없다는 뜻이야.
    if result is None:
        # 프론트에게 "찾을 수 없다"고 알려줘.
        return jsonify({
            "success": False,
            "message": "탐지 결과를 찾을 수 없습니다.",
            "data": None
        }), 404

    # 데이터가 있으면 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "탐지 결과 상세 조회 성공",
        "data": result
    }), 200