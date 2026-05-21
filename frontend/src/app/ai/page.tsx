'use client'
import { useState, useRef, useEffect, useCallback } from 'react'
import styles from './page.module.css'

const API_URL = process.env.NEXT_PUBLIC_AI_URL || 'http://localhost:8000'

type TabType = 'cctv' | 'upload'

type Detection = {
  bbox: [number, number, number, number] // [x1, y1, x2, y2] normalized 0~1
  label: string
  confidence: number
}

type Result = {
  detected: boolean
  confidence: number
  label: string
  detections: Detection[]
}

const cctvList = [
  { name: '경부고속도로 상행 23km', url: 'rtsp://its-cam01.kroad.or.kr', status: '위험', weather: '폭우',  conf: 98.1, time: '14:22' },
  { name: '서울외곽순환 북부 구간',  url: 'rtsp://its-cam02.kroad.or.kr', status: '위험', weather: '폭설',  conf: 95.4, time: '11:05' },
  { name: '중부고속도로 하행 41km',  url: 'rtsp://its-cam03.kroad.or.kr', status: '경고', weather: '안개',  conf: 91.7, time: '09:40' },
  { name: '영동고속도로 횡성 부근',  url: 'rtsp://its-cam04.kroad.or.kr', status: '위험', weather: '폭우',  conf: 88.2, time: '08:15' },
  { name: '남해고속도로 서부 구간',  url: 'rtsp://its-cam05.kroad.or.kr', status: '경고', weather: '강풍',  conf: 84.5, time: '07:30' },
]

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

      // 박스
      ctx.strokeStyle = color
      ctx.lineWidth = 2.5
      ctx.shadowColor = color
      ctx.shadowBlur = 4
      ctx.strokeRect(x, y, w, h)
      ctx.shadowBlur = 0

      // 라벨 배경
      const text = `${det.label}  ${(det.confidence * 100).toFixed(1)}%`
      ctx.font = 'bold 12px sans-serif'
      const tw = ctx.measureText(text).width
      const labelY = y > 26 ? y - 24 : y + h + 2
      ctx.fillStyle = color
      ctx.fillRect(x - 1, labelY, tw + 12, 22)

      // 라벨 텍스트
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

// ── 메인 페이지 ──
export default function AiPage() {
  const [tab, setTab] = useState<TabType>('cctv')
  const [selectedCctv, setSelectedCctv] = useState<number | null>(null)

  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)
  const [isImage, setIsImage] = useState(false)

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
      const res = await fetch(`${API_URL}${endpoint}`, { method: 'POST', body: formData })
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

          {/* 탭 */}
          <div className={styles.tabBar}>
            <button className={`${styles.tabBtn} ${tab === 'cctv' ? styles.tabActive : ''}`} onClick={() => setTab('cctv')}>
              📡 CCTV 실시간
            </button>
            <button className={`${styles.tabBtn} ${tab === 'upload' ? styles.tabActive : ''}`} onClick={() => setTab('upload')}>
              📁 영상 업로드
            </button>
          </div>

          {/* CCTV 실시간 탭 */}
          {tab === 'cctv' && (
            <div className={styles.tabGrid}>
              <div className={styles.panel}>
                <h2>{selected ? selected.name : 'CCTV 실시간 화면'}</h2>
                <div className={styles.cctvBox}>
                  {selected ? (
                    <img
                      src={`${API_URL}/api/ai/cctv_feed?url=${encodeURIComponent(selected.url)}`}
                      alt={selected.name}
                      className={styles.cctvStream}
                    />
                  ) : (
                    <div className={styles.cctvEmpty}>
                      <span>📷</span>
                      <p>오른쪽 목록에서 CCTV를 선택하세요</p>
                    </div>
                  )}
                </div>
                {selected && (
                  <div className={styles.cctvInfo}>
                    <span className={`${styles.badge} ${selected.status === '위험' ? styles.badgeDanger : styles.badgeWarn}`}>{selected.status}</span>
                    <span className={styles.cctvInfoText}>🌧️ {selected.weather} · 신뢰도 {selected.conf}%</span>
                    <span className={styles.cctvInfoTime}>{selected.time} 기준</span>
                  </div>
                )}
              </div>

              <div className={styles.panel}>
                <h2>연동 CCTV 목록</h2>
                <div className={styles.cctvHistory}>
                  {cctvList.map((cam, i) => (
                    <div
                      key={i}
                      className={`${styles.cctvHistoryItem} ${selectedCctv === i ? styles.cctvItemSelected : ''}`}
                      onClick={() => setSelectedCctv(i)}
                    >
                      <span className={`${styles.cctvDot} ${cam.status === '위험' ? styles.dotDanger : styles.dotWarn}`} />
                      <div className={styles.cctvHistoryInfo}>
                        <p className={styles.cctvHistoryUrl}>{cam.name}</p>
                        <p className={styles.cctvHistoryMeta}>🌧️ {cam.weather} · 신뢰도 {cam.conf}%</p>
                      </div>
                      <div className={styles.cctvHistoryRight}>
                        <span className={`${styles.badge} ${cam.status === '위험' ? styles.badgeDanger : styles.badgeWarn}`}>{cam.status}</span>
                        <span className={styles.cctvHistoryTime}>{cam.time}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* 영상 업로드 탭 */}
          {tab === 'upload' && (
            <div className={styles.tabGrid}>
              {/* 왼쪽: 업로드 / 미리보기 */}
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

              {/* 오른쪽: 분석 결과 */}
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

          {/* 최근 탐지 이력 */}
          <div className={styles.recent}>
            <h2>최근 탐지 이력</h2>
            <table className={styles.table}>
              <thead>
                <tr><th>일시</th><th>위치</th><th>날씨</th><th>차량 유형</th><th>신뢰도</th><th>상태</th></tr>
              </thead>
              <tbody>
                {recentDetections.map((r, i) => (
                  <tr key={i}>
                    <td>{r.time}</td><td>{r.loc}</td><td>{r.weather}</td><td>{r.type}</td>
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
