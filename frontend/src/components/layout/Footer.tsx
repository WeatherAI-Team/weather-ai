'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './Footer.module.css'

const teamMembers = {
  frontend: [
    { name: '김소현' },
  ],
  backend: [
    { name: '안건우' },
    { name: '여민엽' },
    { name: '유진설' },
    { name: '조정화' },
  ],
  ai: [
    { name: '여민엽' },
    { name: '유진설' },
  ],
}

export default function Footer() {
  const pathname = usePathname()

  // 관리자 페이지에서는 푸터 숨김
  if (pathname.startsWith('/admin')) {
    return null
  }

  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>

        {/* 로고 + 프로젝트명 */}
        <div className={styles.brand}>
          <Link href="/" className={styles.logo}>
            <img src="/logo_w.png" alt="WeatherGuard AI 로고" height={45} />
          </Link>
          <p className={styles.projectName}>WeatherAI</p>
          <p className={styles.projectDesc}>
            악천후 상황 시 위험물질 차량을 AI로 탐지하여<br />
            사고를 예방하는 지능형 관제 시스템
          </p>
          <p className={styles.teamName}>Team. WeatherAI</p>
        </div>

        {/* 팀원 정보 */}
        <div className={styles.team}>
          <h4 className={styles.sectionTitle}>팀원 소개</h4>
          <div className={styles.memberGroup}>
            <div className={styles.memberRow}>
              <span className={styles.partLabel}>Frontend</span>
              <span className={styles.members}>
                {teamMembers.frontend.map((m, i) => (
                  <span key={m.name}>
                    {m.name}
                    {i < teamMembers.frontend.length - 1 && ', '}
                  </span>
                ))}
              </span>
            </div>
            <div className={styles.memberRow}>
              <span className={styles.partLabel}>Backend</span>
              <span className={styles.members}>
                {teamMembers.backend.map((m, i) => (
                  <span key={m.name}>
                    {m.name}
                    {i < teamMembers.backend.length - 1 && ', '}
                  </span>
                ))}
              </span>
            </div>
            <div className={styles.memberRow}>
              <span className={styles.partLabel}>AI</span>
              <span className={styles.members}>
                {teamMembers.ai.map((m, i) => (
                  <span key={m.name}>
                    {m.name}
                    {i < teamMembers.ai.length - 1 && ', '}
                  </span>
                ))}
              </span>
            </div>
          </div>
        </div>

        {/* 링크 */}
        <div className={styles.links}>
          <h4 className={styles.sectionTitle}>프로젝트 링크</h4>
          <div className={styles.linkList}>
            <a
              href="https://github.com/WeatherAI-Team/weather-ai"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.linkItem}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.202 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
              </svg>
              GitHub 레포지토리
            </a>

            {/* <a
              href="링크넣기"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.linkItem}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <path d="M4.459 4.208c.746.606 1.026.56 2.428.466l13.215-.793c.28 0 .047-.28-.046-.326L17.86 2.088c-.42-.326-.981-.7-2.055-.607L3.01 2.295c-.466.046-.56.28-.374.466zm.793 3.08v13.904c0 .747.373 1.027 1.214.98l14.523-.84c.841-.046.935-.56.935-1.167V6.354c0-.606-.233-.933-.748-.887l-15.177.887c-.56.047-.747.327-.747.933zm14.337.745c.093.42 0 .84-.42.888l-.7.14v10.264c-.608.327-1.168.514-1.635.514-.748 0-.935-.234-1.495-.933l-4.577-7.186v6.952L12.21 19s0 .84-1.168.84l-3.222.186c-.093-.186 0-.653.327-.746l.84-.233V9.854L7.822 9.76c-.094-.42.14-1.026.793-1.073l3.456-.233 4.764 7.279v-6.44l-1.215-.14c-.093-.514.28-.887.747-.933zM1.936 1.035l13.31-.98c1.634-.14 2.055-.047 3.082.7l4.249 2.986c.7.513.934.653.934 1.213v16.378c0 1.026-.373 1.634-1.68 1.726l-15.458.934c-.98.047-1.448-.093-1.962-.747l-3.129-4.06c-.56-.747-.793-1.306-.793-1.96V2.667c0-.839.374-1.54 1.447-1.632z"/>
              </svg>
              Notion 기획서
            </a> */}

            <a
              href="https://your-api-docs-link.com"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.linkItem}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="16" y1="13" x2="8" y2="13"/>
                <line x1="16" y1="17" x2="8" y2="17"/>
                <polyline points="10 9 9 9 8 9"/>
              </svg>
              API 명세서
            </a>
          </div>
        </div>

        {/* 기술 스택 */}
        <div className={styles.stack}>
          <h4 className={styles.sectionTitle}>기술 스택</h4>
          <div className={styles.stackGroups}>
            <div className={styles.stackGroup}>
              <span className={styles.stackLabel}>Frontend</span>
              <div className={styles.stackTags}>
                {['Next.js', 'TypeScript', 'CSS Modules'].map(t => (
                  <span key={t} className={styles.stackTag}>{t}</span>
                ))}
              </div>
            </div>
            <div className={styles.stackGroup}>
              <span className={styles.stackLabel}>Backend</span>
              <div className={styles.stackTags}>
                {['Flask', 'PostgreSQL', 'JWT'].map(t => (
                  <span key={t} className={styles.stackTag}>{t}</span>
                ))}
              </div>
            </div>
            <div className={styles.stackGroup}>
              <span className={styles.stackLabel}>AI</span>
              <div className={styles.stackTags}>
                {['FastAPI', 'YOLOv8', 'OpenCV'].map(t => (
                  <span key={t} className={styles.stackTag}>{t}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

      </div>

      <div className={styles.bottom}>
        <p>© 2026 WeatherAI · Team WeatherAI · All rights reserved.</p>
        <p className={styles.bottomSub}>본 프로젝트는 포트폴리오 목적으로 제작되었습니다</p>
      </div>
    </footer>
  )
}
