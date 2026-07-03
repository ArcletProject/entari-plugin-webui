# entari-plugin-webui

基于 Vite + Vue 3 + Element Plus 的 [Entari](https://github.com/ArcletProject/arclet-entari) 可视化管理面板。

## 功能特性

- **仪表盘** — 消息统计、运行状态一览（ECharts）
- **配置管理** — 可视化编辑所有插件配置，支持 YAML 源码与表单双模式
- **插件管理** — 查看/启用/停用/重载插件
- **插件市场** — 浏览、安装、卸载社区插件
- **实时日志** — WebSocket 流式日志查看，支持 ANSI 转义渲染
- **在线聊天** — 基于 Satori 协议的浏览器内聊天界面
- **扩展机制** — 其他插件可通过 `webui_extend` 注册菜单、页面、路由、国际化、权限
- **主题切换** — 明暗主题一键切换
- **会话管理** — 基于 Cookie 的登录会话，自动过期
- **登录限流** — 防暴力破解

## 安装

### pip

```bash
pip install entari-plugin-webui
```

### pdm

```bash
pdm add entari-plugin-webui
```

## 配置示例

在 `entari.yml` 中启用插件：

```yaml
plugins:
  server:
    port: 8765              # WebUI 服务端口
    path: "satori"
    direct_adapter: true
  database:
    name: .entari/database.db   # 统计数据用 SQLite
  webui: {}                     # 启动 WebUI 面板
```

完整字段说明：

| 字段 | 默认值 | 说明 |
|------|--------|------|
| `password` | `""` | 登录密码（远程部署必填，本地可省略） |
| `registry_url` | `""` | 插件市场地址 |
| `package_manager` | `""` | 包管理器（自动探测 pip/pdm/uv/poetry/rye/pipenv） |
| `session_ttl` | `43200` | 会话过期时间（秒，默认 12 小时） |
| `log_buffer_lines` | `5000` | 日志缓冲区行数 |
| `login_rate_limit` | `5/60s` | 登录频率限制 |

## 认证说明

- **本地部署**（`host=127.0.0.1/localhost/::1`）：自动免认证，无需密码即可登录
- **远程部署**：首次启动时自动生成随机 16 位密码并输出到控制台日志

## 故障恢复

忘记密码时，删除配置中的 `plugins.webui.password` 字段（或置空），重启后即重新生成新密码：

```yaml
plugins:
  webui: {}
  # password 字段可删除或留空
```

## 扩展开发

其他 Entari 插件可通过 `webui_extend` 注册前端扩展，无需修改本插件源码。

```python
from entari_plugin_webui.core.extension import webui_extend

ext = webui_extend("my_plugin")

# 注册侧栏菜单
ext.add_menu("my_plugin.name", "mdi:account", "/extension/my_plugin")

# 注册 iframe 页面
ext.add_page("my_plugin", "my_plugin.name", "mdi:account",
             "http://127.0.0.1:3000/", permission="my_plugin.access")

# 注册后端 API 路由
ext.add_route("/api/my-plugin/hello", ["GET"], my_handler, permission="my_plugin.access")

# 注册国际化文案
ext.add_i18n("zh-CN", "my_plugin.name", "我的插件")
ext.add_i18n("en-US", "my_plugin.name", "My Plugin")

# 注册权限项
ext.add_permission("my_plugin.access", "my_plugin.permission.access")
```

`WebUIExtension` 方法总览：

| 方法 | 参数 | 说明 |
|------|------|------|
| `add_menu` | `label_key, icon, path, order, badge_key, children` | 添加侧栏菜单项 |
| `add_page` | `key, label_key, icon, component_url, permission` | 添加 iframe 页面 |
| `add_route` | `path, methods, handler, permission` | 添加后端 HTTP 路由 |
| `add_websocket_route` | `path, handler, permission` | 添加后端 WebSocket 路由 |
| `add_i18n` | `locale, key, value` | 添加国际化翻译 |
| `add_permission` | `key, label_key` | 添加权限定义 |

## 风险须知

> [!WARNING]
> - 扩展页面以 **iframe 沙箱** 加载，与主面板隔离运行
> - 扩展来源 **仅限本机已安装的插件**，不支持加载外部站点
> - 各扩展通过 `postMessage` 与主面板通信，无法直接操作 DOM 或获取全局状态
> - 安装插件市场中的第三方插件前，请自行评估其安全性
