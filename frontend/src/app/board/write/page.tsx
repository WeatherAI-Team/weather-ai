"use client";
import { useState, useEffect, useRef, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "./page.module.css";

type Role = "admin" | "manager" | "user" | "";
type LocalUser = { id: number; nickname: string; role: Role };

const getLocalUser = (): LocalUser | null => {
  if (typeof window === "undefined") return null;
  try {
    return JSON.parse(localStorage.getItem("user") ?? "null");
  } catch {
    return null;
  }
};

const TAB_TO_TYPE: Record<string, string> = {
  suggest: "FREE",
  info: "INFO",
  bug: "BUG",
  data: "DATA",
};

const TAB_LABEL: Record<string, string> = {
  suggest: "건의게시판",
  info: "정보게시판",
  bug: "버그게시판",
  data: "자료게시판",
};

function WriteForm() {
  useEffect(() => {
    document.title = "Weather AI - 글쓰기";
  }, []);
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab = (searchParams.get("tab") || "suggest") as
    | "info"
    | "suggest"
    | "bug"
    | "data";
  const editId = searchParams.get("edit");
  const [localUser, setLocalUser] = useState<LocalUser | null>(null);
  const [isPrivileged, setIsPrivileged] = useState(false);
  const [ready, setReady] = useState(false); // 권한 확인 완료 여부
  const [boardType, setBoardType] = useState(TAB_TO_TYPE[tab] ?? "FREE");
  const [isPinned, setIsPinned] = useState(false);
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const editorRef = useRef<HTMLDivElement>(null);
  const [file, setFile] = useState<File | null>(null);

  // 로컬 유저 로드 + 권한 확인
  useEffect(() => {
    const user = getLocalUser();
    setLocalUser(user);
    const privileged = user?.role === "admin" || user?.role === "manager";
    setIsPrivileged(privileged);
    setReady(true);
  }, []);

  // 권한 확인 완료 후 리다이렉트 판단
  useEffect(() => {
    if (!ready) return;
    if (!localUser) {
      router.replace("/login");
      return;
    }
    if ((tab === "info" || tab === "bug" || tab === "data") && !isPrivileged) {
      router.replace("/board");
      return;
    }
  }, [ready, localUser, tab, isPrivileged, router]);

  // 수정 모드: 기존 게시글 불러오기
  useEffect(() => {
    if (!editId) return;
    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${editId}`)
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) return;
        const p = data.post;
        setTitle(p.title);
        setBoardType(p.board_type);
        setIsPinned(p.pinned);
        if (editorRef.current) editorRef.current.innerHTML = p.content;
      });
  }, [editId]);

  const exec = (cmd: string, value?: string) => {
    document.execCommand(cmd, false, value);
    editorRef.current?.focus();
  };

  const handleSubmit = async () => {
    const content = editorRef.current?.innerHTML ?? "";

    if (!title.trim()) {
      alert("제목을 입력해주세요.");
      return;
    }

    if (!content.trim() || content === "<br>") {
      alert("내용을 입력해주세요.");
      return;
    }

    if (!localUser) {
      alert("로그인이 필요합니다.");
      return;
    }

    if (boardType === "DATA" && !file && !editId) {
      alert("자료게시판은 첨부파일을 등록해주세요.");
      return;
    }

    setSubmitting(true);

    try {
      // ✅ 여기서 토큰 꺼냄
      const token = localStorage.getItem("access_token");

      if (!token) {
        alert("로그인 토큰이 없습니다. 다시 로그인해주세요.");
        router.replace("/login");
        return;
      }

      const url = editId
        ? `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${editId}`
        : `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts`;

      const method = editId ? "PUT" : "POST";

      // ✅ 게시글 생성/수정 요청에 Authorization 추가
      const res = await fetch(url, {
        method,
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        credentials: "include",
        body: JSON.stringify({
          title,
          content,
          board_type: boardType,
          pinned: isPinned,
        }),
      });

      const data = await res.json();

      if (!data.success) {
        throw new Error(data.message);
      }

      const postId = editId ?? data.post?.id;

      if (file && postId) {
        const formData = new FormData();
        formData.append("file", file);

        // ✅ 첨부파일 업로드 요청에도 Authorization 추가
        // 주의: FormData라서 Content-Type은 넣지 않음
        const uploadRes = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${postId}/attachments`,
          {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            credentials: "include",
            body: formData,
          },
        );

        const uploadData = await uploadRes.json();

        if (!uploadData.success) {
          throw new Error(
            uploadData.message ?? "첨부파일 업로드에 실패했습니다.",
          );
        }
      }

      alert(editId ? "수정되었습니다." : "게시글이 등록되었습니다.");

      // ✅ 자료게시판에서 작성하면 다시 자료게시판으로 이동
      router.push(editId ? `/board/${editId}` : `/board?tab=${tab}`);
    } catch (e: any) {
      alert(e.message ?? "오류가 발생했습니다.");
    } finally {
      setSubmitting(false);
    }
  };

  const boardLabel = TAB_LABEL[tab] ?? "게시판";

  // 권한 확인 전에는 아무것도 렌더링하지 않음 (깜빡임 방지)
  if (!ready) return null;

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        {/* 헤더 */}
        <div className={styles.header}>
          <p className={styles.breadcrumb}>게시판 › {boardLabel}</p>
          <h2 className={styles.heading}>
            {editId ? "게시글 수정" : "글쓰기"}
          </h2>
        </div>

        {/* 카테고리 + 고정 체크박스 */}
        {isPrivileged && (
          <div className={styles.categoryRow}>
            <div className={styles.field}>
              <label className={styles.label}>카테고리</label>
              <select
                value={boardType}
                onChange={(e) => setBoardType(e.target.value)}
                className={styles.select}
              >
                <option value="FREE">건의</option>
                <option value="INFO">정보</option>
                <option value="BUG">버그</option>
                <option value="DATA">자료</option>
              </select>
            </div>
            <label className={styles.pinnedLabel}>
              <input
                type="checkbox"
                checked={isPinned}
                onChange={(e) => setIsPinned(e.target.checked)}
                className={styles.pinnedCheck}
              />
              <span>📌 고정게시글로 등록</span>
              {isPinned && (
                <span className={styles.pinnedHint}>
                  공지는 최대 5개까지 등록할 수 있습니다.
                </span>
              )}
            </label>
          </div>
        )}

        {/* 제목 */}
        <div className={styles.field}>
          <label className={styles.label}>제목</label>
          <input
            type="text"
            placeholder="제목을 입력하세요"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={200}
            className={styles.titleInput}
          />
          <span className={styles.charCount}>{title.length} / 200</span>
        </div>

        {/* 리치 텍스트 에디터 */}
        <div className={styles.field}>
          <label className={styles.label}>내용</label>
          <div className={styles.editorWrap}>
            {/* 툴바 */}
            <div className={styles.toolbar}>
              <select
                defaultValue=""
                onChange={(e) => {
                  exec("fontSize", e.target.value);
                  (e.target as HTMLSelectElement).value = "";
                }}
                className={styles.toolSelect}
              >
                <option value="" disabled>
                  크기
                </option>
                <option value="1">아주 작게</option>
                <option value="2">작게</option>
                <option value="3">보통</option>
                <option value="4">크게</option>
                <option value="5">아주 크게</option>
              </select>
              <div className={styles.divider} />
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("bold");
                }}
                className={styles.toolBtn}
                title="굵게"
              >
                <b>B</b>
              </button>
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("italic");
                }}
                className={styles.toolBtn}
                title="기울임"
              >
                <i>I</i>
              </button>
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("underline");
                }}
                className={styles.toolBtn}
                title="밑줄"
              >
                <u>U</u>
              </button>
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("strikeThrough");
                }}
                className={styles.toolBtn}
                title="취소선"
              >
                <s>S</s>
              </button>
              <div className={styles.divider} />
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("justifyLeft");
                }}
                className={styles.toolBtn}
                title="왼쪽"
              >
                ≡좌
              </button>
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("justifyCenter");
                }}
                className={styles.toolBtn}
                title="가운데"
              >
                ≡중
              </button>
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("justifyRight");
                }}
                className={styles.toolBtn}
                title="오른쪽"
              >
                ≡우
              </button>
              <div className={styles.divider} />
              <label className={styles.colorLabel} title="글자 색상">
                <span>A</span>
                <input
                  type="color"
                  onInput={(e) =>
                    exec("foreColor", (e.target as HTMLInputElement).value)
                  }
                  className={styles.colorInput}
                />
              </label>
              <label className={styles.colorLabel} title="배경 색상">
                <span style={{ background: "#ffe066", padding: "0 3px" }}>
                  A
                </span>
                <input
                  type="color"
                  onInput={(e) =>
                    exec("hiliteColor", (e.target as HTMLInputElement).value)
                  }
                  className={styles.colorInput}
                />
              </label>
              <div className={styles.divider} />
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("insertUnorderedList");
                }}
                className={styles.toolBtn}
                title="목록"
              >
                • 목록
              </button>
              <button
                onMouseDown={(e) => {
                  e.preventDefault();
                  exec("insertOrderedList");
                }}
                className={styles.toolBtn}
                title="번호 목록"
              >
                1. 목록
              </button>
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

        {boardType === "DATA" && (
          <div className={styles.field}>
            <label className={styles.label}>첨부파일</label>

            <label className={styles.fileLabel}>
              <span className={styles.fileLabelText}>📎 파일 선택</span>
              <input
                type="file"
                className={styles.fileInput}
                accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.csv,.xlsx,.docx,.pptx,.zip"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>

            {file ? (
              <p className={styles.selectedFileName}>
                선택된 파일: {file.name}
              </p>
            ) : (
              <p className={styles.fileHint}>
                자료게시판은 첨부파일 등록이 필요합니다.
              </p>
            )}
          </div>
        )}

        {/* 하단 버튼 */}
        <div className={styles.actions}>
          <button
            onClick={() => router.back()}
            className={styles.cancelBtn}
            disabled={submitting}
          >
            취소
          </button>
          <button
            onClick={handleSubmit}
            className={styles.submitBtn}
            disabled={submitting}
          >
            {submitting ? "처리 중..." : editId ? "수정하기" : "등록하기"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function BoardWritePage() {
  return (
    <Suspense
      fallback={
        <div style={{ padding: "40px", textAlign: "center", color: "#5a85a8" }}>
          불러오는 중...
        </div>
      }
    >
      <WriteForm />
    </Suspense>
  );
}
