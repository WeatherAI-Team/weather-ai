'use client'

import styles from './KoreaMap.module.css'

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

type KoreaMapProps = {
  selected: string | null
  hovered: string | null
  regionData: RegionData
  onSelect: (regionId: string) => void
  onHover: (regionId: string | null) => void
}

const regions = [
  {
    id: 'seoul',
    label: '서울',
    labelX: 178,
    labelY: 112,
    d: 'M158 88 L194 90 L205 118 L188 145 L154 138 L140 112 Z',
  },
  {
    id: 'gyeonggi',
    label: '경기',
    labelX: 180,
    labelY: 165,
    d: 'M130 58 L228 50 L264 110 L246 190 L205 225 L145 210 L105 155 L115 95 Z',
  },
  {
    id: 'gangwon',
    label: '강원',
    labelX: 320,
    labelY: 120,
    d: 'M235 35 L382 25 L455 175 L415 245 L272 217 L250 135 Z',
  },
  {
    id: 'chungbuk',
    label: '충북',
    labelX: 260,
    labelY: 255,
    d: 'M205 220 L290 215 L350 265 L318 340 L225 335 L178 278 Z',
  },
  {
    id: 'chungnam',
    label: '충남',
    labelX: 135,
    labelY: 290,
    d: 'M78 230 L176 210 L225 335 L165 405 L70 365 L45 290 Z',
  },
  {
    id: 'daejeon',
    label: '대전',
    labelX: 194,
    labelY: 345,
    d: 'M175 322 L220 323 L235 363 L200 390 L165 365 Z',
  },
  {
    id: 'jeonbuk',
    label: '전북',
    labelX: 145,
    labelY: 430,
    d: 'M82 370 L180 392 L225 462 L190 535 L85 520 L38 455 Z',
  },
  {
    id: 'gwangju',
    label: '광주',
    labelX: 112,
    labelY: 555,
    d: 'M82 535 L132 528 L152 570 L115 598 L72 578 Z',
  },
  {
    id: 'jeonnam',
    label: '전남',
    labelX: 130,
    labelY: 625,
    d: 'M40 520 L190 538 L235 610 L178 705 L70 695 L20 625 Z',
  },
  {
    id: 'gyeongbuk',
    label: '경북',
    labelX: 360,
    labelY: 355,
    d: 'M320 245 L430 250 L480 365 L435 500 L330 475 L288 370 Z',
  },
  {
    id: 'daegu',
    label: '대구',
    labelX: 360,
    labelY: 465,
    d: 'M332 432 L383 428 L408 470 L370 508 L325 485 Z',
  },
  {
    id: 'gyeongnam',
    label: '경남',
    labelX: 330,
    labelY: 585,
    d: 'M235 470 L330 488 L430 520 L410 650 L300 690 L215 625 Z',
  },
  {
    id: 'ulsan',
    label: '울산',
    labelX: 465,
    labelY: 535,
    d: 'M430 492 L490 485 L520 535 L485 585 L425 565 Z',
  },
  {
    id: 'busan',
    label: '부산',
    labelX: 440,
    labelY: 635,
    d: 'M405 612 L470 595 L505 645 L460 700 L398 675 Z',
  },
  {
    id: 'jeju',
    label: '제주',
    labelX: 260,
    labelY: 755,
    d: 'M200 735 L325 728 L360 765 L320 800 L210 795 L170 765 Z',
  },
]

const regionNameMap: Record<string, string> = {
  seoul: '서울특별시',
  gyeonggi: '경기도',
  gangwon: '강원도',
  chungbuk: '충청북도',
  chungnam: '충청남도',
  daejeon: '대전광역시',
  jeonbuk: '전라북도',
  gwangju: '광주광역시',
  jeonnam: '전라남도',
  gyeongbuk: '경상북도',
  daegu: '대구광역시',
  gyeongnam: '경상남도',
  ulsan: '울산광역시',
  busan: '부산광역시',
  jeju: '제주특별자치도',
}

function getRegionColor(total: number) {
  if (total >= 20) return '#20436d'
  if (total >= 10) return '#07559d'
  if (total >= 5) return '#1b9bd1'
  if (total >= 1) return '#81c4e2'
  return '#dbeafe'
}

export default function KoreaMap({
  selected,
  hovered,
  regionData,
  onSelect,
  onHover,
}: KoreaMapProps) {
  return (
    <div className={styles.mapWrap}>
      <svg
        className={styles.mapSvg}
        viewBox="0 0 560 830"
        role="img"
        aria-label="대한민국 지역별 사고 탐지 지도"
      >
        {regions.map((region) => {
          const data = regionData[region.id]
          const total = data?.total ?? 0
          const isSelected = selected === region.id
          const isHovered = hovered === region.id

          return (
            <g
              key={region.id}
              className={`${styles.regionGroup} ${
                isSelected ? styles.selected : ''
              } ${isHovered ? styles.hovered : ''}`}
              onClick={() => onSelect(region.id)}
              onMouseEnter={() => onHover(region.id)}
              onMouseLeave={() => onHover(null)}
            >
              <path
                d={region.d}
                fill={getRegionColor(total)}
                className={styles.regionPath}
              />

              <text
                x={region.labelX}
                y={region.labelY}
                textAnchor="middle"
                className={styles.regionLabel}
              >
                {region.label}
              </text>

              <text
                x={region.labelX}
                y={region.labelY + 22}
                textAnchor="middle"
                className={styles.countLabel}
              >
                {total}건
              </text>
            </g>
          )
        })}
      </svg>

      {hovered && (
        <div className={styles.tooltip}>
          <strong>{regionData[hovered]?.name ?? regionNameMap[hovered]}</strong>
          <span>사고 발생 {regionData[hovered]?.total ?? 0}건</span>
        </div>
      )}
    </div>
  )
}