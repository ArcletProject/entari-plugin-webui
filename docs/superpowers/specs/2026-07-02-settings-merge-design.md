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
- 支持 `/settings?section=plugins:foo` 直接定位到指定 section。

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

#### 搜索过滤行为

- 输入关键词时，左侧菜单只显示名称匹配的插件项；基础配置 / 适配器 / 插件全局始终保留。
- 过滤不改变当前右侧选中项，仅隐藏不匹配的菜单项。
- 清空搜索框后恢复完整插件列表。

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

#### 字段归属

| 字段 | 出现位置 | 说明 |
|------|---------|------|
| `$prefix` | 插件全局 | 插件前缀分组配置 |
| `$files` | 插件全局 | 额外加载的配置文件路径列表 |
| `$prelude` | 插件全局 | 预加载插件列表 |
| `$disable` | 单个插件 | 是否禁用该插件的表达式 |
| `$priority` | 单个插件 | 插件加载优先级 |
| `$filter` | 单个插件 | 插件过滤器表达式 |
| `$optional` | 单个插件 | 该插件是否为可选依赖 |

#### 渲染方式

- 用独立组件 `MetaSettings.vue` 渲染 `metaSchema`。
- 该组件核心作用是 **视觉差异化**（不同背景色/边框）和 **针对性文案提示**。
- 大部分字段可直接复用现有 `SchemaForm` 递归渲染：
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
- `metaData` / `configData`：拆分后的元数据与业务配置数据；`DualConfigEditor` 绑定 `configSchema` 和 `configData`，不包含元数据字段。
- `loading`：加载状态。
- `isDirty`：当前表单是否有未保存修改；`metaData` 和 `configData` 的任意修改均置为 `true`。
- `savePending`：保存中状态。

#### 加载逻辑

选中项变化时：
1. 若 `isDirty` 为 true，弹窗提示用户保存或放弃修改。
2. 若选中插件 section，从 `pluginList` 中补充元信息。
3. 并发请求：
   - `GET /api/config/{section}/schema`
   - `GET /api/config/{section}`
4. 用 `META_KEYS` 拆分 schema 与 data，重置 `isDirty = false`。
   - 对于 `basic` / `adapters`，`META_KEYS` 不在其 schema 中，`metaSchema` 为空对象，`MetaSettings.vue` 不渲染，右侧仅显示常规配置表单。

#### 保存逻辑

- `basic` / `adapters` / `plugins`：
  - `PUT /api/config/{section}`，body 为 `{ data: mergedData }`。
- 单个插件 `plugins:{id}`：
  - 统一使用 `PUT /api/plugins/{id}/config`，body 为 `{ config: mergedData }`。
  - 已确认 `EntariConfig.instance.plugin[key]` 与 `EntariConfig.instance.data["plugins"][key]` 指向同一对象，因此该端点与旧的 `PUT /api/config/plugins:{id}` 在数据落盘上等价。

其中 `mergedData = { ...metaData, ...configData }`。

保存成功后：
- `ElMessage.success("设置已保存")`
- `isDirty = false`

#### 操作按钮

- 启用/停用：`POST /api/plugins/{id}/toggle`
- 重载：`POST /api/plugins/{id}/reload`
- 详情：复用 `PluginDetailModal`

#### 错误处理

- API 请求失败时显示 `ElMessage.error("加载失败：...")` 或 `ElMessage.error("保存失败：...")`。
- 保存按钮在 `savePending` 期间显示加载状态并禁用。

### 文件变更

- 新增：
  - `frontend/src/views/Settings.vue`
  - `frontend/src/stores/settings.ts`
  - `frontend/src/components/settings/MetaSettings.vue`
  - `frontend/src/components/settings/SettingsSidebar.vue`
  - `frontend/src/components/settings/PluginHeader.vue`
- 修改：
  - `frontend/src/router/index.ts`：新增 `/settings`，`/config` 与 `/plugins` 重定向；支持 `?section=` 查询参数。
  - `frontend/src/i18n/zh-CN.ts`：新增 `menu.settings`，可能调整 `menu.config` / `menu.plugins`。
  - `frontend/src/stores/menu.ts`：更新内置菜单。
  - `src/entari_plugin_webui/api/menus.py`：更新 `BUILTIN_MENUS`。
  - `frontend/src/views/Dashboard.vue`：更新"插件管理"、"配置管理"按钮链接到 `/settings`。
- 删除或保留（可选）：
  - `frontend/src/views/Config.vue` 与 `frontend/src/views/Plugins.vue` 可删除或保留为简单重定向组件。

### keep-alive

Settings 页面不需要 `keep-alive`（每次切换 section 需要重新加载状态），`App.vue` 中 `keep-alive include="Chat,Logs"` 不变。

## 兼容性

- 后端 `/api/config/*` 与 `/api/plugins/*` 接口不变。
- 已验证 `EntariConfig.instance.plugin[key]` 与 `EntariConfig.instance.data["plugins"][key]` 为同一对象，保存端点切换不会导致数据分离。

## 验收标准

- [ ] `/settings` 可访问，`/config` 与 `/plugins` 自动跳转。
- [ ] `/settings?section=plugins:foo` 可直接定位到对应 section。
- [ ] 左侧显示基础配置 / 适配器 / 插件，插件分组默认展开。
- [ ] 搜索框可按插件名过滤，清空后恢复完整列表。
- [ ] 选中插件后顶部展示名称、描述、版本、启用开关、重载、详情。
- [ ] `$prefix` / `$files` / `$prelude` 在"插件全局"中以元数据卡片形式展示。
- [ ] `$disable` / `$filter` / `$priority` / `$optional` 在单个插件中以元数据卡片形式展示。
- [ ] 常规业务配置表单不再包含上述元数据字段。
- [ ] 切换 section 时若存在未保存修改，给出提示。
- [ ] 保存后配置正确写入后端，启用/重载按钮工作正常。
- [ ] `npm run build` 与 `pytest` 通过。
