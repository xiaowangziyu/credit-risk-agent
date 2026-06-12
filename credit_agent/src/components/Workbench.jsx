// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
import { useApp } from '../context/AppContext'
import CompanyInfo from './CompanyInfo'
import ScoreCard from './ScoreCard'
import RiskOpinion from './RiskOpinion'
import CreditApplication from './CreditApplication'

export default function Workbench() {
  const {
    currentCompany,
    setCurrentCompany,
    suggestions,
    runAIFengKong,
    companyInfo,
    scoreResult,
    creditSuggestion,
    isRejected,
    applicationStatus,
    openModal
  } = useApp()

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      runAIFengKong(currentCompany)
    }
  }

  return (
    <div id="tab-workbench">
      {/* 企业名称输入区 */}
      <div className="card">
        <div className="card-head">
          <div className="card-title">企业名称</div>
        </div>
        <div className="search-section">
          <div className="search-row">
            <input
              type="text"
              className="search-input"
              value={currentCompany}
              placeholder="输入企业名称发起风控尽调"
              onChange={(e) => setCurrentCompany(e.target.value)}
              onKeyDown={handleKeyDown}
              list="company-suggestions"
            />
            <datalist id="company-suggestions">
              {suggestions.map(name => (
                <option key={name} value={name} />
              ))}
            </datalist>
            <button className="btn btn-primary btn-wide" onClick={() => runAIFengKong(currentCompany)}>
              AI 风控
            </button>
            <button className="btn btn-outline btn-white btn-wide" onClick={() => openModal('edit', companyInfo)}>发起授信</button>
          </div>
        </div>
      </div>

      {/* 企业基础信息卡片：企业信息数据到达时显示 */}
      {companyInfo && <CompanyInfo />}

      {/* 风控评分卡：评分结果数据到达时才显示（评分完后才出现） */}
      {!isRejected && scoreResult && <ScoreCard />}

      {/* 授信风控建议：授信建议数据到达时才显示（AI 给出建议后才出现） */}
      {!isRejected && creditSuggestion && <RiskOpinion />}

      {/* 授信申请单：用户确认生成后才显示 */}
      {applicationStatus === 'confirmed' && <CreditApplication />}
    </div>
  )
}
