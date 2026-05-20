'use client'
import { useState } from 'react'
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

const dummyPosts = [
  { id: 1, author: '홍길동', title: '날씨 알림 기능 추가 건의', content: '폭우 예보 시 미리 알림을 받을 수 있으면 좋겠습니다.', views: 142, isNotice: false, active: true, createdAt: '2026-04-01' },
  { id: 2, author: '김철수', title: '지도 UI 개선 요청', content: '지도에서 지역 클릭 시 더 상세한 정보가 보였으면 합니다.', views: 89, isNotice: false, active: true, createdAt: '2026-04-05' },
  { id: 3, author: '관리자', title: '[공지] 건의게시판 이용 안내', content: '건의사항은 이곳에 작성해주세요.', views: 312, isNotice: true, active: true, createdAt: '2026-03-15' },
  { id: 4, author: '이영희', title: '모바일 화면 최적화 요청', content: '모바일에서 지도가 잘 안보입니다.', views: 67, isNotice: false, active: false, createdAt: '2026-04-10' },
  { id: 5, author: '박민준', title: 'AI 탐지 정확도 개선 건의', content: '안개 상황에서 탐지율이 낮은 것 같습니다.', views: 201, isNotice: false, active: true, createdAt: '2026-04-12' },
]

type Post = typeof dummyPosts[0]

export default function SuggestBoardPage() {
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(true)
  const [posts, setPosts] = useState(dummyPosts)
  const [search, setSearch] = useState('')
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const filtered = posts.filter(p =>
    p.title.includes(search) || p.author.includes(search) || p.content.includes(search)
  )

  const handleEdit = (post: Post) => {
    setSelectedPost({ ...post })
    setModalOpen(true)
  }

  const handleToggleActive = (id: number) => {
    setPosts(prev => prev.map(p => p.id === id ? { ...p, active: !p.active } : p))
  }

  const handleToggleNotice = (id: number) => {
    setPosts(prev => prev.map(p => p.id === id ? { ...p, isNotice: !p.isNotice } : p))
  }

  const handleSave = () => {
    if (!selectedPost) return
    setPosts(prev => prev.map(p => p.id === selectedPost.id ? selectedPost : p))
    setModalOpen(false)
  }

  const handleDelete = (id: number) => {
    if (confirm('정말 삭제하시겠습니까?')) {
      setPosts(prev => prev.filter(p => p.id !== id))
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
          <h1 className={styles.pageTitle}>건의게시판</h1>
        </div>

        <div className={styles.toolbar}>
          <div className={styles.statsRow}>
            {[
              { label: '전체 게시글', value: posts.length, color: '#07559d' },
              { label: '공지 게시글', value: posts.filter(p => p.isNotice).length, color: '#1b9bd1' },
              { label: '활성 게시글', value: posts.filter(p => p.active).length, color: '#2b8a3e' },
              { label: '비활성 게시글', value: posts.filter(p => !p.active).length, color: '#e43b3b' },
            ].map(s => (
              <div key={s.label} className={styles.statCard}>
                <span className={styles.statValue} style={{ color: s.color }}>{s.value}</span>
                <span className={styles.statLabel}>{s.label}</span>
              </div>
            ))}
          </div>
          <input
            type="text"
            placeholder="제목, 작성자, 내용 검색..."
            className={styles.search}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
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
                <tr key={p.id} className={`${styles.tr} ${p.isNotice ? styles.noticeRow : ''}`}>
                  <td className={styles.td}>{p.id}</td>
                  <td className={styles.td}>{p.author}</td>
                  <td className={styles.td}>
                    <span className={styles.title}>
                      {p.isNotice && <span className={styles.noticeBadge}>공지</span>}
                      {p.title}
                    </span>
                  </td>
                  <td className={styles.td}><span className={styles.content}>{p.content}</span></td>
                  <td className={styles.td}>{p.views}</td>
                  <td className={styles.td}>
                    <button
                      className={`${styles.toggleBtn} ${p.isNotice ? styles.toggleOn : styles.toggleOff}`}
                      onClick={() => handleToggleNotice(p.id)}
                    >
                      {p.isNotice ? '공지' : '일반'}
                    </button>
                  </td>
                  <td className={styles.td}>
                    <button
                      className={`${styles.toggleBtn} ${p.active ? styles.activeOn : styles.activeOff}`}
                      onClick={() => handleToggleActive(p.id)}
                    >
                      {p.active ? '활성' : '비활성'}
                    </button>
                  </td>
                  <td className={styles.td}>{p.createdAt}</td>
                  <td className={styles.td}>
                    <div className={styles.actions}>
                      <button className={styles.editBtn} onClick={() => handleEdit(p)}>수정</button>
                      <button className={styles.deleteBtn} onClick={() => handleDelete(p.id)}>삭제</button>
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
                <select className={styles.modalInput} value={selectedPost.isNotice ? 'true' : 'false'}
                  onChange={e => setSelectedPost({ ...selectedPost, isNotice: e.target.value === 'true' })}>
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
