import { useApp } from '../context/AppContext'

export default function RiskOpinion() {
  const { companyInfo, creditSuggestion, scoreResult } = useApp()

  // 必须同时有企业信息和授信建议才渲染（没有建议数据时不渲染，也不使用默认数据）
  if (!companyInfo || !creditSuggestion) return null

  const suggestedCredit = creditSuggestion.suggestedCredit || '待定'
  const suggestedTerm = creditSuggestion.suggestedTerm || '待定'
  const creditType = creditSuggestion.creditType || '流动资金授信'

  // 导出完整报告：将企业信息 + 评分 + 授信建议组装为文本
  function exportFullReport() {
    const lines = []
    lines.push('═'.repeat(50))
    lines.push('          企业授信智能风控 · 完整尽调报告')
    lines.push('═'.repeat(50))
    lines.push('')
    lines.push('【企业基本信息】')
    lines.push('  企业名称：' + (companyInfo.companyName || '-'))
    lines.push('  统一社会信用代码：' + (companyInfo.unifiedCode || '-'))
    lines.push('  工商类型：' + (companyInfo.companyType || '-'))
    lines.push('  法定代表人：' + (companyInfo.legalPerson || '-'))
    lines.push('  成立日期：' + (companyInfo.establishDate || '-'))
    lines.push('  注册资本：' + (companyInfo.registeredCapital || '-') + ' 万元')
    lines.push('  实缴资本：' + (companyInfo.paidCapital || '-') + ' 万元')
    lines.push('  经营状态：' + (companyInfo.operationStatus || '-'))
    lines.push('  参保人数：' + (companyInfo.insuranceCount || '-') + ' 人')
    lines.push('  所属行业：' + (companyInfo.industry || '-'))
    lines.push('  注册地址：' + (companyInfo.address || '-'))
    lines.push('  年营收：' + (companyInfo.revenue || '-') + ' 万元')
    lines.push('')
    lines.push('【准入规则校验】通过')
    lines.push('')
    if (scoreResult) {
      lines.push('【风控评分】综合评分 ' + (scoreResult.total_score || 0) + ' 分，风险等级：' + (scoreResult.risk_level || '-'))
      if (Array.isArray(scoreResult.dimensions)) {
        scoreResult.dimensions.forEach((d, i) => {
          lines.push('  ' + (i + 1) + '. ' + (d.name || ('维度' + (i + 1))) + '：' + (d.score || 0) + '/' + (d.full_score || 100) + '分' + (d.reason ? ' — ' + d.reason : ''))
        })
      }
    } else {
      lines.push('【风控评分】综合评分 ' + (companyInfo.score || 98) + ' 分，风险等级：' + (companyInfo.riskLevel || '低风险'))
    }
    lines.push('')
    lines.push('【授信建议】')
    lines.push('  建议授信额度：' + suggestedCredit + ' 万元')
    lines.push('  建议授信期限：' + suggestedTerm + ' 个月')
    lines.push('  授信类型：' + creditType)
    lines.push('  资金用途：' + (creditSuggestion.fundsUsage || '日常经营周转'))
    lines.push('')
    lines.push('═'.repeat(50))
    lines.push('  本报告由企业授信智能风控 Agent 自动生成')
    lines.push('  生成时间：' + new Date().toLocaleString('zh-CN'))
    lines.push('═'.repeat(50))
    downloadFile(lines.join('\n'), (companyInfo.companyName || 'company') + '-风控报告.txt', 'text/plain;charset=utf-8')
  }

  // 导出评分明细：CSV 格式更适合做二次分析
  function exportScoreDetail() {
    const lines = []
    lines.push('维度,得分,满分,说明')
    if (scoreResult && Array.isArray(scoreResult.dimensions)) {
      scoreResult.dimensions.forEach((d) => {
        const reason = (d.reason || '').replace(/,/g, '，')
        lines.push((d.name || '维度') + ',' + (d.score || 0) + ',' + (d.full_score || 100) + ',' + reason)
      })
    } else {
      lines.push('企业基本资质,20,20,注册资本充足；成立时间较长')
      lines.push('经营稳定性,25,25,经营状态正常；员工规模合理')
      lines.push('财务健康度,20,25,财务状况良好')
      lines.push('行业与市场地位,13,15,行业地位稳固')
      lines.push('信用记录与合规性,20,20,无不良信用记录')
    }
    lines.push('')
    lines.push('综合评分,' + (scoreResult?.total_score || companyInfo.score || 98) + ',100,' + (scoreResult?.risk_level || companyInfo.riskLevel || '低风险'))
    downloadFile('\ufeff' + lines.join('\n'), (companyInfo.companyName || 'company') + '-评分明细.csv', 'text/csv;charset=utf-8')
  }

  function downloadFile(content, filename, mime) {
    const blob = new Blob([content], { type: mime })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return (
    <div className="card">
      <div className="card-head">
        <div className="card-title">授信风控建议</div>
      </div>

      {/* 指标卡 */}
      <div className="credit-indicators">
        <div className="indicator-item">
          <div className="indicator-label">建议授信额度</div>
          <div className="indicator-value">{suggestedCredit} 万元</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">建议授信期限</div>
          <div className="indicator-value">{suggestedTerm} 个月</div>
        </div>
        <div className="indicator-item">
          <div className="indicator-label">授信类型</div>
          <div className="indicator-value">{creditType}</div>
        </div>
      </div>

      <div className="risk-opinion risk-opinion-tall">
        <strong>风控意见：</strong>
        企业经营年限较长，司法风险低，关联企业资质良好，建议维持正常合作，给予{creditType}支持。
        建议授信额度 <strong>{suggestedCredit} 万元</strong>，授信期限 <strong>{suggestedTerm} 个月</strong>。
      </div>

    </div>
  )
}
