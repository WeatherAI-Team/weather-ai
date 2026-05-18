from flask import Blueprint, request, jsonify
from ..services.member_service import MemberService
from functools import wraps
from jose import jwt
import os

# 블루프린트 설정 (url_prefix가 있으니 /api/member/google 로 접속됨)
member_bp = Blueprint('member', __name__, url_prefix='/api/member')
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")

member_service = MemberService()

# [보안] 토큰 확인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"success": False, "message": "토큰이 없습니다."}), 401
        try:
            auth_token = token.split(" ")[1] if " " in token else token
            payload = jwt.decode(auth_token, SECRET_KEY, algorithms=["HS256"])
            request.user_id = payload.get("sub")
        except:
            return jsonify({"success": False, "message": "유효하지 않은 토큰입니다."}), 401
        return f(*args, **kwargs)
    return decorated

@member_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "회원가입 정보를 입력해주세요."
        }), 400
    
    print(f"DEBUG: 프론트에서 온 데이터 -> {data}")  # <--- 이 줄만 추가!
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