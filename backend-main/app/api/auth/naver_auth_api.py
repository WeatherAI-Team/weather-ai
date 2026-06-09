import os
import secrets
import requests
from flask import Blueprint, redirect, request, jsonify, session, make_response
from dotenv import load_dotenv
from urllib.parse import urlencode
from app.services.social_auth_service import SocialAuthService

load_dotenv()

naver_auth_bp = Blueprint("naver_auth", __name__, url_prefix="/api/auth/naver")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

social_auth_service = SocialAuthService()


@naver_auth_bp.route("/login")
def naver_login():
    state = secrets.token_urlsafe(16)
    session["naver_oauth_state"] = state

    params = {
        "response_type": "code",
        "client_id": NAVER_CLIENT_ID,
        "redirect_uri": NAVER_REDIRECT_URI,
        "state": state,
    }
    naver_auth_url = "https://nid.naver.com/oauth2.0/authorize?" + urlencode(params)
    return redirect(naver_auth_url)


@naver_auth_bp.route("/callback")
def naver_callback():
    error = request.args.get("error")
    if error:
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_cancelled")

    code = request.args.get("code")
    state = request.args.get("state")

    if not code or not state:
        return redirect(f"{FRONTEND_URL}/auth/callback?error=login_cancelled")

    saved_state = session.pop("naver_oauth_state", None)
    if state != saved_state:
        return jsonify({"error": "state 값이 일치하지 않습니다."}), 400

    token_url = "https://nid.naver.com/oauth2.0/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": NAVER_CLIENT_ID,
        "client_secret": NAVER_CLIENT_SECRET,
        "redirect_uri": NAVER_REDIRECT_URI,
        "code": code,
        "state": state,
    }
    token_response = requests.post(
        token_url,
        headers={"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"},
        data=data,
    )
    token_json = token_response.json()

    if "access_token" not in token_json:
        return jsonify(token_json), 400

    access_token = token_json["access_token"]

    user_response = requests.get(
        "https://openapi.naver.com/v1/nid/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    naver_result = user_response.json()

    if naver_result.get("resultcode") != "00":
        return jsonify(naver_result), 400

    naver_user = naver_result.get("response", {})
    naver_id = naver_user.get("id")
    email = naver_user.get("email")
    name = naver_user.get("name") or "네이버회원"

    if not naver_id:
        return jsonify({"error": "네이버 고유 ID가 없습니다."}), 400
    if not email:
        return jsonify({"error": "이메일이 없습니다."}), 400

    result, status_code = social_auth_service.login_or_register(
        provider="naver",
        social_id=str(naver_id),
        email=email,
        nickname=name,
        profile_img_url=None,
    )

    if status_code in (200, 201):
        access_token = result.get("access_token")
        # ✅ httpOnly 쿠키로 토큰 발급
        response = make_response(redirect(f"{FRONTEND_URL}/auth/callback?provider=naver"))
        response.set_cookie(
            'access_token',
            access_token,
            httponly=True,
            secure=os.getenv("FLASK_ENV") == "production",
            samesite='Lax',
            max_age=60 * 60 * 24 * 7,
            domain='mbc-sw.iptime.org'  # ✅ 도메인 추가
        )
        return response

    return redirect(f"{FRONTEND_URL}/auth/callback?error=login_failed")