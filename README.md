# 消息聚合推送平台 🚀
<div align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-blue.svg" alt="version">
  <img src="https://img.shields.io/badge/Python-3.9+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-teal.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Vue-3.3+-brightgreen.svg" alt="Vue">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="license">

  企业级消息推送平台 | 支持钉钉 & 飞书机器人
</div>

企业级消息推送平台，支持钉钉和飞书机器人，提供多渠道管理、任务调度、发送记录追踪等功能。

## ✨ 功能特性

- **多平台支持**：同时支持钉钉和飞书自定义机器人
- **渠道管理**：集中管理所有机器人的AccessToken和密钥
- **任务管理**：创建发送任务，关联多个渠道
- **消息发送**：支持纯文本消息发送
- **发送记录**：完整的日志追踪
- **数据统计**：发送趋势、成功率统计

## 🛠️ 技术栈

### 后端
- Python 3.9+
- FastAPI
- SQLAlchemy (异步)
- MySQL
- JWT认证

### 前端
- Vue 3
- Element Plus
- Vite
- Axios
- ECharts

## 📦 快速开始

### 环境要求
- Python 3.9+
- MySQL 5.7+
- Node.js 16+
- pnpm/npm

### 后端部署

1. **克隆项目**
```bash
git clone https://github.com/zixi666/Message-PushConverge.git
cd Message-PushConverge

2. **后端启动**
```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

3. **前端启动**
```bash
# 进入前端目录
cd web

# 安装依赖
npm install
# 或使用 pnpm
pnpm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
