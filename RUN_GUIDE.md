# 尝尝咸淡 - 运行指南

## 项目结构

```
code/
├── backend/      # FastAPI 后端
│   ├── data/     # 食谱数据
│   ├── api/      # API 路由
│   ├── rag_modules/  # RAG 模块
│   ├── main.py   # FastAPI 主应用
│   ├── config.py # 配置文件
│   └── requirements.txt
└── frontend/     # Vue 3 前端
    ├── src/
    ├── index.html
    ├── package.json
    └── vite.config.js
```

## 前置要求

1. **Python 3.8+** - 用于后端
2. **Node.js 16+** - 用于前端
3. **SiliconFlow API Key** - 用于 LLM 调用

## 运行步骤

### 1. 配置后端环境变量

在 `backend` 目录下创建 `.env` 文件：

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，添加你的 SiliconFlow API Key：

```env
LLM_API_KEY=your_api_key_here
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动后端服务

```bash
uvicorn main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动

### 4. 安装前端依赖

打开新的终端窗口：

```bash
cd frontend
npm install
```

### 5. 启动前端开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 启动（Vite 默认端口）

## 访问应用

打开浏览器访问：`http://localhost:5173`

## API 文档

后端启动后，可以访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 主要 API 端点

- `GET /api/stats` - 获取知识库统计信息
- `POST /api/ask` - 提问接口
- `POST /api/search` - 按分类搜索菜品
- `GET /api/categories` - 获取支持的分类列表
- `GET /api/difficulties` - 获取支持的难度列表

## 注意事项

1. 首次运行后端时，会自动构建向量索引，这可能需要几分钟时间
2. 确保 `LLM_API_KEY` 已正确设置
3. 后端和前端需要同时运行才能正常使用
4. 如果修改了后端代码，FastAPI 会自动重载（--reload 模式）
5. 如果修改了前端代码，Vite 会自动热更新

## 开发模式

### 后端开发

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 前端开发

```bash
cd frontend
npm run dev
```

## 生产环境部署

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm run build
# 将 dist 目录部署到 Web 服务器
```

## 故障排除

### 后端启动失败

- 检查 Python 版本是否 >= 3.8
- 检查是否正确安装了所有依赖
- 检查 `.env` 文件是否存在且包含正确的 API Key
- 检查数据目录 `backend/data` 是否存在

### 前端启动失败

- 检查 Node.js 版本是否 >= 16
- 检查是否正确安装了依赖 `npm install`
- 检查端口 5173 是否被占用

### API 调用失败

- 确保后端服务正在运行
- 检查 CORS 配置是否正确
- 查看浏览器控制台和后端日志获取详细错误信息
