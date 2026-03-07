# 库存调账打印格式模板

## 模板概述

本模板用于「库存调账」（Stock Reconciliation）单据的打印格式，适用于期初开账、库存盘点调账等场景。

## 模板特点

### 1. 文档结构

- **文档类型**：库存调账（Stock Reconciliation）
- **基本信息**：单号、过账日期、公司、目的、差异科目、成本中心、差异金额
- **物料明细**：序号、物料信息、仓库、数量、单位、单价、金额、勾选
- **签名区域**：制单人、盘点人、复核人、审批人  
  - **制单人**：显示文档创建者的**全名**（`User.full_name`），由 `doc.owner` 解析；若未维护全名则回退显示登录名（`doc.owner`）

### 2. 主要功能

#### 基本信息显示
- **单号**：`doc.name`
- **过账日期**：`doc.posting_date`
- **公司**：`doc.company`
- **目的**：期初开账 / 库存调账（根据 `doc.purpose` 映射）
- **差异科目**：`doc.expense_account`
- **成本中心**：`doc.cost_center`
- **差异金额**：`doc.difference_amount`（格式化）

#### 物料明细表格
- **序号**：`loop.index`
- **物料信息**：物料代码、物料名称、批次号（如有）、序列号（如有）
- **仓库**：`item.warehouse`
- **数量**：`item.qty`
- **单位**：`item.stock_uom`
- **单价**：`item.valuation_rate`（格式化）
- **金额**：`item.amount`（格式化）

### 3. 文件结构

```
stock-reconciliation-standard/
├── template.html   # 主模板文件
├── styles.css      # 样式文件
└── README.md       # 文档说明
```

### 4. 使用说明

1. **模板位置**：`print_format/stock-reconciliation-standard/template.html`
2. **样式文件**：`print_format/stock-reconciliation-standard/styles.css`
3. **同步到 dev**：执行 `bench --site <dev-site> execute cos.scripts.sync_stock_reconciliation_print_format.sync`
4. **导出与迁移**：详见 `docs/采购订单打印格式_dev导出_prod迁移.md`（流程相同，将「采购订单」替换为「库存调账 - 标准」）
