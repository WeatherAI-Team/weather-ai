'use client'
import { useEffect, useState } from 'react'
import styles from './WeatherOverlay.module.css'

type WeatherState = 'clear' | 'cloudy' | 'rain' | 'snow'
const CYCLE: WeatherState[] = ['clear', 'cloudy', 'rain', 'snow']
const DURATION = 3000

function generateRain(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 2,
    duration: 0.5 + Math.random() * 0.5,
    size: 0.8 + Math.random() * 0.8,
  }))
}

function generateSnow(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 4,
    duration: 3 + Math.random() * 3,
    size: 3 + Math.random() * 6,
    drift: (Math.random() - 0.5) * 60,
  }))
}

function generateClouds(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    top: 5 + Math.random() * 30,
    scale: 0.6 + Math.random() * 0.8,
    delay: Math.random() * 2,
    opacity: 0.5 + Math.random() * 0.4,
  }))
}

const rainDrops = generateRain(80)
const snowFlakes = generateSnow(50)
const clouds = generateClouds(7)

export default function WeatherOverlay() {
  const [phase, setPhase] = useState(0)
  const [transitioning, setTransitioning] = useState(false)

  useEffect(() => {
    const id = setInterval(() => {
      setTransitioning(true)
      setTimeout(() => {
        setPhase(p => (p + 1) % CYCLE.length)
        setTransitioning(false)
      }, 600)
    }, DURATION)
    return () => clearInterval(id)
  }, [])

  const weather = CYCLE[phase]

  return (
    <div className={`${styles.overlay} ${transitioning ? styles.fading : ''}`} aria-hidden="true">

      {/* Sky gradient */}
      <div className={`${styles.sky} ${styles[weather]}`} />

      {/* 맑음 - 태양 */}
      {weather === 'clear' && (
        <div className={styles.sun}>
          <div className={styles.sunCore} />
          <div className={styles.sunRay} />
        </div>
      )}

      {/* 흐림 - 오버레이만 (구름 없음) */}
      {weather === 'cloudy' && (
        <div className={styles.cloudyOverlay} />
      )}

      {/* 비 - 구름 없이 빗방울만 */}
      {weather === 'rain' && (
        <>
          <div className={styles.rainOverlay} />
          {rainDrops.map(r => (
            <div
              key={r.id}
              className={styles.raindrop}
              style={{
                left: `${r.left}%`,
                animationDelay: `${r.delay}s`,
                animationDuration: `${r.duration}s`,
                width: `${r.size}px`,
                height: `${r.size * 14}px`,
              }}
            />
          ))}
        </>
      )}

      {/* 눈 - 눈송이 */}
      {weather === 'snow' && (
        <>
          {snowFlakes.map(s => (
            <div
              key={s.id}
              className={styles.snowflake}
              style={{
                left: `${s.left}%`,
                animationDelay: `${s.delay}s`,
                animationDuration: `${s.duration}s`,
                width: `${s.size}px`,
                height: `${s.size}px`,
                '--drift': `${s.drift}px`,
              } as React.CSSProperties}
            />
          ))}
          <div className={styles.fog} />
        </>
      )}

    </div>
  )
}
