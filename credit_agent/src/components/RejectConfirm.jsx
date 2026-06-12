import { useApp } from '../context/AppContext'

export default function RejectConfirm() {
  const { rejectConfirm, confirmReject, ignoreReject, closeRejectConfirm } = useApp()

  if (!rejectConfirm.show) return null

  const { violations = [], reasons = [], company = '' } = rejectConfirm

  return (
    <div className="modal-mask" onClick={closeRejectConfirm}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-title reject-title">
          <span className="reject-icon">⚠️</span>
          流程确认
        </div>
        <div className="modal-sub reject-sub">小控建议禁止该企业准入，请您确认</div>

        <div className="reject-company-name">
          企业：<span className="company-name-highlight">{company}</span>
        </div>

        <div className="reject-section">
          <div className="reject-section-title">检测到以下违规项：</div>
          {violations.length > 0 ? (
            <ul className="reject-violations">
              {violations.map((v, i) => (
                <li key={i} className="reject-violation-item">
                  <span className="violation-index">{i + 1}</span>
                  <span className="violation-text">{v}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="reject-empty">未获取到具体违规项</div>
          )}
        </div>

        {reasons.length > 0 && (
          <div className="reject-section">
            <div className="reject-section-title">禁入原因：</div>
            <div className="reject-reasons">
              {reasons.map((r, i) => (
                <div key={i} className="reject-reason-item">• {r}</div>
              ))}
            </div>
          </div>
        )}

        <div className="reject-tip">
          <span className="tip-icon">💡</span>
          <span>您可以选择确认禁入（流程终止），或忽略该建议继续分析，但请谨慎决策</span>
        </div>

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={ignoreReject}>
            忽略，继续分析
          </button>
          <button className="btn btn-danger" onClick={confirmReject}>
            确认禁入
          </button>
        </div>
      </div>
    </div>
  )
}
