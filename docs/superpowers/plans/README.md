# Entari Plugin WebUI 重设计 — 实施计划索引

> 设计稿：`docs/superpowers/specs/2026-06-30-webui-redesign-design.md`
> 执行方式：建议 subagent-driven-development；每 phase 内任务按 TDD 顺序、频繁提交。
> 全局约定：后端测试 `pdm run pytest tests/<path> -v`；后端 lint `pdm run format && pdm run lint && pdm run typecheck`；前端 `cd frontend && npm run lint && npm run build`。

各 phase 顺序依赖前后；每个 phase 完成后应能独立运行测试通过、可提交。

| Phase | 内容 | 前置 |
|-------|------|------|
| [01](./2026-06-30-phase-01-foundation.md) | 项目骨架、依赖、配置模型、插件入口（health + SPA fallback 占位）、构建脚本、lint 配置 | — |
| [02](./2026-06-30-phase-02-auth.md) | SessionStore、PBKDF2、CSRF、登录节流、本地/远程判定、`/api/auth/*`、审计日志 | 01 |
| [03](./2026-06-30-phase-03-plugins.md) | plugin_service、`/api/plugins/*`、`/api/menus` | 01、02 |
| [04](./2026-06-30-phase-04-config.md) | config_service、`/api/config/*`、JSON Schema 生成 | 01、02 |
| [05](./2026-06-30-phase-05-stats.md) | MessageStat 模型、DB 建表、stats_service、`/api/stats`、SendResponse 监听 | 01、02 |
| [06](./2026-06-30-phase-06-market.md) | market_service、`/api/market/*`、registry 回退、pip 任务 | 01、02 |
| [07](./2026-06-30-phase-07-logs.md) | LogRingBuffer、loguru sink、`/ws/logs` | 01、02 |
| [08](./2026-06-30-phase-08-extensions.md) | WebUIExtension 注册中心、`/api/extensions/manifest`、WS 路由挂载修复、i18n/permissions | 01、02、03 |
| [09](./2026-06-30-phase-09-frontend-foundation.md) | Vite+Vue3+Element Plus 骨架、router 守卫、stores、axios、useBackendHealth、layouts、Login | 01–08 全部 |
| [10](./2026-06-30-phase-10-schema-form-and-views.md) | SchemaForm 树、DualConfigEditor、Dashboard/Plugins/Market/Config/Logs 页面、ExtensionPanelHost | 09 |
| [11](./2026-06-30-phase-11-release.md) | 完整测试套件补齐、CI、Dockerfile、docker-compose、README、发布 | 10 |

## 执行后交接

全部 phase 完成后，运行 `pdm run format && pdm run lint && pdm run typecheck && pdm run pytest -q && cd frontend && npm run lint && npm run build`，全绿即视为完成。