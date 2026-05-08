 
from app import db
from .. models.member import Member

class MemberRepository:
    # 1. 새로운 멤버 저장
    def save(self, member):
        db.session.add(member)
        db.session.commit()
        return member

    # 2. login_id로 멤버 찾기 (중복 체크용)
    def find_by_login_id(self, login_id):
        return Member.query.filter_by(login_id=login_id).first()

    # 3. 고유 번호(ID)로 멤버 찾기 (조회용) - 이게 없어서 에러난 거야!
    def find_by_id(self, member_id):
        return Member.query.get(member_id)