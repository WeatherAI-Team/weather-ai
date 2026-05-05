'use client'
import { useState } from 'react'
import styles from './page.module.css'

export default function AiPage() {
  const [uploading, setUploading] = useState(false)
  const [result, setResult] = useState<null | { detected: boolean; confidence: number; label: string }>(null)

  const handleUpload = () => {
    setUploading(true)
    setResult(null)
    // 실제 구현: FormData -> POST /api/ai/detect
    setTimeout(() => {
      setUploading(false)
      setResult({ detected: true, confidence: 97.3, label: '탱크로리 (위험물질 추정)' })
    }, 2000)
  }

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>AI 탐지</p>
          <h1 className={styles.title}>위험 차량 탐지</h1>
          <p className={styles.desc}>영상 파일을 업로드하거나 실시간 스트림 URL을 입력하여 AI 분석을 시작하세요</p>
        </div>
      </section>

      <section className={styles.main}>
        <div className="container">
          <div className={styles.grid}>
            {/* Upload panel */}
            <div className={styles.panel}>
              <h2>영상 업로드</h2>
              <div className={styles.dropZone}>
                <span className={styles.dropIcon}>📁</span>
                <p>영상 파일을 드래그하거나 클릭하여 업로드</p>
                <span className={styles.dropHint}>MP4, AVI, MOV · 최대 500MB</span>
                <input type="file" accept="video/*,image/*" className={styles.fileInput} onChange={handleUpload} />
              </div>
              <div className={styles.divider}><span>또는</span></div>
              <div className={styles.streamInput}>
                <input type="text" placeholder="rtsp:// 또는 http:// 스트림 URL 입력" className={styles.input} />
                <button className={styles.analyzeBtn}>분석 시작</button>
              </div>
            </div>

            {/* Result panel */}
            <div className={styles.panel}>
              <h2>분석 결과</h2>
              {uploading && (
                <div className={styles.loading}>
                  <div className={styles.spinner} />
                  <p>AI 분석 중...</p>
                </div>
              )}
              {result && !uploading && (
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
              )}
              {!result && !uploading && (
                <div className={styles.placeholder}>
                  <span>📷</span>
                  <p>영상을 업로드하면 분석 결과가 표시됩니다</p>
                </div>
              )}
            </div>
          </div>

          {/* Recent detections */}
          <div className={styles.recent}>
            <h2>최근 탐지 이력</h2>
            <table className={styles.table}>
              <thead>
                <tr><th>일시</th><th>위치</th><th>날씨</th><th>차량 유형</th><th>신뢰도</th><th>상태</th></tr>
              </thead>
              <tbody>
                {[
                  { time: '2026-04-28 14:22', loc: '경부고속도로 상행 23km', weather: '폭우', type: '탱크로리', conf: 98.1, status: '위험' },
                  { time: '2026-04-28 11:05', loc: '서울외곽순환 북부', weather: '폭설', type: 'LPG 화물차', conf: 95.4, status: '위험' },
                  { time: '2026-04-27 22:40', loc: '중부고속도로 하행', weather: '안개', type: '화학물질 탱크', conf: 91.7, status: '경고' },
                ].map((r, i) => (
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
