# 订单物料子表：拖拽调整列宽 — 实现阶段与检查说明

## 控制台一键检查（阶段 1 + 2 + 脚本是否执行）

打开订单表单（如 [采购订单](https://cos-dev.junhai.work/desk/purchase-order/xxx)），**先点一下表单主体或物料表格**，再在浏览器控制台粘贴并执行：

```javascript
(function () {
	var step1 = document.querySelector('.form-grid .grid-heading-row .grid-row .grid-static-col[data-fieldname]');
	var step2 = document.querySelectorAll('.cos-grid-col-resize-handle');
	var scriptRan = document.querySelectorAll('.grid-field[data-cos-grid-id]').length;
	console.log('阶段1 表头列(含 data-fieldname):', step1 ? 'OK ' + (step1.getAttribute('data-fieldname')) : 'FAIL 未找到');
	console.log('阶段2 拖拽手柄数量:', step2.length, step2.length >= 1 ? 'OK' : 'FAIL 未找到');
	console.log('脚本是否执行过:', scriptRan >= 1 ? '是 (已设置 data-cos-grid-id)' : '否 或 尚未命中本表单');
})();
```

- **阶段 1 OK**：DOM 结构正常。
- **阶段 2 ≥ 1**：手柄已插入，可在表头列右边缘拖拽试列宽。
- **先确认脚本已加载**：在控制台输入 `__cos_grid_resize_loaded` 回车，若为 `true` 表示本脚本已加载；若为 `undefined` 表示未加载（未部署/未 build/缓存），需部署后执行 `bench build --app cos` 并强制刷新（Ctrl+Shift+R）。
- **脚本是否执行 = 否**：脚本加载后会在约 0.5s～6s 内轮询当前表单并尝试挂载；若仍为否，请刷新页面再等几秒后重跑检查。
- **脚本执行但阶段 2 = 0**：先**点击一次表单或物料表格**，等约 1 秒后再执行上述检查。

---

## 实现阶段

### 阶段 1：确认脚本已加载并命中目标 grid

- **做法**：在控制台执行（打开销售订单/采购订单后）：
  ```js
  // 应存在
  document.querySelector('.form-grid .grid-heading-row .grid-row .grid-static-col[data-fieldname]')
  ```
- **检查**：返回一个 DOM 元素（表头某一列），说明 DOM 结构符合预期。
- **若为 null**：说明表头列没有 `data-fieldname` 或选择器与当前 Frappe 版本不一致，需对照实际 DOM 调整选择器。

### 阶段 2：确认 resize 手柄已插入且可点

- **做法**：打开订单表单，在物料子表表头列**右边缘**查找可拖拽区域（约 8px 宽，鼠标悬停应为 `col-resize`）。
- **检查**：
  - 控制台执行：`document.querySelectorAll('.cos-grid-col-resize-handle').length` 应 ≥ 1。
  - 表头第一行（非搜索行）的每个数据列右侧应有一个手柄。
- **若为 0**：说明 `setupResizeHandles` 未执行或未找到 `.grid-static-col[data-fieldname="..."]`，检查 `grid.visible_columns` 与表头 DOM 是否一致、是否被 `RESIZE_INIT_ATTR` 误跳过。

### 阶段 3：拖拽时列宽是否实时变化

- **做法**：在手柄上按下鼠标左键并水平拖动。
- **检查**：该列（表头+表体）宽度应随拖动变化，且不小于约 60px。
- **若不动**：可能是 (1) 事件被阻止或未绑定；(2) 应用的样式被 Frappe/Bootstrap 覆盖 — 脚本已通过注入 `<style id="cos-grid-col-widths">` 的 `!important` 规则覆盖。

### 阶段 4：刷新后列宽是否恢复

- **做法**：拖拽保存某列宽度后，刷新页面或关闭再打开同类型单据。
- **检查**：该列宽度应与上次拖拽结果一致。
- **若不恢复**：检查 localStorage 是否有 key `cos_grid_col_{doctype}_{table}_{fieldname}`，以及 `applySavedColumnWidths` 是否在表单 refresh 后执行。

---

## 技术要点（当前实现）

- **列宽生效**：通过全局 `<style id="cos-grid-col-widths">` 注入规则，选择器作用在带 `data-cos-grid-id` 的 `.grid-field` 下的 `.grid-static-col[data-fieldname="..."]`，使用 `!important` 覆盖 Bootstrap/Frappe 的 flex/width。
- **手柄挂载**：仅在表头第一行（`.grid-heading-row .grid-row:not(.filter-row)`）的 `.grid-static-col[data-fieldname]` 上追加手柄，避免行号/复选框列。
- **时机**：在 Form `refresh` 与 `grid-make-sortable` 后延迟执行（约 150ms / 80ms），确保 grid 已渲染。
