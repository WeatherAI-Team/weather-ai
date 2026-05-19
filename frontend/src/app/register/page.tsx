"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import styles from "./page.module.css";

export default function RegisterPage() {
  const router = useRouter();

  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [realName, setRealName] = useState("");
  const [nickname, setNickname] = useState("");
  const [message, setMessage] = useState("");

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

  const handleRegister = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      const res = await fetch(`${API_BASE_URL}/api/member/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          login_id: loginId,
          password,
          email,
          nickname,
          real_name: realName,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setMessage(data.message || "회원가입에 실패했습니다.");
        return;
      }

      alert("회원가입이 완료되었습니다.");
      router.push("/login");
    } catch (error) {
      console.error(error);
      setMessage("서버 연결에 실패했습니다.");
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.registerCard}>
        <div className={styles.header}>
          <p className={styles.eyebrow}>WeatherAI</p>
          <h1>회원가입</h1>
          <p>계정을 생성하고 AI 탐지 서비스를 시작하세요.</p>
        </div>

        <form className={styles.form} onSubmit={handleRegister}>
          <label className={styles.field}>
            <span>아이디</span>
            <input
              type="text"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              placeholder="아이디를 입력하세요"
            />
          </label>

          <label className={styles.field}>
            <span>비밀번호</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
            />
          </label>

          <label className={styles.field}>
            <span>이메일</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="이메일을 입력하세요"
            />
          </label>

          <label className={styles.field}>
            <span>이름</span>
            <input
              type="text"
              value={realName}
              onChange={(e) => setRealName(e.target.value)}
              placeholder="실명을 입력하세요"
            />
          </label>

          <label className={styles.field}>
            <span>닉네임</span>
            <input
              type="text"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="닉네임을 입력하세요"
            />
          </label>

          {message && <p className={styles.message}>{message}</p>}

          <button type="submit" className={styles.registerButton}>
            회원가입
          </button>
        </form>

        <div className={styles.bottomLink}>
          이미 계정이 있으신가요? <Link href="/login">로그인</Link>
        </div>
      </section>
    </main>
  );
}
