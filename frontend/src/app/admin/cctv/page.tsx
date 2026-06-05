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

function HlsPlayer({ src, className }: { src: string; className?: string }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  useEffect(() => {
    const video = videoRef.current
    if (!video || !src) return
    let hls: Hls | null = null
    if (Hls.isSupported()) {
      hls = new Hls()
      hls.loadSource(src)
      hls.attachMedia(video)
      hls.on(Hls.Events.MANIFEST_PARSED, () => { video.play().catch(() => {}) })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.play().catch(() => {})
    }
    return () => { hls?.destroy() }
  }, [src])
  return <video ref={videoRef} className={className} autoPlay muted playsInline controls />
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
    fetch(`${API_URL}/api/cctv`)
      .then(r => r.json())
      .then(data => setCctvList(data?.response?.data ?? []))
      .catch(() => {})
      .finally(() => setLoading(false))
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
            <span className={styles.sideIcon}>📝</span>게시글 관리
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
                          <HlsPlayer key={cam.cctvurl} src={streamUrl(cam)} className={styles.videoCellStream} />
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
