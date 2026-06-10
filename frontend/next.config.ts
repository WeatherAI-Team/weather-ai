// 기존 로컬 배포 코드
// import type { NextConfig } from "next";

// const nextConfig: NextConfig = {
//   /* config options here */
//   reactCompiler: true,
// };

// export default nextConfig;
// 배포 코드
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactCompiler: true,
  allowedDevOrigins: ['mbc-sw.iptime.org'],  // 이거 추가
  experimental: {
    proxyTimeout: 120000,
  },
  async rewrites() {
  return [
    {
      source: "/api/admin/notifications/stream",
      destination: "http://192.168.0.243:5000/api/admin/notifications/stream",
    },
    {
      source: "/api/:path*",
      destination: "http://192.168.0.243:5000/api/:path*",
    },
    {
      source: "/ai/:path*",
      destination: "http://192.168.0.241:8000/ai/:path*",
    },
    {
      source: "/ai-static/:path*",
      destination: "http://192.168.0.241:8000/static/:path*",
    },
  ];
},
};

export default nextConfig;