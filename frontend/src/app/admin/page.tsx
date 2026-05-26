'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { usePathname } from 'next/navigation'
import styles from './page.module.css'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

const sideMenus = [
  { label: '대시보드',  href: '/admin',         icon: '📊' },
  { label: '관제센터',  href: '/admin/monitor',  icon: '📡' },
  { label: '사용자관리', href: '/admin/users',   icon: '👥' },
]

const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info',    icon: '📋' },
]


const WEATHER_LABEL: Record<string, string> = {
  sun: '맑음', fog: '안개', heavy_rain: '폭우', heavy_snow: '폭설',
}
const WEATHER_COLOR: Record<string, string> = {
  sun:        '#d5e3a9',
  fog:        '#94a3b8',
  heavy_rain: '#1b9bd1',
  heavy_snow: '#81c4e2',
}
function weatherLabel(key: string) { return WEATHER_LABEL[key] ?? key }
function weatherColor(key: string) { return WEATHER_COLOR[key] ?? '#aaa' }

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('user')
    if (raw) { const p = JSON.parse(raw); if (p?.access_token) return p.access_token }
    return localStorage.getItem('access_token')
  } catch { return null }
}

type Event = {
  id: number
  event_title: string
  llm_title: string | null
  location_name: string
  weather_type: string
  main_vehicle_type: string
  risk_score: number | null
  risk_level: string
  event_status: string
  alert_required: boolean
  detected_at: string | null
}

type Summary = {
  total_event_count: number
  alert_required_count: number
  high_risk_count: number
  false_positive_count: number
  risk_level_counts: Record<string, number>
  weather_type_counts: Record<string, number>
  vehicle_type_counts: Record<string, number>
  recent_events: Event[]
}

export default function ControlPage() {
  const pathname  = usePathname()
  const router    = useRouter()
  const [boardOpen, setBoardOpen]   = useState(false)
  const [summary, setSummary]       = useState<Summary | null>(null)
  const [memberCount, setMemberCount] = useState<number | null>(null)
  const [weeklyData, setWeeklyData] = useState<{ day: string; count: number }[]>([])
  const [loading, setLoading]       = useState(true)

  useEffect(() => {
    const token = getToken()
    if (!token) { router.push('/login'); return }

    const headers = { Authorization: `Bearer ${token}` }

    Promise.all([
      fetch(`${API}/api/admin/dashboard/summary`, { headers }).then(r => r.json()),
      fetch(`${API}/api/admin/members?per_page=1`, { headers }).then(r => r.json()),
      fetch(`${API}/api/admin/dashboard/weekly`,   { headers }).then(r => r.json()),
    ]).then(([dash, members, weekly]) => {
      if (dash.success)    setSummary(dash.data)
      if (members.success) setMemberCount(members.data?.total ?? null)
      if (weekly.success)  setWeeklyData(weekly.data)
    }).catch(console.error).finally(() => setLoading(false))
  }, [router])

  // 날씨별 통계 배열로 변환
  const weatherStats = summary
    ? Object.entries(summary.weather_type_counts).map(([key, count]) => ({
        label: weatherLabel(key),
        count,
        color: weatherColor(key),
      }))
    : []

  const totalWeather = weatherStats.reduce((s, w) => s + w.count, 0)
  const maxWeekly    = Math.max(...weeklyData.map(d => d.count), 1)

  if (loading) {
    return (
      <div className={styles.layout}>
        <aside className={styles.sidebar} />
        <main className={styles.main}>
          <p style={{ padding: '40px', color: 'var(--text-muted)' }}>불러오는 중...</p>
        </main>
      </div>
    )
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.sideLogoWrap}>
          <Link href="/main" className={styles.logoLink}>
            <img src="/logo.png" alt="WeatherAI 로고" height={36} />
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

      <main className={styles.main}>
        <div className={styles.topBar}>
          <h1 className={styles.pageTitle}>관리자 대시보드</h1>
        </div>

        {/* 통계 카드 4개 */}
        <div className={styles.statsRow}>
          {[
            { label: '총 탐지 건수',      value: summary?.total_event_count?.toLocaleString() ?? '-',  unit: '건', color: '#07559d' },
            { label: '알림 필요 이벤트',   value: summary?.alert_required_count ?? '-',                unit: '건', color: '#e43b3b' },
            { label: '고위험 이벤트',      value: summary?.high_risk_count ?? '-',                     unit: '건', color: '#f39c12' },
            { label: '전체 회원 수',       value: memberCount?.toLocaleString() ?? '-',                unit: '명', color: '#1b9bd1' },
          ].map(s => (
            <div key={s.label} className={styles.statCard}>
              <p className={styles.statLabel}>{s.label}</p>
              <p className={styles.statValue} style={{ color: s.color }}>
                {s.value} <span className={styles.statUnit}>{s.unit}</span>
              </p>
            </div>
          ))}
        </div>

        {/* 중간 패널 (실시간 이벤트 피드 + 날씨 통계) */}
        <div className={styles.midRow}>
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>
              최근 탐지 이벤트 <span className={styles.liveBadge}>LIVE</span>
            </h2>
            <div className={styles.eventList}>
              {(summary?.recent_events ?? []).length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>탐지 이벤트가 없습니다.</p>
              )}
              {(summary?.recent_events ?? []).map(e => (
                <div key={e.id} className={styles.eventItem}>
                  <span className={`${styles.eventDot} ${e.risk_level === 'high' ? styles.dotDanger : styles.dotWarn}`} />
                  <div className={styles.eventInfo}>
                    <p className={styles.eventType}>{e.llm_title || e.event_title}</p>
                    <p className={styles.eventLoc}>{e.location_name}</p>
                  </div>
                  <div className={styles.eventRight}>
                    <span className={styles.eventBadge}>
                      {weatherLabel(e.weather_type)}
                    </span>
                    <span className={styles.eventTime}>
                      {e.detected_at ? new Date(e.detected_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '-'}
                    </span>
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
                  {totalWeather === 0 ? (
                    <circle cx="70" cy="70" r="55" fill="#e8f4fb" />
                  ) : (
                    weatherStats.reduce((acc, w) => {
                      if (w.count === 0) return acc
                      const pct = w.count / totalWeather
                      const angle = pct * 360
                      const startAngle = acc.total
                      const endAngle = startAngle + angle
                      const r = 55, cx = 70, cy = 70
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
                    }, { paths: [] as React.ReactNode[], total: 0 }).paths
                  )}
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
                        style={{ width: totalWeather > 0 ? `${(w.count / totalWeather) * 100}%` : '0%', background: w.color }}
                      />
                    </div>
                    <span className={styles.barCount}>{w.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 하단 패널 (주간 탐지 현황 + 알림 이벤트) */}
        <div className={styles.bottomRow}>
          <div className={styles.panel}>
            <h2 className={styles.panelTitle}>주간 탐지 현황 (최근 7일)</h2>
            <div className={styles.weekChart}>
              {weeklyData.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>데이터가 없습니다.</p>
              ) : weeklyData.map(d => (
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
            <h2 className={styles.panelTitle}>최근 알림 필요 이벤트 (최근 5개)</h2>
            <div className={styles.alertList}>
              {(summary?.recent_events ?? []).filter(e => e.alert_required).slice(0, 5).length === 0 && (
                <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem' }}>알림 이벤트가 없습니다.</p>
              )}
              {(summary?.recent_events ?? []).filter(e => e.alert_required).slice(0, 5).map(e => (
                <div key={e.id} className={styles.alertItem}>
                  <span className={`${styles.alertIcon} ${e.risk_level === 'high' ? styles.alertDanger : styles.alertWarn}`}>
                    {e.risk_level === 'high' ? '🚨' : '⚠️'}
                  </span>
                  <span className={styles.alertMsg}>{e.llm_title || e.event_title}</span>
                  <span className={styles.alertTime}>
                    {e.detected_at ? new Date(e.detected_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) : '-'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
