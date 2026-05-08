import os
import secrets
import requests
from flask import Blueprint, redirect, request, session, jsonify
from dotenv import load_dotenv
from urllib.parse import urlencode
from datetime import datetime

from app.models import db
from app.models.member import Member
from app.repositories.member_repo import MemberRepository

load_dotenv()

naver_auth_bp = Blueprint("naver_auth", __name__, url_prefix="/api/auth/naver")

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_REDIRECT_URI = os.getenv("NAVER_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


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
        return jsonify({
            "error": "네이버 로그인 실패",
            "detail": error
        }), 400

    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return jsonify({"error": "인가 코드가 없습니다."}), 400

    if not state:
        return jsonify({"error": "state 값이 없습니다."}), 400

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
        "https://openapi.naver.com/v1/nid/me",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
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

    repo = MemberRepository()

    try:
        # 1. provider + social_id로 기존 네이버 회원 조회
        member = repo.find_by_provider_and_social_id("naver", naver_id)

        # 2. 기존 회원이 없으면 신규 가입
        if member is None:
            same_email_member = repo.find_by_email(email)

            if same_email_member is not None:
                return jsonify({
                    "error": "이미 같은 이메일로 가입된 회원이 있습니다.",
                    "email": email,
                    "provider": same_email_member.provider
                }), 409

            member = Member(
                login_id=f"naver_{naver_id}"[:50],
                password=None,
                email=email,
                nickname=name,
                profile_img_url=None,
                role="user",
                active=True,
                provider="naver",
                social_id=str(naver_id),
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

        # 4. 세션 저장
        session["user"] = {
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "role": str(member.role),
            "provider": member.provider,
            "social_id": member.social_id,
        }

        return jsonify({
            "message": "네이버 로그인 성공",
            "user": session["user"]
        })

    except Exception as e:
        db.session.rollback()
        print("[NAVER LOGIN DB ERROR]", e)

        return jsonify({
            "error": "네이버 로그인 DB 처리 실패",
            "detail": str(e)
        }), 500