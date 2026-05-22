'use client'

import { useState } from 'react'
import styles from './ChatBot.module.css'

type Message = {
  id: number
  sender: 'bot' | 'user'
  text: string
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
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: 'bot',
      text: '안녕하세요. WeatherAI 상담 챗봇입니다. 궁금한 내용을 선택하거나 직접 입력해주세요.',
    },
  ])

  const getBotAnswer = (question: string) => {
    if (question.includes('AI') || question.includes('탐지')) {
      return 'WeatherAI는 CCTV 영상을 기반으로 위험물질 차량을 탐지하고, 악천후 상황에서 사고 위험이 높다고 판단되면 관제센터에 알림을 전달하는 시스템입니다.'
    }

    if (question.includes('위험물질') || question.includes('차량')) {
      return '위험물질 차량은 탱크로리, 화학물질 운반차량, 대형 화물차 등 사고 발생 시 피해가 커질 수 있는 차량을 의미합니다.'
    }

    if (question.includes('관제') || question.includes('알림')) {
      return '관제센터 알림은 위험물질 차량이 감지되고, 동시에 비·눈·흐림 등 위험 기상 조건이 확인될 때 발생하도록 설계할 수 있습니다.'
    }

    if (question.includes('악천후') || question.includes('날씨')) {
      return '악천후는 비, 눈, 흐림, 시야 저하 등 도로 주행 위험을 높이는 기상 조건을 기준으로 판단합니다.'
    }

    return '현재는 기본 안내 챗봇입니다. 추후 백엔드 API와 연결하면 실제 사용자 질문에 맞는 답변을 DB나 AI 서버에서 받아올 수 있습니다.'
  }

  const sendMessage = (text?: string) => {
    const value = text ?? input.trim()
    if (!value) return

    const userMessage: Message = {
      id: Date.now(),
      sender: 'user',
      text: value,
    }

    const botMessage: Message = {
      id: Date.now() + 1,
      sender: 'bot',
      text: getBotAnswer(value),
    }

    setMessages(prev => [...prev, userMessage, botMessage])
    setInput('')
  }

  return (
    <>
      {!open && (
        <button className={styles.floatingButton} onClick={() => setOpen(true)}>
          <span className={styles.buttonIcon}>💬</span>
          <span className={styles.buttonText}>AI 상담</span>
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

                <div
                  className={`${styles.messageBubble} ${
                    message.sender === 'user' ? styles.userBubble : styles.botBubble
                  }`}
                >
                  {message.text}
                </div>
              </div>
            ))}
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
              onKeyDown={e => {
                if (e.key === 'Enter') sendMessage()
              }}
              placeholder="궁금한 내용을 입력하세요"
              className={styles.input}
            />
            <button className={styles.sendButton} onClick={() => sendMessage()}>
              전송
            </button>
          </div>
        </div>
      )}
    </>
  )
}