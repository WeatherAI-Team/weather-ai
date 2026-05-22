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

const getLLMReport = (city: string, area: string, type: string, weather: string, count: number) =>
  `${city} ${area} 구간에서 ${weather} 기상 조건 하에 ${type} 차량이 총 ${count}건 탐지되었습니다.\n\n해당 기상 조건은 시야 확보를 어렵게 하며 노면 마찰력을 저하시켜 위험물질 운반 차량의 사고 위험을 크게 높입니다. 특히 ${type}의 경우 급제동 시 적재물 쏠림 현상이 발생할 수 있으며, 충돌 시 위험물질 유출로 인한 2차 피해가 우려됩니다.\n\n즉각적인 해당 구간 모니터링 강화와 담당 기관 통보가 필요하며, 필요 시 차량 통행 제한 조치를 검토하시기 바랍니다.`

type EventItem = {
  city: string; area: string; type: string; weather: string
  count: number; status: string; time: string
}
type LLMTarget = EventItem & { regionName: string }

export default function MonitorPage() {
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(false)
  const [selected, setSelected] = useState<string | null>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  const [regionData, setRegionData] = useState<RegionData>({})
  const [loading, setLoading] = useState(true)
  const [popupOpen, setPopupOpen] = useState(false)
  const [popupData, setPopupData] = useState<{ name: string; events: EventItem[] } | null>(null)
  const [llmTarget, setLlmTarget] = useState<LLMTarget | null>(null)


  useEffect(() => {
    async function fetchRegionData() {
      try {
        // 임시 더미 데이터 (API 연결 전까지 사용)
        const dummyData: RegionData = {
          seoul: { name: '서울특별시', total: 12, events: [
            { city: '서울시', area: '강남구', type: 'LPG 화물차', weather: '폭설', count: 3, status: '위험', time: '11:05' },
            { city: '서울시', area: '송파구', type: '탱크로리', weather: '폭우', count: 2, status: '경고', time: '09:20' },
          ]},
          gyeonggi: { name: '경기도', total: 24, events: [
            { city: '수원시', area: '경부고속도로 상행', type: '탱크로리', weather: '폭우', count: 5, status: '위험', time: '14:22' },
            { city: '성남시', area: '중부고속도로 하행', type: '화학물질 탱크', weather: '안개', count: 3, status: '경고', time: '09:40' },
          ]},
          gangwon: { name: '강원도', total: 8, events: [
            { city: '춘천시', area: '중앙고속도로', type: 'LPG 화물차', weather: '폭설', count: 2, status: '위험', time: '13:10' },
            { city: '강릉시', area: '동해고속도로', type: '탱크로리', weather: '강풍', count: 3, status: '경고', time: '10:30' },
          ]},
          chungbuk: { name: '충청북도', total: 6, events: [
            { city: '청주시', area: '경부고속도로', type: '화학물질 탱크', weather: '폭우', count: 2, status: '경고', time: '12:00' },
            { city: '충주시', area: '중부내륙고속도로', type: '탱크로리', weather: '안개', count: 1, status: '경고', time: '07:50' },
          ]},
          chungnam: { name: '충청남도', total: 5, events: [
            { city: '천안시', area: '천안논산고속도로', type: 'LPG 화물차', weather: '폭우', count: 2, status: '위험', time: '11:40' },
            { city: '아산시', area: '서해안고속도로', type: '탱크로리', weather: '강풍', count: 1, status: '경고', time: '09:00' },
          ]},
          daejeon: { name: '대전광역시', total: 4, events: [
            { city: '대전시', area: '경부고속도로', type: '탱크로리', weather: '안개', count: 2, status: '경고', time: '09:30' },
          ]},
          jeonbuk: { name: '전라북도', total: 4, events: [
            { city: '전주시', area: '호남고속도로', type: '화학물질 탱크', weather: '폭우', count: 2, status: '경고', time: '10:20' },
          ]},
          jeonnam: { name: '전라남도', total: 3, events: [
            { city: '순천시', area: '남해고속도로', type: '탱크로리', weather: '안개', count: 1, status: '경고', time: '08:30' },
          ]},
          gyeongbuk: { name: '경상북도', total: 9, events: [
            { city: '포항시', area: '동해고속도로', type: 'LPG 화물차', weather: '강풍', count: 3, status: '위험', time: '13:45' },
            { city: '구미시', area: '경부고속도로', type: '탱크로리', weather: '폭우', count: 2, status: '경고', time: '11:00' },
          ]},
          daegu: { name: '대구광역시', total: 5, events: [
            { city: '대구시', area: '경부고속도로', type: '화학물질 탱크', weather: '폭우', count: 2, status: '경고', time: '11:20' },
          ]},
          gyeongnam: { name: '경상남도', total: 7, events: [
            { city: '창원시', area: '남해고속도로', type: '화학물질 탱크', weather: '폭우', count: 3, status: '위험', time: '12:30' },
            { city: '진주시', area: '대전통영고속도로', type: '탱크로리', weather: '안개', count: 2, status: '경고', time: '09:15' },
          ]},
          ulsan: { name: '울산광역시', total: 4, events: [
            { city: '울산시', area: '울산고속도로', type: '탱크로리', weather: '강풍', count: 2, status: '위험', time: '14:10' },
          ]},
          busan: { name: '부산광역시', total: 6, events: [
            { city: '부산시', area: '부산외곽순환', type: 'LPG 화물차', weather: '폭우', count: 2, status: '위험', time: '14:00' },
            { city: '부산시', area: '남해고속도로', type: '탱크로리', weather: '강풍', count: 2, status: '경고', time: '10:45' },
          ]},
          jeju: { name: '제주특별자치도', total: 2, events: [
            { city: '제주시', area: '제주일주도로', type: 'LPG 화물차', weather: '강풍', count: 1, status: '경고', time: '13:00' },
          ]},
        }

        setRegionData(dummyData)

        // 실제 API 연결 시 아래 주석 해제
        // const res = await fetch('/api/monitor/regions', { cache: 'no-store' })
        // if (!res.ok) throw new Error('데이터 로드 실패')
        // const data: RegionData = await res.json()
        // setRegionData(data)

      } catch (error) {
        console.error(error)
      } finally {
        setLoading(false)
      }
    }
    fetchRegionData()
  }, [])

  // useEffect(() => {
  //   async function fetchRegionData() {
  //     try {
  //       const res = await fetch('/api/monitor/regions', { cache: 'no-store' })
  //       if (!res.ok) throw new Error('데이터 로드 실패')
  //       const data: RegionData = await res.json()
  //       setRegionData(data)
  //     } catch (error) {
  //       console.error(error)
  //     } finally {
  //       setLoading(false)
  //     }
  //   }
  //   fetchRegionData()
  // }, [])

  const handleRegionSelect = (id: string) => {
    setSelected(id)
    const data = regionData[id]
    if (data) {
      setPopupData({ name: data.name, events: data.events })
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
                      {getLLMReport(llmTarget.city, llmTarget.area, llmTarget.type, llmTarget.weather, llmTarget.count)
                        .split('\n\n').map((p, i) => <p key={i}>{p}</p>)}
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
