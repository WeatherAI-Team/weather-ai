"use client";

export default function KakaoLoginButton() {
  const handleLogin = () => {
    window.location.href = "http://localhost:5000/api/auth/kakao/login";
  };

  return (
    <button
      onClick={handleLogin}
      style={{
        marginTop: "30px",
        padding: "14px 24px",
        backgroundColor: "#FEE500",
        color: "#000",
        border: "none",
        borderRadius: "8px",
        fontWeight: "bold",
        cursor: "pointer",
      }}
    >
      카카오로 로그인
    </button>
  );
}