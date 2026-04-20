# 工业产品买卖合同（采购 · A4 单页简版）

## 用途

在「采购订单」上打印**一页 A4** 的简易工业产品买卖合同正文，字段与 `contract-and-terms-purchase`（采购订单 - 合同 - 通用）一致，条款压缩为 6 条，表格含**规格型号**列（`item.custom_specification`）。

## ERP 打印格式名称

| 项 | 说明 |
|----|------|
| **Print Format 名称** | **采购订单 - 合同 - 工业产品 A4** |
| **doc_type** | Purchase Order |
| **module** | COS Share（与其它采购合同模板一致） |

首次使用前，请在站点中**新建**上述名称的 Print Format（Jinja、自定义格式），再执行同步脚本将本目录 `template.html` / `styles.css` 写入数据库。

## 同步到站点（dev）

```text
bench --site <dev-site> execute cos.scripts.sync_contract_po_so_print_formats.sync
```

`sync_contract_po_so_print_formats` 已包含本模板目录 `contract-industrial-product-purchase-a4`；若站点上不存在「采购订单 - 合同 - 工业产品 A4」，请先创建同名 Print Format 后再执行。

## 单页说明

- 版式：`@page` 边距约 6–7mm，正文字号约 8–8.5px，适合**行数较少**的订单。
- 若明细行过多，打印会自然分页；需要严格单页时请控制行数或拆单。

## 字段对照

与 `contract-and-terms-purchase` README 中「从 doc 获取的字段」一致；本版签名区为紧凑两行「单位名称～税号 + 盖章」，不再单独列出通信信息大表。

- **是否打印物料备注**（`custom_is_print_item_remarks`，位于 **`custom_is_print_terms` 之后**）：默认勾选；取消勾选后明细表**不显示「备注」列**（不打印行 `description`），以节省版面。与「采购订单 - 合同 - 通用」模板行为一致。
