# Entari Plugin WebUI

基于 **Nuxt 3 + Naive UI** 的 Entari 可视化管理面板。

## 功能特性

- 🎛️ **仪表盘** - 实时统计数据展示，包括消息量、运行时长、插件状态
- 🧩 **插件管理** - 启用/禁用插件、配置编辑、热重载
- 🛒 **插件市场** - 浏览和安装社区插件
- ⚙️ **配置管理** - 可视化编辑 entari.yml 配置文件
- 📜 **实时日志** - WebSocket 推送的实时日志查看
- 🔐 **安全认证** - 本地部署免认证，远程部署 JWT 认证
- 🔌 **扩展接口** - 允许其他插件注册路由和菜单

## 安装

```bash
pip install entari-plugin-webui
```

或使用 PDM：

```bash
pdm add entari-plugin-webui
```

## 配置

在 `entari.yml` 中添加：

```yaml
plugins:
  # WebUI 依赖的插件
  database:
    type: sqlite
    name: data/entari.db
  
  server:
    host: 127.0.0.1  # 本地部署无需认证
    # host: 0.0.0.0  # 远程部署需要认证
    port: 5150
  
  # 启用 WebUI
  webui: {}
```

## 认证说明

- **本地部署** (`host: 127.0.0.1` 或 `localhost`)：无需认证，直接访问
- **远程部署** (`host: 0.0.0.0` 或其他 IP)：
  - 首次启动自动生成随机密码
  - 密码会输出到日志并保存到配置文件
  - 支持 JWT 双 token 机制

## Docker 部署

```bash
# 构建镜像
docker build -t entari-webui .

# 运行
docker run -d \
  -p 5150:5150 \
  -v $(pwd)/entari.yml:/app/entari.yml:ro \
  -v $(pwd)/data:/app/data \
  entari-webui
```

或使用 docker-compose：

```bash
docker-compose up -d
```

## 开发

### 前置要求

- Python >= 3.10
- Node.js >= 18
- PDM

### 本地开发

```bash
# 安装 Python 依赖
pdm install

# 安装前端依赖
cd frontend && npm install

# 启动前端开发服务器
npm run dev

# 另一个终端启动后端
pdm run python -m arclet.entari
```

### 构建

```bash
# 构建前端
pdm run build-frontend

# 构建 Python wheel
pdm build

# 或一键构建
pdm run build-all
```

## 插件扩展

其他插件可以向 WebUI 注册路由和菜单：

```python
from entari_plugin_webui import webui_extend, MenuItem

# 获取扩展实例
ext = webui_extend("my-plugin")

# 注册菜单
ext.add_menu(
    label="我的功能",
    icon="mdi:star",
    path="/my-plugin",
    order=50
)

# 注册路由
@ext.add_route("/api/my-plugin/data", ["GET"])
async def my_handler(request):
    return {"data": "hello"}
```

## 项目结构

```
entari-plugin-webui/
├── frontend/                    # Nuxt 3 前端项目
│   ├── pages/                   # 页面组件
│   ├── components/              # 通用组件
│   ├── composables/             # 组合式函数
│   ├── layouts/                 # 布局组件
│   └── middleware/              # 路由中间件
│
├── src/entari_plugin_webui/     # Python 后端
│   ├── api/                     # API 路由
│   ├── core/                    # 核心逻辑
│   ├── models/                  # 数据库模型
│   ├── utils/                   # 工具函数
│   ├── static/                  # 静态资源
│   └── frontend/                # 前端构建产物
│
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## 许可证

MIT License
