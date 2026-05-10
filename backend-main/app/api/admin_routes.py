from flask import Blueprint, jsonify
from .. models.member import Member, EventLog
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

# 1. 사용자 목록 조회
@admin_bp.route('/users', methods=['GET'])
def get_users():
    users = Member.query.all()
    return jsonify([{"id": u.id, "name": u.login_id, "role": u.role} for u in users])

# 2. 대시보드 통계 (위험도별 이벤트 개수)
@admin_bp.route('/stats', methods=['GET'])
def get_stats():
    # 위험도(risk_level)별로 그룹화하여 개수를 셈
    stats = EventLog.query.with_entities(
        EventLog.risk_level, func.count(EventLog.id)
    ).group_by(EventLog.risk_level).all()
    return jsonify(dict(stats))

# 3. 과거 알림 내역 확인
@admin_bp.route('/notifications', methods=['GET'])
def get_notifications():
    logs = EventLog.query.order_by(EventLog.created_at.desc()).all()
    return jsonify([{
        "id": l.id, "level": l.risk_level, "msg": l.message, "time": l.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for l in logs])