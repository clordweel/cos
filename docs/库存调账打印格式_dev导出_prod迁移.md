# 库存调账打印格式：dev 完成 → 导出 cos → 迁移 prod

## 模板位置

- **本地模板**：`print_format/stock-reconciliation-standard/`
  - `template.html`：Jinja 模板
  - `styles.css`：模板特定样式（通用样式在 `standard.css`）

## 流程概览

```
[1] dev 同步  →  [2] 导出 fixtures  →  [3] 提交 cos 仓库  →  [4] prod migrate
```

---

## 步骤 1：在 dev 中同步打印格式

在 dev 服务器上执行：

```bash
cd /path/to/frappe-bench
bench --site cos-dev.junhai.work execute cos.scripts.sync_stock_reconciliation_print_format.sync
```

脚本会：
- 读取 `print_format/stock-reconciliation-standard/template.html` 和 `styles.css`
- 若 Print Format「库存调账 - 标准」不存在则自动创建
- 若已存在则更新内容，并设置 module 为 COS Stock

---

## 步骤 2：导出 fixtures

```bash
bench --site cos-dev.junhai.work export-fixtures
```

检查 `apps/cos/cos/fixtures/print_format.json` 中是否包含「库存调账 - 标准」。

---

## 步骤 3：提交到 cos 仓库

```bash
cd apps/cos
git add cos/fixtures/print_format.json
git commit -m "feat(print): 添加库存调账 - 标准打印格式"
git push
```

---

## 步骤 4：迁移到 prod

```bash
bench --site cos.junhai.work migrate
```
