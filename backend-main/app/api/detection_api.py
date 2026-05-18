# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소들을 묶어주는 도구야.
# request는 사용자가 보낸 값을 읽을 때 써.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
from flask import Blueprint, request, jsonify

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