'use client'
import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import styles from './page.module.css'

function AuthCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('로그인 처리 중...')

  useEffect(() => {
    const token = searchParams.get('token')
    const provider = searchParams.get('provider')
    const error = searchParams.get('error')

    if (error) {
      setStatus('error')
      setMessage('로그인에 실패했습니다. 다시 시도해주세요.')
      setTimeout(() => router.push('/login'), 2500)
      return
    }

    if (!token) {
      setStatus('error')
      setMessage('토큰 정보가 없습니다.')
      setTimeout(() => router.push('/login'), 2500)
      return
    }

    try {
      localStorage.setItem('access_token', token)
      if (provider) localStorage.setItem('login_provider', provider)

      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

      fetch(`${API_BASE_URL}/api/member/me`, {
        headers: { Authorization: `Bearer ${token}` },
        credentials: 'include',
      })
        .then(res => res.json())
        .then(data => {
          if (data?.data) {
            localStorage.setItem('user', JSON.stringify({
              ...data.data,
              access_token: token,   // URL에서 받은 token 사용
            }))
            localStorage.setItem('loginUser', JSON.stringify(data.data))
          }
        })
        .catch(() => {})
        .finally(() => {
          setStatus('success')
          setMessage('로그인 성공! 메인 페이지로 이동합니다.')
          setTimeout(() => { window.location.href = '/' }, 1500)
        })
    } catch {
      setStatus('error')
      setMessage('처리 중 오류가 발생했습니다.')
      setTimeout(() => router.push('/login'), 2500)
    }
  }, [searchParams, router])

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <div className={styles.logoWrap}>
          <img src="/logo.png" alt="WeatherAI 로고" height={40} />
        </div>

        {status === 'loading' && (
          <>
            <div className={styles.spinner} />
            <p className={styles.message}>{message}</p>
          </>
        )}
        {status === 'success' && (
          <>
            <div className={styles.successIcon}>✓</div>
            <p className={`${styles.message} ${styles.successMsg}`}>{message}</p>
          </>
        )}
        {status === 'error' && (
          <>
            <div className={styles.errorIcon}>✕</div>
            <p className={`${styles.message} ${styles.errorMsg}`}>{message}</p>
            <p className={styles.sub}>잠시 후 로그인 페이지로 이동합니다...</p>
          </>
        )}
      </div>
    </div>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className={styles.page}>
        <div className={styles.card}>
          <div className={styles.spinner} />
          <p className={styles.message}>로그인 처리 중...</p>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  )
}
