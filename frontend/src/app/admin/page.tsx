'use client'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './page.module.css'

// 임시 더미 데이터 (실제 구현 시 API로 교체)
const dummyEvents = [
  { id: 1, type: '탱크로리', location: '경부고속도로 상행 23km', weather: '폭우', time: '14:22', status: '위험' },
  { id: 2, type: 'LPG 화물차', location: '서울외곽순환 북부', weather: '폭설', time: '11:05', status: '위험' },
  { id: 3, type: '화학물질 탱크', location: '중부고속도로 하행', weather: '안개', time: '09:40', status: '경고' },
  { id: 4, type: '탱크로리', location: '영동고속도로 서행', weather: '폭우', time: '08:15', status: '위험' },
  { id: 5, type: 'LPG 화물차', location: '올림픽대로 동행', weather: '강풍', time: '07:30', status: '경고' },
]

const dummyAlerts = [
  { id: 1, msg: '경부고속도로 탱크로리 탐지', time: '14:22', level: 'danger' },
  { id: 2, msg: '서울외곽순환 LPG 차량 탐지', time: '11:05', level: 'danger' },
  { id: 3, msg: '중부고속도로 화학물질 차량 경고', time: '09:40', level: 'warn' },
  { id: 4, msg: '영동고속도로 위험차량 탐지', time: '08:15', level: 'danger' },
  { id: 5, msg: '올림픽대로 LPG 차량 경고', time: '07:30', level: 'warn' },
]

const weatherStats = [
  { label: '폭우', count: 42, color: '#1b9bd1' },
  { label: '폭설', count: 28, color: '#81c4e2' },
  { label: '맑음', count: 12, color: '#d5e3a9' },
]

const weeklyData = [
  { day: '월', count: 12 },
  { day: '화', count: 8 },
  { day: '수', count: 15 },
  { day: '목', count: 6 },
  { day: '금', count: 18 },
  { day: '토', count: 4 },
  { day: '일', count: 3 },
]

const maxWeekly = Math.max(...weeklyData.map(d => d.count))

const sideMenus = [
  { label: '대시보드', href: '/admin', icon: '📊' },
  { label: '관제센터', href: '/admin/monitor', icon: '📡' },
  { label: '사용자관리', href: '/admin/users', icon: '👥' },
]

const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info', icon: '📋' },
]

export default function ControlPage() {
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(false)
  const [stats] = useState({
    todayEvents: 24,
    unhandled: 5,
    totalDetections: 1847,
    activeUsers: 248,
  })

  const totalWeather = weatherStats.reduce((s, w) => s + w.count, 0)

  return (
    <div className={styles.layout}>

      {/* ── 사이드바 (화면 맨 위부터 고정됨) ── */}
      <aside className={styles.sidebar}>
        {/* ⭐ 로고 이미지 클릭 시 /main으로 이동하도록 변경 */}
        <div className={styles.sideLogoWrap}>
          <Link href="/main" className={styles.logoLink}>
            <img src="/logo.png" alt="WeatherI 로고" height={36} />
          </Link>
        </div>

        <nav className={styles.sideNav}>
          {sideMenus.map(m => (
            <Link
              key={m.href}
              href={m.href}
              className={`${styles.sideItem} ${pathname === m.href ? styles.sideActive : ''}`}
            >
              <span className={styles.sideIcon}>{m.icon}</span>
              {m.label}
            </Link>
          ))}

          {/* 게시글 드롭다운 */}
          <button
            className={`${styles.sideItem} ${styles.sideDropBtn}`}
            onClick={() => setBoardOpen(!boardOpen)}
          >
            <span className={styles.sideIcon}>📝</span>
            게시글
            <span className={`${styles.arrow} ${boardOpen ? styles.arrowOpen : ''}`}>▾</span>
          </button>
          {boardOpen && (
            <div className={styles.subMenu}>
              {boardMenus.map(m => (
                <Link key={m.href} href={m.href} className={styles.subItem}>
                  {m.icon} {m.label}
                </Link>
              ))}
            </div>
          )}
        </nav>
      </aside>

      {/* ── 메인 콘텐츠 (사이드바 너비만큼 margin-left로 밀어줌) ── */}
      <main className={styles.main}>
        <div className={styles.topBar}>
          <h1 className={styles.pageTitle}>관리자 대시보드</h1>
        </div>

        {/* 통계 카드 4개 */}
        <div className={styles.statsRow}>
          {[
            { label: '오늘 위험 이벤트', value: stats.todayEvents, unit: '건', color: '#e43b3b' },
            { label: '미처리 이벤트', value: stats.unhandled, unit: '건', color: '#f39c12' },
            { label: '총 탐지 건수', value: stats.totalDetections.toLocaleString(), unit: '건', color: '#07559d' },
            { label: '활성 사용자 수', value: stats.activeUsers, unit: '명', color: '#1b9bd1' },
          ].map(s => (
            <div key={s.label} className={styles.statCard}>
              <p className={styles.statLabel}>{s.label}</p>
              <p className={styles.statValue} style={{ color: s.color }}>
                {s.value} <span className={styles.statUnit}>{s.unit}</span>
              </p>
            </div>
          ))}
        </div>

        {/* 중간 패널 (실시간 피드 + 날씨 통계) */}
        <div className={styles.midRow}>
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>실시간 이벤트 피드 <span className={styles.liveBadge}>LIVE</span></h2>
            <div className={styles.eventList}>
              {dummyEvents.map(e => (
                <div key={e.id} className={styles.eventItem}>
                  <span className={`${styles.eventDot} ${e.status === '위험' ? styles.dotDanger : styles.dotWarn}`} />
                  <div className={styles.eventInfo}>
                    <p className={styles.eventType}>{e.type}</p>
                    <p className={styles.eventLoc}>{e.location} · {e.weather}</p>
                  </div>
                  <div className={styles.eventRight}>
                    <span className={`${styles.eventBadge} ${e.status === '위험' ? styles.badgeDanger : styles.badgeWarn}`}>{e.status}</span>
                    <span className={styles.eventTime}>{e.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>날씨별 탐지 통계</h2>
            <div className={styles.chartWrap}>
              <div className={styles.donutWrap}>
                <svg width="250" height="250" viewBox="0 0 140 140">
                  {weatherStats.reduce((acc, w) => {
                    const pct = w.count / totalWeather
                    const angle = pct * 360
                    const startAngle = acc.total
                    const endAngle = startAngle + angle
                    const r = 55
                    const cx = 70, cy = 70
                    const start = {
                      x: cx + r * Math.cos((startAngle - 90) * Math.PI / 180),
                      y: cy + r * Math.sin((startAngle - 90) * Math.PI / 180),
                    }
                    const end = {
                      x: cx + r * Math.cos((endAngle - 90) * Math.PI / 180),
                      y: cy + r * Math.sin((endAngle - 90) * Math.PI / 180),
                    }
                    const largeArc = angle > 180 ? 1 : 0
                    acc.paths.push(
                      <path
                        key={w.label}
                        d={`M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y} Z`}
                        fill={w.color}
                        stroke="white"
                        strokeWidth="2"
                      />
                    )
                    acc.total += angle
                    return acc
                  }, { paths: [] as React.ReactNode[], total: 0 }).paths}
                  <circle cx="70" cy="70" r="35" fill="white" />
                  <text x="70" y="66" textAnchor="middle" fontSize="11" fill="#20436d" fontWeight="700">총</text>
                  <text x="70" y="80" textAnchor="middle" fontSize="13" fill="#07559d" fontWeight="700">{totalWeather}건</text>
                </svg>
                <div className={styles.donutLegend}>
                  {weatherStats.map(w => (
                    <div key={w.label} className={styles.legendItem}>
                      <span className={styles.legendDot} style={{ background: w.color }} />
                      <span>{w.label}</span>
                      <span className={styles.legendCount}>{w.count}건</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className={styles.barChart}>
                {weatherStats.map(w => (
                  <div key={w.label} className={styles.barRow}>
                    <span className={styles.barLabel}>{w.label}</span>
                    <div className={styles.barTrack}>
                      <div
                        className={styles.barFill}
                        style={{ width: `${(w.count / totalWeather) * 100}%`, background: w.color }}
                      />
                    </div>
                    <span className={styles.barCount}>{w.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 하단 패널 (주간 차트 + 알림) */}
        <div className={styles.bottomRow}>
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>주간 탐지 현황 (최근 7일)</h2>
            <div className={styles.weekChart}>
              {weeklyData.map(d => (
                <div key={d.day} className={styles.weekCol}>
                  <span className={styles.weekDay}>{d.day}</span>
                  <div className={styles.weekBarWrap}>
                    <div className={styles.weekBar} style={{ width: `${(d.count / maxWeekly) * 100}%` }} />
                  </div>
                  <span className={styles.weekCount}>{d.count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>최근 알림 이력 (최근 5개)</h2>
            <div className={styles.alertList}>
              {dummyAlerts.map(a => (
                <div key={a.id} className={styles.alertItem}>
                  <span className={`${styles.alertIcon} ${a.level === 'danger' ? styles.alertDanger : styles.alertWarn}`}>
                    {a.level === 'danger' ? '🚨' : '⚠️'}
                  </span>
                  <span className={styles.alertMsg}>{a.msg}</span>
                  <span className={styles.alertTime}>{a.time}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}