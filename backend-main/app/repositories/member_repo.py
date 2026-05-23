from datetime import datetime 

from app import db
from sqlalchemy import or_ 
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
    
    # 4. 관리자용 회원 목록 조회
    # 관리자용 사용자 목록 조회 함수
    # 쉽게 말하면 DB에서 회원들을 여러 명 가져오는 기능이야.
    def find_all(self, page=1, per_page=10, keyword=None, role=None, active=None):
        # Member 테이블에서 삭제되지 않은 회원만 찾기 시작해.
        # deleted_at이 None이라는 뜻은 아직 삭제되지 않았다는 뜻이야.
        query = Member.query.filter(Member.deleted_at.is_(None))
        # keyword가 있으면 아이디, 이메일, 닉네임 중에서 검색해.
        # 예를 들어 keyword가 "정화"면 닉네임에 정화가 들어간 회원을 찾을 수 있어.
        if keyword:
            search = f"%{keyword}%"
            query = query.filter(
                or_(
                    Member.login_id.ilike(search),    # login_id에 keyword가 들어가는지 확인
                    Member.email.ilike(search),       # email에 keyword가 들어가는지 확인   
                    Member.nickname.ilike(search)     # nickname에 keyword가 들어가는지 확인
                )
            )
        # role 값이 있으면 해당 권한의 회원만 찾음.
        # 예: role=user 이면 일반 사용자만 조회
        # 예: role=admin 이면 관리자만 조회
        if role:
            query = query.filter(Member.role == role)
        # active 값이 있으면 활성/비활성 회원만 찾음.
        # active=True면 사용 중인 회원
        # active=False면 정지되었거나 비활성화된 회원
        if active is not None:
            query = query.filter(Member.active == active)
        # created_at 기준으로 최신 가입자부터 정렬해.
        # paginate는 페이지를 나눠서 가져오는 기능이야.
        # 예: 1페이지에 10명씩 보여주기
        return query.order_by(Member.created_at.desc()).paginate(
            page=page,                      # 몇 번째 페이지인지
            per_page=per_page,              # 한 페이지에 몇 명 보여줄지   
            error_out=False                 # 페이지가 없어도 에러 대신 빈 결과를 주게 함  
        )
        # 나중에 관리자 페이지에서 사용자 목록을 검색
        

    # 5. 이메일로 회원 찾기
    def find_by_email(self, email):
        return Member.query.filter(
            Member.email == email,
            Member.deleted_at.is_(None)
        ).first()

    # 6. 마지막 로그인 시간 업데이트
    # 사용자가 로그인했을 때 마지막 로그인 시간을 현재 시간으로 바꿔줘
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
    def update_member_info(self, member, email, real_name, nickname, profile_img_url):
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
    
     # 10. 회원 탈퇴 처리 - 실제 삭제 없이 비활성화
    def deactivate_member(self, member):
        member.active=False
        member.updated_at = datetime.now()

        db.session.commit()
        return member
