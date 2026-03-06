# 销售发票 - 标准打印格式

## 说明

适用于 Sales Invoice（销售发票）的标准打印模板，含发票号、税号、税额、价税合计、客户信息、物料明细、签名区。

## 同步

```bash
bench --site junhai.local execute cos.scripts.sync_sales_invoice_print_format.sync
```

同步后执行 `bench export-fixtures`，再提交 `cos/fixtures/print_format.json`。
