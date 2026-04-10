---
name: agent-standard-flow-create-item
description: 从粗略用户描述创建物料的端到端标准流程：解析→匹配模板→（若无则创建模板）→在模板约束下创建 Item。优先 FAC MCP。
---

# 创建物料标准流程（Create Item Standard Flow）

## 适用范围

- 用户给出**粗略描述**（如「六角头螺栓 M16×60 4.8级 发黑 50个」「平垫 M16 镀锌 50个」）
- 需在系统中创建对应 Item，且可能涉及**新建参数模板**

## 流程概览

```
粗略描述 → 阶段1解析 → 阶段2匹配模板 → [未匹配] 阶段3创建模板 → 阶段4创建物料
```

## 阶段 1：解析为结构化物料清单

从用户描述提取：

| 字段 | 说明 | 示例 |
|------|------|------|
| 基础名 | 物料类型 | 六角头螺栓、平垫圈、弹簧垫圈、1型六角螺母、膨胀螺栓 |
| 规格参数 | 尺寸/型号 | M16×60、M16、M20×150 |
| 强度/性能等级 | 螺栓 4.8/8.8，螺母 8级/10级 | 8.8、4.8、8级 |
| 表面处理 | 发黑、镀锌、热镀锌 | 发黑 |
| 材质 | 可选，默认 Q235B | Q235B |
| 执行标准 | 螺栓 4.8→GB/T 5780，8.8→GB/T 5783 | GB/T 5783 |
| 数量 | 需求数量 | 50 |

**参考**：`scripts/production_required_to_dev_specs.py`、`scripts/normalize_bolt_nut_washer_spec.py` 的解析逻辑。

## 阶段 2：匹配物料参数模板

按基础名/类型映射到 `Item Parameter Template`：

| 基础名/类型 | 模板名 |
|-------------|--------|
| 六角头螺栓、外六角螺栓 | 标准模板 - 螺栓 |
| 平垫圈、平垫 | 标准模板 - 平垫 |
| 弹簧垫圈、弹垫 | 标准模板 - 弹垫 |
| 1型六角螺母、螺母 | 标准模板 - 螺母 |
| 膨胀螺栓 | 标准模板 - 膨胀螺栓 |
| 微型断路器(MCB) | 标准模板 - 微型断路器(MCB) |
| 墙面五孔插座 | 标准模板 - 墙面插座（五孔） |
| 导轨电源（订货号为主，如西门子 SITOP） | 标准模板 - 导轨电源（订货号驱动） |
| 导轨电源（明纬类可拆系列型号） | 标准模板 - 导轨式开关电源 |
| 导轨/螺钉式接线端子、PT 类 | 标准模板 - 接线端子 或 标准模板 - 固定式接线端子（择更贴切者） |
| 分线端子 | 标准模板 - 分线端子 |
| 冷压端子 | 标准模板 - 冷压端子 |
| 钢板 | 标准模板 - 钢板 |
| 压带轮 | 标准模板 - 压带轮 |
| 槽型托辊组 | 标准模板 - 槽型托辊组 |

- **匹配到**：进入阶段 4
- **未匹配**：进入阶段 3

**禁止**：在系统中**已存在**与品类对应的「标准模板 - …」时（尤其端子、指示灯、按钮等），仍选用「标准模板 - 非标」。选型前可对 `Item Parameter Template` 按名称关键字检索。

## 阶段 3：创建新参数模板（仅当阶段 2 未匹配）

1. **参考模板**：读取「标准模板 - 参考」（dev）或最相近的现有模板
2. **定义参数**：基础名（Doctype→Item Base Name）、尺寸参数（Integer/Float）、表面处理（Doctype→Item Surface）、材质（Doctype→Item Material）、执行标准（Doctype→Executive Standard）等。**Format 参数**：`value_format` 与 `parameter_default_value` 必须同时填充。
3. **创建**：`create_document` 创建 `Item Parameter Template`，子表 `parameters` 为 `Item Parameter Template Definition`
4. **复核理由**：输出为何需要新模板、参考了哪个模板、参数设计依据

**非标兜底**：仅当物料确属无法归入任何现有标准细分类时，才使用「标准模板 - 非标」；能归类的应新建专用标准模板而非长期用非标。

**参数定义参考**：`docs/Doctypes/Item_Parameter_Template_Definition.prompt.md`

**结构参考**：`vendor/cos/cos/patches/v1_2/add_belt_conveyor_core_item_templates.py` 的 `_param` 与模板构建方式。

## 阶段 4：在模板约束下创建物料

按 [create-item-from-parameter-template](../create-item-from-parameter-template/SKILL.md) 与 [item-creation-guide-for-agent](../../../../../docs/item-creation-guide-for-agent.md) 执行：

- **基础名**：必填；不存在则创建 Item Base Name
- **技术标准号**：推荐；不存在则创建 Executive Standard
- **规格**：必填
- **品牌、材质、表面处理、颜色**：建议填写
- **单位**：必要时创建多单位并配置转换系数
- **描述**：严格按照物料参数模板的「详细描述」Format 规范格式
- 新建基础资料时输出复核理由

## 交叉引用

| 主题 | 文档/技能 |
|------|-----------|
| 详细流程与映射表 | `docs/agent-standard-flows.md` |
| 按模板创建物料 | `create-item-from-parameter-template` |
| 物料编码规则 | `docs/item-encoding-rules.md` |
| 模板结构参考 | dev 中「标准模板 - 参考」 |
