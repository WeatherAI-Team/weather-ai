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

    print("[KAKAO TOKEN STATUS]", token_response.status_code)
    print("[KAKAO TOKEN BODY]", token_response.text)

    token_json = token_response.json()

    if "access_token" not in token_json:
        return jsonify({
            "error": "카카오 토큰 발급 실패",
            "detail": token_json
        }), 400

    access_token = token_json["access_token"]
    print("[ACCESS TOKEN]", access_token)

    user_response = requests.get(
        "https://kapi.kakao.com/v2/user/me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
        },
    )

    print("[KAKAO USER STATUS]", user_response.status_code)
    print("[KAKAO USER BODY]", user_response.text)

    if user_response.status_code != 200:
        return jsonify({
            "error": "카카오 사용자 정보 조회 실패",
            "detail": user_response.json()
        }), 400

    kakao_user = user_response.json()

    kakao_id = str(kakao_user.get("id"))

    kakao_account = kakao_user.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    email = kakao_account.get("email")
    nickname = profile.get("nickname") or "카카오회원"
    profile_img_url = (
        profile.get("profile_image_url")
        or profile.get("thumbnail_image_url")
    )

    if not kakao_id or kakao_id == "None":
        return jsonify({"error": "카카오 고유 ID가 없습니다."}), 400

    if not email:
        return jsonify({
            "error": "카카오 이메일이 없습니다.",
            "message": "카카오 개발자센터에서 이메일 제공 항목을 필수로 설정했는지 확인하세요."
        }), 400

    repo = MemberRepository()

    try:
        # 1. provider + social_id로 기존 카카오 회원 조회
        member = repo.find_by_provider_and_social_id("kakao", kakao_id)

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
                login_id=f"kakao_{kakao_id}"[:50],
                password=None,
                email=email,
                nickname=nickname,
                profile_img_url=profile_img_url,
                role="user",
                active=True,
                provider="kakao",
                social_id=str(kakao_id),
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

        
        user_data = {
            "id": member.id,
            "login_id": member.login_id,
            "email": member.email,
            "nickname": member.nickname,
            "role": str(member.role),
            "provider": member.provider,
            "social_id": member.social_id,
        }

        access_token = create_access_token({"sub": str(member.id)})

        return jsonify({
            "success": True,
            "message": "카카오 로그인 성공",
            "access_token": access_token,
            "user": user_data
})

    except Exception as e:
        db.session.rollback()
        print("[KAKAO LOGIN DB ERROR]", e)

        return jsonify({
            "error": "카카오 로그인 DB 처리 실패",
            "detail": str(e)
        }), 500