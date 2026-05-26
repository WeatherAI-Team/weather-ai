'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './page.module.css'
import KakaoMap, { type RegionData } from '@/components/map/KakaoMap'

const sideMenus = [
  { label: '대시보드', href: '/admin', icon: '📊' },
  { label: '관제센터', href: '/admin/monitor', icon: '📡' },
  { label: '사용자관리', href: '/admin/users', icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info', icon: '📋' },
]

const API_URL = process.env.NEXT_PUBLIC_API_URL

type DetectionApiItem = {
  id: number
  location_name: string | null
  latitude: number | null
  longitude: number | null
  weather_type: string | null
  main_vehicle_type: string | null
  risk_level: string | null
  risk_vehicle_count: number | null
  total_vehicle_count: number | null
  event_status: string | null
  llm_title: string | null
  llm_summary: string | null
  detected_at: string | null
}

type EventItem = {
  id: number
  city: string; area: string; type: string; weather: string
  count: number; status: string; time: string
  llm_title: string | null; llm_summary: string | null
}
type LLMTarget = EventItem & { regionName: string }

const REGION_NAMES: Record<string, string> = {
  seoul: '서울특별시', gyeonggi: '경기도', gangwon: '강원도',
  chungbuk: '충청북도', chungnam: '충청남도', daejeon: '대전광역시',
  jeonbuk: '전라북도', gwangju: '광주광역시', jeonnam: '전라남도',
  gyeongbuk: '경상북도', daegu: '대구광역시', gyeongnam: '경상남도',
  ulsan: '울산광역시', busan: '부산광역시', jeju: '제주특별자치도',
}

// 특별시·광역시를 먼저 검사해 도(道) 범위에 흡수되지 않도록 순서 유지
const REGION_BOUNDS = [
  { id: 'seoul',     latMin: 37.41, latMax: 37.70, lngMin: 126.73, lngMax: 127.18 },
  { id: 'busan',     latMin: 35.05, latMax: 35.40, lngMin: 128.74, lngMax: 129.32 },
  { id: 'daegu',     latMin: 35.78, latMax: 35.98, lngMin: 128.45, lngMax: 128.73 },
  { id: 'daejeon',   latMin: 36.25, latMax: 36.48, lngMin: 127.32, lngMax: 127.55 },
  { id: 'gwangju',   latMin: 35.08, latMax: 35.27, lngMin: 126.74, lngMax: 127.00 },
  { id: 'ulsan',     latMin: 35.46, latMax: 35.65, lngMin: 128.94, lngMax: 129.43 },
  { id: 'jeju',      latMin: 33.10, latMax: 33.60, lngMin: 126.10, lngMax: 126.97 },
  { id: 'gyeonggi',  latMin: 36.90, latMax: 38.30, lngMin: 126.40, lngMax: 127.90 },
  { id: 'gangwon',   latMin: 37.00, latMax: 38.60, lngMin: 127.70, lngMax: 129.40 },
  { id: 'chungbuk',  latMin: 36.10, latMax: 37.20, lngMin: 127.30, lngMax: 128.50 },
  { id: 'chungnam',  latMin: 36.00, latMax: 37.10, lngMin: 125.90, lngMax: 127.30 },
  { id: 'jeonbuk',   latMin: 35.50, latMax: 36.10, lngMin: 126.30, lngMax: 127.80 },
  { id: 'jeonnam',   latMin: 33.90, latMax: 35.10, lngMin: 125.90, lngMax: 127.80 },
  { id: 'gyeongbuk', latMin: 35.60, latMax: 37.20, lngMin: 127.90, lngMax: 130.00 },
  { id: 'gyeongnam', latMin: 34.70, latMax: 35.60, lngMin: 127.50, lngMax: 129.50 },
]

function getRegionFromCoords(lat: number, lng: number): string | null {
  for (const b of REGION_BOUNDS) {
    if (lat >= b.latMin && lat <= b.latMax && lng >= b.lngMin && lng <= b.lngMax) return b.id
  }
  return null
}

const VEHICLE_TYPE_KO: Record<string, string> = {
  RMC: '래미콘',
  Gas_Truck: '탱크로리',
  cargo_truck: '카고트럭',
  '25t_truck': '25톤 이상의 차량',
}
const WEATHER_KO: Record<string, string> = {
  clear: '맑음', heavy_snow: '폭설', heavy_rain: '폭우', fog: '안개',
}

function toVehicleType(v: string | null) { return v ? (VEHICLE_TYPE_KO[v] ?? v) : '알 수 없음' }
function toWeather(w: string | null) { return w ? (WEATHER_KO[w] ?? w) : '알 수 없음' }
function toStatus(r: string | null) { return r === 'high' ? '위험' : '경고' }
function toTime(iso: string | null) { return iso ? iso.slice(11, 16) : '--:--' }

export default function MonitorPage() {
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const [regionData, setRegionData] = useState<RegionData>({})
  const [eventsByRegion, setEventsByRegion] = useState<Record<string, EventItem[]>>({})
  const [loading, setLoading] = useState(true)
  const [popupOpen, setPopupOpen] = useState(false)
  const [popupData, setPopupData] = useState<{ name: string; events: EventItem[] } | null>(null)
  const [llmTarget, setLlmTarget] = useState<LLMTarget | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const res  = await fetch(`${API_URL}/api/detections?per_page=200`)
        const json = await res.json()
        if (!json.success) throw new Error(json.message)

        const items: DetectionApiItem[] = json.data.items
        const buckets: Record<string, EventItem[]> = {}

        for (const e of items) {
          if (e.latitude == null || e.longitude == null) continue
          const regionId = getRegionFromCoords(e.latitude, e.longitude)
          if (!regionId) continue
          if (!buckets[regionId]) buckets[regionId] = []
          buckets[regionId].push({
            id:          e.id,
            city:        REGION_NAMES[regionId],
            area:        e.location_name ?? '위치 미상',
            type:        toVehicleType(e.main_vehicle_type),
            weather:     toWeather(e.weather_type),
            count:       e.risk_vehicle_count ?? e.total_vehicle_count ?? 1,
            status:      toStatus(e.risk_level),
            time:        toTime(e.detected_at),
            llm_title:   e.llm_title,
            llm_summary: e.llm_summary,
          })
        }

        setEventsByRegion(buckets)
        setRegionData(
          Object.fromEntries(
            Object.entries(buckets).map(([id, evs]) => [
              id, { name: REGION_NAMES[id], total: evs.length, events: [] },
            ])
          )
        )
      } catch (error) {
        console.error('[Monitor] 탐지 데이터 로드 실패:', error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const handleRegionSelect = (id: string) => {
    setSelected(id)
    const evs = eventsByRegion[id]
    if (evs?.length) {
      setPopupData({ name: REGION_NAMES[id] ?? id, events: evs })
      setPopupOpen(true)
    }
  }

  const handleEventClick = (event: EventItem, regionName: string) => {
    setLlmTarget({ ...event, regionName })
    setPopupOpen(false)
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.sideLogoWrap}>
          <Link href="/"><img src="/logo.png" alt="로고" height={36} /></Link>
        </div>
        <nav className={styles.sideNav}>
          {sideMenus.map((m) => (
            <Link key={m.href} href={m.href}
              className={`${styles.sideItem} ${pathname === m.href ? styles.sideActive : ''}`}>
              <span className={styles.sideIcon}>{m.icon}</span>{m.label}
            </Link>
          ))}
          <button className={`${styles.sideItem} ${styles.sideDropBtn}`} onClick={() => setBoardOpen(!boardOpen)}>
            <span className={styles.sideIcon}>📝</span>게시글
            <span className={`${styles.arrow} ${boardOpen ? styles.arrowOpen : ''}`}>▾</span>
          </button>
          {boardOpen && (
            <div className={styles.subMenu}>
              {boardMenus.map((m) => (
                <Link key={m.href} href={m.href} className={styles.subItem}>{m.icon} {m.label}</Link>
              ))}
            </div>
          )}
        </nav>
      </aside>

      <main className={styles.main}>
        <div className={styles.topBar}>
          <h1 className={styles.pageTitle}>관제센터</h1>
        </div>

        <div className={styles.contentRow}>
          {/* 지도 */}
          <div className={styles.mapPanel}>
            <div className={styles.mapHeader}>
              <span className={styles.mapTitle}>대한민국 지역별 탐지 현황</span>
              <span className={styles.liveBadge}>LIVE</span>
              <span className={styles.mapHint}>🖱️ 지역 클릭 시 팝업 표시</span>
            </div>
            <div className={styles.mapLegend}>
              {[['#20436d','20건+'],['#07559d','10~19건'],['#1b9bd1','5~9건'],['#81c4e2','1~4건'],['#dbeafe','0건']].map(([c,l]) => (
                <span key={l} className={styles.legendItem}>
                  <span className={styles.legendBox} style={{ background: c }}/>{l}
                </span>
              ))}
            </div>
            <div className={styles.mapArea}>
              {loading ? (
                <p className={styles.loadingText}>지도 데이터를 불러오는 중입니다...</p>
              ) : (
                <KakaoMap selected={selected} hovered={hovered} regionData={regionData}
                  onSelect={handleRegionSelect} onHover={setHovered} />
              )}
            </div>
          </div>

          {/* LLM 패널 */}
          <div className={styles.rightPanel}>

            {/* 위치 */}
            <div className={styles.infoSection}>
              <h3 className={styles.infoTitle}>위치</h3>
              <div className={styles.locationBox}>
                {llmTarget ? (
                  <p className={styles.locationText}>
                    {llmTarget.regionName} · {llmTarget.city} {llmTarget.area}
                  </p>
                ) : (
                  <p className={styles.locationEmpty}>지도에서 지역을 선택하세요</p>
                )}
              </div>
            </div>

            {/* LLM 정보 분석 결과 */}
            <div className={styles.infoSectionLarge}>
              <h3 className={styles.infoTitle}>🤖 LLM 정보 분석 결과</h3>
              <div className={styles.llmBox}>
                {llmTarget ? (
                  <>
                    <div className={styles.llmMeta}>
                      <span className={`${styles.llmBadge} ${llmTarget.status === '위험' ? styles.badgeDanger : styles.badgeWarn}`}>
                        {llmTarget.status === '위험' ? '🚨' : '⚠️'} {llmTarget.status}
                      </span>
                      <span className={styles.llmTime}>{llmTarget.time}</span>
                    </div>
                    <div className={styles.llmReport}>
                      {llmTarget.llm_summary
                        ? llmTarget.llm_summary.split('\n\n').map((p: string, i: number) => <p key={i}>{p}</p>)
                        : llmTarget.llm_title
                          ? <p>{llmTarget.llm_title}</p>
                          : <p>AI 분석 결과가 없습니다.</p>
                      }
                    </div>
                  </>
                ) : (
                  <p className={styles.locationEmpty}>사고 건수를 선택하면 AI 분석 결과가 표시됩니다</p>
                )}
              </div>
            </div>

            {/* 상세 패널 */}
            <div className={styles.infoSectionLarge}>
              <h3 className={styles.infoTitle}>상세 패널</h3>
              <div className={styles.detailBox}>
                {llmTarget ? (
                  <>
                    {[
                      ['차량 유형', llmTarget.type],
                      ['기상 조건', llmTarget.weather],
                      ['탐지 시각', llmTarget.time],
                      ['위험 등급', llmTarget.status],
                      ['사고 건수', `${llmTarget.count}건`],
                    ].map(([label, value]) => (
                      <div key={label} className={styles.detailRow}>
                        <span className={styles.detailLabel}>{label}</span>
                        <span className={`${styles.detailValue} ${label === '위험 등급' && llmTarget.status === '위험' ? styles.textDanger : label === '위험 등급' ? styles.textWarn : ''}`}>
                          {value}
                        </span>
                      </div>
                    ))}
                    <div className={styles.llmActions}>
                      <button className={styles.actionBtn}>📋 리포트 저장</button>
                      <button className={styles.actionBtnSecondary}>🔔 담당자 알림</button>
                    </div>
                  </>
                ) : (
                  <p className={styles.locationEmpty}>상세 정보가 여기에 표시됩니다</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 팝업 */}
      {popupOpen && popupData && (
        <div className={styles.popupOverlay} onClick={() => setPopupOpen(false)}>
          <div className={styles.popup} onClick={(e) => e.stopPropagation()}>
            <div className={styles.popupHeader}>
              <h2 className={styles.popupTitle}>{popupData.name}</h2>
              <button className={styles.popupClose} onClick={() => setPopupOpen(false)}>✕</button>
            </div>
            <p className={styles.popupDesc}>건수를 클릭하면 AI 분석 보고서가 표시됩니다</p>
            {popupData.events.length > 0 ? (
              <div className={styles.popupList}>
                {popupData.events.map((e, i) => (
                  <button key={i} className={styles.popupItem}
                    onClick={() => handleEventClick(e, popupData.name)}>
                    <div className={styles.popupItemLeft}>
                      <span className={`${styles.popupDot} ${e.status === '위험' ? styles.dotDanger : styles.dotWarn}`}/>
                      <div>
                        <p className={styles.popupItemArea}>{e.city} · {e.area}</p>
                        <p className={styles.popupItemMeta}>🚛 {e.type} · 🌧️ {e.weather} · ⏰ {e.time}</p>
                      </div>
                    </div>
                    <span className={`${styles.popupCount} ${e.status === '위험' ? styles.countDanger : styles.countWarn}`}>
                      {e.count}건 →
                    </span>
                  </button>
                ))}
              </div>
            ) : (
              <p className={styles.popupEmpty}>등록된 사고 정보가 없습니다.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
