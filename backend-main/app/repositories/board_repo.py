"""
board_repo.py  –  Repository 레이어 (DB 쿼리만)
위치: backend-main/app/repositories/board_repo.py

- SQLAlchemy 쿼리만 담당
- 비즈니스 로직 없음
- Service에서만 호출
"""

from sqlalchemy import or_
from app import db
from app.models.board import Board, BoardComment
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# Board
# ──────────────────────────────────────────────────────────────

def get_posts(board_types: list[str], search: str, page: int, per_page: int):
    """게시글 목록 조회 (공개용 - active=True만)"""
    q = Board.query.filter(
        Board.board_type.in_(board_types),
        Board.active == True,
        Board.deleted_at == None,
    )
    if search:
        q = q.filter(or_(
            Board.title.ilike(f"%{search}%"),
            Board.content.ilike(f"%{search}%"),
        ))
    total = q.count()
    posts = (q
             .order_by(Board.pinned.desc(), Board.created_at.desc())
             .offset((page - 1) * per_page)
             .limit(per_page)
             .all())
    return posts, total


def get_post_by_id(post_id: int) -> Board | None:
    """게시글 단건 조회 (active=True)"""
    return Board.query.filter_by(id=post_id, active=True, deleted_at=None).first()


def get_post_by_id_admin(post_id: int) -> Board | None:
    """게시글 단건 조회 (관리자용 - active 무관)"""
    return Board.query.filter_by(id=post_id, deleted_at=None).first()


def get_posts_admin(board_type: str, search: str, page: int, per_page: int):
    """게시글 목록 조회 (관리자용 - active 무관)"""
    q = Board.query.filter(Board.deleted_at == None)
    if board_type:
        q = q.filter(Board.board_type == board_type)
    if search:
        q = q.filter(or_(
            Board.title.ilike(f"%{search}%"),
            Board.content.ilike(f"%{search}%"),
        ))
    total = q.count()
    posts = (q
             .order_by(Board.created_at.desc())
             .offset((page - 1) * per_page)
             .limit(per_page)
             .all())
    return posts, total


def create_post(member_id: int, title: str, content: str, board_type: str, pinned: bool) -> Board:
    """게시글 생성"""
    now  = datetime.utcnow()
    post = Board(
        member_id  = member_id,
        title      = title,
        content    = content,
        board_type = board_type,
        pinned     = pinned,
        created_at = now,
        updated_at = now,
    )
    db.session.add(post)
    db.session.commit()
    return post


def update_post(post: Board, fields: dict) -> Board:
    """게시글 수정 (전달된 필드만 업데이트)"""
    for key, value in fields.items():
        if hasattr(post, key):
            setattr(post, key, value)
    post.updated_at = datetime.utcnow()
    db.session.commit()
    return post


def increment_view_count(post: Board) -> None:
    """조회수 +1"""
    post.view_count += 1
    db.session.commit()


def soft_delete_post(post: Board) -> None:
    """게시글 soft delete"""
    post.deleted_at = datetime.utcnow()
    post.active     = False
    db.session.commit()


def toggle_post_field(post: Board, field: str) -> Board:
    """boolean 필드 토글 (pinned / active)"""
    setattr(post, field, not getattr(post, field))
    post.updated_at = datetime.utcnow()
    db.session.commit()
    return post


# ──────────────────────────────────────────────────────────────
# BoardComment
# ──────────────────────────────────────────────────────────────

def get_comments_by_post(post_id: int) -> list[BoardComment]:
    """최상위 댓글 목록 (parent_id=None)"""
    return (BoardComment.query
            .filter_by(board_id=post_id, parent_id=None, active=True, deleted_at=None)
            .order_by(BoardComment.created_at.asc())
            .all())


def get_replies_by_comment(post_id: int, parent_id: int) -> list[BoardComment]:
    """대댓글 목록"""
    return (BoardComment.query
            .filter_by(board_id=post_id, parent_id=parent_id, active=True, deleted_at=None)
            .order_by(BoardComment.created_at.asc())
            .all())


def get_comment_by_id(comment_id: int) -> BoardComment | None:
    """댓글 단건 조회"""
    return BoardComment.query.filter_by(id=comment_id, active=True, deleted_at=None).first()


def create_comment(board_id: int, member_id: int, content: str, parent_id: int | None) -> BoardComment:
    """댓글/대댓글 생성"""
    now     = datetime.utcnow()
    comment = BoardComment(
        board_id   = board_id,
        member_id  = member_id,
        content    = content,
        parent_id  = parent_id,
        created_at = now,
        updated_at = now,
    )
    db.session.add(comment)
    db.session.commit()
    return comment


def soft_delete_comment(comment: BoardComment) -> None:
    """댓글 soft delete"""
    comment.deleted_at = datetime.utcnow()
    comment.active     = False
    db.session.commit()