'use client'
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'
import { useModalKeyboard } from '@/hooks/useModalKeyboard'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

type Post = {
  id: number
  board_type: string
  title: string
  content: string
  view_count: number
  comment_count: number
  created_at: string
}

const TYPE_LABEL: Record<string, string> = {
  FREE:   '건의게시판',
  INFO:   '정보게시판',
  NOTICE: '정보게시판',
}
const TYPE_COLOR: Record<string, string> = {
  FREE:   'suggest',
  INFO:   'info',
  NOTICE: 'info',
}

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('user')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed?.access_token) return parsed.access_token
    }
    return localStorage.getItem('access_token')
  } catch { return null }
}

function getRole(): string {
  try {
    const raw = localStorage.getItem('user')
    if (raw) {
      const parsed = JSON.parse(raw)
      if (parsed?.role) return parsed.role
    }
  } catch { /* ignore */ }
  return 'user'
}

export default function MyPostsPage() {
  useEffect(() => { document.title = 'Weather AI - 내 게시글' }, [])
  const router = useRouter()
  const [role, setRole]             = useState('user')
  const [posts, setPosts]           = useState<Post[]>([])
  const [total, setTotal]           = useState(0)
  const [page, setPage]             = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [search, setSearch]         = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [boardFilter, setBoardFilter] = useState('전체')
  const [detailPost, setDetailPost]   = useState<Post | null>(null)
  const [loading, setLoading]         = useState(true)

  useEffect(() => { setRole(getRole()) }, [])

  useModalKeyboard(!!detailPost, () => setDetailPost(null))

  const PER_PAGE = 10

  const fetchPosts = useCallback(async (p: number, s: string) => {
    const token = getToken()
    if (!token) { router.push('/login'); return }
    setLoading(true)
    try {
      const res = await fetch(
        `${API}/api/board/my-posts?page=${p}&per_page=${PER_PAGE}&search=${encodeURIComponent(s)}`,
        { headers: { Authorization: `Bearer ${token}` } },
      )
      const data = await res.json()
      if (data.success) {
        setPosts(data.posts)
        setTotal(data.total)
        setTotalPages(data.total_pages)
      }
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => { fetchPosts(page, search) }, [page, search, fetchPosts])

  const handleSearch = () => {
    setPage(1)
    setSearch(searchInput)
  }

  const isUser = role === 'user'

  const visiblePosts = isUser ? posts.filter(p => p.board_type === 'FREE') : posts

  const filtered = boardFilter === '전체'
    ? visiblePosts
    : visiblePosts.filter(p => TYPE_LABEL[p.board_type] === boardFilter)

  const counts = {
    total:   isUser ? visiblePosts.length : total,
    suggest: visiblePosts.filter(p => p.board_type === 'FREE').length,
    info:    visiblePosts.filter(p => p.board_type !== 'FREE').length,
  }

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <Link href="/mypage" className={styles.backLink}>← 마이페이지로</Link>
          <p className={styles.eyebrow}>작성 게시글</p>
          <h1 className={styles.title}>내가 작성한 게시글</h1>
        </div>
      </section>

      <section className={styles.main}>
        <div className="container">

          <div className={styles.statsRow}>
            {[
              { label: '전체 게시글', value: counts.total,   key: '전체',      color: '#07559d' },
              { label: '건의게시판',  value: counts.suggest, key: '건의게시판', color: '#1b9bd1' },
              ...(!isUser ? [{ label: '정보게시판', value: counts.info, key: '정보게시판', color: '#2b8a3e' }] : []),
            ].map(s => (
              <button
                key={s.key}
                className={`${styles.statCard} ${boardFilter === s.key ? styles.statCardActive : ''}`}
                onClick={() => setBoardFilter(boardFilter === s.key ? '전체' : s.key)}
              >
                <span className={styles.statNum} style={{ color: s.color }}>{s.value}</span>
                <span className={styles.statLabel}>{s.label}</span>
              </button>
            ))}
          </div>

          <div className={styles.toolbar}>
            <input
              type="text"
              placeholder="제목, 내용 검색..."
              className={styles.search}
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
            <button className={styles.searchBtn} onClick={handleSearch}>검색</button>
            <div className={styles.filterGroup}>
              {['전체', '건의게시판', ...(!isUser ? ['정보게시판'] : [])].map(f => (
                <button
                  key={f}
                  className={`${styles.filterBtn} ${boardFilter === f ? styles.filterActive : ''}`}
                  onClick={() => setBoardFilter(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  {['번호', '게시판', '제목', '조회수', '작성일'].map(h => (
                    <th key={h} className={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className={styles.noData}>불러오는 중...</td></tr>
                ) : filtered.length > 0 ? filtered.map(p => (
                  <tr key={p.id} className={styles.tr} onClick={() => setDetailPost(p)}>
                    <td className={styles.td}><span className={styles.idChip}>{p.id}</span></td>
                    <td className={styles.td}>
                      <span className={`${styles.boardBadge} ${styles[TYPE_COLOR[p.board_type] ?? 'suggest']}`}>
                        {TYPE_LABEL[p.board_type] ?? p.board_type}
                      </span>
                    </td>
                    <td className={styles.td}><span className={styles.postTitle}>{p.title}</span></td>
                    <td className={styles.td}>{p.view_count.toLocaleString()}</td>
                    <td className={styles.td}>{p.created_at}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={5} className={styles.noData}>작성한 게시글이 없습니다</td></tr>
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className={styles.pageBtn}
                disabled={page <= 1}
                onClick={() => setPage(p => p - 1)}
              >이전</button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(n => (
                <button
                  key={n}
                  className={`${styles.pageBtn} ${page === n ? styles.pageBtnActive : ''}`}
                  onClick={() => setPage(n)}
                >{n}</button>
              ))}
              <button
                className={styles.pageBtn}
                disabled={page >= totalPages}
                onClick={() => setPage(p => p + 1)}
              >다음</button>
            </div>
          )}

        </div>
      </section>

      {detailPost && (
        <div className={styles.overlay} onClick={() => setDetailPost(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div className={styles.modalMeta}>
                <span className={`${styles.boardBadge} ${styles[TYPE_COLOR[detailPost.board_type] ?? 'suggest']}`}>
                  {TYPE_LABEL[detailPost.board_type] ?? detailPost.board_type}
                </span>
                <span className={styles.modalDate}>{detailPost.created_at}</span>
              </div>
              <button className={styles.modalClose} onClick={() => setDetailPost(null)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <h2 className={styles.modalTitle}>{detailPost.title}</h2>
              <p className={styles.modalContent}>{detailPost.content}</p>
            </div>
            <div className={styles.modalFooter}>
              <span className={styles.modalViews}>조회 {detailPost.view_count.toLocaleString()}</span>
              <Link href={`/board/${detailPost.id}`} className={styles.modalLink}>게시글 보기 →</Link>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
