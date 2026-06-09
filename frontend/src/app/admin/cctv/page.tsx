'use client'

import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './page.module.css'
import { useNotification } from '@/contexts/NotificationContext'

const API_URL = process.env.NEXT_PUBLIC_API_URL

type CctvItem = {
  cctvname: string
  cctvurl: string
  cctvformat: string
  coordx: number
  coordy: number
}

const sideMenus = [
  { label: '대시보드',   href: '/admin',               icon: '📊' },
  { label: 'AI 관제센터', href: '/admin/monitor',        icon: '📡' },
  { label: 'CCTV 모니터링', href: '/admin/cctv',           icon: '📷' },
  { label: '알림이력',   href: '/admin/notifications',  icon: '🔔' },
  { label: '사용자관리', href: '/admin/users',           icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info',    icon: '📋' },
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

function HlsPlayer({
  src,
  className,
  onStreamError,
}: {
  // 재생할 CCTV 주소야.
  src: string

  // 기존 CSS 클래스야.
  className?: string

  // CCTV 재생 실패 시 부모에게 알려주는 함수야.
  onStreamError?: () => void
}) {
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

    // 부모 컴포넌트에게 이 CCTV가 실패했다고 알려줘.
    onStreamError?.()
  }

    // 15초 안에 영상이 준비되지 않으면 실패로 바꿔.
    // 단, hls에서 조각을 받으면 markPlaying이 먼저 실행돼서 로딩은 꺼져.
    const failTimer = window.setTimeout(() => {
      markError()
    }, 8000)

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

export default function CctvPage() {
  useEffect(() => { document.title = 'Weather AI - CCTV 모니터링' }, [])
  const pathname = usePathname()
  const { unreadCount } = useNotification()
  const [boardOpen, setBoardOpen] = useState(false)
  const [cctvList, setCctvList] = useState<CctvItem[]>([])
  const [loading, setLoading] = useState(true)
  const [splitMode, setSplitMode] = useState<1 | 4>(1)
  const [selectedIdxs, setSelectedIdxs] = useState<(number | null)[]>([null, null, null, null])
  const [activeSlot, setActiveSlot] = useState(0)
  const [expandedRegions, setExpandedRegions] = useState<Set<string>>(new Set())

  useEffect(() => {
    const load = () => {
      fetch(`${API_URL}/api/cctv`)
        .then(r => r.json())
        .then(data => setCctvList(data?.response?.data ?? []))
        .catch(() => {})
        .finally(() => setLoading(false))
    }
    load()
    const timer = setInterval(load, 50000) // 50초마다 새 URL 발급
    return () => clearInterval(timer)
  }, [])

  const cctvByRegion: Record<string, CctvItem[]> = {}
  const cctvNoRegion: CctvItem[] = []
  for (const c of cctvList) {
    const rid = getRegionFromCoords(c.coordy, c.coordx)
    if (rid) {
      if (!cctvByRegion[rid]) cctvByRegion[rid] = []
      cctvByRegion[rid].push(c)
    } else {
      cctvNoRegion.push(c)
    }
  }

  const toggleRegion = (rid: string) => {
    setExpandedRegions(prev => {
      const next = new Set(prev)
      if (next.has(rid)) next.delete(rid); else next.add(rid)
      return next
    })
  }

  const handleCctvSelect = (globalIdx: number) => {
    if (splitMode === 1) {
      setSelectedIdxs([globalIdx, null, null, null])
    } else {
      const next = [...selectedIdxs]
      next[activeSlot] = globalIdx
      setSelectedIdxs(next)
      setActiveSlot((activeSlot + 1) % 4)  
    }
  }

  const replaceFailedCctv = (slot: number, failedIdx: number) => {
    let nextIdx = failedIdx + 1
    while (nextIdx < cctvList.length) {
      if (!selectedIdxs.includes(nextIdx)) {
        const next = [...selectedIdxs]
        next[slot] = nextIdx
        setSelectedIdxs(next)
        return
      }
      nextIdx += 1
    }
  }

  const streamUrl = (cam: CctvItem) =>
    `${API_URL}/api/cctv/stream?url=${encodeURIComponent(cam.cctvurl)}`

  const regionEntries = Object.entries(cctvByRegion)

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
          <div className={styles.topBarLeft}>
            <h1 className={styles.pageTitle}>CCTV 모니터링</h1>
            <span className={styles.liveBadge}>LIVE</span>
            <div className={styles.splitToggle}>
              <button
                className={`${styles.splitBtn} ${splitMode === 1 ? styles.splitBtnActive : ''}`}
                onClick={() => setSplitMode(1)}
              >1분할</button>
              <button
                className={`${styles.splitBtn} ${splitMode === 4 ? styles.splitBtnActive : ''}`}
                onClick={() => setSplitMode(4)}
              >4분할</button>
            </div>
          </div>
          <div />
        </div>

        <div className={styles.contentRow}>
          {/* 좌측: 영상 */}
          <div className={styles.videoPanel}>
            {splitMode === 1 ? (
              <div className={styles.videoBox}>
                {selectedIdxs[0] !== null && cctvList[selectedIdxs[0]!] ? (
                  <>
                    <HlsPlayer
                      key={cctvList[selectedIdxs[0]!].cctvurl}
                      src={streamUrl(cctvList[selectedIdxs[0]!])}
                      className={styles.videoStream}
                    />
                    <div className={styles.videoLabel}>{cctvList[selectedIdxs[0]!].cctvname}</div>
                  </>
                ) : (
                  <div className={styles.videoEmpty}>
                    <span>📷</span>
                    <p>우측 목록에서 CCTV를 선택하세요</p>
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.videoGrid4}>
                {[0, 1, 2, 3].map((slot) => {
                  const idx = selectedIdxs[slot]
                  const cam = idx !== null ? cctvList[idx] : null
                  return (
                    <div
                      key={slot}
                      className={`${styles.videoCell} ${activeSlot === slot ? styles.videoCellActive : ''}`}
                      onClick={() => setActiveSlot(slot)}
                    >
                     {cam ? (
                        <>
                          <HlsPlayer
                            key={`slot-${slot}-${idx}`}
                            src={streamUrl(cam)}
                            className={styles.videoCellStream}
                            onStreamError={() => replaceFailedCctv(slot, selectedIdxs[slot]!)}
                          />
                          <div className={styles.videoCellLabel}>{cam.cctvname}</div>
                        </>
                      ) : (
                        <div className={styles.videoEmpty}>
                          <span>📷</span>
                          <p>슬롯 {slot + 1}</p>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* 우측: CCTV 목록 */}
          <div className={styles.listPanel}>
            <div className={styles.listHeader}>
              <span className={styles.listTitle}>CCTV 연동 목록</span>
              <span className={styles.listCount}>{cctvList.length}개</span>
            </div>
            {splitMode === 4 && (
              <div className={styles.slotGuide}>
                클릭 시 <strong>슬롯 {activeSlot + 1}</strong>에 표시됩니다
              </div>
            )}
            <div className={styles.regionList}>
              {loading ? (
                <p className={styles.emptyText}>목록을 불러오는 중...</p>
              ) : cctvList.length === 0 ? (
                <p className={styles.emptyText}>연동된 CCTV가 없습니다</p>
              ) : (
                <>
                  {regionEntries.map(([rid, cams]) => (
                    <div key={rid} className={styles.regionGroup}>
                      <button className={styles.regionHeader} onClick={() => toggleRegion(rid)}>
                        <span className={styles.regionName}>{REGION_NAMES[rid] ?? rid}</span>
                        <span className={styles.regionCount}>{cams.length}</span>
                        <span className={`${styles.regionArrow} ${expandedRegions.has(rid) ? styles.arrowOpen : ''}`}>▾</span>
                      </button>
                      {expandedRegions.has(rid) && (
                        <div className={styles.regionCams}>
                          {cams.map((cam, i) => {
                            const globalIdx = cctvList.indexOf(cam)
                            const isActive = selectedIdxs.includes(globalIdx)
                            return (
                              <button
                                key={i}
                                className={`${styles.camItem} ${isActive ? styles.camItemActive : ''}`}
                                onClick={() => handleCctvSelect(globalIdx)}
                              >
                                <span className={styles.camDot} />
                                <div className={styles.camInfo}>
                                  <p className={styles.camName}>{cam.cctvname}</p>
                                  <p className={styles.camMeta}>{cam.cctvformat}</p>
                                </div>
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                  {cctvNoRegion.length > 0 && (
                    <div className={styles.regionGroup}>
                      <button className={styles.regionHeader} onClick={() => toggleRegion('__etc__')}>
                        <span className={styles.regionName}>기타</span>
                        <span className={styles.regionCount}>{cctvNoRegion.length}</span>
                        <span className={`${styles.regionArrow} ${expandedRegions.has('__etc__') ? styles.arrowOpen : ''}`}>▾</span>
                      </button>
                      {expandedRegions.has('__etc__') && (
                        <div className={styles.regionCams}>
                          {cctvNoRegion.map((cam, i) => {
                            const globalIdx = cctvList.indexOf(cam)
                            const isActive = selectedIdxs.includes(globalIdx)
                            return (
                              <button
                                key={i}
                                className={`${styles.camItem} ${isActive ? styles.camItemActive : ''}`}
                                onClick={() => handleCctvSelect(globalIdx)}
                              >
                                <span className={styles.camDot} />
                                <div className={styles.camInfo}>
                                  <p className={styles.camName}>{cam.cctvname}</p>
                                  <p className={styles.camMeta}>{cam.cctvformat}</p>
                                </div>
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
