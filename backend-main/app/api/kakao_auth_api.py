import os
import requests
from flask import Blueprint, redirect, request, session, jsonify
from dotenv import load_dotenv

load_dotenv()

kakao_auth_bp = Blueprint("kakao_auth", __name__, url_prefix="/api/auth/kakao")

KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_CLIENT_SECRET = os.getenv("KAKAO_CLIENT_SECRET")
KAKAO_REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


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
    code = request.args.get("code")

    if not code:
        return jsonify({"error": "인가 코드가 없습니다."}), 400

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
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
        },
        data=data,
    )

    token_json = token_response.json()

    if "access_token" not in token_json:
        return jsonify(token_json), 400

    access_token = token_json["access_token"]

    user_response = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
    )

    kakao_user = user_response.json()

    kakao_id = str(kakao_user.get("id"))
    kakao_account = kakao_user.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    email = kakao_account.get("email")
    nickname = profile.get("nickname")

    # 여기서 DB 회원 확인/가입 처리하면 됨
    # 예: kakao_id로 회원 조회 → 없으면 insert → 있으면 로그인 처리

    session["user"] = {
        "provider": "kakao",
        "kakao_id": kakao_id,
        "email": email,
        "nickname": nickname,
    }
# 로그인 성공 확인용
    return jsonify({
        "message": "카카오 로그인 성공",
        "user": session["user"]
    })