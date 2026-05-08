from datetime import datetime
from ..models import db
from ..models.member import Member

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