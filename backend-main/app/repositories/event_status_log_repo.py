# app/repositories/event_status_log_repo.py

from app import db
from app.models.event_status_log import EventStatusLog


class EventStatusLogRepository:
    def create_status_log(self, data: dict):
        # 이벤트 상태 변경 이력을 DB에 새로 저장해.
        status_log = EventStatusLog(**data)

        db.session.add(status_log)

        return status_log

    def create_initial_status_log(
        self,
        event_id: int,
        new_status: str = "DETECTED",
        memo: str | None = None,
    ):
        # 탐지 이벤트가 처음 생성됐을 때 초기 상태 이력을 남긴다
        status_log = EventStatusLog(
            event_id=event_id,
            changed_by=None,
            previous_status=None,
            new_status=new_status,
            memo=memo,
        )

        db.session.add(status_log)

        return status_log

    def create_changed_status_log(
        self,
        event_id: int,
        previous_status: str | None,
        new_status: str,
        changed_by: int | None = None,
        memo: str | None = None,
    ):
        # 관리자가 이벤트 상태를 변경했을 때 변경 이력을 남긴다
        status_log = EventStatusLog(
            event_id=event_id,
            changed_by=changed_by,
            previous_status=previous_status,
            new_status=new_status,
            memo=memo,
        )

        db.session.add(status_log)

        return status_log

    def find_by_event_id(self, event_id: int):
        # 특정 탐지 이벤트의 상태 변경 이력을 시간순으로 조회한다.
        return EventStatusLog.query.filter(
            EventStatusLog.event_id == event_id
        ).order_by(
            EventStatusLog.created_at.asc()
        ).all()