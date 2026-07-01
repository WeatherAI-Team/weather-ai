import json
import time

from flask import Blueprint, Response, jsonify, request, stream_with_context
from jose.exceptions import JWTError

from ..services.notification_service import NotificationService
from ..services.auth_utils import decode_token
from ..utils.auth_decorators import admin_required

notification_bp = Blueprint('notification', __name__, url_prefix='/api/admin/notifications')
svc = NotificationService()


# ── GET /api/admin/notifications ────────────────────────────────────────────
@notification_bp.route('', methods=['GET'])
@admin_required
def get_notifications():
    page      = request.args.get('page',     1,  type=int)
    per_page  = request.args.get('per_page', 20, type=int)
    status    = request.args.get('status')

    # is_urgent: 'true' → True, 'false' → False, 없으면 None(전체)
    _iu = request.args.get('is_urgent')
    is_urgent = True if _iu == 'true' else (False if _iu == 'false' else None)

    data = svc.get_admin_notifications(page, per_page, is_urgent, status)
    return jsonify({"success": True, "data": data}), 200


# ── GET /api/admin/notifications/unread-count ────────────────────────────────
@notification_bp.route('/unread-count', methods=['GET'])
@admin_required
def get_unread_count():
    return jsonify({"success": True, "data": svc.get_unread_count()}), 200


# ── PATCH /api/admin/notifications/<id>/read ─────────────────────────────────
@notification_bp.route('/<int:notification_id>/read', methods=['PATCH'])
@admin_required
def mark_as_read(notification_id):
    ok = svc.mark_as_read(notification_id)
    if not ok:
        return jsonify({"success": False, "message": "알림을 찾을 수 없습니다."}), 404
    return jsonify({"success": True}), 200


# ── GET /api/admin/notifications/<id> ───────────────────────────────────────
@notification_bp.route('/<int:notification_id>', methods=['GET'])
@admin_required
def get_notification_detail(notification_id):
    data = svc.get_detail(notification_id)
    if data is None:
        return jsonify({"success": False, "message": "알림을 찾을 수 없습니다."}), 404
    return jsonify({"success": True, "data": data}), 200


# ── PATCH /api/admin/notifications/<id>/confirm ──────────────────────────────
@notification_bp.route('/<int:notification_id>/confirm', methods=['PATCH'])
@admin_required
def confirm(notification_id):
    ok = svc.confirm(notification_id)
    if not ok:
        return jsonify({"success": False, "message": "알림을 찾을 수 없습니다."}), 404
    return jsonify({"success": True}), 200


# ── PATCH /api/admin/notifications/<id>/unconfirm ────────────────────────────
@notification_bp.route('/<int:notification_id>/unconfirm', methods=['PATCH'])
@admin_required
def unconfirm(notification_id):
    ok = svc.unconfirm(notification_id)
    if not ok:
        return jsonify({"success": False, "message": "알림을 찾을 수 없습니다."}), 404
    return jsonify({"success": True}), 200


# ── PATCH /api/admin/notifications/<id>/unread ───────────────────────────────
@notification_bp.route('/<int:notification_id>/unread', methods=['PATCH'])
@admin_required
def mark_as_unread(notification_id):
    ok = svc.mark_as_unread(notification_id)
    if not ok:
        return jsonify({"success": False, "message": "알림을 찾을 수 없습니다."}), 404
    return jsonify({"success": True}), 200


# ── GET /api/admin/notifications/stream?token=<JWT>&last_id=<int> ────────────
# EventSource는 커스텀 헤더를 지원하지 않으므로 token을 쿼리 파라미터로 받음.
# 쿼리 파라미터 토큰은 auth_decorators의 쿠키/헤더 방식 데코레이터로 처리할 수 없어 별도 검증한다.
@notification_bp.route('/stream', methods=['GET'])
def stream():
    token = request.args.get('token')
    if not token:
        token = request.cookies.get('access_token')

    payload = None
    if token:
        try:
            payload = decode_token(token)
        except JWTError:
            payload = None

    if payload is None or payload.get('role') not in ('admin', 'manager'):
        return Response(
            "data: unauthorized\n\n",
            status=401,
            mimetype='text/event-stream',
        )

    last_id = request.args.get('last_id', 0, type=int)

    def generate():
        nonlocal last_id
        while True:
            try:
                items = svc.get_new_since(last_id)
                for item in items:
                    last_id = item['id']
                    payload_str = json.dumps(item, ensure_ascii=False)
                    yield f"event: notification\ndata: {payload_str}\n\n"
                # 연결 유지용 keepalive
                yield ": keepalive\n\n"
                time.sleep(3)
            except GeneratorExit:
                return
            except Exception:
                return

    resp = Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
    )
    resp.headers['Cache-Control']      = 'no-cache'
    resp.headers['X-Accel-Buffering']  = 'no'
    # CORS: SSE는 preflight 없이 직접 연결하므로 명시 필요
    origin = request.headers.get('Origin', 'http://localhost:3000')
    resp.headers['Access-Control-Allow-Origin']      = origin
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    return resp
