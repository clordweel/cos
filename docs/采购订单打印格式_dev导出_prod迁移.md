# 采购订单打印格式：dev 完成 → 导出 cos → 迁移 prod

## 参考模板

- **prod 预览**：<https://cos.junhai.work/desk/print-format/采购订单%20-%20标准>（需登录）
- **本地模板**：`print_format/purchase-order-standard/`
  - `template.html`：Jinja 模板
  - `styles.css`：模板特定样式（通用样式在 `standard.css`）

## 流程概览

```
[1] dev 编辑/同步  →  [2] 导出 fixtures  →  [3] 提交 cos 仓库  →  [4] prod migrate
```

---

## 步骤 1：在 dev 中完成打印格式

### 方式 A：从 print_format 目录同步到 dev（推荐）

在 dev 服务器上（cos app 所在 bench 环境）：

```bash
cd /path/to/frappe-bench
bench --site cos-dev.junhai.work execute cos.scripts.sync_purchase_order_print_format.sync
```

脚本会读取 `print_format/purchase-order-standard/template.html` 和 `styles.css`，更新 Print Format「采购订单 - 标准」，并设置 module 为 COS Share。

### 方式 B：在 dev 界面手动编辑

1. 登录 dev：`http://cos-dev.junhai.work` 或 `https://cos-dev.junhai.work`
2. 搜索 **Print Format** → 打开「采购订单 - 标准」
3. 参考 prod 模板（<https://cos.junhai.work/desk/print-format/采购订单%20-%20标准>）调整：
   - **HTML**：复制 `print_format/purchase-order-standard/template.html` 内容
   - **CSS**：复制 `print_format/purchase-order-standard/styles.css` 内容（通用样式由 Print Style 提供）
4. 保存

### 确保 module 可被导出

Print Format「采购订单 - 标准」的 **Module** 需为 `COS Share`（或 `COS Stock`、`COS Accounts`），才能在 `bench export-fixtures` 时被导出。若为 `Buying`，请在编辑时改为 `COS Share`。

---

## 步骤 2：导出 fixtures

在 dev 服务器上：

```bash
cd /path/to/frappe-bench
bench --site cos-dev.junhai.work export-fixtures
```

检查 `apps/cos/cos/fixtures/print_format.json` 中是否包含「采购订单 - 标准」。hooks.py 已配置：

```python
{"dt": "Print Format", "filters": [["module", "in", ["COS Share", "COS Stock", "COS Accounts"]]]}
```

---

## 步骤 3：提交到 cos 仓库

```bash
cd apps/cos
git add cos/fixtures/print_format.json
git commit -m "chore(print): 同步采购订单 - 标准打印格式"
git push
```

---

## 步骤 4：迁移到 prod

在 prod 服务器上：

```bash
cd /path/to/frappe-bench
git pull  # 拉取 cos 最新代码
bench --site cos.junhai.work migrate
```

或若使用 `bench update`：

```bash
bench update
```

Fixtures 会在 migrate 时自动同步到 prod 数据库。

---

## 文件对应关系

| 位置 | 说明 |
|------|------|
| `print_format/purchase-order-standard/template.html` | 源 HTML 模板 |
| `print_format/purchase-order-standard/styles.css` | 源 CSS（模板特定） |
| `print_format/standard.css` | 通用样式（由 Print Style 或 Letter Head 引用） |
| `cos/fixtures/print_format.json` | 导出的 Print Format 记录（含 html、css 字段） |

---

## 常见问题

### Q: prod 模板与 cos 仓库不一致？

在 dev 中按 prod 实际效果调整，保存后执行 `bench export-fixtures`，再提交 `print_format.json`。

### Q: 导出时未包含「采购订单 - 标准」？

检查 Print Format 的 Module 是否为 `COS Share` / `COS Stock` / `COS Accounts`。若为 `Buying`，改为 `COS Share` 后重新导出。

### Q: migrate 后 prod 未更新？

确认 `bench migrate` 已成功执行，且 cos app 已更新。可手动清除缓存：`bench --site cos.junhai.work clear-cache`。
