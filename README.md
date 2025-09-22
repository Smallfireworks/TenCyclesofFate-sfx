# 《浮生十梦》

**《浮生十梦》** 是一款基于 Web 的沉浸式文字冒险游戏。玩家在游戏中扮演一个与命运博弈的角色，每天有十次机会进入不同的“梦境”（即生命轮回），体验由 AI 动态生成的、独一无二的人生故事。游戏的核心在于“知足”与“贪欲”之间的抉择：是见好就收，还是追求更高的回报但可能失去一切？

## ✨ 功能特性

- **动态 AI 生成内容**:每一次游戏体验都由大型语言模型（如 GPT）实时生成，确保了故事的独特性和不可预测性。
- **实时交互**: 通过 WebSocket 实现前端与后端的实时通信，提供流畅的游戏体验。
- **用户名密码认证**: 简单安全的用户名密码认证系统，支持多用户账户管理。
- **精美的前端界面**: 采用具有“江南园林”风格的 UI 设计，提供沉浸式的视觉体验。
- **互动式判定系统**: 游戏中的关键行动可能触发“天命判定”。AI 会根据情境请求一次 D100 投骰，其“成功”、“失败”、“大成功”或“大失败”的结果将实时影响叙事走向，增加了游戏的随机性和戏剧性。
- **智能反作弊机制**: 内置一套基于 AI 的反作弊系统。它会分析玩家的输入行为，以识别并惩罚那些试图使用“奇巧咒语”（如 Prompt 注入）来破坏游戏平衡或牟取不当利益的玩家，确保了游戏的公平性。
- **数据持久化**: 游戏状态会定期保存，并在应用重启时加载，保证玩家进度不丢失。

## 🛠️ 技术栈

- **后端**:

  - **框架**: FastAPI
  - **Web 服务器**: Uvicorn
  - **实时通信**: WebSockets
  - **认证**: Python-JOSE (JWT), Authlib (OAuth)
  - **数据库**: SQLite (用于存储兑换码)
  - **AI 集成**: OpenAI API
  - **依赖管理**: uv / pip

- **前端**:

  - **语言**: HTML, CSS, JavaScript (ESM)
  - **库**:
    - `marked.js`: 用于在前端渲染 Markdown 格式的叙事文本。
    - `pako.js`: 用于解压缩从 WebSocket 服务器接收的 Gzip 数据，提高传输效率。

- **部署**:
  - **容器化**: Docker 和 Docker Compose 支持
  - **反向代理**: Nginx 配置，支持域名和 SSL
  - **跨平台**: 支持 Linux、macOS 和 Windows

## 🚀 部署指南

《浮生十梦》现在支持两种部署方式：**Docker 部署（推荐）** 和 **传统部署**。

### 🐳 Docker 部署（推荐）

Docker 部署是最简单、最可靠的部署方式，支持一键部署和自动化管理。

#### 1. 环境准备

确保您的系统已安装：

- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- **Git**

#### 2. 获取项目代码

```bash
git clone https://github.com/CassiopeiaCode/TenCyclesofFate.git
cd TenCyclesofFate
```

#### 3. 配置环境变量

```bash
# 复制环境配置文件
cp .env.docker.example .env

# 编辑配置文件
nano .env  # 或使用您喜欢的编辑器
```

**必须配置的项目：**

- `OPENAI_API_KEY`: 您的 OpenAI API 密钥
- `SECRET_KEY`: JWT 签名密钥（使用 `openssl rand -hex 32` 生成）
- `AUTH_USERS`: 用户账户（格式：`username1:password1,username2:password2`）

#### 4. 部署应用

```bash
# 给部署脚本添加执行权限
chmod +x deploy.sh

# 部署应用（仅应用）
./deploy.sh deploy

# 或者部署应用 + Nginx 反向代理
./deploy.sh deploy --with-nginx

# 或者部署应用 + Nginx + SSL 证书
./deploy.sh deploy --with-nginx --ssl
```

#### 5. 访问应用

- **仅应用模式**: http://localhost:8000
- **Nginx 模式**: http://localhost
- **SSL 模式**: https://localhost

#### 6. 管理命令

```bash
# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart

# 更新应用
./deploy.sh update

# 备份数据
./deploy.sh backup
```

### 🔧 传统部署

如果您不想使用 Docker，也可以使用传统方式部署。

#### 1. 环境准备

确保您的系统已安装：

- **Python 3.8+**
- **Git**
- **uv** (推荐) 或 **pip**

```bash
# 安装 uv (推荐)
pip install uv
```

#### 2. 获取项目代码

```bash
git clone https://github.com/CassiopeiaCode/TenCyclesofFate.git
cd TenCyclesofFate
```

#### 3. 安装依赖

```bash
# 使用 uv (推荐)
uv pip install -r backend/requirements.txt

# 或使用 pip
pip install -r backend/requirements.txt
```

#### 4. 配置环境变量

```bash
# 复制环境配置文件
cp backend/.env.example backend/.env

# 编辑配置文件
nano backend/.env  # 或使用您喜欢的编辑器
```

**配置示例：**

```dotenv
# OpenAI API Settings
OPENAI_API_KEY="your_openai_api_key_here"
OPENAI_BASE_URL="https://api.openai.com/v1"
OPENAI_MODEL="gpt-4o"
OPENAI_MODEL_CHEAT_CHECK="gpt-3.5-turbo"

# JWT Settings
SECRET_KEY="your_very_secure_secret_key_here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=600

# Authentication Settings (Username/Password System)
# Format: username1:password1,username2:password2
AUTH_USERS="admin:changeme123,demo:demo123"

# Database
DATABASE_URL="sqlite:///veloera.db"

# Server Settings
HOST="0.0.0.0"
PORT=8000
UVICORN_RELOAD=true
```

**重要配置说明：**

- **`OPENAI_API_KEY`**: 必填，您的 OpenAI API 密钥
- **`SECRET_KEY`**: 必填，JWT 签名密钥（使用 `openssl rand -hex 32` 生成）
- **`AUTH_USERS`**: 必填，用户账户配置，格式为 `用户名:密码,用户名:密码`

#### 5. 运行应用

```bash
# 给脚本添加执行权限
chmod +x run.sh

# 启动应用
./run.sh
```

服务器成功启动后，在浏览器中访问 `http://localhost:8000` 即可开始游戏。

## 🔐 用户管理

### 添加新用户

1. **Docker 部署**: 编辑 `.env` 文件中的 `AUTH_USERS` 变量
2. **传统部署**: 编辑 `backend/.env` 文件中的 `AUTH_USERS` 变量

```bash
# 格式：用户名1:密码1,用户名2:密码2
AUTH_USERS="admin:admin123,player1:password1,player2:password2"
```

### 重新部署以应用更改

```bash
# Docker 部署
./deploy.sh restart

# 传统部署
./run.sh
```

## 🌐 域名和 SSL 配置

### 使用域名访问

1. 将域名解析到服务器 IP
2. 编辑 `nginx/nginx.conf`，将 `server_name` 改为您的域名
3. 重新部署：`./deploy.sh deploy --with-nginx`

### 启用 SSL

1. 将 SSL 证书文件放置到 `nginx/ssl/` 目录：

   - `cert.pem`: 证书文件
   - `key.pem`: 私钥文件

2. 编辑 `nginx/nginx.conf`，取消注释 HTTPS 服务器配置

3. 重新部署：`./deploy.sh deploy --with-nginx --ssl`

## 📁 项目结构

```
.
├── backend/                    # 后端代码
│   ├── .env.example           # 环境变量示例文件
│   ├── requirements.txt       # Python 依赖
│   └── app/
│       ├── __init__.py
│       ├── main.py            # FastAPI 应用主入口
│       ├── config.py          # Pydantic 配置模型
│       ├── auth_simple.py     # 用户名密码认证系统
│       ├── game_logic.py      # 核心游戏逻辑
│       ├── websocket_manager.py # WebSocket 连接管理
│       ├── state_manager.py   # 游戏状态的保存与加载
│       ├── db.py              # 数据库连接
│       ├── openai_client.py   # OpenAI API 客户端
│       ├── cheat_check.py     # 作弊检查逻辑
│       ├── redemption.py      # 兑换码生成逻辑
│       └── prompts/           # 存放 AI 系统提示的目录
│
├── frontend/                   # 前端代码
│   ├── index.html             # 主 HTML 文件
│   ├── index.css              # CSS 样式文件
│   └── index.js               # 前端 JavaScript 逻辑
│
├── nginx/                      # Nginx 配置
│   ├── nginx.conf             # Nginx 配置文件
│   └── ssl/                   # SSL 证书目录
│
├── scripts/
│   └── generate_token.py      # 用于生成测试 token 的脚本
│
├── Dockerfile                  # Docker 镜像构建文件
├── docker-compose.yml          # Docker Compose 配置
├── .dockerignore              # Docker 忽略文件
├── .env.docker.example        # Docker 环境变量示例
├── deploy.sh                  # Docker 部署脚本
├── .gitignore
├── README.md                  # 本文档
└── run.sh                     # 传统部署启动脚本
```

## 🎮 新功能特性

### 🔄 重新开始功能

当玩家达到"破碎虚空"状态后，现在可以选择重新开始今日的试炼：

- 点击"重新开始今日试炼"按钮
- 保留当日日期，重置所有进度和机缘次数
- 允许玩家在同一天内多次体验游戏

### 🎨 界面优化

- **扩大对话区域**: 增加叙事窗口的显示空间
- **紧凑状态面板**: 优化人物业力显示，节省屏幕空间
- **响应式布局**: 更好地适配不同屏幕尺寸
- **视觉增强**: 保持原有江南园林风格，提升整体美观度
