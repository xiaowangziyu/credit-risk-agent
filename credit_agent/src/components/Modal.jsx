import { useState, useEffect } from 'react'
import { useApp } from '../context/AppContext'

export default function Modal() {
  const { modal, closeModal, submitToApproval, recallCredit, setActiveTab, updateCompanyInfo } = useApp()
  const [formData, setFormData] = useState({
    creditType: '流动资金授信',
    amount: 300,
    term: 12,
    fundsUsage: '日常经营周转'
  })
  const [warning, setWarning] = useState('')
  
  // 获取建议授信区间
  const getCreditRange = () => {
    const range = modal.data?.suggestedCredit?.split('-') || ['200', '350']
    return {
      min: parseInt(range[0]) || 200,
      max: parseInt(range[1]) || 350,
      original: modal.data?.suggestedCredit || '200-350'
    }
  }

  // 校验金额是否在建议区间内
  const validateAmount = (amount) => {
    const { min, max, original } = getCreditRange()
    const num = parseInt(amount)
    if (isNaN(num)) return ''
    
    if (num > max) {
      return `⚠️ 您输入的申请额度（${num}万元）超出建议授信上限（${max}万元）。超出建议额度可能触发更严格的审批流程，请确认是否继续提交。`
    }
    if (num < min) {
      return `⚠️ 您输入的申请额度（${num}万元）低于建议授信下限（${min}万元）。授信额度可能不足以满足业务需求，请确认是否继续提交。`
    }
    return ''
  }

  // 实时校验金额变化
  const handleAmountChange = (value) => {
    const num = parseInt(value)
    setFormData({ ...formData, amount: num })
    setWarning(validateAmount(num))
  }
  
  useEffect(() => {
    if (modal.type === 'submit' && modal.data) {
      const defaultAmount = parseInt(modal.data.suggestedCredit?.split('-')[0] || '300')
      setFormData({
        creditType: modal.data.creditType || '流动资金授信',
        amount: defaultAmount,
        term: parseInt(modal.data.suggestedTerm || '12'),
        fundsUsage: modal.data.fundsUsage || '日常经营周转'
      })
      setWarning('')
    } else if (modal.type === 'edit' && modal.data) {
      const defaultAmount = modal.data.applicationAmount || parseInt(modal.data.suggestedCredit?.split('-')[0] || '300')
      setFormData({
        creditType: modal.data.creditType || '流动资金授信',
        amount: defaultAmount,
        term: parseInt(modal.data.suggestedTerm || '12'),
        fundsUsage: modal.data.fundsUsage || '日常经营周转'
      })
      setWarning(validateAmount(defaultAmount))
    }
  }, [modal])
  
  if (!modal.type) return null
  
  const handleSubmit = () => {
    // 检查超限
    const warnings = []
    const { min, max } = getCreditRange()
    
    if (formData.amount > max) {
      warnings.push(`${formData.amount} 万元超出建议授信上限，可能触发更严格的审批流程。`)
    }
    if (formData.amount < min) {
      warnings.push(`${formData.amount} 万元低于建议授信下限，授信额度可能不足以满足业务需求。`)
    }
    if (formData.term > 24) {
      warnings.push('建议授信期限为 12-24 个月，超出此期限可能影响审批通过率。')
    }
    
    if (warnings.length > 0) {
      setWarning(warnings.join('<br>'))
      return
    }
    
    if (modal.data) {
      submitToApproval(modal.data.companyName)
      closeModal()
      setActiveTab('credit')
    }
  }
  
  const handleEditConfirm = () => {
    // 更新企业信息（注意：申请金额/期限写到 applicationAmount/applicationTerm，不修改 AI 建议的 suggestedCredit/suggestedTerm）
    const updatedInfo = {
      ...modal.data,
      creditType: formData.creditType,
      applicationAmount: formData.amount,
      applicationTerm: formData.term,
      fundsUsage: formData.fundsUsage
    }

    // 通过上下文更新企业信息
    if (modal.data && modal.data.companyName) {
      updateCompanyInfo(updatedInfo)
    }

    closeModal()
  }
  
  const handleRecall = () => {
    if (modal.data) {
      recallCredit(modal.data.companyName)
    }
  }
  
  // 提交审批弹窗
  if (modal.type === 'submit') {
    return (
      <div className="modal-mask" onClick={closeModal}>
        <div className="modal-card" onClick={(e) => e.stopPropagation()}>
          <div className="modal-title">授信申请信息确认</div>
          
          {/* 只有当有警告时才显示警告框 */}
          {warning && (
            <div className="modal-warning show" dangerouslySetInnerHTML={{ __html: warning }} />
          )}
          
          <div className="modal-field">
            <label>授信类型</label>
            <select
              value={formData.creditType}
              onChange={(e) => setFormData({ ...formData, creditType: e.target.value })}
            >
              <option value="流动资金授信">流动资金授信</option>
              <option value="固定资产授信">固定资产授信</option>
              <option value="仓单质押授信">仓单质押授信</option>
              <option value="应收账款保理授信">应收账款保理授信</option>
              <option value="投标保函授信">投标保函授信</option>
              <option value="纯信用授信">纯信用授信</option>
            </select>
          </div>
          
          <div className="modal-field">
            <label>申请金额（万元）</label>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => handleAmountChange(e.target.value)}
              />
              <span style={{ fontSize: 12, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                建议区间：{getCreditRange().original}
              </span>
            </div>
          </div>
          
          <div className="modal-field">
            <label>申请期限（月）</label>
            <input
              type="number"
              value={formData.term}
              onChange={(e) => setFormData({ ...formData, term: e.target.value })}
            />
          </div>
          
          <div className="modal-field">
            <label>资金用途</label>
            <select
              value={formData.fundsUsage}
              onChange={(e) => setFormData({ ...formData, fundsUsage: e.target.value })}
            >
              <option value="日常经营周转">日常经营周转</option>
              <option value="货物采购备货">货物采购备货</option>
              <option value="物流运费支付">物流运费支付</option>
              <option value="设备购置更新">设备购置更新</option>
              <option value="项目履约垫资">项目履约垫资</option>
            </select>
          </div>
          
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={closeModal}>取消</button>
            <button className="btn btn-primary" onClick={handleSubmit}>提交</button>
          </div>
        </div>
      </div>
    )
  }
  
  // 编辑弹窗
  if (modal.type === 'edit') {
    return (
      <div className="modal-mask" onClick={closeModal}>
        <div className="modal-card" onClick={(e) => e.stopPropagation()}>
          <div className="modal-title">编辑授信申请信息</div>
          
          {/* 只有当有警告时才显示警告框 */}
          {warning && (
            <div className="modal-warning show" dangerouslySetInnerHTML={{ __html: warning }} />
          )}
          
          <div className="modal-field">
            <label>授信类型</label>
            <select
              value={formData.creditType}
              onChange={(e) => setFormData({ ...formData, creditType: e.target.value })}
            >
              <option value="流动资金授信">流动资金授信</option>
              <option value="固定资产授信">固定资产授信</option>
              <option value="仓单质押授信">仓单质押授信</option>
              <option value="应收账款保理授信">应收账款保理授信</option>
              <option value="投标保函授信">投标保函授信</option>
              <option value="纯信用授信">纯信用授信</option>
            </select>
          </div>
          
          <div className="modal-field">
            <label>申请金额（万元）</label>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <input
                type="number"
                value={formData.amount}
                onChange={(e) => handleAmountChange(e.target.value)}
              />
              <span style={{ fontSize: 12, color: '#94a3b8', whiteSpace: 'nowrap' }}>
                建议区间：{getCreditRange().original}
              </span>
            </div>
          </div>
          
          <div className="modal-field">
            <label>申请期限（月）</label>
            <input
              type="number"
              value={formData.term}
              onChange={(e) => setFormData({ ...formData, term: e.target.value })}
            />
          </div>
          
          <div className="modal-field">
            <label>资金用途</label>
            <select
              value={formData.fundsUsage}
              onChange={(e) => setFormData({ ...formData, fundsUsage: e.target.value })}
            >
              <option value="日常经营周转">日常经营周转</option>
              <option value="货物采购备货">货物采购备货</option>
              <option value="物流运费支付">物流运费支付</option>
              <option value="设备购置更新">设备购置更新</option>
              <option value="项目履约垫资">项目履约垫资</option>
            </select>
          </div>
          
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={closeModal}>取消</button>
            <button className="btn btn-outline" onClick={handleEditConfirm}>确认</button>
          </div>
        </div>
      </div>
    )
  }

  // 撤回确认弹窗
  if (modal.type === 'recall') {
    return (
      <div className="modal-mask" onClick={closeModal}>
        <div className="modal-card small" onClick={(e) => e.stopPropagation()}>
          <div className="modal-title">撤回提示</div>
          <div className="confirm-text">确定要撤回该授信单吗？</div>
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={closeModal}>取消</button>
            <button className="btn btn-primary" onClick={handleRecall}>确认</button>
          </div>
        </div>
      </div>
    )
  }

  // 查看风控报告——弹窗内卡片式自适应布局，无滚动条
  if (modal.type === 'report') {
    const data = modal.data || {}
    const extractNum = (val) => {
      if (val === null || val === undefined) return '-'
      if (typeof val === 'number') return val
      const s = String(val)
      const m = s.match(/\d+/)
      return m ? m[0] : val || '-'
    }
    const totalScore = data.total_score ?? data.score ?? 0
    const riskLevel = data.risk_level ?? data.riskLevel ?? '低风险'

    // 维度颜色对：进度条用稀释色，分数数字用原色
    const dimPairs = [
      { fill: '#FFD6E8', text: '#E91E63' },
      { fill: '#FFE0C2', text: '#FF6F00' },
      { fill: '#FFF5BF', text: '#C79100' },
      { fill: '#D6F5E5', text: '#2E7D32' },
      { fill: '#D6E8FF', text: '#1565C0' },
      { fill: '#E0D6F5', text: '#512DA8' },
      { fill: '#FFD6D6', text: '#C62828' },
      { fill: '#D6E8F5', text: '#0277BD' }
    ]

    // 维度数据：优先从 data 取，否则用默认
    let dimensions = []
    if (Array.isArray(data.dimensions) && data.dimensions.length > 0) {
      dimensions = data.dimensions
    } else {
      dimensions = [
        { name: '企业基本资质', score: 20, maxScore: 20 },
        { name: '经营稳定性', score: 23, maxScore: 25 },
        { name: '财务健康度', score: 18, maxScore: 25 },
        { name: '行业与市场地位', score: 12, maxScore: 15 },
        { name: '信用记录与合规性', score: 18, maxScore: 20 }
      ]
    }

    const riskTagClass = String(riskLevel).includes('高')
      ? 'tag-danger'
      : String(riskLevel).includes('中')
      ? 'tag-warn'
      : 'tag-ok'

    return (
      <div className="modal-mask" onClick={closeModal}>
        <div className="modal-card large" onClick={(e) => e.stopPropagation()}>
          <div className="modal-title">{data.companyName || '企业'} · 风控报告</div>

          <div className="report-body">
            {/* 上半部：企业基础信息 + 综合评分 */}
            <div className="report-card" style={{ flex: '0 0 auto' }}>
              <div className="report-card-title">企业基础信息</div>
              <div className="report-grid">
                <div className="report-row">
                  <span className="k">统一社会信用代码</span>
                  <span className="v">{data.unifiedCode || '-'}</span>
                </div>
                <div className="report-row">
                  <span className="k">法定代表人</span>
                  <span className="v">{data.legalPerson || data.legal_representative || '-'}</span>
                </div>
                <div className="report-row">
                  <span className="k">成立时间</span>
                  <span className="v">{data.establishDate || data.establishment_date || '-'}</span>
                </div>
                <div className="report-row">
                  <span className="k">参保人数</span>
                  <span className="v">{extractNum(data.insuranceCount || data.employee_count_num)}</span>
                </div>
                <div className="report-row">
                  <span className="k">经营地址</span>
                  <span className="v">{data.address || '-'}</span>
                </div>
                <div className="report-row">
                  <span className="k">所属行业</span>
                  <span className="v">{data.industry || '-'}</span>
                </div>
              </div>

              {/* 综合评分摘要 —— 与企业信息在同一个卡片中 */}
              <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px dashed var(--border)' }}>
                <div className="report-summary">
                  <div className="report-score">
                    <span className="report-score-value">{totalScore}</span>
                    <span className="report-score-label">综合评分 · 满分 100</span>
                  </div>
                  <span className={`tag ${riskTagClass}`}>{riskLevel}</span>
                </div>
              </div>
            </div>

            {/* 下半部：风控评分卡 —— 维度进度条，占剩余空间 */}
            <div className="report-card" style={{ flex: '1 1 auto', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
              <div className="report-card-title">风控评分卡</div>
              <div className="report-dimensions" style={{ flex: '1 1 auto', overflow: 'hidden' }}>
                {dimensions.map((d, idx) => {
                  const pair = dimPairs[idx % dimPairs.length]
                  const score = Number(d.score) || 0
                  const max = Number(d.maxScore) || d.full_score || 100
                  const pct = max > 0 ? Math.min(100, Math.round((score / max) * 100)) : 0
                  return (
                    <div key={idx} className="report-dim-row">
                      <span className="report-dim-label">{d.name || `维度${idx + 1}`}</span>
                      <div className="report-dim-bar">
                        <div className="report-dim-fill" style={{ width: `${pct}%`, background: pair.fill }} />
                      </div>
                      <span className="report-dim-score" style={{ color: pair.text }}>
                        {score.toFixed ? score.toFixed(1) : score}
                      </span>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>

          {/* 风控意见卡片 */}
          <div className="report-card" style={{ flex: '0 0 auto', marginTop: 12 }}>
            <div className="report-card-title">风控意见</div>
            <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.7, padding: '4px 0' }}>
              {data.riskOpinion || data.opinion || `该企业综合评分为${totalScore}分，风险等级为${riskLevel}。建议授信额度${data.suggestedCredit || '300-500'}万元，授信期限${data.suggestedTerm || '12'}个月。`}
            </div>
          </div>

          <div className="report-actions">
            <button className="btn btn-primary" onClick={closeModal}>关闭</button>
          </div>
        </div>
      </div>
    )
  }

  // 需求5（新）：审批进度——竖向进度条
  if (modal.type === 'approval') {
    const companyName = (modal.data && modal.data.companyName) || '企业'
    const steps = [
      { label: '发起授信', time: '2024-06-10 09:15', opinion: '已提交', state: 'done' },
      { label: '风控主管审批', time: '2024-06-10 10:30', opinion: '通过 · 企业经营状况良好，风险可控', state: 'done' },
      { label: '业务经理审批', time: '2024-06-10 14:20', opinion: '通过 · 授信方案合理，期限适度', state: 'done' },
      { label: '风控总监审批', time: '2024-06-11 09:50', opinion: '通过 · 额度在风险阈值内，原则同意', state: 'doing' },
      { label: '总经理审批', time: '待定', opinion: '待审批', state: 'pending' }
    ]

    return (
      <div className="modal-mask" onClick={closeModal}>
        <div className="modal-card large" onClick={(e) => e.stopPropagation()}>
          <div className="modal-title">{companyName} · 审批进度</div>

          <div className="approval-flow">
            {steps.map((s, idx) => (
              <div key={idx} className={`approval-step ${s.state}`}>
                <div className="approval-node">
                  <div className="approval-dot">
                    {s.state === 'done' ? '✓' : s.state === 'doing' ? '…' : ''}
                  </div>
                  {idx < steps.length - 1 && <div className="approval-line" />}
                </div>
                <div className="approval-content">
                  <div className="approval-label">{s.label}</div>
                  <div className="approval-time">{s.time}</div>
                  <div className="approval-opinion">{s.opinion}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="modal-actions">
            <button className="btn btn-primary" onClick={closeModal}>关闭</button>
          </div>
        </div>
      </div>
    )
  }

  return null
}
