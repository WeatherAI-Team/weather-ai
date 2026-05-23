'use client'
import { useState, useEffect, useRef, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import styles from './page.module.css'

type Role = 'admin' | 'manager' | 'user' | ''

function WriteForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const tab = (searchParams.get('tab') || 'suggest') as 'info' | 'suggest'

  const [userRole, setUserRole] = useState<Role>('')
  const [category, setCategory] = useState('')
  const [isPinned, setIsPinned] = useState(false)
  const [title, setTitle] = useState('')
  const [images, setImages] = useState<File[]>([])
  const [imagePreviews, setImagePreviews] = useState<string[]>([])
  const editorRef = useRef<HTMLDivElement>(null)

  const isPrivileged = userRole === 'admin' || userRole === 'manager'

  useEffect(() => {
    const saved = localStorage.getItem('user')
    if (saved) {
      try { setUserRole(JSON.parse(saved).role ?? '') } catch { /* ignore */ }
    }
  }, [])

  useEffect(() => {
    setCategory(tab === 'suggest' ? '건의' : isPrivileged ? '정보' : '')
  }, [tab, isPrivileged])

  // 권한 없는 경우 리다이렉트
  useEffect(() => {
    if (userRole === '') return
    if (tab === 'info' && !isPrivileged) router.replace('/board')
  }, [userRole, tab, isPrivileged, router])

  const exec = (cmd: string, value?: string) => {
    document.execCommand(cmd, false, value)
    editorRef.current?.focus()
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (!files.length) return
    setImages(prev => [...prev, ...files])
    setImagePreviews(prev => [...prev, ...files.map(f => URL.createObjectURL(f))])
    e.target.value = ''
  }

  const removeImage = (idx: number) => {
    URL.revokeObjectURL(imagePreviews[idx])
    setImages(prev => prev.filter((_, i) => i !== idx))
    setImagePreviews(prev => prev.filter((_, i) => i !== idx))
  }

  const handleSubmit = () => {
    const content = editorRef.current?.innerHTML || ''
    if (!title.trim()) { alert('제목을 입력해주세요.'); return }
    if (!content.trim() || content === '<br>') { alert('내용을 입력해주세요.'); return }

    const formData = new FormData()
    formData.append('category', category)
    formData.append('title', title)
    formData.append('content', content)
    formData.append('is_pinned', String(isPinned))
    images.forEach(img => formData.append('images', img))

    // TODO: API 연결 시 아래 fetch 활성화
    // await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts`, {
    //   method: 'POST',
    //   headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
    //   body: formData,
    // })

    alert('게시글이 등록되었습니다.')
    router.push('/board')
  }

  const categoryOptions =
    isPrivileged ? ['정보', '건의'] : ['건의']

  const boardLabel = tab === 'info' ? '정보게시판' : '건의게시판'

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>

        {/* 헤더 */}
        <div className={styles.header}>
          <p className={styles.breadcrumb}>게시판 &gt; {boardLabel}</p>
          <h2 className={styles.heading}>글쓰기</h2>
        </div>

        {/* 카테고리 + 고정게시글 체크박스 */}
        {(categoryOptions.length > 1 || isPrivileged) && (
          <div className={styles.categoryRow}>
            {categoryOptions.length > 1 && (
              <div className={styles.field}>
                <label className={styles.label}>카테고리</label>
                <select value={category} onChange={e => setCategory(e.target.value)} className={styles.select}>
                  {categoryOptions.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            )}
            {isPrivileged && (
              <label className={styles.pinnedLabel}>
                <input
                  type="checkbox"
                  checked={isPinned}
                  onChange={e => setIsPinned(e.target.checked)}
                  className={styles.pinnedCheck}
                />
                <span>📌 고정게시글로 등록</span>
                {isPinned && <span className={styles.pinnedHint}>공지는 최대 5개까지 등록할 수 있습니다.</span>}
              </label>
            )}
          </div>
        )}

        {/* 제목 */}
        <div className={styles.field}>
          <label className={styles.label}>제목</label>
          <input
            type="text"
            placeholder="제목을 입력하세요"
            value={title}
            onChange={e => setTitle(e.target.value)}
            maxLength={200}
            className={styles.titleInput}
          />
          <span className={styles.charCount}>{title.length} / 200</span>
        </div>

        {/* 내용 – 리치 텍스트 에디터 */}
        <div className={styles.field}>
          <label className={styles.label}>내용</label>
          <div className={styles.editorWrap}>

            {/* 툴바 */}
            <div className={styles.toolbar}>
              {/* 글자 크기 */}
              <select
                defaultValue=""
                onChange={e => { exec('fontSize', e.target.value); (e.target as HTMLSelectElement).value = '' }}
                className={styles.toolSelect}
              >
                <option value="" disabled>크기</option>
                <option value="1">아주 작게</option>
                <option value="2">작게</option>
                <option value="3">보통</option>
                <option value="4">크게</option>
                <option value="5">아주 크게</option>
              </select>

              <div className={styles.divider} />

              <button onMouseDown={e => { e.preventDefault(); exec('bold') }} className={styles.toolBtn} title="굵게"><b>B</b></button>
              <button onMouseDown={e => { e.preventDefault(); exec('italic') }} className={styles.toolBtn} title="기울임"><i>I</i></button>
              <button onMouseDown={e => { e.preventDefault(); exec('underline') }} className={styles.toolBtn} title="밑줄"><u>U</u></button>
              <button onMouseDown={e => { e.preventDefault(); exec('strikeThrough') }} className={styles.toolBtn} title="취소선"><s>S</s></button>

              <div className={styles.divider} />

              <button onMouseDown={e => { e.preventDefault(); exec('justifyLeft') }} className={styles.toolBtn} title="왼쪽 정렬">≡좌</button>
              <button onMouseDown={e => { e.preventDefault(); exec('justifyCenter') }} className={styles.toolBtn} title="가운데 정렬">≡중</button>
              <button onMouseDown={e => { e.preventDefault(); exec('justifyRight') }} className={styles.toolBtn} title="오른쪽 정렬">≡우</button>

              <div className={styles.divider} />

              <label className={styles.colorLabel} title="글자 색상">
                <span>A</span>
                <input type="color" onInput={e => exec('foreColor', (e.target as HTMLInputElement).value)} className={styles.colorInput} />
              </label>
              <label className={styles.colorLabel} title="배경 색상">
                <span style={{ background: '#ffe066', padding: '0 3px' }}>A</span>
                <input type="color" onInput={e => exec('hiliteColor', (e.target as HTMLInputElement).value)} className={styles.colorInput} />
              </label>

              <div className={styles.divider} />

              <button onMouseDown={e => { e.preventDefault(); exec('insertUnorderedList') }} className={styles.toolBtn} title="목록">• 목록</button>
              <button onMouseDown={e => { e.preventDefault(); exec('insertOrderedList') }} className={styles.toolBtn} title="번호 목록">1. 목록</button>
            </div>

            {/* 에디터 본문 */}
            <div
              ref={editorRef}
              contentEditable
              suppressContentEditableWarning
              className={styles.editor}
              data-placeholder="내용을 입력하세요"
            />
          </div>
        </div>

        {/* 이미지 첨부 */}
        <div className={styles.field}>
          <label className={styles.label}>이미지 첨부</label>
          <label className={styles.fileLabel}>
            <span className={styles.fileLabelText}>+ 이미지 선택</span>
            <input type="file" accept="image/*" multiple onChange={handleImageUpload} className={styles.fileInput} />
          </label>
          <p className={styles.fileHint}>JPG, PNG, GIF, WEBP 지원 · 여러 장 선택 가능</p>
          {imagePreviews.length > 0 && (
            <div className={styles.previewGrid}>
              {imagePreviews.map((src, i) => (
                <div key={i} className={styles.previewItem}>
                  <img src={src} alt={`첨부 이미지 ${i + 1}`} className={styles.previewImg} />
                  <button onClick={() => removeImage(i)} className={styles.removeBtn}>✕</button>
                  <span className={styles.previewName}>{images[i]?.name}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 하단 버튼 */}
        <div className={styles.actions}>
          <button onClick={() => router.back()} className={styles.cancelBtn}>취소</button>
          <button onClick={handleSubmit} className={styles.submitBtn}>등록하기</button>
        </div>

      </div>
    </div>
  )
}

export default function BoardWritePage() {
  return (
    <Suspense fallback={<div style={{ padding: '40px', textAlign: 'center', color: '#5a85a8' }}>불러오는 중...</div>}>
      <WriteForm />
    </Suspense>
  )
}
