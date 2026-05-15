"use client";

export default function GoogleLoginButton() {
  const handleGoogleLogin = () => {
    window.location.href = "http://localhost:5000/api/auth/google/login";
  };

  return (
    <button
      type="button"
      onClick={handleGoogleLogin}
      style={{
        width: "100%",
        height: "46px",
        border: "1px solid #dde6ef",
        borderRadius: "14px",
        backgroundColor: "#ffffff",
        color: "#2d4054",
        fontSize: "14px",
        fontWeight: 900,
        cursor: "pointer",
      }}
    >
      구글 로그인
    </button>
  );
}
