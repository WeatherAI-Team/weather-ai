from datetime import datetime, timezone
from app import db
from app.models.admin_board import AdminBoard
from app.models.notification import Notification
from app.models.detection_event import DetectionEvent

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def save_alert_to_db(
    event_id: int | None,
    final_alert: dict,
    weather_type: str = "UNKNOWN",
    risk_score: int = 0,
) -> dict:
    try:
        risk_level  = final_alert.get("risk_level", "CAUTION")
        title       = final_alert.get("title", "위험 차량 감지 알림")
        content     = final_alert.get("admin_message", "관제센터 확인 필요")
        vehicle_type = "UNKNOWN"

        # detection_events llm 컬럼 업데이트
        if event_id:
            event = DetectionEvent.query.get(event_id)
            if event:
                event.event_title  = title
                event.llm_title    = title
                event.llm_summary  = final_alert.get("admin_message", "")
                event.llm_decision = "ALERT" if final_alert.get("alert_required") else "SKIP"
                event.llm_reason   = final_alert.get("reason", "")
                event.alert_required = bool(final_alert.get("alert_required", True))
                event.updated_at   = utc_now()
                db.session.flush()

        # admin_boards 저장
        admin_board = AdminBoard(
            event_id       = event_id,
            admin_id       = None,
            title          = title,
            content        = content,
            risk_score     = risk_score,
            risk_level     = risk_level,
            weather_type   = weather_type,
            vehicle_type   = vehicle_type,
            event_status   = "UNCONFIRMED",
            created_by_llm = True,
            created_at     = utc_now(),
            updated_at     = utc_now(),
        )
        db.session.add(admin_board)
        db.session.flush()

        # notifications 저장
        notification = Notification(
            target_type = "ADMIN",
            member_id   = None,
            event_id    = event_id,
            title       = title,
            content     = final_alert.get("driver_message", content),  # driver_message로 변경
            risk_level  = risk_level,
            status      = "SENT",
            sent_at     = utc_now(),
            created_at  = utc_now(),
        )
        db.session.add(notification)
        db.session.commit()

        print(f"[DB] admin_boards 저장 완료 | id: {admin_board.id}")
        print(f"[DB] notifications 저장 완료 | id: {notification.id}")

        return {
            "admin_board_id":  admin_board.id,
            "notification_id": notification.id,
        }

    except Exception as e:
        db.session.rollback()
        print(f"[DB] 알림 저장 실패: {e}")
        return {}