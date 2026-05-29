'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import styles from './page.module.css'

const API_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5000'

export default function FindPasswordPage() {
  useEffect(() => { document.title = 'Weather AI - 비밀번호 찾기' }, [])
  const [sent, setSent] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [email, setEmail] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!email.trim()) { setError('이메일을 입력해주세요.'); return }

    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/api/member/forgot-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      const data = await res.json()
      if (data.success) {
        setSent(true)
      } else {
        setError(data.message || '오류가 발생했습니다.')
      }
    } catch {
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
          <p>{sent ? '이메일을 확인해주세요' : '가입 시 등록한 이메일을 입력해주세요'}</p>
        </div>

        {!sent ? (
          <form className={styles.form} onSubmit={handleSubmit}>
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
              {loading ? '전송 중...' : '재설정 링크 보내기'}
            </button>
          </form>
        ) : (
          <div className={styles.done}>
            <div className={styles.doneIcon}>✓</div>
            <p className={styles.doneText}>
              <strong>{email}</strong>로<br />
              비밀번호 재설정 링크를 보냈습니다.<br />
              이메일을 확인해주세요. (15분 내 유효)
            </p>
            <button className={styles.loginButton} onClick={() => { setSent(false); setEmail('') }}>
              다시 시도
            </button>
          </div>
        )}

        <div className={styles.links}>
          <Link href="/login">로그인</Link>
          <span />
          <Link href="/find-id">아이디 찾기</Link>
          <span />
          <Link href="/register">회원가입</Link>
        </div>

      </div>
    </div>
  )
}
