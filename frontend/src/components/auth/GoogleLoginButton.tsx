"use client";

import Script from "next/script";
import { useState, useRef } from "react";

declare global {
  interface Window {
    google?: any;
  }
}

export default function GoogleLoginButton() {
  const [message, setMessage] = useState("");
  const isInitialized = useRef(false);

  const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:5000";
  const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

  const handleGoogleLogin = async (response: { credential?: string }) => {
    const credential = response.credential;
    if (!credential) {
      setMessage("구글 인증 토큰을 받지 못했습니다.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/member/google`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential }),
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setMessage(data.message || "구글 로그인에 실패했습니다.");
        return;
      }

      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      window.location.href = "/";
    } catch (error) {
      console.error(error);
      setMessage("서버 연결에 실패했습니다.");
    }
  };

  const initializeGoogleButton = () => {
    if (isInitialized.current || !window.google || !GOOGLE_CLIENT_ID) return;

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleLogin,
      use_fedcm_for_prompt: false,
      auto_select: false, // 자동으로 계정 선택창이 뜨는 것을 방지
    });

    isInitialized.current = true;
  };

  const handlePrompt = () => {
    if (window.google) {
      if (!isInitialized.current) initializeGoogleButton();
      window.google.accounts.id.prompt();
    } else {
      setMessage("구글 라이브러리를 로드 중입니다. 잠시 후 다시 시도해주세요.");
    }
  };

  return (
    <>
      <Script
        src="https://accounts.google.com/gsi/client"
        strategy="afterInteractive"
        onLoad={initializeGoogleButton}
      />

      <button
        type="button"
        onClick={handlePrompt}
        style={{
          width: "360px",
          height: "48px",
          borderRadius: "100px",
          backgroundColor: "#ffffff",
          border: "1px solid #dadce0",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: "10px",
          fontSize: "16px",
          fontWeight: "500",
          cursor: "pointer",
          padding: "0",
        }}
      >
        <img
          src="https://www.gstatic.com/images/branding/product/1x/gsa_512dp.png"
          alt="Google"
          width="20"
        />
        <span>Google 계정으로 로그인</span>
      </button>

      {message && (
        <p
          style={{
            marginTop: "8px",
            fontSize: "13px",
            color: "crimson",
            textAlign: "center",
          }}
        >
          {message}
        </p>
      )}
    </>
  );
}
