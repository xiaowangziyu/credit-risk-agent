import { useApp } from '../context/AppContext'

export default function Header() {
  const { activeTab, setActiveTab } = useApp()
  const today = new Date()
  const dateStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
  
  return (
    <div className="header">
      <div className="header-brand">
        <div className="header-icon" style={{ transform: 'translateY(2px)' }}>
          <svg viewBox="0 0 40 44" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="headG" x1="20" y1="2" x2="20" y2="34" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#a9c6ff" />
                <stop offset="35%" stopColor="#6d90ff" />
                <stop offset="80%" stopColor="#3a5cd6" />
                <stop offset="100%" stopColor="#1f3bb0" />
              </linearGradient>
            </defs>
            {/* 耳朵 */}
            <circle cx="3" cy="22" r="3.5" fill="#3a5cd6" />
            <circle cx="37" cy="22" r="3.5" fill="#3a5cd6" />
            <circle cx="3" cy="22" r="1.8" fill="#a9c6ff" />
            <circle cx="37" cy="22" r="1.8" fill="#a9c6ff" />
            {/* 头 */}
            <rect x="6" y="4" width="28" height="28" rx="10" fill="url(#headG)" />
            {/* 脸 */}
            <rect x="11" y="10" width="18" height="15" rx="5" fill="#ffffff" />
            {/* 眼睛 */}
            <ellipse cx="16" cy="17.5" rx="1.6" ry="2.4" fill="#2a3db0" />
            <ellipse cx="24" cy="17.5" rx="1.6" ry="2.4" fill="#2a3db0" />
            {/* 腮红 */}
            <circle cx="14" cy="21.5" r="1.4" fill="#ff9fb0" opacity="0.6" />
            <circle cx="26" cy="21.5" r="1.4" fill="#ff9fb0" opacity="0.6" />
            {/* 微笑 */}
            <path d="M17 22 Q20 24.5 23 22" stroke="#2a3db0" strokeWidth="1.2" strokeLinecap="round" fill="none" />
          </svg>
        </div>
        <span>企业授信智能风控助手Agent</span>
      </div>
      <div className="header-tabs">
        <button 
          className={`tab-btn ${activeTab === 'workbench' ? 'active' : ''}`}
          onClick={() => setActiveTab('workbench')}
        >
          风控工作台
        </button>
        <button 
          className={`tab-btn ${activeTab === 'credit' ? 'active' : ''}`}
          onClick={() => setActiveTab('credit')}
        >
          客户授信
        </button>
      </div>
      <div className="header-right">
        <span>{dateStr}</span>
        <div className="avatar">A</div>
      </div>
    </div>
  )
}
