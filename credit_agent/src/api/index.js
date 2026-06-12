// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
// 注意：API_BASE 使用相对路径（/api/*），由 Vite 代理到后端 localhost:8001
// 对应后端路由见：my-second-agent/main.py

const API_BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!res.ok) {
    let detail = `请求失败: ${res.status}`
    try {
      const err = await res.json()
      if (err && err.detail) detail = err.detail
    } catch (_) {}
    throw new Error(detail)
  }
  return res.json()
}

// ====== 企业相关 ======

// 获取本地可查询的企业列表（建议列表）
// 后端: GET /api/companies/local
// 返回: { companies: ["公司A", "公司B", ...] }
export async function getLocalCompanies() {
  return request('/companies/local', { method: 'GET' })
}

// 快速查询企业基本信息（单步，非流式）
// 后端: GET /api/companies/search/{company_name}
export async function searchCompany(companyName) {
  const encoded = encodeURIComponent(companyName)
  return request(`/companies/search/${encoded}`, { method: 'GET' })
}

// ====== Agent 智能风控分析（核心）======

// 对企业执行完整的风控尽调分析。
// 后端: POST /api/agent/analyze
// 请求体: { company_name: string, session_id?: string }
// 返回: Server-Sent Events (text/event-stream) 流式响应
// 每个事件都是一个 JSON 对象，格式示例：
//   { type: "step", content: "正在调用 search_company" }
//   { type: "info", content: "工商信息采集完成（12 维度）" }
//   { type: "tool_result", tool: "search_company", data: {...} }
//   { type: "final", data: { score, risk_level, suggestions, ... } }
//
// 用法示例（在组件里）：
//   const response = await analyzeCompany('浙商中拓集团股份有限公司')
//   const reader = response.body.getReader()
//   ... // 按字节块读取，解析 "data: {...}\n\n" 格式
export async function analyzeCompany(companyName) {
  const res = await fetch(`${API_BASE}/agent/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company_name: companyName })
  })
  if (!res.ok) {
    let detail = `请求失败: ${res.status}`
    try {
      const err = await res.json()
      if (err && err.detail) detail = err.detail
    } catch (_) {}
    throw new Error(detail)
  }
  return res
}

// ====== 授信申请相关 ======

// 列出所有授信申请
// 后端: GET /api/applications
export async function getApplications() {
  return request('/applications', { method: 'GET' })
}

// 按企业名称获取授信申请详情
// 后端: GET /api/applications/{enterprise_name}
export async function getApplication(enterpriseName) {
  const encoded = encodeURIComponent(enterpriseName)
  return request(`/applications/${encoded}`, { method: 'GET' })
}

// 更新授信申请字段（可部分更新）
// 后端: PUT /api/applications/{application_id}
// 请求体字段: credit_type, application_amount, application_period,
//             fund_purpose, status （全部可选）
export async function updateApplication(applicationId, patch) {
  return request(`/applications/${applicationId}`, {
    method: 'PUT',
    body: JSON.stringify(patch || {})
  })
}

// 提交授信申请（状态变更为 "审批中"）
// 后端: POST /api/applications/{application_id}/submit
export async function submitApplication(applicationId) {
  return request(`/applications/${applicationId}/submit`, {
    method: 'POST',
    body: JSON.stringify({})
  })
}

// 撤回授信申请（状态变更为 "draft"）
// 后端: POST /api/applications/{application_id}/withdraw
export async function withdrawApplication(applicationId) {
  return request(`/applications/${applicationId}/withdraw`, {
    method: 'POST',
    body: JSON.stringify({})
  })
}
