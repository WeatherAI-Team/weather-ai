from datetime import datetime

from app.models import db
from app.models.member import Member
from app.repositories.member_repo import MemberRepository
from app.services.auth_utils import create_access_token


class SocialAuthService:
    def __init__(self):
        self.member_repo = MemberRepository()

    def login_or_register(
        self,
        provider,
        social_id,
        email,
        nickname,
        profile_img_url=None,
    ):
        try:
            # 1. provider + social_id로 기존 소셜 회원 조회
            member = self.member_repo.find_by_provider_and_social_id(
                provider,
                social_id
            )

            # 2. 기존 회원이 없으면 신규 가입
            if member is None:
                same_email_member = self.member_repo.find_by_email(email)

                if same_email_member is not None:
                    return {
                        "success": False,
                        "error": "이미 같은 이메일로 가입된 회원이 있습니다.",
                        "email": email,
                        "provider": same_email_member.provider
                    }, 409

                member = Member(
                    login_id=f"{provider}_{social_id}"[:50],
                    password=None,
                    email=email,
                    nickname=nickname,
                    profile_img_url=profile_img_url,
                    role="user",
                    active=True,
                    provider=provider,
                    social_id=str(social_id),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    last_login_at=datetime.now(),
                    deleted_at=None,
                )

                self.member_repo.save(member)

            # 3. 기존 회원이면 상태 확인 + 로그인 시간 갱신
            else:
                if member.deleted_at is not None:
                    return {
                        "success": False,
                        "error": "탈퇴한 계정입니다."
                    }, 403

                if member.active is False:
                    return {
                        "success": False,
                        "error": "비활성화된 계정입니다."
                    }, 403

                self.member_repo.update_last_login(member)

            # 4. 프론트에 내려줄 사용자 정보
            user_data = {
                "id": member.id,
                "login_id": member.login_id,
                "email": member.email,
                "nickname": member.nickname,
                "role": str(member.role),
                "provider": member.provider,
                "social_id": member.social_id,
            }

            # 5. JWT 발급
            access_token = create_access_token({
                "sub": str(member.id)
            })

            return {
                "success": True,
                "message": f"{provider} 로그인 성공",
                "access_token": access_token,
                "user": user_data
            }, 200

        except Exception as e:
            db.session.rollback()
            print("[SOCIAL AUTH SERVICE ERROR]", e)

            return {
                "success": False,
                "error": "소셜 로그인 DB 처리 실패",
                "detail": str(e)
            }, 500