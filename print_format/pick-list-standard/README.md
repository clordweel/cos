# 拣货单打印格式模板

## 模板概述

本模板用于生成"拣货单"（Pick List），适用于仓库拣货作业的打印格式。

## 模板特点

### 1. 文档结构

- **文档类型**：拣货单（Pick List）
- **文档标题**：拣货单（居中显示，顶部留白，下边距 `mb-3`）
- **基本信息**：单号、日期、用途、项目、关联来源
- **物料明细**：序号、物料信息、源仓库、批次/序列号、数量、确认框
- **备注区域**：备注信息
- **签名区域**：制单人、拣货人、复核人、接收人

### 2. 主要功能

#### 基本信息显示
- **单号**：显示文档编号（`doc.name`）
- **日期**：显示创建日期（`doc.creation`），使用 `frappe.utils.format_date` 格式化
- **用途**：显示拣货用途（`doc.purpose`），使用 `_()` 函数进行翻译
- **项目**：自动查找并显示关联项目
  - 场景A：制造发料（Material Transfer for Manufacture）-> 从工单查找项目
  - 场景B：材料转移（Material Transfer）-> 从物料请求查找项目
  - 显示格式：`项目ID (项目名称)` 或 `项目ID`
- **关联来源**：自动识别并显示关联文档
  - 优先显示生产工单（`doc.work_order`）
  - 其次显示销售订单（从 `doc.locations[0].sales_order` 获取）
  - 最后显示物料请求（从 `doc.locations[0].material_request` 获取）

#### 物料明细表格
- **序号**：自动编号（`loop.index`）
- **物料信息**：显示物料代码、物料名称、描述（如果存在）
- **源仓库**：显示源仓库名称（`item.warehouse`）
- **批次/序列号**：显示批次号（`item.batch_no`）和序列号（`item.serial_no`）
- **数量**：显示拣货数量（`item.picked_qty`）和单位（`item.uom`）
- **确认框**：用于拣货确认的复选框

#### 备注区域
- 显示文档备注（`doc.remarks`）
- 如果无备注，显示 `&nbsp;`

#### 签名区域
- **制单人**：显示文档创建者（`doc.owner`）
- **拣货人**：空白签名行
- **复核人**：空白签名行
- **接收人**：空白签名行

### 3. HTML结构特点

#### 样式框架
- **Bootstrap CSS框架**：模板使用 **Bootstrap v3.3.1** 进行样式化
- **自定义样式**：通过 `styles.css` 补充 Bootstrap 未覆盖的样式需求

#### 主要容器
- `.pick-list-wrapper`：主容器
- `.print-format-body`：正文容器
- `.header-title`：标题区域

#### 关键元素类名（结合Bootstrap类）
- `.info-table`：基本信息表格（使用 `table table-bordered`）
- `.info-cell`：信息单元格
- `.info-label`：信息标签（如"单号:"）
- `.info-value`：信息值
- `.items-table`：物料明细表格（使用 `table table-bordered`）
- `.item-info-cell`：物料信息单元格
- `.item-code`：物料代码
- `.item-name`：物料名称
- `.item-description`：物料描述
- `.warehouse-cell`：仓库单元格
- `.batch-serial-cell`：批次/序列号单元格
- `.quantity-cell`：数量单元格
- `.quantity-value`：数量值
- `.quantity-uom`：数量单位
- `.check-box-outline`：复选框
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
- `doc.name`：文档编号（拣货单号）
- `doc.creation`：创建日期
- `doc.purpose`：拣货用途（需要翻译）
- `doc.owner`：文档创建者（制单人）
- `doc.remarks`：备注信息
- `doc.docstatus`：文档状态（0=草稿，1=已提交，2=已取消）

##### 关联字段
- `doc.work_order`：生产工单（如果存在）
- `doc.locations`：拣货位置列表
  - `item.item_code`：物料代码
  - `item.item_name`：物料名称
  - `item.description`：物料描述
  - `item.warehouse`：源仓库
  - `item.batch_no`：批次号
  - `item.serial_no`：序列号
  - `item.picked_qty`：拣货数量
  - `item.uom`：单位
  - `item.sales_order`：销售订单（如果存在）
  - `item.material_request`：物料请求（如果存在）

##### 计算字段
- `source_label`：关联来源标签（"生产工单"、"销售订单"、"物料请求"或"无"）
- `source_name`：关联来源名称
- `project_display`：项目显示文本（格式：`项目ID (项目名称)`）

### 5. 重要信息

#### 项目查找逻辑
1. **场景A：制造发料**
   - 条件：`doc.purpose == "Material Transfer for Manufacture"` 且 `doc.work_order` 存在
   - 查找：从工单（Work Order）获取项目ID
   - 查询：`frappe.db.get_value("Work Order", doc.work_order, "project")`

2. **场景B：材料转移**
   - 条件：`doc.purpose == "Material Transfer"` 且存在物料请求
   - 查找：从物料请求（Material Request）获取项目ID
   - 查询：`frappe.db.get_value("Material Request", doc.locations[0].material_request, "project")`

3. **项目名称拼接**
   - 如果项目存在名称：`项目ID (项目名称)`
   - 如果项目无名称：`项目ID`

#### 关联来源识别逻辑
1. **优先级1**：生产工单（`doc.work_order`）
   - 标签：`"生产工单"`
   - 名称：`doc.work_order`

2. **优先级2**：销售订单（从 `doc.locations[0].sales_order` 获取）
   - 标签：`"销售订单"`
   - 名称：`doc.locations[0].sales_order`

3. **优先级3**：物料请求（从 `doc.locations[0].material_request` 获取）
   - 标签：`"物料请求"`
   - 名称：`doc.locations[0].material_request`

4. **默认**：无关联
   - 标签：`"无"`
   - 名称：空字符串

#### 物料明细表格列
- **序号**：自动编号（1, 2, 3, ...）
- **物料信息**：物料代码（粗体）、物料名称、描述（如果存在且不同于名称）
- **源仓库**：仓库名称，如果为空显示 `"--"`
- **批次/序列号**：批次号（格式：`[批] 批次号`）、序列号（格式：`[序] 序列号`）
- **数量**：拣货数量（粗体）+ 单位
- **确认框**：用于拣货确认的复选框

### 6. 特殊说明

#### 文档状态水印
- **草稿状态**（`doc.docstatus == 0`）：显示"草稿"水印
- **已取消状态**（`doc.docstatus == 2`）：显示"已作废"水印
- 水印样式：旋转-15度，灰色边框和文字，绝对定位

#### 表格样式
- 基本信息表格：单边框，浅色背景
- 物料明细表格：单边框，表头浅灰色背景，隔行变色（偶数行浅灰色背景）
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
pick-list-standard/
├── template.html      # 主模板文件
├── styles.css         # 样式文件
└── README.md          # 文档说明
```

### 9. 使用说明

1. **模板位置**：`print_format/pick-list-standard/template.html`
2. **样式文件**：`print_format/pick-list-standard/styles.css`
3. **在Frappe中配置**：
   - 创建或编辑打印格式
   - 选择"HTML"类型
   - 将 `template.html` 的内容复制到模板编辑器
   - 确保样式文件 `styles.css` 被正确引用

### 10. 待完善项

- 部分字段可能需要从自定义字段或配置中获取
- 签名区域可能需要支持更多签名人
- 可能需要添加打印日期时间戳
- 可能需要支持多页打印的分页控制
