'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import WeatherOverlay from '@/components/weather/WeatherOverlay'
import styles from './page.module.css'
import ChatBot from '@/components/chatbot/ChatBot'

const weatherLabels = ['☀️ 맑음', '☁️ 흐림', '🌧️ 비', '❄️ 눈']
const DURATION = 3000

export default function HomePage() {
  useEffect(() => { document.title = 'Weather AI' }, [])
  const [phaseIdx, setPhaseIdx] = useState(0)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const id = setInterval(() => setPhaseIdx(p => (p + 1) % 4), DURATION)
    return () => clearInterval(id)
  }, [])

  return (
    <div className={styles.page}>
      {/* ── HERO ── */}
      <section className={styles.hero}>
        {mounted && <WeatherOverlay />}

        {/* Background image placeholder */}
        <div className={styles.heroBg} />

        <div className={styles.heroContent}>
          {/* Weather indicator */}
          <div className={styles.weatherBadge}>
            <span className={styles.weatherDot} />
            <span>{weatherLabels[phaseIdx]}</span>
          </div>

          <h1 className={styles.heroTitle}>
            <span>악천후 속</span>
            <em>위험물질 차량</em>
            <span>AI 탐지 시스템</span>
          </h1>

          <p className={styles.heroDesc}>
            극한의 기상 조건에서도 위험 물질 운반 차량을 실시간으로 탐지하여<br />
            도로 위의 잠재적 사고를 사전에 예방합니다
          </p>

          <div className={styles.heroCtas}>
            <Link href="/ai" className={styles.ctaPrimary}>
              AI 탐지 시작
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </Link>
            <Link href="/intro" className={styles.ctaSecondary}>
              시스템 소개
            </Link>
          </div>

          {/* Scroll indicator dots */}
          <div className={styles.weatherDots}>
            {weatherLabels.map((_, i) => (
              <span key={i} className={`${styles.dot} ${i === phaseIdx ? styles.dotActive : ''}`} />
            ))}
          </div>
        </div>
      </section>

      {/* ── QUICK NAV CARDS ── */}
      <section className={styles.cards}>
        <div className="container">
          <div className={styles.cardGrid}>
            <Link href="/intro" className={styles.card}>
              <div className={styles.cardIcon}>
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <circle cx="18" cy="18" r="16" fill="var(--light-blue)" opacity="0.4"/>
                  <circle cx="18" cy="18" r="10" stroke="var(--secondary)" strokeWidth="2"/>
                  <circle cx="18" cy="14" r="2" fill="var(--primary)"/>
                  <rect x="16" y="17" width="4" height="7" rx="1" fill="var(--primary)"/>
                </svg>
              </div>
              <h3>소개</h3>
              <p>프로젝트 개요, 탐지 방식, 기술 스택, 팀 소개를 확인하세요</p>
              <span className={styles.cardArrow}>→</span>
            </Link>

            <Link href="/ai" className={`${styles.card} ${styles.cardHighlight}`}>
              <div className={styles.cardBadge}>LIVE</div>
              <div className={styles.cardIcon}>
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <circle cx="18" cy="18" r="16" fill="white" opacity="0.15"/>
                  <rect x="8" y="12" width="20" height="14" rx="3" stroke="white" strokeWidth="2"/>
                  <circle cx="18" cy="19" r="4" fill="white" opacity="0.8"/>
                  <path d="M14 8l4 4 4-4" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
                </svg>
              </div>
              <h3 style={{ color: '#ffffff' }}>CCTV 실시간 분석</h3>
              <p style={{ color: 'rgba(255,255,255,0.8)' }}>CCTV 실시간 스트림 기반의 악천후 위험 차량 탐지 시스템</p>
              <span className={styles.cardArrow}>→</span>
            </Link>

            <Link href="/board" className={styles.card}>
              <div className={styles.cardIcon}>
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <circle cx="18" cy="18" r="16" fill="var(--sage)" opacity="0.4"/>
                  <rect x="10" y="10" width="16" height="18" rx="2" stroke="var(--dark-navy)" strokeWidth="2"/>
                  <path d="M13 15h10M13 19h10M13 23h6" stroke="var(--secondary)" strokeWidth="1.6" strokeLinecap="round"/>
                </svg>
              </div>
              <h3>게시판</h3>
              <p>탐지 결과 공유, 사례 분석, 공지사항 및 커뮤니티 게시글을 확인하세요</p>
              <span className={styles.cardArrow}>→</span>
            </Link>
          </div>
        </div>
      </section>
      <ChatBot />
    </div>
  )
}
