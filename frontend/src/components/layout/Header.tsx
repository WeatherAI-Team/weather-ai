"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import styles from "./Header.module.css";

type User = {
  id: number;
  login_id: string;
  email: string;
  nickname: string;
  role: string;
  provider: string;
  grade?: string;
} | null;

export default function Header() {
  const pathname = usePathname();
  const [user, setUser] = useState<User>(null);
  const [mounted, setMounted] = useState(false);
  const isAdmin = user?.role === "admin";
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("user");
      setUser(saved ? JSON.parse(saved) : null);
    } catch {}
    setMounted(true);

    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

const handleLogout = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/member/logout`, {
        method: "POST",
        credentials: "include",
      });
    } catch (e) {}
    localStorage.removeItem("user");
    localStorage.removeItem("loginUser");
    localStorage.removeItem("access_token");
    setUser(null);
    setProfileOpen(false);
    window.location.href = "/";
  };

  const navLinks = [
    { href: "/intro", label: "소개" },
    { href: "/ai", label: "CCTV 관제" },
    { href: "/board", label: "게시판" },
    ...(user ? [{ href: "/mypage", label: "마이페이지" }] : []),
    ...(user ? [{ href: "#", label: "로그아웃", onClick: handleLogout }] : []),
    ...(isAdmin ? [{ href: "/admin", label: "관리자" }] : []),
  ];

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ""}`}>
      <div className={styles.inner}>

        {/* 로고 */}
        <Link href="/" className={styles.logo}>
          <span className={styles.logoIcon}>
            <img src="/logo.png" width="90" height="50" alt="로고" />
          </span>
        </Link>

        {/* Desktop Nav */}
        <nav className={styles.nav}>
          <Link href="/intro" className={`${styles.navLink} ${pathname?.startsWith("/intro") ? styles.active : ""}`}>소개</Link>
          <Link href="/ai" className={`${styles.navLink} ${pathname?.startsWith("/ai") ? styles.active : ""}`}>CCTV 관제</Link>
          <div className={styles.boardMenu}>
            <Link href="/board" className={`${styles.navLink} ${pathname?.startsWith("/board") ? styles.active : ""}`}>
              게시판 <span className={styles.boardArrow}>▾</span>
            </Link>
            <div className={styles.boardDropdown}>
              <Link href="/board?tab=info" className={styles.boardDropdownItem}>정보 &amp; 건의</Link>
              <Link href="/board?tab=bug" className={styles.boardDropdownItem}>버그 &amp; 자료</Link>
            </div>
          </div>

          {/* 로그인 후 마이페이지, 로그아웃 네비에 바로 표시 */}
          {user && (
            <>
              <Link href="/mypage" className={`${styles.navLink} ${pathname?.startsWith("/mypage") ? styles.active : ""}`}>마이페이지</Link>
              <button className={styles.navLink} onClick={handleLogout}>로그아웃</button>
            </>
          )}

          {/* 관리자만 보이는 메뉴 (뱃지 없이) */}
          {isAdmin && (
            <Link href="/admin" className={`${styles.navLink} ${styles.adminLink} ${pathname?.startsWith("/admin") ? styles.active : ""}`}>
              관제센터
            </Link>
          )}
        </nav>

        {/* 오른쪽 영역 */}
        <div className={styles.right}>

          {mounted && (user ? (
            /* ── 로그인 상태 ── */
            <div className={styles.profileArea}>
              <span className={styles.nicknameText}>
                <span className={styles.roleLabel}>
                  {{ admin: '관리자', manager: '매니저', user: '일반' }[user.role] ?? user.role}
                </span>
                <span className={styles.nicknameDivider}> | </span>
                {user.nickname} 님
              </span>
              <button
                type="button"
                className={styles.profileBtn}
                onClick={() => setProfileOpen(!profileOpen)}
                title="프로필 메뉴"
              >
                {user.grade && <span className={styles.gradeBadge}>{user.grade}</span>}
              </button>

              {/* 드롭다운 */}
              {profileOpen && (
                <div className={styles.profileDropdown}>
                  <div className={styles.dropdownUser}>
                    <span className={styles.dropdownNickname}>{user.nickname}</span>
                    <span className={styles.dropdownEmail}>{user.email}</span>
                  </div>
                </div>
              )}
            </div>
          ) : (
            /* ── 비로그인 상태 ── */
            <Link href="/login" className={styles.loginBtn}>
              로그인
            </Link>
          ))}

          {/* 모바일 햄버거 */}
          <button
            className={styles.hamburger}
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="메뉴 열기"
          >
            <span className={menuOpen ? styles.barOpen : ""} />
            <span className={menuOpen ? styles.barOpen : ""} />
            <span className={menuOpen ? styles.barOpen : ""} />
          </button>
        </div>
      </div>

      {/* 모바일 메뉴 */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          {[
            { href: "/intro", label: "소개" },
            { href: "/ai", label: "CCTV 관제" },
            { href: "/board", label: "게시판" },
            ...(isAdmin ? [{ href: "/admin", label: "관리자" }] : []),
          ].map(({ href, label }) => (
            <Link key={href} href={href} className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
              {label}
            </Link>
          ))}
          {user ? (
            <>
              <Link href="/mypage" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>마이페이지</Link>
              <button className={styles.mobileLink} onClick={handleLogout}>로그아웃</button>
            </>
          ) : (
            <Link href="/login" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>로그인</Link>
          )}
        </div>
      )}
    </header>
  );
}
