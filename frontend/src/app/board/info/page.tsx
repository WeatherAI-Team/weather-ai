'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from '../suggest/page.module.css'
import { useModalKeyboard } from '@/hooks/useModalKeyboard'

const API = process.env.NEXT_PUBLIC_API_URL

const sideMenus = [
  { label: '대시보드', href: '/admin', icon: '📊' },
  { label: '관제센터', href: '/admin/monitor', icon: '📡' },
  { label: '사용자관리', href: '/admin/users', icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info', icon: '📋' },
]

type Post = {
  id: number
  author_nickname: string
  title: string
  content: string
  board_type: string
  view_count: number
  pinned: boolean
  active: boolean
  created_at: string
}

const getToken = (): string => {
  try { return JSON.parse(localStorage.getItem('user') ?? 'null')?.access_token ?? '' } catch { return '' }
}

export default function InfoBoardPage() {
  useEffect(() => { document.title = 'Weather AI - 정보게시판' }, [])
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(true)
  const [posts, setPosts] = useState<Post[]>([])
  const [search, setSearch] = useState('')
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  useModalKeyboard(modalOpen, () => setModalOpen(false))

  const fetchPosts = async () => {
    try {
      const res = await fetch(`${API}/api/board/admin/posts?board_type=INFO,NOTICE&per_page=200`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      })
      const data = await res.json()
      if (data.success) setPosts(data.posts)
    } catch {}
  }

  useEffect(() => { fetchPosts() }, [])

  const filtered = posts.filter(p =>
    p.title.includes(search) || p.author_nickname.includes(search) || p.content.includes(search)
  )

  const handleEdit = (post: Post) => { setSelectedPost({ ...post }); setModalOpen(true) }

  const handleToggleActive = async (id: number) => {
    const res = await fetch(`${API}/api/board/admin/posts/${id}/toggle-active`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    const data = await res.json()
    if (data.success) {
      setPosts(prev => prev.map(p => p.id === id ? { ...p, active: data.active } : p))
    } else {
      alert(data.message ?? '오류가 발생했습니다.')
    }
  }

  const handleTogglePinned = async (id: number) => {
    const res = await fetch(`${API}/api/board/admin/posts/${id}/toggle-pinned`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    const data = await res.json()
    if (data.success) {
      setPosts(prev => prev.map(p => p.id === id ? { ...p, pinned: data.pinned } : p))
    } else {
      alert(data.message ?? '오류가 발생했습니다.')
    }
  }

  const handleSave = async () => {
    if (!selectedPost) return
    const res = await fetch(`${API}/api/board/posts/${selectedPost.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({
        title: selectedPost.title,
        content: selectedPost.content,
        pinned: selectedPost.pinned,
        active: selectedPost.active,
      }),
    })
    const data = await res.json()
    if (data.success) {
      setPosts(prev => prev.map(p => p.id === selectedPost.id ? data.post : p))
      setModalOpen(false)
    } else {
      alert(data.message ?? '수정에 실패했습니다.')
    }
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
                <Link key={m.href} href={m.href}
                  className={`${styles.subItem} ${pathname === m.href ? styles.subActive : ''}`}>
                  {m.icon} {m.label}
                </Link>
              ))}
            </div>
          )}
        </nav>
      </aside>

      <main className={styles.main}>
        <div className={styles.topBar}>
          <h1 className={styles.pageTitle}>정보게시판</h1>
        </div>

        <div className={styles.toolbar}>
          <div className={styles.statsRow}>
            {[
              { label: '전체 게시글', value: posts.length, color: '#07559d' },
              { label: '공지 게시글', value: posts.filter(p => p.pinned).length, color: '#1b9bd1' },
              { label: '활성 게시글', value: posts.filter(p => p.active).length, color: '#2b8a3e' },
              { label: '비활성 게시글', value: posts.filter(p => !p.active).length, color: '#e43b3b' },
            ].map(s => (
              <div key={s.label} className={styles.statCard}>
                <span className={styles.statValue} style={{ color: s.color }}>{s.value}</span>
                <span className={styles.statLabel}>{s.label}</span>
              </div>
            ))}
          </div>
          <input type="text" placeholder="제목, 작성자, 내용 검색..." className={styles.search}
            value={search} onChange={e => setSearch(e.target.value)} />
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                {['ID', '작성자', '제목', '내용', '조회수', '공지여부', '활성여부', '작성일', '관리'].map(h => (
                  <th key={h} className={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length > 0 ? filtered.map(p => (
                <tr key={p.id} className={`${styles.tr} ${p.pinned ? styles.noticeRow : ''}`}>
                  <td className={styles.td}>{p.id}</td>
                  <td className={styles.td}>{p.author_nickname}</td>
                  <td className={styles.td}>
                    <span className={styles.title}>
                      {p.pinned && <span className={styles.noticeBadge}>공지</span>}
                      {p.title}
                    </span>
                  </td>
                  <td className={styles.td}><span className={styles.content}>{p.content}</span></td>
                  <td className={styles.td}>{p.view_count}</td>
                  <td className={styles.td}>
                    <button className={`${styles.toggleBtn} ${p.pinned ? styles.toggleOn : styles.toggleOff}`}
                      onClick={() => handleTogglePinned(p.id)}>{p.pinned ? '공지' : '일반'}</button>
                  </td>
                  <td className={styles.td}>
                    <button className={`${styles.toggleBtn} ${p.active ? styles.activeOn : styles.activeOff}`}
                      onClick={() => handleToggleActive(p.id)}>{p.active ? '활성' : '비활성'}</button>
                  </td>
                  <td className={styles.td}>{p.created_at}</td>
                  <td className={styles.td}>
                    <div className={styles.actions}>
                      <button className={styles.editBtn} onClick={() => handleEdit(p)}>수정</button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={9} className={styles.noData}>검색 결과가 없습니다</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>

      {modalOpen && selectedPost && (
        <div className={styles.modalOverlay} onClick={() => setModalOpen(false)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <h2 className={styles.modalTitle}>게시글 수정</h2>
              <button className={styles.modalClose} onClick={() => setModalOpen(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.modalField}>
                <label className={styles.modalLabel}>제목</label>
                <input className={styles.modalInput} value={selectedPost.title}
                  onChange={e => setSelectedPost({ ...selectedPost, title: e.target.value })} />
              </div>
              <div className={styles.modalField}>
                <label className={styles.modalLabel}>내용</label>
                <textarea className={styles.modalTextarea} value={selectedPost.content}
                  onChange={e => setSelectedPost({ ...selectedPost, content: e.target.value })} />
              </div>
              <div className={styles.modalField}>
                <label className={styles.modalLabel}>공지 여부</label>
                <select className={styles.modalInput} value={selectedPost.pinned ? 'true' : 'false'}
                  onChange={e => setSelectedPost({ ...selectedPost, pinned: e.target.value === 'true' })}>
                  <option value="false">일반</option>
                  <option value="true">공지</option>
                </select>
              </div>
              <div className={styles.modalField}>
                <label className={styles.modalLabel}>활성 여부</label>
                <select className={styles.modalInput} value={selectedPost.active ? 'true' : 'false'}
                  onChange={e => setSelectedPost({ ...selectedPost, active: e.target.value === 'true' })}>
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
