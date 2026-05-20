'use client'
import styles from './KakaoLoginButton.module.css'

export default function KakaoLoginButton() {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

  const handleKakaoLogin = () => {
    window.location.href = `${API_BASE_URL}/api/auth/kakao/login`
  }

  return (
    <button type="button" className={styles.kakaoBtn} onClick={handleKakaoLogin}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
        <path fillRule="evenodd" clipRule="evenodd" d="M12 3C7.029 3 3 6.358 3 10.5c0 2.636 1.612 4.958 4.063 6.348L6.1 20.1a.5.5 0 00.724.548L11.1 17.98c.296.02.596.02.9.02 4.971 0 9-3.358 9-7.5S16.971 3 12 3z" fill="#3C1E1E"/>
      </svg>
      카카오로 로그인
    </button>
  )
}
