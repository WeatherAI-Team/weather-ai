'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import styles from './not-found.module.css'

export default function NotFound() {
  const [drops, setDrops] = useState<{ left: number; delay: number; duration: number }[]>([])

  useEffect(() => {
    document.title = 'Weather AI - 페이지 없음'
    setDrops(
      Array.from({ length: 40 }, () => ({
        left:     Math.random() * 100,
        delay:    Math.random() * 3,
        duration: 0.6 + Math.random() * 0.6,
      }))
    )
  }, [])

  return (
    <div className={styles.page}>
      {drops.map((d, i) => (
        <span
          key={i}
          className={styles.rain}
          style={{ left: `${d.left}%`, animationDelay: `${d.delay}s`, animationDuration: `${d.duration}s` }}
        />
      ))}

      <div className={styles.content}>
        <div className={styles.weatherIcon}>⛈️</div>
        <h1 className={styles.code}>404</h1>
        <p className={styles.title}>폭풍 속에서 길을 잃었습니다.</p>
        <p className={styles.desc}>
          요청하신 페이지가 존재하지 않거나 이동되었습니다.<br />
          악천후 속에서도 AI는 계속 탐지 중입니다.
        </p>
        <Link href="/" className={styles.btn}>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2L2 8l6 6M2 8h12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          메인으로 돌아가기
        </Link>
      </div>
    </div>
  )
}
