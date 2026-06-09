# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소들을 묶어주는 도구야.
# request는 사용자가 보낸 값을 읽을 때 써.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
from flask import Blueprint, request, jsonify

# 알림 기능을 처리하는 AlertService를 가져와.
from ..services.alert_service import AlertService

from app.utils.auth_decorators import admin_required
# 관리자 알림 API 묶음을 만들어.
# 이 파일의 API 주소는 /api/admin/alerts 로 시작해.
alert_bp = Blueprint("alert", __name__, url_prefix="/api/admin/alerts")

# AlertService를 만들어.
# 이제 API에서 알림 조회 기능을 사용할 수 있어.
alert_service = AlertService()


@alert_bp.route("", methods=["GET"])
@admin_required
def get_admin_alerts():
    # 이 함수는 GET /api/admin/alerts 요청이 들어오면 실행돼.
    # 예: /api/admin/alerts?risk_level=high

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
        # 이 날짜 이후의 알림만 볼 때 사용해.
        "start_date": request.args.get("start_date"),

        # 끝 날짜를 받아.
        # 이 날짜 이전의 알림만 볼 때 사용해.
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
        "time_type": request.args.get("time_type")
    }

    # Service에게 관리자 알림 목록을 가져와 달라고 부탁해.
    result = alert_service.get_admin_alerts(filters)

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "관리자 알림 내역 조회 성공",
        "data": result
    }), 200

# f-014 관리자 알림 위치 표시 API
@alert_bp.route("/map", methods=["GET"])
@admin_required
def get_admin_alert_map_markers():
    # 이 함수는 GET /api/admin/alerts/map 요청이 들어오면 실행돼.
    # 쉽게 말하면 "지도에 찍을 알림 위치 목록을 주세요"라는 요청이야.

    # Service에게 지도에 표시할 알림 위치 목록을 가져와 달라고 부탁해.
    result = alert_service.get_admin_alert_map_markers()

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "관리자 알림 지도 위치 조회 성공",
        "data": result
    }), 200

# f-013 지역별 알림 현황
@alert_bp.route("/locations", methods=["GET"])
@admin_required
def get_admin_alert_location_summary():
    # 이 함수는 GET /api/admin/alerts/locations 요청이 들어오면 실행돼.
    # 쉽게 말하면 "지역별 알림 현황을 보여줘"라는 요청이야.

    # Service에게 지역별 알림 현황을 만들어 달라고 부탁해.
    result = alert_service.get_admin_alert_location_summary()

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "지역별 알림 현황 조회 성공",
        "data": result
    }), 200

@alert_bp.route("/<int:alert_id>", methods=["GET"])
@admin_required
def get_admin_alert_detail(alert_id):
    # 이 함수는 GET /api/admin/alerts/<id> 요청이 들어오면 실행돼.
    # 예: /api/admin/alerts/1 로 접속하면 alert_id에는 1이 들어와.

    # Service에게 해당 id의 알림 상세 정보를 가져와 달라고 부탁해.
    result = alert_service.get_admin_alert_detail(alert_id)

    # result가 None이면 해당 id의 알림을 찾을 수 없다는 뜻이야.
    if result is None:
        # 프론트에게 "찾을 수 없다"고 알려줘.
        return jsonify({
            "success": False,
            "message": "관리자 알림을 찾을 수 없습니다.",
            "data": None
        }), 404

    # 알림 데이터가 있으면 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "관리자 알림 상세 조회 성공",
        "data": result
    }), 200