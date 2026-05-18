import os
import requests
from flask import Blueprint, redirect, request, jsonify
from urllib.parse import urlencode
from dotenv import load_dotenv
from app.services.social_auth_service import SocialAuthService


load_dotenv()

google_auth_bp = Blueprint("google_auth", __name__, url_prefix="/api/auth/google")

# .env 파일에 아래 설정들이 들어있어야 합니다.
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

social_auth_service = SocialAuthService()

@google_auth_bp.route("/login")

def google_login():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }

    google_auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )

    print("[GOOGLE AUTH URL]", google_auth_url)

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

    google_access_token = token_json["access_token"]

    # 2. access_token으로 구글 사용자 정보 가져오기
    user_info_url = "https://www.googleapis.com/oauth2/v3/userinfo"

    user_response = requests.get(
        user_info_url,
        headers={"Authorization": f"Bearer {google_access_token}"}
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

    result, status_code = social_auth_service.login_or_register(
    provider="google",
    social_id=str(google_id),
    email=email,
    nickname=nickname,
    profile_img_url=profile_img_url,
    )

    if status_code in (200, 201):
        access_token = result.get("access_token")
        return redirect(f"{FRONTEND_URL}/auth/callback?token={access_token}&provider=google")
    else:
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_failed")