# Docker 部署问题修复总结

本文档总结了解决 Docker 部署过程中遇到的所有问题及其修复方案。

## 🐛 问题列表与修复

### 1. NameError: name 'get_password_hash' is not defined

**问题描述**:
- 容器启动时立即进入重启状态
- 日志显示 `NameError: name 'get_password_hash' is not defined`
- 错误发生在 `auth_simple.py` 第 58 行和第 61 行

**根本原因**:
- `get_password_hash` 函数在第 74 行定义
- 但在第 50、58、61 行的 `parse_auth_users` 函数中被调用
- Python 中函数必须在使用前定义

**修复方案**:
```python
# 修复前：函数定义在使用之后
def parse_auth_users():  # 第 39 行
    # ...
    get_password_hash("admin123")  # 第 50 行 - 错误！

def get_password_hash(password):  # 第 74 行
    return pwd_context.hash(password)

# 修复后：函数定义在使用之前
def get_password_hash(password):  # 第 43 行
    return pwd_context.hash(password)

def parse_auth_users():  # 第 48 行
    # ...
    get_password_hash("admin123")  # 第 59 行 - 正确！
```

**验证方法**:
```bash
python test_syntax_fix.py
```

### 2. Docker Compose 版本警告

**问题描述**:
- 警告: "the attribute `version` is obsolete, it will be ignored"

**根本原因**:
- Docker Compose 新版本不再需要 `version` 属性
- 该属性已被标记为过时

**修复方案**:
```yaml
# 修复前
version: '3.8'
services:
  app:
    # ...

# 修复后
name: fushengshimeng
services:
  app:
    # ...
```

### 3. Docker Compose 命令兼容性问题

**问题描述**:
- 错误: "docker-compose: command not found"
- 新版 Docker 使用 `docker compose`（空格）
- 旧版 Docker 使用 `docker-compose`（连字符）

**修复方案**:

**Linux/macOS (deploy.sh)**:
```bash
# 自动检测可用的命令
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif command_exists docker-compose; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "Docker Compose is not available"
    exit 1
fi

# 使用变量替代硬编码命令
$DOCKER_COMPOSE_CMD build
$DOCKER_COMPOSE_CMD up -d
```

**Windows (deploy.bat)**:
```batch
REM 检测可用命令
docker compose version >nul 2>&1
if %errorlevel% equ 0 (
    set "DOCKER_COMPOSE_CMD=docker compose"
) else (
    where docker-compose >nul 2>&1
    if %errorlevel% equ 0 (
        set "DOCKER_COMPOSE_CMD=docker-compose"
    ) else (
        echo Docker Compose is not available
        exit /b 1
    )
)

REM 使用变量
%DOCKER_COMPOSE_CMD% build
%DOCKER_COMPOSE_CMD% up -d
```

### 4. 项目名称为空错误

**问题描述**:
- 错误: "project name must not be empty"

**修复方案**:
- 在 `docker-compose.yml` 中添加项目名称：
```yaml
name: fushengshimeng
```

## 🧪 测试验证

### 1. 语法和函数顺序测试
```bash
python test_syntax_fix.py
```

### 2. 认证系统测试
```bash
python test_auth_fix.py
```

### 3. Docker 部署测试
```bash
# Linux/macOS
./deploy.sh deploy

# Windows
deploy.bat deploy
```

## 📁 修改的文件

1. **backend/app/auth_simple.py**
   - 重新排列函数定义顺序
   - 将 `get_password_hash` 和 `verify_password` 移到文件前部

2. **docker-compose.yml**
   - 移除过时的 `version` 属性
   - 添加 `name: fushengshimeng` 项目名称

3. **deploy.sh**
   - 添加 Docker Compose 命令自动检测
   - 支持新旧版本的 Docker Compose

4. **deploy.bat**
   - 添加 Windows 版本的命令检测
   - 与 Linux 版本保持功能一致

5. **VALIDATION_CHECKLIST.md**
   - 更新故障排除部分
   - 添加已修复问题的说明

6. **测试文件**
   - `test_syntax_fix.py`: 验证函数定义顺序
   - `test_auth_fix.py`: 测试认证系统功能

## 🚀 部署流程

修复后的正确部署流程：

1. **配置环境**:
```bash
cp .env.docker.example .env
# 编辑 .env 文件，设置必要的环境变量
```

2. **部署应用**:
```bash
# Linux/macOS
./deploy.sh deploy

# Windows
deploy.bat deploy
```

3. **验证部署**:
```bash
# 检查服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs
```

4. **访问应用**:
- 浏览器打开 `http://localhost:8000`
- 使用配置的用户名密码登录

## 🔒 安全注意事项

1. **更改默认密码**: 
   - 修改 `.env` 文件中的 `AUTH_USERS`
   - 使用强密码

2. **保护敏感信息**:
   - 确保 `.env` 文件不被提交到版本控制
   - 定期更新 `SECRET_KEY`

3. **生产环境配置**:
   - 使用 HTTPS（配置 SSL 证书）
   - 设置防火墙规则
   - 定期备份数据

## 📞 支持

如果遇到其他问题：

1. 查看容器日志：`./deploy.sh logs`
2. 检查服务状态：`./deploy.sh status`
3. 运行测试脚本验证修复
4. 参考 `VALIDATION_CHECKLIST.md` 中的故障排除部分
