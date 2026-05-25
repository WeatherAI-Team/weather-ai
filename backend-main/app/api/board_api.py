"""
board_api.py  –  API 레이어 (요청/응답만)
위치: backend-main/app/api/board_api.py
"""

from flask import Blueprint, request, jsonify
from app.services import board_service
from functools import wraps
from jose import jwt
import os

board_bp = Blueprint("board", __name__, url_prefix="/api/board")

SECRET_KEY = os.getenv("SECRET_KEY", "your-fallback-secret-key")


# ──────────────────────────────────────────────────────────────
# 데코레이터 (기존 member_api.py 패턴과 동일)
# ──────────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"success": False, "message": "토큰이 없습니다."}), 401
        try:
            auth_token = token.split(" ")[1] if " " in token else token
            payload = jwt.decode(auth_token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
            request.user_id   = payload.get("sub")
            request.user_role = payload.get("role", "user")
        except Exception as e:
            print(f"[JWT ERROR] {e}")
            return jsonify({"success": False, "message": "유효하지 않은 토큰입니다."}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"success": False, "message": "토큰이 없습니다."}), 401
        try:
            auth_token = token.split(" ")[1] if " " in token else token
            payload = jwt.decode(auth_token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False})
            request.user_id   = payload.get("sub")
            request.user_role = payload.get("role", "user")
            if request.user_role not in ("admin", "manager"):
                return jsonify({"success": False, "message": "관리자 권한이 필요합니다."}), 403
        except Exception as e:
            print(f"[JWT ERROR] {e}")
            return jsonify({"success": False, "message": "유효하지 않은 토큰입니다."}), 401
        return f(*args, **kwargs)
    return decorated


# ──────────────────────────────────────────────────────────────
# 게시글 목록
# GET /api/board/posts?board_type=suggest&search=&page=1&per_page=10
# ──────────────────────────────────────────────────────────────
@board_bp.route("/posts", methods=["GET"])
def get_posts():
    result = board_service.get_post_list(
        board_type_param = request.args.get("board_type", "suggest"),
        search           = request.args.get("search", "").strip(),
        page             = int(request.args.get("page", 1)),
        per_page         = int(request.args.get("per_page", 10)),
    )
    return jsonify({"success": True, **result})


# ──────────────────────────────────────────────────────────────
# 게시글 상세
# GET /api/board/posts/<post_id>
# ──────────────────────────────────────────────────────────────
@board_bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    data, error = board_service.get_post_detail(post_id)
    if error:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, "post": data})


# ──────────────────────────────────────────────────────────────
# 게시글 작성
# POST /api/board/posts
# Body: { title, content, board_type, pinned }
# ──────────────────────────────────────────────────────────────
@board_bp.route("/posts", methods=["POST"])
@login_required
def create_post():
    body = request.get_json()
    post, error, status = board_service.create_post(
        member_id  = request.user_id,
        title      = body.get("title", ""),
        content    = body.get("content", ""),
        board_type = body.get("board_type", "FREE"),
        pinned     = bool(body.get("pinned", False)),
        user_role  = request.user_role,
    )
    if error:
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "post": post}), status


# ──────────────────────────────────────────────────────────────
# 게시글 수정
# PUT /api/board/posts/<post_id>
# ──────────────────────────────────────────────────────────────
@board_bp.route("/posts/<int:post_id>", methods=["PUT"])
@login_required
def update_post(post_id):
    body = request.get_json()
    post, error, status = board_service.update_post(
        post_id     = post_id,
        update_data = body,
        user_id     = request.user_id,
        user_role   = request.user_role,
    )
    if error:
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "post": post})


# ──────────────────────────────────────────────────────────────
# 게시글 삭제
# DELETE /api/board/posts/<post_id>
# ──────────────────────────────────────────────────────────────
@board_bp.route("/posts/<int:post_id>", methods=["DELETE"])
@login_required
def delete_post(post_id):
    error, status = board_service.delete_post(
        post_id   = post_id,
        user_id   = request.user_id,
        user_role = request.user_role,
    )
    if error:
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "message": "삭제되었습니다."})


# ──────────────────────────────────────────────────────────────
# 댓글 작성
# POST /api/board/posts/<post_id>/comments
# Body: { content, parent_id? }
# ──────────────────────────────────────────────────────────────
@board_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@login_required
def create_comment(post_id):
    body = request.get_json()
    comment, error, status = board_service.create_comment(
        post_id   = post_id,
        member_id = request.user_id,
        content   = body.get("content", ""),
        parent_id = body.get("parent_id"),
    )
    if error:
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "comment": comment}), status


# ──────────────────────────────────────────────────────────────
# 댓글 삭제
# DELETE /api/board/comments/<comment_id>
# ──────────────────────────────────────────────────────────────
@board_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@login_required
def delete_comment(comment_id):
    error, status = board_service.delete_comment(
        comment_id = comment_id,
        user_id    = request.user_id,
        user_role  = request.user_role,
    )
    if error:
        return jsonify({"success": False, "message": error}), status
    return jsonify({"success": True, "message": "삭제되었습니다."})


# ──────────────────────────────────────────────────────────────
# [관리자] 게시글 목록
# GET /api/board/admin/posts?board_type=FREE&search=&page=1
# ──────────────────────────────────────────────────────────────
@board_bp.route("/admin/posts", methods=["GET"])
@admin_required
def admin_get_posts():
    result = board_service.admin_get_post_list(
        board_type = request.args.get("board_type", "FREE"),
        search     = request.args.get("search", "").strip(),
        page       = int(request.args.get("page", 1)),
        per_page   = int(request.args.get("per_page", 20)),
    )
    return jsonify({"success": True, **result})


# ──────────────────────────────────────────────────────────────
# [관리자] 공지 토글
# PATCH /api/board/admin/posts/<post_id>/toggle-pinned
# ──────────────────────────────────────────────────────────────
@board_bp.route("/admin/posts/<int:post_id>/toggle-pinned", methods=["PATCH"])
@admin_required
def admin_toggle_pinned(post_id):
    data, error = board_service.admin_toggle_pinned(post_id)
    if error:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, **data})


# ──────────────────────────────────────────────────────────────
# [관리자] 활성 토글
# PATCH /api/board/admin/posts/<post_id>/toggle-active
# ──────────────────────────────────────────────────────────────
@board_bp.route("/admin/posts/<int:post_id>/toggle-active", methods=["PATCH"])
@admin_required
def admin_toggle_active(post_id):
    data, error = board_service.admin_toggle_active(post_id)
    if error:
        return jsonify({"success": False, "message": error}), 404
    return jsonify({"success": True, **data})