'use client'
import { useState } from 'react'
import Link from 'next/link'
import styles from './page.module.css'

type Comment = {
  id: number
  board: '건의게시판' | '정보게시판'
  postTitle: string
  content: string
  createdAt: string
}

const dummyComments: Comment[] = [
  { id: 21, board: '정보게시판', postTitle: '폭우 시 고속도로 대피 요령 정리',     content: '정말 유용한 정보네요. 저도 비슷한 상황을 겪었는데 도움이 됐습니다.',           createdAt: '2026-05-12' },
  { id: 20, board: '건의게시판', postTitle: 'AI 탐지 정확도 개선 건의',           content: '안개 외에도 역광 상황에서 탐지율이 낮은 것 같습니다. 같이 개선됐으면 합니다.',   createdAt: '2026-05-08' },
  { id: 19, board: '정보게시판', postTitle: '겨울철 도로 결빙 위험 구간 안내',     content: '제가 아는 구간도 추가할게요. 영동고속도로 대관령 부근도 위험합니다.',            createdAt: '2026-04-30' },
  { id: 18, board: '건의게시판', postTitle: '지도 UI 개선 요청',                  content: '동의합니다. 모바일에서도 클릭이 잘 안 됩니다.',                                 createdAt: '2026-04-18' },
  { id: 17, board: '정보게시판', postTitle: '안개 구간 위험 차량 목격 제보',       content: '저도 같은 구간에서 비슷한 상황 목격했습니다. 관계 기관에 신고해야 할 것 같아요.', createdAt: '2026-04-10' },
  { id: 16, board: '건의게시판', postTitle: '날씨 알림 기능 추가 건의',            content: '앱 푸시 알림도 함께 추가해주시면 더 좋을 것 같습니다.',                          createdAt: '2026-03-28' },
  { id: 15, board: '정보게시판', postTitle: '[공지] 서비스 이용 안내',             content: '확인했습니다. 감사합니다.',                                                     createdAt: '2026-03-15' },
]

const BOARD_COLOR: Record<string, string> = {
  건의게시판: 'suggest',
  정보게시판: 'info',
}

export default function MyCommentsPage() {
  const [search, setSearch] = useState('')
  const [boardFilter, setBoardFilter] = useState('전체')
  const [detailComment, setDetailComment] = useState<Comment | null>(null)

  const filtered = dummyComments.filter(c => {
    const matchSearch = c.content.includes(search) || c.postTitle.includes(search)
    const matchBoard = boardFilter === '전체' || c.board === boardFilter
    return matchSearch && matchBoard
  })

  const counts = {
    total: dummyComments.length,
    suggest: dummyComments.filter(c => c.board === '건의게시판').length,
    info: dummyComments.filter(c => c.board === '정보게시판').length,
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
                  {['번호', '게시판', '원본 게시글', '댓글 내용', '작성일'].map(h => (
                    <th key={h} className={styles.th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.length > 0 ? filtered.map(c => (
                  <tr key={c.id} className={styles.tr} onClick={() => setDetailComment(c)}>
                    <td className={styles.td}><span className={styles.idChip}>{c.id}</span></td>
                    <td className={styles.td}>
                      <span className={`${styles.boardBadge} ${styles[BOARD_COLOR[c.board]]}`}>{c.board}</span>
                    </td>
                    <td className={styles.td}><span className={styles.postRef}>{c.postTitle}</span></td>
                    <td className={styles.td}><span className={styles.commentPreview}>{c.content}</span></td>
                    <td className={styles.td}>{c.createdAt}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={5} className={styles.noData}>작성한 댓글이 없습니다</td></tr>
                )}
              </tbody>
            </table>
          </div>

        </div>
      </section>

      {detailComment && (
        <div className={styles.overlay} onClick={() => setDetailComment(null)}>
          <div className={styles.modal} onClick={e => e.stopPropagation()}>
            <div className={styles.modalHeader}>
              <div className={styles.modalMeta}>
                <span className={`${styles.boardBadge} ${styles[BOARD_COLOR[detailComment.board]]}`}>{detailComment.board}</span>
                <span className={styles.modalDate}>{detailComment.createdAt}</span>
              </div>
              <button className={styles.modalClose} onClick={() => setDetailComment(null)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.modalPostRef}>
                <span className={styles.modalPostLabel}>원본 게시글</span>
                <span className={styles.modalPostTitle}>{detailComment.postTitle}</span>
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