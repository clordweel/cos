---
name: cursor-mcp-tooling
description: 规范化在 Cursor 内使用 MCP 工具的流程：先定位并读取 tool schema，再按 schema 组装参数调用；包含浏览器类 MCP 的锁/解锁注意事项与常见错误排查。用于需要“直接调用 MCP / 使用 CallMcpTool 操作外部工具”的场景。
---

# Cursor MCP 工具调用规范（Schema First）

## 适用场景

- 需要直接调用 MCP（例如“用 MCP 操作浏览器/第三方服务/自动化工具”）
- 需要通过 MCP 获取结构化数据（而不是仅靠代码阅读/推断）

## 标准流程（必须遵守）

1. **先发现 server**
   - 在本工作区，MCP 描述文件位于：`/home/frappe/.cursor/projects/home-frappe-frappe-bench-apps-cos/mcps/<server>/tools/*.json`

2. **再读 schema（强制）**
   - 调用任何 MCP tool 之前，必须先读取对应的 `tools/<tool>.json` 描述文件
   - 重点确认：必填参数、参数类型、是否允许 FREEFORM、是否有副作用/鉴权要求

3. **按 schema 组参并调用**
   - 参数严格匹配 schema（字段名、类型、嵌套结构）
   - 若 schema 要求先 lock 再操作（如浏览器类 MCP），严格遵循其流程

4. **验证结果与回滚意识**
   - 有副作用的调用（创建/修改/删除）必须：
     - 先做只读探测（list/get）确认目标
     - 记录关键标识（name/id），便于失败后定位与回滚

## 浏览器类 MCP（锁/解锁）通用要点

- 交互前先列出当前 tabs；若已有 tab，需要先 lock 再交互
- 每次点击/输入前先 snapshot 获取最新结构与 element refs
- 等待策略：短等待（1–3s）+ snapshot 轮询，不用一次性长等待
- 全部操作结束后再 unlock（避免遗留锁导致后续调用失败）

## 常见错误与处理

- **“参数缺失/类型不匹配”**
  - 回到对应 `tools/<tool>.json`，对照 required 与 type 修正
- **“需要先 lock / tab 不存在”**
  - 先 list tabs → navigate/create tab → lock → snapshot → 交互
- **“401/403/权限不足”**
  - 先确认当前环境的鉴权方式与可用权限；必要时改用只读工具或降级方案

