from datetime import datetime, timezone

from app import db
from ..models.notification import Notification
from ..models.detection_event import DetectionEvent
from sqlalchemy import desc


class NotificationRepository:

    def _base_query(self):
        """Notification + DetectionEvent LEFT JOIN 기본 쿼리."""
        return (
            db.session.query(
                Notification,
                DetectionEvent.location_name,
                DetectionEvent.weather_type,
            )
            .outerjoin(DetectionEvent, Notification.event_id == DetectionEvent.id)
            .filter(Notification.target_type == 'ADMIN')
        )

    # 긴급 판정 기준: HIGH 또는 CRITICAL
    URGENT_LEVELS = ('HIGH', 'CRITICAL')

    def find_all(self, page=1, per_page=20, is_urgent=None, status=None):
        q = self._base_query()
        if is_urgent is True:
            q = q.filter(Notification.risk_level.in_(self.URGENT_LEVELS))
        elif is_urgent is False:
            q = q.filter(~Notification.risk_level.in_(self.URGENT_LEVELS))
        if status:
            q = q.filter(Notification.status == status.upper())
        return q.order_by(desc(Notification.created_at)).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def count_unread(self):
        return (
            Notification.query
            .filter(Notification.target_type == 'ADMIN', Notification.status != 'READ')
            .count()
        )

    def find_by_id(self, notification_id):
        return Notification.query.get(notification_id)

    def mark_as_read(self, notification_id):
        n = Notification.query.get(notification_id)
        if n is None:
            return None
        n.status = 'READ'
        db.session.commit()
        return n

    def confirm(self, notification_id):
        n = Notification.query.get(notification_id)
        if n is None:
            return None
        n.read_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
        return n

    def unconfirm(self, notification_id):
        n = Notification.query.get(notification_id)
        if n is None:
            return None
        n.read_at = None
        db.session.commit()
        return n

    def find_new_since(self, last_id: int):
        """SSE 폴링용: last_id 이후에 생성된 ADMIN 알림 반환."""
        return (
            self._base_query()
            .filter(Notification.id > last_id)
            .order_by(Notification.id)
            .all()
        )

    def find_detail_by_id(self, notification_id: int):
        """알림 1건 + 연결된 DetectionEvent 전체 데이터 반환."""
        return (
            db.session.query(Notification, DetectionEvent)
            .outerjoin(DetectionEvent, Notification.event_id == DetectionEvent.id)
            .filter(Notification.id == notification_id)
            .first()
        )

    def mark_as_unread(self, notification_id: int):
        """처리 취소: status만 SENT로 되돌림."""
        n = Notification.query.get(notification_id)
        if n is None:
            return None
        n.status = 'SENT'
        db.session.commit()
        return n
