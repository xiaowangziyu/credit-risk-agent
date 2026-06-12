// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
import { useApp } from '../context/AppContext'

// 需求3：维度颜色映射（饱和度已降低的稀释色）
// 对应的未稀释色（原色）用于分数数字显示
const DIMENSION_PAIRS = [
  { fill: '#FFD6E8', text: '#E91E63' },   // 粉色组
  { fill: '#FFE0C2', text: '#FF6F00' },   // 橙色组
  { fill: '#FFF5BF', text: '#C79100' },   // 黄色组
  { fill: '#D6F5E5', text: '#2E7D32' },   // 绿色组
  { fill: '#D6E8FF', text: '#1565C0' },   // 蓝色组
  { fill: '#E0D6F5', text: '#512DA8' },   // 紫色组
  { fill: '#FFD6D6', text: '#C62828' },   // 红色组
  { fill: '#D6E8F5', text: '#0277BD' }    // 天蓝色组
]

// 兼容：仍然保留 DIMENSION_COLORS 供可能引用它的其他代码
const DIMENSION_COLORS = DIMENSION_PAIRS.map(p => p.fill)

export default function ScoreCard() {
  const { companyInfo, scoreResult } = useApp()

  // 必须同时有企业信息和评分结果才渲染评分卡（没有评分数据时不渲染，也不使用默认数据）
  if (!companyInfo || !scoreResult) return null

  // 解析后端返回的评分卡数据
  let dimensions = []
  if (scoreResult?.dimensions && Array.isArray(scoreResult.dimensions)) {
    dimensions = scoreResult.dimensions.map((d, idx) => {
      const pair = DIMENSION_PAIRS[idx % DIMENSION_PAIRS.length]
      return {
        name: d.name || `维度${idx + 1}`,
        score: Number(d.score) || 0,
        maxScore: Number(d.full_score) || 100,
        reason: d.reason || '',
        fillColor: pair.fill,
        textColor: pair.text
      }
    })
  } else if (scoreResult?.breakdown && typeof scoreResult.breakdown === 'object') {
    dimensions = Object.entries(scoreResult.breakdown).map(([name, score], idx) => {
      const pair = DIMENSION_PAIRS[idx % DIMENSION_PAIRS.length]
      return {
        name,
        score: Number(score) || 0,
        maxScore: 100,
        reason: '',
        fillColor: pair.fill,
        textColor: pair.text
      }
    })
  }

  // 没有真实维度数据时不渲染
  if (dimensions.length === 0) return null

  const totalScore = scoreResult?.total_score || 0
  const riskLevel = scoreResult?.risk_level || '未知'

  // 计算总分（从维度累加）
  const calcTotal = dimensions.reduce((sum, d) => sum + d.score, 0)
  const displayTotal = scoreResult?.total_score || (calcTotal > 0 ? Math.round(calcTotal * 10) / 10 : 0)

  // 获取风险标签颜色
  const getRiskColor = (level) => {
    if (level?.includes('高')) return 'tag-danger'
    if (level?.includes('中')) return 'tag-warn'
    return 'tag-ok'
  }

  return (
    <div className="card">
      <div className="card-head">
        <div className="card-title">风控评分卡</div>
      </div>

      <div className="score-dimensions score-dimensions-tall">
        {dimensions.map((dim, idx) => {
          const score = Number(dim.score) || 0
          const maxScore = Number(dim.maxScore) || 100
          const fillPercent = maxScore > 0 ? (score / maxScore) * 100 : 0

          return (
            <div key={`${dim.name}-${idx}`} className="dimension-row dimension-row-tall">
              <span className="dimension-label dimension-label-wide">
                {dim.name}
                <span className="dimension-weight">({maxScore}分)</span>
              </span>
              <div className="dimension-bar dimension-bar-thick">
                <div
                  className="dimension-fill"
                  style={{
                    width: `${fillPercent}%`,
                    background: dim.fillColor
                  }}
                />
              </div>
              {/* 需求3：分数数字用未稀释的原色 */}
              <span className="dimension-score" style={{ color: dim.textColor, fontWeight: 600 }}>{score.toFixed(1)}</span>
            </div>
          )
        })}
      </div>

      <div className="score-summary">
        <div>
          <span className="total-score">{displayTotal}</span>
          <span className="total-label">综合评分 · 满分100</span>
        </div>
        <span className={`tag ${getRiskColor(riskLevel)} scorecard-risk-tag`}>{riskLevel}</span>
      </div>
    </div>
  )
}
