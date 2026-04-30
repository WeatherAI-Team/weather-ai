'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import styles from './Header.module.css'

// 실제 구현 시 auth context/hook으로 교체
const useAuth = () => ({
  user: { name: '홍길동', role: 'admin', grade: 'GOLD' },
  isAdmin: true,
})

export default function Header() {
  const pathname = usePathname()
  const { user, isAdmin } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const navLinks = [
    { href: '/intro', label: '소개' },
    { href: '/ai', label: 'AI 탐지' },
    { href: '/board', label: '게시판' },
    ...(isAdmin ? [{ href: '/admin', label: '관리자' }] : []),
  ]

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ''}`}>
      <div className={styles.inner}>
        {/* Logo */}
        <Link href="/" className={styles.logo}>
          <span className={styles.logoIcon}>
            <img src="/logo.png" width="90" height="50" alt="로고" />
          </span>
          {/* <span className={styles.logoText}>Weather<em>AI</em></span> */}
        </Link>

        {/* Desktop Nav */}
        <nav className={styles.nav}>
          {navLinks.map(({ href, label }) => (
            <Link
              key={href}
              href={href}
              className={`${styles.navLink} ${pathname?.startsWith(href) ? styles.active : ''} ${href === '/admin' ? styles.adminLink : ''}`}
            >
              {label}
              {href === '/admin' && <span className={styles.adminBadge}>ADMIN</span>}
            </Link>
          ))}
        </nav>

        {/* Profile */}
        <div className={styles.right}>
          <Link href="/mypage" className={styles.profileBtn} title="마이페이지">
            <span className={styles.avatar}>
              {user?.name?.[0] ?? 'U'}
            </span>
            <span className={styles.gradeBadge}>{user?.grade}</span>
          </Link>

          {/* Mobile hamburger */}
          <button
            className={styles.hamburger}
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="메뉴 열기"
          >
            <span className={menuOpen ? styles.barOpen : ''} />
            <span className={menuOpen ? styles.barOpen : ''} />
            <span className={menuOpen ? styles.barOpen : ''} />
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          {navLinks.map(({ href, label }) => (
            <Link key={href} href={href} className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
              {label}
            </Link>
          ))}
          <Link href="/mypage" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
            마이페이지
          </Link>
        </div>
      )}
    </header>
  )
}
