'use client'
import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'
import { useModalKeyboard } from '@/hooks/useModalKeyboard'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

type Comment = {
  id: number
  board_id: number
  board_type: string
  post_title: string
  post_board_type: string
  content: string
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

export default function MyCommentsPage() {
  useEffect(() => { document.title = 'Weather AI - 내 댓글' }, [])
  const router = useRouter()
  const [comments, setComments]       = useState<Comment[]>([])
  const [total, setTotal]             = useState(0)
  const [page, setPage]               = useState(1)
  const [totalPages, setTotalPages]   = useState(1)
  const [search, setSearch]           = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [boardFilter, setBoardFilter] = useState('전체')
  const [detailComment, setDetailComment] = useState<Comment | null>(null)
  const [loading, setLoading]         = useState(true)

  useModalKeyboard(!!detailComment, () => setDetailComment(null))

  const PER_PAGE = 10

  const fetchComments = useCallback(async (p: number, s: string) => {
    const token = getToken()
    if (!token) { router.push('/login'); return }
    setLoading(true)
    try {
      const res = await fetch(
        `${API}/api/board/my-comments?page=${p}&per_page=${PER_PAGE}&search=${encodeURIComponent(s)}`,
        { headers: { Authorization: `Bearer ${token}` } },
      )
      const data = await res.json()
      if (data.success) {
        setComments(data.comments)
        setTotal(data.total)
        setTotalPages(data.total_pages)
      }
    } finally {
      setLoading(false)
    }
  }, [router])

  useEffect(() => { fetchComments(page, search) }, [page, search, fetchComments])

  const handleSearch = () => {
    setPage(1)
    setSearch(searchInput)
  }

  const filtered = boardFilter === '전체'
    ? comments
    : comments.filter(c => TYPE_LABEL[c.post_board_type] === boardFilter)

  const counts = {
    total:   total,
    suggest: comments.filter(c => c.post_board_type === 'FREE').length,
    info:    comments.filter(c => c.post_board_type !== 'FREE').length,
  }

  return (
    <div className={styles.page}>
      <section className={styles.hero}>
        <div className="container">
          <Link href="/mypage" className={styles.backLink}>← 마이페이지로</Link>
          <p className={styles.eyebrow}>작성 댓글</p>
          <h1 className={styles.title}>내가 작성한 댓글</h1>
        </div>
      </section>

      <section className={styles.main}>
        <div className="container">

          <div className={styles.statsRow}>
            {[
              { label: '전체 댓글',  value: counts.total,   key: '전체',      color: '#07559d' },
              { label: '건의게시판', value: counts.suggest, key: '건의게시판', color: '#1b9bd1' },
              { label: '정보게시판', value: counts.info,    key: '정보게시판', color: '#2b8a3e' },
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
              placeholder="댓글 내용, 게시글 제목 검색..."
              className={styles.search}
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
            />
            <button className={styles.searchBtn} onClick={handleSearch}>검색</button>
            <div className={styles.filterGroup}>
              {['전체', '건의게시판', '정보게시판'].map(f => (
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
                  {['번호', '게시판', '원본 게시글', '댓글 내용', '작성일'].map(h => (
                    <th key={h} className={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr><td colSpan={5} className={styles.noData}>불러오는 중...</td></tr>
                ) : filtered.length > 0 ? filtered.map(c => (
                  <tr key={c.id} className={styles.tr} onClick={() => setDetailComment(c)}>
                    <td className={styles.td}><span className={styles.idChip}>{c.id}</span></td>
                    <td className={styles.td}>
                      <span className={`${styles.boardBadge} ${styles[TYPE_COLOR[c.post_board_type] ?? 'suggest']}`}>
                        {TYPE_LABEL[c.post_board_type] ?? c.post_board_type}
                      </span>
                    </td>
                    <td className={styles.td}><span className={styles.postRef}>{c.post_title}</span></td>
                    <td className={styles.td}><span className={styles.commentPreview}>{c.content}</span></td>
                    <td className={styles.td}>{c.created_at}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={5} className={styles.noData}>작성한 댓글이 없습니다</td></tr>
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

      {detailComment && (
        <div className={styles.overlay} onClick={() => setDetailComment(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div className={styles.modalMeta}>
                <span className={`${styles.boardBadge} ${styles[TYPE_COLOR[detailComment.post_board_type] ?? 'suggest']}`}>
                  {TYPE_LABEL[detailComment.post_board_type] ?? detailComment.post_board_type}
                </span>
                <span className={styles.modalDate}>{detailComment.created_at}</span>
              </div>
              <button className={styles.modalClose} onClick={() => setDetailComment(null)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.modalPostRef}>
                <span className={styles.modalPostLabel}>원본 게시글</span>
                <Link href={`/board/${detailComment.board_id}`} className={styles.modalPostTitle}>
                  {detailComment.post_title}
                </Link>
              </div>
              <div className={styles.modalCommentBox}>
                <span className={styles.modalCommentLabel}>내 댓글</span>
                <p className={styles.modalCommentContent}>{detailComment.content}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
