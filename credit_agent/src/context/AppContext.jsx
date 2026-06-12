// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/
// API 调用通过 Vite 代理走 /api/* -> 后端 localhost:8001，不手写绝对地址
import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import * as api from '../api'

const AppContext = createContext(null)

// 模拟的企业数据（用于前端演示，实际会通过API获取）
const MOCK_COMPANIES = {
  '深圳市智联科技有限公司': {
    companyName: '深圳市智联科技有限公司',
    companyType: '有限责任公司',
    unifiedCode: '91440300MA5XXXXXXX',
    legalPerson: '张三',
    establishDate: '2015-03-20',
    registeredCapital: 5000,
    paidCapital: 3000,
    operationStatus: '存续',
    industry: '科技服务业',
    insuranceCount: 128,
    revenue: 8500,
    address: '深圳市南山区科技园南区',
    score: 98,
    riskLevel: '低风险',
    status: '草稿',
    suggestedCredit: '300-500',
    suggestedTerm: '12',
    creditType: '流动资金授信',
    fundsUsage: '日常经营周转'
  },
  '广州华南制造有限公司': {
    companyName: '广州华南制造有限公司',
    companyType: '有限责任公司',
    unifiedCode: '91440100MA5YYYYYY',
    legalPerson: '李四',
    establishDate: '2012-08-15',
    registeredCapital: 8000,
    paidCapital: 6000,
    operationStatus: '存续',
    industry: '先进制造业',
    insuranceCount: 256,
    revenue: 12000,
    address: '广州市黄埔区开发区',
    score: 88,
    riskLevel: '低风险',
    status: '审批中',
    suggestedCredit: '800-1200',
    suggestedTerm: '36',
    creditType: '固定资产授信',
    fundsUsage: '设备购置更新'
  },
  '深圳蓝天物流股份有限公司': {
    companyName: '深圳蓝天物流股份有限公司',
    companyType: '股份有限公司',
    unifiedCode: '91440300MA5ZZZZZZ',
    legalPerson: '王五',
    establishDate: '2008-11-30',
    registeredCapital: 10000,
    paidCapital: 10000,
    operationStatus: '存续',
    industry: '现代物流',
    insuranceCount: 189,
    revenue: 15000,
    address: '深圳市宝安区物流园',
    score: 85,
    riskLevel: '低风险',
    status: '已生效',
    suggestedCredit: '500-800',
    suggestedTerm: '24',
    creditType: '流动资金授信',
    fundsUsage: '货物采购备货'
  },
  '东莞绿源能源科技有限公司': {
    companyName: '东莞绿源能源科技有限公司',
    companyType: '有限责任公司',
    unifiedCode: '91441900MA5AAAAAA',
    legalPerson: '赵六',
    establishDate: '2018-05-20',
    registeredCapital: 3000,
    paidCapital: 2000,
    operationStatus: '存续',
    industry: '绿色低碳产业',
    insuranceCount: 67,
    revenue: 4500,
    address: '东莞市松山湖高新区',
    score: 78,
    riskLevel: '低风险',
    status: '草稿',
    suggestedCredit: '200-350',
    suggestedTerm: '12',
    creditType: '流动资金授信',
    fundsUsage: '货物采购备货'
  },
  '北京中关村软件园科技': {
    companyName: '北京中关村软件园科技',
    companyType: '有限责任公司',
    unifiedCode: '91110108MA5BBBBBB',
    legalPerson: '孙七',
    establishDate: '2010-01-10',
    registeredCapital: 6000,
    paidCapital: 4500,
    operationStatus: '存续',
    industry: '科技服务业',
    insuranceCount: 145,
    revenue: 9200,
    address: '北京市海淀区中关村',
    score: 82,
    riskLevel: '低风险',
    status: '审批中',
    suggestedCredit: '400-600',
    suggestedTerm: '18',
    creditType: '流动资金授信',
    fundsUsage: '日常经营周转'
  },
  '上海自贸区供应链管理': {
    companyName: '上海自贸区供应链管理',
    companyType: '有限责任公司',
    unifiedCode: '91310115MA5CCCCCC',
    legalPerson: '周八',
    establishDate: '2014-07-01',
    registeredCapital: 12000,
    paidCapital: 8000,
    operationStatus: '存续',
    industry: '现代物流',
    insuranceCount: 210,
    revenue: 18000,
    address: '上海市浦东新区自贸区',
    score: 80,
    riskLevel: '低风险',
    status: '草稿',
    suggestedCredit: '500-700',
    suggestedTerm: '24',
    creditType: '流动资金授信',
    fundsUsage: '项目履约垫资'
  }
}

export function AppProvider({ children }) {
  // 当前激活的页面
  const [activeTab, setActiveTab] = useState('workbench')

  // 聊天窗口是否打开
  const [chatOpen, setChatOpen] = useState(true)

  // 当前企业名称
  const [currentCompany, setCurrentCompany] = useState('深圳市智联科技有限公司')

  // 当前企业的完整信息（工商、参保等基础数据，初始为空，分析完成后填充）
  const [companyInfo, setCompanyInfo] = useState(null)

  // ⭐ 建议授信信息（AI风控完成后生成，业务操作不改变这一状态）
  // 注意：这是 AI 分析的建议值，与用户在授信申请单中的申请金额分离
  const [creditSuggestion, setCreditSuggestion] = useState(null)

  // 当前企业是否被准入不通过（禁入）
  const [isRejected, setIsRejected] = useState(false)

  // 授信申请单显示时机：'hidden'（未分析）| 'pending'（待确认生成）| 'confirmed'（已确认生成）
  const [applicationStatus, setApplicationStatus] = useState('hidden')

  // 待生成的授信申请单数据（在 pending 状态下暂存）
  const [pendingApplicationData, setPendingApplicationData] = useState(null)

  // 所有企业列表（客户授信页用）
  const [companies, setCompanies] = useState(Object.values(MOCK_COMPANIES))

  // 企业选择提示列表（从后端动态加载）
  const [suggestions, setSuggestions] = useState(Object.keys(MOCK_COMPANIES))

  // 组件挂载时从后端加载企业建议列表（可用企业）
  useEffect(() => {
    async function loadSuggestions() {
      try {
        const res = await api.getLocalCompanies()
        if (res && Array.isArray(res.companies) && res.companies.length > 0) {
          setSuggestions(res.companies)
        }
      } catch (err) {
        // 后端不可用时，保持默认 mock 数据，不报错
        console.info('[AppContext] 加载企业列表失败，使用默认数据:', err.message)
      }
    }
    loadSuggestions()
  }, [])
  
  // 评分结果
  const [scoreResult, setScoreResult] = useState(null)

  // 规则校验结果
  const [ruleResult, setRuleResult] = useState(null)

  // 禁入确认弹窗（LLM建议禁入后，等待用户确认）
  const [rejectConfirm, setRejectConfirm] = useState({ show: false, violations: [], reasons: [], company: null })
  
  // 加载状态
  const [loading, setLoading] = useState(false)
  
  // 弹窗状态
  const [modal, setModal] = useState({ type: null, data: null })
  
  // Toast消息
  const [toast, setToast] = useState({ show: false, message: '' })
  
  // 执行模式追踪（供前端显示：是LLM驱动还是降级）
  const [executionMode, setExecutionMode] = useState({
    mode: 'idle',  // 'idle' | 'llm' | 'fallback' | 'fallback_complete' | 'frontend_fallback'
    reason: null,
    llmCalls: 0,
    toolCalls: 0
  })

  // 聊天消息
  const [chatMessages, setChatMessages] = useState([
    { role: 'ai', text: '欢迎使用企业授信智能风控助手Agent，请输入企业名称后点击AI风控，或使用下方快捷按钮开始尽调。', time: getCurrentTime() }
  ])
  
  // 显示Toast
  const showToast = useCallback((message) => {
    setToast({ show: true, message })
    setTimeout(() => setToast({ show: false, message: '' }), 2500)
  }, [])
  
  // 打开弹窗
  const openModal = useCallback((type, data) => {
    setModal({ type, data })
  }, [])
  
  // 关闭弹窗
  const closeModal = useCallback(() => {
    setModal({ type: null, data: null })
  }, [])
  
  // 切换聊天窗口
  const toggleChat = useCallback(() => {
    setChatOpen(prev => !prev)
  }, [])
  
  // 执行AI风控（调用后端SSE流）
  const runAIFengKong = useCallback(async (companyName) => {
    const name = companyName || currentCompany
    if (!name.trim()) {
      showToast('请先输入企业！')
      return
    }

    setCurrentCompany(name)
    setLoading(true)
    // 开始新分析：清空所有卡片数据（逐个出现的新交互）
    setCompanyInfo(null)
    setScoreResult(null)
    setCreditSuggestion(null)
    setRuleResult(null)
    setIsRejected(false)
    setApplicationStatus('hidden')
    setPendingApplicationData(null)

    // 需求12：在聊天窗口先显示用户消息：一键风控「{企业名称}」
    setChatMessages(prev => [...prev, {
      role: 'me',
      text: `一键风控「${name}」`,
      time: getCurrentTime()
    }])

    // 显示AI等待中
    setChatMessages(prev => [...prev, {
      role: 'ai',
      text: `正在对企业「${name}」进行智能风控尽调，请稍候…`,
      time: getCurrentTime()
    }])

    try {
      // 调用后端 SSE 接口（通过 api/index.js，走 Vite 代理到 8001）
      setExecutionMode({ mode: 'llm', reason: null, llmCalls: 0, toolCalls: 0 })
      const response = await api.analyzeCompany(name)
      
      if (!response.ok) {
        throw new Error('请求失败')
      }
      
      // 处理SSE流
      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const text = decoder.decode(value, { stream: true })
        const lines = text.split('\n\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              await handleSSEData(data)
            } catch (e) {
              console.error('解析SSE数据失败:', e)
            }
          }
        }
      }
      
      setLoading(false)
      showToast('风控尽调完成')
    } catch (error) {
      console.error('风控分析失败:', error)
      setExecutionMode({ mode: 'frontend_fallback', reason: `API请求失败: ${error.message}`, llmCalls: 0, toolCalls: 0 })
      setChatMessages(prev => [...prev, {
        role: 'ai',
        text: `[DEBUG] ⚠️ [前端降级] 后端API不可用(${error.message})，已切换到前端模拟数据模式`,
        time: getCurrentTime()
      }])
      setChatMessages(prev => [...prev, {
        role: 'ai',
        text: `风控分析失败: ${error.message}，已切换到离线模式`,
        time: getCurrentTime()
      }])
      
      // 降级到模拟模式
      fallbackAnalysis(name)
      setLoading(false)
    }
  }, [showToast])
  
  // 处理SSE数据
  const handleSSEData = async (data) => {
    const { type, content, step, data: payload, result, _execution_mode, _fallback_reason, _llm_calls_total, _tool_calls_total, _llm_content_preview, _llm_tool_calls, _llm_config, _context_state } = data

    // 更新执行模式追踪
    if (_execution_mode) {
      setExecutionMode(prev => ({
        mode: _execution_mode || prev.mode,
        reason: _fallback_reason || prev.reason,
        llmCalls: _llm_calls_total != null ? _llm_calls_total : prev.llmCalls,
        toolCalls: _tool_calls_total != null ? _tool_calls_total : prev.toolCalls
      }))
    }

    switch (type) {
      case 'start':
        // 开始分析
        break
        
      case 'thought':
        // LLM思考
        setChatMessages(prev => [...prev, {
          role: 'ai',
          text: content,
          step: step,
          thinking: true,
          status: 'doing',
          time: getCurrentTime()
        }])
        break
        
      case 'thought_detail':
        // LLM详细思考 - 作为上一个思考步骤的子内容
        setChatMessages(prev => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg && lastMsg.thinking && !lastMsg.detailAdded) {
            return [...prev.slice(0, -1), {
              ...lastMsg,
              detail: content,
              detailAdded: true
            }]
          }
          return [...prev, {
            role: 'ai',
            text: content,
            thinking: true,
            time: getCurrentTime()
          }]
        })
        break
        
      case 'action':
        // 调用工具 - 更新上一个思考步骤的状态
        setChatMessages(prev => {
          const lastMsg = prev[prev.length - 1]
          if (lastMsg && lastMsg.thinking && !lastMsg.actionAdded) {
            return [...prev.slice(0, -1), {
              ...lastMsg,
              action: data.tool,
              actionAdded: true
            }]
          }
          return [...prev, {
            role: 'ai',
            text: data.tool,
            thinking: true,
            time: getCurrentTime()
          }]
        })
        break
        
      case 'action_detail':
        // 工具调用详情
        setChatMessages(prev => [...prev, {
          role: 'ai',
          text: `📋 ${content}`,
          time: getCurrentTime()
        }])
        break
        
      case 'observation':
        // 观察结果
        const obsText = payload ? formatObservation(data.tool, payload) : content
        setChatMessages(prev => [...prev, {
          role: 'ai',
          text: `🔍 ${obsText}`,
          time: getCurrentTime()
        }])

        // 更新企业信息
        if (data.tool === 'search_company' && payload) {
          const companyData = {
            companyName: payload.name || payload.companyName || currentCompany,
            companyType: payload.company_type || '有限责任公司',
            unifiedCode: payload.unified_code || payload.creditCode || payload.credit_code || '',
            legalPerson: payload.legal_representative || payload.legalPerson || '',
            establishDate: payload.establishment_date || payload.establishDate || '',
            registeredCapital: payload.registered_capital_wan || payload.registered_capital || payload.registeredCapital || 0,
            paidCapital: payload.paid_capital || payload.paidCapital || 0,
            operationStatus: payload.business_status || payload.operationStatus || '存续',
            industry: payload.industry || '其他',
            insuranceCount: payload.employee_count_num || payload.insuranceCount || 0,
            revenue: payload.annual_revenue_wan || payload.annual_revenue || payload.revenue || 0,
            address: payload.address || '',
            dataSource: payload.data_source || '演示数据'
          }
          setCompanyInfo(companyData)
        }

        // 保存规则校验中间结果
        if (data.tool === 'check_rules' && payload) {
          setRuleResult(payload)
        }

        // 更新评分结果（支持 dimensions 数组格式）
        if (data.tool === 'create_scorecard' && payload) {
          setScoreResult({
            total_score: payload.total_score || 0,
            risk_level: payload.risk_level || '未知',
            dimensions: payload.dimensions || []
          })
        }
        break
        
      case 'final':
        // 最终结果
        if (result) {
          const { company, rule_check, scorecard, credit_suggestion, report, status } = result

          // ⭐ 先检测是否禁入企业（需求11）
          const shouldReject = status === 'rejected' || (rule_check && !rule_check.passed)

          if (shouldReject) {
            // 禁入企业：只保留企业基础信息，不生成评分卡/授信建议/申请单
            if (company) {
              const companyData = {
                companyName: company.name || company.companyName || currentCompany,
                companyType: company.company_type || company.companyType || '有限责任公司',
                unifiedCode: company.unified_code || company.creditCode || company.credit_code || '',
                legalPerson: company.legal_representative || company.legalPerson || '',
                establishDate: company.establishment_date || company.establishDate || '',
                registeredCapital: company.registered_capital_wan || company.registered_capital || company.registeredCapital || 0,
                paidCapital: company.paid_capital || company.paidCapital || 0,
                operationStatus: company.business_status || company.operationStatus || '存续',
                industry: company.industry || '其他',
                insuranceCount: company.employee_count_num || company.insuranceCount || 0,
                revenue: company.annual_revenue_wan || company.annual_revenue || company.revenue || 0,
                address: company.address || '',
                dataSource: company.data_source || '演示数据'
              }
              setCompanyInfo(companyData)
            }
            // 需求11：明确标记为禁入企业，不渲染评分卡、授信建议和申请单
            setIsRejected(true)
            setScoreResult(null)
            setCreditSuggestion(null)

            const violations = rule_check?.violations || []
            const reasons = rule_check?.reasons || []
            setRejectConfirm({
              show: true,
              violations,
              reasons,
              company: company?.name || currentCompany
            })
            setChatMessages(prev => [...prev, {
              role: 'ai',
              text: `⚠️ 准入规则校验未通过！\n${violations.map((v, i) => `${i + 1}. ${v}`).join('\n')}\n\n小控建议禁止该企业准入，请确认您的决定。`,
              time: getCurrentTime()
            }])
            return  // 等待用户确认
          }

          // 正常流程：更新企业信息 + 评分 + 授信建议
          // 更新企业信息
          if (company) {
            const companyData = {
              companyName: company.name || company.companyName || currentCompany,
              companyType: company.company_type || company.companyType || '有限责任公司',
              unifiedCode: company.unified_code || company.creditCode || company.credit_code || '',
              legalPerson: company.legal_representative || company.legalPerson || '',
              establishDate: company.establishment_date || company.establishDate || '',
              registeredCapital: company.registered_capital_wan || company.registered_capital || company.registeredCapital || 0,
              paidCapital: company.paid_capital || company.paidCapital || 0,
              operationStatus: company.business_status || company.operationStatus || '存续',
              industry: company.industry || '其他',
              insuranceCount: company.employee_count_num || company.insuranceCount || 0,
              revenue: company.annual_revenue_wan || company.annual_revenue || company.revenue || 0,
              address: company.address || '',
              dataSource: company.data_source || '演示数据'
            }
            setCompanyInfo(companyData)
          }

          // 保存规则校验结果
          if (rule_check) {
            setRuleResult(rule_check)
          }

          // 评分结果处理
          if (scorecard) {
            setScoreResult({
              total_score: scorecard.total_score || 0,
              risk_level: scorecard.risk_level || '未知',
              dimensions: scorecard.dimensions || []
            })
          }

          // ⭐ 需求6：设置独立的建议授信（与申请金额解耦）
          if (credit_suggestion) {
            const suggestedCredit = credit_suggestion.amount_range || credit_suggestion.suggested_amount || credit_suggestion.suggested_credit || '300-500'
            const suggestedTerm = credit_suggestion.suggested_period || credit_suggestion.suggested_term || '12'
            const creditType = credit_suggestion.primary_credit_type || credit_suggestion.credit_type || '流动资金授信'
            const fundsUsage = credit_suggestion.funds_usage || '日常经营周转'

            setCreditSuggestion({ suggestedCredit, suggestedTerm, creditType, fundsUsage })

            // 暂存授信申请单数据，等待用户确认后再生成
            setPendingApplicationData({
              creditType,
              suggestedCredit,
              suggestedTerm,
              fundsUsage
            })
            // 进入"待确认生成授信申请单"状态
            setApplicationStatus('pending')
          }

          // 显示最终报告
          const modeLabels = {
            llm: '✅ LLM智能驱动',
            fallback: '⚠️ 后端降级流（硬编码）',
            fallback_complete: '⚠️ 后端降级补全（硬编码）',
            frontend_fallback: '⚠️ 前端降级（模拟数据）',
            idle: '未执行'
          }
          let finalText = `【执行模式: ${modeLabels[executionMode.mode] || executionMode.mode}】${executionMode.reason ? `\n降级原因: ${executionMode.reason}` : ''}\n\n`
          finalText += report?.summary || `风控尽调完成！\n\n`
          if (scorecard) {
            finalText += `📊 综合评分：${scorecard.total_score} 分 · ${scorecard.risk_level}\n`
          }
          if (credit_suggestion) {
            finalText += `💰 建议额度：${credit_suggestion.suggested_amount || credit_suggestion.amount_range}\n`
            finalText += `📅 建议期限：${credit_suggestion.suggested_period || '12个月'}\n`
          }

          setChatMessages(prev => [...prev, {
            role: 'ai',
            text: finalText,
            time: getCurrentTime()
          }])

          // 询问用户是否生成授信申请单
          if (credit_suggestion) {
            setTimeout(() => {
              setChatMessages(prev => [...prev, {
                role: 'ai',
                text: `是否生成授信申请单？请回复「生成」继续，或「跳过」暂不生成。`,
                time: getCurrentTime()
              }])
            }, 100)
          }
        }
        break
        
      case 'debug':
        // 调试信息（关键！显示执行模式和降级原因
        let debugText = content
        const extras = []
        if (_llm_config) {
          extras.push('model=' + _llm_config.model)
          extras.push('url=' + _llm_config.api_url.slice(0, 40) + '...')
          extras.push('has_api_key=' + _llm_config.has_api_key)
        }
        if (_llm_content_preview) {
          extras.push('内容预览: "' + String(_llm_content_preview).slice(0, 80).replace(/"/g, "'") + '"')
        }
        if (_llm_tool_calls && _llm_tool_calls.length > 0) {
          const tcs = _llm_tool_calls.map(function(t) {
            const args = t.args ? String(t.args).slice(0, 60) : ''
            return t.name + '(' + args + ')'
          }).join('; ')
          extras.push('工具调用: [' + tcs + ']')
        }
        if (_context_state) {
          const cs = _context_state
          extras.push('上下文: search=' + cs.has_company_data + ', check=' + cs.has_rule_result + ', score=' + cs.has_scorecard + ', credit=' + cs.has_credit)
        }
        if (extras.length > 0) {
          debugText += '\n' + extras.map(function(e) { return '  · ' + e }).join('\n')
        }
        setChatMessages(prev => [...prev, {
          role: 'ai',
          text: debugText,
          isDebug: true,
          time: getCurrentTime()
        }])
        break

      case 'error':
        // 错误
        setChatMessages(prev => [...prev, {
          role: 'ai',
          text: `❌ ${content}`,
          time: getCurrentTime()
        }])
        break
        
      default:
        // 未知类型
        setChatMessages(prev => [...prev, {
          role: 'ai',
          text: content,
          time: getCurrentTime()
        }])
    }
  }
  
  // 格式化观察结果
  const formatObservation = (toolName, payload) => {
    switch (toolName) {
      case 'search_company':
        return `企业信息获取成功：\n• 名称：${payload.name || payload.companyName}\n• 注册资本：${payload.registered_capital || payload.registeredCapital || 0}万\n• 成立时间：${payload.establishment_date || payload.establishDate || 'N/A'}\n• 行业：${payload.industry || 'N/A'}\n• 来源：${payload.data_source || '演示数据'}`
        
      case 'check_rules':
        const passed = payload.passed !== undefined ? payload.passed : true
        const violations = payload.violations || []
        if (passed) {
          return `规则校验通过，无违规项`
        } else {
          return `规则校验未通过！\n违规项：\n${violations.map((v, i) => `${i+1}. ${v}`).join('\n')}`
        }
        
      case 'create_scorecard':
        return `评分完成！\n• 综合得分：${payload.total_score || 0} 分\n• 风险等级：${payload.risk_level || '未知'}\n• 评估维度：${payload.dimensions?.length || 0} 项`
        
      case 'calculate_credit':
        return `授信建议生成：\n• 建议额度：${payload.suggested_amount || payload.amount_range || '待定'}\n• 建议期限：${payload.suggested_period || '12个月'}\n• 推荐类型：${payload.primary_credit_type || '流动资金授信'}`
        
      default:
        return content
    }
  }
  
  // 降级模式：后端不可用时使用模拟数据
  // 注意：如果已经通过LLM获取了部分数据（如评分、授信建议），保留已有的真实数据，只补充缺失部分
  const fallbackAnalysis = (name) => {
    const info = MOCK_COMPANIES[name] || {
      companyName: name,
      companyType: '有限责任公司',
      unifiedCode: '91440300MA5XXXXXXX',
      legalPerson: '张三',
      establishDate: '2015-03-20',
      registeredCapital: 5000,
      paidCapital: 3000,
      operationStatus: '存续',
      industry: '科技服务业',
      insuranceCount: 128,
      revenue: 8500,
      address: '深圳市南山区科技园南区',
      score: 98,
      riskLevel: '低风险',
      status: '草稿',
      suggestedCredit: '300-500',
      suggestedTerm: '12',
      creditType: '流动资金授信',
      fundsUsage: '日常经营周转'
    }
    
    // 只在企业信息为空时设置
    if (!companyInfo) {
      setCompanyInfo(info)
    }
    
    // 只在评分结果为空时设置（保留LLM已获取的真实评分）
    if (!scoreResult) {
      setScoreResult({
        total_score: info.score,
        risk_level: info.riskLevel,
        breakdown: {
          '主体资质': 28,
          '司法风险': 30,
          '经营稳定性': 25,
          '关联风险': 15
        }
      })
    }
    
    // 只在授信建议为空时设置（保留LLM已获取的真实建议）
    if (!creditSuggestion) {
      setCreditSuggestion({
        suggestedCredit: info.suggestedCredit,
        suggestedTerm: info.suggestedTerm,
        creditType: info.creditType,
        fundsUsage: info.fundsUsage
      })
    }
    
    setIsRejected(false)
    
    // 获取当前实际的评分和授信建议用于显示
    const currentScore = scoreResult?.total_score || info.score
    const currentRisk = scoreResult?.risk_level || info.riskLevel
    const currentCredit = creditSuggestion?.suggestedCredit || info.suggestedCredit
    const currentTerm = creditSuggestion?.suggestedTerm || info.suggestedTerm
    const currentType = creditSuggestion?.creditType || info.creditType
    
    setChatMessages(prev => [...prev, {
      role: 'ai',
      text: `【执行模式: ⚠️ 前端降级（模拟数据）】\n\n已完成「${name}」风控尽调！\n✓ 工商信息采集完成\n✓ 准入规则校验通过\n✓ 行业评分卡加载完成\n✓ 综合评分 ${currentScore} 分 · ${currentRisk}\n授信方案已生成，建议额度 ${currentCredit} 万，期限 ${currentTerm} 个月，${currentType}。`,
      time: getCurrentTime()
    }])
  }

  // 更新企业信息（编辑保存）
  const updateCompanyInfo = useCallback((updatedInfo) => {
    const name = updatedInfo.companyName
    setCompanies(prev => prev.map(c =>
      c.companyName === name ? { ...c, ...updatedInfo } : c
    ))
    if (companyInfo && companyInfo.companyName === name) {
      setCompanyInfo(updatedInfo)
    }
    showToast('保存成功')
  }, [companyInfo, showToast])

  // 确认生成授信申请单
  const confirmGenerateApplication = useCallback(() => {
    if (!pendingApplicationData || !companyInfo) return
    // 将 pending 数据写入 companyInfo 生成授信申请单
    updateCompanyInfo({
      ...companyInfo,
      ...pendingApplicationData,
      status: '草稿'
    })
    setApplicationStatus('confirmed')
    setPendingApplicationData(null)
    setChatMessages(prev => [...prev, {
      role: 'ai',
      text: '已生成授信申请单，请确认信息后点击「提交审批」。',
      time: getCurrentTime()
    }])
  }, [pendingApplicationData, companyInfo, updateCompanyInfo])

  // 跳过生成授信申请单
  const skipGenerateApplication = useCallback(() => {
    setApplicationStatus('hidden')
    setPendingApplicationData(null)
    setChatMessages(prev => [...prev, {
      role: 'ai',
      text: '好的，授信申请单已跳过，您随时可以在右侧聊天窗口输入指令继续操作。',
      time: getCurrentTime()
    }])
  }, [])

  // 发送聊天消息
  const sendMessage = useCallback((text) => {
    if (!text.trim()) return

    const lowerText = text.trim().toLowerCase()

    // 快捷指令处理
    if (text.includes('一键风控') || text.includes('尽调')) {
      runAIFengKong(currentCompany)
      return
    }

    // 授信申请单生成指令
    if (applicationStatus === 'pending') {
      if (lowerText.includes('生成') || lowerText.includes('确认') || lowerText.includes('好的') || lowerText.includes('是') || lowerText.includes('好的')) {
        setChatMessages(prev => [...prev, {
          role: 'me',
          text,
          time: getCurrentTime()
        }])
        confirmGenerateApplication()
        return
      }
      if (lowerText.includes('跳过') || lowerText.includes('暂不') || lowerText.includes('不要')) {
        setChatMessages(prev => [...prev, {
          role: 'me',
          text,
          time: getCurrentTime()
        }])
        skipGenerateApplication()
        return
      }
    }

    setChatMessages(prev => [...prev, {
      role: 'me',
      text,
      time: getCurrentTime()
    }])

    // 模拟AI回复
    setTimeout(() => {
      let response = ''
      if (text.includes('扣分')) {
        response = '扣分较高的三项：\n1. 经营稳定性 · 营收规模（-3分）\n2. 主体资质 · 参保人数（-2分）\n3. 关联风险 · 关联企业数（-1分）'
      } else if (text.includes('额度') || text.includes('授信')) {
        response = '建议授信额度：200-350万元，建议授信期限：12个月，建议采用纯信用授信方式。'
      } else {
        response = '已收到您的请求，正在为您处理。您可以点击下方的快捷按钮快速执行常用操作。'
      }

      setChatMessages(prev => [...prev, {
        role: 'ai',
        text: response,
        time: getCurrentTime()
      }])
    }, 800)
  }, [currentCompany, runAIFengKong, applicationStatus, confirmGenerateApplication, skipGenerateApplication])
  
  // 更新企业状态（提交审批）
  const submitToApproval = useCallback((companyName) => {
    setCompanies(prev => prev.map(c => 
      c.companyName === companyName ? { ...c, status: '审批中' } : c
    ))
    // 如果是当前企业也更新
    if (companyInfo && companyInfo.companyName === companyName) {
      setCompanyInfo(prev => ({ ...prev, status: '审批中' }))
    }
    showToast('提交成功，授信单已进入审批流程')
  }, [companyInfo, showToast])
  
  // 撤回审批
  const recallCredit = useCallback((companyName) => {
    setCompanies(prev => prev.map(c => 
      c.companyName === companyName ? { ...c, status: '草稿' } : c
    ))
    if (companyInfo && companyInfo.companyName === companyName) {
      setCompanyInfo(prev => ({ ...prev, status: '草稿' }))
    }
    closeModal()
    showToast('授信单已撤回至草稿状态')
  }, [companyInfo, closeModal, showToast])

  // 确认禁入：用户同意小控的禁入建议
  const confirmReject = useCallback(() => {
    const { company } = rejectConfirm
    setChatMessages(prev => [...prev, {
      role: 'ai',
      text: `已确认：「${company}」准入不通过，流程终止。`,
      time: getCurrentTime()
    }])
    setRejectConfirm({ show: false, violations: [], reasons: [], company: null })
    showToast('已确认禁入')
  }, [rejectConfirm, showToast])

  // 忽略禁入建议：用户决定继续分析
  const ignoreReject = useCallback(() => {
    const { company } = rejectConfirm
    setChatMessages(prev => [...prev, {
      role: 'ai',
      text: `已忽略小控的禁入建议，继续为「${company}」进行风控评分和授信分析。`,
      time: getCurrentTime()
    }])
    setRejectConfirm({ show: false, violations: [], reasons: [], company: null })
    showToast('已忽略禁入建议，继续分析')
  }, [rejectConfirm, showToast])

  // 关闭禁入确认弹窗
  const closeRejectConfirm = useCallback(() => {
    setRejectConfirm({ show: false, violations: [], reasons: [], company: null })
  }, [])
  
  const value = {
    activeTab,
    setActiveTab,
    chatOpen,
    toggleChat,
    currentCompany,
    setCurrentCompany,
    companyInfo,
    setCompanyInfo,
    companies,
    suggestions,
    scoreResult,
    ruleResult,
    rejectConfirm,
    executionMode,
    creditSuggestion,
    isRejected,
    loading,
    modal,
    openModal,
    closeModal,
    toast,
    showToast,
    chatMessages,
    sendMessage,
    runAIFengKong,
    submitToApproval,
    recallCredit,
    updateCompanyInfo,
    confirmReject,
    ignoreReject,
    closeRejectConfirm,
    applicationStatus,
    confirmGenerateApplication,
    skipGenerateApplication
  }
  
  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) {
    throw new Error('useApp must be used within AppProvider')
  }
  return ctx
}

function getCurrentTime() {
  const d = new Date()
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
