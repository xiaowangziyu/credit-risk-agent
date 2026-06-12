# GitHub & PythonAnywhere 部署执行引导

## 一、项目结构概览

```
python项目/
├── credit_agent/          # 前端（React + Vite）
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── my-second-agent/       # 后端（FastAPI）
│   ├── main.py
│   ├── run.py
│   ├── requirements.txt
│   └── config/settings.py
└── .env                   # 环境变量（已存在）
```

---

## 二、GitHub 仓库准备

### 步骤1：初始化 Git 仓库

```bash
cd d:\pycharm\python项目

# 初始化仓库
git init

# 创建 .gitignore 文件
cat > .gitignore << 'EOF'
# 前端依赖
node_modules/
dist/
.vite/

# Python依赖
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd

# 数据库
*.db

# 环境变量
.env
.env.local
.env.*.local

# 日志
*.log

# IDE
.idea/
.vscode/
*.swp
*.swo

# 操作系统
.DS_Store
Thumbs.db
EOF
```

### 步骤2：配置远程仓库

```bash
# 添加远程仓库（替换为你的GitHub地址）
git remote add origin https://github.com/你的用户名/你的仓库名.git

# 设置主分支
git branch -M main
```

### 步骤3：提交代码

```bash
# 查看状态
git status

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: 企业授信智能风控助手Agent"

# 推送到GitHub
git push -u origin main
```

---

## 三、PythonAnywhere 部署

### 步骤1：创建账户

1. 访问 [PythonAnywhere](https://www.pythonanywhere.com/)
2. 注册免费账户（Free tier足够用于演示）
3. 登录后进入 Dashboard

### 步骤2：创建 Web App

1. 点击 **Web > Add a new web app**
2. 选择 **Flask**（使用默认模板，后续会替换）
3. 选择 Python 版本：**Python 3.10** 或更高

### 步骤3：配置代码

#### 3.1 从 GitHub 克隆

```bash
# 在 PythonAnywhere 的 Bash console 中执行
cd /home/你的用户名
git clone https://github.com/你的用户名/你的仓库名.git
```

#### 3.2 安装依赖

```bash
cd 你的仓库名

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装后端依赖
pip install -r my-second-agent/requirements.txt
```

#### 3.3 配置 WSGI 文件

编辑 `/var/www/你的用户名_pythonanywhere_com_wsgi.py`：

```python
import sys
import os

# 添加项目路径
path = '/home/你的用户名/你的仓库名/my-second-agent'
if path not in sys.path:
    sys.path.insert(0, path)

# 设置环境变量
os.environ['LLM_API_KEY'] = '你的GLM API密钥'
os.environ['LLM_MODEL'] = 'glm-4-flash'
os.environ['LLM_API_URL'] = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

# 导入应用
from main import app as application
```

### 步骤4：配置静态文件（前端）

#### 4.1 构建前端

```bash
cd credit_agent
npm install
npm run build
```

#### 4.2 设置静态文件映射

在 PythonAnywhere 的 Web 配置页面：
- **Static files** > **URL**: `/static/`
- **Static files** > **Directory**: `/home/你的用户名/你的仓库名/credit_agent/dist`

### 步骤5：配置环境变量

在 PythonAnywhere 的 **Web > Environment variables** 中添加：

| 变量名 | 值 |
|-------|-----|
| LLM_API_KEY | 你的GLM API密钥 |
| LLM_MODEL | glm-4-flash |
| LLM_API_URL | https://open.bigmodel.cn/api/paas/v4/chat/completions |
| PORT | 8000 |

### 步骤6：重启应用

点击 PythonAnywhere Web 配置页面的 **Reload** 按钮

---

## 四、关键配置说明

### 后端配置文件

`my-second-agent/config/settings.py` 中的关键配置：

```python
# 模型配置（确保使用正确的模型名称）
LLM_MODEL = os.getenv("LLM_MODEL", "glm-4-flash")
LLM_API_URL = os.getenv("LLM_API_URL", "https://open.bigmodel.cn/api/paas/v4/chat/completions")
```

### 前端代理配置

`credit_agent/vite.config.js` 中的代理配置：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8001',
      changeOrigin: true
    }
  }
}
```

**部署时注意**：前端需要通过 PythonAnywhere 的域名访问后端 API，可能需要调整代理配置。

---

## 五、部署检查清单

### 前端检查
- [ ] `npm run build` 能正常完成
- [ ] 没有编译错误
- [ ] 静态资源路径正确

### 后端检查
- [ ] `python run.py` 能正常启动
- [ ] 访问 `/docs` 能看到 Swagger 文档
- [ ] LLM API 调用正常

### 环境变量检查
- [ ] LLM_API_KEY 已设置
- [ ] LLM_MODEL = glm-4-flash
- [ ] 数据库连接正常

---

## 六、常见问题

### Q1: LLM 调用返回 400 错误
**解决方案**：
- 确保模型名称正确（glm-4, glm-4-flash, glm-4-plus）
- 检查 API 密钥是否有效
- 检查 API URL 是否正确

### Q2: 前端无法连接后端
**解决方案**：
- 确保后端服务已启动
- 检查 CORS 配置
- 检查代理配置

### Q3: PythonAnywhere 部署后前端样式丢失
**解决方案**：
- 确保静态文件目录配置正确
- 重新构建前端并上传

---

## 七、下一步操作

1. **完成 GitHub 推送**（参考第二部分）
2. **在 PythonAnywhere 创建账户**（参考第三部分）
3. **配置后端服务**（参考步骤3-5）
4. **配置前端静态文件**（参考步骤4）
5. **测试部署结果**

需要我帮你执行其中任何一步吗？