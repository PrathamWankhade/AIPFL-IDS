'use client'

import { useEffect, ReactNode } from 'react'
import { usePathname } from 'next/navigation'

function initReveals() {
  const els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right')
  if (!els.length) return

  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
          obs.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
  )
  els.forEach((el) => obs.observe(el))
}

function initCounters() {
  const counters = document.querySelectorAll('[data-count-to]')
  if (!counters.length) return

  const obs = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target as HTMLElement
        const raw = el.getAttribute('data-count-to') || '0'
        const target = parseFloat(raw)
        const suffix = el.getAttribute('data-count-suffix') || ''
        const duration = parseInt(el.getAttribute('data-count-duration') || '2000')
        // Preserve the source value's own precision: `79.13` must settle as
        // `79.13` (not rounded to `79.1`), and ECE `0.007` must never collapse
        // to `0.0`. Non-numeric placeholders (e.g. a loading "—") are left as-is.
        const decimals = raw.includes('.') ? raw.split('.')[1].length : 0
        if (!Number.isFinite(target)) {
          obs.unobserve(el)
          return
        }

        const start = performance.now()
        const update = (now: number) => {
          const t = Math.min((now - start) / duration, 1)
          const eased = 1 - Math.pow(1 - t, 3)
          el.textContent = (target * eased).toFixed(decimals) + suffix
          if (t < 1) requestAnimationFrame(update)
          else el.textContent = target.toFixed(decimals) + suffix
        }
        requestAnimationFrame(update)
        obs.unobserve(el)
      }
    })
  }, { threshold: 0.3 })

  counters.forEach((el) => obs.observe(el))
}

function initTypewriters() {
  const els = document.querySelectorAll('.typewriter')
  if (!els.length) return

  const obs = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const el = entry.target as HTMLElement
        const text = el.getAttribute('data-text') || el.textContent || ''
        const speed = parseInt(el.getAttribute('data-speed') || '40')
        let i = 0
        el.textContent = ''
        el.style.visibility = 'visible'
        const interval = setInterval(() => {
          if (i < text.length) {
            el.textContent += text[i]
            i++
          } else {
            clearInterval(interval)
            el.classList.add('done')
          }
        }, speed)
        obs.unobserve(el)
      }
    })
  }, { threshold: 0.2 })

  els.forEach((el) => obs.observe(el))
}

function initCycleText() {
  const containers = document.querySelectorAll('.cycle-text')
  if (!containers.length) return

  containers.forEach((container) => {
    const spans = container.querySelectorAll('span')
    if (!spans.length) return
    let idx = 0
    spans[0].classList.add('active')
    setInterval(() => {
      spans[idx].classList.remove('active')
      idx = (idx + 1) % spans.length
      spans[idx].classList.add('active')
    }, 2500)
  })
}

export function AnimationInit({ children }: { children: ReactNode }) {
  const pathname = usePathname()

  useEffect(() => {
    const t = setTimeout(() => {
      initReveals()
      initCounters()
      initTypewriters()
      initCycleText()
    }, 80)
    return () => clearTimeout(t)
  }, [pathname])

  return <div className="page-enter">{children}</div>
}
