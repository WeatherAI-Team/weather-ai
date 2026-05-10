from flask import Blueprint, request, jsonify
from ..services.member_service import MemberService
from functools import wraps
from jose import jwt
import os

# 블루프린트 설정 (url_prefix가 있으니 /api/member/google 로 접속됨)
member_bp = Blueprint('member', __name__, url_prefix='/api/member')
SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")

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

# 1. 일반 회원가입
@member_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    service = MemberService()
    result = service.register_member(data)
    return jsonify(result)

# 2. 일반 로그인
@member_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    service = MemberService()
    result = service.login_member(data)
    return jsonify(result)

# 3. 구글 소셜 로그인 (이게 있어야 flask routes에 뜸)
@member_bp.route('/google', methods=['POST'])
def google_login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "데이터가 없습니다."}), 400
    
    service = MemberService()
    result = service.social_login_or_register(data)
    return jsonify(result)

# 4. 내 프로필 조회
@member_bp.route('/me', methods=['GET'])
@login_required
def get_my_profile():
    service = MemberService()
    result = service.get_member_info(request.user_id)
    return jsonify(result)