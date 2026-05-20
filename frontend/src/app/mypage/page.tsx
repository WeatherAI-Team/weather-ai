'use client'
import { useState } from 'react'
import Link from 'next/link'
import styles from './page.module.css'

type User = {
  id: number
  login_id: string
  name: string
  nickname: string
  email: string
  role: string
  grade: string
  joined: string
  posts: number
  comments: number
  provider: string
}

const gradePermissions: Record<string, { label: string; color: string; permissions: string[] }> = {
  ADMIN: {
    label: 'ADMIN',
    color: '#20436d',
    permissions: ['실시간 CCTV 분석', 'CCTV 분석 결과 확인', '리포트 생성', '탐지 이력 조회', '게시글 관리', '회원 관리'],
  },
  MANAGER: {
    label: 'MANAGER',
    color: '#07559d',
    permissions: ['실시간 CCTV 분석', 'CCTV 분석 결과 확인', '탐지 이력 조회', '게시글 작성 · 수정 · 관리'],
  },
  USER: {
    label: 'USER',
    color: '#1b9bd1',
    permissions: ['CCTV 분석 결과 확인', '탐지 이력 조회', '건의 게시글 작성/수정'],
  },
}

export default function MyPage() {
  const [user, setUser] = useState<User>({
    id: 1,
    login_id: 'hong123',
    name: '홍길동',
    nickname: '홍길동',
    email: 'hong@example.com',
    role: 'admin',
    grade: 'ADMIN',
    joined: '2025-09-01',
    posts: 37,
    comments: 21,
    provider: '일반',
  })

  const [nameModal, setNameModal] = useState(false)
  const [pwModal, setPwModal] = useState(false)
  const [notiModal, setNotiModal] = useState(false)
  const [permModal, setPermModal] = useState(false)

  const [newName, setNewName] = useState('')
  const [pwForm, setPwForm] = useState({ current: '', next: '', confirm: '' })
  const [pwError, setPwError] = useState('')
  const [noti, setNoti] = useState({ email: true, sms: false, app: true })

  const handleNameSave = () => {
    if (!newName.trim()) return
    setUser(prev => ({ ...prev, name: newName }))
    setNameModal(false)
  }

  const handlePwSave = () => {
    if (pwForm.next !== pwForm.confirm) {
      setPwError('새 비밀번호가 일치하지 않습니다')
      return
    }
    if (pwForm.next.length < 8) {
      setPwError('비밀번호는 8자 이상이어야 합니다')
      return
    }
    setPwError('')
    setPwForm({ current: '', next: '', confirm: '' })
    setPwModal(false)
    alert('비밀번호가 변경되었습니다')
  }

  const gradeInfo = gradePermissions[user.grade] || gradePermissions.USER

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
              <div className={styles.avatar}>{user.name[0]}</div>
              <h2 className={styles.profileName}>{user.name}</h2>
              <p className={styles.profileEmail}>{user.email}</p>
              <div className={styles.badges}>
                <span className={styles.roleBadge}>
                  {user.role === 'admin' ? '관리자' : user.role === 'manager' ? '매니저' : '일반회원'}
                </span>
                <span className={styles.gradeBadge} style={{ borderColor: gradeInfo.color, color: gradeInfo.color }}>
                  {user.grade}
                </span>
              </div>
              <div className={styles.profileMeta}>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>가입일</span>
                  <span className={styles.metaValue}>{user.joined}</span>
                </div>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>가입유형</span>
                  <span className={styles.metaValue}>{user.provider}</span>
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
                    <span className={styles.statNum}>{user.posts}</span>
                    <span className={styles.statLabel}>작성 게시글</span>
                  </Link>
                  <Link href="/mypage/comments" className={styles.stat}>
                    <span className={styles.statNum}>{user.comments}</span>
                    <span className={styles.statLabel}>작성 댓글</span>
                  </Link>
                </div>
              </div>

              {/* 계정 설정 */}
              <div className={styles.section}>
                <h3 className={styles.sectionTitle}>계정 설정</h3>
                <div className={styles.settingsList}>
                  <button className={styles.settingItem} onClick={() => { setNewName(user.name); setNameModal(true) }}>
                    <div className={styles.settingLeft}>
                      <span className={styles.settingIcon}>✏️</span>
                      <span className={styles.settingName}>이름 변경</span>
                    </div>
                    <span className={styles.settingArrow}>›</span>
                  </button>

                  <button className={styles.settingItem} onClick={() => { setPwForm({ current: '', next: '', confirm: '' }); setPwError(''); setPwModal(true) }}>
                    <div className={styles.settingLeft}>
                      <span className={styles.settingIcon}>🔒</span>
                      <span className={styles.settingName}>비밀번호 변경</span>
                    </div>
                    <span className={styles.settingArrow}>›</span>
                  </button>

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
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>

      {/* 이름 변경 모달 */}
      {nameModal && (
        <div className={styles.overlay} onClick={() => setNameModal(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2>이름 변경</h2>
              <button className={styles.modalClose} onClick={() => setNameModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.currentInfo}>
                <span className={styles.currentLabel}>현재 이름</span>
                <span className={styles.currentValue}>{user.name}</span>
              </div>
              <div className={styles.field}>
                <label>변경할 이름</label>
                <input className={styles.input} value={newName} onChange={e => setNewName(e.target.value)} placeholder="새 이름을 입력하세요" />
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.cancelBtn} onClick={() => setNameModal(false)}>취소</button>
              <button className={styles.saveBtn} onClick={handleNameSave}>저장</button>
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
                  onChange={e => setPwForm(p => ({ ...p, next: e.target.value }))} placeholder="8자 이상, 영문+숫자+특수문자" />
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
              <button className={styles.saveBtn} onClick={handlePwSave}>변경</button>
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
                { key: 'sms', icon: '📱', label: 'SMS 알림', desc: '위험 탐지 시 문자로 알림을 받습니다' },
                { key: 'app', icon: '🔔', label: '앱 푸시 알림', desc: '앱에서 실시간 알림을 받습니다' },
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
                  <span className={styles.gradeBig} style={{ color: gradeInfo.color }}>{user.grade}</span>
                  <span className={styles.roleTag}>{user.role === 'admin' ? '관리자' : '일반회원'}</span>
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
