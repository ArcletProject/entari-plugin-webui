# Settings 页面合并设计

## 背景

目前 WebUI 的"配置管理"（`/config`）和"插件管理"（`/plugins`）是两个独立页面：
- `/config`：左侧菜单选择基础配置 / 适配器 / 插件配置，右侧显示 DualConfigEditor。
- `/plugins`：表格展示插件列表，提供启用开关、重载、详情、抽屉式配置编辑。

用户希望将两者合并为一个统一的设置页面，参考 koishi-webui 的插件配置页布局，并在元数据字段上做特殊适配。

## 目标

1. 合并 `/config` 与 `/plugins` 为新的 `/settings` 页面。
2. 左侧菜单保持"基础配置"、"适配器"、"插件"三个区域，且默认全部展开。
3. 右侧顶部固定展示插件名称、描述、版本与操作栏（启用开关、重载、详情）。
4. 将插件相关元数据字段作为常规表单外的特殊设置项渲染。

## 方案

### 路由

- 新增 `/settings`。
- `/config` 与 `/plugins` 重定向到 `/settings`。
- 菜单合并为单一入口 `menu.settings`（显示为"设置"）。

### 页面布局

```
+-------------------------------------------------------------+
|  设置                                                         |
+--------------------------------+-----------------------------+
|  左侧边栏                      |  右侧主内容                  |
|  [搜索框]                      |  +-------------------------+|
|                                |  | 名称 / 描述 / 版本 / 操作 ||
|  基础配置                      |  +-------------------------+|
|  适配器                        |  +-------------------------+|
|  插件                          |  | 元数据设置（特殊卡片）    ||
|    ├─ 插件全局                 |  +-------------------------+|
|    ├─ plugin-a                 |  +-------------------------+|
|    ├─ plugin-b                 |  | 常规配置表单              ||
|    └─ ...                      |  +-------------------------+|
+--------------------------------+-----------------------------+
```

### 左侧边栏

- 固定宽度 260px。
- 顶部搜索框，按插件名过滤。
- 三个分组默认展开：
  - `basic`：基础配置
  - `adapters`：适配器
  - `plugins`：插件
    - `plugins`（全局插件配置）
    - 所有已加载插件，按插件名排列

### 顶部信息栏

针对插件项展示：
- 插件名称
- 描述（tooltip 或副标题）
- 版本
- 启用开关（仅非 static 插件可操作）
- 重载按钮
- 详情按钮（弹出 PluginDetailModal）

针对基础配置 / 适配器 / 插件全局仅展示标题与保存按钮。

### 元数据特殊处理

定义全局元数据字段集合：

```ts
const META_KEYS = [
  '$prefix',
  '$files',
  '$prelude',
  '$disable',
  '$priority',
  '$filter',
  '$optional',
];
```

拿到 schema 后拆分为：
- `metaSchema`：仅保留 `META_KEYS` 中的属性。
- `configSchema`：移除 `META_KEYS` 后的剩余属性。

#### 渲染方式

- 用独立组件 `MetaSettings.vue` 渲染 `metaSchema`。
- 该组件基于现有 `SchemaForm` 递归渲染，但对不同字段做针对性 UI 适配：
  - `$disable` / `$filter`：字符串输入 + 表达式说明文案。
  - `$priority`：数字输入框。
  - `$optional`：开关。
  - `$prefix`：对象数组，每项包含 key 输入与 plugins 输入（字符串或字符串数组）。
  - `$files` / `$prelude`：字符串数组输入框。
- 元数据卡片使用与常规配置不同的背景色 / 边框，便于区分。

### 数据流

#### Store

新建 `frontend/src/stores/settings.ts`：
- `pluginList`：从 `/api/plugins` 加载的插件列表。
- `currentSection`：当前选中的 section key，例如 `'basic'`、`'adapters'`、`'plugins'`、`'plugins:xxx'`。
- `schema` / `data`：当前选中的 schema 与数据。
- `loading`：加载状态。

#### 加载逻辑

选中项变化时：
1. 若选中插件 section，从 `pluginList` 中补充元信息。
2. 并发请求：
   - `GET /api/config/{section}/schema`
   - `GET /api/config/{section}`
3. 用 `META_KEYS` 拆分 schema，合并数据到 `metaData` 与 `configData`。

#### 保存逻辑

- `basic` / `adapters` / `plugins`：
  - `PUT /api/config/{section}`，body 为 `{ data: mergedData }`。
- 单个插件 `plugins:{id}`：
  - `PUT /api/plugins/{id}/config`，body 为 `{ config: mergedData }`。

其中 `mergedData = { ...metaData, ...configData }`。

#### 操作按钮

- 启用/停用：`POST /api/plugins/{id}/toggle`
- 重载：`POST /api/plugins/{id}/reload`
- 详情：复用 `PluginDetailModal`

### 文件变更

- 新增：
  - `frontend/src/views/Settings.vue`
  - `frontend/src/stores/settings.ts`
  - `frontend/src/components/settings/MetaSettings.vue`
  - `frontend/src/components/settings/SettingsSidebar.vue`
  - `frontend/src/components/settings/PluginHeader.vue`
- 修改：
  - `frontend/src/router/index.ts`：新增 `/settings`，`/config` 与 `/plugins` 重定向。
  - `frontend/src/i18n/zh-CN.ts`：新增 `menu.settings`，可能调整 `menu.config` / `menu.plugins`。
  - `frontend/src/stores/menu.ts`：更新内置菜单。
  - `src/entari_plugin_webui/api/menus.py`：更新 `BUILTIN_MENUS`。
- 删除或保留（可选）：
  - `frontend/src/views/Config.vue` 与 `frontend/src/views/Plugins.vue` 可删除或保留为简单重定向组件。

## 兼容性

- 后端 `/api/config/*` 与 `/api/plugins/*` 接口不变。
- 仅前端路由与菜单调整，后端无需改动。

## 验收标准

- [ ] `/settings` 可访问，`/config` 与 `/plugins` 自动跳转。
- [ ] 左侧显示基础配置 / 适配器 / 插件，插件分组默认展开。
- [ ] 选中插件后顶部展示名称、描述、版本、启用开关、重载、详情。
- [ ] `$prefix` / `$files` / `$prelude` 在"插件全局"中以元数据卡片形式展示。
- [ ] `$disable` / `$filter` / `$priority` / `$optional` 在单个插件中以元数据卡片形式展示。
- [ ] 常规业务配置表单不再包含上述元数据字段。
- [ ] 保存后配置正确写入后端，启用/重载按钮工作正常。
- [ ] `npm run build` 与 `pytest` 通过。
