'use client'
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'
import { useNotification } from '@/contexts/NotificationContext'

const sideMenus = [
  { label: '대시보드',  href: '/admin',                icon: '📊' },
  { label: '관제센터',  href: '/admin/monitor',         icon: '📡' },
  { label: '알림이력',  href: '/admin/notifications',   icon: '🔔' },
  { label: '사용자관리', href: '/admin/users',           icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info',    icon: '📋' },
]

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

const WEATHER_LABEL: Record<string, string> = {
  clear: '맑음', fog: '안개', heavy_rain: '폭우', heavy_snow: '폭설',
}
const WEATHER_ICON: Record<string, string> = {
  clear: '☀️', fog: '🌫️', heavy_rain: '🌧️', heavy_snow: '❄️',
}
const VEHICLE_LABEL: Record<string, string> = {
  RMC:        '래미콘',
  Gas_Truck:  '탱크로리',
  cargo_truck:'카고트럭',
  '25t_truck':'25톤 이상 차량',
}
const DECISION_LABEL: Record<string, { label: string; color: string }> = {
  approved:  { label: '위험 확인', color: '#e43b3b' },
  rejected:  { label: '오탐 판정', color: '#27ae60' },
  uncertain: { label: '불확실',    color: '#f39c12' },
}

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('user')
    if (raw) { const p = JSON.parse(raw); if (p?.access_token) return p.access_token }
    return localStorage.getItem('access_token')
  } catch { return null }
}

type ApiNotification = {
  id: number
  target_type: string
  member_id: number | null
  event_id: number | null
  title: string
  content: string
  risk_level: string
  status: string
  is_confirmed: boolean
  sent_at: string | null
  read_at: string | null
  created_at: string
  location_name: string
  weather_type: string
}

type NotificationDetail = ApiNotification & {
  is_confirmed: boolean
  latitude: number | null
  longitude: number | null
  main_vehicle_type: string | null
  risk_score: number | null
  total_vehicle_count: number | null
  risk_vehicle_count: number | null
  normal_vehicle_count: number | null
  event_status: string | null
  llm_title: string | null
  llm_summary: string | null
  llm_decision: string | null
  llm_reason: string | null
  detected_at: string | null
}

type Filters = {
  is_urgent: '' | 'true' | 'false'
  status: '' | 'PENDING' | 'SENT' | 'FAILED' | 'READ'
}

// ── 상세 모달 ─────────────────────────────────────────────────────────────────
function NotificationModal({
  detail,
  loading,
  onClose,
  onRead,
  onUnread,
}: {
  detail: NotificationDetail | null
  loading: boolean
  onClose: () => void
  onRead: (id: number) => void
  onUnread: (id: number) => void
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const URGENT_LEVELS = ['HIGH', 'CRITICAL']
  const isUrgent     = !!detail?.risk_level && URGENT_LEVELS.includes(detail.risk_level)
  const isConfirmed  = !!detail?.is_confirmed
  const isResolved   = detail?.status === 'READ'
  const decision   = detail?.llm_decision ? DECISION_LABEL[detail.llm_decision] : null
  const vehicleLabel = detail?.main_vehicle_type ? (VEHICLE_LABEL[detail.main_vehicle_type] ?? detail.main_vehicle_type) : null

  const mapUrl = detail?.latitude && detail?.longitude
    ? `https://map.kakao.com/link/map/${encodeURIComponent(detail.location_name || '위치')},${detail.latitude},${detail.longitude}`
    : null

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={e => e.stopPropagation()}>

        {/* 헤더 */}
        <div className={`${styles.modalHeader} ${isUrgent ? styles.modalHeaderUrgent : ''}`}>
          <div className={styles.modalTitleRow}>
            <span className={`${styles.modalUrgentBadge} ${isUrgent ? styles.badgeUrgent : styles.badgeNormal}`}>
              {isUrgent ? '🚨 긴급' : '📋 일반'}
            </span>
            <h2 className={styles.modalTitle}>
              {loading ? '불러오는 중...' : (detail?.title ?? '알림 상세')}
            </h2>
          </div>
          <div className={styles.modalHeaderActions}>
            {!loading && detail && (
              isResolved
                ? <button className={styles.cancelBtn} onClick={() => onUnread(detail.id)}>처리 취소</button>
                : <button className={styles.readBtnModal} onClick={() => onRead(detail.id)}>처리완료</button>
            )}
            <button className={styles.closeBtn} onClick={onClose} aria-label="닫기">✕</button>
          </div>
        </div>

        {/* 본문 */}
        <div className={styles.modalBody}>
          {loading && <div className={styles.modalLoading}>상세 정보를 불러오는 중...</div>}

          {!loading && detail && (
            <>
              {/* 상태 칩 */}
              <div className={styles.infoChips}>
                <span className={`${styles.chip} ${isUrgent ? styles.chipDanger : styles.chipBlue}`}>
                  위험도 {detail.risk_level}
                  {detail.risk_score != null && ` · ${detail.risk_score}점`}
                </span>
                <span className={styles.chip}>
                  {WEATHER_ICON[detail.weather_type] ?? '🌤️'}&nbsp;
                  {WEATHER_LABEL[detail.weather_type] ?? detail.weather_type}
                </span>
                <span className={styles.chip}>
                  📍 {detail.location_name || '-'}
                </span>
                <span className={`${styles.chip} ${isConfirmed ? styles.chipGreen : styles.chipOrange}`}>
                  {isConfirmed ? '✅ 확인완료' : '⏳ 미확인'}
                </span>
                {detail.detected_at && (
                  <span className={styles.chipTime}>
                    탐지: {new Date(detail.detected_at).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}
                  </span>
                )}
              </div>

              {/* 2열: AI 분석 | CCTV */}
              <div className={styles.modalGrid}>

                {/* AI 분석 보고서 */}
                <div className={styles.modalSection}>
                  <h3 className={styles.sectionTitle}>🤖 AI 분석 보고서</h3>

                  {decision && (
                    <div className={styles.decisionRow}>
                      <span className={styles.decisionLabel}>판정</span>
                      <span className={styles.decisionValue} style={{ color: decision.color }}>
                        ● {decision.label}
                      </span>
                    </div>
                  )}

                  {detail.llm_title && (
                    <div className={styles.llmBlock}>
                      <p className={styles.llmSubLabel}>분석 제목</p>
                      <p className={styles.llmText}>{detail.llm_title}</p>
                    </div>
                  )}

                  {detail.llm_summary && (
                    <div className={styles.llmBlock}>
                      <p className={styles.llmSubLabel}>상황 요약</p>
                      <p className={styles.llmText}>{detail.llm_summary}</p>
                    </div>
                  )}

                  {detail.llm_reason && (
                    <div className={styles.llmBlock}>
                      <p className={styles.llmSubLabel}>판정 근거</p>
                      <p className={styles.llmText}>{detail.llm_reason}</p>
                    </div>
                  )}

                  {detail.content && (
                    <div className={styles.llmBlock}>
                      <p className={styles.llmSubLabel}>알림 내용</p>
                      <p className={styles.llmText}>{detail.content}</p>
                    </div>
                  )}

                  {!detail.llm_title && !detail.llm_summary && !detail.llm_reason && !detail.content && (
                    <p className={styles.emptyText}>AI 분석 정보가 없습니다.</p>
                  )}
                </div>

                {/* CCTV */}
                <div className={styles.modalSection}>
                  <h3 className={styles.sectionTitle}>📷 CCTV 화면</h3>
                  <div className={styles.cctvPlaceholder}>
                    <span className={styles.cctvIcon}>📹</span>
                    <p className={styles.cctvMsg}>탐지 당시 저장된 영상이 없습니다</p>
                    <p className={styles.cctvSub}>
                      {detail.event_id ? `이벤트 ID: ${detail.event_id}` : '탐지 이벤트 정보 없음'}
                    </p>
                  </div>
                </div>
              </div>

              {/* 위치 */}
              <div className={styles.modalSection}>
                <h3 className={styles.sectionTitle}>📍 위치 정보</h3>
                <div className={styles.locationRow}>
                  <div className={styles.locationInfo}>
                    <div className={styles.locItem}>
                      <span className={styles.locLabel}>위치명</span>
                      <span className={styles.locValue}>{detail.location_name || '-'}</span>
                    </div>
                    {detail.latitude != null && (
                      <div className={styles.locItem}>
                        <span className={styles.locLabel}>위도</span>
                        <span className={styles.locValue}>{detail.latitude.toFixed(6)}</span>
                      </div>
                    )}
                    {detail.longitude != null && (
                      <div className={styles.locItem}>
                        <span className={styles.locLabel}>경도</span>
                        <span className={styles.locValue}>{detail.longitude.toFixed(6)}</span>
                      </div>
                    )}
                  </div>
                  {mapUrl && (
                    <a href={mapUrl} target="_blank" rel="noopener noreferrer" className={styles.mapBtn}>
                      🗺️ 카카오맵에서 보기
                    </a>
                  )}
                </div>
              </div>

              {/* 차량 통계 */}
              {(detail.total_vehicle_count != null || vehicleLabel) && (
                <div className={styles.modalSection}>
                  <h3 className={styles.sectionTitle}>🚛 차량 통계</h3>
                  <div className={styles.vehicleGrid}>
                    {detail.total_vehicle_count != null && (
                      <div className={styles.vehicleStat}>
                        <span className={styles.vehicleNum}>{detail.total_vehicle_count}</span>
                        <span className={styles.vehicleStatLabel}>전체 차량</span>
                      </div>
                    )}
                    {detail.risk_vehicle_count != null && (
                      <div className={`${styles.vehicleStat} ${styles.vehicleStatDanger}`}>
                        <span className={styles.vehicleNum}>{detail.risk_vehicle_count}</span>
                        <span className={styles.vehicleStatLabel}>위험 차량</span>
                      </div>
                    )}
                    {detail.normal_vehicle_count != null && (
                      <div className={styles.vehicleStat}>
                        <span className={styles.vehicleNum}>{detail.normal_vehicle_count}</span>
                        <span className={styles.vehicleStatLabel}>일반 차량</span>
                      </div>
                    )}
                    {vehicleLabel && (
                      <div className={`${styles.vehicleStat} ${styles.vehicleStatAccent}`}>
                        <span className={`${styles.vehicleNum} ${styles.vehicleNumText}`}>{vehicleLabel}</span>
                        <span className={styles.vehicleStatLabel}>주요 차종</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────
export default function NotificationsPage() {
  const pathname = usePathname()
  const router   = useRouter()
  const { unreadCount, notifications: sseNotifications, markAllRead, resolveNotification } = useNotification()

  const [boardOpen, setBoardOpen]     = useState(false)
  const [apiItems, setApiItems]       = useState<ApiNotification[]>([])
  const [loading, setLoading]         = useState(true)
  const [filters, setFilters]         = useState<Filters>({ is_urgent: '', status: '' })
  const [page, setPage]               = useState(1)
  const [total, setTotal]             = useState(0)
  const [modalOpen, setModalOpen]     = useState(false)
  const [detail, setDetail]           = useState<NotificationDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)

  const PER_PAGE = 20

  useEffect(() => { markAllRead() }, [markAllRead])

  const fetchNotifications = useCallback(async (p = 1, f = filters) => {
    const token = getToken()
    if (!token) { router.push('/login'); return }
    setLoading(true)
    const q = new URLSearchParams({ page: String(p), per_page: String(PER_PAGE) })
    if (f.is_urgent) q.set('is_urgent', f.is_urgent)
    if (f.status)    q.set('status',    f.status)
    try {
      const res  = await fetch(`${API}/api/admin/notifications?${q}`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const json = await res.json()
      if (json.success) { setApiItems(json.data.items); setTotal(json.data.total) }
    } catch {}
    finally { setLoading(false) }
  }, [filters, router])

  useEffect(() => { fetchNotifications(1, filters); setPage(1) }, [filters]) // eslint-disable-line
  useEffect(() => { fetchNotifications(page, filters) },          [page])    // eslint-disable-line

  const URGENT_LEVELS = ['HIGH', 'CRITICAL']

  const merged: ApiNotification[] = (() => {
    const ids = new Set(apiItems.map(i => i.id))
    const sseFiltered = sseNotifications
      .filter(n => !ids.has(n.id))
      .filter(n => {
        if (filters.is_urgent === 'true')  return URGENT_LEVELS.includes(n.risk_level)
        if (filters.is_urgent === 'false') return !URGENT_LEVELS.includes(n.risk_level)
        return true
      })
      .filter(n => {
        if (filters.status) return n.status === filters.status
        return true
      })
    return [...sseFiltered.map(n => ({ ...n })), ...apiItems]
  })()

  const handleRowClick = async (n: ApiNotification) => {
    setModalOpen(true)
    setDetail(null)
    setDetailLoading(true)
    const token = getToken()
    try {
      const res  = await fetch(`${API}/api/admin/notifications/${n.id}`, {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      const json = await res.json()
      if (json.success) setDetail(json.data)
    } catch {}
    finally { setDetailLoading(false) }
  }

  const handleRead = async (id: number) => {
    await resolveNotification(id)
    setApiItems(prev => prev.map(n => n.id === id ? { ...n, status: 'READ' } : n))
    setDetail(prev => prev ? { ...prev, status: 'READ' } : prev)
  }

  const handleUnread = async (id: number) => {
    const token = getToken()
    if (!token) return
    await fetch(`${API}/api/admin/notifications/${id}/unread`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    })
    setApiItems(prev => prev.map(n => n.id === id ? { ...n, status: 'SENT' } : n))
    setDetail(prev => prev ? { ...prev, status: 'SENT' } : prev)
  }

  const handleConfirm = async (id: number) => {
    const token = getToken()
    if (!token) return
    await fetch(`${API}/api/admin/notifications/${id}/confirm`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    })
    setApiItems(prev => prev.map(n => n.id === id ? { ...n, is_confirmed: true } : n))
    setDetail(prev => prev ? { ...prev, is_confirmed: true } : prev)
  }

  const handleUnconfirm = async (id: number) => {
    const token = getToken()
    if (!token) return
    await fetch(`${API}/api/admin/notifications/${id}/unconfirm`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    })
    setApiItems(prev => prev.map(n => n.id === id ? { ...n, is_confirmed: false } : n))
    setDetail(prev => prev ? { ...prev, is_confirmed: false } : prev)
  }

  const totalPages = Math.ceil(total / PER_PAGE)

  return (
    <div className={styles.layout}>
      {/* 사이드바 */}
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
              {m.href === '/admin/notifications' && unreadCount > 0 && (
                <span className={styles.notiBadge}>{unreadCount > 99 ? '99+' : unreadCount}</span>
              )}
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

      {/* 메인 */}
      <main className={styles.main}>
        <div className={styles.topBar}>
          <h1 className={styles.pageTitle}>알림 이력</h1>
        </div>

        {/* 필터 바 */}
        <div className={styles.filterBar}>
          <label className={styles.filterLabel}>긴급 여부</label>
          <select
            className={styles.filterSelect}
            value={filters.is_urgent}
            onChange={e => setFilters(f => ({ ...f, is_urgent: e.target.value as Filters['is_urgent'] }))}
          >
            <option value="">전체</option>
            <option value="true">긴급</option>
            <option value="false">일반</option>
          </select>

          <label className={styles.filterLabel}>확인 여부</label>
          <select
            className={styles.filterSelect}
            value={filters.status}
            onChange={e => setFilters(f => ({ ...f, status: e.target.value as Filters['status'] }))}
          >
            <option value="">전체</option>
            <option value="PENDING">미확인</option>
            <option value="SENT">발송됨</option>
            <option value="READ">확인완료</option>
          </select>

          <span className={styles.totalCount}>총 {total.toLocaleString()}건</span>
        </div>

        {/* 테이블 */}
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className={styles.th}>긴급 여부</th>
                <th className={styles.th}>내용</th>
                <th className={styles.th}>장소</th>
                <th className={styles.th}>날씨</th>
                <th className={styles.th}>확인 여부</th>
                <th className={styles.th}>발생 시각</th>
                <th className={styles.th}>처리</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={7} className={styles.emptyCell}>불러오는 중...</td></tr>
              ) : merged.length === 0 ? (
                <tr><td colSpan={7} className={styles.emptyCell}>알림 이력이 없습니다.</td></tr>
              ) : merged.map(n => {
                const isUrgent     = URGENT_LEVELS.includes(n.risk_level)
                const isConfirmed  = n.is_confirmed
                const isResolved   = n.status === 'READ'
                return (
                  <tr
                    key={n.id}
                    className={`${styles.tr} ${isUrgent ? styles.trUrgent : ''} ${styles.trClickable}`}
                    onClick={() => handleRowClick(n)}
                  >
                    <td className={styles.td}>
                      {isUrgent
                        ? <span className={styles.badgeUrgent}>🚨 긴급</span>
                        : <span className={styles.badgeNormal}>일반</span>}
                    </td>
                    <td className={`${styles.td} ${styles.tdContent}`}>{n.title}</td>
                    <td className={styles.td}>{n.location_name}</td>
                    <td className={styles.td}>
                      <span className={styles.weatherBadge}>
                        {WEATHER_LABEL[n.weather_type] ?? n.weather_type}
                      </span>
                    </td>
                    <td className={styles.td} onClick={e => e.stopPropagation()}>
                      {isConfirmed
                        ? <button className={styles.confirmedBtn} onClick={() => handleUnconfirm(n.id)}>✅ 확인완료</button>
                        : <button className={styles.unconfirmedBtn} onClick={() => handleConfirm(n.id)}>⏳ 미확인</button>}
                    </td>
                    <td className={styles.td}>
                      {n.created_at
                        ? new Date(n.created_at).toLocaleString('ko-KR', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
                        : '-'}
                    </td>
                    {/* 버튼 셀: 클릭 이벤트가 행 클릭으로 전파되지 않도록 차단 */}
                    <td className={styles.td} onClick={e => e.stopPropagation()}>
                      {isResolved ? (
                        <button className={styles.cancelBtn} onClick={() => handleUnread(n.id)}>
                          취소
                        </button>
                      ) : (
                        <button className={styles.resolveBtn} onClick={() => handleRead(n.id)}>
                          처리완료
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>

        </div>

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div className={styles.pagination}>
            <button className={styles.pageBtn} disabled={page <= 1} onClick={() => setPage(p => p - 1)}>이전</button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const start = Math.max(1, page - 2)
              const num   = start + i
              if (num > totalPages) return null
              return (
                <button
                  key={num}
                  className={`${styles.pageBtn} ${num === page ? styles.pageBtnActive : ''}`}
                  onClick={() => setPage(num)}
                >
                  {num}
                </button>
              )
            })}
            <button className={styles.pageBtn} disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>다음</button>
          </div>
        )}
      </main>

      {/* 상세 모달 */}
      {modalOpen && (
        <NotificationModal
          detail={detail}
          loading={detailLoading}
          onClose={() => setModalOpen(false)}
          onRead={handleRead}
          onUnread={handleUnread}
        />
      )}
    </div>
  )
}
