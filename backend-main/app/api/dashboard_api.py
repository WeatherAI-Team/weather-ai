# Flask에서 필요한 도구들을 가져와.
# Blueprint는 API 주소들을 묶어주는 도구야.
# jsonify는 Python 데이터를 JSON으로 바꿔줘.
# f-022 관리자 대시보드
from flask import Blueprint, jsonify

# 관리자 대시보드 기능을 처리하는 DashboardService를 가져와.
from ..services.dashboard_service import DashboardService


# 관리자 대시보드 API 묶음을 만들어.
# 이 파일의 API 주소는 /api/admin/dashboard 로 시작해.
dashboard_bp = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/api/admin/dashboard"
)

# DashboardService를 만들어.
# 이제 API에서 대시보드 통계 기능을 사용할 수 있어.
dashboard_service = DashboardService()


@dashboard_bp.route("/weekly", methods=["GET"])
def get_weekly_counts():
    result = dashboard_service.get_weekly_counts()
    return jsonify({"success": True, "data": result}), 200


@dashboard_bp.route("/summary", methods=["GET"])
def get_dashboard_summary():
    # 이 함수는 GET /api/admin/dashboard/summary 요청이 들어오면 실행돼.
    # 쉽게 말하면 "관리자 대시보드에 보여줄 요약 통계를 주세요"라는 요청이야.

    # Service에게 대시보드 요약 통계를 만들어 달라고 부탁해.
    result = dashboard_service.get_summary()

    # 결과를 JSON 형태로 프론트에게 보내줘.
    return jsonify({
        "success": True,
        "message": "관리자 대시보드 요약 조회 성공",
        "data": result
    }), 200