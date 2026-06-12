import { useApp } from '../context/AppContext'

// 从区间值中提取"建议默认值"（取区间下限
function parseRangeCredit(value) {
  if (!value) return 300
  if (typeof value === 'number') return value
  const s = String(value)
  const parts = s.split('-').map(p => parseInt(p.trim(), 10)).filter(n => !isNaN(n))
  if (parts.length === 0) return 300
  if (parts.length === 1) return parts[0]
  return Math.min(...parts)
}

// 从区间值中提取期限（取数值部分
function parseTerm(value) {
  if (!value) return 12
  if (typeof value === 'number') return value
  const s = String(value)
  const m = s.match(/\d+/)
  return m ? parseInt(m[0], 10) : 12
}

export default function CreditApplication() {
  const { companyInfo, creditSuggestion, openModal } = useApp()

  if (!companyInfo) return null

  // 需求6：申请金额的优先级：用户编辑过的 applicationAmount > 建议额度下限
  // 建议值从独立的 creditSuggestion 读取（不随 companyInfo 变化而变化
  const creditType = companyInfo.creditType || '流动资金授信'
  const defaultSuggestedCredit = creditSuggestion
    ? parseRangeCredit(creditSuggestion.suggestedCredit)
    : parseRangeCredit(companyInfo.suggestedCredit)
  const defaultSuggestedTerm = creditSuggestion
    ? parseTerm(creditSuggestion.suggestedTerm)
    : parseTerm(companyInfo.suggestedTerm)

  // 用户编辑后，申请金额取用户填过的值（如果有）
  const applicationAmount = companyInfo.applicationAmount || defaultSuggestedCredit
  const applicationTerm = companyInfo.applicationTerm || defaultSuggestedTerm
  const fundsUsage = companyInfo.fundsUsage || '日常经营周转'

  return (
    <div className="card">
      <div className="card-head">
        <div className="card-title">授信申请单</div>
        <div className="card-sub">
          <span style={{ color: 'var(--primary)', fontWeight: 500, background: 'var(--primary-light)', padding: '4px 12px', borderRadius: 100, fontSize: 12 }}>
            {companyInfo.status || '草稿'}
          </span>
        </div>
      </div>

      <div className="info-grid info-grid-left">
        <div className="info-row">
          <span className="k">申请企业</span>
          <span className="v">{companyInfo.companyName}</span>
        </div>
        <div className="info-row">
          <span className="k">统一社会信用代码</span>
          <span className="v">{companyInfo.unifiedCode}</span>
        </div>
        <div className="info-row">
          <span className="k">授信类型</span>
          <span className="v">{creditType}</span>
        </div>
        <div className="info-row">
          <span className="k">申请金额（万元）</span>
          <span className="v" style={{ color: 'var(--primary)', fontWeight: 600 }}>
            {applicationAmount}
          </span>
        </div>
        <div className="info-row">
          <span className="k">申请期限（月）</span>
          <span className="v">{applicationTerm}</span>
        </div>
        <div className="info-row">
          <span className="k">资金用途</span>
          <span className="v">{fundsUsage}</span>
        </div>
      </div>

      <div className="action-row">
        <button className="btn btn-outline btn-white" onClick={() => openModal('edit', companyInfo)}>
          编辑
        </button>
        <button className="btn btn-primary" onClick={() => openModal('submit', companyInfo)}>
          提交审批
        </button>
      </div>
    </div>
  )
}
