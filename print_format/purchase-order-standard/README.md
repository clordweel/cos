# 采购订单打印格式模板

## 模板概述

本模板用于生成"采购订单"（Purchase Order），适用于采购业务场景的打印格式。

## 模板特点

### 1. 文档结构

- **文档类型**：采购订单（Purchase Order）
- **基本信息**：供应商、单号、联系人、日期、关联项目
- **物料明细**：序号、物料信息、交货日期、数量、单价、金额
- **金额汇总**：小计、税费、总计
- **备注区域**：大写金额、备注/条款
- **签名区域**：采购员、部门经理、财务审核、供应商确认

### 2. 主要功能

#### 基本信息显示
- **供应商**：显示供应商名称（`doc.supplier_name`）
- **单号**：显示文档编号（`doc.name`）
- **联系人**：显示供应商联系人信息（`doc.contact_person`）
  - 如果存在联系人，显示联系人名称和手机号（格式：`联系人名称 (手机号)`）
- **日期**：显示交易日期（`doc.transaction_date`），使用 `frappe.utils.format_date` 格式化
- **关联项目**：自动查找并显示关联项目
  - 优先级1：从主表获取项目ID（`doc.project`）
  - 优先级2：从子表第一行获取项目ID（`doc.items[0].project`）
  - 显示格式：`项目ID (项目名称)` 或 `项目ID`

#### 物料明细表格
- **序号**：自动编号（`loop.index`）
- **物料信息**：显示物料代码、物料名称、描述（如果存在）、供应商物料编号（如果存在）
- **交货日期**：显示交货日期（`item.schedule_date`），使用 `frappe.utils.format_date` 格式化
- **数量**：显示采购数量（`item.qty`）和单位（`item.uom`）
- **单价**：显示单价（`item.get_formatted("rate")`）
- **金额**：显示金额（`item.get_formatted("amount")`）

#### 金额汇总表格
- **小计**：显示订单小计（`doc.get_formatted("total")`）
- **税费**：循环显示所有税费项（`doc.taxes`），仅显示税额大于0的税费
- **总计**：显示订单总计（`doc.get_formatted("grand_total")`），包含币种信息

#### 备注区域
- **大写金额**：显示金额大写（`doc.in_words`）
- **备注/条款**：优先显示条款（`doc.terms`），如果不存在则显示备注（`doc.remarks`）

#### 签名区域
- **采购员**：显示文档创建者（`doc.owner`）
- **部门经理**：空白签名行
- **财务审核**：空白签名行
- **供应商确认**：空白签名行

### 3. HTML结构特点

#### 样式框架
- **Bootstrap CSS框架**：模板使用 **Bootstrap v3.3.1** 进行样式化
- **自定义样式**：通过 `styles.css` 补充 Bootstrap 未覆盖的样式需求

#### 主要容器
- `.print-format-wrapper`：主容器（通用前缀，可复用到其他模板）
- `.print-format-body`：正文容器（全局样式）

#### 关键元素类名（结合Bootstrap类）
- `.info-table`：基本信息表格（使用 `table table-bordered`）
- `.info-cell`：信息单元格
- `.info-label`：信息标签（如"供应商:"）
- `.info-value`：信息值
- `.items-table`：物料明细表格（使用 `table table-bordered`）
- `.item-info-cell`：物料信息单元格
- `.item-code`：物料代码
- `.item-name`：物料名称
- `.item-description`：物料描述
- `.quantity-cell`：数量单元格
- `.quantity-value`：数量值
- `.quantity-uom`：数量单位
- `.totals-table`：金额汇总表格（使用 `table table-bordered`）
- `.remarks-box`：备注区域
- `.remarks-label`：备注标签
- `.remarks-content`：备注内容
- `.signature-table`：签名表格（使用 `table table-borderless`）
- `.signature-cell`：签名单元格
- `.signature-label`：签名标签
- `.signature-name`：签名姓名
- `.signature-line`：签名线

#### Bootstrap工具类使用
- **布局类**：`row`, `col-xs-*`（Bootstrap v3 网格系统）
- **间距类**：`mb-2`, `mb-3`, `mt-2`
- **文本类**：`text-center`, `text-right`, `text-left`, `font-weight-bold`
- **表格类**：`table`, `table-bordered`, `table-borderless`

### 4. 数据字段映射

#### 从doc对象获取的字段

##### 基础字段
- `doc.name`：文档编号（采购订单号）
- `doc.transaction_date`：交易日期
- `doc.supplier_name`：供应商名称
- `doc.contact_person`：联系人ID
- `doc.contact_display`：联系人显示名称
- `doc.project`：项目ID（如果存在）
- `doc.owner`：文档创建者（采购员）
- `doc.remarks`：备注信息
- `doc.terms`：条款信息（富文本）
- `doc.in_words`：金额大写
- `doc.currency`：币种
- `doc.docstatus`：文档状态（0=草稿，1=已提交，2=已取消）

##### 关联字段
- `doc.items`：物料明细列表
  - `item.item_code`：物料代码
  - `item.item_name`：物料名称
  - `item.description`：物料描述
  - `item.supplier_part_no`：供应商物料编号
  - `item.schedule_date`：交货日期
  - `item.qty`：采购数量
  - `item.uom`：单位
  - `item.rate`：单价
  - `item.amount`：金额
  - `item.project`：项目ID（如果存在）
- `doc.taxes`：税费列表
  - `tax.description`：税费描述
  - `tax.tax_amount`：税费金额

##### 计算字段
- `project_display`：项目显示文本（格式：`项目ID (项目名称)`）
- `contact_display`：联系人显示文本（格式：`联系人名称 (手机号)`）

### 5. 重要信息

#### 项目查找逻辑
1. **优先级1**：从主表获取
   - 条件：`doc.project` 存在
   - 项目ID：`doc.project`

2. **优先级2**：从子表第一行获取
   - 条件：`doc.items` 存在且长度大于 0，且 `doc.items[0].project` 存在
   - 项目ID：`doc.items[0].project`

3. **项目名称拼接**
   - 如果项目存在名称：`项目ID (项目名称)`
   - 如果项目无名称：`项目ID`

#### 联系人信息处理
1. **获取联系人显示名称**
   - 优先使用：`doc.contact_display`
   - 其次使用：`doc.contact_person`

2. **获取联系人手机号**
   - 查询：`frappe.db.get_value("Contact", doc.contact_person, "mobile_no")`

3. **拼接联系人显示文本**
   - 如果存在手机号：`联系人名称 (手机号)`
   - 如果无手机号：`联系人名称`

#### 物料明细表格列
- **序号**：自动编号（1, 2, 3, ...）
- **物料信息**：物料代码（粗体）、物料名称、描述（如果存在且不同于名称）、供应商物料编号（如果存在，格式：`[供]: 供应商物料编号`）
- **交货日期**：格式化后的日期
- **数量**：采购数量（粗体）+ 单位
- **单价**：格式化后的单价
- **金额**：格式化后的金额（粗体）

#### 金额汇总表格
- **小计**：订单小计金额
- **税费**：循环显示所有税费项（仅显示税额大于0的税费）
- **总计**：订单总计金额，包含币种信息，使用深灰色背景突出显示

### 6. 特殊说明

#### 文档状态水印
- 水印功能已在 `letter-head.html` 中统一处理
- 草稿状态（`doc.docstatus == 0`）：显示"草稿"水印
- 已取消状态（`doc.docstatus == 2`）：显示"已作废"水印

#### 表格样式
- 基本信息表格：单边框，浅色背景
- 物料明细表格：单边框，表头浅灰色背景，隔行变色（偶数行浅灰色背景）
- 金额汇总表格：单边框，总计行深灰色背景
- 签名表格：无边框

#### 打印优化
- 使用 `@media print` 规则优化打印效果
- 表格行避免分页
- 表头重复显示
- 颜色精确打印（`print-color-adjust: exact`）

### 7. 样式实现

#### Bootstrap集成
- 模板已集成 **Bootstrap v3.3.1** CSS框架
- 使用Bootstrap的工具类进行布局和样式控制
- **兼容性**：Bootstrap v3.3.1 不包含 flex 相关样式，使用 `row`/`col-xs-*` 网格系统
- 自定义样式文件 `styles.css` 补充Bootstrap未覆盖的需求

#### 样式特点
- 响应式布局（使用Bootstrap v3的网格系统）
- 统一的间距系统（使用Bootstrap的spacing工具类和CSS统一控制）
- 专业的表格样式（结合Bootstrap表格类和自定义样式）
- 打印和PDF导出优化（包含 `@media print` 规则）
- 隔行变色（物料明细表格偶数行浅灰色背景）

### 8. 文件结构

```
purchase-order-standard/
├── template.html      # 主模板文件
├── styles.css         # 样式文件
└── README.md          # 文档说明
```

### 9. 使用说明

1. **模板位置**：`print_format/purchase-order-standard/template.html`
2. **样式文件**：`print_format/purchase-order-standard/styles.css`
3. **同步到 dev**：执行 `bench --site <dev-site> execute cos.scripts.sync_purchase_order_print_format.sync` 将模板同步到 Print Format「采购订单 - 标准」
4. **导出与迁移**：详见 `docs/采购订单打印格式_dev导出_prod迁移.md`

### 10. 样式和HTML结构规范

本模板遵循 `pick-list-standard` 模板的样式和HTML结构规范，包括：

- **表格单元格边距**：统一为 `4px`
- **表格列宽**：使用百分比，总和为 `100%`
  - 序号：`6%`
  - 物料信息：`32%`
  - 交货日期：`14%`
  - 数量：`12%`
  - 单价：`18%`
  - 金额：`18%`
  - 总计：`100%`
- **主容器类名**：`.print-format-wrapper`（通用前缀，可复用样式）
- **标准HTML结构**：遵循规范化的HTML结构模板
- **标准类名**：使用统一的类名规范
- **金额汇总表格**：使用 `.totals-table` 类名，单元格 padding 为 `4px`

详细规范请参考 `pick-list-standard/README.md` 中的"样式和HTML结构规范"章节。

### 11. 待完善项

- 部分字段可能需要从自定义字段或配置中获取
- 签名区域可能需要支持更多签名人
- 可能需要添加打印日期时间戳
- 可能需要支持多页打印的分页控制
