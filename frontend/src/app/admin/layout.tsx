"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type User = { role: string } | null;

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    let user: User = null;
    try {
      const saved = localStorage.getItem("user");
      user = saved ? JSON.parse(saved) : null;
    } catch {}

    if (!user || (user.role !== "admin" && user.role !== "manager")) {
      router.replace("/login");
      return;
    }

    setChecked(true);
  }, [router]);

  // 실제 접근 제어는 백엔드 API(auth_decorators.admin_required)가 담당한다.
  // 여기서는 비관리자에게 관리자 화면이 그대로 노출되지 않도록 막는 UX 가드다.
  if (!checked) return null;

  return <>{children}</>;
}
