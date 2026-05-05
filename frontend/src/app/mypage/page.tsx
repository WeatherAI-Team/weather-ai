import styles from './page.module.css'

export default function MyPage() {
  const user = { name: '홍길동', email: 'hong@example.com', role: '운영자', grade: 'GOLD', joined: '2025-09-01', detections: 142, reports: 37 }
  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>마이페이지</p>
          <h1 className={styles.title}>내 계정</h1>
        </div>
      </section>
      <section className={styles.main}>
        <div className="container">
          <div className={styles.grid}>
            <div className={styles.profileCard}>
              <div className={styles.avatar}>{user.name[0]}</div>
              <h2>{user.name}</h2>
              <p className={styles.email}>{user.email}</p>
              <div className={styles.badges}>
                <span className={styles.roleBadge}>{user.role}</span>
                <span className={styles.gradeBadge}>{user.grade}</span>
              </div>
              <p className={styles.joined}>가입일: {user.joined}</p>
            </div>
            <div className={styles.infoPanel}>
              <h3>활동 통계</h3>
              <div className={styles.stats}>
                <div className={styles.stat}><span className={styles.statNum}>{user.detections}</span><span>탐지 분석</span></div>
                <div className={styles.stat}><span className={styles.statNum}>{user.reports}</span><span>리포트 생성</span></div>
              </div>
              <h3>계정 설정</h3>
              <div className={styles.settingsList}>
                {['이름 변경', '비밀번호 변경', '알림 설정', '접근 권한 확인'].map(s => (
                  <button key={s} className={styles.settingItem}>{s} <span>→</span></button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
