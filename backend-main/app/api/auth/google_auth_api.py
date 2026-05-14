import os
import requests
from flask import Blueprint, redirect, request, jsonify
from app.services.auth_utils import create_access_token
from dotenv import load_dotenv
from datetime import datetime

from app.models import db
from app.models.member import Member
from app.repositories.member_repo import MemberRepository

load_dotenv()

google_auth_bp = Blueprint("google_auth", __name__, url_prefix="/api/auth/google")

# .env 파일에 아래 설정들이 들어있어야 합니다.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@google_auth_bp.route("/login")
def google_login():
    """사용자를 구글 로그인 페이지로 리다이렉트"""
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
    )
    return redirect(google_auth_url)

@google_auth_bp.route("/callback")
def google_callback():
    """구글 인증 후 콜백 처리"""
    code = request.args.get("code")

    if not code:
        return jsonify({"error": "인가 코드가 없습니다."}), 400

    # 1. 인가 코드로 access_token 받기
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    token_response = requests.post(token_url, data=data)
    token_json = token_response.json()

    if "access_token" not in token_json:
        return jsonify(token_json), 400

    access_token = token_json["access_token"]

    # 2. access_token으로 구글 사용자 정보 가져오기
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    user_response = requests.get(
        user_info_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    google_user = user_response.json()

    # 구글 유저 데이터 추출 (카카오와 대응되는 필드)
    google_id = google_user.get("sub")  # 구글의 고유 식별자
    email = google_user.get("email")
    nickname = google_user.get("name") or "구글회원"
    profile_img_url = google_user.get("picture")

    if not google_id:
        return jsonify({"error": "구글 고유 ID가 없습니다."}), 400

    if not email:
        return jsonify({"error": "구글 이메일 정보가 없습니다."}), 400

    repo = MemberRepository()

    try:
        # 1. provider + social_id로 기존 구글 회원 조회
        member = repo.find_by_provider_and_social_id("google", google_id)

        # 2. 기존 회원이 없으면 신규 가입
        if member is None:
            same_email_member = repo.find_by_email(email)

            if same_email_member is not None:
                return jsonify({
                    "error": "이미 다른 소셜 계정으로 가입된 이메일입니다.",
                    "email": email,
                    "provider": same_email_member.provider
                }), 409

            member = Member(
                login_id=f"google_{google_id}"[:50],
                password=None,
                email=email,
                nickname=nickname,
                profile_img_url=profile_img_url,
                role="user",
                active=True,
                provider="google",
                social_id=str(google_id),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_login_at=datetime.now(),
                deleted_at=None,
            )
            repo.save(member)

        # 3. 기존 회원이면 마지막 로그인 시간 업데이트
        else:
            if member.active is False:
                return jsonify({"error": "비활성화된 계정입니다."}), 403
            
            repo.update_last_login(member)

        # 응답 데이터 구성 (카카오와 동일)
        user_data = {
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "role": str(member.role),
            "provider": member.provider,
            "social_id": member.social_id,
        }

        # Flask-JWT-Extended 토큰 생성
        access_token_jwt = create_access_token({"sub": str(member.id)})

        return jsonify({
            "success": True,
            "message": "구글 로그인 성공",
            "access_token": access_token_jwt,
            "user": user_data
        })

    except Exception as e:
        db.session.rollback()
        print("[GOOGLE LOGIN DB ERROR]", e)
        return jsonify({
            "error": "구글 로그인 DB 처리 실패",
            "detail": str(e)
        }), 500