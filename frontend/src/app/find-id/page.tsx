"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import Image from "next/image";
import styles from "./page.module.css";

export default function FindIdPage() {
  useEffect(() => { document.title = 'Weather AI - 아이디 찾기' }, [])
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [loginId, setLoginId] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

  const handleFindId = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    setMessage("");
    setLoginId("");
    setLoading(true);

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
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.loginCard}>

        <div className={styles.header}>
          <div className={styles.logoWrap}>
            <Image src="/logo.png" alt="WeatherAI 로고" width={0} height={0} sizes="100vw" style={{ width: "auto", height: "48px" }} />
          </div>
          <h1>아이디 찾기</h1>
          <p>가입할 때 사용한 이메일을 입력하세요</p>
        </div>

        <form className={styles.form} onSubmit={handleFindId}>
          <label className={styles.field}>
            <span>이메일</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="이메일을 입력하세요"
            />
          </label>

          <button type="submit" className={styles.loginButton} disabled={loading}>
            {loading ? "찾는 중..." : "아이디 찾기"}
          </button>
        </form>

        {message && !loginId && (
          <p className={styles.error}>{message}</p>
        )}

        {loginId && (
          <div className={styles.resultBox}>
            회원님의 아이디는 <strong>{loginId}</strong> 입니다.
          </div>
        )}

        <div className={styles.links}>
          <Link href="/login">로그인</Link>
          <span />
          <Link href="/find-pw">비밀번호 찾기</Link>
          <span />
          <Link href="/register">회원가입</Link>
        </div>

      </div>
    </div>
  );
}
