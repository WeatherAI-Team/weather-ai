from datetime import datetime

from app.models import db
from app.models.member import Member
from app.models.member_social_account import MemberSocialAccount
from app.repositories.member_repo import MemberRepository
from app.repositories.social_account_repo import SocialAccountRepository
from app.services.auth_utils import create_access_token


class SocialAuthService:
    def __init__(self):
        # members 테이블 접근용 repository
        self.member_repo = MemberRepository()

        # member_social_accounts 테이블 접근용 repository
        self.social_account_repo = SocialAccountRepository()

    def login_or_register(
        self,
        provider,
        social_id,
        email,
        nickname,
        profile_img_url=None,
    ):
        try:
            # 1. 먼저 소셜 계정 테이블에서 provider + social_id로 기존 연동 계정이 있는지 조회
            # 예: provider="kakao", social_id="4896760811"
            social_account = self.social_account_repo.find_by_provider_and_social_id(
                provider,
                social_id
            )

            # 2. 이미 소셜 계정 연동 정보가 있는 경우
            if social_account:
                # social_account.member_id를 기준으로 실제 회원 정보 조회
                member = self.member_repo.find_by_id(social_account.member_id)

                # 회원이 없거나 soft delete 처리된 경우 로그인 차단
                if not member or member.deleted_at is not None:
                    return {
                        "success": False,
                        "error": "탈퇴한 계정입니다."
                    }, 403

                # active=False면 비활성화/탈퇴 처리된 계정이므로 로그인 차단
                if member.active is False:
                    return {
                        "success": False,
                        "error": "비활성화된 계정입니다."
                    }, 403

                # 정상 회원이면 마지막 로그인 시간 갱신
                self.member_repo.update_last_login(member)

                # 소셜 계정 쪽 이메일 정보도 최신 값으로 갱신
                self.social_account_repo.update_login_info(social_account, email)

            # 3. 소셜 계정 연동 정보가 없는 경우
            else:
                # 같은 이메일을 가진 members 계정이 있는지 먼저 확인
                # 일반 회원가입으로 이미 가입한 계정이면 이 회원에 소셜 계정을 연결할 수 있음
                member = self.member_repo.find_by_email(email)

                # 3-1. 같은 이메일의 기존 회원이 있는 경우
                if member:
                    # 탈퇴 계정이면 연동/로그인 차단
                    if member.deleted_at is not None:
                        return {
                            "success": False,
                            "error": "탈퇴한 계정입니다."
                        }, 403

                    # 비활성 계정이면 연동/로그인 차단
                    if member.active is False:
                        return {
                            "success": False,
                            "error": "비활성화된 계정입니다."
                        }, 403

                    # 같은 회원이 이미 같은 provider를 연동했는지 확인
                    # 예: 이미 kakao가 연동된 회원에게 또 kakao 연동 시도하는 경우 방지
                    existing_provider = self.social_account_repo.find_by_member_and_provider(
                        member.id,
                        provider
                    )

                    if existing_provider:
                        return {
                            "success": False,
                            "error": f"이미 {provider} 계정이 연동되어 있습니다."
                        }, 409

                    # 기존 members 정보는 건드리지 않고,
                    # member_social_accounts 테이블에만 새 소셜 연동 정보를 저장
                    social_account = MemberSocialAccount(
                        member_id=member.id,
                        provider=provider,
                        social_id=str(social_id),
                        email=email,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                    )

                    self.social_account_repo.save(social_account)

                    # 소셜 로그인 성공으로 보고 마지막 로그인 시간 갱신
                    self.member_repo.update_last_login(member)

                # 3-2. 같은 이메일의 회원도 없으면 완전 신규 소셜 회원 생성
                else:
                    # 소셜 가입 회원은 일반 로그인용 login_id/password가 없음
                    # members에는 기본 회원 정보만 저장
                    member = Member(
                        login_id=None,
                        password=None,
                        email=email,
                        real_name=nickname,
                        nickname=nickname,
                        profile_img_url=profile_img_url,
                        role="user",
                        active=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        last_login_at=datetime.now(),
                        deleted_at=None,
                    )

                    self.member_repo.save(member)

                    # 새로 만든 회원에 대해 소셜 연동 정보 저장
                    social_account = MemberSocialAccount(
                        member_id=member.id,
                        provider=provider,
                        social_id=str(social_id),
                        email=email,
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        deleted_at=None,
                    )

                    self.social_account_repo.save(social_account)

            # 4. 프론트에 내려줄 사용자 정보 구성
            # provider는 members 테이블이 아니라 현재 로그인한 소셜 provider를 응답에 포함
            user_data = {
                "id": member.id,
                "login_id": member.login_id,
                "display_login_id": member.login_id or (
                    member.email.split("@")[0] if member.email and "@" in member.email else "-"
                ),
                "email": member.email,
                "real_name": member.real_name,
                "nickname": member.nickname,
                "profile_img_url": member.profile_img_url,
                "role": str(member.role),
                "active": member.active,
                "provider": provider,
            }

            # 5. JWT 발급
            # sub에는 사용자 PK를 문자열로 넣음
            access_token = create_access_token({
                "sub": str(member.id)
            })

            # 6. 로그인 성공 응답 반환
            return {
                "success": True,
                "message": f"{provider} 로그인 성공",
                "access_token": access_token,
                "user": user_data
            }, 200

        except Exception as e:
            # DB 저장/조회 중 예외 발생 시 rollback
            db.session.rollback()
            print("[SOCIAL AUTH SERVICE ERROR]", e)

            return {
                "success": False,
                "error": "소셜 로그인 DB 처리 실패",
                "detail": str(e)
            }, 500