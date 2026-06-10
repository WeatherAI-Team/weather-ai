from flask import Blueprint, request, jsonify
from ..services.admin_member_service import AdminMemberService
from app.utils.auth_decorators import admin_required

# 관리자 사용자 조회 전용 Blueprint
admin_member_bp = Blueprint("admin_member", __name__)

# 관리자 사용자 조회 서비스 준비
admin_member_service = AdminMemberService()


# f-006 관리자 사용자 목록 조회
# GET /api/admin/members
# GET /api/admin/members?page=1&per_page=10
# GET /api/admin/members?keyword=테스트
# GET /api/admin/members?role=user
# GET /api/admin/members?active=true
@admin_member_bp.route("", methods=["GET"])
@admin_required
def get_members():
    # 주소에서 page 값을 가져와.
    # 없으면 기본값 1을 사용해.
    page = request.args.get("page", 1, type=int)

    # 주소에서 per_page 값을 가져와.
    # 없으면 기본값 10을 사용해.
    per_page = request.args.get("per_page", 10, type=int)

    # 검색어를 가져와.
    keyword = request.args.get("keyword")

    # 권한 필터를 가져와.
    role = request.args.get("role")

    # 활성 상태 필터를 가져와.
    active_param = request.args.get("active")

    # active가 없으면 전체 조회
    active = None

    # active=true / active=false를 진짜 True/False로 바꿔줘.
    if active_param is not None:
        active = active_param.lower() == "true"

    # 서비스에게 사용자 목록을 가져오라고 요청해.
    result = admin_member_service.get_member_list(
        page=page,
        per_page=per_page,
        keyword=keyword,
        role=role,
        active=active
    )

    return jsonify(result), 200


# f-006 관리자 사용자 상세 조회
# GET /api/admin/members/1
@admin_member_bp.route("/<int:member_id>", methods=["GET"])
@admin_required
def get_member_detail(member_id):
    # 서비스에게 해당 id의 사용자 정보를 가져오라고 요청해.
    result = admin_member_service.get_member_detail(member_id)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 404

# f-006 관리자 사용자 활성/비활성 변경
# PATCH /api/admin/members/1/active
@admin_member_bp.route("/<int:member_id>/active", methods=["PATCH"])
@admin_required
def update_member_active(member_id):
    # 프론트에서 보낸 JSON 데이터를 가져와.
    body = request.get_json() or {}

    # active 값이 없으면 어떤 상태로 바꿀지 모르니까 실패 처리해.
    if "active" not in body:
        return jsonify({
            "success": False,
            "message": "active 값이 필요합니다."
        }), 400

    # 프론트에서 받은 active 값을 True/False로 바꿔.
    active = bool(body.get("active"))

    # 서비스에게 실제 DB 변경을 요청해.
    result = admin_member_service.update_member_active(
        member_id=member_id,
        active=active
    )

    # 실패하면 404로 응답해.
    if not result["success"]:
        return jsonify(result), 404

    # 성공하면 200으로 응답해.
    return jsonify(result), 200