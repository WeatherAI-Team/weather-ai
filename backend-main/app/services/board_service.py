"""
board_service.py  –  Service 레이어 (비즈니스 로직)
위치: backend-main/app/services/board_service.py
"""

from app.repositories import board_repo
from app.models.board import Board, BoardComment


# ──────────────────────────────────────────────────────────────
# 직렬화 헬퍼
# ──────────────────────────────────────────────────────────────

def _serialize_post(post: Board) -> dict:
    return {
        "id":              post.id,
        "member_id":       post.member_id,
        "author_nickname": post.member.nickname if post.member else "탈퇴한 회원",
        "title":           post.title,
        "content":         post.content,
        "board_type":      post.board_type,
        "view_count":      post.view_count,
        "comment_count":   post.comments.filter_by(active=True).count(),
        "pinned":          post.pinned,
        "active":          post.active,
        "created_at":      post.created_at.strftime("%Y-%m-%d") if post.created_at else None,
        "updated_at":      post.updated_at.strftime("%Y-%m-%d %H:%M:%S") if post.updated_at else None,
    }


def _serialize_comment(comment: BoardComment) -> dict:
    return {
        "id":              comment.id,
        "board_id":        comment.board_id,
        "member_id":       comment.member_id,
        "author_nickname": comment.member.nickname if comment.member else "탈퇴한 회원",
        "content":         comment.content,
        "parent_id":       comment.parent_id,
        "active":          comment.active,
        "created_at":      comment.created_at.strftime("%Y-%m-%d") if comment.created_at else None,
    }


# ──────────────────────────────────────────────────────────────
# 권한 체크 (user 객체 대신 user_id/user_role 사용)
# ──────────────────────────────────────────────────────────────

def _is_privileged(user_role: str) -> bool:
    return user_role in ("admin", "manager")


# ──────────────────────────────────────────────────────────────
# 게시글 서비스
# ──────────────────────────────────────────────────────────────

_BOARD_TYPE_MAP = {
    "suggest": ["FREE"],
    "info":    ["INFO", "NOTICE"],
}


def get_post_list(board_type_param: str, search: str, page: int, per_page: int) -> dict:
    board_types  = _BOARD_TYPE_MAP.get(board_type_param, ["FREE"])
    posts, total = board_repo.get_posts(board_types, search, page, per_page)
    return {
        "posts":       [_serialize_post(p) for p in posts],
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


def get_post_detail(post_id: int) -> tuple[dict | None, str]:
    post = board_repo.get_post_by_id(post_id)
    if not post:
        return None, "게시글을 찾을 수 없습니다."

    board_repo.increment_view_count(post)

    parent_comments = board_repo.get_comments_by_post(post_id)
    comments_data   = []
    for c in parent_comments:
        c_dict            = _serialize_comment(c)
        replies           = board_repo.get_replies_by_comment(post_id, c.id)
        c_dict["replies"] = [_serialize_comment(r) for r in replies]
        comments_data.append(c_dict)

    data             = _serialize_post(post)
    data["comments"] = comments_data
    return data, ""


def create_post(member_id: str, title: str, content: str, board_type: str, pinned: bool, user_role: str) -> tuple[dict | None, str, int]:
    if not title.strip() or not content.strip():
        return None, "제목과 내용을 입력해주세요.", 400

    if board_type in ("INFO", "NOTICE") and not _is_privileged(user_role):
        return None, "정보/공지 게시글은 관리자만 작성할 수 있습니다.", 403

    post = board_repo.create_post(member_id, title, content, board_type, pinned)
    return _serialize_post(post), "", 201


def update_post(post_id: int, update_data: dict, user_id: str, user_role: str) -> tuple[dict | None, str, int]:
    post = board_repo.get_post_by_id(post_id)
    if not post:
        return None, "게시글을 찾을 수 없습니다.", 404

    # member_id는 int, user_id는 JWT sub(str) 이므로 타입 맞춰 비교
    is_author     = str(post.member_id) == str(user_id)
    is_privileged = _is_privileged(user_role)

    if not is_author and not is_privileged:
        return None, "수정 권한이 없습니다.", 403

    allowed_fields = {"title", "content"}
    if is_privileged:
        allowed_fields |= {"pinned", "active", "board_type"}

    fields_to_update = {k: v for k, v in update_data.items() if k in allowed_fields}
    updated_post     = board_repo.update_post(post, fields_to_update)
    return _serialize_post(updated_post), "", 200


def delete_post(post_id: int, user_id: str, user_role: str) -> tuple[str, int]:
    post = board_repo.get_post_by_id(post_id)
    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    is_author = str(post.member_id) == str(user_id)
    if not is_author and not _is_privileged(user_role):
        return "삭제 권한이 없습니다.", 403

    board_repo.soft_delete_post(post)
    return "", 200


# ──────────────────────────────────────────────────────────────
# 관리자 전용 서비스
# ──────────────────────────────────────────────────────────────

def admin_get_post_list(board_type: str, search: str, page: int, per_page: int) -> dict:
    board_types = [bt.strip() for bt in board_type.split(",")] if board_type else []
    posts, total = board_repo.get_posts_admin(board_types, search, page, per_page)
    return {
        "posts":    [_serialize_post(p) for p in posts],
        "total":    total,
        "page":     page,
        "per_page": per_page,
    }


def admin_toggle_pinned(post_id: int) -> tuple[dict | None, str]:
    post = board_repo.get_post_by_id_admin(post_id)
    if not post:
        return None, "게시글을 찾을 수 없습니다."
    updated = board_repo.toggle_post_field(post, "pinned")
    return {"pinned": updated.pinned}, ""


def admin_toggle_active(post_id: int) -> tuple[dict | None, str]:
    post = board_repo.get_post_by_id_admin(post_id)
    if not post:
        return None, "게시글을 찾을 수 없습니다."
    updated = board_repo.toggle_post_field(post, "active")
    return {"active": updated.active}, ""


# ──────────────────────────────────────────────────────────────
# 댓글 서비스
# ──────────────────────────────────────────────────────────────

def create_comment(post_id: int, member_id: str, content: str, parent_id: int | None) -> tuple[dict | None, str, int]:
    post = board_repo.get_post_by_id(post_id)
    if not post:
        return None, "게시글을 찾을 수 없습니다.", 404

    if not content.strip():
        return None, "댓글 내용을 입력해주세요.", 400

    comment = board_repo.create_comment(post_id, member_id, content, parent_id)
    return _serialize_comment(comment), "", 201


def delete_comment(comment_id: int, user_id: str, user_role: str) -> tuple[str, int]:
    comment = board_repo.get_comment_by_id(comment_id)
    if not comment:
        return "댓글을 찾을 수 없습니다.", 404

    is_author = str(comment.member_id) == str(user_id)
    if not is_author and not _is_privileged(user_role):
        return "삭제 권한이 없습니다.", 403

    board_repo.soft_delete_comment(comment)
    return "", 200