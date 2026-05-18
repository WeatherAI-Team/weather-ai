# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소들을 묶어주는 도구야.
# request는 사용자가 보낸 값을 읽을 때 써.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
# f-012 지도 API 연동
from flask import Blueprint, request, jsonify

# 지도 기능을 처리하는 MapService를 가져와.
from ..services.map_service import MapService


# 지도 API 묶음을 만들어.
# 이 파일의 API 주소는 /api/map 으로 시작해.
map_bp = Blueprint("map", __name__, url_prefix="/api/map")

# MapService를 만들어.
# 이제 API에서 지도 데이터를 가져올 수 있어.
map_service = MapService()


@map_bp.route("/events", methods=["GET"])
def get_map_event_markers():
    # 이 함수는 GET /api/map/events 요청이 들어오면 실행돼.
    # 쉽게 말하면 "지도에 찍을 탐지 이벤트 위치들을 주세요"라는 요청이야.

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
        "per_page": request.args.get("per_page", 100, type=int),

        # 검색어를 받아.
        # 제목, 위치, LLM 요약 등에서 검색할 때 사용해.
        "keyword": request.args.get("keyword"),

        # 시작 날짜를 받아.
        "start_date": request.args.get("start_date"),

        # 끝 날짜를 받아.
        "end_date": request.args.get("end_date"),

        # 위치 이름을 받아.
        "location_name": request.args.get("location_name"),

        # 날씨 유형을 받아.
        "weather_type": request.args.get("weather_type"),

        # 위험도 등급을 받아.
        "risk_level": request.args.get("risk_level"),

        # 주요 차량 유형을 받아.
        "main_vehicle_type": request.args.get("main_vehicle_type"),

        # 이벤트 처리 상태를 받아.
        "event_status": request.args.get("event_status"),

        # 낮/밤 정보를 받아.
        "time_type": request.args.get("time_type"),

        # 알림 필요 여부를 받아.
        "alert_required": alert_required
    }

    # Service에게 지도에 표시할 탐지 이벤트 목록을 가져와 달라고 부탁해.
    result = map_service.get_event_markers(filters)

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "지도 탐지 이벤트 위치 조회 성공",
        "data": result
    }), 200