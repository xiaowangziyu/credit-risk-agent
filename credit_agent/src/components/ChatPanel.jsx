// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
import { useState, useRef, useEffect } from 'react'
import { useApp } from '../context/AppContext'

export default function ChatPanel() {
  const { chatMessages, sendMessage, currentCompany, runAIFengKong, applicationStatus, confirmGenerateApplication, skipGenerateApplication } = useApp()
  const [input, setInput] = useState('')
  const [showDebug, setShowDebug] = useState(false)
  const chatBodyRef = useRef(null)

  useEffect(() => {
    if (chatBodyRef.current) {
      chatBodyRef.current.scrollTop = chatBodyRef.current.scrollHeight
    }
  }, [chatMessages])

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input)
      setInput('')
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  const handleQuickAction = (action) => {
    switch (action) {
      case 'risk':
        runAIFengKong(currentCompany)
        break
      case 'details':
        sendMessage('请查看扣分详情')
        break
      case 'credit':
        sendMessage('请重新测算额度')
        break
      case 'admission':
        sendMessage('请查看准入明细')
        break
      case 'opinion':
        sendMessage('请生成风控意见')
        break
      default:
        break
    }
  }

  const debugCount = chatMessages.filter(m => m.isDebug).length

  // 获取步骤状态图标
  const getStepIcon = (status) => {
    switch (status) {
      case 'done':
        return <span className="step-dot done">✓</span>
      case 'doing':
        return <span className="step-dot doing">◉</span>
      default:
        return <span className="step-dot pending">○</span>
    }
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="chat-title">AI 小控</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span
            className="status-dot"
            title="AI 小控运行中"
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#22c55e',
              display: 'inline-block',
              boxShadow: '0 0 0 3px rgba(34, 197, 94, 0.2)',
              animation: 'pulse 2s ease-in-out infinite'
            }}
          />
          <div className="chat-sub">正在协助完成尽调</div>
        </div>
      </div>

      <div className="chat-body" ref={chatBodyRef}>
        {chatMessages.map((msg, index) => {
          // DEBUG消息默认隐藏
          if (msg.isDebug) {
            if (!showDebug) return null
            return (
              <div key={index} className="msg ai">
                <div className="bubble" style={{
                  background: '#f8fafc',
                  border: '1px dashed #cbd5e1',
                  fontSize: 12,
                  color: '#64748b',
                  fontStyle: 'italic'
                }}>
                  🐞 [DEBUG] {msg.text}
                </div>
                <div className="msg-time">{msg.time}</div>
              </div>
            )
          }

          // 思考消息 - 特殊样式
          if (msg.thinking) {
            return (
              <div key={index} className="thinking-item">
                <div className="thinking-step">
                  <div className="step-node">
                    {getStepIcon(msg.status)}
                    {index < chatMessages.length - 1 && (
                      chatMessages[index + 1]?.thinking && (
                        <div className="step-line" />
                      )
                    )}
                  </div>
                  <div className="step-content">
                    <div className="step-title">
                      <span className="step-num">{msg.step}.</span>
                      <span className="step-text">{msg.text}</span>
                    </div>
                    {/* 思考详情 */}
                    {msg.detail && (
                      <div className="thinking-detail">
                        <div className="detail-label">思考过程</div>
                        <div className="detail-content">{msg.detail}</div>
                        {msg.action && (
                          <div className="detail-action">正在{msg.action}...</div>
                        )}
                      </div>
                    )}
                    {/* 没有详情但有action */}
                    {!msg.detail && msg.action && (
                      <div className="thinking-detail">
                        <div className="detail-action">正在{msg.action}...</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          }

          // 普通消息
          return (
            <div key={index} className={`msg ${msg.role}`}>
              <div className="bubble">{msg.text}</div>
              <div className="msg-time">{msg.time}</div>
            </div>
          )
        })}
      </div>

      <div className="chat-bottom">
        <div className="quick-row">
          <button className="quick-btn" onClick={() => handleQuickAction('risk')}>
            一键风控「{currentCompany}」
          </button>
          <button className="quick-btn" onClick={() => handleQuickAction('details')}>
            查看扣分详情
          </button>
          <button className="quick-btn" onClick={() => handleQuickAction('credit')}>
            重新测算额度
          </button>
          {/* 生成/跳过按钮：仅在待确认生成授信申请单时显示 */}
          {applicationStatus === 'pending' && (
            <>
              <button className="quick-btn" onClick={confirmGenerateApplication}>
                生成
              </button>
              <button className="quick-btn" onClick={skipGenerateApplication}>
                跳过
              </button>
            </>
          )}
          {debugCount > 0 && (
            <button
              className="quick-btn"
              onClick={() => setShowDebug(v => !v)}
              style={{
                background: showDebug ? '#22c55e' : '#e2e8f0',
                color: showDebug ? '#fff' : '#475569'
              }}
              title="显示或隐藏调试消息"
            >
              {showDebug ? '隐藏调试' : `显示调试(${debugCount})`}
            </button>
          )}
        </div>

        <div className="chat-input-row">
          <input
            type="text"
            className="chat-input"
            placeholder="输入指令，如：把额度调整为500万..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button className="btn btn-primary" onClick={handleSend}>
            发送
          </button>
        </div>
      </div>
    </div>
  )
}
