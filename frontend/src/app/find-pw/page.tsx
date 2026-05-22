'use client'
import { useState } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

export default function FindPasswordPage() {
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // 1단계: 본인 확인
  const [loginId, setLoginId] = useState('')
  const [email, setEmail] = useState('')

  // 2단계: 새 비밀번호
  const [newPw, setNewPw] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  // ── 1단계: 아이디 + 이메일 확인 ──
  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!loginId.trim() || !email.trim()) {
      setError('아이디와 이메일을 모두 입력해주세요.')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/auth/verify-account`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login_id: loginId, email }),
      })
      const data = await res.json()

      if (data.success) {
        setStep(2)
      } else {
        setError(data.message || '일치하는 계정 정보가 없습니다.')
      }
    } catch (err) {
      console.error(err)
      setError('서버 연결에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  // ── 2단계: 새 비밀번호 설정 ──
  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (newPw.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.')
      return
    }
    if (newPw !== confirmPw) {
      setError('새 비밀번호가 일치하지 않습니다.')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login_id: loginId, email, new_password: newPw }),
      })
      const data = await res.json()

      if (data.success) {
        setStep(3)
      } else {
        setError(data.message || '비밀번호 재설정에 실패했습니다.')
      }
    } catch (err) {
      console.error(err)
      setError('서버 연결에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.loginCard}>

        <div className={styles.header}>
          <div className={styles.logoWrap}>
            <Image src="/logo.png" alt="WeatherAI 로고" width={0} height={0} sizes="100vw" style={{ width: 'auto', height: '48px' }} />
          </div>
          <h1>비밀번호 찾기</h1>
          <p>
            {step === 1 && '가입 시 등록한 아이디와 이메일을 입력해주세요'}
            {step === 2 && '새로운 비밀번호를 설정해주세요'}
            {step === 3 && '비밀번호가 성공적으로 변경되었습니다'}
          </p>
        </div>

        {/* 단계 표시 */}
        {step < 3 && (
          <div className={styles.steps}>
            <div className={`${styles.stepDot} ${step >= 1 ? styles.stepActive : ''}`}>1</div>
            <div className={`${styles.stepLine} ${step >= 2 ? styles.stepActive : ''}`} />
            <div className={`${styles.stepDot} ${step >= 2 ? styles.stepActive : ''}`}>2</div>
          </div>
        )}

        {/* ── 1단계: 본인 확인 ── */}
        {step === 1 && (
          <form className={styles.form} onSubmit={handleVerify}>
            <label className={styles.field}>
              <span>아이디</span>
              <input
                type="text"
                placeholder="아이디 입력"
                value={loginId}
                onChange={e => setLoginId(e.target.value)}
              />
            </label>
            <label className={styles.field}>
              <span>이메일</span>
              <input
                type="email"
                placeholder="가입 시 등록한 이메일"
                value={email}
                onChange={e => setEmail(e.target.value)}
              />
            </label>

            {error && <p className={styles.error}>{error}</p>}

            <button type="submit" className={styles.loginButton} disabled={loading}>
              {loading ? '확인 중...' : '다음'}
            </button>
          </form>
        )}

        {/* ── 2단계: 새 비밀번호 ── */}
        {step === 2 && (
          <form className={styles.form} onSubmit={handleReset}>
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
              {loading ? '변경 중...' : '비밀번호 재설정'}
            </button>
          </form>
        )}

        {/* ── 3단계: 완료 ── */}
        {step === 3 && (
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
        )}

        {/* 하단 링크 */}
        {step < 3 && (
          <div className={styles.links}>
            <Link href="/login">로그인</Link>
            <span />
            <Link href="/find-id">아이디 찾기</Link>
            <span />
            <Link href="/register">회원가입</Link>
          </div>
        )}

      </div>
    </div>
  )
}
