import { useApp } from '../context/AppContext'

export default function CreditList() {
  const { companies, openModal } = useApp()
  
  const getStatusStyle = (status) => {
    switch (status) {
      case '草稿': return { background: 'var(--primary-light)', color: 'var(--primary)' }
      case '审批中': return { background: '#dbe4ff', color: '#5273e0' }
      case '已生效': return { background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)' }
      case '已拒绝': return { background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)' }
      default: return { background: 'var(--primary-light)', color: 'var(--primary)' }
    }
  }
  
  return (
    <div id="tab-credit">
      {/* 授信申请列表头部 */}
      <div className="card credit-list-head">
        <div className="card-head credit-list-head-inner">
          <div className="card-title">授信申请列表</div>
          <div className="card-sub credit-list-count">共 {companies.length} 条记录</div>
        </div>
      </div>
      
      {/* 企业列表 */}
      {companies.map((company, index) => (
        <div key={index} className="card">
          <div className="draft-head">
            <div className="draft-left">
              <div className="draft-dot"></div>
              <div className="draft-title">{company.companyName}</div>
            </div>
            <span className="draft-badge" style={getStatusStyle(company.status)}>
              {company.status}
            </span>
          </div>
          
          <div className="info-grid">
            <div className="info-row">
              <span className="k">授信类型</span>
              <span className="v">{company.creditType}</span>
            </div>
            <div className="info-row">
              <span className="k">申请金额（万元）</span>
              <span className="v" style={{ color: 'var(--primary)', fontWeight: 600 }}>
                {company.suggestedCredit?.split('-')[0] || '300'}
              </span>
            </div>
            <div className="info-row">
              <span className="k">申请期限（月）</span>
              <span className="v">{company.suggestedTerm}</span>
            </div>
            <div className="info-row">
              <span className="k">资金用途</span>
              <span className="v">{company.fundsUsage}</span>
            </div>
            <div className="info-row">
              <span className="k">综合评分</span>
              <span className="v" style={{ color: 'var(--primary)', fontWeight: 600 }}>{company.score} 分</span>
            </div>
            <div className="info-row">
              <span className="k">风险等级</span>
              <span className="v">
                <span className={`tag ${company.riskLevel.includes('高') ? 'tag-danger' : company.riskLevel.includes('中') ? 'tag-warn' : 'tag-ok'}`}>
                  {company.riskLevel}
                </span>
              </span>
            </div>
          </div>
          
          <div className="action-row">
            {company.status === '草稿' && (
              <>
                <button className="btn btn-outline btn-white" onClick={() => openModal('edit', company)}>
                  编辑
                </button>
                <button className="btn btn-primary" onClick={() => openModal('submit', company)}>
                  提交审批
                </button>
              </>
            )}
            {company.status === '审批中' && (
              <>
                <button className="btn btn-ghost" onClick={() => openModal('approval', company)}>查看审批进度</button>
                <button className="btn btn-outline btn-white" onClick={() => openModal('recall', company)}>
                  撤回
                </button>
              </>
            )}
            {company.status === '已生效' && (
              <button className="btn btn-ghost" onClick={() => openModal('report', company)}>查看风控报告</button>
            )}
            {company.status === '已拒绝' && (
              <button className="btn btn-ghost" onClick={() => openModal('report', company)}>查看风控报告</button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
