'use client'
import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from '../suggest/page.module.css'

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
  { id: 1, author: '관리자', title: '[공지] 시스템 정기 점검 안내', content: '5월 1일 오전 2시~4시 정기 점검이 있습니다.', views: 512, isNotice: true, active: true, createdAt: '2026-04-25' },
  { id: 2, author: '관리자', title: 'YOLOv8 모델 업데이트 안내', content: '탐지 정확도가 98.7%로 향상되었습니다.', views: 389, isNotice: false, active: true, createdAt: '2026-04-20' },
  { id: 3, author: '김분석', title: '폭우 구간 탐지 성능 분석 리포트', content: '경부고속도로 구간 탐지 성능 분석 결과입니다.', views: 241, isNotice: false, active: true, createdAt: '2026-04-18' },
  { id: 4, author: '이연구', title: '야간 안개 환경 AI 탐지율 실험', content: '야간 안개 조건에서 탐지율 향상 실험 결과입니다.', views: 178, isNotice: false, active: true, createdAt: '2026-04-15' },
  { id: 5, author: '관리자', title: '카카오맵 API 연동 업데이트', content: '관제센터 지도 기능이 업데이트되었습니다.', views: 302, isNotice: false, active: false, createdAt: '2026-04-10' },
]

type Post = typeof dummyPosts[0]

export default function InfoBoardPage() {
  const pathname = usePathname()
  const [boardOpen, setBoardOpen] = useState(true)
  const [posts, setPosts] = useState(dummyPosts)
  const [search, setSearch] = useState('')
  const [selectedPost, setSelectedPost] = useState<Post | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  const filtered = posts.filter(p =>
    p.title.includes(search) || p.author.includes(search) || p.content.includes(search)
  )

  const handleEdit = (post: Post) => { setSelectedPost({ ...post }); setModalOpen(true) }
  const handleToggleActive = (id: number) => setPosts(prev => prev.map(p => p.id === id ? { ...p, active: !p.active } : p))
  const handleToggleNotice = (id: number) => setPosts(prev => prev.map(p => p.id === id ? { ...p, isNotice: !p.isNotice } : p))
  const handleSave = () => { if (!selectedPost) return; setPosts(prev => prev.map(p => p.id === selectedPost.id ? selectedPost : p)); setModalOpen(false) }
  const handleDelete = (id: number) => { if (confirm('정말 삭제하시겠습니까?')) setPosts(prev => prev.filter(p => p.id !== id)) }

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
                    <button className={`${styles.toggleBtn} ${p.isNotice ? styles.toggleOn : styles.toggleOff}`}
                      onClick={() => handleToggleNotice(p.id)}>{p.isNotice ? '공지' : '일반'}</button>
                  </td>
                  <td className={styles.td}>
                    <button className={`${styles.toggleBtn} ${p.active ? styles.activeOn : styles.activeOff}`}
                      onClick={() => handleToggleActive(p.id)}>{p.active ? '활성' : '비활성'}</button>
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
