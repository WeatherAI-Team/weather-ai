"""
board_models.py
위치: backend-main/app/models/board_models.py

boards 테이블에 parent_id 컬럼이 없으므로 board_comments에 parent_id를 추가해
대댓글(1-depth)을 구현합니다.
Supabase에서 아래 마이그레이션을 한 번 실행하세요:
  ALTER TABLE board_comments ADD COLUMN IF NOT EXISTS parent_id BIGINT
    REFERENCES board_comments(id) ON DELETE CASCADE;
"""

from app import db
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def kst_now():
    return datetime.now(KST).replace(tzinfo=None)

class Board(db.Model):
    __tablename__ = "boards"

    id         = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    member_id  = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    title      = db.Column(db.String(200), nullable=False)
    content    = db.Column(db.Text, nullable=False)
    board_type = db.Column(db.String(50), nullable=False, default="FREE")
    bug_status = db.Column(db.String(20), nullable=False, default="pending")
    
    # FREE  → 건의게시판 (일반 사용자)
    # INFO  → 정보게시판 (관리자 작성)
    # BUG      → 버그게시판
    # RESOURCE → 자료게시판
    # NOTICE→ 공지 (pinned=True 와 함께 사용)
    
    view_count = db.Column(db.Integer, nullable=False, default=0)
    pinned     = db.Column(db.Boolean, nullable=False, default=False)
    active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=kst_now)
    updated_at = db.Column(db.DateTime, default=kst_now, onupdate=kst_now)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # relationships
    member   = db.relationship("Member", backref="boards", lazy="joined")
    comments = db.relationship(
        "BoardComment",
        backref="board",
        lazy="dynamic",
        foreign_keys="BoardComment.board_id",
    )


class BoardComment(db.Model):
    __tablename__ = "board_comments"

    id        = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    board_id  = db.Column(db.BigInteger, db.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("members.id", ondelete="CASCADE"), nullable=False)
    content   = db.Column(db.Text, nullable=False)
    # 대댓글 지원: 최상위 댓글은 NULL, 대댓글은 부모 댓글 ID
    parent_id = db.Column(db.BigInteger, db.ForeignKey("board_comments.id", ondelete="CASCADE"), nullable=True)
    active     = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    # relationships
    member  = db.relationship("Member", backref="comments", lazy="joined")
    replies = db.relationship(
        "BoardComment",
        backref=db.backref("parent", remote_side="BoardComment.id"),
        lazy="dynamic",
        foreign_keys=[parent_id],
    )

class BoardAttachment(db.Model):
    __tablename__ = "board_attachments"

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    board_id = db.Column(db.BigInteger, db.ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)

    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.Text, nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    file_size = db.Column(db.BigInteger, nullable=True)

    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)

    board = db.relationship("Board", backref=db.backref("attachments", lazy="dynamic"))