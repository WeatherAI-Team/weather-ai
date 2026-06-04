'use client'

import { useState, useRef, useEffect } from 'react'
import styles from './ChatBot.module.css'

const API = process.env.NEXT_PUBLIC_API_URL ?? ''

type Message = {
  id: number
  sender: 'bot' | 'user'
  text: string
  suggestions?: string[]
}

function formatBotText(text: string) {
  return text.split('\n').flatMap((line, li, lineArr) => {
    const parts = line.split(/(?<!\d)\. /)
    const nodes = parts.flatMap((part, i) =>
      i < parts.length - 1
        ? [part + '.', <br key={`s${li}-${i}`} />]
        : [part]
    )
    return li < lineArr.length - 1 ? [...nodes, <br key={`n${li}`} />] : nodes
  })
}

const quickQuestions = [
  'AI 탐지는 어떻게 작동하나요?',
  '위험물질 차량은 어떤 차량인가요?',
  '관제센터 알림 기준이 궁금해요',
  '악천후 상황은 어떻게 판단하나요?',
]

export default function ChatBot() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: 'bot',
      text: '안녕하세요. WeatherAI 상담 챗봇입니다. 궁금한 내용을 선택하거나 직접 입력해주세요.',
    },
  ])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = async (text?: string) => {
    const value = text ?? input.trim()
    if (!value || loading) return

    const userMessage: Message = { id: Date.now(), sender: 'user', text: value }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API}/api/chatbot/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: value }),
      })
      const json = await res.json()

      const answer: string = json.data?.answer ?? json.message ?? '답변을 가져오지 못했습니다.'
      const suggestions: string[] | undefined = json.data?.data?.suggestions

      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, sender: 'bot', text: answer, suggestions },
      ])
    } catch {
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, sender: 'bot', text: '서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      {!open && (
        <button className={styles.floatingButton} onClick={() => setOpen(true)}>
          <span className={styles.buttonIcon}>🤖</span>
          <span className={styles.buttonText}>AI 챗봇</span>
        </button>
      )}

      {open && (
        <div className={styles.chatBox}>
          <div className={styles.header}>
            <div>
              <p className={styles.headerLabel}>WeatherAI</p>
              <h3 className={styles.headerTitle}>AI 상담 챗봇</h3>
            </div>
            <button className={styles.closeBtn} onClick={() => setOpen(false)}>
              ✕
            </button>
          </div>

          <div className={styles.notice}>
            <span>안내</span>
            악천후 위험 차량 탐지 시스템에 대해 빠르게 안내해드려요.
          </div>

          <div className={styles.messages}>
            {messages.map(message => (
              <div
                key={message.id}
                className={`${styles.messageRow} ${
                  message.sender === 'user' ? styles.userRow : styles.botRow
                }`}
              >
                {message.sender === 'bot' && (
                  <div className={styles.botAvatar}>AI</div>
                )}

                <div className={styles.botColumn}>
                  <div
                    className={`${styles.messageBubble} ${
                      message.sender === 'user' ? styles.userBubble : styles.botBubble
                    }`}
                  >
                    {message.sender === 'bot' ? formatBotText(message.text) : message.text}
                  </div>
                  {message.suggestions && (
                    <div className={styles.suggestions}>
                      {message.suggestions.map(s => (
                        <button key={s} className={styles.suggestionBtn} onClick={() => sendMessage(s)}>
                          {s}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className={`${styles.messageRow} ${styles.botRow}`}>
                <div className={styles.botAvatar}>AI</div>
                <div className={`${styles.messageBubble} ${styles.botBubble} ${styles.typingBubble}`}>
                  <span className={styles.dot} /><span className={styles.dot} /><span className={styles.dot} />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className={styles.quickArea}>
            {quickQuestions.map(q => (
              <button
                key={q}
                className={styles.quickButton}
                onClick={() => sendMessage(q)}
              >
                {q}
              </button>
            ))}
          </div>

          <div className={styles.inputArea}>
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') sendMessage() }}
              placeholder="궁금한 내용을 입력하세요"
              className={styles.input}
              disabled={loading}
            />
            <button className={styles.sendButton} onClick={() => sendMessage()} disabled={loading}>
              {loading ? '...' : '전송'}
            </button>
          </div>
        </div>
      )}
    </>
  )
}