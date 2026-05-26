from datetime import datetime
from app import db


class MemberSocialAccount(db.Model):
    __tablename__ = "member_social_accounts"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    member_id = db.Column(
        db.Integer,
        db.ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False
    )

    provider = db.Column(db.String(20), nullable=False)
    social_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)