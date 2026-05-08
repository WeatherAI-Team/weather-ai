"use client";

export default function NaverLoginButton() {
  const handleNaverLogin = () => {
    console.log("네이버 로그인 버튼 클릭됨");

    window.location.href = "http://localhost:5000/api/auth/naver/login";
  };

  return (
    <button
      type="button"
      onClick={handleNaverLogin}
      style={{
        width: "130px",
        height: "36px",
        border: "none",
        borderRadius: "6px",
        backgroundColor: "#03C75A",
        color: "#ffffff",
        fontSize: "13px",
        fontWeight: 700,
        cursor: "pointer",
        marginLeft: "18px",
      }}
    >
      네이버 로그인
    </button>
  );
}