'use client'
import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useParams } from 'next/navigation'
import styles from './page.module.css'

type Reply = {
  id: number
  parent_id: number
  author_nickname: string
  content: string
  created_at: string
}

type Comment = {
  id: number
  post_id: number
  author_nickname: string
  content: string
  created_at: string
  replies: Reply[]
}

type Post = {
  id: number
  category: string
  title: string
  content: string
  author_nickname: string
  author_id: number
  created_at: string
  views: number
  is_pinned: boolean
  images?: string[]
}

const MOCK_POSTS: Post[] = [
  {
    id: 1, category: '공지', title: '시스템 정기 점검 안내 (5월 1일)',
    content: '<p>5월 1일 오전 2시~4시 정기 점검이 있습니다.</p><p>점검 중에는 서비스 이용이 불가합니다.</p>',
    author_nickname: '관리자', author_id: 1, created_at: '2026-04-25', views: 312, is_pinned: true,
  },
  {
    id: 2, category: '정보', title: '경부고속도로 폭우 상황 탱크로리 탐지 성공 보고',
    content: '<p>경부고속도로 구간에서 폭우 상황 중 탱크로리 탐지에 성공했습니다.</p>',
    author_nickname: '홍길동', author_id: 2, created_at: '2026-04-24', views: 589, is_pinned: false,
  },
  {
    id: 7, category: '건의', title: '탐지 알림 소리 크기 조절 기능 추가 요청',
    content: '<p>현재 알림 소리가 너무 커서 조절 기능이 있으면 좋겠습니다.</p>',
    author_nickname: '김건의', author_id: 3, created_at: '2026-04-23', views: 87, is_pinned: false,
  },
]

const MOCK_COMMENTS: Comment[] = [
  {
    id: 1, post_id: 2, author_nickname: '이탐지', content: '좋은 정보 감사합니다!',
    created_at: '2026-04-24', replies: [
      { id: 1, parent_id: 1, author_nickname: '홍길동', content: '읽어주셔서 감사해요 :)', created_at: '2026-04-25' },
    ],
  },
  {
    id: 2, post_id: 2, author_nickname: '박개발', content: '탐지 모델 버전이 어떻게 되나요?',
    created_at: '2026-04-25', replies: [],
  },
]

const getCatClass = (cat: string) => {
  if (cat === '정보') return `${styles.catBadge} ${styles.catInfo}`
  if (cat === '건의') return `${styles.catBadge} ${styles.catSuggest}`
  return `${styles.catBadge} ${styles.catNotice}`
}

let nextCommentId = 100
let nextReplyId = 100

function PostDetail() {
  const router = useRouter()
  const params = useParams()
  const postId = Number(params.id)

  const [post, setPost] = useState<Post | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [currentNickname, setCurrentNickname] = useState('')
  const [currentRole, setCurrentRole] = useState('')
  const [loading, setLoading] = useState(true)
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  // 댓글 입력
  const [commentInput, setCommentInput] = useState('')
  // 대댓글: 어느 댓글에 답글 쓰는지
  const [replyTargetId, setReplyTargetId] = useState<number | null>(null)
  const [replyInput, setReplyInput] = useState('')
  // 댓글/대댓글 삭제 확인
  const [deleteCommentId, setDeleteCommentId] = useState<number | null>(null)
  const [deleteReplyKey, setDeleteReplyKey] = useState<{ commentId: number; replyId: number } | null>(null)
  const [expandedReplies, setExpandedReplies] = useState<Set<number>>(new Set())

  const toggleReplies = (commentId: number) =>
    setExpandedReplies(prev => {
      const next = new Set(prev)
      next.has(commentId) ? next.delete(commentId) : next.add(commentId)
      return next
    })

  const replyInputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const saved = localStorage.getItem('user')
    if (saved) {
      try {
        const u = JSON.parse(saved)
        setCurrentNickname(u.nickname ?? '')
        setCurrentRole(u.role ?? '')
      } catch { /* ignore */ }
    }
  }, [])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}`)
        const data = await res.json()
        if (data.success) { setPost(data.post); setLoading(false) }
      } catch { /* fallback */ }
      setPost(MOCK_POSTS.find(p => p.id === postId) ?? null)
      setComments(MOCK_COMMENTS.filter(c => c.post_id === postId))
      setLoading(false)
    }
    load()
  }, [postId])

  // 대댓글 입력창 열릴 때 포커스
  useEffect(() => {
    if (replyTargetId !== null) replyInputRef.current?.focus()
  }, [replyTargetId])

  const isPrivileged = currentRole === 'admin' || currentRole === 'manager'
  const isAuthor = post?.author_nickname === currentNickname
  const canEdit = isAuthor
  const canDelete = isAuthor || isPrivileged

  const handleDeletePost = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      })
    } catch { /* ignore */ }
    router.push('/board')
  }

  const today = new Date().toISOString().slice(0, 10)

  const handleAddComment = () => {
    if (!commentInput.trim()) return
    const newComment: Comment = {
      id: nextCommentId++,
      post_id: postId,
      author_nickname: currentNickname || '익명',
      content: commentInput.trim(),
      created_at: today,
      replies: [],
    }
    setComments(prev => [...prev, newComment])
    setCommentInput('')
    // TODO: POST /api/board/posts/{postId}/comments
  }

  const handleAddReply = (commentId: number) => {
    if (!replyInput.trim()) return
    const newReply: Reply = {
      id: nextReplyId++,
      parent_id: commentId,
      author_nickname: currentNickname || '익명',
      content: replyInput.trim(),
      created_at: today,
    }
    setComments(prev => prev.map(c =>
      c.id === commentId ? { ...c, replies: [...c.replies, newReply] } : c
    ))
    setReplyInput('')
    setReplyTargetId(null)
    // TODO: POST /api/board/posts/{postId}/comments/{commentId}/replies
  }

  const handleDeleteComment = (commentId: number) => {
    setComments(prev => prev.filter(c => c.id !== commentId))
    setDeleteCommentId(null)
    // TODO: DELETE /api/board/comments/{commentId}
  }

  const handleDeleteReply = (commentId: number, replyId: number) => {
    setComments(prev => prev.map(c =>
      c.id === commentId ? { ...c, replies: c.replies.filter(r => r.id !== replyId) } : c
    ))
    setDeleteReplyKey(null)
    // TODO: DELETE /api/board/replies/{replyId}
  }

  if (loading) return <div className={styles.empty}>불러오는 중...</div>
  if (!post) return <div className={styles.empty}>게시글을 찾을 수 없습니다.</div>

  const tabParam = post.category === '건의' ? 'suggest' : 'info'
  const tabLabel = post.category === '건의' ? '건의게시판' : '정보게시판'

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>

        {/* 브레드크럼 */}
        <p className={styles.breadcrumb}>
          <span className={styles.breadLink} onClick={() => router.push('/board')}>게시판</span>
          <span> &gt; </span>
          <span className={styles.breadLink} onClick={() => router.push(`/board?tab=${tabParam}`)}>{tabLabel}</span>
        </p>

        {/* 제목 */}
        <div className={styles.titleArea}>
          <div className={styles.titleRow}>
            {post.is_pinned && <span className={styles.pin}>📌</span>}
            <span className={getCatClass(post.category)}>{post.category}</span>
            <h1 className={styles.title}>{post.title}</h1>
          </div>
          <div className={styles.meta}>
            <span>{post.author_nickname}</span>
            <span className={styles.dot}>·</span>
            <span>{post.created_at}</span>
            <span className={styles.dot}>·</span>
            <span>조회 {post.views}</span>
            <span className={styles.dot}>·</span>
            <span>댓글 {comments.length}</span>
          </div>
        </div>

        {/* 본문 */}
        <div className={styles.content} dangerouslySetInnerHTML={{ __html: post.content }} />

        {/* 첨부 이미지 */}
        {post.images && post.images.length > 0 && (
          <div className={styles.imageSection}>
            <p className={styles.imageLabel}>첨부 이미지</p>
            <div className={styles.imageGrid}>
              {post.images.map((src, i) => (
                <img key={i} src={src} alt={`첨부 ${i + 1}`} className={styles.image} />
              ))}
            </div>
          </div>
        )}

        {/* 수정/삭제 버튼 */}
        <div className={styles.actions}>
          <button onClick={() => router.push('/board')} className={styles.backBtn}>← 목록으로</button>
          <div className={styles.rightBtns}>
            {canEdit && (
              <button onClick={() => router.push(`/board/write?tab=${tabParam}&edit=${post.id}`)} className={styles.editBtn}>수정</button>
            )}
            {canDelete && !deleteConfirm && (
              <button onClick={() => setDeleteConfirm(true)} className={styles.deleteBtn}>삭제</button>
            )}
            {deleteConfirm && (
              <div className={styles.confirmBox}>
                <span>정말 삭제하시겠습니까?</span>
                <button onClick={handleDeletePost} className={styles.confirmYes}>삭제</button>
                <button onClick={() => setDeleteConfirm(false)} className={styles.confirmNo}>취소</button>
              </div>
            )}
          </div>
        </div>

        {/* ───── 댓글 섹션 ───── */}
        <div className={styles.commentSection}>
          <h3 className={styles.commentHeading}>댓글 <span className={styles.commentCount}>{comments.length}</span></h3>

          {/* 댓글 목록 */}
          {comments.length === 0 ? (
            <p className={styles.noComment}>첫 번째 댓글을 남겨보세요.</p>
          ) : (
            <ul className={styles.commentList}>
              {comments.map(comment => (
                <li key={comment.id} className={styles.commentItem}>

                  {/* 댓글 본문 */}
                  <div className={styles.commentHeader}>
                    <span className={styles.commentAuthor}>{comment.author_nickname}</span>
                    <span className={styles.commentDate}>{comment.created_at}</span>
                  </div>
                  <p className={styles.commentContent}>{comment.content}</p>

                  {/* 댓글 액션 */}
                  <div className={styles.commentActions}>
                    {currentNickname && (
                      <button
                        className={styles.replyToggleBtn}
                        onClick={() => setReplyTargetId(replyTargetId === comment.id ? null : comment.id)}
                      >
                        {replyTargetId === comment.id ? '취소' : '↳ 대댓글'}
                      </button>
                    )}
                    {(comment.author_nickname === currentNickname || isPrivileged) && (
                      deleteCommentId === comment.id ? (
                        <span className={styles.inlineConfirm}>
                          삭제할까요?
                          <button className={styles.confirmYesSmall} onClick={() => handleDeleteComment(comment.id)}>삭제</button>
                          <button className={styles.confirmNoSmall} onClick={() => setDeleteCommentId(null)}>취소</button>
                        </span>
                      ) : (
                        <button className={styles.commentDeleteBtn} onClick={() => setDeleteCommentId(comment.id)}>삭제</button>
                      )
                    )}
                  </div>

                  {/* 대댓글 목록 */}
                  {comment.replies.length > 0 && (() => {
                    const REPLY_LIMIT = 2
                    const isExpanded = expandedReplies.has(comment.id)
                    const visible = isExpanded ? comment.replies : comment.replies.slice(0, REPLY_LIMIT)
                    const hidden = comment.replies.length - REPLY_LIMIT
                    return (
                      <ul className={styles.replyList}>
                        {visible.map(reply => (
                          <li key={reply.id} className={styles.replyItem}>
                            <div className={styles.replyArrow}>↳</div>
                            <div className={styles.replyBody}>
                              <div className={styles.commentHeader}>
                                <span className={styles.commentAuthor}>{reply.author_nickname}</span>
                                <span className={styles.commentDate}>{reply.created_at}</span>
                              </div>
                              <p className={styles.commentContent}>{reply.content}</p>
                              {(reply.author_nickname === currentNickname || isPrivileged) && (
                                <div className={styles.commentActions}>
                                  {deleteReplyKey?.commentId === comment.id && deleteReplyKey.replyId === reply.id ? (
                                    <span className={styles.inlineConfirm}>
                                      삭제할까요?
                                      <button className={styles.confirmYesSmall} onClick={() => handleDeleteReply(comment.id, reply.id)}>삭제</button>
                                      <button className={styles.confirmNoSmall} onClick={() => setDeleteReplyKey(null)}>취소</button>
                                    </span>
                                  ) : (
                                    <button className={styles.commentDeleteBtn} onClick={() => setDeleteReplyKey({ commentId: comment.id, replyId: reply.id })}>삭제</button>
                                  )}
                                </div>
                              )}
                            </div>
                          </li>
                        ))}
                        {!isExpanded && hidden > 0 && (
                          <li>
                            <button className={styles.moreRepliesBtn} onClick={() => toggleReplies(comment.id)}>
                              대댓글 {hidden}개 더보기 ▾
                            </button>
                          </li>
                        )}
                        {isExpanded && comment.replies.length > REPLY_LIMIT && (
                          <li>
                            <button className={styles.moreRepliesBtn} onClick={() => toggleReplies(comment.id)}>
                              접기 ▴
                            </button>
                          </li>
                        )}
                      </ul>
                    )
                  })()}

                  {/* 대댓글 입력 */}
                  {replyTargetId === comment.id && (
                    <div className={styles.replyInputWrap}>
                      <div className={styles.replyArrow}>↳</div>
                      <div className={styles.replyInputBox}>
                        <textarea
                          ref={replyInputRef}
                          value={replyInput}
                          onChange={e => setReplyInput(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAddReply(comment.id) } }}
                          placeholder="대댓글을 입력하세요 (Enter로 등록)"
                          className={styles.replyTextarea}
                          rows={2}
                        />
                        <button onClick={() => handleAddReply(comment.id)} className={styles.replySubmitBtn}>등록</button>
                      </div>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}

          {/* 댓글 입력 */}
          <div className={styles.commentInputWrap}>
            <span className={styles.commentInputAuthor}>{currentNickname || '로그인 후 댓글을 작성할 수 있습니다'}</span>
            <div className={styles.commentInputRow}>
              <textarea
                value={commentInput}
                onChange={e => setCommentInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAddComment() } }}
                placeholder="댓글을 입력하세요 (Enter로 등록, Shift+Enter 줄바꿈)"
                className={styles.commentTextarea}
                rows={3}
                disabled={!currentNickname}
              />
              <button onClick={handleAddComment} className={styles.commentSubmitBtn} disabled={!currentNickname}>등록</button>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

export default function BoardDetailPage() {
  return (
    <Suspense fallback={<div style={{ padding: '60px', textAlign: 'center', color: '#5a85a8' }}>불러오는 중...</div>}>
      <PostDetail />
    </Suspense>
  )
}
