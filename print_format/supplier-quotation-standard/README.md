# 供应商报价单 - 标准

Supplier Quotation 的标准打印格式。

## 头信息

- 供应商、报价编号
- 联系人、报价日期
- 有效期至、供应商报价单号（如有）

## 表格

- 序号、物料信息（含供应商料号 [供]）、数量、单位、单价、金额、备注

## 底部

- 小计、税费、总计、大写金额
- 备注/条款

## 同步到站点

```bash
bench --site <site> execute cos.scripts.sync_supplier_quotation_print_format.sync
```
