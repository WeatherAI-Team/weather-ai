from datetime import datetime

from app.models import db
from app.models.member_social_account import MemberSocialAccount


class SocialAccountRepository:
    def find_by_provider_and_social_id(self, provider, social_id):
        return MemberSocialAccount.query.filter(
            MemberSocialAccount.provider == provider,
            MemberSocialAccount.social_id == str(social_id)
        ).first()

    def find_by_member_and_provider(self, member_id, provider):
        return MemberSocialAccount.query.filter(
            MemberSocialAccount.member_id == member_id,
            MemberSocialAccount.provider == provider
        ).first()
    
    # member_id로 연결된 소셜 계정 목록 조회
    def find_all_by_member_id(self, member_id):
        return MemberSocialAccount.query.filter(
            MemberSocialAccount.member_id == member_id
        ).all()

    def save(self, social_account):
        db.session.add(social_account)
        db.session.commit()
        return social_account

    def update_login_info(self, social_account, email=None):
        social_account.email = email or social_account.email
        social_account.updated_at = datetime.now()
        db.session.commit()
        return social_account