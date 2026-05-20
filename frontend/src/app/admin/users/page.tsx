'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './page.module.css'

const sideMenus = [
  { label: '대시보드', href: '/admin', icon: '📊' },
  { label: '관제센터', href: '/admin/monitor', icon: '📡' },
  { label: '사용자관리', href: '/admin/users', icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info', icon: '📋' },
]

const API_URL = process.env.NEXT_PUBLIC_API_URL

type User = {
  id: number
  login_id: string
  nickname: string
  email: string
  role: string
  active: boolean
  provider: string | null
  created_at: string | null
  profile_img_url: string | null
}

export default function UsersPage() {
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(false)
  const [users, setUsers] = useState<User[]>([])
  const [search, setSearch] = useState('')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 사용자 목록 불러오기
  const fetchUsers = async (keyword?: string) => {
    try {
      setLoading(true)
      setError(null)
      const query = new URLSearchParams({ per_page: '100' })
      if (keyword) query.append('keyword', keyword)
      const res = await fetch(`${API_URL}/api/admin/members?${query}`)
      const json = await res.json()
      if (json.success) {
        setUsers(json.data.members)
      } else {
        setError('사용자 목록을 불러오지 못했습니다.')
      }
    } catch {
      setError('서버 연결에 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [])

  // 검색은 프론트 필터링 (API 검색으로 바꾸려면 fetchUsers(search) 호출)
  const filtered = users.filter(u =>
    u.nickname.includes(search) ||
    (u.login_id ?? '').includes(search) ||
    u.email.includes(search)
  )

  const handleEdit = (user: User) => {
    setSelectedUser({ ...user })
    setModalOpen(true)
  }

  // 활성 상태 토글 (API 연동 필요 시 PATCH 요청 추가)
  const handleToggleActive = (id: number) => {
    setUsers(prev => prev.map(u => u.id === id ? { ...u, active: !u.active } : u))
  }

  // 저장 (API 연동 필요 시 PATCH /api/admin/members/:id 요청 추가)
  const handleSave = () => {
    if (!selectedUser) return
    setUsers(prev => prev.map(u => u.id === selectedUser.id ? selectedUser : u))
    setModalOpen(false)
  }

  // 날짜 포맷 (ISO → YYYY-MM-DD)
  const formatDate = (iso: string | null) => {
    if (!iso) return '-'
    return iso.slice(0, 10)
  }

  // provider null 처리
  const formatProvider = (provider: string | null) => {
    if (!provider) return '일반'
    return provider
  }

  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <div className={styles.sideLogoWrap}>
          <Link href="/"><img src="/logo.png" alt="로고" height={36} /></Link>
        </div>
        <nav className={styles.sideNav}>
          {sideMenus.map((m) => (
            <Link key={m.href} href={m.href}
              className={`${styles.sideItem} ${pathname === m.href ? styles.sideActive : ''}`}>
              <span className={styles.sideIcon}>{m.icon}</span>{m.label}
            </Link>
          ))}
          <button className={`${styles.sideItem} ${styles.sideDropBtn}`} onClick={() => setBoardOpen(!boardOpen)}>
            <span className={styles.sideIcon}>📝</span>게시글
            <span className={`${styles.arrow} ${boardOpen ? styles.arrowOpen : ''}`}>▾</span>
          </button>
          {boardOpen && (
            <div className={styles.subMenu}>
              {boardMenus.map((m) => (
                <Link key={m.href} href={m.href} className={styles.subItem}>{m.icon} {m.label}</Link>
              ))}
            </div>
          )}
        </nav>
      </aside>

      <main className={styles.main}>
        <div className={styles.topBar}>
          <h1 className={styles.pageTitle}>사용자 관리</h1>
        </div>

        {/* 검색 + 통계 */}
        <div className={styles.toolbar}>
          <div className={styles.statsRow}>
            {[
              { label: '전체 사용자', value: users.length, color: '#07559d' },
              { label: '활성 사용자', value: users.filter(u => u.active).length, color: '#1b9bd1' },
              { label: '비활성 사용자', value: users.filter(u => !u.active).length, color: '#e43b3b' },
              { label: '관리자', value: users.filter(u => u.role === 'admin').length, color: '#20436d' },
            ].map(s => (
              <div key={s.label} className={styles.statCard}>
                <span className={styles.statValue} style={{ color: s.color }}>{s.value}</span>
                <span className={styles.statLabel}>{s.label}</span>
              </div>
            ))}
          </div>
          <input
            type="text"
            placeholder="이름, 아이디, 이메일 검색..."
            className={styles.search}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* 로딩 / 에러 */}
        {loading && <p style={{ padding: '1rem' }}>불러오는 중...</p>}
        {error && <p style={{ padding: '1rem', color: '#e43b3b' }}>{error}</p>}

        {/* 테이블 */}
        {!loading && !error && (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  {['ID', '로그인ID', '닉네임', '메일주소', '권한', '가입일', '활성여부', '가입정보', '관리'].map(h => (
                    <th key={h} className={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length > 0 ? filtered.map(u => (
                  <tr key={u.id} className={styles.tr}>
                    <td className={styles.td}>{u.id}</td>
                    <td className={styles.td}><span className={styles.loginId}>{u.login_id ?? '-'}</span></td>
                    <td className={styles.td}>{u.nickname}</td>
                    <td className={styles.td}><span className={styles.email}>{u.email}</span></td>
                    <td className={styles.td}>
                      <span className={`${styles.roleBadge} ${u.role === 'admin' ? styles.roleAdmin : styles.roleUser}`}>
                        {u.role === 'admin' ? '관리자' : '일반'}
                      </span>
                    </td>
                    <td className={styles.td}>{formatDate(u.created_at)}</td>
                    <td className={styles.td}>
                      <button
                        className={`${styles.activeBadge} ${u.active ? styles.activeOn : styles.activeOff}`}
                        onClick={() => handleToggleActive(u.id)}
                      >
                        {u.active ? '활성' : '비활성'}
                      </button>
                    </td>
                    <td className={styles.td}>
                      <span className={styles.provider}>{formatProvider(u.provider)}</span>
                    </td>
                    <td className={styles.td}>
                      <button className={styles.editBtn} onClick={() => handleEdit(u)}>수정</button>
                    </td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={9} className={styles.noData}>검색 결과가 없습니다</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* 수정 모달 */}
      {modalOpen && selectedUser && (
        <div className={styles.modalOverlay} onClick={() => setModalOpen(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>사용자 정보 수정</h2>
              <button className={styles.modalClose} onClick={() => setModalOpen(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              {[
                { label: '닉네임', key: 'nickname' },
                { label: '이메일', key: 'email' },
              ].map(f => (
                <div key={f.key} className={styles.modalField}>
                  <label className={styles.modalLabel}>{f.label}</label>
                  <input
                    className={styles.modalInput}
                    value={selectedUser[f.key as keyof User] as string ?? ''}
                    onChange={e => setSelectedUser({ ...selectedUser, [f.key]: e.target.value })}
                  />
                </div>
              ))}
              <div className={styles.modalField}>
                <label className={styles.modalLabel}>권한</label>
                <select
                  className={styles.modalInput}
                  value={selectedUser.role}
                  onChange={e => setSelectedUser({ ...selectedUser, role: e.target.value })}
                >
                  <option value="user">일반</option>
                  <option value="admin">관리자</option>
                </select>
              </div>
              <div className={styles.modalField}>
                <label className={styles.modalLabel}>활성 여부</label>
                <select
                  className={styles.modalInput}
                  value={selectedUser.active ? 'true' : 'false'}
                  onChange={e => setSelectedUser({ ...selectedUser, active: e.target.value === 'true' })}
                >
                  <option value="true">활성</option>
                  <option value="false">비활성</option>
                </select>
              </div>
            </div>
            <div className={styles.modalActions}>
              <button className={styles.modalCancel} onClick={() => setModalOpen(false)}>취소</button>
              <button className={styles.modalSave} onClick={handleSave}>저장</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}