'use client'
import { useEffect, useRef, useState } from 'react'
import styles from './KakaoMap.module.css'

declare global {
  interface Window { kakao: any }
}

export type EventStatus = '위험' | '경고'

export type AccidentEvent = {
  city: string
  area: string
  type: string
  weather: string
  count: number
  status: EventStatus
  time: string
}

export type RegionInfo = {
  name: string
  total: number
  events: AccidentEvent[]
}

export type RegionData = Record<string, RegionInfo>

type KakaoMapProps = {
  selected: string | null
  hovered: string | null
  regionData: RegionData
  onSelect: (regionId: string) => void
  onHover: (regionId: string | null) => void
}

const regionCenters: Record<string, { lat: number; lng: number; label: string }> = {
  seoul:     { lat: 37.5665, lng: 126.9780, label: '서울' },
  gyeonggi:  { lat: 37.4138, lng: 127.5183, label: '경기' },
  gangwon:   { lat: 37.8228, lng: 128.1555, label: '강원' },
  chungbuk:  { lat: 36.6357, lng: 127.4913, label: '충북' },
  chungnam:  { lat: 36.5184, lng: 126.8000, label: '충남' },
  daejeon:   { lat: 36.3504, lng: 127.3845, label: '대전' },
  jeonbuk:   { lat: 35.7175, lng: 127.1530, label: '전북' },
  gwangju:   { lat: 35.1595, lng: 126.8526, label: '광주' },
  jeonnam:   { lat: 34.8679, lng: 126.9910, label: '전남' },
  gyeongbuk: { lat: 36.4919, lng: 128.8889, label: '경북' },
  daegu:     { lat: 35.8714, lng: 128.6014, label: '대구' },
  gyeongnam: { lat: 35.4606, lng: 128.2132, label: '경남' },
  ulsan:     { lat: 35.5384, lng: 129.3114, label: '울산' },
  busan:     { lat: 35.1796, lng: 129.0756, label: '부산' },
  jeju:      { lat: 33.4996, lng: 126.5312, label: '제주' },
}

function getColor(total: number) {
  if (total >= 20) return '#20436d'
  if (total >= 10) return '#07559d'
  if (total >= 5)  return '#1b9bd1'
  if (total >= 1)  return '#81c4e2'
  return '#b0cfe8'
}

export default function KakaoMap({ selected, regionData, onSelect, onHover }: KakaoMapProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<any>(null)
  const overlaysRef = useRef<any[]>([])
  const [mapReady, setMapReady] = useState(false)

  // SDK 로드 및 지도 초기화
  useEffect(() => {
    const key = process.env.NEXT_PUBLIC_KAKAO_MAP_KEY
    if (!key) {
      console.warn('NEXT_PUBLIC_KAKAO_MAP_KEY 환경변수가 설정되지 않았습니다.')
      return
    }

    const createMap = () => {
      console.log('[KakaoMap] createMap 호출됨, mapRef:', mapRef.current)
      if (!mapRef.current) {
        console.error('[KakaoMap] mapRef.current 가 null — 컨테이너 없음')
        return
      }
      const map = new window.kakao.maps.Map(mapRef.current, {
        center: new window.kakao.maps.LatLng(36.2, 127.8),
        level: 13,
      })
      mapInstanceRef.current = map
      setMapReady(true)
      console.log('[KakaoMap] 지도 생성 완료')

      // 컨테이너 크기 변화 감지 → 자동 relayout
      const observer = new ResizeObserver(() => {
        map.relayout()
      })
      observer.observe(mapRef.current!)

    }

    console.log('[KakaoMap] 초기화 시작, window.kakao:', window.kakao)

    // 케이스 1: Map 생성자까지 완전히 로드된 상태
    if (window.kakao?.maps?.Map) {
      console.log('[KakaoMap] 케이스1 - 이미 로드됨')
      createMap()
      return
    }

    // 케이스 2: kakao 객체는 있지만 maps.load() 호출이 필요한 상태
    if (window.kakao?.maps) {
      console.log('[KakaoMap] 케이스2 - maps.load() 호출')
      window.kakao.maps.load(createMap)
      return
    }

    // 케이스 3: 스크립트 태그가 이미 DOM에 있지만 아직 로드 중인 상태
    const existingScript = document.getElementById('kakao-map-sdk')
    if (existingScript) {
      console.log('[KakaoMap] 케이스3 - 스크립트 로드 대기 중')
      existingScript.addEventListener('load', () => window.kakao.maps.load(createMap))
      return
    }

    // 케이스 4: 스크립트 태그 자체가 없는 상태 → 새로 삽입
    console.log('[KakaoMap] 케이스4 - 스크립트 새로 삽입')
    const script = document.createElement('script')
    script.id = 'kakao-map-sdk'
    script.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false`
    script.async = true
    script.onload = () => {
      console.log('[KakaoMap] 스크립트 로드 완료, maps.load() 호출')
      window.kakao.maps.load(createMap)
    }
    script.onerror = (e) => console.error('[KakaoMap] 스크립트 로드 실패:', e)
    document.head.appendChild(script)
  }, [])

  // 오버레이 업데이트 (지도 준비 완료 or regionData / selected 변경 시)
  useEffect(() => {
    if (!mapReady || !mapInstanceRef.current) return

    // 기존 오버레이 제거
    overlaysRef.current.forEach(o => o.setMap(null))
    overlaysRef.current = []

    Object.entries(regionCenters).forEach(([id, region]) => {
      const data = regionData[id]
      const total = data?.total ?? 0
      const color = getColor(total)
      const isSelected = selected === id

      const el = document.createElement('div')
      el.className = `${styles.overlay} ${isSelected ? styles.overlaySelected : ''}`
      el.style.backgroundColor = color
      el.innerHTML = `
        <span class="${styles.overlayLabel}">${region.label}</span>
        <span class="${styles.overlayCount}">${total}건</span>
      `
      el.addEventListener('click', () => onSelect(id))
      el.addEventListener('mouseenter', () => onHover(id))
      el.addEventListener('mouseleave', () => onHover(null))

      const overlay = new window.kakao.maps.CustomOverlay({
        position: new window.kakao.maps.LatLng(region.lat, region.lng),
        content: el,
        zIndex: isSelected ? 10 : 1,
        xAnchor: 0.5,
        yAnchor: 0.5,
      })
      overlay.setMap(mapInstanceRef.current)
      overlaysRef.current.push(overlay)
    })
  }, [mapReady, regionData, selected, onSelect, onHover])

  return (
    <div className={styles.wrapper}>
      <div ref={mapRef} className={styles.map} />
    </div>
  )
}
