'use client'
import { useState } from 'react'
import Link from 'next/link'
import styles from './page.module.css'

type Post = {
  id: number
  board: '건의게시판' | '정보게시판'
  title: string
  content: string
  views: number
  createdAt: string
}

const dummyPosts: Post[] = [
  { id: 12, board: '건의게시판', title: 'AI 탐지 정확도 개선 건의',          content: '안개 상황에서 탐지율이 낮은 것 같습니다. 개선 부탁드립니다.',    views: 201, createdAt: '2026-05-10' },
  { id: 11, board: '정보게시판', title: '폭우 시 고속도로 대피 요령 정리',     content: '폭우 시 고속도로에서 대피하는 방법을 공유합니다.',              views: 134, createdAt: '2026-05-03' },
  { id: 10, board: '건의게시판', title: '지도 UI 개선 요청',                  content: '지도에서 지역 클릭 시 더 상세한 정보가 보였으면 합니다.',        views: 89,  createdAt: '2026-04-22' },
  { id: 9,  board: '정보게시판', title: '안개 구간 위험 차량 목격 제보',       content: '중부고속도로 안개 구간에서 과속 탱크로리를 목격했습니다.',      views: 315, createdAt: '2026-04-15' },
  { id: 8,  board: '건의게시판', title: '날씨 알림 기능 추가 건의',            content: '폭우 예보 시 미리 알림을 받을 수 있으면 좋겠습니다.',           views: 142, createdAt: '2026-04-01' },
  { id: 7,  board: '정보게시판', title: '겨울철 도로 결빙 위험 구간 안내',     content: '결빙 위험이 높은 구간 정보를 공유합니다.',                     views: 278, createdAt: '2026-03-20' },
  { id: 6,  board: '건의게시판', title: '모바일 화면 최적화 요청',             content: '모바일에서 지도가 잘 안 보입니다. 최적화 부탁드립니다.',         views: 67,  createdAt: '2026-03-10' },
]

const BOARD_COLOR: Record<string, string> = {
  건의게시판: 'suggest',
  정보게시판: 'info',
}

export default function MyPostsPage() {
  const [search, setSearch] = useState('')
  const [boardFilter, setBoardFilter] = useState('전체')
  const [detailPost, setDetailPost] = useState<Post | null>(null)

  const filtered = dummyPosts.filter(p => {
    const matchSearch = p.title.includes(search) || p.content.includes(search)
    const matchBoard = boardFilter === '전체' || p.board === boardFilter
    return matchSearch && matchBoard
  })

  const counts = {
    total: dummyPosts.length,
    suggest: dummyPosts.filter(p => p.board === '건의게시판').length,
    info: dummyPosts.filter(p => p.board === '정보게시판').length,
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
              { label: '전체 게시글', value: counts.total,   key: '전체',    color: '#07559d' },
              { label: '건의게시판',  value: counts.suggest, key: '건의게시판', color: '#1b9bd1' },
              { label: '정보게시판',  value: counts.info,    key: '정보게시판', color: '#2b8a3e' },
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
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
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
                  {['번호', '게시판', '제목', '조회수', '작성일'].map(h => (
                    <th key={h} className={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length > 0 ? filtered.map(p => (
                  <tr key={p.id} className={styles.tr} onClick={() => setDetailPost(p)}>
                    <td className={styles.td}><span className={styles.idChip}>{p.id}</span></td>
                    <td className={styles.td}>
                      <span className={`${styles.boardBadge} ${styles[BOARD_COLOR[p.board]]}`}>{p.board}</span>
                    </td>
                    <td className={styles.td}><span className={styles.postTitle}>{p.title}</span></td>
                    <td className={styles.td}>{p.views.toLocaleString()}</td>
                    <td className={styles.td}>{p.createdAt}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={5} className={styles.noData}>작성한 게시글이 없습니다</td></tr>
                )}
              </tbody>
            </table>
          </div>

        </div>
      </section>

      {detailPost && (
        <div className={styles.overlay} onClick={() => setDetailPost(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div className={styles.modalMeta}>
                <span className={`${styles.boardBadge} ${styles[BOARD_COLOR[detailPost.board]]}`}>{detailPost.board}</span>
                <span className={styles.modalDate}>{detailPost.createdAt}</span>
              </div>
              <button className={styles.modalClose} onClick={() => setDetailPost(null)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <h2 className={styles.modalTitle}>{detailPost.title}</h2>
              <p className={styles.modalContent}>{detailPost.content}</p>
            </div>
            <div className={styles.modalFooter}>
              <span className={styles.modalViews}>조회 {detailPost.views.toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
