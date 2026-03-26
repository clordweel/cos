# 供应商报价单 - 外部

Supplier Quotation 的**外部版**打印格式，用于发给供应商填写。

## 与标准版差异

- **物料信息**：仅物料编码、名称、供应商料号、（若勾选）加粗「供应商提供图纸」；**明细描述仅出现在「备注」列**，避免与备注重复
- **表格**：单价（元）、金额（元）、备注 列留空，供供应商手填（不显示 0.00）
- **金额汇总**：小计、总计、大写金额 留空供供应商填写
- **序号表头**：增加 `white-space: nowrap`、`min-width` 避免换行

## 同步到站点

```bash
bench --site <site> execute cos.scripts.sync_supplier_quotation_external.sync
```
