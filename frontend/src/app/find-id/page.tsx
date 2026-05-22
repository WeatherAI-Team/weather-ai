"use client";

import { useState } from "react";
import Link from "next/link";

export default function FindIdPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loginId, setLoginId] = useState("");

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

  const handleFindId = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setMessage("");
    setLoginId("");

    try {
      const res = await fetch(`${API_BASE_URL}/api/member/find-id`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setMessage(data.message || "아이디 찾기에 실패했습니다.");
        return;
      }

      if (data.account_type === "social") {
        setLoginId("");
        setMessage(data.message);
        return;
      }
      setLoginId(data.login_id);
      setMessage(data.message);
    } catch (error) {
      console.error(error);
      setMessage("서버 연결에 실패했습니다.");
    }
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <section
        style={{
          width: "420px",
          padding: "40px",
          borderRadius: "24px",
          background: "#fff",
        }}
      >
        <h1 style={{ marginBottom: "12px" }}>아이디 찾기</h1>
        <p style={{ marginBottom: "28px" }}>
          가입할 때 사용한 이메일을 입력하세요.
        </p>

        <form onSubmit={handleFindId}>
          <label style={{ display: "block", marginBottom: "12px" }}>
            이메일
          </label>

          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="이메일을 입력하세요"
            style={{
              width: "100%",
              height: "48px",
              padding: "0 14px",
              border: "1px solid #cbd5e1",
              borderRadius: "12px",
              marginBottom: "18px",
            }}
          />

          <button
            type="submit"
            style={{
              width: "100%",
              height: "50px",
              border: "none",
              borderRadius: "12px",
              backgroundColor: "#168bd3",
              color: "#fff",
              fontWeight: 700,
              cursor: "pointer",
            }}
          >
            아이디 찾기
          </button>
        </form>

        {message && (
          <p style={{ marginTop: "20px", fontWeight: 600 }}>{message}</p>
        )}

        {loginId && (
          <div
            style={{
              marginTop: "16px",
              padding: "16px",
              background: "#f1f5f9",
              borderRadius: "12px",
            }}
          >
            회원님의 아이디는 <strong>{loginId}</strong> 입니다.
          </div>
        )}

        <div style={{ marginTop: "24px" }}>
          <Link href="/login">로그인 페이지로 돌아가기</Link>
        </div>
      </section>
    </main>
  );
}
