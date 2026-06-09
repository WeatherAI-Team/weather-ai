from flask import Blueprint, request, jsonify
from ..services.member_service import MemberService
from app.utils.auth_decorators import login_required

# 블루프린트 설정 (url_prefix가 있으니 /api/member/google 로 접속됨)
member_bp = Blueprint('member', __name__, url_prefix='/api/member')


member_service = MemberService()


@member_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "회원가입 정보를 입력해주세요."
        }), 400
    
    result = member_service.register_member(data)
    
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400

@member_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "로그인 정보를 입력해주세요."
        }), 400

    result = member_service.login_member(data)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 401


# GET http://localhost:5000/api/member/1
@member_bp.route('/<int:member_id>', methods=['GET'])
@login_required
def get_profile(member_id):
    if request.user_id != member_id and request.user_role not in ("admin", "manager"):
        return jsonify({
            "success": False,
            "message": "본인 정보만 조회할 수 있습니다."
        }), 403

    result = member_service.get_member_info(member_id)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 404

@member_bp.route("/me", methods=["GET"])
@login_required
def get_my_profile():
    service = MemberService()
    result = service.get_member_info(request.user_id)
    return jsonify(result)


@member_bp.route("/me", methods=["PUT"])
@login_required
def update_my_profile():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "수정할 정보를 입력해주세요."
        }), 400

    result = member_service.update_member_info(request.user_id, data)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 400

@member_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    return jsonify({
        "success": True,
        "message": "로그아웃되었습니다."
    }), 200


@member_bp.route("/find-id", methods=["POST"])
def find_id():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "이메일을 입력해주세요."
        }), 400
    
    service = MemberService()
    result = service.find_login_id(data)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 404

@member_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()

    if not data or not data.get("email"):
        return jsonify({
            "success": False,
            "message": "이메일을 입력해주세요."
        }), 400

    result = member_service.request_password_reset(data)

    return jsonify(result), 200


@member_bp.route("/reset-password", methods=["POST"])
def reset_password():
    # 토큰은 URL에서 추출 (?token=abc123...)
    token = request.args.get("token")
    
    if not token:
        return jsonify({
            "success": False,
            "message": "유효하지 않은 접근입니다."
        }), 400

    data = request.get_json()

    if not data or not data.get("new_password"):
        return jsonify({
            "success": False,
            "message": "새 비밀번호를 입력해주세요."
        }), 400

    result = member_service.reset_password(token, data["new_password"])

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 400

@member_bp.route("/me/password", methods=["PUT"])
@login_required
def change_my_password():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "비밀번호 정보를 입력해주세요."
        }), 400

    result = member_service.change_password(request.user_id, data)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 400

@member_bp.route("/me/notifications", methods=["GET"])
@login_required
def get_my_noti_settings():
    result = member_service.get_noti_settings(request.user_id)
    return jsonify(result), 200 if result["success"] else 404

@member_bp.route("/me/notifications", methods=["PUT"])
@login_required
def update_my_noti_settings():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "수정할 정보를 입력해주세요."}), 400
    result = member_service.update_noti_settings(request.user_id, data)
    return jsonify(result), 200 if result["success"] else 400

@member_bp.route("/me/withdraw", methods=["PATCH"])
@login_required
def withdraw_my_account():
    result = member_service.withdraw_member(request.user_id)

    if result["success"]:
        return jsonify(result), 200

    return jsonify(result), 400