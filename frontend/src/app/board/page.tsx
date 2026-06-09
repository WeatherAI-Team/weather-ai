'use client'
import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import styles from './page.module.css'

// ─────────────────────────────────────────
// 타입 (API 응답 + 화면 표시용)
// ─────────────────────────────────────────
type Post = {
  id: number
  category: string          // 화면 표시용 한글 (공지/정보/건의/버그/자료)
  title: string
  author_nickname: string
  created_at: string
  views: number
  comment_count?: number
  attachment_count?: number
}

// board_type(DB) → category(화면) 변환
const toCategory = (board_type: string): string => {
  if (board_type === 'NOTICE') return '공지'
  if (board_type === 'INFO')   return '정보'
  if (board_type === 'BUG')    return '버그'
  if (board_type === 'DATA')   return '자료'
  return '건의'
}

const SEARCH_TYPES = [
  { value: 'title',   label: '제목' },
  { value: 'content', label: '내용' },
  { value: 'all',     label: '제목+내용' },
]

// ─────────────────────────────────────────
// Fallback mock (백엔드 미연결 시)
// ─────────────────────────────────────────
const MOCK_NOTICES: Post[] = [
  { id: 1, category: '공지', title: '시스템 정기 점검 안내 (5월 1일)', author_nickname: '관리자', created_at: '2026-04-25', views: 312, comment_count: 3 },
]
const MOCK_INFO: Post[] = [
  { id: 2, category: '정보', title: '경부고속도로 폭우 상황 탱크로리 탐지 성공 보고', author_nickname: '홍길동', created_at: '2026-04-24', views: 589, comment_count: 12, attachment_count: 3 },
  { id: 3, category: '정보', title: '눈보라 조건에서 YOLOv8 모델 성능 분석 리포트', author_nickname: '김분석', created_at: '2026-04-22', views: 441, comment_count: 5, attachment_count: 1 },
  { id: 4, category: '정보', title: '중부내륙고속도로 안개 구간 LPG 차량 감지', author_nickname: '이탐지', created_at: '2026-04-20', views: 378, comment_count: 0 },
  { id: 5, category: '정보', title: 'FastAPI와 Flask 간 통신 지연 문제 해결 방법 공유', author_nickname: '박개발', created_at: '2026-04-18', views: 215, comment_count: 7 },
  { id: 6, category: '정보', title: '야간 폭우 환경에서의 탐지율 향상 실험', author_nickname: '최연구', created_at: '2026-04-16', views: 302, comment_count: 2 },
]
const MOCK_SUGGEST: Post[] = [
  { id: 7, category: '건의', title: '탐지 알림 소리 크기 조절 기능 추가 요청', author_nickname: '김건의', created_at: '2026-04-23', views: 87, comment_count: 4 },
  { id: 8, category: '건의', title: '야간 모드 UI 지원 건의', author_nickname: '이사용자', created_at: '2026-04-19', views: 134, comment_count: 1, attachment_count: 2 },
]

const PAGE_SIZE = 10

export default function BoardPage() {
  useEffect(() => { document.title = 'Weather AI - 게시판' }, [])
  const router = useRouter()
  const [tab, setTab] = useState<'info' | 'suggest' | 'bug' | 'data'>('info')
  const [searchType, setSearchType] = useState('title')
  const [searchInput, setSearchInput] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [page, setPage]             = useState(1)
  const [notices, setNotices]       = useState<Post[]>([])
  const [posts, setPosts]           = useState<Post[]>([])
  const [totalPages, setTotalPages] = useState(1)
  const [loading, setLoading]       = useState(false)
  const [userRole, setUserRole]     = useState<string>('')
  const [loginAlert, setLoginAlert] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem('user')
    if (saved) {
      try { setUserRole(JSON.parse(saved).role ?? '') } catch { /* ignore */ }
    }
  }, [])

  const fetchPosts = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        board_type:  tab,          // Flask board_service의 _BOARD_TYPE_MAP 키와 일치
        page:        String(page),
        search:      searchQuery,
        search_type: searchType,
        per_page:    String(PAGE_SIZE),
      })
      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts?${params}`)
      const data = await res.json()

      if (data.success) {
        // API 응답의 board_type → 화면용 category 변환
        const mapPost = (p: any): Post => ({
          id:               p.id,
          category:         toCategory(p.board_type),
          title:            p.title,
          author_nickname:  p.author_nickname,
          created_at:       p.created_at,
          views:            p.view_count,
          comment_count:    p.comment_count ?? 0,
          attachment_count: p.attachment_count ?? 0,
        })

        // pinned(공지) 분리: board_type=NOTICE 또는 pinned=true
        const allPosts = data.posts.map(mapPost)
        setNotices(allPosts.filter((_: Post, i: number) => data.posts[i].pinned))
        setPosts(allPosts.filter((_: Post, i: number) => !data.posts[i].pinned))
        setTotalPages(data.total_pages)
        setLoading(false)
        return
      }
    } catch {
      // 백엔드 미연결 시 mock 사용
    }

    // ── mock fallback ──
    // 백엔드 연결이 안 됐을 때 임시로 보여줄 데이터
    const source =
      tab === 'info'
        ? MOCK_INFO
        : tab === 'bug'
          ? []
          : tab === 'data'
            ? []
            : MOCK_SUGGEST
    const filtered = source.filter(p => {
      if (!searchQuery) return true
      const q = searchQuery.toLowerCase()
      if (searchType === 'title')   return p.title.toLowerCase().includes(q)
      if (searchType === 'content') return false
      return p.title.toLowerCase().includes(q)
    })
    setNotices(MOCK_NOTICES)
    setPosts(filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE))
    setTotalPages(Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)))
    setLoading(false)
  }, [tab, page, searchQuery, searchType])

  useEffect(() => { fetchPosts() }, [fetchPosts])

  const handleTabChange = (newTab: 'info' | 'suggest' | 'bug' | 'data') => {
    setTab(newTab)
    setPage(1)
    setSearchInput('')
    setSearchQuery('')
  }

  const handleSearch = () => {
    setPage(1)
    setSearchQuery(searchInput)
  }

  const paginationRange = () => {
    const delta = 2
    const range: number[] = []
    for (let i = Math.max(1, page - delta); i <= Math.min(totalPages, page + delta); i++) range.push(i)
    return range
  }

  const getCatClass = (cat: string) => {
    if (cat === '정보') return `${styles.category} ${styles.categoryInfo}`
    if (cat === '건의') return `${styles.category} ${styles.categorySuggest}`

    // CSS에 버그/자료 전용 스타일이 아직 없으면 일단 건의 스타일을 같이 써.
    if (cat === '버그') return `${styles.category} ${styles.categorySuggest}`
    if (cat === '자료') return `${styles.category} ${styles.categoryInfo}`

    return `${styles.category} ${styles.categoryNotice}`
  }

  return (
    <div className={styles.wrapper}>
      <section className={styles.heroWrap}>
        <div className={styles.hero}>
          <p className={styles.eyebrow}>게시판</p>
          <h1 className={styles.title}>정보 공유 & 건의사항</h1>
          <p className={styles.desc}>공유된 정보와 공지 사항, 건의 사항을 확인하세요.</p>
        </div>
      </section>

      <section>
        <div className={styles.main}>
          <div className={styles.tabs}>
            <button
              className={tab === 'info' ? `${styles.tab} ${styles.tabActive}` : styles.tab}
              onClick={() => handleTabChange('info')}
            >정보게시판</button>
            <button
              className={tab === 'suggest' ? `${styles.tab} ${styles.tabActive}` : styles.tab}
              onClick={() => handleTabChange('suggest')}
            >건의게시판</button>
            <button
              className={tab === 'bug' ? `${styles.tab} ${styles.tabActive}` : styles.tab}
              onClick={() => handleTabChange('bug')}
            >버그게시판</button>
            <button
              className={tab === 'data' ? `${styles.tab} ${styles.tabActive}` : styles.tab}
              onClick={() => handleTabChange('data')}
            >자료게시판</button>
          </div>

          <div className={styles.toolbar}>
            <div className={styles.searchBox}>
              <select value={searchType} onChange={e => setSearchType(e.target.value)} className={styles.searchSelect}>
                {SEARCH_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
              <input
                type="text"
                placeholder="검색어를 입력하세요"
                value={searchInput}
                onChange={e => setSearchInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()}
                className={styles.search}
              />
              <button onClick={handleSearch} className={styles.searchBtn}>검색</button>
            </div>
            {(tab === 'suggest' || userRole === 'admin' || userRole === 'manager') && (
              <button
                className={styles.writeBtn}
                onClick={() => {
                  if (!userRole) { setLoginAlert(true); return }
                  router.push(`/board/write?tab=${tab}`)
                }}
              >
                ✏️ 글쓰기
              </button>
            )}
          </div>

          <div className={styles.postList}>
            <div className={styles.listHeader}>
              <span>번호</span>
              <span>카테고리</span>
              <span>제목</span>
              <span>작성자</span>
              <span>날짜</span>
              <span>댓글</span>
              <span>조회</span>
            </div>

            {/* 공지 고정 행 */}
            {notices.map(post => (
              <Link key={`n-${post.id}`} href={`/board/${post.id}`} className={`${styles.postRow} ${styles.pinned}`}>
                <span className={styles.postNum}>{post.id}</span>
                <span className={getCatClass('공지')}>공지</span>
                <span className={styles.postTitle}>
                  <span className={styles.pin}>📌</span>
                  {post.title}
                  {!!post.attachment_count && <span className={styles.clip}>[{post.attachment_count}]</span>}
                </span>
                <span className={styles.author}>{post.author_nickname}</span>
                <span className={styles.date}>{post.created_at}</span>
                <span className={styles.commentCol}>{post.comment_count ?? 0}</span>
                <span className={styles.views}>👁 {post.views}</span>
              </Link>
            ))}

            {/* 일반 게시글 */}
            {loading ? (
              <div className={styles.empty}>불러오는 중...</div>
            ) : posts.length === 0 ? (
              <div className={styles.empty}>게시글이 없습니다.</div>
            ) : posts.map(post => (
              <Link key={post.id} href={`/board/${post.id}`} className={styles.postRow}>
                <span className={styles.postNum}>{post.id}</span>
                <span className={getCatClass(post.category)}>{post.category}</span>
                <span className={styles.postTitle}>
                  {post.title}
                  {!!post.attachment_count && <span className={styles.clip}>[{post.attachment_count}]</span>}
                </span>
                <span className={styles.author}>{post.author_nickname}</span>
                <span className={styles.date}>{post.created_at}</span>
                <span className={styles.commentCol}>{post.comment_count ?? 0}</span>
                <span className={styles.views}>👁 {post.views}</span>
              </Link>
            ))}
          </div>

          <div className={styles.pagination}>
            <button className={styles.pageNav} onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>&lt;</button>
            {paginationRange().map(n => (
              <button
                key={n}
                onClick={() => setPage(n)}
                className={n === page ? `${styles.pageBtn} ${styles.pageActive}` : styles.pageBtn}
              >{n}</button>
            ))}
            <button className={styles.pageNav} onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}>&gt;</button>
          </div>
        </div>
      </section>

      {loginAlert && (
        <div className={styles.modalOverlay} onClick={() => setLoginAlert(false)}>
          <div className={styles.modalBox} onClick={e => e.stopPropagation()}>
            <p className={styles.modalMsg}>로그인 후 이용해주세요.</p>
            <div className={styles.modalBtns}>
              <button className={styles.modalLogin} onClick={() => router.push('/login')}>로그인하기</button>
              <button className={styles.modalCancel} onClick={() => setLoginAlert(false)}>취소</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}