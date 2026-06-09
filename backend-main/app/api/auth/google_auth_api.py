import os
import requests
from flask import Blueprint, redirect, request, jsonify, make_response
from urllib.parse import urlencode
from dotenv import load_dotenv
from app.services.social_auth_service import SocialAuthService

load_dotenv()

google_auth_bp = Blueprint("google_auth", __name__, url_prefix="/api/auth/google")

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
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    print("[GOOGLE AUTH URL]", google_auth_url)
    return redirect(google_auth_url)


@google_auth_bp.route("/callback")
def google_callback():
    if request.args.get("error"):
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_cancelled")

    code = request.args.get("code")
    if not code:
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_cancelled")

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

    user_response = requests.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {google_access_token}"}
    )
    google_user = user_response.json()

    google_id = google_user.get("sub")
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
        # ✅ httpOnly 쿠키로 토큰 발급
        response = make_response(redirect(f"{FRONTEND_URL}/auth/callback?provider=google"))
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=False,      # ✅ HTTPS니까 True
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,
            domain='mbc-sw.iptime.org'  # ✅ 도메인 추가
        )
        return response

    return redirect(f"{FRONTEND_URL}/auth/callback?error=login_failed")