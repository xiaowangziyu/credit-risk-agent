# 企业授信智能风控决策 Agent

一个面向 B 端产品：输入企业名称，通过 AI Agent（ReAct 模式 · function calling）执行企业尽调、规则校验、风控评分、授信额度计算。

> 一键完成整个流程。

## 目录结构

```
.
├── my-second-agent/    ← Python 后端（FastAPI + ReAct Agent）
│   ├── main.py              ← FastAPI 入口（同时 serve API + 前端静态文件）
│   ├── agent/               ← ReAct Agent 核心逻辑（react_agent.py）
│   ├── services/            ← LLM 调用 / 数据库
│   ├── tools/               ← 工具链（search_company、check_rules、create_scorecard...）
│   ├── static/             ← 前端构建产物（由 build-frontend.bat 生成）
│   ├── config/             ← 配置（settings.py）
│   ├── requirements.txt
│   └── .env.example
│
├── credit_agent/        ← React 前端（Vite 构建）
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── context/AppContext.jsx   ← 核心状态管理
│   │   ├── api/index.js          ← API 层（请求后端接口）
│   │   └── components/
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
└── build-frontend.bat    ← 一键构建脚本（把前端 → 后端 static/）
```

## 运行方式（本地开发）

### 1. 启动后端

```bash
cd my-second-agent
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

然后在浏览器访问 http://localhost:8001/api/agent/analyze 测试 API 可用性。

### 2. 启动前端（开发模式，热更新）

```bash
cd credit_agent
npm install          # 首次需要
npm run dev
```

访问 http://localhost:5173/ 使用界面会看到 React 开发服务器，它的请求会被 Vite 代理到 `http://localhost:8001/api/*`。

### 3. 构建前端到后端（让后端同时 serve 前后端

在项目根目录执行：

```bash
build-frontend.bat
```

然后启动后端：

```bash
cd my-second-agent
python -m uvicorn main:app --reload
```

访问 http://localhost:8001/ 即可看到**完整的前后端一体化应用**（不需要再开 5173。

## 上传 GitHub

这是**单一仓库项目（monorepo 风格），前后端代码都放在一起管理，Git 初始化：

```bash
# 在项目根目录
git init
git add .
git commit -m "initial commit
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

上传时 Git 会自动忽略：
- `my-second-agent/` 里的 Python 代码
- `credit_agent/` 里的 React 源码
- `build-frontend.bat` 构建脚本
- 本 README

同时忽略（不会上传的）：`node_modules/`、`.venv/`、`.pyc`、`.env` 等敏感/临时文件由两份 `.gitignore` 管理。

## 部署到 PythonAnywhere

PythonAnywhere 免费版只支持部署**一个 Web 应用**（一个项目）。
本项目支持单项目部署：把 `my-second-agent/` 就是那个项目部署，**作为一个 FastAPI 项目同时 serve 前后端**。

### 步骤 A：先在本地构建前端

```bash
build-frontend.bat
```

确认构建后 `my-second-agent/static/index.html` 和 `my-second-agent/static/assets/` 已生成。

### 步骤 B：上传到 PythonAnywhere

**方式 1：从 GitHub 拉取（推荐）

```bash
# 在 PythonAnywhere 的 Bash 控制台
cd ~
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名/my-second-agent
pip install -r requirements.txt
```

**方式 2：通过 Files 页面直接上传

把本地构建好的整个 `my-second-agent/` 目录压缩为 zip，上传到 PythonAnywhere 后解压。

### 步骤 C：在 PythonAnywhere 创建 Web 配置

1. 在 PythonAnywhere 的 **Web** 页面 → **Add a new web app**

2. 选择 **Manual configuration** → 然后选择 **Python 3.x**

3. 在 WSGI 配置文件（Web 页面里点击 WSGI 配置文件路径（类似 `/var/www/你的用户名_pythonanywhere_com_wsgi.py`），修改为：

```python
import sys
path = '/home/你的用户名/my-second-agent'  # ← 改成你的项目实际路径
if path not in sys.path:
    sys.path.insert(0, path)

from main import app as application
```

4. **Virtualenv**：在 Web 页面的 "Virtualenv" 部分填写你的虚拟环境路径（如果用了），或者留空表示用系统 Python。

5. **Static files**：
- URL: `/static/`
- Path: `/home/你的用户名/my-second-agent/static

- URL: `/assets/`
- Path: `/home/你的用户名/my-second-agent/static/assets

（因为 FastAPI 也会 serve 这些，但显式声明可以让 PythonAnywhere 直接处理更高效。

6. **Reload** 按钮重新加载应用。

### 步骤 D：配置环境变量

在 PythonAnywhere 的 Web 页面，进入项目目录下创建 `.env` 文件：

```bash
cd /home/你的用户名/my-second-agent
cp .env.example .env
nano .env
```

填入你的 API 配置：

```
LLM_API_KEY=your_api_key_here
LLM_MODEL=deepseek-chat
LLM_API_URL=https://api.deepseek.com/v1/chat/completions

# 企业工商信息查询（可选，没有时使用本地示例数据）
JUHE_API_KEY=
```

### 步骤 E：测试

访问 `https://你的用户名.pythonanywhere.com/

应该看到 React 前端界面正常加载，点击"一键风控"能正常调用后端 API。

## FAQ

**Q：前端和后端是两个独立目录，为什么能一起部署？

A：`build-frontend.bat` 把 `credit_agent/dist/` 的构建产物复制到 `my-second-agent/static/`，
然后 FastAPI 的 `main.py` 同时 serve：
- `/api/*` → API 接口
- `/` 和其它路径 → `static/index.html`（React 应用）
- `/assets/*` → React 的 JS/CSS 文件

**Q：为什么不把两个目录合成一个？

A：React 前端和 Python 后端技术栈不同，分开管理更清晰。但部署时通过构建产物被"折叠"进同一个项目目录。

**Q：本地开发和线上部署有什么区别？

本地开发：`npm run dev`（Vite 热更新） + `uvicorn`（后端）同时运行，访问 5173。
线上部署：`npm run build`（一次性），然后 FastAPI serve 静态文件 + API。访问一个域名。

**Q：如何更新部署后前端？

修改了前端代码后重新运行 `build-frontend.bat`，然后 `git push`，在 PythonAnywhere `git pull`，最后 Web 页面点 Reload。

## 技术栈

- 后端：Python 3.11+、FastAPI、Uvicorn
- 前端：React 18、Vite 5
- AI：OpenAI 兼容接口（function calling）
- 数据库：SQLite（轻量级）
