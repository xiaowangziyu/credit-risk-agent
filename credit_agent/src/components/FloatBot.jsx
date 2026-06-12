import { useApp } from '../context/AppContext'

export default function FloatBot() {
  const { toggleChat } = useApp()
  
  return (
    <div className="float-bot" onClick={toggleChat}>
      <svg viewBox="0 0 64 72" width="56" height="64" fill="none" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="botHead" x1="32" y1="2" x2="32" y2="38" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#a9c6ff" />
            <stop offset="35%" stopColor="#6d90ff" />
            <stop offset="80%" stopColor="#3a5cd6" />
            <stop offset="100%" stopColor="#1f3bb0" />
          </linearGradient>
          <linearGradient id="botBody" x1="32" y1="38" x2="32" y2="70" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#3a5cd6" />
            <stop offset="100%" stopColor="#1f3bb0" />
          </linearGradient>
        </defs>
        {/* 耳朵 */}
        <circle cx="8" cy="24" r="5" fill="#3a5cd6" />
        <circle cx="56" cy="24" r="5" fill="#3a5cd6" />
        <circle cx="8" cy="24" r="2.5" fill="#a9c6ff" />
        <circle cx="56" cy="24" r="2.5" fill="#a9c6ff" />
        {/* 头 */}
        <rect x="12" y="4" width="40" height="38" rx="14" fill="url(#botHead)" />
        {/* 脸 */}
        <rect x="20" y="14" width="24" height="22" rx="8" fill="#ffffff" />
        {/* 眼睛 */}
        <ellipse cx="27" cy="25" rx="2.2" ry="3.2" fill="#2a3db0" />
        <ellipse cx="37" cy="25" rx="2.2" ry="3.2" fill="#2a3db0" />
        {/* 腮红 */}
        <circle cx="24" cy="30.5" r="1.8" fill="#ff9fb0" opacity="0.6" />
        <circle cx="40" cy="30.5" r="1.8" fill="#ff9fb0" opacity="0.6" />
        {/* 微笑 */}
        <path d="M28 32 Q32 35.5 36 32" stroke="#2a3db0" strokeWidth="1.8" strokeLinecap="round" fill="none" />
        {/* 身体 */}
        <rect x="18" y="42" width="28" height="26" rx="12" fill="url(#botBody)" />
        {/* 胸牌 */}
        <rect x="26" y="50" width="12" height="10" rx="3" fill="#ffffff" />
        <text x="32" y="57" textAnchor="middle" fill="#3a5cd6" fontSize="8" fontWeight="700">控</text>
      </svg>
    </div>
  )
}
