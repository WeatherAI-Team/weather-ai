from . import socketio, db
from .models import EventLog

# 관리자 웹소켓 연결 확인용 (선택 사항)
@socketio.on('connect', namespace='/admin')
def test_connect():
    print("관리자가 대시보드에 접속했습니다.")

# 4. 실시간 알림 함수 (AI 분석 결과가 나올 때 이 함수를 호출하세요)
def send_danger_alert(event_data):
    """
    event_data 예시: {'type': 'Heavy Rain', 'risk_level': 8, 'message': '침수 위험!'}
    """
    # DB에 먼저 저장 (알림 내역 기능)
    new_log = EventLog(
        event_type=event_data['type'],
        risk_level=event_data['risk_level'],
        message=event_data['message']
    )
    db.session.add(new_log)
    db.session.commit()

    # 위험도가 7 이상일 때만 관리자에게 실시간 알림 (웹소켓)
    if event_data['risk_level'] >= 7:
        socketio.emit('critical_alert', {
            'level': event_data['risk_level'],
            'message': event_data['message'],
            'type': event_data['type']
        }, namespace='/admin')