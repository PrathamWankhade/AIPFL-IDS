'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useTheme } from './ThemeProvider'

export function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const pathname = usePathname()
  const { theme, toggle } = useTheme()
  const menuRef = useRef<HTMLUListElement>(null)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    setMenuOpen(false)
    document.body.style.overflow = ''
  }, [pathname])

  useEffect(() => {
    document.body.style.overflow = menuOpen ? 'hidden' : ''
  }, [menuOpen])

  useEffect(() => {
    if (!menuOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenuOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [menuOpen])

  const links = [
    { to: '/', label: 'Home' },
    { to: '/about', label: 'About' },
    { to: '/dashboard', label: 'Dashboard' },
    { to: '/predict', label: 'Predict' },
    { to: '/contact', label: 'Contact' },
  ]

  return (
    <header className={`header${scrolled ? ' scrolled' : ''}`}>
      <nav className="navbar">
        <Link href="/" className="logo">
          <div className="logo-icon">
            <i className="fa-solid fa-shield-halved" />
          </div>
          <div className="logo-text">
            AIPFL<span>IDS</span>
          </div>
        </Link>

        <ul ref={menuRef} id="primary-navigation" className={`nav-menu${menuOpen ? ' open' : ''}`}>
          {links.map((l) => (
            <li key={l.to}>
              <Link
                href={l.to}
                className={`nav-link${pathname === l.to ? ' active' : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                {l.label}
              </Link>
            </li>
          ))}
        </ul>

        <div className="nav-right">
          <button className="theme-toggle" onClick={toggle} aria-label="Toggle theme">
            <i className={`fa-solid fa-${theme === 'light' ? 'moon' : 'sun'}`} />
          </button>
          <Link href="/predict" className="nav-cta">Get Started</Link>
          <button
            className="menu-btn"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
            aria-controls="primary-navigation"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            <i className={`fa-solid fa-${menuOpen ? 'xmark' : 'bars'}`} />
          </button>
        </div>
      </nav>
    </header>
  )
}
