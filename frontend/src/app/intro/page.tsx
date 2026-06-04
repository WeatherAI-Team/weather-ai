import type { Metadata } from 'next'
import styles from './page.module.css'

export const metadata: Metadata = { title: '소개' }

export default function IntroPage() {
  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>소개</p>
          <h1 className={styles.title}>WeatherAI란?</h1>
          <p className={styles.desc}>
            악천후 기상 조건에서 일반 탐지 시스템이 놓치는<br/>
            위험물질 운반 차량을 AI로 실시간 탐지하여 대형 사고를 예방합니다.
          </p>
        
        </div>
      </section>

      <section className={styles.features}>
        <div className="container">
          <div className={styles.featureGrid}>
            {[
              { icon: '🌧️', title: '악천후 특화 AI', desc: '비, 눈, 안개 등 시야가 제한된 악천후 환경에서도 높은 탐지 정확도를 유지합니다. 기상 악화 시나리오에 특화된 데이터셋으로 파인튜닝된 AI 모델을 기반으로 구동됩니다.' },
              { icon: '🚛', title: '위험 차량 분류', desc: '탱크로리, 화학물질 운반 트럭, LPG 차량 등 다양한 위험 차종을 자동으로 분류하고, 실시간 위험도 점수를 산출합니다.' },
              { icon: '⚡', title: '실시간 처리', desc: 'CCTV 스트리밍 영상을 지연 없이 실시간으로 분석합니다. FastAPI 기반의 비동기 아키텍처를 활용하여 대용량 다중 스트림을 안정적으로 동시 처리합니다.' },
              { icon: '🔔', title: '즉각 알림 시스템', desc: '위험 차량 탐지 즉시 담당자에게 알림을 발송하고, 탐지 이미지와 위치 정보가 포함된 상세 리포트를 자동 생성합니다.' },
              { icon: '📊', title: '데이터 대시보드', desc: '탐지 이력, 기상 조건별 통계, 위험 구간 히트맵 등 핵심 분석 데이터를 한눈에 파악할 수 있는 직관적인 대시보드로 제공합니다.' },
              { icon: '🔒', title: '등급별 접근 제어', desc: '관리자, 운영자, 일반 사용자 등 시스템 역할에 따른 세분화된 접근 권한을 부여하여, 민감한 보안 데이터를 안전하게 보호합니다.' },
            ].map(f => (
              <div key={f.title} className={styles.featureCard}>
                <span className={styles.featureIcon}>{f.icon}</span>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* <section className={styles.techStack}>
        <div className="container">
          <p className={styles.eyebrow}>기술 스택</p>
          <h2 className={styles.sectionTitle}>사용 기술</h2>
          <div className={styles.techGrid}>
            {[
              { category: 'Frontend', items: ['Next.js 15', 'TypeScript', 'CSS Modules'] },
              { category: 'Backend Main', items: ['Flask', 'PostgreSQL', 'JWT Auth'] },
              { category: 'Backend AI', items: ['FastAPI', 'YOLOv8', 'OpenCV'] },
              { category: 'DevOps', items: ['WSL Ubuntu', 'Docker', 'Nginx'] },
            ].map(t => (
              <div key={t.category} className={styles.techCard}>
                <h4>{t.category}</h4>
                <ul>{t.items.map(item => <li key={item}>{item}</li>)}</ul>
              </div>
            ))}
          </div>
        </div>
      </section> */}
    </div>
  )
}
