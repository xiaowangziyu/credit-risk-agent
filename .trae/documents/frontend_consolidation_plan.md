# 前端代码统一清理计划

## 问题诊断

当前目录下存在**两套前端代码**，分布在不同位置，容易造成混乱：

| 位置 | 类型 | 访问地址 | 是否真实调用后端API | 状态 |
|------|------|----------|---------------------|------|
| `credit_agent/` | React + Vite 项目 | `http://localhost:5173/` | ✅ 是（通过 fetch 调用 `http://localhost:8001/api/agent/analyze`） | **真实前端** |
| `my-second-agent/static/index.html` | 单文件静态 HTML | `http://localhost:8001/` | ❌ 否（内部是 `setTimeout` 硬编码动画） | **历史遗留** |
| `agent-service/` | 另一个 Python 后端 | - | - | **历史遗留** |
| `my-first-agent/` | Flask 老项目 | - | - | **历史遗留** |

## 当前架构

```
┌───────────────────────────────────────────────────────────┐
│                                                           │
│   用户浏览器 → http://localhost:5173/ (React 开发服务器)  │
│                        │                                   │
│                        ▼                                   │
│         Vite 代理 /api → http://localhost:8001/api/*      │
│                        │                                   │
│                        ▼                                   │
│     Python 后端 FastAPI → my-second-agent/                 │
│                  │    ├── main.py                          │
│                  │    ├── agent/react_agent.py             │
│                  │    └── static/index.html (⚠️ 遗留)      │
│                  │                                          │
│                  └── 同时在 8001 根路径还挂了一个          │
│                       静态HTML演示页（setTimeout动画）      │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## 目标

1. **唯一前端源**：让 `credit_agent/` 成为**唯一的前端代码所在地**
2. **明确归属标记**：在所有关键文件顶部加清晰标记，任何代理都能一眼看出"这是前端代码，去 credit_agent/ 里改"
3. **API对齐**：让 React 前端的 `api/index.js` 与后端实际路由匹配
4. **清理遗留**：将 `my-second-agent/static/index.html` 替换为一个简单的跳转/提示页面，避免误访问

## 具体改动清单

### 改动 1：在关键 JSX/JS 文件顶部加归属标识

目标文件：
- [credit_agent/src/App.jsx](file:///d:/pycharm/python项目/credit_agent/src/App.jsx)
- [credit_agent/src/context/AppContext.jsx](file:///d:/pycharm/python项目/credit_agent/src/context/AppContext.jsx)
- [credit_agent/src/components/Layout.jsx](file:///d:/pycharm/python项目/credit_agent/src/components/Layout.jsx)
- [credit_agent/src/components/Workbench.jsx](file:///d:/pycharm/python项目/credit_agent/src/components/Workbench.jsx)
- [credit_agent/src/components/ChatPanel.jsx](file:///d:/pycharm/python项目/credit_agent/src/components/ChatPanel.jsx)
- [credit_agent/src/components/ScoreCard.jsx](file:///d:/pycharm/python项目/credit_agent/src/components/ScoreCard.jsx)
- [credit_agent/src/api/index.js](file:///d:/pycharm/python项目/credit_agent/src/api/index.js)
- [credit_agent/index.html](file:///d:/pycharm/python项目/credit_agent/index.html)
- [credit_agent/src/main.jsx](file:///d:/pycharm/python项目/credit_agent/src/main.jsx)
- [credit_agent/src/index.css](file:///d:/pycharm/python项目/credit_agent/src/index.css)
- [credit_agent/package.json](file:///d:/pycharm/python项目/credit_agent/package.json)

改动内容：在每个文件顶部加注释标记：
- JSX/JS/JS 文件：`// 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/`
- CSS 文件：`/* 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/ */`
- HTML 文件：`<!-- 📍 前端代码归属：本文件是 React 前端的一部分，位于 credit_agent/ -->`
- package.json：在 `"name"` 字段上方加一个 `"_note"` 字段做声明

### 改动 2：让 React 前端的 API 层与后端路由对齐

**当前问题**：[credit_agent/src/api/index.js](file:///d:/pycharm/python项目/credit_agent/src/api/index.js) 中定义的函数（`searchCompany` → `/agent/search`、`scoreCompany` → `/agent/score`、`checkRules` → `/agent/rule`、`calculateCredit` → `/agent/credit`、`getReport` → `/agent/report`、`getCompany` → `/company/:name`）和后端实际路由（见 [my-second-agent/main.py](file:///d:/pycharm/python项目/my-second-agent/main.py) 第 46–130 行：`/api/agent/analyze`、`/api/companies/local`、`/api/companies/search/:name`、`/api/applications` 等）完全不匹配。

**当前实际情况**：[AppContext.jsx](file:///d:/pycharm/python项目/credit_agent/src/context/AppContext.jsx) 里的 `runAIFengKong` 直接用 `fetch('http://localhost:8001/api/agent/analyze', ...)` 绕过了 `api/index.js`，所以页面能用，但 `api/index.js` 里的函数其实一个都用不上。

**计划**：
- 重写 `api/index.js`，让它只暴露后端实际存在的路由：
  - `analyzeCompany(companyName)` → `POST /api/agent/analyze`（SSE流式响应）
  - `getLocalCompanies()` → `GET /api/companies/local`
  - `searchCompany(companyName)` → `GET /api/companies/search/:name`
  - `getApplications()` → `GET /api/applications`
  - `getApplication(enterprise_name)` → `GET /api/applications/:enterprise_name`
  - `updateApplication(application_id, data)` → `PUT /api/applications/:application_id`
  - `submitApplication(application_id)` → `POST /api/applications/:application_id/submit`
  - `withdrawApplication(application_id)` → `POST /api/applications/:application_id/withdraw`
- 将 `api/index.js` 的 `API_BASE` 从 `/api/agent` 改为 `/api`，让所有函数路径正确
- 修改 `AppContext.jsx` 里的 `runAIFengKong`：不再手写 `fetch('http://localhost:8001/api/agent/analyze')`，而是从 `api/index.js` `import { analyzeCompany }` 并使用标准 Vite 代理（`/api/agent/analyze`）。这样访问地址就从 `localhost:5173` 时走代理到 `localhost:8001/api/agent/analyze`，不需要写死 `http://localhost:8001`

### 改动 3：替换 `my-second-agent/static/index.html`

**问题**：当前这个文件是一个**完整的"假演示"页面**，包含硬编码的 `setTimeout` 动画。用户访问 `http://localhost:8001/` 时看到的是这个页，而不是 React 前端。

**计划**：替换为一个**非常简洁的提示页面**，内容为：
```
"✅ 后端服务运行中。请访问 http://localhost:5173/ 打开 React 前端。
 或使用 POST /api/agent/analyze 调用风控API。"
```
同时在文件顶部加 HTML 注释：
`<!-- ⚠️ 这是后端入口页，不是前端。真正的前端代码在 credit_agent/ 目录。 -->`

这样任何人误访问 `http://localhost:8001/` 都会立刻知道应该去 `5173` 访问真正的前端。

### 改动 4：在项目根目录放置一个 README 类型的"文件地图"

在 `d:\pycharm\python项目\README.md`（或 `.trae/documents/project_map.md`）放一个简洁的架构说明，包括：
- 本项目是一个"企业授信智能风控决策 Agent"，由 Python 后端 + React 前端组成
- **后端**：`my-second-agent/`（FastAPI + ReAct agent），启动命令：在该目录下 `python -m uvicorn main:app --reload`，端口 `8001`
- **前端**：`credit_agent/`（React + Vite），启动命令：在该目录下 `npm run dev`，端口 `5173`
- **前端开发时，应该修改 `credit_agent/src/` 下的文件**
- `my-second-agent/static/index.html` 只是一个后端服务入口提示页，**不是真实前端**

## 风险与注意事项

1. **不修改业务逻辑**：本次改动只涉及文件标识、API 路径对齐、以及替换一个演示页面，不触碰 `react_agent.py` 的 ReAct 逻辑、不触碰后端工具链。
2. **AppContext.jsx 的改动需谨慎**：当前它用 `fetch('http://localhost:8001/api/agent/analyze')` 直接请求后端。改为走 Vite 代理（`/api/agent/analyze`）后，必须确保用户在 `localhost:5173` 访问（Vite 开发服务器启动中），代理才有效——这本来就是正常的使用方式，但需要确保 `vite.config.js` 中 `proxy` 配置正确（目前已配置为 `/api → http://localhost:8001`，看起来是对的）。
3. **SSE 流式响应**：`/api/agent/analyze` 返回的是 Server-Sent Events 流（`text/event-stream`），`runAIFengKong` 中已经在用 `reader = response.body.getReader()` 处理。改走代理后，响应格式不变，所以处理逻辑不变，唯一改动就是 URL 从 `'http://localhost:8001/api/agent/analyze'` 改成 `'/api/agent/analyze'`。
4. **不删除历史项目**：`agent-service/`、`my-first-agent/`、`my-first-rag/` 这些目录保留不动，它们可能是早期探索版本或另有用途。本计划只做"统一当前在用的前后端"。

## 操作步骤总览

```
步骤 1：给 credit_agent/ 下所有关键文件加归属标识注释  (10 个文件)
步骤 2：重写 credit_agent/src/api/index.js，对齐后端路由
步骤 3：修改 credit_agent/src/context/AppContext.jsx，改用 api/index.js 中的函数 + Vite 代理
步骤 4：替换 my-second-agent/static/index.html 为简洁提示页
步骤 5：新增项目架构说明文档
```
