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
        return Member.query.filter_by(login_id=login_id).first()

    # 3. 고유 번호(ID)로 멤버 찾기
    def find_by_id(self, member_id):
        return Member.query.get(member_id)

    # 4. 이메일로 멤버 찾기 (소셜 로그인 시 필수!)
    def find_by_email(self, email):
        return Member.query.filter_by(email=email).first()