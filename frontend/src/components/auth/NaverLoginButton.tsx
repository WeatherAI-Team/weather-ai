'use client'
import styles from './NaverLoginButton.module.css'

export default function NaverLoginButton() {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

  const handleNaverLogin = () => {
    window.location.href = `${API_BASE_URL}/api/auth/naver/login`
  }

  return (
    <button type="button" className={styles.naverBtn} onClick={handleNaverLogin}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="4" fill="#03C75A"/>
        <path d="M13.6 12.3L10.2 7H7v10h3.4V11.7L14.2 17H17V7h-3.4v5.3z" fill="white"/>
      </svg>
      네이버로 로그인
    </button>
  )
}
