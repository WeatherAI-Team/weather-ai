"""
board_service.py  –  Service 레이어 (비즈니스 로직)
위치: backend-main/app/services/board_service.py
"""

import os
import uuid
from werkzeug.utils import secure_filename

from app.repositories import board_repo
from app.models.board import Board, BoardComment, BoardAttachment


UPLOAD_ROOT = os.path.join(os.getcwd(), "uploads", "board")

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "gif", "webp",
    "pdf", "txt", "csv", "xlsx", "docx", "pptx", "zip"
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

VALID_BOARD_TYPES = {"FREE", "INFO", "NOTICE", "BUG", "RESOURCE"}

# 자료게시판도 로그인 사용자 작성 허용이면 INFO/NOTICE만 제한
PRIVILEGED_WRITABLE_TYPES = {"INFO", "NOTICE"}

VALID_BUG_STATUS = {"pending", "in_progress", "done"}


def _to_front_board_type(board_type: str) -> str:
    if board_type == "RESOURCE":
        return "DATA"
    return board_type

# ──────────────────────────────────────────────────────────────
# 직렬화 헬퍼
# ──────────────────────────────────────────────────────────────

def _serialize_post(post: Board) -> dict:
    attachment_count = 0

    if hasattr(post, "attachments"):
        attachment_count = post.attachments.filter_by(active=True, deleted_at=None).count()

    return {
        "id":              post.id,
        "member_id":       post.member_id,
        "author_nickname": post.member.nickname if post.member else "탈퇴한 회원",
        "title":           post.title,
        "content":         post.content,
        "board_type":      _to_front_board_type(post.board_type),
        "view_count":      post.view_count,
        "views":           post.view_count,
        "status":          getattr(post, "bug_status", "pending"),
        "comment_count":   post.comments.filter_by(active=True).count(),
        "attachment_count": attachment_count,
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
    "suggest":  ["FREE"],
    "free":     ["FREE"],
    "info":     ["INFO", "NOTICE"],
    "notice":   ["NOTICE"],
    "bug":      ["BUG"],
    "resource": ["DATA", "RESOURCE"],
    "data":     ["DATA", "RESOURCE"],
}

def get_post_list(board_type_param: str, search: str, page: int, per_page: int) -> dict:
    board_type_key = (board_type_param or "suggest").lower()
    board_types  = _BOARD_TYPE_MAP.get(board_type_key, ["FREE"])
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

    parent_comments = board_repo.get_comments_by_post(post_id)
    comments_data   = []
    for c in parent_comments:
        c_dict            = _serialize_comment(c)
        replies           = board_repo.get_replies_by_comment(post_id, c.id)
        c_dict["replies"] = [_serialize_comment(r) for r in replies]
        comments_data.append(c_dict)
        
    data             = _serialize_post(post)

    attachments = board_repo.get_attachments_by_post(post_id)
    data["attachments"] = [_serialize_attachment(f) for f in attachments]
   
    data["comments"] = comments_data
    return data, ""


def increment_post_view(post_id: int) -> tuple[bool, str]:
    post = board_repo.get_post_by_id(post_id)
    if not post:
        return False, "게시글을 찾을 수 없습니다."
    board_repo.increment_view_count(post)
    return True, ""


def create_post(member_id: str, title: str, content: str, board_type: str, pinned: bool, user_role: str) -> tuple[dict | None, str, int]:
    title = title.strip()
    content = content.strip()
    board_type = _normalize_board_type(board_type)

    if not title or not content:
        return None, "제목과 내용을 입력해주세요.", 400

    if board_type not in VALID_BOARD_TYPES:
        return None, "유효하지 않은 게시판 유형입니다.", 400

    if board_type in PRIVILEGED_WRITABLE_TYPES and not _is_privileged(user_role):
        return None, "해당 게시판은 관리자만 작성할 수 있습니다.", 403

    if not _is_privileged(user_role):
        pinned = False

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
    if "board_type" in fields_to_update:
        fields_to_update["board_type"] = _normalize_board_type(fields_to_update["board_type"])

        if fields_to_update["board_type"] not in VALID_BOARD_TYPES:
            return None, "유효하지 않은 게시판 유형입니다.", 400
        
    updated_post     = board_repo.update_post(post, fields_to_update)
    return _serialize_post(updated_post), "", 200



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

def update_bug_status(post_id: int, status: str, user_role: str) -> tuple[dict | None, str, int]:
    if not _is_privileged(user_role):
        return None, "관리자 권한이 필요합니다.", 403

    status = (status or "").strip()

    if status not in VALID_BUG_STATUS:
        return None, "유효하지 않은 버그 상태입니다.", 400

    post = board_repo.get_post_by_id_admin(post_id)
    if not post:
        return None, "게시글을 찾을 수 없습니다.", 404

    if post.board_type != "BUG":
        return None, "버그게시판 글만 상태를 변경할 수 있습니다.", 400

    updated = board_repo.update_bug_status(post, status)
    return _serialize_post(updated), "", 200

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

def delete_post(post_id: int, user_id: str, user_role: str) -> tuple[str, int]:
    post = board_repo.get_post_by_id(post_id)
    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    is_author = str(post.member_id) == str(user_id)
    is_privileged = _is_privileged(user_role)

    if not is_author and not is_privileged:
        return "삭제 권한이 없습니다.", 403

    board_repo.soft_delete_attachments_by_post(post_id)
    board_repo.soft_delete_post(post)
    return "", 200


# ──────────────────────────────────────────────────────────────
# 마이페이지 서비스
# ──────────────────────────────────────────────────────────────

_TYPE_TO_BOARD = {"FREE": "건의게시판", "INFO": "정보게시판", "NOTICE": "정보게시판", "BUG": "버그게시판", "RESOURCE": "자료게시판",}


def get_my_posts(member_id: str, search: str, page: int, per_page: int) -> dict:
    posts, total = board_repo.get_posts_by_member(member_id, search, page, per_page)
    return {
        "posts":       [_serialize_post(p) for p in posts],
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


def get_my_comments(member_id: str, search: str, page: int, per_page: int) -> dict:
    comments, total = board_repo.get_comments_by_member(member_id, search, page, per_page)
    result = []
    for c in comments:
        d = _serialize_comment(c)
        d["post_title"]     = c.board.title if c.board else ""
        d["post_board_type"] = c.board.board_type if c.board else ""
        result.append(d)
    return {
        "comments":    result,
        "total":       total,
        "page":        page,
        "per_page":    per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }

def _normalize_board_type(board_type: str) -> str:
    value = (board_type or "FREE").strip()

    mapping = {
        "suggest": "FREE",
        "free": "FREE",
        "info": "INFO",
        "notice": "NOTICE",
        "bug": "BUG",
        "resource": "RESOURCE",
        "data": "RESOURCE",
    }

    return mapping.get(value.lower(), value.upper())

def _serialize_attachment(file: BoardAttachment) -> dict:
    return {
        "id": file.id,
        "board_id": file.board_id,
        "original_filename": file.original_filename,
        "file_url": file.file_url,
        "mime_type": file.mime_type,
        "file_size": file.file_size,
        "created_at": file.created_at.strftime("%Y-%m-%d %H:%M:%S") if file.created_at else None,
          }

# ──────────────────────────────────────────────────────────────
# 첨부파일 업로드/삭제
# ──────────────────────────────────────────────────────────────
def _is_allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def upload_attachment(post_id: int, user_id: str, user_role: str, file) -> tuple[dict | None, str, int]:
    post = board_repo.get_post_by_id(post_id)

    if not post:
        return None, "게시글을 찾을 수 없습니다.", 404

    is_author = str(post.member_id) == str(user_id)
    is_privileged = _is_privileged(user_role)

    if not is_author and not is_privileged:
        return None, "첨부파일 업로드 권한이 없습니다.", 403

    if not file or file.filename == "":
        return None, "파일을 선택해주세요.", 400

    if not _is_allowed_file(file.filename):
        return None, "허용되지 않는 파일 형식입니다.", 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_FILE_SIZE:
        return None, "파일 크기는 20MB 이하만 가능합니다.", 400

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"

    save_dir = os.path.join(UPLOAD_ROOT, str(post_id))
    os.makedirs(save_dir, exist_ok=True)

    file_path = os.path.join(save_dir, stored_filename)
    file.save(file_path)

    file_url = f"/api/board/files/{post_id}/{stored_filename}"

    attachment = board_repo.create_attachment(
        board_id=post_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_url=file_url,
        file_path=file_path,
        mime_type=file.mimetype,
        file_size=file_size,
    )

    return _serialize_attachment(attachment), "", 201


def delete_attachment(attachment_id: int, user_id: str, user_role: str) -> tuple[str, int]:
    file = board_repo.get_attachment_by_id(attachment_id)

    if not file:
        return "첨부파일을 찾을 수 없습니다.", 404

    post = board_repo.get_post_by_id_admin(file.board_id)

    if not post:
        return "게시글을 찾을 수 없습니다.", 404

    is_author = str(post.member_id) == str(user_id)
    is_privileged = _is_privileged(user_role)

    if not is_author and not is_privileged:
        return "첨부파일 삭제 권한이 없습니다.", 403

    board_repo.soft_delete_attachment(file)

    try:
        if file.file_path and os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        print(f"[FILE DELETE ERROR] {e}")

    return "", 200