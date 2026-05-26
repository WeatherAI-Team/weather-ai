'use client'
import { useState, useRef, useEffect, useCallback } from 'react'
import Hls from 'hls.js'
import styles from './page.module.css'

const BACKEND_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'
const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

type TabType = 'cctv' | 'upload'

type Detection = {
  bbox: [number, number, number, number]
  label: string
  confidence: number
}

type Result = {
  detected: boolean 
  confidence: number
  label: string
  detections: Detection[]
}

type CctvItem = {
  cctvname: string
  cctvurl: string
  cctvformat: string
  coordx: number
  coordy: number
}

const REGIONS = [
  { label: '전체',  keywords: [] },
  { label: '서울',  keywords: ['서울'] },
  { label: '경기',  keywords: ['경기', '수원', '성남', '안양', '부천', '평택', '안산', '고양', '용인', '파주', '시흥', '김포', '화성', '양주', '포천'] },
  { label: '인천',  keywords: ['인천'] },
  { label: '강원',  keywords: ['강원', '춘천', '원주', '강릉', '동해', '태백', '속초', '삼척'] },
  { label: '충청',  keywords: ['충북', '충남', '충청', '대전', '세종', '청주', '천안', '공주', '아산', '서산', '논산'] },
  { label: '전북',  keywords: ['전북', '전주', '군산', '익산', '정읍', '남원', '김제'] },
  { label: '전남',  keywords: ['전남', '목포', '여수', '순천', '나주', '광양'] },
  { label: '광주',  keywords: ['광주'] },
  { label: '경북',  keywords: ['경북', '포항', '경주', '김천', '안동', '구미', '영주'] },
  { label: '경남',  keywords: ['경남', '창원', '진주', '통영', '사천', '김해', '밀양', '거제', '양산'] },
  { label: '대구',  keywords: ['대구'] },
  { label: '울산',  keywords: ['울산'] },
  { label: '부산',  keywords: ['부산'] },
  { label: '제주',  keywords: ['제주'] },
]

function getRegion(cctvname: string): string {
  for (const r of REGIONS.slice(1)) {
    if (r.keywords.some(kw => cctvname.includes(kw))) return r.label
  }
  return '기타'
}

// ── 바운딩박스 오버레이 컴포넌트 ──
function BoundingBoxOverlay({ src, detections }: { src: string; detections: Detection[] }) {
  const imgRef = useRef<HTMLImageElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const draw = useCallback(() => {
    const img = imgRef.current
    const canvas = canvasRef.current
    if (!img || !canvas) return

    canvas.width = img.offsetWidth
    canvas.height = img.offsetHeight
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    detections.forEach(det => {
      const [x1, y1, x2, y2] = det.bbox
      const x = x1 * canvas.width
      const y = y1 * canvas.height
      const w = (x2 - x1) * canvas.width
      const h = (y2 - y1) * canvas.height
      const color = det.confidence >= 0.85 ? '#e74c3c' : '#f39c12'

      ctx.strokeStyle = color
      ctx.lineWidth = 2.5
      ctx.shadowColor = color
      ctx.shadowBlur = 4
      ctx.strokeRect(x, y, w, h)
      ctx.shadowBlur = 0

      const text = `${det.label}  ${(det.confidence * 100).toFixed(1)}%`
      ctx.font = 'bold 12px sans-serif'
      const tw = ctx.measureText(text).width
      const labelY = y > 26 ? y - 24 : y + h + 2
      ctx.fillStyle = color
      ctx.fillRect(x - 1, labelY, tw + 12, 22)

      ctx.fillStyle = '#fff'
      ctx.fillText(text, x + 5, labelY + 15)
    })
  }, [detections])

  useEffect(() => { draw() }, [draw])

  return (
    <div className={styles.bboxContainer}>
      <img ref={imgRef} src={src} alt="분석 이미지" className={styles.bboxImage} onLoad={draw} />
      <canvas ref={canvasRef} className={styles.bboxCanvas} />
    </div>
  )
}

// ── HLS 플레이어 컴포넌트 ──
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
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(() => {})
      })
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      video.src = src
      video.play().catch(() => {})
    }

    return () => { hls?.destroy() }
  }, [src])

  return <video ref={videoRef} className={className} autoPlay muted playsInline controls />
}

// ── 메인 페이지 ──
export default function AiPage() {
  const [tab, setTab] = useState<TabType>('cctv')
  const [selectedCctv, setSelectedCctv] = useState<number | null>(null)
  const [cctvList, setCctvList] = useState<CctvItem[]>([])
  const [cctvLoading, setCctvLoading] = useState(false)
  const [selectedRegion, setSelectedRegion] = useState('전체')

  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)
  const [isImage, setIsImage] = useState(false)

  useEffect(() => {
    if (tab !== 'cctv') return
    setCctvLoading(true)
    fetch(`${BACKEND_URL}/api/cctv`)
      .then(res => res.json())
      .then(data => {
        const items: CctvItem[] = data?.response?.data ?? []
        setCctvList(items)
      })
      .catch(err => console.error('CCTV 목록 불러오기 실패:', err))
      .finally(() => setCctvLoading(false))
  }, [tab])

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const fileIsImage = file.type.startsWith('image/')
    setIsImage(fileIsImage)
    setUploading(true)
    setResult(null)
    setUploadedUrl(URL.createObjectURL(file))

    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', '1')
    formData.append('original_filename', file.name)

    const endpoint = fileIsImage ? '/api/ai/detect' : '/api/ai/analyze_and_save_video'

    try {
      const res = await fetch(`${BACKEND_URL}${endpoint}`, { method: 'POST', body: formData })
      const data = await res.json()
      if (data.success) {
        setResult({
          detected: data.is_danger,
          confidence: data.confidence,
          label: data.weather,
          detections: data.detections ?? [],
        })
      }
    } catch {
      setResult({ detected: false, confidence: 0, label: '분석 실패', detections: [] })
    } finally {
      setUploading(false)
    }
  }

  const handleReset = () => {
    setUploadedUrl(null)
    setResult(null)
    setIsImage(false)
  }

  const selected = selectedCctv !== null ? cctvList[selectedCctv] : null

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>AI 탐지</p>
          <h1 className={styles.title}>위험 차량 탐지</h1>
          <p className={styles.desc}>연동된 CCTV 실시간 영상을 분석하거나, 영상 파일을 업로드하여 AI 분석을 시작하세요</p>
        </div>
      </section>

      <section className={styles.main}>
        <div className="container">

          <div className={styles.tabBar}>
            <button className={`${styles.tabBtn} ${tab === 'cctv' ? styles.tabActive : ''}`} onClick={() => setTab('cctv')}>
              📡 CCTV 실시간
            </button>
            <button className={`${styles.tabBtn} ${tab === 'upload' ? styles.tabActive : ''}`} onClick={() => setTab('upload')}>
              📁 영상 업로드
            </button>
          </div>

          {tab === 'cctv' && (
            <div className={styles.cctvTabGrid}>
              <div className={styles.panel}>
                <h2>{selected ? selected.cctvname : 'CCTV 실시간 화면'}</h2>
                <div className={styles.cctvBox}>
                  {selected ? (
                    <HlsPlayer
                      key={selected.cctvurl}
                      src={`${BACKEND_URL}/api/cctv/stream?url=${encodeURIComponent(selected.cctvurl)}`}
                      className={styles.cctvStream}
                    />
                  ) : (
                    <div className={styles.cctvEmpty}>
                      <span>📷</span>
                      <p>오른쪽 목록에서 CCTV를 선택하세요</p>
                    </div>
                  )}
                </div>
              </div>

              <div className={styles.panel}>
                <h2>연동 CCTV 목록</h2>
                <div className={styles.regionBar}>
                  {REGIONS.map(r => (
                    <button
                      key={r.label}
                      className={`${styles.regionBtn} ${selectedRegion === r.label ? styles.regionActive : ''}`}
                      onClick={() => { setSelectedRegion(r.label); setSelectedCctv(null) }}
                    >
                      {r.label}
                    </button>
                  ))}
                </div>
                <div className={styles.cctvHistory}>
                  {cctvLoading && <p>불러오는 중...</p>}
                  {!cctvLoading && cctvList.length === 0 && <p>CCTV 목록이 없습니다.</p>}
                  {!cctvLoading && (() => {
                    const filtered = selectedRegion === '전체'
                      ? cctvList
                      : cctvList.filter(cam => getRegion(cam.cctvname) === selectedRegion)
                    if (filtered.length === 0 && cctvList.length > 0) {
                      return <p className={styles.cctvEmpty2}>해당 지역에 연동된 CCTV가 없습니다</p>
                    }
                    return filtered.map((cam) => {
                      const origIdx = cctvList.indexOf(cam)
                      return (
                        <div
                          key={origIdx}
                          className={`${styles.cctvHistoryItem} ${selectedCctv === origIdx ? styles.cctvItemSelected : ''}`}
                          onClick={() => setSelectedCctv(origIdx)}
                        >
                          <span className={`${styles.cctvDot} ${styles.dotWarn}`} />
                          <div className={styles.cctvHistoryInfo}>
                            <p className={styles.cctvHistoryUrl}>{cam.cctvname}</p>
                            <p className={styles.cctvHistoryMeta}>{cam.cctvformat} · {cam.coordx}, {cam.coordy}</p>
                          </div>
                        </div>
                      )
                    })
                  })()}
                </div>
              </div>
            </div>
          )}

          {tab === 'upload' && (
            <div className={styles.tabGrid}>
              <div className={styles.panel}>
                <h2>
                  {uploadedUrl
                    ? isImage
                      ? result?.detections?.length ? '탐지 결과 (바운딩박스)' : '업로드된 이미지'
                      : '업로드된 영상'
                    : '영상 업로드'}
                </h2>

                {uploadedUrl ? (
                  <div className={styles.videoPreview}>
                    {isImage ? (
                      result?.detections?.length ? (
                        <BoundingBoxOverlay src={uploadedUrl} detections={result.detections} />
                      ) : (
                        <img src={uploadedUrl} alt="업로드된 이미지" className={styles.uploadedImage} />
                      )
                    ) : (
                      <video src={uploadedUrl} controls className={styles.videoPlayer} />
                    )}
                    <button className={styles.resetBtn} onClick={handleReset}>다시 업로드</button>
                  </div>
                ) : (
                  <div className={styles.dropZone}>
                    <span className={styles.dropIcon}>📁</span>
                    <p>영상 또는 이미지 파일을 드래그하거나 클릭하여 업로드</p>
                    <span className={styles.dropHint}>MP4, AVI, MOV, JPG, PNG · 최대 500MB</span>
                    <input type="file" accept="video/*,image/*" className={styles.fileInput} onChange={handleUpload} />
                  </div>
                )}
              </div>

              <div className={styles.panel}>
                <h2>분석 결과</h2>
                {uploading && (
                  <div className={styles.loading}>
                    <div className={styles.spinner} />
                    <p>AI 분석 중...</p>
                  </div>
                )}
                {result && !uploading && (
                  <>
                    <div className={`${styles.result} ${result.detected ? styles.danger : styles.safe}`}>
                      <div className={styles.resultIcon}>{result.detected ? '⚠️' : '✅'}</div>
                      <h3>{result.detected ? '위험 차량 탐지됨' : '위험 차량 없음'}</h3>
                      <p className={styles.resultLabel}>{result.label}</p>
                      <div className={styles.confidence}>
                        <span>신뢰도</span>
                        <div className={styles.bar}><div className={styles.fill} style={{ width: `${result.confidence}%` }} /></div>
                        <span>{result.confidence}%</span>
                      </div>
                    </div>

                    {result.detections.length > 0 && (
                      <div className={styles.detectionList}>
                        <p className={styles.detectionListTitle}>탐지된 객체 ({result.detections.length}개)</p>
                        {result.detections.map((det, i) => (
                          <div key={i} className={styles.detectionItem}>
                            <span className={styles.detectionIndex}>{i + 1}</span>
                            <span className={styles.detectionLabel}>{det.label}</span>
                            <div className={styles.detectionConf}>
                              <div className={styles.detectionConfBar}>
                                <div
                                  className={styles.detectionConfFill}
                                  style={{
                                    width: `${det.confidence * 100}%`,
                                    background: det.confidence >= 0.85 ? '#e74c3c' : '#f39c12',
                                  }}
                                />
                              </div>
                              <span>{(det.confidence * 100).toFixed(1)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )}
                {!result && !uploading && (
                  <div className={styles.placeholder}>
                    <span>📷</span>
                    <p>영상 또는 이미지를 업로드하면<br />분석 결과가 표시됩니다</p>
                  </div>
                )}
              </div>
            </div>
          )}


        </div>
      </section>
    </div>
  )
}