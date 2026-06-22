'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from '../suggest/page.module.css'
import { useNotification } from '@/contexts/NotificationContext'

const API = process.env.NEXT_PUBLIC_API_URL

const sideMenus = [
  { label: '대시보드',     href: '/admin',               icon: '📊' },
  { label: 'AI 관제센터',  href: '/admin/monitor',        icon: '📡' },
  { label: 'CCTV 모니터링', href: '/admin/cctv',           icon: '📷' },
  { label: '알림이력',     href: '/admin/notifications',  icon: '🔔' },
  { label: '사용자관리',   href: '/admin/users',           icon: '👥' },
]
const boardMenus = [
  { label: '건의게시판', href: '/board/suggest', icon: '💬' },
  { label: '정보게시판', href: '/board/info', icon: '📋' },
  { label: '버그게시판', href: '/board/bug', icon: '🐛' },
]

type BugStatus = 'pending' | 'in_progress' | 'done'

const BUG_STATUS_LABELS: Record<BugStatus, string> = {
  pending: '미처리',
  in_progress: '진행중',
  done: '처리완료',
}

const BUG_STATUS_COLORS: Record<BugStatus, string> = {
  pending: '#e43b3b',
  in_progress: '#f59e0b',
  done: '#2b8a3e',
}

type Post = {
  id: number
  author_nickname: string
  title: string
  content: string
  board_type: string
  view_count: number
  pinned: boolean
  active: boolean
  status: BugStatus
  created_at: string
}

const previewContent = (content: string) => {
  if (content.includes('data:image') || content.includes('<img')) return '[이미지 첨부]'
  const text = content.replace(/<[^>]*>/g, '')
  return text.length > 50 ? text.slice(0, 50) + '...' : text
}

export default function BugBoardPage() {
  useEffect(() => { document.title = 'Weather AI - 버그게시판' }, [])
  const pathname = usePathname()
  const { unreadCount } = useNotification()
  const [boardOpen, setBoardOpen] = useState(true)
  const [posts, setPosts] = useState<Post[]>([])
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<BugStatus | 'all'>('all')

  const fetchPosts = async () => {
    try {
      const res = await fetch(`${API}/api/board/admin/posts?board_type=BUG&per_page=200`, {
        credentials: 'include',
      })
      const data = await res.json()
      if (data.success) setPosts(data.posts)
    } catch {}
  }

  useEffect(() => { fetchPosts() }, [])

  const filtered = posts
    .filter(p => statusFilter === 'all' || p.status === statusFilter)
    .filter(p =>
      p.title.includes(search) || p.author_nickname.includes(search) || p.content.includes(search)
    )

  const handleToggleActive = async (id: number) => {
    const res = await fetch(`${API}/api/board/admin/posts/${id}/toggle-active`, {
      method: 'PATCH',
      credentials: 'include',
    })
    const data = await res.json()
    if (data.success) {
      setPosts(prev => prev.map(p => p.id === id ? { ...p, active: data.active } : p))
    } else {
      alert(data.message ?? '오류가 발생했습니다.')
    }
  }

  const handleStatusChange = async (id: number, status: BugStatus) => {
    try {
      const res = await fetch(`${API}/api/board/posts/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ status }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.message)
      setPosts(prev => prev.map(p => p.id === id ? { ...p, status: data.post?.status ?? status } : p))
    } catch (e: any) {
      alert(e.message ?? '상태 변경 실패')
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
              {m.href === '/admin/notifications' && unreadCount > 0 && (
                <span className={styles.notiBadge}>{unreadCount > 99 ? '99+' : unreadCount}</span>
              )}
            </Link>
          ))}
          <button className={`${styles.sideItem} ${styles.sideDropBtn}`} onClick={() => setBoardOpen(!boardOpen)}>
            <span className={styles.sideIcon}>📝</span>게시글 관리
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
          <h1 className={styles.pageTitle}>버그게시판</h1>
        </div>

        <div className={styles.toolbar}>
          <div className={styles.statsRow}>
            {[
              { label: '전체 게시글', value: posts.length, color: '#07559d' },
              { label: '미처리', value: posts.filter(p => p.status === 'pending').length, color: '#e43b3b' },
              { label: '진행중', value: posts.filter(p => p.status === 'in_progress').length, color: '#f59e0b' },
              { label: '처리완료', value: posts.filter(p => p.status === 'done').length, color: '#2b8a3e' },
            ].map(s => (
              <div key={s.label} className={styles.statCard}>
                <span className={styles.statValue} style={{ color: s.color }}>{s.value}</span>
                <span className={styles.statLabel}>{s.label}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as BugStatus | 'all')}
              className={styles.search}
              style={{ width: 'auto' }}
            >
              <option value="all">전체 상태</option>
              <option value="pending">미처리</option>
              <option value="in_progress">진행중</option>
              <option value="done">처리완료</option>
            </select>
            <input type="text" placeholder="제목, 작성자, 내용 검색..." className={styles.search}
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>

        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                {['ID', '작성자', '제목', '내용', '조회수', '처리상태', '활성여부', '작성일'].map(h => (
                  <th key={h} className={styles.th}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length > 0 ? filtered.map(p => (
                <tr key={p.id} className={styles.tr}>
                  <td className={styles.td}>{p.id}</td>
                  <td className={styles.td}>{p.author_nickname}</td>
                  <td className={styles.td}><span className={styles.title}>{p.title}</span></td>
                  <td className={styles.td}>
                    <span className={styles.content}>{previewContent(p.content)}</span>
                  </td>
                  <td className={styles.td}>{p.view_count}</td>
                  <td className={styles.td}>
                    <select
                      value={p.status ?? 'pending'}
                      onChange={e => handleStatusChange(p.id, e.target.value as BugStatus)}
                      style={{
                        padding: '3px 8px',
                        borderRadius: '6px',
                        border: '1px solid #ddd',
                        fontSize: '12px',
                        fontWeight: 600,
                        color: BUG_STATUS_COLORS[p.status ?? 'pending'],
                        cursor: 'pointer',
                      }}
                    >
                      <option value="pending">미처리</option>
                      <option value="in_progress">진행중</option>
                      <option value="done">처리완료</option>
                    </select>
                  </td>
                  <td className={styles.td}>
                    <button className={`${styles.toggleBtn} ${p.active ? styles.activeOn : styles.activeOff}`}
                      onClick={() => handleToggleActive(p.id)}>{p.active ? '활성' : '비활성'}</button>
                  </td>
                  <td className={styles.td}>{p.created_at}</td>
                </tr>
              )) : (
                <tr><td colSpan={8} className={styles.noData}>검색 결과가 없습니다</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}