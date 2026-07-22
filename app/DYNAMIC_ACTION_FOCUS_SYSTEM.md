# 首页动态优先阅读系统

本文档说明仪表盘首页是如何生成“先看哪里、先读什么”的动态阅读提示。

这层设计的目标很简单：

- 让首页提示尽量贴近当前市场状态
- 让阈值和文案可配置
- 避免为了加一点首页提示，就把主业务逻辑重新写成大量硬编码分支

## 当前用途

首页里的动作摘要卡片，不再只告诉你：

- 先打开哪个模块

它现在还尝试告诉你：

- 在这个模块里先看什么
- 先得出什么结论

只要模块和实时状态强相关，这个“首读提示”就是动态的。

当前已接入动态提示的模块包括：

- `latest_alerts`
- `stock_pool_health`
- `strongest_sector`
- `leader_summary`
- `next_session_action`

## 相关文件

主配置和主逻辑入口：

- `app/dashboard/presentation.py`
  - `build_dynamic_action_focus_specs()`
  - `build_dynamic_action_focus_fact_specs()`
- `app/dashboard/streamlit_app.py`
  - `_build_priority_action_content_focus_lines(...)`
  - `_resolve_dynamic_action_focus_overrides(...)`
  - `_build_dynamic_action_focus_facts(...)`
  - `_resolve_dynamic_action_focus_rule_spec(...)`
  - `_dynamic_action_focus_rule_matches(...)`
  - `_dynamic_action_focus_condition_matches(...)`

## 工作方式

这套系统目前分成三层：

1. 事实提取层

- 定义模块从哪里拿原始数据
- 定义每个事实如何归一化

2. 规则层

- 定义规则优先级顺序
- 定义触发条件
- 定义最终显示文案

3. 通用匹配层

- 生成归一化事实
- 按规则顺序逐条匹配
- 返回第一条命中的规则
- 把规则文案渲染进首页动作摘要卡片

## 事实配置结构

事实配置定义在：

- `build_dynamic_action_focus_fact_specs()`

每个模块可以定义：

- `source_key`
  - 可选，表示原始数据容器键名
- `container_transform`
  - 可选，表示对原始容器做一次标准化处理
- `fields`
  - 事实定义列表

每条事实定义可以包含：

- `fact_key`
  - 规则层使用的最终事实名
- `source_key`
  - 原始字段名
- `derive_from`
  - 当前支持从容器直接推导
- `transform`
  - 归一化规则
- `fallback`
  - 原始值不存在或非法时的回退值

当前支持的转换键：

- `safe_int`
- `safe_float`
- `normalized_lower_str`
- `bool`
- `len`

## 规则配置结构

规则配置定义在：

- `build_dynamic_action_focus_specs(copy_variant="default" | "business_cn")`

每个模块可以定义：

- `rule_order`
  - 规则执行顺序

每条规则可以定义：

- `conditions`
  - 条件列表
- `match`
  - 可选，默认是 `all`
  - 当前支持 `any`
- 可见文案字段：
  - `hint`
  - `field_hint`
  - `group_hint`
  - `conclusion_hint`

当前支持的条件操作符：

- `truthy`
- `in`
- `gt`
- `gte`
- `eq`
- `lte`
- `gte_field`
- `lte_field`

## 扩展步骤

如果以后要新增一个动态首读模块，建议按这个顺序做：

1. 先确定模块键名

- 通常和首页内容模块键保持一致，例如 `leader_summary`

2. 补事实提取配置

- 修改 `build_dynamic_action_focus_fact_specs()`
- 确定：
  - 原始数据源是哪一块
  - 规则真正需要看到哪些归一化事实

3. 补规则配置

- 修改 `build_dynamic_action_focus_specs()`
- 增加：
  - `rule_order`
  - 一条或多条规则
  - 必要时补 `available_state` 这类兜底状态

4. 保持事实命名可读

- 优先使用这类名字：
  - `leader_count`
  - `risk_level`
  - `avg_pct_chg`
- 尽量不要把完整业务结论直接塞进事实名里

5. 补回归测试

- 至少补两类：
  - 如果引入了新结构或新转换规则，补配置暴露测试
  - 如果引入了新首页行为，补动作摘要行为测试

6. 记入 `MEMORY.md`

- 简短记录这次新增的动态提示逻辑

## 极简示例

示例事实配置：

```python
"example_module": {
    "source_key": "example_summary",
    "container_transform": "normalize_dict",
    "fields": [
        {
            "fact_key": "score",
            "source_key": "score",
            "transform": "safe_int",
            "fallback": 0,
        },
        {
            "fact_key": "has_data",
            "derive_from": "container",
            "transform": "bool",
            "fallback": False,
        },
    ],
}
```

示例规则配置：

```python
"example_module": {
    "rule_order": ["high_state", "available_state"],
    "high_state": {
        "conditions": [
            {"field": "score", "op": "gte", "value": 5},
        ],
        "hint": "先看最高优先级行。",
        "field_hint": "先看优先级分数和标签。",
        "group_hint": "先看优先级明细组。",
        "conclusion_hint": "判断这个模块是否仍应放在最前面阅读。",
    },
    "available_state": {
        "conditions": [
            {"field": "has_data", "op": "truthy"},
        ],
        "hint": "先看当前摘要。",
        "field_hint": "先看摘要字段。",
        "group_hint": "先看摘要结果行。",
        "conclusion_hint": "判断这个模块对当前阅读是否仍然有用。",
    },
}
```

## 当前设计边界

这层系统是故意保持轻量的。

它当前不负责：

- 替代主场景决策器
- 替代页面布局优先级逻辑
- 从复杂大规则树里推导隐藏业务状态

它主要负责：

- 模块内部的“首读提示”
- 基于阈值的可配置文案切换

## 写规则时的建议

- `rule_order` 保持短而明确
- 每个模块优先控制在 2 到 4 条规则
- 只要模块有数据，就尽量提供一个容易理解的兜底规则
- 阈值保持可读，便于后续快速复核
- 如果一条规则开始需要很多条件，优先考虑先引入一个更简单的归一化事实

## 何时再继续抽象

只有在下面情况变多时，才值得继续做下一轮重构：

- 很多模块都需要复用同一种事实推导
- 转换键开始超出简单归一化工具的范围
- 规则开始需要复杂嵌套业务表达式
- 同一套规则族要复用到首页动作摘要以外的场景

在那之前，当前两层结构仍然是最合适的：

- 事实层：`build_dynamic_action_focus_fact_specs()`
- 规则层：`build_dynamic_action_focus_specs()`
