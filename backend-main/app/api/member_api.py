from flask import Blueprint, request, jsonify, make_response
from ..services.member_service import MemberService
from functools import wraps
from jose import jwt
import os

member_bp = Blueprint('member', __name__, url_prefix='/api/member')
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")

member_service = MemberService()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # ✅ 헤더 또는 쿠키에서 토큰 읽기
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header
        if not token:
            token = request.cookies.get('access_token')
        if not token:
            return jsonify({"success": False, "message": "토큰이 없습니다."}), 401
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload.get("sub")
        except:
            return jsonify({"success": False, "message": "유효하지 않은 토큰입니다."}), 401
        return f(*args, **kwargs)
    return decorated

@member_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "회원가입 정보를 입력해주세요."}), 400
    print(f"DEBUG: 프론트에서 온 데이터 -> {data}")
    result = member_service.register_member(data)
    if result["success"]:
        return jsonify(result), 201
    return jsonify(result), 400

@member_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "로그인 정보를 입력해주세요."}), 400

    result = member_service.login_member(data)

    if result["success"]:
        access_token = result.get("access_token")
        # ✅ httpOnly 쿠키로 토큰 발급
        response = make_response(jsonify(result), 200)
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=os.getenv("FLASK_ENV") == "production"
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,
            domain='mbc-sw.iptime.org'  # ✅ 도메인 추가
        )
        return response

    return jsonify(result), 401

@member_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    # ✅ 쿠키 삭제
    response = make_response(jsonify({"success": True, "message": "로그아웃되었습니다."}), 200)
    response.delete_cookie('access_token')
    return response

# 나머지 라우트는 기존 그대로
@member_bp.route('/<int:member_id>', methods=['GET'])
def get_profile(member_id):
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
        return jsonify({"success": False, "message": "수정할 정보를 입력해주세요."}), 400
    result = member_service.update_member_info(request.user_id, data)
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 400

@member_bp.route("/find-id", methods=["POST"])
def find_id():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "이메일을 입력해주세요."}), 400
    service = MemberService()
    result = service.find_login_id(data)
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 404

@member_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    if not data or not data.get("email"):
        return jsonify({"success": False, "message": "이메일을 입력해주세요."}), 400
    result = member_service.request_password_reset(data)
    return jsonify(result), 200

@member_bp.route("/reset-password", methods=["POST"])
def reset_password():
    token = request.args.get("token")
    if not token:
        return jsonify({"success": False, "message": "유효하지 않은 접근입니다."}), 400
    data = request.get_json()
    if not data or not data.get("new_password"):
        return jsonify({"success": False, "message": "새 비밀번호를 입력해주세요."}), 400
    result = member_service.reset_password(token, data["new_password"])
    if result["success"]:
        return jsonify(result), 200
    return jsonify(result), 400

@member_bp.route("/me/password", methods=["PUT"])
@login_required
def change_my_password():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "비밀번호 정보를 입력해주세요."}), 400
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