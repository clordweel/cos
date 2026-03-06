# 采购收货单 - 标准打印格式

## 说明

适用于 Purchase Receipt（采购收货单）的标准打印模板，含供应商、收货仓库、物料明细、金额汇总、签收区。

## 同步

```bash
bench --site junhai.local execute cos.scripts.sync_purchase_receipt_print_format.sync
```

同步后执行 `bench export-fixtures`，再提交 `cos/fixtures/print_format.json`。
