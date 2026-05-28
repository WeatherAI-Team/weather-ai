'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import styles from './page.module.css'

const API = process.env.NEXT_PUBLIC_API_URL

const GRADE_INFO: Record<string, { label: string; color: string; permissions: string[] }> = {
  ADMIN: {
    label: 'ADMIN', color: '#20436d',
    permissions: ['CCTV 분석 결과 확인', '리포트 생성', '탐지 이력 조회', '게시글 관리', '회원 관리'],
  },
  MANAGER: {
    label: 'MANAGER', color: '#07559d',
    permissions: ['CCTV 분석 결과 확인', '탐지 이력 조회', '게시글 작성 · 수정 · 관리'],
  },
  USER: {
    label: 'USER', color: '#1b9bd1',
    permissions: ['건의 게시글 작성/수정'],
  },
}

const PROVIDER_LABEL: Record<string, string> = {
  local: '일반', google: '구글', kakao: '카카오', naver: '네이버',
}

const roleToGrade = (role: string) => {
  if (role === 'admin')   return 'ADMIN'
  if (role === 'manager') return 'MANAGER'
  return 'USER'
}

export default function MyPage() {
  const router = useRouter()

  const [nickname, setNickname]     = useState('')
  const [realName, setRealName]     = useState('')
  const [email, setEmail]           = useState('')
  const [role, setRole]             = useState('user')
  const [provider, setProvider]     = useState('local')
  const [joinedAt, setJoinedAt]     = useState('')
  const [loading, setLoading]       = useState(true)
  const [isSocial, setIsSocial]     = useState(false)

  const [nameModal, setNameModal]   = useState(false)
  const [pwModal, setPwModal]       = useState(false)
  const [notiModal, setNotiModal]   = useState(false)
  const [permModal, setPermModal]   = useState(false)

  const [newNickname, setNewNickname] = useState('')
  const [pwForm, setPwForm]           = useState({ current: '', next: '', confirm: '' })
  const [pwError, setPwError]         = useState('')
  const [noti, setNoti]               = useState({ email: true, sms: false, app: true })
  const [saving, setSaving]           = useState(false)
  const [postCount, setPostCount]     = useState(0)
  const [commentCount, setCommentCount] = useState(0)
  const [withdrawModal, setWithdrawModal] = useState(false)
  const [withdrawing, setWithdrawing]     = useState(false)

  const getToken = () => {
    try {
      const user = localStorage.getItem('user')
      if (user) {
        const parsed = JSON.parse(user)
        if (parsed?.access_token) return parsed.access_token
      }
      return localStorage.getItem('access_token')
    } catch { return null }
  }

  // ── 프로필 불러오기
  useEffect(() => {
    const load = async () => {
      const token = getToken()
      if (!token) { router.replace('/login'); return }
      try {
        const res  = await fetch(`${API}/api/member/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        if (!data.success) { router.replace('/login'); return }
        const m = data.data
        setNickname(m.nickname ?? '')
        setRealName(m.real_name ?? '')
        setEmail(m.email ?? '')
        setRole(m.role ?? 'user')
        setProvider(m.provider ?? 'local')
        setJoinedAt(m.created_at ? m.created_at.slice(0, 10) : '')
        setIsSocial(m.provider !== 'local')

        // 게시글/댓글 수 별도 조회
        try {
          const statsRes  = await fetch(`${API}/api/board/my-stats`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          const statsData = await statsRes.json()
          if (statsData.success) {
            setPostCount(statsData.post_count ?? 0)
            setCommentCount(statsData.comment_count ?? 0)
          }
        } catch { /* 통계 실패 시 0 유지 */ }
      } catch {
        router.replace('/login')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [router])

  const grade    = roleToGrade(role)
  const gradeInfo = GRADE_INFO[grade]
  const displayName = nickname || realName || '사용자'

  // ── 닉네임 변경
  const handleNameSave = async () => {
    if (!newNickname.trim()) return
    setSaving(true)
    const token = getToken()
    try {
      const res  = await fetch(`${API}/api/member/me`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ nickname: newNickname.trim(), email }),
      })
      const data = await res.json()
      if (!data.success) { alert(data.message); return }
      setNickname(data.data.nickname)
      // localStorage user 동기화
      const saved = localStorage.getItem('user')
      if (saved) {
        try {
          const u = JSON.parse(saved)
          localStorage.setItem('user', JSON.stringify({ ...u, nickname: data.data.nickname }))
        } catch { /* ignore */ }
      }
      setNameModal(false)
    } catch { alert('오류가 발생했습니다.') }
    finally { setSaving(false) }
  }

  // ── 회원 탈퇴
  const handleWithdraw = async () => {
    setWithdrawing(true)
    const token = getToken()
    try {
      const res  = await fetch(`${API}/api/member/me/withdraw`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      if (!data.success) { alert(data.message); return }
      localStorage.removeItem('user')
      localStorage.removeItem('access_token')
      router.replace('/login')
    } catch { alert('오류가 발생했습니다.') }
    finally { setWithdrawing(false) }
  }

  // ── 비밀번호 변경
  const handlePwSave = async () => {
    if (pwForm.next !== pwForm.confirm) { setPwError('새 비밀번호가 일치하지 않습니다.'); return }
    if (pwForm.next.length < 8)        { setPwError('비밀번호는 8자 이상이어야 합니다.'); return }
    setPwError('')
    setSaving(true)
    const token = getToken()
    try {
      const res  = await fetch(`${API}/api/member/me/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ current_password: pwForm.current, new_password: pwForm.next }),
      })
      const data = await res.json()
      if (!data.success) { setPwError(data.message); return }
      alert('비밀번호가 변경되었습니다.')
      setPwForm({ current: '', next: '', confirm: '' })
      setPwModal(false)
    } catch { setPwError('오류가 발생했습니다.') }
    finally { setSaving(false) }
  }

  if (loading) return <div style={{ padding: '80px', textAlign: 'center', color: '#5a85a8' }}>불러오는 중...</div>

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <p className={styles.eyebrow}>마이페이지</p>
          <h1 className={styles.title}>내 계정</h1>
        </div>
      </section>

      <section className={styles.main}>
        <div className="container">
          <div className={styles.grid}>

            {/* 프로필 카드 */}
            <div className={styles.profileCard}>
              <div className={styles.avatar}>{displayName[0]}</div>
              <h2 className={styles.profileName}>{displayName}</h2>
              <p className={styles.profileEmail}>{email}</p>
              <div className={styles.badges}>
                <span className={styles.roleBadge}>
                  {role === 'admin' ? '관리자' : role === 'manager' ? '매니저' : '일반회원'}
                </span>
                <span className={styles.gradeBadge} style={{ borderColor: gradeInfo.color, color: gradeInfo.color }}>
                  {grade}
                </span>
              </div>
              <div className={styles.profileMeta}>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>가입일</span>
                  <span className={styles.metaValue}>{joinedAt}</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>가입유형</span>
                  <span className={styles.metaValue}>{PROVIDER_LABEL[provider] ?? provider}</span>
                </div>
              </div>
            </div>

            {/* 우측 패널 */}
            <div className={styles.infoPanel}>

              {/* 활동 통계 */}
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>활동 통계</h3>
                <div className={styles.stats}>
                  <Link href="/mypage/posts" className={styles.stat}>
                    <span className={styles.statNum}>{postCount}</span>
                    <span className={styles.statLabel}>작성 게시글</span>
                  </Link>
                  <Link href="/mypage/comments" className={styles.stat}>
                    <span className={styles.statNum}>{commentCount}</span>
                    <span className={styles.statLabel}>작성 댓글</span>
                  </Link>
                </div>
              </div>

              {/* 계정 설정 */}
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>계정 설정</h3>
                <div className={styles.settingsList}>

                  <button className={styles.settingItem} onClick={() => { setNewNickname(nickname); setNameModal(true) }}>
                    <div className={styles.settingLeft}>
                      <span className={styles.settingIcon}>✏️</span>
                      <span className={styles.settingName}>닉네임 변경</span>
                    </div>
                    <span className={styles.settingArrow}>›</span>
                  </button>

                  {!isSocial && (
                    <button className={styles.settingItem} onClick={() => { setPwForm({ current: '', next: '', confirm: '' }); setPwError(''); setPwModal(true) }}>
                      <div className={styles.settingLeft}>
                        <span className={styles.settingIcon}>🔒</span>
                        <span className={styles.settingName}>비밀번호 변경</span>
                      </div>
                      <span className={styles.settingArrow}>›</span>
                    </button>
                  )}

                  <button className={styles.settingItem} onClick={() => setNotiModal(true)}>
                    <div className={styles.settingLeft}>
                      <span className={styles.settingIcon}>🔔</span>
                      <span className={styles.settingName}>알림 설정</span>
                    </div>
                    <span className={styles.settingArrow}>›</span>
                  </button>

                  <button className={styles.settingItem} onClick={() => setPermModal(true)}>
                    <div className={styles.settingLeft}>
                      <span className={styles.settingIcon}>🛡️</span>
                      <span className={styles.settingName}>접근 권한 확인</span>
                    </div>
                    <span className={styles.settingArrow}>›</span>
                  </button>

                  <button className={`${styles.settingItem} ${styles.settingItemDanger}`} onClick={() => setWithdrawModal(true)}>
                    <div className={styles.settingLeft}>
                      <span className={styles.settingIcon}>🚪</span>
                      <span className={`${styles.settingName} ${styles.settingNameDanger}`}>회원 탈퇴</span>
                    </div>
                    <span className={styles.settingArrow}>›</span>
                  </button>

                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* 닉네임 변경 모달 */}
      {nameModal && (
        <div className={styles.overlay} onClick={() => setNameModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>닉네임 변경</h2>
              <button className={styles.modalClose} onClick={() => setNameModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.currentInfo}>
                <span className={styles.currentLabel}>현재 닉네임</span>
                <span className={styles.currentValue}>{nickname}</span>
              </div>
              <div className={styles.field}>
                <label>변경할 닉네임</label>
                <input
                  className={styles.input}
                  value={newNickname}
                  onChange={e => setNewNickname(e.target.value)}
                  placeholder="새 닉네임을 입력하세요"
                  onKeyDown={e => e.key === 'Enter' && handleNameSave()}
                />
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={() => setNameModal(false)}>취소</button>
              <button className={styles.saveBtn} onClick={handleNameSave} disabled={saving}>
                {saving ? '저장 중...' : '저장'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 비밀번호 변경 모달 */}
      {pwModal && (
        <div className={styles.overlay} onClick={() => setPwModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>비밀번호 변경</h2>
              <button className={styles.modalClose} onClick={() => setPwModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.field}>
                <label>현재 비밀번호</label>
                <input type="password" className={styles.input} value={pwForm.current}
                  onChange={e => setPwForm(p => ({ ...p, current: e.target.value }))} placeholder="현재 비밀번호 입력" />
              </div>
              <div className={styles.field}>
                <label>새 비밀번호</label>
                <input type="password" className={styles.input} value={pwForm.next}
                  onChange={e => setPwForm(p => ({ ...p, next: e.target.value }))} placeholder="8자 이상" />
              </div>
              <div className={styles.field}>
                <label>새 비밀번호 확인</label>
                <input type="password" className={`${styles.input} ${pwError ? styles.inputError : ''}`} value={pwForm.confirm}
                  onChange={e => setPwForm(p => ({ ...p, confirm: e.target.value }))} placeholder="새 비밀번호 재입력" />
                {pwError && <p className={styles.errorMsg}>{pwError}</p>}
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={() => setPwModal(false)}>취소</button>
              <button className={styles.saveBtn} onClick={handlePwSave} disabled={saving}>
                {saving ? '변경 중...' : '변경'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 알림 설정 모달 */}
      {notiModal && (
        <div className={styles.overlay} onClick={() => setNotiModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>알림 설정</h2>
              <button className={styles.modalClose} onClick={() => setNotiModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              {[
                { key: 'email', icon: '📧', label: '이메일 알림', desc: '위험 탐지 시 이메일로 알림을 받습니다' },
                { key: 'sms',   icon: '📱', label: 'SMS 알림',   desc: '위험 탐지 시 문자로 알림을 받습니다' },
                { key: 'app',   icon: '🔔', label: '앱 푸시 알림', desc: '앱에서 실시간 알림을 받습니다' },
              ].map(n => (
                <div key={n.key} className={styles.notiRow}>
                  <div className={styles.notiLeft}>
                    <span className={styles.notiIcon}>{n.icon}</span>
                    <div>
                      <p className={styles.notiLabel}>{n.label}</p>
                      <p className={styles.notiDesc}>{n.desc}</p>
                    </div>
                  </div>
                  <button
                    className={`${styles.toggle} ${noti[n.key as keyof typeof noti] ? styles.toggleOn : styles.toggleOff}`}
                    onClick={() => setNoti(prev => ({ ...prev, [n.key]: !prev[n.key as keyof typeof noti] }))}
                  >
                    {noti[n.key as keyof typeof noti] ? 'ON' : 'OFF'}
                  </button>
                </div>
              ))}
            </div>
            <div className={styles.modalActions}>
              <button className={styles.saveBtn} style={{ flex: 1 }} onClick={() => setNotiModal(false)}>저장</button>
            </div>
          </div>
        </div>
      )}

      {/* 회원 탈퇴 확인 모달 */}
      {withdrawModal && (
        <div className={styles.overlay} onClick={() => setWithdrawModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>회원 탈퇴</h2>
              <button className={styles.modalClose} onClick={() => setWithdrawModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.withdrawWarning}>
                <p className={styles.withdrawWarningTitle}>정말로 탈퇴하시겠습니까?</p>
                <p className={styles.withdrawWarningDesc}>탈퇴 시 계정 및 모든 활동 내역이 비활성화되며, 이 작업은 되돌릴 수 없습니다.</p>
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={() => setWithdrawModal(false)}>취소</button>
              <button className={styles.withdrawBtn} onClick={handleWithdraw} disabled={withdrawing}>
                {withdrawing ? '처리 중...' : '탈퇴하기'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 접근 권한 확인 모달 */}
      {permModal && (
        <div className={styles.overlay} onClick={() => setPermModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>접근 권한 확인</h2>
              <button className={styles.modalClose} onClick={() => setPermModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.gradeCard} style={{ borderColor: gradeInfo.color }}>
                <div className={styles.gradeTop}>
                  <span className={styles.gradeBig} style={{ color: gradeInfo.color }}>{grade}</span>
                  <span className={styles.roleTag}>{role === 'admin' ? '관리자' : role === 'manager' ? '매니저' : '일반회원'}</span>
                </div>
                <p className={styles.gradeDesc}>현재 {gradeInfo.label} 등급으로 아래 기능을 이용할 수 있습니다</p>
              </div>
              <div className={styles.permList}>
                {gradeInfo.permissions.map(p => (
                  <div key={p} className={styles.permItem}>
                    <span className={styles.permCheck}>✓</span>
                    <span>{p}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.saveBtn} style={{ flex: 1 }} onClick={() => setPermModal(false)}>확인</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
