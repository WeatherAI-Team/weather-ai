import os
import requests
from flask import Blueprint, redirect, request, jsonify, make_response
from urllib.parse import urlencode
from dotenv import load_dotenv
from app.services.social_auth_service import SocialAuthService

load_dotenv()

kakao_auth_bp = Blueprint("kakao_auth", __name__, url_prefix="/api/auth/kakao")

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

social_auth_service = SocialAuthService()


@kakao_auth_bp.route("/login")
def kakao_login():
    kakao_auth_url = (
        "https://kauth.kakao.com/oauth/authorize"
        f"?client_id={KAKAO_REST_API_KEY}"
        f"&redirect_uri={KAKAO_REDIRECT_URI}"
        "&response_type=code"
    )
    return redirect(kakao_auth_url)


@kakao_auth_bp.route("/callback")
def kakao_callback():
    if request.args.get("error"):
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_cancelled")

    code = request.args.get("code")
    if not code:
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_cancelled")

    token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    if KAKAO_CLIENT_SECRET:
        data["client_secret"] = KAKAO_CLIENT_SECRET

    token_response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        data=data,
    )
    token_json = token_response.json()

    if "access_token" not in token_json:
        return jsonify({"error": "카카오 토큰 발급 실패", "detail": token_json}), 400

    kakao_access_token = token_json["access_token"]

    user_response = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={
            "Authorization": f"Bearer {kakao_access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
    )
    if user_response.status_code != 200:
        return jsonify({"error": "카카오 사용자 정보 조회 실패"}), 400

    kakao_user = user_response.json()
    kakao_id = str(kakao_user.get("id"))
    kakao_account = kakao_user.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    email = kakao_account.get("email")
    nickname = profile.get("nickname") or "카카오회원"
    profile_img_url = profile.get("profile_image_url") or profile.get("thumbnail_image_url")

    if not kakao_id or kakao_id == "None":
        return jsonify({"error": "카카오 고유 ID가 없습니다."}), 400

    if not email:
        query = urlencode({"error": "kakao_email_missing", "message": "카카오 이메일 제공 동의가 필요합니다."})
        return redirect(f"{FRONTEND_URL}/auth/callback?{query}")

    result, status_code = social_auth_service.login_or_register(
        provider="kakao",
        social_id=str(kakao_id),
        email=email,
        nickname=nickname,
        profile_img_url=profile_img_url,
    )

    if status_code in (200, 201):
        access_token = result.get("access_token")
        # ✅ httpOnly 쿠키로 토큰 발급 (URL 노출 제거)
        response = make_response(redirect(f"{FRONTEND_URL}/auth/callback?provider=kakao"))
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