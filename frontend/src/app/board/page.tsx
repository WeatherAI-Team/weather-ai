import Link from 'next/link'
import styles from './page.module.css'

const posts = [
  { id: 1, category: '공지', title: '시스템 정기 점검 안내 (5월 1일)', author: '관리자', date: '2026-04-25', views: 312, isPinned: true },
  { id: 2, category: '사례', title: '[사례] 경부고속도로 폭우 상황 탱크로리 탐지 성공 보고', author: '홍길동', date: '2026-04-24', views: 589 },
  { id: 3, category: '분석', title: '눈보라 조건에서 YOLOv8 모델 성능 분석 리포트', author: '김분석', date: '2026-04-22', views: 441 },
  { id: 4, category: '사례', title: '[사례] 중부내륙고속도로 안개 구간 LPG 차량 감지', author: '이탐지', date: '2026-04-20', views: 378 },
  { id: 5, category: '질문', title: 'FastAPI와 Flask 간 통신 지연 문제 해결 방법 공유', author: '박개발', date: '2026-04-18', views: 215 },
  { id: 6, category: '분석', title: '야간 폭우 환경에서의 탐지율 향상 실험', author: '최연구', date: '2026-04-16', views: 302 },
]

const categoryColors: Record<string, string> = {
  '공지': 'categoryNotice',
  '사례': 'categoryCase',
  '분석': 'categoryAnalysis',
  '질문': 'categoryQuestion',
}

export default function BoardPage() {
  return (
    <div style={{ width: '100%', overflowX: 'hidden' }}>
      <section style={{ width: '100%', padding: '30px 0 40px', background: 'linear-gradient(160deg, #e8f6ff, #ffffff)', borderBottom: '1px solid rgba(7,85,157,0.12)' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
          <p style={{ fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.15em', textTransform: 'uppercase', color: '#1b9bd1', marginBottom: '12px' }}>게시판</p>
          <h1 style={{ fontFamily: 'Exo 2, sans-serif', fontSize: '2.5rem', fontWeight: 700, color: '#20436d', marginBottom: '16px' }}>커뮤니티 & 공지</h1>
          <p style={{ fontSize: '1rem', color: '#5a85a8' }}>탐지 결과 공유, 사례 분석, 공지사항을 확인하세요</p>
        </div>
      </section>

      <section style={{ padding: '30px 0' }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' as const }}>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' as const }}>
              {['전체', '공지', '사례', '분석', '질문'].map(c => (
                <button key={c} style={{ padding: '7px 16px', borderRadius: '999px', fontSize: '0.82rem', fontWeight: 600, color: c === '전체' ? 'white' : '#5a85a8', background: c === '전체' ? '#07559d' : '#f0f8ff', border: '1.5px solid ' + (c === '전체' ? '#07559d' : 'rgba(7,85,157,0.12)'), cursor: 'pointer' }}>{c}</button>
              ))}
            </div>
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <input type="text" placeholder="검색..." style={{ padding: '9px 16px', border: '1.5px solid rgba(7,85,157,0.12)', borderRadius: '10px', fontSize: '0.85rem', outline: 'none', width: '200px' }} />
              <button style={{ padding: '9px 18px', background: 'linear-gradient(135deg, #07559d, #1b9bd1)', color: 'white', borderRadius: '10px', fontWeight: 600, fontSize: '0.85rem', cursor: 'pointer', border: 'none' }}>✏️ 글쓰기</button>
            </div>
          </div>

          <div style={{ background: 'white', borderRadius: '16px', border: '1.5px solid rgba(7,85,157,0.12)', overflow: 'hidden' }}>
            {posts.map(post => (
              <Link key={post.id} href={`/board/${post.id}`} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 90px 100px 70px', gap: '16px', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid rgba(7,85,157,0.12)', textDecoration: 'none', background: post.isPinned ? '#fffde8' : 'transparent' }}>
                <span style={{ padding: '3px 10px', borderRadius: '999px', fontSize: '0.72rem', fontWeight: 700, textAlign: 'center' as const, background: post.category === '공지' ? '#e8f0ff' : post.category === '사례' ? '#e8fff0' : post.category === '분석' ? '#fff3e8' : '#f8e8ff', color: post.category === '공지' ? '#3b5bdb' : post.category === '사례' ? '#2b8a3e' : post.category === '분석' ? '#d9480f' : '#7c3aed' }}>{post.category}</span>
                <span style={{ fontSize: '0.9rem', color: '#20436d', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {post.isPinned && <span>📌</span>}
                  {post.title}
                </span>
                <span style={{ fontSize: '0.82rem', color: '#5a85a8', textAlign: 'center' as const }}>{post.author}</span>
                <span style={{ fontSize: '0.8rem', color: '#5a85a8', textAlign: 'center' as const }}>{post.date}</span>
                <span style={{ fontSize: '0.8rem', color: '#5a85a8', textAlign: 'right' as const }}>👁 {post.views}</span>
              </Link>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '32px' }}>
            {[1,2,3,4,5].map(n => (
              <button key={n} style={{ width: '36px', height: '36px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, color: n === 1 ? 'white' : '#5a85a8', background: n === 1 ? '#07559d' : 'white', border: '1.5px solid ' + (n === 1 ? '#07559d' : 'rgba(7,85,157,0.12)'), cursor: 'pointer' }}>{n}</button>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}