---
name: fac-external-tools
description: 在自定义 Frappe App（本项目 COS）中开发并注册可被 Frappe Assistant Core (FAC) 发现的 assistant_tools：创建 BaseTool 工具类、定义 inputSchema/权限/配置、在 hooks.py 注册、并按 FAC 的发现与审计机制进行测试与排错。用于“给 LLM 暴露业务工具/通过 MCP 远程调用 COS 业务逻辑”的场景。
---

# 在 COS 中开发 FAC External Tools（assistant_tools）

## 目标

把 COS 的业务能力封装为 FAC 可发现的工具（Tool），通过 FAC 的 MCP `tools/list` / `tools/call` 暴露给 LLM 客户端调用。

## 关键机制（必须理解）

- FAC 会从所有已安装 apps 的 `hooks.py` 读取 `assistant_tools` hook
- 你在 `assistant_tools` 中声明的**类路径**会被导入并实例化
- 每个工具类应继承 `frappe_assistant_core.core.base_tool.BaseTool`
- 执行路径默认走 `_safe_execute()`：
  - 依赖校验 → 权限校验 → schema 校验 → 执行 → 审计日志

## COS 推荐目录结构

在本项目中建议使用：

- `cos/assistant_tools/`
  - `__init__.py`
  - `<tool>.py`

工具类的导入路径形如：`cos.assistant_tools.<tool>.<ToolClass>`

## 工具类编写清单（最低要求）

- **name**：tool 名称（小写、下划线），后续调用 `tools/call` 用它
- **description**：尽量写清楚“能做什么 + 输入输出 + 示例”
- **source_app**：设为 `"cos"`（用于 FAC 侧识别来源）
- **category**：便于工具分类（如 `"COS Stock"` / `"COS Accounts"`）
- **inputSchema**：严格定义参数（required/properties/type）
- **requires_permission**：尽量绑定到最贴近的 DocType（最低读权限）
- **execute(arguments)**：只做业务逻辑；不要自己做 schema 校验/审计（FAC 已封装）

## hooks.py 注册（COS）

在 `cos/hooks.py` 中加入（或维护）：

- `assistant_tools = [...]`：工具类路径列表
- 可选：`assistant_tool_configs = {...}`：对单个 tool 的配置覆盖（app 级别）

注意：site 级配置可通过 `site_config.json` 的 `assistant_tools` 覆盖（FAC 侧支持）。

## 安全与质量要求（强制）

- **权限**：工具内部不要假设有权限；即使 `requires_permission` 存在，也建议在关键操作前再次用 `frappe.has_permission` 做细化校验
- **SQL**：避免裸 SQL；确需使用必须参数化（严禁 f-string 拼接用户输入）
- **日志**：不要记录 token / secret / password；输出数据规模要受控（避免巨大数组）
- **幂等性**：工具可被重复调用；尽量做到重复调用不会破坏数据
- **返回结构**：返回可 JSON 序列化的 dict/list/str；datetime/Decimal 等类型尽量提前转换（FAC 侧通常会做 `default=str` 兜底，但不要依赖）

## 测试/验证建议（最短闭环）

1. **bench console**：确认工具类可 import、可实例化
2. **FAC 工具列表**：通过 `tools/list` 能看到新工具
3. **最小调用**：用一组最小参数跑通 `tools/call`
4. **权限回归**：用权限不足的用户验证确实被拒绝（403/PermissionError）

## 常见问题排查

- **工具未被发现**
  - 检查 `cos/hooks.py` 是否声明 `assistant_tools`
  - 检查类路径是否正确、`__init__.py` 是否存在
  - 检查 import 是否抛异常（语法错误/依赖缺失）
- **参数校验失败**
  - 对照 `inputSchema.required` 与 `properties[type]` 修正调用参数
- **权限错误**
  - 检查 `requires_permission` 与工具内额外校验逻辑
  - 检查用户是否有目标 DocType 的 read/write 权限

