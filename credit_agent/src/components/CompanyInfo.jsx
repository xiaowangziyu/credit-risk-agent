import { useApp } from '../context/AppContext'

// 空值占位符
const PLACEHOLDER = '-'

// 格式化显示值：空值/0显示为"-"
const formatValue = (value) => {
  if (value === null || value === undefined || value === '' || value === 0) {
    return PLACEHOLDER
  }
  return value
}

// 需求2：从任意值中提取数字（处理 "128个"、"员工128人"、"128"等情形）
function extractNumber(value) {
  if (value === null || value === undefined) return null
  if (typeof value === 'number') return value
  const s = String(value)
  const m = s.match(/\d+/)
  if (m) return parseInt(m[0], 10)
  return null
}

export default function CompanyInfo() {
  const { companyInfo, isRejected } = useApp()

  if (!companyInfo) return null

  const insuranceNum = extractNumber(companyInfo.insuranceCount)
  const hasInsurance = insuranceNum && insuranceNum > 0

  return (
    <div className="card">
      <div className="card-head">
        <div className="card-title">企业基础信息</div>
        <div className="card-sub" style={{ fontSize: 12, color: '#94a3b8', background: '#f1f5f9', padding: '4px 10px', borderRadius: 100 }}>
          模拟数据
        </div>
        {isRejected && (
          <div className="tag tag-danger">准入不通过</div>
        )}
      </div>
      <div className="info-grid">
        <div className="info-row">
          <span className="k">企业名称</span>
          <span className="v">{formatValue(companyInfo.companyName)}</span>
        </div>
        <div className="info-row">
          <span className="k">统一社会信用代码</span>
          <span className="v">{formatValue(companyInfo.unifiedCode)}</span>
        </div>
        <div className="info-row">
          <span className="k">工商类型</span>
          <span className="v">{formatValue(companyInfo.companyType)}</span>
        </div>
        <div className="info-row">
          <span className="k">法定代表人</span>
          <span className="v">{formatValue(companyInfo.legalPerson)}</span>
        </div>
        <div className="info-row">
          <span className="k">成立日期</span>
          <span className="v">{formatValue(companyInfo.establishDate)}</span>
        </div>
        <div className="info-row">
          <span className="k">注册资本（万元）</span>
          <span className="v">{formatValue(companyInfo.registeredCapital).toLocaleString ? formatValue(companyInfo.registeredCapital).toLocaleString() : formatValue(companyInfo.registeredCapital)}</span>
        </div>
        <div className="info-row">
          <span className="k">实缴资本（万元）</span>
          <span className="v">{formatValue(companyInfo.paidCapital).toLocaleString ? formatValue(companyInfo.paidCapital).toLocaleString() : formatValue(companyInfo.paidCapital)}</span>
        </div>
        <div className="info-row">
          <span className="k">经营状态</span>
          <span className="v">
            <span className="tag tag-ok company-info-tag">{formatValue(companyInfo.operationStatus)}</span>
          </span>
        </div>
        <div className="info-row">
          <span className="k">参保人数</span>
          <span className="v">{hasInsurance ? insuranceNum : PLACEHOLDER}</span>
        </div>
        <div className="info-row">
          <span className="k">所属行业</span>
          <span className="v">{formatValue(companyInfo.industry)}</span>
        </div>
        <div className="info-row">
          <span className="k">注册地址</span>
          <span className="v">{formatValue(companyInfo.address)}</span>
        </div>
        <div className="info-row">
          <span className="k">年营收（万元）</span>
          <span className="v">{companyInfo.revenue ? companyInfo.revenue.toLocaleString() : PLACEHOLDER}</span>
        </div>
      </div>
    </div>
  )
}
