'use client'
import { createContext, useContext, useEffect, useState, useCallback, useRef, ReactNode } from 'react'

export type Notification = {
  id: number
  target_type: string       // 'ADMIN' | 'MEMBER'
  member_id: number | null
  event_id: number | null
  title: string             // 알림 제목 (주 표시 텍스트)
  content: string           // 알림 상세 내용
  risk_level: string        // 'HIGH' | 'MEDIUM' | 'LOW'
  status: string            // 'PENDING' | 'SENT' | 'FAILED' | 'READ'
  is_confirmed: boolean
  sent_at: string | null
  read_at: string | null
  created_at: string
  // detection_events JOIN으로 API가 추가 제공하는 필드
  location_name: string
  weather_type: string
}

type NotificationContextType = {
  unreadCount: number
  notifications: Notification[]
  markAllRead: () => void
  resolveNotification: (id: number) => Promise<void>
}

const NotificationContext = createContext<NotificationContextType>({
  unreadCount: 0,
  notifications: [],
  markAllRead: () => {},
  resolveNotification: async () => {},
})

function getToken(): string | null {
  try {
    const raw = localStorage.getItem('user')
    if (raw) { const p = JSON.parse(raw); if (p?.access_token) return p.access_token }
    return localStorage.getItem('access_token')
  } catch { return null }
}

function isAdmin(): boolean {
  try {
    const raw = localStorage.getItem('user')
    if (raw) { const p = JSON.parse(raw); return p?.role === 'admin' }
  } catch {}
  return false
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [unreadCount, setUnreadCount] = useState(0)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const token = getToken()
    if (!token || !isAdmin()) return

    const API = process.env.NEXT_PUBLIC_API_URL ?? ''

    // 초기 unread count 로드
    fetch(`${API}/api/admin/notifications/unread-count`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then(r => r.json())
      .then(data => { if (data.success) setUnreadCount(data.data.count) })
      .catch(() => {})

    // SSE 실시간 연결 (토큰을 쿼리 파라미터로 전달 - EventSource는 헤더 설정 불가)
    const connect = () => {
      const es = new EventSource(`${API}/api/admin/notifications/stream?token=${token}`)
      esRef.current = es

      es.addEventListener('notification', (e) => {
        try {
          const notification: Notification = JSON.parse(e.data)
          setNotifications(prev => [notification, ...prev].slice(0, 100))
          setUnreadCount(prev => prev + 1)
        } catch {}
      })

      es.onerror = () => {
        es.close()
        // 5초 후 재연결
        setTimeout(connect, 5000)
      }
    }

    connect()

    return () => {
      esRef.current?.close()
    }
  }, [])

  const markAllRead = useCallback(() => {
    setUnreadCount(0)
  }, [])

  const resolveNotification = useCallback(async (id: number) => {
    const token = getToken()
    if (!token) return
    const API = process.env.NEXT_PUBLIC_API_URL ?? ''
    await fetch(`${API}/api/admin/notifications/${id}/read`, {
      method: 'PATCH',
      headers: { Authorization: `Bearer ${token}` },
    })
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, status: 'READ', read_at: new Date().toISOString() } : n))
  }, [])

  return (
    <NotificationContext.Provider value={{ unreadCount, notifications, markAllRead, resolveNotification }}>
      {children}
    </NotificationContext.Provider>
  )
}

export function useNotification() {
  return useContext(NotificationContext)
}
