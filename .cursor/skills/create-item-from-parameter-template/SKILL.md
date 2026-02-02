---
name: create-item-from-parameter-template
description: 基于 Item Parameter Template（及其子表 Item Parameter Template Definition）作为“参数约束与参考”，直接创建目标 Item；重点处理 Doctype 约束参数（doctype_selector 限定的可选 DocType）并在需要新建基础资料时输出“必须这样做”的复核理由。优先使用 FAC MCP（tools/list → tools/call），可降级到 Frappe REST。
---

# 基于参数模板创建物料（Item）

## 适用范围

- 你已确定一个 **`Item Parameter Template`**（参数模板）
- 希望按模板的参数定义（类型/默认值/可选/正则/Doctype 约束/是否参与指纹）来创建物料
- 目标是生成一个 **`Item`**（本 skill 默认**不依赖/不关注** `New Item Request` 流程）

## 依赖（建议）

- **核心单据**
  - `Item Parameter Template`
  - `Item Parameter Template Definition`（模板子表）
  - `Item`（最终物料）
- **可选（若你要走“申请单→生成物料”的审计链路）**
  - `New Item Request`（可提交）
  - `Item Parameter Definition`（申请子表）
- **接口能力**
  - **优先：FAC MCP**（`tools/list` / `tools/call`）
  - 备选：Frappe REST（`/api/resource/...` / `/api/method/...`）

## 输入（你需要提供/确认）

- **template**：模板名（推荐用 `Item Parameter Template.name`，本项目中通常等于 `template_name`）
- **item_group**：物料组（可不传，优先使用模板自带 `item_group`）
- **parameter_values**：参数输入（key 为 `parameter_name`，value 为用户填写的值）
- **uoms**：计量单位换算（可不传，优先从模板复制）
- **是否允许自动新建“参数约束引用的基础资料”**：默认 **否**（除非必要且理由充分）

## 工作流（推荐：FAC MCP）

### 0) 工具探测（Schema First）

1. `tools/list`：确认至少可用
   - `list_documents`
   - `get_document`
   - `create_document`
2. 若要“模板约束 + Format 渲染 + 指纹计算”的一致性，建议同时可用：
   - `run_python_code`（在服务器端完成渲染/校验/创建，减少往返与数据泄露）
   - 或提供一个 COS external tool（见“增强建议”）

### 1) 找到并读取模板（Item Parameter Template）

- `list_documents`：按 `template_name`/`name` 查找模板
- `get_document`：取回模板全文（应包含子表 `parameters` 和 `uoms`）

你需要从模板中读取：

- 模板 `item_group`（默认物料组）
- 子表 `parameters`（每行是 `Item Parameter Template Definition`）
  - `parameter_name`
  - `constraint_type`（Data/Integer/Float/Format/Doctype）
  - `parameter_default_value`
  - `allowed_data`（Data 的可选值/正则）
  - `doctype_selector`（Doctype 的允许 DocType 列表）
  - `join_to_hash`（是否参与 MD5 指纹）
  - `binding_field/target_field`（是否映射到 Item 字段）
- 子表 `uoms`（单位换算）

### 2) 解析参数并执行约束校验（重点：Doctype 约束）

#### 2.1 Data/Integer/Float/Format 的处理要点

- `allowed_data`（Data）：必须匹配枚举/正则（模板定义的约束）
- `Integer/Float`：按数值类型解析并归一
- `Format`：尽量由模板定义（Jinja）自动渲染产生，不建议自由输入

#### 2.2 Doctype 约束（你必须关注的点）

当模板参数 `constraint_type == "Doctype"` 时：

- 该参数的 `doctype_selector` 会限制“允许选择的 DocType 范围”
  - 本项目典型允许范围（见 `Item Parameter Definition.doctype_selector` 的 link_filters）：  
    `Item Base Name` / `Item Material` / `Item Surface` / `Item Color` / `Executive Standard` / `UOM` / `Brand` / `Source Type` / `Item Group` / `Supplier`
- 用户输入必须最终落成：`(doctype_selector, value_doctype)` 这对组合所指向的**已存在记录**

如果用户输入的是“一个新材质/新标准号/新维度值”，你需要先判断：

1. **该 DocType 是否允许在当前场景新建**（权限、流程、是否应由主数据管理员维护）
2. **是否真的不存在可复用记录**（先查重，再谈新建）
3. **新建是否会引入数据污染**（同义词/别名/编码不一致）

> 默认策略：**不自动新建基础资料**；只有在“必须新建”且理由充分时才新建，并输出复核理由。

##### “必须新建”复核理由模板（创建前必须输出）

- **触发参数**：`parameter_name=<...>`（constraint_type=Doctype）
- **目标 DocType**：`<doctype_selector>`
- **为什么不能复用**：检索范围/关键字段/无匹配记录的证据（例如按编码/名称都未找到）
- **新建字段来源**：编码/名称/描述来自哪里（图纸/标准/客户要求/技术输入）
- **影响评估**：是否会影响编码、BOM、采购、报表统计
- **回滚/治理**：若发现重复，如何合并/禁用/迁移引用

然后按 `parameter_values` 覆盖：

- `constraint_type == "Data"`：覆盖 `parameter_value`
- `constraint_type == "Integer"/"Float"`：覆盖 `value_integer/value_float`，并同步 `parameter_value`（本项目前端会把它们同步到 `parameter_value`）
- `constraint_type == "Doctype"`：覆盖 `value_doctype`（并同步 `parameter_value`）
- `constraint_type == "Format"`：
  - 通常不需要用户输入；依赖 `parameter_default_value/value_format` + 级联渲染
  - 若需要人工覆盖，建议覆盖 `value_format`（并允许 preview/渲染更新）

### 3) 创建/补齐 Doctype 约束引用的基础资料（仅在必要时）

仅当满足以下条件才允许创建新记录：

- `doctype_selector` 在模板允许范围内，且当前用户具备新建权限
- 输入信息足够完整（至少包含“唯一标识 + 人类可读名称”）
- 按“复核理由模板”给出充分理由

建议的“先查后建”顺序：

- `list_documents` / `search_doctype` 先按唯一字段查找
- 确认不存在再 `create_document`

常见 DocType 的“唯一字段”参考（用于查重与新建最小字段集）：

- `Item Material`：`material_code`（唯一）与 `material_name`（唯一）
- `Executive Standard`：`standard_code`（唯一），可选 `standard_name`
- `Item Color`：`color_name`（唯一）
- `Item Surface`：`surface_name`（唯一）
- `Item Base Name`：`base_name`（唯一，树形）
- `Source Type`：`source_name`（唯一）

### 4) 生成 Item 的字段字典（绑定字段映射）

以模板子表的 `binding_field/target_field` 为准，把参数值映射到 `Item.<target_field>`。

注意：

- `constraint_type == "Format"` 且参与绑定时：应先渲染得到最终值再赋值
- `constraint_type == "Doctype"` 参与绑定时：赋值通常是被引用 Doc 的 `name`（Link 值）

### 5)（可选但推荐）生成参数指纹并做查重

若你希望保持与 COS 现有逻辑一致，可按 `join_to_hash=1` 的参数计算指纹（MD5），并查重：

- 在 `Item` 上使用的字段通常为：`custom_unique_code`
- 查重方式：`list_documents` 过滤 `Item.custom_unique_code == <md5>`

### 6) 创建 Item

使用 `create_document` 创建 `Item`（建议最小字段集）：

- `item_group`（必须；触发 COS 的自动编码逻辑）
- 模板绑定字段映射得到的各字段值
-（可选）`custom_unique_code`
-（可选）`uoms`（若你已确认子表结构与字段一致）

创建后建议回读校验：

- 物料编码是否按 `Item Group.custom_code` 规则生成（否则说明物料组基础数据缺失）

## 备选工作流：Frappe REST

当没有 FAC MCP 时，可以走 REST（注意权限与 CSRF/session）：

1. `GET/POST /api/resource/Item Parameter Template/<name>` 读取模板（含子表）
2. 对 Doctype 约束参数：先查重（必要时再新建基础资料，并写明复核理由）
3. `POST /api/resource/Item` 创建物料（建议只做最小字段集）

## 增强建议（建议补齐的能力）

为实现“真正一键”且把风险控制集中在服务端，建议在 COS 增加一个 FAC External Tool：

- `cos_create_item_from_template`
  - 输入：`template_name`、`item_group?`、`parameter_values`、`allow_create_missing_masters=false/true`
  - 输出：`item_name`、`custom_unique_code`、`created_masters[]`、`review_reasons[]`
  - 内部逻辑：
    - 读取模板 → 校验约束（含 Doctype 允许范围）→ 查重/（必要时）创建基础资料 → 渲染 Format → 创建 Item
  - 好处：LLM 调用成本低，且“新建基础资料的理由”能标准化输出用于复核

## 安全与一致性（强制）

- 不允许在技能输出中泄露 token / api_secret / api key
- 默认只做“按模板创建单个物料”最小闭环；批量创建必须额外确认范围
- Doctype 约束参数如需新建基础资料：必须输出“复核理由模板”内容供人工复核
- 所有校验以模板定义为准：
  - `allowed_data`（正则/枚举）
  - `doctype_selector/value_doctype`
  - `optional`
  - `join_to_hash`

