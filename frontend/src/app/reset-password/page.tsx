'use client'
import { useState, Suspense } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useSearchParams, useRouter } from 'next/navigation'
import styles from '../find-pw/page.module.css'

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

function ResetForm() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const token = searchParams.get('token')

  const [done, setDone] = useState(false)
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    if (newPw.length < 8) { setError('비밀번호는 8자 이상이어야 합니다.'); return }
    if (newPw !== confirmPw) { setError('비밀번호가 일치하지 않습니다.'); return }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/member/reset-password?token=${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_password: newPw }),
      })
      const data = await res.json()
      if (data.success) {
        setDone(true)
      } else {
        setError(data.message || '비밀번호 재설정에 실패했습니다.')
      }
    } catch {
      setError('서버 연결에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // 토큰 없음 - 잘못된 접근
  if (!token) {
    return (
      <div className={styles.page}>
        <div className={styles.loginCard}>
          <div className={styles.header}>
            <div className={styles.logoWrap}>
              <Image src="/logo.png" alt="WeatherAI 로고" width={0} height={0} sizes="100vw" style={{ width: 'auto', height: '48px' }} />
            </div>
            <h1>비밀번호 재설정</h1>
            <p>유효하지 않은 링크입니다</p>
          </div>
          <div className={styles.done}>
            <div className={styles.doneIcon} style={{ background: '#d64545' }}>✕</div>
            <p className={styles.doneText}>
              유효하지 않거나 만료된 링크입니다.<br />
              비밀번호 찾기를 다시 시도해주세요.
            </p>
            <Link href="/find-pw" style={{ width: '100%', textDecoration: 'none' }}>
              <button className={styles.loginButton} style={{ width: '100%' }}>비밀번호 찾기</button>
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // 변경 완료
  if (done) {
    return (
      <div className={styles.page}>
        <div className={styles.loginCard}>
          <div className={styles.header}>
            <div className={styles.logoWrap}>
              <Image src="/logo.png" alt="WeatherAI 로고" width={0} height={0} sizes="100vw" style={{ width: 'auto', height: '48px' }} />
            </div>
            <h1>비밀번호 재설정</h1>
            <p>비밀번호가 성공적으로 변경되었습니다</p>
          </div>
          <div className={styles.done}>
            <div className={styles.doneIcon}>✓</div>
            <p className={styles.doneText}>
              비밀번호가 변경되었습니다.<br />
              새 비밀번호로 로그인해주세요.
            </p>
            <button className={styles.loginButton} onClick={() => router.push('/login')}>
              로그인하러 가기
            </button>
          </div>
        </div>
      </div>
    )
  }

  // 비밀번호 입력 폼
  return (
    <div className={styles.page}>
      <div className={styles.loginCard}>

        <div className={styles.header}>
          <div className={styles.logoWrap}>
            <Image src="/logo.png" alt="WeatherAI 로고" width={0} height={0} sizes="100vw" style={{ width: 'auto', height: '48px' }} />
          </div>
          <h1>비밀번호 재설정</h1>
          <p>새로운 비밀번호를 설정해주세요</p>
        </div>

        <form className={styles.form} onSubmit={handleSubmit}>
          <label className={styles.field}>
            <span>새 비밀번호</span>
            <input
              type="password"
              placeholder="8자 이상, 영문+숫자+특수문자"
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
            />
          </label>
          <label className={styles.field}>
            <span>새 비밀번호 확인</span>
            <input
              type="password"
              placeholder="새 비밀번호 재입력"
              value={confirmPw}
              onChange={e => setConfirmPw(e.target.value)}
            />
          </label>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" className={styles.loginButton} disabled={loading}>
            {loading ? '변경 중...' : '비밀번호 변경'}
          </button>
        </form>

        <div className={styles.links}>
          <Link href="/login">로그인</Link>
          <span />
          <Link href="/find-pw">비밀번호 찾기</Link>
        </div>

      </div>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <ResetForm />
    </Suspense>
  )
}
