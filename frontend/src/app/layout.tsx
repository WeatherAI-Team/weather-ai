import type { Metadata } from 'next'
import './globals.css'
import Header from '@/components/layout/Header'
import Footer from '@/components/layout/Footer'
import Providers from '@/components/Providers'

export const metadata: Metadata = {
  title: {
    template: 'Weather AI - %s',
    default: 'Weather AI — 악천후 위험물질 차량 탐지 시스템',
  },
  description: '악천후 상황 시 위험 물질 차량을 AI로 탐지하여 사고를 예방합니다',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <Providers>
          <Header />
          <main style={{ paddingTop: 'var(--header-h)', width: '100%', overflowX: 'hidden' }}>
            {children}
          </main>
          <Footer />
        </Providers>
      </body>
    </html>
  )
}