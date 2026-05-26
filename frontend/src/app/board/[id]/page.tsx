'use client'
import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useParams } from 'next/navigation'
import styles from './page.module.css'

// ─────────────────────────────────────────
// 타입 정의 (DB 컬럼 매핑)
// ─────────────────────────────────────────
type Reply = {
  id: number
  parent_id: number
  member_id: number
  author_nickname: string
  content: string
  created_at: string
}

type Comment = {
  id: number
  board_id: number
  member_id: number
  author_nickname: string
  content: string
  created_at: string
  replies: Reply[]
}

type Post = {
  id: number
  member_id: number
  board_type: string   // FREE | INFO | NOTICE
  title: string
  content: string
  author_nickname: string
  created_at: string
  view_count: number
  pinned: boolean
}

// ─────────────────────────────────────────
// 로컬 user 정보
// ─────────────────────────────────────────
type LocalUser = { id: number; nickname: string; role: string; access_token: string }
const getLocalUser = (): LocalUser | null => {
  if (typeof window === 'undefined') return null
  try { return JSON.parse(localStorage.getItem('user') ?? 'null') } catch { return null }
}

const getCategoryLabel = (board_type: string) => {
  if (board_type === 'FREE')   return '건의'
  if (board_type === 'INFO')   return '정보'
  if (board_type === 'NOTICE') return '공지'
  return board_type
}

const getCatClass = (board_type: string) => {
  const base = styles.catBadge
  if (board_type === 'INFO')   return `${base} ${styles.catInfo}`
  if (board_type === 'FREE')   return `${base} ${styles.catSuggest}`
  return `${base} ${styles.catNotice}`
}

// ─────────────────────────────────────────
// 컴포넌트
// ─────────────────────────────────────────
function PostDetail() {
  const router   = useRouter()
  const params   = useParams()
  const postId   = Number(params.id)

  const [post, setPost]         = useState<Post | null>(null)
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')

  const [deleteConfirm, setDeleteConfirm] = useState(false)

  const [commentInput, setCommentInput]     = useState('')
  const [replyTargetId, setReplyTargetId]   = useState<number | null>(null)
  const [replyInput, setReplyInput]         = useState('')
  const [deleteCommentId, setDeleteCommentId] = useState<number | null>(null)
  const [deleteReplyKey, setDeleteReplyKey]   = useState<{ commentId: number; replyId: number } | null>(null)
  const [expandedReplies, setExpandedReplies] = useState<Set<number>>(new Set())

  const replyRef = useRef<HTMLTextAreaElement>(null)
  const localUser = getLocalUser()

  // 게시글 + 댓글 fetch
  useEffect(() => {
    const load = async () => {
      try {
        const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}`)
        const data = await res.json()
        if (!data.success) throw new Error(data.message)
        setPost(data.post)
        setComments(data.post.comments ?? [])
      } catch (e: any) {
        setError(e.message ?? '불러오기 실패')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [postId])

  useEffect(() => {
    if (replyTargetId !== null) replyRef.current?.focus()
  }, [replyTargetId])

  const isPrivileged = localUser?.role === 'admin' || localUser?.role === 'manager'
  const isAuthor     = post?.member_id === localUser?.id
  const canEdit      = isAuthor
  const canDelete    = isAuthor || isPrivileged

  // ── 게시글 삭제
  const handleDeletePost = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localUser?.access_token}` },
      })
    } catch { /* soft delete 처리 */ }
    router.push('/board')
  }

  // ── 댓글 작성
  const handleAddComment = async () => {
    if (!commentInput.trim() || !localUser) return
    try {
      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localUser.access_token}`,
        },
        body: JSON.stringify({ content: commentInput.trim() }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.message)
      setComments(prev => [...prev, { ...data.comment, replies: [] }])
      setCommentInput('')
    } catch (e: any) { alert(e.message) }
  }

  // ── 대댓글 작성
  const handleAddReply = async (commentId: number) => {
    if (!replyInput.trim() || !localUser) return
    try {
      const res  = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}/comments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localUser.access_token}`,
        },
        body: JSON.stringify({ content: replyInput.trim(), parent_id: commentId }),
      })
      const data = await res.json()
      if (!data.success) throw new Error(data.message)
      setComments(prev => prev.map(c =>
        c.id === commentId ? { ...c, replies: [...c.replies, data.comment] } : c
      ))
      setReplyInput('')
      setReplyTargetId(null)
    } catch (e: any) { alert(e.message) }
  }

  // ── 댓글 삭제
  const handleDeleteComment = async (commentId: number) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/comments/${commentId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localUser?.access_token}` },
      })
      setComments(prev => prev.filter(c => c.id !== commentId))
    } catch (e: any) { alert(e.message) }
    setDeleteCommentId(null)
  }

  // ── 대댓글 삭제
  const handleDeleteReply = async (commentId: number, replyId: number) => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/comments/${replyId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${localUser?.access_token}` },
      })
      setComments(prev => prev.map(c =>
        c.id === commentId ? { ...c, replies: c.replies.filter(r => r.id !== replyId) } : c
      ))
    } catch (e: any) { alert(e.message) }
    setDeleteReplyKey(null)
  }

  const toggleReplies = (commentId: number) =>
    setExpandedReplies(prev => {
      const next = new Set(prev)
      next.has(commentId) ? next.delete(commentId) : next.add(commentId)
      return next
    })

  // ── 렌더링
  if (loading) return <div className={styles.empty}>불러오는 중...</div>
  if (error)   return <div className={styles.empty}>{error}</div>
  if (!post)   return <div className={styles.empty}>게시글을 찾을 수 없습니다.</div>

  const tabParam  = post.board_type === 'FREE' ? 'suggest' : 'info'
  const tabLabel  = post.board_type === 'FREE' ? '건의게시판' : '정보게시판'
  const REPLY_LIMIT = 2

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>

        {/* 브레드크럼 */}
        <p className={styles.breadcrumb}>
          <span className={styles.breadLink} onClick={() => router.push('/board')}>게시판</span>
          <span> › </span>
          <span className={styles.breadLink} onClick={() => router.push(`/board?tab=${tabParam}`)}>{tabLabel}</span>
        </p>

        {/* 제목 영역 */}
        <div className={styles.titleArea}>
          <div className={styles.titleRow}>
            {post.pinned && <span className={styles.pin}>📌</span>}
            <span className={getCatClass(post.board_type)}>{getCategoryLabel(post.board_type)}</span>
            <h1 className={styles.title}>{post.title}</h1>
          </div>
          <div className={styles.meta}>
            <span>{post.author_nickname}</span>
            <span className={styles.dot}>·</span>
            <span>{post.created_at}</span>
            <span className={styles.dot}>·</span>
            <span>조회 {post.view_count}</span>
            <span className={styles.dot}>·</span>
            <span>댓글 {comments.length}</span>
          </div>
        </div>

        {/* 본문 */}
        <div className={styles.content} dangerouslySetInnerHTML={{ __html: post.content }} />

        {/* 수정/삭제 */}
        <div className={styles.actions}>
          <button onClick={() => router.push('/board')} className={styles.backBtn}>← 목록으로</button>
          <div className={styles.rightBtns}>
            {canEdit && (
              <button
                onClick={() => router.push(`/board/write?tab=${tabParam}&edit=${post.id}`)}
                className={styles.editBtn}
              >수정</button>
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

        {/* ── 댓글 섹션 ── */}
        <div className={styles.commentSection}>
          <h3 className={styles.commentHeading}>
            댓글 <span className={styles.commentCount}>{comments.length}</span>
          </h3>

          {comments.length === 0 ? (
            <p className={styles.noComment}>첫 번째 댓글을 남겨보세요.</p>
          ) : (
            <ul className={styles.commentList}>
              {comments.map(comment => {
                const isExpanded = expandedReplies.has(comment.id)
                const visible    = isExpanded ? comment.replies : comment.replies.slice(0, REPLY_LIMIT)
                const hiddenCnt  = comment.replies.length - REPLY_LIMIT

                return (
                  <li key={comment.id} className={styles.commentItem}>
                    {/* 댓글 본문 */}
                    <div className={styles.commentHeader}>
                      <span className={styles.commentAuthor}>{comment.author_nickname}</span>
                      <span className={styles.commentDate}>{comment.created_at}</span>
                    </div>
                    <p className={styles.commentContent}>{comment.content}</p>

                    {/* 댓글 액션 */}
                    <div className={styles.commentActions}>
                      {localUser && (
                        <button
                          className={styles.replyToggleBtn}
                          onClick={() => setReplyTargetId(replyTargetId === comment.id ? null : comment.id)}
                        >
                          {replyTargetId === comment.id ? '취소' : '↳ 대댓글'}
                        </button>
                      )}
                      {(comment.member_id === localUser?.id || isPrivileged) && (
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
                    {comment.replies.length > 0 && (
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
                              {(reply.member_id === localUser?.id || isPrivileged) && (
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
                        {!isExpanded && hiddenCnt > 0 && (
                          <li>
                            <button className={styles.moreRepliesBtn} onClick={() => toggleReplies(comment.id)}>
                              대댓글 {hiddenCnt}개 더보기 ▾
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
                    )}

                    {/* 대댓글 입력 */}
                    {replyTargetId === comment.id && (
                      <div className={styles.replyInputWrap}>
                        <div className={styles.replyArrow}>↳</div>
                        <div className={styles.replyInputBox}>
                          <textarea
                            ref={replyRef}
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
                )
              })}
            </ul>
          )}

          {/* 댓글 입력 */}
          <div className={styles.commentInputWrap}>
            <span className={styles.commentInputAuthor}>
              {localUser?.nickname ?? '로그인 후 댓글을 작성할 수 있습니다'}
            </span>
            <div className={styles.commentInputRow}>
              <textarea
                value={commentInput}
                onChange={e => setCommentInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleAddComment() } }}
                placeholder="댓글을 입력하세요 (Enter로 등록, Shift+Enter 줄바꿈)"
                className={styles.commentTextarea}
                rows={3}
                disabled={!localUser}
              />
              <button onClick={handleAddComment} className={styles.commentSubmitBtn} disabled={!localUser}>
                등록
              </button>
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