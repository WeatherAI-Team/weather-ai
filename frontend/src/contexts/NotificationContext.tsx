"use client";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  useRef,
  ReactNode,
} from "react";

export type Notification = {
  id: number;
  target_type: string;
  member_id: number | null;
  event_id: number | null;
  title: string;
  content: string;
  risk_level: string;
  status: string;
  is_confirmed: boolean;
  sent_at: string | null;
  read_at: string | null;
  created_at: string;
  location_name: string;
  weather_type: string;
};

type NotificationContextType = {
  unreadCount: number;
  notifications: Notification[];
  markAllRead: () => void;
  resolveNotification: (id: number) => Promise<void>;
  updateNotificationConfirm: (id: number, confirmed: boolean) => void;
  revertNotificationStatus: (id: number) => void;
};

const NotificationContext = createContext<NotificationContextType>({
  unreadCount: 0,
  notifications: [],
  markAllRead: () => {},
  resolveNotification: async () => {},
  updateNotificationConfirm: () => {},
  revertNotificationStatus: () => {},
});

function getToken(): string | null {
  try {
    const getTokenFromJson = (key: string) => {
      const raw = localStorage.getItem(key);
      if (!raw) return null;

      const obj = JSON.parse(raw);

      return (
        obj?.access_token ||
        obj?.accessToken ||
        obj?.token ||
        obj?.authToken ||
        obj?.jwt ||
        obj?.data?.access_token ||
        obj?.data?.accessToken ||
        obj?.data?.token ||
        null
      );
    };

    const jsonToken = getTokenFromJson("loginUser") || getTokenFromJson("user");
    if (jsonToken) return jsonToken;

    return (
      localStorage.getItem("access_token") ||
      localStorage.getItem("token") ||
      localStorage.getItem("accessToken") ||
      localStorage.getItem("authToken")
    );
  } catch {
    return null;
  }
}

function isAdmin(): boolean {
  try {
    const checkRoleFromJson = (key: string) => {
      const raw = localStorage.getItem(key);
      if (!raw) return false;

      const obj = JSON.parse(raw);

      return obj?.role === "admin" || obj?.data?.role === "admin";
    };

    return checkRoleFromJson("loginUser") || checkRoleFromJson("user");
  } catch {
    return false;
  }
}

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [popups, setPopups] = useState<Notification[]>([]);
  const esRef = useRef<EventSource | null>(null);
  const lastIdRef = useRef<number>(0);

  useEffect(() => {
    const token = getToken();
    if (!token || !isAdmin()) return;

    const API =
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:5000";

    fetch(`${API}/api/admin/notifications/unread-count`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.success) setUnreadCount(data.data.count);
      })
      .catch(() => {});

    const connect = (startId: number) => {
      const url = `${API}/api/admin/notifications/stream?token=${token}&last_id=${startId}`;
      const es = new EventSource(url);
      esRef.current = es;

      es.addEventListener("notification", (e) => {
        try {
          const notification: Notification = JSON.parse(e.data);
          lastIdRef.current = Math.max(lastIdRef.current, notification.id);
          setNotifications((prev) => [notification, ...prev].slice(0, 100));
          setUnreadCount((prev) => prev + 1);

          setPopups((prev) => [...prev, notification].slice(-3));
          setTimeout(() => {
            setPopups((prev) => prev.filter((p) => p.id !== notification.id));
          }, 5000);
        } catch {}
      });

      es.onerror = () => {
        es.close();
        setTimeout(() => connect(lastIdRef.current), 5000);
      };
    };

    // 최신 id 가져온 후 SSE 연결
    fetch(`${API}/api/admin/notifications?per_page=1`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => {
        const latestId = data?.data?.items?.[0]?.id ?? 0;
        lastIdRef.current = latestId;
        connect(latestId);
      })
      .catch(() => connect(0));

    return () => {
      esRef.current?.close();
    };
  }, []);

  const markAllRead = useCallback(() => {
    setUnreadCount(0);
  }, []);

  const resolveNotification = useCallback(async (id: number) => {
    const token = getToken();
    if (!token) return;
    const API =
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "http://localhost:5000";
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id
          ? { ...n, status: "READ", read_at: new Date().toISOString() }
          : n,
      ),
    );
    fetch(`${API}/api/admin/notifications/${id}/read`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
    });
  }, []);

  const updateNotificationConfirm = useCallback(
    (id: number, confirmed: boolean) => {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_confirmed: confirmed } : n)),
      );
    },
    [],
  );

  const revertNotificationStatus = useCallback((id: number) => {
    setNotifications((prev) =>
      prev.map((n) =>
        n.id === id ? { ...n, status: "SENT", read_at: null } : n,
      ),
    );
  }, []);

  return (
    <NotificationContext.Provider
      value={{
        unreadCount,
        notifications,
        markAllRead,
        resolveNotification,
        updateNotificationConfirm,
        revertNotificationStatus,
      }}
    >
      {children}

      {/* 팝업 */}
      <div
        style={{
          position: "fixed",
          top: "20px",
          right: "20px",
          zIndex: 9999,
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {popups.map((popup) => (
          <div
            key={popup.id}
            style={{
              background: popup.risk_level === "DANGER" ? "#e74c3c" : "#e67e22",
              color: "#fff",
              borderRadius: "8px",
              padding: "16px 20px",
              minWidth: "300px",
              boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
            }}
          >
            <div style={{ fontWeight: "bold", marginBottom: "6px" }}>
              ⚠️ {popup.title}
            </div>
            <div style={{ fontSize: "13px", opacity: 0.9 }}>
              {popup.content}
            </div>
            <button
              onClick={() =>
                setPopups((prev) => prev.filter((p) => p.id !== popup.id))
              }
              style={{
                marginTop: "8px",
                background: "rgba(255,255,255,0.2)",
                border: "none",
                color: "#fff",
                borderRadius: "4px",
                padding: "4px 10px",
                cursor: "pointer",
                fontSize: "12px",
              }}
            >
              닫기
            </button>
          </div>
        ))}
      </div>
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  return useContext(NotificationContext);
}
