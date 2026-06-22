"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import styles from "./page.module.css";
type Tab = "info" | "suggest" | "bug" | "data";
type BugStatus = "pending" | "in_progress" | "done";

type Post = {
  id: number;

  category: string;
  title: string;
  author_nickname: string;
  created_at: string;
  views: number;
  comment_count?: number;
  attachment_count?: number;
};

type BugPost = Post & { status: BugStatus };

const toCategory = (board_type: string): string => {
  if (board_type === "NOTICE") return "공지";
  if (board_type === "INFO") return "정보";
  if (board_type === "BUG") return "버그";
  if (board_type === "DATA") return "자료";
  return "건의";
};

const SEARCH_TYPES = [
  { value: "title", label: "제목" },
  { value: "content", label: "내용" },
  { value: "all", label: "제목+내용" },
];

const BUG_STATUS_LABELS: Record<BugStatus, string> = {
  pending: "미처리",
  in_progress: "진행중",
  done: "처리완료",
};

const DATA_AUTHORS = ["전체", "안건우", "여민엽", "유진설", "김소현", "조정화"];

const PAGE_SIZE = 10;

function BoardPageInner() {
  useEffect(() => {
    document.title = "Weather AI - 게시판";
  }, []);
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") as Tab) ?? "info";
  const [tab, setTab] = useState<Tab>(initialTab);
  const [searchType, setSearchType] = useState("title");
  const [searchInput, setSearchInput] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [notices, setNotices] = useState<Post[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [bugPosts, setBugPosts] = useState<BugPost[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [userRole, setUserRole] = useState<string>("");
  const [loginAlert, setLoginAlert] = useState(false);
  const [bugStatusFilter, setBugStatusFilter] = useState<BugStatus | "all">(
    "all",
  );
  const [dataAuthorFilter, setDataAuthorFilter] = useState("전체");

  useEffect(() => {
    const saved = localStorage.getItem("user");
    if (saved) {
      try {
        setUserRole(JSON.parse(saved).role ?? "");
      } catch {}
    }
  }, []);

  // 헤더 드롭다운에서 tab param 변경 시 반영
  useEffect(() => {
    const t = (searchParams.get("tab") as Tab) ?? "info";
    setTab(t);
    setPage(1);
    setSearchInput("");
    setSearchQuery("");
  }, [searchParams]);

  const fetchPosts = useCallback(async () => {
    if (tab === "bug") {
      setLoading(true);
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts?board_type=bug&per_page=200`,
        );
        const data = await res.json();
        if (data.success) {
          setBugPosts(data.posts);
          setLoading(false);
          return;
        }
      } catch {}
      setBugPosts([]);
      setLoading(false);
      return;
    }
    if (tab === "data") {
      setLoading(true);
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts?board_type=data&per_page=200`,
        );
        const data = await res.json();
        if (data.success) {
          setPosts(data.posts);
          setLoading(false);
          return;
        }
      } catch {}
      setPosts([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const params = new URLSearchParams({
        board_type: tab,
        page: String(page),
        search: searchQuery,
        search_type: searchType,
        per_page: String(PAGE_SIZE),
      });
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts?${params}`,
      );
      const data = await res.json();

      if (data.success) {
        const mapPost = (p: any): Post => ({
          id: p.id,
          category: toCategory(p.board_type),
          title: p.title,
          author_nickname: p.author_nickname,
          created_at: p.created_at,
          views: p.view_count,
          comment_count: p.comment_count ?? 0,
          attachment_count: p.attachment_count ?? 0,
        });
        const allPosts = data.posts.map(mapPost);
        setNotices(
          allPosts.filter((_: Post, i: number) => data.posts[i].pinned),
        );
        setPosts(
          allPosts.filter((_: Post, i: number) => !data.posts[i].pinned),
        );
        setTotalPages(data.total_pages);
        setLoading(false);
        return;
      }
    } catch {}

    setNotices([]);
    setPosts([]);
    setTotalPages(1);
    setLoading(false);
  }, [tab, page, searchQuery, searchType]);

  useEffect(() => {
    fetchPosts();
  }, [fetchPosts]);

  const handleTabChange = (newTab: "info" | "suggest" | "bug" | "data") => {
    // 화면에서 선택된 탭을 바꿔.
    setTab(newTab);

    // 탭을 바꾸면 1페이지부터 다시 보여줘.
    setPage(1);

    // 탭이 바뀌면 검색어도 초기화해.
    setSearchInput("");
    setSearchQuery("");

    // 주소에도 현재 탭을 표시해.
    router.push(`/board?tab=${newTab}`);
  };

  const handleSearch = () => {
    setPage(1);
    setSearchQuery(searchInput);
  };

  const handleBugStatusChange = async (id: number, status: BugStatus) => {
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/board/posts/${id}/status`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ status }),
        },
      );

      const data = await res.json();

      if (!data.success) {
        throw new Error(data.message ?? "상태 변경에 실패했습니다.");
      }

      setBugPosts((prev) =>
        prev.map((p) =>
          p.id === id ? { ...p, status: data.post?.status ?? status } : p,
        ),
      );
    } catch (e: any) {
      alert(e.message ?? "상태 변경에 실패했습니다.");
    }
  };

  const paginationRange = () => {
    const delta = 2;
    const range: number[] = [];
    for (
      let i = Math.max(1, page - delta);
      i <= Math.min(totalPages, page + delta);
      i++
    )
      range.push(i);
    return range;
  };

  const getCatClass = (cat: string) => {
    if (cat === "정보") return `${styles.category} ${styles.categoryInfo}`;
    if (cat === "건의") return `${styles.category} ${styles.categorySuggest}`;
    if (cat === "버그") return `${styles.category} ${styles.categoryBug}`;
    if (cat === "자료") return `${styles.category} ${styles.categoryData}`;

    return `${styles.category} ${styles.categoryNotice}`;
  };

  const filteredBugPosts =
    bugStatusFilter === "all"
      ? bugPosts
      : bugPosts.filter((p) => p.status === bugStatusFilter);

  const filteredDataPosts =
    dataAuthorFilter === "전체"
      ? posts
      : posts.filter((p) => p.author_nickname === dataAuthorFilter);

  const isInfoSuggestGroup = tab === "info" || tab === "suggest";

  return (
    <div className={styles.wrapper}>
      <section className={styles.heroWrap}>
        <div className={styles.hero}>
          <p className={styles.eyebrow}>게시판</p>
          <h1 className={styles.title}>
            {isInfoSuggestGroup ? "정보 공유 & 건의사항" : "버그 신고 & 자료실"}
          </h1>
          <p className={styles.desc}>
            {isInfoSuggestGroup
              ? "공유된 정보와 공지 사항, 건의 사항을 확인하세요."
              : "버그를 신고하고 팀 자료를 공유하세요."}
          </p>
        </div>
      </section>

      <section>
        <div className={styles.main}>
          {/* 서브 탭 — 해당 그룹만 표시 */}
          <div className={styles.tabs}>
            {isInfoSuggestGroup ? (
              <>
                <button
                  className={
                    tab === "info"
                      ? `${styles.tab} ${styles.tabActive}`
                      : styles.tab
                  }
                  onClick={() => handleTabChange("info")}
                >
                  정보게시판
                </button>
                <button
                  className={
                    tab === "suggest"
                      ? `${styles.tab} ${styles.tabActive}`
                      : styles.tab
                  }
                  onClick={() => handleTabChange("suggest")}
                >
                  건의게시판
                </button>
              </>
            ) : (
              <>
                <button
                  className={
                    tab === "bug"
                      ? `${styles.tab} ${styles.tabActive}`
                      : styles.tab
                  }
                  onClick={() => handleTabChange("bug")}
                >
                  버그게시판
                </button>
                <button
                  className={
                    tab === "data"
                      ? `${styles.tab} ${styles.tabActive}`
                      : styles.tab
                  }
                  onClick={() => handleTabChange("data")}
                >
                  자료게시판
                </button>
              </>
            )}
          </div>

          {/* 버그 게시판 */}
          {tab === "bug" && (
            <>
              <div className={styles.filterRow}>
                {(["all", "pending", "in_progress", "done"] as const).map(
                  (s) => (
                    <button
                      key={s}
                      className={
                        bugStatusFilter === s
                          ? `${styles.filterBtn} ${styles.filterBtnActive}`
                          : styles.filterBtn
                      }
                      onClick={() => setBugStatusFilter(s)}
                    >
                      {s === "all" ? "전체" : BUG_STATUS_LABELS[s]}
                      <span className={styles.filterCount}>
                        {s === "all"
                          ? bugPosts.length
                          : bugPosts.filter((p) => p.status === s).length}
                      </span>
                    </button>
                  ),
                )}
                <button
                  className={styles.writeBtn}
                  style={{ marginLeft: "auto" }}
                  onClick={() => {
                    if (!userRole) {
                      setLoginAlert(true);
                      return;
                    }
                    router.push("/board/write?tab=bug");
                  }}
                >
                  ✏️ 버그 신고
                </button>
              </div>

              <div className={styles.postList}>
                <div className={`${styles.listHeader} ${styles.listHeaderBug}`}>
                  <span>번호</span>
                  <span>제목</span>
                  <span>작성자</span>
                  <span>날짜</span>
                  <span>조회</span>
                  <span>상태</span>
                </div>
                {loading ? (
                  <div className={styles.empty}>불러오는 중...</div>
                ) : filteredBugPosts.length === 0 ? (
                  <div className={styles.empty}>게시글이 없습니다.</div>
                ) : (
                  filteredBugPosts.map((post) => (
                    <div
                      key={post.id}
                      className={`${styles.postRow} ${styles.postRowBug}`}
                    >
                      <span className={styles.postNum}>{post.id}</span>
                      <Link
                        href={`/board/${post.id}`}
                        className={styles.postTitleLink}
                      >
                        {post.title}
                      </Link>
                      <span className={styles.author}>
                        {post.author_nickname}
                      </span>
                      <span className={styles.date}>{post.created_at}</span>
                      <span className={styles.views}>👁 {post.views}</span>
                      <span className={styles.statusCell}>
                        {isAdmin(userRole) ? (
                          <select
                            className={`${styles.statusSelect} ${styles[`status_${post.status}`]}`}
                            value={post.status}
                            onChange={(e) =>
                              handleBugStatusChange(
                                post.id,
                                e.target.value as BugStatus,
                              )
                            }
                          >
                            <option value="pending">미처리</option>
                            <option value="in_progress">진행중</option>
                            <option value="done">처리완료</option>
                          </select>
                        ) : (
                          <span
                            className={`${styles.statusBadge} ${styles[`status_${post.status}`]}`}
                          >
                            {BUG_STATUS_LABELS[post.status]}
                          </span>
                        )}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </>
          )}

          {/* 자료 게시판 */}
          {tab === "data" && (
            <>
              <div className={styles.filterRow}>
                {DATA_AUTHORS.map((author) => (
                  <button
                    key={author}
                    className={
                      dataAuthorFilter === author
                        ? `${styles.filterBtn} ${styles.filterBtnActive}`
                        : styles.filterBtn
                    }
                    onClick={() => setDataAuthorFilter(author)}
                  >
                    {author}
                    {author !== "전체" && (
                      <span className={styles.filterCount}>
                        {
                          posts.filter((p) => p.author_nickname === author)
                            .length
                        }
                      </span>
                    )}
                  </button>
                ))}
                {isAdmin(userRole) && (
                  <button
                    className={styles.writeBtn}
                    style={{ marginLeft: "auto" }}
                    onClick={() => router.push("/board/write?tab=data")}
                  >
                    ✏️ 자료 올리기
                  </button>
                )}
              </div>

              <div className={styles.postList}>
                <div
                  className={`${styles.listHeader} ${styles.listHeaderData}`}
                >
                  <span>번호</span>
                  <span>제목</span>
                  <span>작성자</span>
                  <span>날짜</span>
                  <span>첨부</span>
                  <span>조회</span>
                </div>
                {loading ? (
                  <div className={styles.empty}>불러오는 중...</div>
                ) : filteredDataPosts.length === 0 ? (
                  <div className={styles.empty}>자료가 없습니다.</div>
                ) : (
                  filteredDataPosts.map((post) => (
                    <Link
                      key={post.id}
                      href={`/board/${post.id}`}
                      className={`${styles.postRow} ${styles.postRowData}`}
                    >
                      <span className={styles.postNum}>{post.id}</span>
                      <span className={styles.postTitle}>{post.title}</span>
                      <span className={styles.author}>
                        {post.author_nickname}
                      </span>
                      <span className={styles.date}>{post.created_at}</span>
                      <span className={styles.commentCol}>
                        {post.attachment_count ?? 0}
                      </span>
                      <span className={styles.views}>👁 {post.views}</span>
                    </Link>
                  ))
                )}
              </div>
            </>
          )}

          {/* 정보 / 건의 게시판 (기존) */}
          {isInfoSuggestGroup && (
            <>
              <div className={styles.toolbar}>
                <div className={styles.searchBox}>
                  <select
                    value={searchType}
                    onChange={(e) => setSearchType(e.target.value)}
                    className={styles.searchSelect}
                  >
                    {SEARCH_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {t.label}
                      </option>
                    ))}
                  </select>
                  <input
                    type="text"
                    placeholder="검색어를 입력하세요"
                    value={searchInput}
                    onChange={(e) => setSearchInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className={styles.search}
                  />
                  <button onClick={handleSearch} className={styles.searchBtn}>
                    검색
                  </button>
                </div>
                {(tab === "suggest" ||
                  userRole === "admin" ||
                  userRole === "manager") && (
                  <button
                    className={styles.writeBtn}
                    onClick={() => {
                      if (!userRole) {
                        setLoginAlert(true);
                        return;
                      }
                      router.push(`/board/write?tab=${tab}`);
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

                {notices.map((post) => (
                  <Link
                    key={`n-${post.id}`}
                    href={`/board/${post.id}`}
                    className={`${styles.postRow} ${styles.pinned}`}
                  >
                    <span className={styles.postNum}>{post.id}</span>
                    <span className={getCatClass("공지")}>공지</span>
                    <span className={styles.postTitle}>
                      <span className={styles.pin}>📌</span>
                      {post.title}
                      {!!post.attachment_count && (
                        <span className={styles.clip}>
                          [{post.attachment_count}]
                        </span>
                      )}
                    </span>
                    <span className={styles.author}>
                      {post.author_nickname}
                    </span>
                    <span className={styles.date}>{post.created_at}</span>
                    <span className={styles.commentCol}>
                      {post.comment_count ?? 0}
                    </span>
                    <span className={styles.views}>👁 {post.views}</span>
                  </Link>
                ))}

                {loading ? (
                  <div className={styles.empty}>불러오는 중...</div>
                ) : posts.length === 0 ? (
                  <div className={styles.empty}>게시글이 없습니다.</div>
                ) : (
                  posts.map((post) => (
                    <Link
                      key={post.id}
                      href={`/board/${post.id}`}
                      className={styles.postRow}
                    >
                      <span className={styles.postNum}>{post.id}</span>
                      <span className={getCatClass(post.category)}>
                        {post.category}
                      </span>
                      <span className={styles.postTitle}>
                        {post.title}
                        {!!post.attachment_count && (
                          <span className={styles.clip}>
                            [{post.attachment_count}]
                          </span>
                        )}
                      </span>
                      <span className={styles.author}>
                        {post.author_nickname}
                      </span>
                      <span className={styles.date}>{post.created_at}</span>
                      <span className={styles.commentCol}>
                        {post.comment_count ?? 0}
                      </span>
                      <span className={styles.views}>👁 {post.views}</span>
                    </Link>
                  ))
                )}
              </div>

              <div className={styles.pagination}>
                <button
                  className={styles.pageNav}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  &lt;
                </button>
                {paginationRange().map((n) => (
                  <button
                    key={n}
                    onClick={() => setPage(n)}
                    className={
                      n === page
                        ? `${styles.pageBtn} ${styles.pageActive}`
                        : styles.pageBtn
                    }
                  >
                    {n}
                  </button>
                ))}
                <button
                  className={styles.pageNav}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  &gt;
                </button>
              </div>
            </>
          )}
        </div>
      </section>

      {loginAlert && (
        <div
          className={styles.modalOverlay}
          onClick={() => setLoginAlert(false)}
        >
          <div className={styles.modalBox} onClick={(e) => e.stopPropagation()}>
            <p className={styles.modalMsg}>로그인 후 이용해주세요.</p>
            <div className={styles.modalBtns}>
              <button
                className={styles.modalLogin}
                onClick={() => router.push("/login")}
              >
                로그인하기
              </button>
              <button
                className={styles.modalCancel}
                onClick={() => setLoginAlert(false)}
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function isAdmin(role: string) {
  return role === "admin" || role === "manager";
}

import { Suspense } from "react";
export default function BoardPage() {
  return (
    <Suspense fallback={<div>로딩중...</div>}>
      <BoardPageInner />
    </Suspense>
  );
}
