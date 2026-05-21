"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";

import styles from "./page.module.css";
import KakaoLoginButton from "@/components/auth/KakaoLoginButton";
import NaverLoginButton from "@/components/auth/NaverLoginButton";
import GoogleLoginButton from "@/components/auth/GoogleLoginButton";

export default function LoginPage() {
  const router = useRouter();

  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    try {
      const res = await fetch(`${API_BASE_URL}/api/member/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          login_id: loginId,
          password,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.success) {
        setMessage(data.message || "로그인에 실패했습니다.");
        return;
      }

      localStorage.setItem("user", JSON.stringify(data.data));
      localStorage.setItem("loginUser", JSON.stringify(data.data));

      router.push("/");
    } catch (error) {
      console.error(error);
      setMessage("서버 연결에 실패했습니다.");
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.loginCard}>
        <div className={styles.header}>
          <div className={styles.eyebrow}>
            <Image src="/logo.png" alt="WeatherGuard AI 로고" width={120} height={40} />
          </div>
          <h1>로그인</h1>
          <p>로그인하고 다양한 서비스를 이용하세요.</p>
        </div>

        <form className={styles.form} onSubmit={handleLogin}>
          <label className={styles.field}>
            <span>아이디</span>
            <input
              type="text"
              name="login_id"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              placeholder="아이디를 입력하세요"
            />
          </label>

          <label className={styles.field}>
            <span>비밀번호</span>
            <input
              type="password"
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호를 입력하세요"
            />
          </label>

          {message && <p className={styles.message}>{message}</p>}

          <button type="submit" className={styles.loginButton}>
            로그인
          </button>
        </form>
        
        <div className={styles.links}>
          <Link href="/find-id">아이디 찾기</Link>
          <span />
          <a href="#">비밀번호 찾기</a>
          <span />
          <Link href="/register">회원가입</Link>
        </div>

        <div className={styles.divider}>
          <span>또는 소셜 계정으로 로그인</span>
        </div>

        <div className={styles.socialList}>
          <KakaoLoginButton />
          <NaverLoginButton />
          <GoogleLoginButton />
        </div>
      </section>
    </main>
  );
}
