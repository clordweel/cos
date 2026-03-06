# 打印格式模板未生效根因分析

## 现象

用户反馈：发货单 - 标准、销售发票 - 标准、采购收货单 - 标准 三个打印格式在系统中未显示。

## 验证结果（dev 服务器 10.1.1.21）

手动执行 sync 脚本后，三个格式均已存在且已更新：

```bash
bench --site junhai.local execute cos.scripts.sync_delivery_note_print_format.sync
# {"updated": "发货单 - 标准", "created": false, ...}

bench --site junhai.local execute cos.scripts.sync_sales_invoice_print_format.sync
# {"updated": "销售发票 - 标准", "created": false, ...}

bench --site junhai.local execute cos.scripts.sync_purchase_receipt_print_format.sync
# {"updated": "采购收货单 - 标准", "created": false, ...}
```

`created: false` 表示格式已存在，sync 仅做了更新。

## 根因分析

### 1. Patch 只执行一次

Frappe 的 patch 在 `bench migrate` 时执行，执行成功后会被记录到 `tabPatch Log`，**后续 migrate 不再运行**。

### 2. 静默失败

原 patch `sync_new_print_formats.py` 对 `FileNotFoundError` 使用 `except: pass` 静默跳过：

- 若首次 migrate 时 `print_format/` 模板尚未部署（如 git 未拉取、路径错误），会抛出 `FileNotFoundError`
- Patch 静默跳过，Frappe 仍将 patch 标记为「已执行」
- 后续 migrate 不再运行，格式永远不会被创建

### 3. 环境差异

- **dev** (cos-dev.junhai.work)：已手动执行 sync，格式存在
- **prod** (cos.junhai.work)：若未部署或 patch 曾静默失败，格式可能不存在

## 修复措施

1. **Patch 不再静默失败**：`FileNotFoundError` 改为记录到 Error Log，便于排查
2. **手动补救**：若某环境格式缺失，在服务器上执行：

   ```bash
   bench --site junhai.local execute cos.scripts.sync_delivery_note_print_format.sync
   bench --site junhai.local execute cos.scripts.sync_sales_invoice_print_format.sync
   bench --site junhai.local execute cos.scripts.sync_purchase_receipt_print_format.sync
   ```

3. **prod 部署**：需执行 `bench migrate` 并视情况手动执行上述 sync

## 验证

列出名称含「标准」的 Print Format：

```bash
bench --site junhai.local execute cos.scripts.list_print_formats_standard.list_standard
```
