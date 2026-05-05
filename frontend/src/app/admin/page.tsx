import styles from './page.module.css'

export default function AdminPage() {
  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <span className={styles.adminBadge}>🔐 관리자 전용</span>
          <h1 className={styles.title}>관리자 대시보드</h1>
          <p className={styles.desc}>시스템 현황, 사용자 관리, 탐지 통계를 확인하세요</p>
        </div>
      </section>
      <section className={styles.main}>
        <div className="container">
          <div className={styles.statsRow}>
            {[
              { label:'총 사용자', value:'248', icon:'👥', delta:'+12 이번 달' },
              { label:'이번 달 탐지', value:'1,847', icon:'📡', delta:'+23% vs 지난달' },
              { label:'평균 신뢰도', value:'97.2%', icon:'🎯', delta:'↑ 0.3%p' },
              { label:'활성 스트림', value:'14', icon:'📺', delta:'현재 모니터링 중' },
            ].map(s => (
              <div key={s.label} className={styles.statCard}>
                <span className={styles.statIcon}>{s.icon}</span>
                <div>
                  <div className={styles.statValue}>{s.value}</div>
                  <div className={styles.statLabel}>{s.label}</div>
                  <div className={styles.statDelta}>{s.delta}</div>
                </div>
              </div>
            ))}
          </div>

          <div className={styles.panels}>
            <div className={styles.panel}>
              <h2>사용자 관리</h2>
              <table className={styles.table}>
                <thead><tr><th>이름</th><th>이메일</th><th>등급</th><th>상태</th><th>액션</th></tr></thead>
                <tbody>
                  {[
                    { name:'홍길동', email:'hong@ex.com', grade:'GOLD', status:'활성' },
                    { name:'김철수', email:'kim@ex.com', grade:'SILVER', status:'활성' },
                    { name:'이영희', email:'lee@ex.com', grade:'BRONZE', status:'정지' },
                  ].map((u,i) => (
                    <tr key={i}>
                      <td>{u.name}</td><td>{u.email}</td>
                      <td><span className={styles.gradeBadge}>{u.grade}</span></td>
                      <td><span className={`${styles.statusBadge} ${u.status === '활성' ? styles.active : styles.suspended}`}>{u.status}</span></td>
                      <td><button className={styles.actionBtn}>수정</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className={styles.panel}>
              <h2>시스템 상태</h2>
              <div className={styles.systemList}>
                {[
                  { name:'Frontend (Next.js)', port:'3000', status:'정상' },
                  { name:'Backend Main (Flask)', port:'5000', status:'정상' },
                  { name:'Backend AI (FastAPI)', port:'8000', status:'정상' },
                  { name:'PostgreSQL DB', port:'5432', status:'정상' },
                ].map(s => (
                  <div key={s.name} className={styles.systemItem}>
                    <span className={styles.systemDot} />
                    <span className={styles.systemName}>{s.name}</span>
                    <span className={styles.systemPort}>:{s.port}</span>
                    <span className={styles.systemStatus}>{s.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
