from ..repositories.notification_repo import NotificationRepository


class NotificationService:

    def __init__(self):
        self.repo = NotificationRepository()

    def get_admin_notifications(self, page, per_page, is_urgent=None, status=None):
        result = self.repo.find_all(page, per_page, is_urgent, status)
        return {
            "items": [self._to_dict(n, loc, weather) for n, loc, weather in result.items],
            "total": result.total,
            "page": result.page,
            "per_page": result.per_page,
        }

    def get_unread_count(self):
        return {"count": self.repo.count_unread()}

    def mark_as_read(self, notification_id):
        n = self.repo.mark_as_read(notification_id)
        return n is not None

    def mark_as_unread(self, notification_id):
        n = self.repo.mark_as_unread(notification_id)
        return n is not None

    def confirm(self, notification_id):
        n = self.repo.confirm(notification_id)
        return n is not None

    def unconfirm(self, notification_id):
        n = self.repo.unconfirm(notification_id)
        return n is not None

    def get_detail(self, notification_id):
        result = self.repo.find_detail_by_id(notification_id)
        if result is None:
            return None
        n, event = result
        data = self._to_dict(
            n,
            event.location_name if event else None,
            event.weather_type  if event else None,
        )
        if event:
            data.update({
                'latitude':            float(event.latitude)  if event.latitude  else None,
                'longitude':           float(event.longitude) if event.longitude else None,
                'main_vehicle_type':   event.main_vehicle_type,
                'risk_score':          event.risk_score,
                'total_vehicle_count': event.total_vehicle_count,
                'risk_vehicle_count':  event.risk_vehicle_count,
                'normal_vehicle_count':event.normal_vehicle_count,
                'event_status':        event.event_status,
                'llm_title':           event.llm_title,
                'llm_summary':         event.llm_summary,
                'llm_decision':        event.llm_decision,
                'llm_reason':          event.llm_reason,
                'detected_at':         event.detected_at.isoformat() if event.detected_at else None,
            })
        return data

    def get_new_since(self, last_id: int):
        rows = self.repo.find_new_since(last_id)
        return [self._to_dict(n, loc, weather) for n, loc, weather in rows]

    def _to_dict(self, n, location_name=None, weather_type=None):
        return {
            "id":            n.id,
            "target_type":   n.target_type,
            "member_id":     n.member_id,
            "event_id":      n.event_id,
            "title":         n.title,
            "content":       n.content,
            "risk_level":    n.risk_level,
            "status":        n.status,
            "is_confirmed":  n.read_at is not None,
            "sent_at":       n.sent_at.isoformat()   if n.sent_at    else None,
            "read_at":       n.read_at.isoformat()   if n.read_at    else None,
            "created_at":    n.created_at.isoformat() if n.created_at else None,
            "location_name": location_name or "",
            "weather_type":  weather_type  or "",
        }
