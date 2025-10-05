<!-- markdownlint-disable MD033 MD041 -->
<h1 align="center">Entari Plugin WebUI</h1>

<p align="center">
  <strong>图形化 Entari 实例管理面板 | Graphical Entari Instance Manager</strong>
</p>

<p align="center">
  <a href="https://github.com/ArcletProject/entari-plugin-webui/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"/>
  </a>
  <a href="https://github.com/ArcletProject/Entari">
    <img src="https://img.shields.io/badge/Powered%20by-Entari-ff2072.svg" alt="Powered by Entari"/>
  </a>
</p>

🌟 特性一览 Feature Matrix

| 模块 | 状态 | 说明 |
| ---- | :--: | ---- |
| 用户认证 | ✅ | 登录 / 登出 / Token 鉴权，默认管理员账号自动初始化 |
| 实例管理 | ✅ | 创建、删除、启动、停止；支持 JSON 配置实时编辑与热重载 |
| 插件系统 | ✅ | 本地 & 远程插件列表；加载、卸载、热重载；在线代码编辑器 |
| 控制台日志 | ✅ | WebSocket 实时推送，ANSI 高亮，自动滚动，清空 / 重连 |
| 系统配置 | ✅ | 可视化编辑 YAML（基础配置 + 插件配置），一键保存生效 |
| 社区扩展 | ✅ | 社区项目展示、贡献者头像墙、插件市场入口 |
| UI/UX | ✅ | 暗黑模式、响应式布局、表单校验、操作反馈、空状态提示 |
| 协议支持 | ✅ | 已接入 Satori、Console、GitHub、OneBot 等主流协议 |

---

## 🚀 快速开始 Quick Start

### 1. 安装插件
```bash
# 在 Entari 项目根目录执行
pip install entari-plugin-webui
```

### 2. 启用插件
`config.yaml` 中追加：
```yaml
  database:
    type: sqlite
    name: database.db
    driver: aiosqlite
  server:
    host: 127.0.0.1
    port: 8080
    adapters:
      - $path: nekobox.main:NekoBoxAdapt
        uin: 自己的账号
        sign_url: https://sign.lagrangecore.org/api/sign/30366
        protocol: remote
        log_level: INFO
        use_png: false
  webui: {}
```

### 3. 启动 Entari
```bash
entari run
```
浏览器访问 [http://localhost:8080](http://localhost:8080) 即可。

---

## 🛠️ 技术栈 Tech Stack

| 方向 | 技术 |
| ---- | ---- |
| 后端 | Python 3.10+ · Entari · FastAPI |
| 前端 | Vue 3 · Vite · TypeScript · Element-Plus · SCSS |
| 实时通信 | WebSocket (原生) |
| 包管理 | pnpm |
| 代码规范 | ESLint · Prettier · Husky · lint-staged |

---

## 📝 代码规范

- 前端：遵守 `@vue/eslint-config-typescript` + `prettier`
- 后端：遵守 `black` 格式化 + `ruff` 静态检查
- 提交前自动触发 `lint-staged`，不合规无法提交

---

## 🤝 贡献指南

1. Fork 本仓库
2. 新建分支 (`git checkout -b feat/xxx`)
3. 提交合规 Commit (`git commit -m 'feat: add xxx'`)
4. 推送分支 (`git push origin feat/xxx`)
5. 提交 Pull Request

---

## 📄 开源协议

[MIT](./LICENSE) © 2025 ArcletProject

---

## 🔗 相关链接

- [Entari 主仓库](https://github.com/ArcletProject/Entari) 
- [Entari 文档](https://github.com/ArcletProject/Entari/tree/main/docs)
- [Satori 协议](https://satori.js.org/)

: [Entari Releases](https://github.com/ArcletProject/Entari/releases)  
: [entari-plugin-server · PyPI](https://pypi.org/project/entari-plugin-server/)
```
