# ERPNext（v16）面向 AI Agent 的开发手册（COS 项目版）

> 适用范围：本仓库 `apps/cos`（分支：`version-16-beta`），运行在 Frappe/ERPNext v16 的 bench 环境中。  
> 目标读者：负责“读代码→定位落点→实现变更→交付（fixtures/patches）→回归验证”的 AI agent。

---

## 0. 关键约束（必须遵守）

- **输出与代码注释语言**：中文（含提交信息建议）。
- **先读文档再动手**：优先阅读 `docs/`、`README.md`、`print_format/README.md`，并对照官方 Frappe/ERPNext 文档（见文末参考）。
- **环境变量与敏感信息**：
  - `.env` 仅本地使用，可能包含密钥，**禁止提交**；提交只保留 `.env.example`。
  - 任何 URL/token **从环境变量读取**，不要硬编码到代码/文档/fixtures/提交信息。
- **协议选择（本地 hosts→127.0.0.1 且无 TLS）**：访问 `cos-dev.junhai.work` 必须用 **HTTP**（`http://cos-dev.junhai.work`），不要用 HTTPS。
- **格式化/规范**：以 `.editorconfig` + `pre-commit` 为准；Python/JS **主要使用 tab 缩进**；JSON（Doctype schema）使用空格缩进且通常不强制末尾换行。
- **安全**：对外 API 必须 `@frappe.whitelist()` 且做权限与输入校验；默认避免手动 `frappe.db.commit()`（需要时写清原因并保证幂等）。

---

## 1. 当前系统与仓库的系统性理解

### 1.1 运行形态（bench / apps / site）

- **项目类型**：Frappe 自定义 App（`cos`），安装到 bench 的站点上，与 ERPNext/Frappe v16 同时运行。
- **安装方式**（仓库 `README.md`）：

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16-beta
bench install-app cos
```

- **版本与运行时**（v16 迁移说明要点）：
  - Python：v16 常见要求为 **Python 3.14+**
  - Node：v16 常见要求为 **Node 24+**
  - Desk/导航：v16 引入更强的 Workspace/Sidebar 机制，升级时要关注自定义 Workspace/Sidebar 的行为变化。

### 1.2 仓库顶层结构（交付物视角）

- **`cos/`**：App 主体（Python 包、DocType、controllers/utils、public 资源、fixtures、patches 等）。
- **`print_format/`**：打印模板（`template.html` + `styles.css` + `README.md`），用于 Print Format 交付与复用。
- **`importable_data/`**：可导入基础数据（CSV：Brand、Item Group、物料属性字典、Workflow State 等）。
- **工程质量**：
  - `.pre-commit-config.yaml`：ruff / prettier / eslint 等预提交检查
  - `pyproject.toml`：依赖、ruff 配置（`indent-style=tab`、`line-length=110`）
  - `.editorconfig`：缩进/换行/JSON 格式约定

---

## 2. COS 应用架构与扩展点地图（你要先理解这些再写代码）

### 2.1 模块划分（Desk 中的业务域）

`cos/modules.txt`：

- `COS`
- `COS Share`：通用能力/共享能力
- `COS Stock`：物料/库存相关扩展
- `COS Accounts`：财税/公司信息相关扩展
- `COS Logto`：Logto 社交登录集成

### 2.2 总挂载点：`cos/hooks.py`

AI agent 需要把 `hooks.py` 当作“系统扩展点目录”来读：

- **资源注入**：`app_include_css`、`app_include_js`
- **标准 DocType 的 JS 注入**：`doctype_js`（例如 `Item`、`Item Group`、`Company`、发票税务登记脚本）
- **DocType 事件钩子**：`doc_events`
  - `New Item Request.before_save`：计算参数指纹（MD5）
  - `Item.before_insert`：自动设置物料编码（命名系列/手动编码）
  - `Project.before_insert`：自动项目编码
  - `Address.before_save/validate`：地址 display 逻辑
  - `Sales Invoice / Purchase Invoice.before_cancel/on_trash`：税务登记引用联动处理（避免动态链接校验拦截流程）
- **方法覆写**：`override_whitelisted_methods`
  - 覆写 `frappe.desk.search.search_link` 为自定义搜索（兼容升级：按原函数 signature 过滤参数）
- **登录会话钩子**：`on_login` / `on_session_creation`
  - Logto 登录后自动绑定角色 `Logto User`
- **安装钩子**：`before_install` / `after_install`（例如复制报表模板、初始化 UOM）
- **交付策略**：`fixtures`（按模块/名称过滤导出，保证安装后配置可复现）

### 2.3 典型实现案例（用于理解“为什么这样做”）

- **覆写搜索 `search_link` 的兼容写法**：通过 `inspect.signature()` 仅保留原函数接受的参数，避免 Frappe 升级新增/删减参数导致崩溃。
- **New Item Request 参数指纹（MD5）**：仅对 `join_to_hash=1` 且非 `Format` 的参数参与 hash；标准化后拼接 `key=value|...` 生成 `unique_code`。
- **发票取消/删除与 Tax Registry 的关系**：
  - 取消前：对发票设置 `ignore_linked_doctypes += ["Tax Registry"]` 与 `doc.flags.ignore_links=True`，并清空 `custom_tax_registry_reference`，避免 Tax Registry 动态链接阻断系统取消流程。
  - 删除前：只尽力清空引用字段，不强行联动删除 Tax Registry（由系统链接校验决定是否允许删除）。
- **Item 自动编码**：
  - 自动模式：从 `Item Group.custom_code` 拼出 `naming_series = "<code>.####"`
  - 手动模式：当 `naming_series == "{custom_unique_item_name}"` 时用 `custom_unique_item_name` 直接作为 `doc.name`，并设置 `doc.flags.name_set=True` 跳过命名系列。

### 2.4 本项目自定义 DocType 清单（按模块，理解业务边界用）

> 仅列出本仓库 `cos/**/doctype/**` 下定义的自定义 DocType（不含 fixtures 导出的 Custom Field/Property Setter 等）。

#### COS Share

| DocType | 类型 | 主要用途 |
|---|---|---|
| `Executive Standard` | 主数据 | 执行/技术标准维护（编号/名称/类型/状态/附件等），供物料等引用 |
| `Source Type` | 主数据 | “来源/类型”字典，可关联目标 DocType，用于分类/筛选/链接类型约束 |
| `External Link` | 主数据 | 外部链接入口（标题/URL/打开方式等），用于导航与资源集成 |

#### COS Stock

| DocType | 类型 | 主要用途 |
|---|---|---|
| `New Item Request` | 可提交单据 | 新物料申请/建码入口：按参数模板收集参数并计算 `unique_code` 指纹 |
| `Item Parameter Template` | 主数据 | 参数模板：定义参数集合、默认值与约束（绑定物料组） |
| `Item Parameter Template Definition` | 子表 | 参数模板明细：参数类型/默认值/是否参与 hash/Doctype 约束等 |
| `Item Parameter Definition` | 子表 | 申请单参数明细：参数值、绑定字段、是否参与 hash 等 |
| `Item Base Name` | 树形主数据 | 物料基础名称树（分层管理、规范命名） |
| `Item Material` / `Item Color` / `Item Surface` | 主数据 | 物料属性字典（材料/颜色/表面处理等），供物料引用 |

#### COS Accounts

| DocType | 类型 | 主要用途 |
|---|---|---|
| `Tax Registry` | 可提交单据 | 税务登记/发票税额汇总（含明细与会计科目关联） |
| `Tax Registry Item` | 子表 | 税务登记明细（Dynamic Link 指向发票，记录税号/日期/税额等） |

#### COS Logto

| DocType | 类型 | 主要用途 |
|---|---|---|
| `Logto User Settings` | Single（单例设置） | Logto 集成相关设置与辅助字段 |

---

## 3. AI Agent 的“落点选择”规则（决定写哪里）

### 3.1 DocType 结构约定（强制）

DocType 目录保持标准化（规则文件已定义）：

- `cos/<module>/doctype/<doctype>/<doctype>.json`：schema
- `cos/<module>/doctype/<doctype>/<doctype>.py`：controller（校验/事件/服务端逻辑）
- `cos/<module>/doctype/<doctype>/<doctype>.js`：客户端脚本（表单交互）
- `cos/<module>/doctype/<doctype>/test_<doctype>.py`：测试（如适用）

命名：

- DocType 名称用 PascalCase（例如 `New Item Request`）
- 文件夹/文件名用 snake_case（例如 `new_item_request`）

### 3.2 后端逻辑落点优先级

- **优先**：对应 DocType 的 controller（当逻辑强绑定该 DocType 生命周期/字段校验）。
- **其次**：`cos/<module>/utils/`（可复用、可被 hooks/doc_events 调用的纯逻辑/工具函数）。
- **再次**：`cos/<module>/controllers/`（更像“服务层/接口层”的入口逻辑）。
- **最后**：`hooks.py` 只做“挂载”，不堆业务逻辑。

### 3.3 前端（Desk）脚本落点

- **DocType 表单行为**：`frappe.ui.form.on('<DocType>', {...})`
- **标准 DocType 的增强脚本**（例如 `Item`/`Company`）：放 `cos/public/js/doctype/`，并在 `cos/hooks.py` 的 `doctype_js` 显式注入。
- **国际化**：用户可见文本使用 `__('...')`。
- **与服务端交互**：优先 `frappe.call` 调白名单方法；参数显式、可校验、可追踪。

---

## 4. 交付物选择：什么时候用 fixtures / patches / 纯代码

### 4.1 何时用 fixtures（配置型变更）

典型属于 fixtures 的内容（本项目 `hooks.py` 已配置导出过滤）：

- Client Script / Server Script / Report
- Print Format / Print Style / Letter Head / Terms and Conditions
- Custom Field / Property Setter / Custom DocPerm / Role 等
- 一些主数据型 DocType 的记录（如 `Item Parameter Template`、`Source Type`、`External Link`）

操作要点（AI agent checklist）：

- 变更发生在站点数据库（Customize Form / Print Format / Scripts）→ **需要导出 fixtures**
- 不要把敏感信息写入 fixtures（尤其是 URL/token/secret）

### 4.2 何时用 patches（迁移/修复历史数据）

当你需要：

- 修复/迁移已有数据（重命名、补默认值、修复脏数据）
- 做一次性、可回放、可幂等的变更

则创建 patch，并写入 `cos/patches.txt`（`pre_model_sync` 或 `post_model_sync`）。

Patch 必须：

- **幂等**（重复执行不会造成二次破坏）
- **可记录**（必要时写日志/注释说明）
- **避免大事务**（分批处理，避免锁表过久）

### 4.3 纯代码变更（不涉及站点配置/历史数据）

例如：

- 新增 utils/controller 方法
- 新增 hooks 挂载点
- 调整 DocType controller 校验逻辑

一般不需要 patch/fixtures（除非同时修改了配置或历史数据）。

---

## 5. 安全、权限、事务、数据库（AI agent 防呆红线）

- **白名单不是默认**：只有前端/外部需要调用的方法才加 `@frappe.whitelist()`。
- **权限校验必须做**：至少 `frappe.has_permission(...)` / `frappe.only_for(...)`，并对输入做类型/空值/范围校验。
- **数据库访问**：优先 `frappe.get_doc` / `frappe.db.get_value/set_value` / `frappe.get_all`；避免裸 SQL（必要时参数化）。
- **事务**：
  - 默认避免 `frappe.db.commit()`；让请求生命周期自然提交。
  - 只有在“登录/集成落库”等明确场景才考虑 commit，并在代码注释里说明理由与幂等策略（本仓库 Logto 登录钩子里有 commit 的实践）。

---

## 6. 常用开发流程（AI agent 标准作业 SOP）

### 6.0 常用 bench 命令与调试入口（把“操作”标准化）

> 下面命令通常在 bench 根目录执行（即 `frappe-bench/`）。`<site>` 替换为你的站点名。

```bash
# 启动开发（进程：web、socketio、watch 等）
bench start

# 构建前端资源（改了 public js/css 时常用）
bench build

# 清缓存（改了脚本/翻译/配置后常用）
bench --site <site> clear-cache
bench --site <site> clear-website-cache

# 迁移：同步 schema、执行 patches、同步 fixtures 等
bench --site <site> migrate

# 导出 fixtures（按 hooks.py: fixtures 的 dt + filters）
bench --site <site> export-fixtures

# 进入交互式控制台（排查数据、快速验证逻辑）
bench --site <site> console

# 执行某个 Python 函数（适合一次性校验/小脚本）
bench --site <site> execute "cos.some.module.method" --kwargs "{'a': 1}"

# 运行测试（仅跑 cos 应用）
bench --site <site> run-tests --app cos
```

### 6.1 新增/修改字段（Custom Field / Property Setter）

- 如果是对标准 DocType（如 `Item`）加字段：通常会落到 **Custom Field/Property Setter**（属于 fixtures 范畴）。
- 变更后：
  - 更新对应脚本/后端逻辑（如 hooks 的 `doc_events`、`doctype_js`）
  - 导出 fixtures（确保安装/迁移可复现）

### 6.2 新增 DocType 或修改 DocType schema（.json）

- 变更 `.json` 属于代码层 schema 变更，部署后通过 `bench migrate` 同步到数据库。
- 若 schema 变更需要“数据回填/修复”，补一个 patch。

### 6.3 新增 DocType 事件逻辑

做法：

- 在对应 DocType controller 或 `utils/` 写函数
- 在 `cos/hooks.py` 的 `doc_events` 挂载
- 保持函数幂等、校验清晰，必要时 `frappe.throw` 给出可读错误

### 6.4 覆写核心方法（高风险）

仅在必要时使用 `override_whitelisted_methods`，并遵循：

- 兼容升级：对照原函数 signature 过滤参数（本仓库 `custom_search_link` 的做法）
- 影响面评估：覆写会影响所有调用方，必须写清楚原因与回滚方式

### 6.5 打印模板开发

打印模板位于 `print_format/`，通用要点：

- Jinja 渲染：可用 `doc` 与 `frappe`（示例见 `print_format/README.md`）
- CSS 定位：利用 `data-fieldtype` / `data-fieldname` 与 `.value`
- 交付：Print Format/Print Style/Letter Head/Terms 等通常通过 fixtures 交付

---

## 7. 快速定位索引（遇到需求先来这里找）

- **总挂载点**：`cos/hooks.py`
- **模块列表**：`cos/modules.txt`
- **DocType 定义**：`cos/**/doctype/**`
- **前端注入脚本**：`cos/public/js/doctype/` + `hooks.py: doctype_js`
- **fixtures**：`cos/fixtures/*.json`（filters 在 `hooks.py: fixtures`）
- **patches**：`cos/patches.txt`、`cos/patches/`
- **打印模板**：`print_format/`
- **可导入基础数据**：`importable_data/`

---

## 8. 参考资料（优先查“新文档/官方文档”，再落到本仓库实现）

> 当你（AI agent）不确定做法时：先对照官方文档，再回看本仓库的既有实现与约束，避免“照搬旧版本经验”。

- Frappe Hooks：`https://docs.frappe.io/framework/user/en/python-api/hooks`
- Database Migrations / patches：`https://docs.frappe.io/framework/user/en/database-migrations`
- Exporting Customizations：`https://docs.frappe.io/framework/user/en/guides/app-development/exporting-customizations`
- ERPNext Client Scripts：`https://docs.erpnext.com/docs/user/manual/en/client-scripts`
- Frappe Unit Testing：`https://docs.frappe.io/framework/user/en/guides/automated-testing/unit-testing`
- Migrating to v16（迁移要点参考）：`https://github.com/frappe/frappe/wiki/Migrating-to-version-16`

