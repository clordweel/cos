# 供应商报价单 - 外部（无价格）

Supplier Quotation 的外部版变体：**不展示**行级单价/金额与页末小计、税费、总计、大写金额。

## 与「供应商报价单 - 外部」差异

- **表格列**：仅序号、物料信息、数量、单位、备注；无单价、金额列
- **汇总区**：整段移除（不显示任何金额相关字段）

其余（抬头信息、物料编码/名称/供方料号/供应商提供图纸、备注与条款区）与外部版一致。

## 同步到站点

```bash
bench --site <site> execute cos.scripts.sync_supplier_quotation_external_no_price.sync
```
