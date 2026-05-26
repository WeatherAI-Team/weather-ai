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

const recentDetections = [
  { time: '2026-04-28 14:22', loc: '경부고속도로 상행 23km', weather: '폭우', type: '탱크로리',      conf: 98.1, status: '위험' },
  { time: '2026-04-28 11:05', loc: '서울외곽순환 북부',       weather: '폭설', type: 'LPG 화물차',   conf: 95.4, status: '위험' },
  { time: '2026-04-27 22:40', loc: '중부고속도로 하행',       weather: '안개', type: '화학물질 탱크', conf: 91.7, status: '경고' },
]

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

// ── HLS 플레이어 + AI 바운딩박스 컴포넌트 ──
function HlsPlayer({ src, className }: { src: string; className?: string }) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const overlayRef = useRef<HTMLCanvasElement>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const isAnalyzingRef = useRef(false)  // 분석 중 중복 요청 방지

  // HLS 스트리밍 연결
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

  // 프레임 캡처 → AI 서버 전송 → 바운딩박스 그리기
  useEffect(() => {
    const video = videoRef.current
    const captureCanvas = canvasRef.current
    const overlay = overlayRef.current
    if (!video || !captureCanvas || !overlay) return

    const analyzeFrame = async () => {
      // 이전 분석 중이면 스킵
      if (isAnalyzingRef.current) return
      if (video.readyState < 2 || video.paused) return

      isAnalyzingRef.current = true

      try {
        // 프레임 캡처
        captureCanvas.width = 640
        captureCanvas.height = 360
        const ctx = captureCanvas.getContext('2d')
        if (!ctx) { isAnalyzingRef.current = false; return }
        ctx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height)

        // blob 변환 후 AI 서버로 전송
        captureCanvas.toBlob(async (blob) => {
          if (!blob) { isAnalyzingRef.current = false; return }
          try {
            const formData = new FormData()
            formData.append('file', blob, 'frame.jpg')

            const res = await fetch(`${API_URL}/api/ai/detect`, {
              method: 'POST',
              body: formData,
            })
            const data = await res.json()

            // 오버레이 초기화
            overlay.width = video.offsetWidth
            overlay.height = video.offsetHeight
            const octx = overlay.getContext('2d')
            if (!octx) { isAnalyzingRef.current = false; return }
            octx.clearRect(0, 0, overlay.width, overlay.height)

            if (data.success) {
              // 날씨/위험차량 정보 텍스트 오버레이
              const weatherColor = data.is_danger ? '#e74c3c' : '#2ecc71'
              octx.fillStyle = 'rgba(0,0,0,0.5)'
              octx.fillRect(10, 10, 280, 60)
              octx.fillStyle = weatherColor
              octx.font = 'bold 16px sans-serif'
              octx.fillText(`날씨: ${data.weather} (${data.confidence}%)`, 20, 35)
              const hasDangerVehicle = data.yolo_boxes && data.yolo_boxes.length > 0
              octx.fillStyle = hasDangerVehicle ? '#e74c3c' : '#2ecc71'
              octx.fillText(
                hasDangerVehicle ? '⚠️ 위험차량: 감지됨' : '✅ 위험차량: 없음',
                20, 58
              )

              // YOLO 바운딩박스 그리기
              if (data.yolo_boxes && data.yolo_boxes.length > 0) {
                data.yolo_boxes.forEach((box: any) => {
                  const [x1, y1, x2, y2] = box.box_coords
                  const scaleX = overlay.width / captureCanvas.width
                  const scaleY = overlay.height / captureCanvas.height

                  const x = x1 * scaleX
                  const y = y1 * scaleY
                  const w = (x2 - x1) * scaleX
                  const h = (y2 - y1) * scaleY

                  octx.strokeStyle = '#e74c3c'
                  octx.lineWidth = 2.5
                  octx.shadowColor = '#e74c3c'
                  octx.shadowBlur = 4
                  octx.strokeRect(x, y, w, h)
                  octx.shadowBlur = 0

                  const text = `${box.class_name} ${box.confidence}%`
                  octx.font = 'bold 13px sans-serif'
                  const tw = octx.measureText(text).width
                  octx.fillStyle = '#e74c3c'
                  octx.fillRect(x, y - 24, tw + 12, 22)
                  octx.fillStyle = '#fff'
                  octx.fillText(text, x + 6, y - 7)
                })
              }
            }
          } catch (e) {
            console.error('AI 분석 실패:', e)
          } finally {
            isAnalyzingRef.current = false  // 분석 완료
          }
        }, 'image/jpeg', 0.8)
      } catch (e) {
        console.error('프레임 캡처 실패:', e)
        isAnalyzingRef.current = false
      }
    }

    // 500ms마다 프레임 분석 시도 (분석 중이면 자동 스킵)
    intervalRef.current = setInterval(analyzeFrame, 500)

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [src])

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <video ref={videoRef} className={className} autoPlay muted playsInline controls />
      {/* 캡처용 숨김 캔버스 */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      {/* 바운딩박스 오버레이 캔버스 */}
      <canvas
        ref={overlayRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
        }}
      />
    </div>
  )
}

// ── 메인 페이지 ──
export default function AiPage() {
  const [tab, setTab] = useState<TabType>('cctv')
  const [selectedCctv, setSelectedCctv] = useState<number | null>(null)
  const [cctvList, setCctvList] = useState<CctvItem[]>([])
  const [cctvLoading, setCctvLoading] = useState(false)

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
            <div className={styles.tabGrid}>
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
                <div className={styles.cctvHistory}>
                  {cctvLoading && <p>불러오는 중...</p>}
                  {!cctvLoading && cctvList.length === 0 && <p>CCTV 목록이 없습니다.</p>}
                  {cctvList.map((cam, i) => (
                    <div
                      key={i}
                      className={`${styles.cctvHistoryItem} ${selectedCctv === i ? styles.cctvItemSelected : ''}`}
                      onClick={() => setSelectedCctv(i)}
                    >
                      <span className={`${styles.cctvDot} ${styles.dotWarn}`} />
                      <div className={styles.cctvHistoryInfo}>
                        <p className={styles.cctvHistoryUrl}>{cam.cctvname}</p>
                        <p className={styles.cctvHistoryMeta}>{cam.cctvformat} · {cam.coordx}, {cam.coordy}</p>
                      </div>
                    </div>
                  ))}
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

          <div className={styles.recent}>
            <h2>최근 탐지 이력</h2>
            <table className={styles.table}>
              <thead>
                <tr><th>일시</th><th>위치</th><th>날씨</th><th>차량 유형</th><th>신뢰도</th><th>상태</th></tr>
              </thead>
              <tbody>
                {recentDetections.map((r, i) => (
                  <tr key={i}>
                    <td>{r.time}</td><td>{r.loc}</td><td>{r.weather}</td><td>{r.time}</td>
                    <td>{r.conf}%</td>
                    <td><span className={`${styles.badge} ${r.status === '위험' ? styles.badgeDanger : styles.badgeWarn}`}>{r.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

        </div>
      </section>
    </div>
  )
}