from datetime import datetime
from ..models import db
from ..models.member import Member
from datetime import datetime


class MemberRepository:
    # 1. 새로운 멤버 저장
    def save(self, member):
        db.session.add(member)
        db.session.commit()
        return member

    # 2. login_id로 멤버 찾기 (중복 체크용)
    def find_by_login_id(self, login_id):
        return Member.query.filter(
            Member.login_id == login_id,
            Member.deleted_at.is_(None)
        ).first()

    # 3. 고유 번호(ID)로 멤버 찾기 (조회용)
    def find_by_id(self, member_id):
        return Member.query.filter(
            Member.id == member_id,
            Member.deleted_at.is_(None)
        ).first()
    

    # 4. 소셜 로그인 회원 찾기
    def find_by_provider_and_social_id(self, provider, social_id):
        return Member.query.filter(
            Member.provider == provider,
            Member.social_id == str(social_id),
            Member.deleted_at.is_(None)
        ).first()

    # 5. 이메일로 회원 찾기
    def find_by_email(self, email):
        return Member.query.filter(
            Member.email == email,
            Member.deleted_at.is_(None)
        ).first()

    # 6. 마지막 로그인 시간 업데이트
    def update_last_login(self, member):
        member.last_login_at = datetime.now()
        member.updated_at = datetime.now()
        db.session.commit()
        return member
    
    # 7. 비밀번호 재설정 업데이트
    def update_password_reset_token(self, member, token, expires_at):
        member.password_reset_token = token
        member.password_reset_token_expires_at = expires_at
        member.updated_at = datetime.now()

        db.session.commit()
        return member

    def find_by_password_reset_token(self, token):
        return Member.query.filter_by(
            password_reset_token=token
        ).first()

    def update_password_after_reset(self, member, hashed_password):
        now = datetime.now()

        member.password = hashed_password

        # 재설정 토큰 사용 완료 → 제거
        member.password_reset_token = None
        member.password_reset_token_expires_at = None

        # 비밀번호 변경 시각 기록
        member.password_changed_at = now

        # 회원 정보 수정 시각도 갱신
        member.updated_at = datetime.utcnow()

        db.session.commit()
        return member
    
    # 8. 회원정보 수정
    def update_member_info(self, member, email, nickname, profile_img_url):
        member.email = email
        member.nickname = nickname
        member.real_name = real_name
        member.profile_img_url = profile_img_url
        member.updated_at = datetime.now()

        db.session.commit()
        return member
    
    # 9. 로그인한 회원 비밀번호 변경
    def update_password(self, member, hashed_password):
        member.password = hashed_password
        member.updated_at = datetime.now()

        db.session.commit()
        return member