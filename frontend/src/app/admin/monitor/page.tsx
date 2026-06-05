'use client'

import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './page.module.css'
import KakaoMap, { type RegionData } from '@/components/map/KakaoMap'
import { useNotification } from '@/contexts/NotificationContext'
import { useModalKeyboard } from '@/hooks/useModalKeyboard'

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
type LLMTarget = EventItem & { regionName: string; regionId: string }

type CctvItem = {
  cctvname: string
  cctvurl: string
  cctvformat: string
  coordx: number
  coordy: number
}

const sideMenus = [
  { label: '대시보드',  href: '/admin',                icon: '📊' },
  { label: 'AI 관제센터',  href: '/admin/monitor',         icon: '📡' },
  { label: 'CCTV 모니터링', href: '/admin/cctv',            icon: '📷' },
  { label: '알림이력',  href: '/admin/notifications',   icon: '🔔' },
  { label: '사용자관리', href: '/admin/users',           icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info', icon: '📋' },
]

const REGION_NAMES: Record<string, string> = {
  seoul: '서울특별시', gyeonggi: '경기도', gangwon: '강원도',
  chungbuk: '충청북도', chungnam: '충청남도', daejeon: '대전광역시',
  jeonbuk: '전라북도', gwangju: '광주광역시', jeonnam: '전라남도',
  gyeongbuk: '경상북도', daegu: '대구광역시', gyeongnam: '경상남도',
  ulsan: '울산광역시', busan: '부산광역시', jeju: '제주특별자치도',
}

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
  rmc: '레미콘', gas_truck: '탱크로리', cargo_truck: '카고트럭',
}
const WEATHER_KO: Record<string, string> = {
  clear: '맑음', heavy_snow: '폭설', heavy_rain: '폭우', fog: '안개',
}

function toVehicleType(v: string | null) { return v ? (VEHICLE_TYPE_KO[v.toLowerCase()] ?? '차량') : '알 수 없음' }
function toWeather(w: string | null) { return w ? (WEATHER_KO[w] ?? w) : '알 수 없음' }
function toStatus(r: string | null) { return r === 'high' ? '위험' : '경고' }
function toTime(iso: string | null) { return iso ? iso.slice(11, 16) : '--:--' }

function HlsPlayer({ src, className }: { src: string; className?: string }) {
  // 실제 video 태그를 제어하기 위한 공간이야.
  const videoRef = useRef<HTMLVideoElement>(null)

  // hls 객체를 저장해두는 공간이야.
  const hlsRef = useRef<Hls | null>(null)

  // 현재 CCTV 영상 상태야.
  // loading: 처음 불러오는 중
  // playing: 영상 표시 중
  // error: 영상 연결 실패
  const [videoStatus, setVideoStatus] = useState<'loading' | 'playing' | 'error'>('loading')

  // 다시 불러오기 버튼을 눌렀을 때 useEffect를 다시 실행시키기 위한 숫자야.
  const [reloadKey, setReloadKey] = useState(0)

  useEffect(() => {
    // video 태그를 가져와.
    const video = videoRef.current

    // video 태그가 없으면 아무것도 하지 않아.
    if (!video) return

    // CCTV 주소가 없으면 실패 처리해.
    if (!src) {
      setVideoStatus('error')
      return
    }

    // 새 CCTV를 불러올 때는 로딩 상태로 시작해.
    setVideoStatus('loading')

    // 기존 hls 연결이 있으면 먼저 정리해.
    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }

    // 이전 영상이 남아 보이지 않게 비워줘.
    video.pause()
    video.removeAttribute('src')
    video.load()

    // 이미 실패 처리됐는지 확인하기 위한 값이야.
    let isFinished = false

    // 로딩을 끄고 재생 상태로 바꾸는 함수야.
    const markPlaying = () => {
      // 이미 실패/정리된 상태면 아무것도 하지 않아.
      if (isFinished) return

      // 영상이 보이기 시작했다고 판단해서 로딩 화면을 꺼.
      setVideoStatus('playing')
    }

    // 실패 화면으로 바꾸는 함수야.
    const markError = () => {
      // 이미 처리됐으면 또 처리하지 않아.
      if (isFinished) return

      // 실패 처리 완료 표시야.
      isFinished = true

      // 실패 화면을 보여줘.
      setVideoStatus('error')
    }

    // 15초 안에 영상이 준비되지 않으면 실패로 바꿔.
    // 단, hls에서 조각을 받으면 markPlaying이 먼저 실행돼서 로딩은 꺼져.
    const failTimer = window.setTimeout(() => {
      markError()
    }, 15000)

    // 재생 상태가 되면 실패 타이머를 꺼주는 함수야.
    const markPlayingAndClearTimer = () => {
      window.clearTimeout(failTimer)
      markPlaying()
    }

    // video 태그에서 영상 준비/재생 이벤트가 오면 로딩을 꺼.
    video.onloadedmetadata = markPlayingAndClearTimer
    video.onloadeddata = markPlayingAndClearTimer
    video.oncanplay = markPlayingAndClearTimer
    video.onplaying = markPlayingAndClearTimer

    // video 태그 자체에서 에러가 나면 실패 화면을 보여줘.
    video.onerror = markError

    if (Hls.isSupported()) {
      // hls 객체를 만들어.
      const hls = new Hls({
        // m3u8 목록 로딩 제한 시간이야.
        manifestLoadingTimeOut: 10000,

        // ts 영상 조각 로딩 제한 시간이야.
        fragLoadingTimeOut: 10000,

        // 재시도를 너무 오래 하지 않게 제한해.
        manifestLoadingMaxRetry: 1,
        fragLoadingMaxRetry: 1,

        // 재시도 간격이야.
        manifestLoadingRetryDelay: 1000,
        fragLoadingRetryDelay: 1000,
      })

      // 나중에 정리할 수 있게 저장해.
      hlsRef.current = hls

      // CCTV 주소를 hls에 넣어.
      hls.loadSource(src)

      // hls를 video 태그와 연결해.
      hls.attachMedia(video)

      // m3u8을 읽으면 재생을 시도해.
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        // m3u8을 읽은 시점에도 로딩을 꺼줘.
        // CCTV는 실제 영상이 살짝 늦게 붙어도 검은 로딩이 계속 덮이는 것보다 이게 나아.
        markPlayingAndClearTimer()

        video.play().catch(() => {
          // 자동재생이 막혀도 controls가 있어서 사용자가 재생할 수 있어.
        })
      })

      // 영상 조각 하나라도 받아오면 로딩을 꺼.
      // 지금 정화 화면처럼 영상은 나오는데 로딩이 남는 문제를 잡는 핵심이야.
      hls.on(Hls.Events.FRAG_LOADED, () => {
        markPlayingAndClearTimer()
      })

      // 영상 조각이 버퍼에 들어가도 로딩을 꺼.
      hls.on(Hls.Events.FRAG_BUFFERED, () => {
        markPlayingAndClearTimer()
      })

      // hls 에러 처리야.
      hls.on(Hls.Events.ERROR, (_, data) => {
        console.log('[HLS 에러]', data)

        // 치명적이지 않은 에러는 무시해.
        // 실시간 CCTV는 작은 버퍼 에러가 자주 날 수 있어.
        if (!data.fatal) return

        // 미디어 에러는 복구를 한 번 시도해.
        if (data.type === Hls.ErrorTypes.MEDIA_ERROR) {
          hls.recoverMediaError()
          return
        }

        // 네트워크 fatal 에러는 실패 화면으로 바꿔.
        markError()
      })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Safari처럼 HLS를 기본 지원하는 브라우저용 코드야.
      video.src = src
      video.play().catch(() => {})
    } else {
      // HLS를 지원하지 않는 브라우저면 실패 처리해.
      markError()
    }

    // CCTV가 바뀌거나 컴포넌트가 사라질 때 정리해.
    return () => {
      isFinished = true
      window.clearTimeout(failTimer)

      video.onloadedmetadata = null
      video.onloadeddata = null
      video.oncanplay = null
      video.onplaying = null
      video.onerror = null

      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }
    }
  }, [src, reloadKey])

  // 다시 불러오기 버튼을 눌렀을 때 실행돼.
  const handleRetry = () => {
    setVideoStatus('loading')
    setReloadKey((prev) => prev + 1)
  }

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', background: '#000' }}>
      {videoStatus === 'loading' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.35)',
            color: '#fff',
            fontSize: '14px',
            fontWeight: 600,
            pointerEvents: 'none',
          }}
        >
          CCTV 영상 로딩 중...
        </div>
      )}

      {videoStatus === 'error' && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.82)',
            color: '#fff',
            textAlign: 'center',
            padding: '16px',
          }}
        >
          <div>
            <p style={{ margin: '0 0 8px', fontSize: '14px', fontWeight: 700 }}>
              CCTV 영상 연결 실패
            </p>
            <p style={{ margin: '0 0 12px', fontSize: '12px', opacity: 0.75 }}>
              원본 CCTV 서버가 응답하지 않거나 접근을 거부했습니다.
            </p>
            <button
              type="button"
              onClick={handleRetry}
              style={{
                border: 'none',
                borderRadius: '8px',
                padding: '8px 12px',
                background: '#fff',
                color: '#111',
                fontSize: '12px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              다시 불러오기
            </button>
          </div>
        </div>
      )}

      <video
        ref={videoRef}
        className={className}
        autoPlay
        muted
        playsInline
        controls
      />
    </div>
  )
}

export default function MonitorPage() {
  useEffect(() => { document.title = 'Weather AI - AI 관제센터' }, [])
  const pathname = usePathname()
  const { unreadCount } = useNotification()
  const [boardOpen, setBoardOpen] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const [regionData, setRegionData] = useState<RegionData>({})
  const [eventsByRegion, setEventsByRegion] = useState<Record<string, EventItem[]>>({})
  const [loading, setLoading] = useState(true)
  const [popupOpen, setPopupOpen] = useState(false)
  const [popupData, setPopupData] = useState<{ name: string; events: EventItem[] } | null>(null)

  useModalKeyboard(popupOpen, () => setPopupOpen(false))
  const [llmTarget, setLlmTarget] = useState<LLMTarget | null>(null)

  const [cctvList, setCctvList] = useState<CctvItem[]>([])
  const [leftTab, setLeftTab] = useState<'map' | 'cctv'>('map')
  const [leftCctvIdx, setLeftCctvIdx] = useState<number | null>(null)


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
            id: e.id, city: REGION_NAMES[regionId], area: e.location_name ?? '위치 미상',
            type: toVehicleType(e.main_vehicle_type), weather: toWeather(e.weather_type),
            count: e.risk_vehicle_count ?? e.total_vehicle_count ?? 1,
            status: toStatus(e.risk_level), time: toTime(e.detected_at),
            llm_title: e.llm_title, llm_summary: e.llm_summary,
          })
        }
        setEventsByRegion(buckets)
        setRegionData(Object.fromEntries(
          Object.entries(buckets).map(([id, evs]) => [id, { name: REGION_NAMES[id], total: evs.length, events: [] }])
        ))
      } catch (error) {
        console.error('[Monitor] 탐지 데이터 로드 실패:', error)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  useEffect(() => {
    fetch(`${API_URL}/api/cctv`)
      .then(r => r.json())
      .then(data => setCctvList(data?.response?.data ?? []))
      .catch(() => {})
  }, [])

  const leftCctvs: CctvItem[] = (() => {
    const regionId = llmTarget?.regionId || selected
    if (!regionId) return []
    const filtered = cctvList.filter(c => getRegionFromCoords(c.coordy, c.coordx) === regionId)
    return llmTarget ? filtered.slice(0, llmTarget.count) : filtered
  })()

  const handleRegionSelect = (id: string) => {
    setSelected(id)
    setLeftCctvIdx(0)
    const evs = eventsByRegion[id]
    if (evs?.length) {
      setPopupData({ name: REGION_NAMES[id] ?? id, events: evs })
      setPopupOpen(true)
    }
  }

  const handleEventClick = (event: EventItem, regionName: string) => {
    setLlmTarget({ ...event, regionName, regionId: selected ?? '' })
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
              {m.href === '/admin/notifications' && unreadCount > 0 && (
                <span className={styles.notiBadge}>{unreadCount > 99 ? '99+' : unreadCount}</span>
              )}
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
          <h1 className={styles.pageTitle}>AI 관제센터</h1>
        </div>

        <div className={styles.contentRow}>
          {/* ── 좌측: 지도 / CCTV 탭 ── */}
          <div className={styles.mapPanel}>
            <div className={styles.mapHeader}>
              <span className={styles.mapTitle}>대한민국 지역별 탐지 현황</span>
              <span className={styles.liveBadge}>LIVE</span>
              {leftTab === 'map' && <span className={styles.mapHint}>🖱️ 지역 클릭 시 팝업 표시</span>}
              <div className={styles.mapTabs}>
                <button
                  className={`${styles.mapTab} ${leftTab === 'map' ? styles.mapTabActive : ''}`}
                  onClick={() => setLeftTab('map')}
                >🗺️ 지도</button>
                <button
                  className={`${styles.mapTab} ${leftTab === 'cctv' ? styles.mapTabActive : ''}`}
                  onClick={() => setLeftTab('cctv')}
                >📷 CCTV</button>
              </div>
            </div>

            {leftTab === 'map' && (
              <div className={styles.mapLegend}>
                {[['#20436d','20건+'],['#07559d','10~19건'],['#1b9bd1','5~9건'],['#81c4e2','1~4건'],['#dbeafe','0건']].map(([c,l]) => (
                  <span key={l} className={styles.legendItem}>
                    <span className={styles.legendBox} style={{ background: c }}/>{l}
                  </span>
                ))}
              </div>
            )}

            {leftTab === 'map' ? (
              <div className={styles.mapArea}>
                {loading ? (
                  <p className={styles.loadingText}>지도 데이터를 불러오는 중입니다...</p>
                ) : (
                  <KakaoMap selected={selected} hovered={hovered} regionData={regionData}
                    onSelect={handleRegionSelect} onHover={setHovered} />
                )}
              </div>
            ) : (
              <div className={styles.cctvPanel}>
                <div className={styles.cctvPlayerBox}>
                  {leftCctvIdx !== null && leftCctvs[leftCctvIdx] ? (
                    <HlsPlayer
                      key={leftCctvs[leftCctvIdx].cctvurl}
                      src={`${API_URL}/api/cctv/stream?url=${encodeURIComponent(leftCctvs[leftCctvIdx].cctvurl)}`}
                      className={styles.cctvStream}
                    />
                  ) : (
                    <div className={styles.cctvEmpty}>
                      <span>📷</span>
                      <p>{selected ? '이 지역의 연동된 CCTV가 없습니다' : '지도 탭에서 지역을 선택하세요'}</p>
                    </div>
                  )}
                </div>
                {leftCctvs.length > 0 && (
                  <div className={styles.cctvList}>
                    <p className={styles.cctvListTitle}>
                      {selected ? `${REGION_NAMES[selected]} CCTV (${leftCctvs.length}개)` : '연동 CCTV 목록'}
                    </p>
                    {leftCctvs.map((cam, i) => (
                      <button
                        key={i}
                        className={`${styles.cctvItem} ${leftCctvIdx === i ? styles.cctvItemActive : ''}`}
                        onClick={() => setLeftCctvIdx(i)}
                      >
                        <span className={styles.cctvDotGreen} />
                        <div>
                          <p className={styles.cctvItemName}>{cam.cctvname}</p>
                          <p className={styles.cctvItemMeta}>{cam.cctvformat} · {cam.coordy}, {cam.coordx}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* ── 우측: LLM + CCTV ── */}
          <div className={styles.rightPanel}>

            {/* 위치 */}
            <div className={styles.infoSection}>
              <h3 className={styles.infoTitle}>위치</h3>
              <div className={styles.locationBox}>
                {llmTarget ? (
                  <p className={styles.locationText}>{llmTarget.regionName} · {llmTarget.city} {llmTarget.area}</p>
                ) : (
                  <p className={styles.locationEmpty}>지도에서 지역을 선택하세요</p>
                )}
              </div>
            </div>

            {/* LLM 분석 결과 */}
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
                        <p className={styles.popupItemMeta}>🚛 {e.type} · {e.weather === 'CLEAR' ? '☀️' : e.weather === 'SNOW' ? '🌨️' : (e.weather === 'HEAVY_RAIN' || e.weather === 'RAIN') ? '🌧️' : '🌤️'} {e.weather} · ⏰ {e.time}</p>
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
