# SmileX Zenoh Gateway

基于 Zenoh 技术的机器人通信与云端控制平台。

## 功能特性

- **机器人组网**：支持多台机器人设备的自动发现、动态加入与退出网络
- **云端控制**：实现对机器人的远程状态监控、指令下发和数据采集
- **安全通信**：设备认证与数据加密功能，保障通信安全性
- **RESTful API**：提供完整的 RESTful API 接口，支持第三方系统集成
- **数据存储**：内置 SQLite 数据库，支持设备数据的存储和查询
- **完善的日志**：结构化日志系统，支持日志分级和轮转

## 技术栈

- **Python 3.13+**
- **Eclipse Zenoh >= 1.8.0**：高性能的分布式通信中间件
- **FastAPI**：现代化的 Web API 框架
- **cryptography**：加密库，支持 AES-256-GCM 加密
- **SQLite**：轻量级嵌入式数据库

## 项目结构

```
smilex-zenoh-gateway/
├── src/
│   ├── common/                # 共用模块
│   │   ├── __init__.py
│   │   ├── core/              # 核心通信和设备管理
│   │   │   ├── __init__.py
│   │   │   ├── zenoh_session.py
│   │   │   └── device_manager.py
│   │   ├── config/            # 配置管理
│   │   │   ├── __init__.py
│   │   │   └── settings.py
│   │   ├── security/          # 安全功能
│   │   │   ├── __init__.py
│   │   │   ├── crypto.py
│   │   │   └── auth.py
│   │   └── utils/             # 工具模块
│   │       ├── __init__.py
│   │       └── logger.py
│   ├── api/                   # API 服务模块
│   │   ├── __init__.py
│   │   ├── __main__.py        # 入口文件
│   │   ├── main.py            # FastAPI 应用
│   │   └── models.py          # API 数据模型
│   ├── cloud/                 # 云端控制器模块
│   │   ├── __init__.py
│   │   ├── __main__.py        # 入口文件
│   │   ├── main.py            # 云端控制逻辑
│   │   └── data_storage.py    # 数据存储
│   └── robot/                 # 机器人端模块
│       ├── __init__.py
│       ├── __main__.py        # 入口文件
│       └── main.py            # 机器人端逻辑
├── api.py                     # API 服务启动脚本
├── cloud.py                   # 云端控制器启动脚本
├── robot.py                   # 机器人端启动脚本
├── main.py                    # 说明文件
├── pyproject.toml             # 项目配置
└── README.md
```

## 快速开始

### 安装依赖

```bash
uv sync
```

### 启动各个服务

```bash
# 运行 RESTful API 服务
uv run python api.py

# 运行云端控制器
uv run python cloud.py

# 运行机器人端
uv run python robot.py
```

API 文档将在 `http://localhost:8000/docs` 可用。

## API 使用示例

### 1. 设备认证

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "robot-001",
    "device_secret": "secret123"
  }'
```

### 2. 获取设备列表

```bash
curl -X GET "http://localhost:8000/api/v1/devices" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. 发送指令

```bash
curl -X POST "http://localhost:8000/api/v1/commands" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "robot-001",
    "command": "move",
    "parameters": {"x": 10, "y": 20}
  }'
```

## 配置说明

可以通过环境变量配置应用，环境变量前缀为 `SMILEX_`。

### 快速配置步骤

1. 复制环境变量模板：
   ```bash
   cp .env.example .env
   ```

2. 生成安全密钥（推荐）：
   ```bash
   uv run python scripts/generate_keys.py
   ```

3. 将生成的密钥添加到 `.env` 文件中

### 完整配置列表

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| **应用基本配置** | | |
| `SMILEX_APP_NAME` | 应用名称 | `SmileX Zenoh Gateway` |
| `SMILEX_APP_VERSION` | 应用版本 | `0.1.0` |
| `SMILEX_DEBUG` | 调试模式 | `true` |
| **Zenoh 网络配置** | | |
| `SMILEX_ZENOH_CONNECT` | Zenoh 连接端点 | - |
| `SMILEX_ZENOH_LISTEN` | Zenoh 监听端点 | `tcp/0.0.0.0:7447` |
| **API 服务配置** | | |
| `SMILEX_API_HOST` | API 服务主机 | `0.0.0.0` |
| `SMILEX_API_PORT` | API 服务端口 | `8000` |
| **设备管理配置** | | |
| `SMILEX_HEARTBEAT_INTERVAL` | 心跳间隔（秒） | `1.0` |
| `SMILEX_HEARTBEAT_TIMEOUT` | 心跳超时（秒） | `3.0` |
| `SMILEX_MAX_DEVICES` | 最大设备数 | `50` |
| **日志配置** | | |
| `SMILEX_LOG_LEVEL` | 日志级别（DEBUG/INFO/WARNING/ERROR） | `INFO` |
| `SMILEX_LOG_FILE` | 日志文件路径 | `logs/app.log` |
| `SMILEX_LOG_MAX_BYTES` | 单个日志文件最大大小（字节） | `10485760` |
| `SMILEX_LOG_BACKUP_COUNT` | 保留的日志文件备份数 | `5` |
| **安全配置** | | |
| `SMILEX_ENABLE_TLS` | 是否启用 TLS | `false` |
| `SMILEX_TLS_CERT_PATH` | TLS 证书路径 | - |
| `SMILEX_TLS_KEY_PATH` | TLS 私钥路径 | - |
| `SMILEX_TLS_CA_CERT_PATH` | TLS CA 证书路径 | - |
| `SMILEX_ENCRYPTION_KEY` | 加密密钥（Base64） | - |
| `SMILEX_TOKEN_SECRET` | 令牌签名密钥 | - |

### 安全密钥生成

使用提供的工具脚本生成安全密钥：

```bash
uv run python scripts/generate_keys.py
```

生成的输出示例：
```
============================================================
SmileX Zenoh Gateway - 安全密钥生成工具
============================================================

🔐 生成的安全密钥：

加密密钥 (用于 AES-256-GCM):
SMILEX_ENCRYPTION_KEY=C04ZXO5d1mBlHBJi2vkvk/5pRAAurKZWVwnmKAF3xlU=

令牌密钥 (用于 HMAC-SHA256 签名):
SMILEX_TOKEN_SECRET=800fcf1a880ab550a851d489d27f06f9e3e2bdfa6c8d6ee9c88226460adf00fe

============================================================
⚠️  重要提示：
1. 请将以上密钥添加到你的 .env 文件中
2. 请妥善保管这些密钥，不要泄露
3. 生产环境请使用不同的密钥
============================================================
```

## 开发

### 运行测试

```bash
# 测试各个模块（待更新）
```

## 许可证

Apache License 2.0
