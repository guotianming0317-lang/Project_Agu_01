# 报告规则配置说明

当前项目把报告侧规则配置存放在：

- `app/report_rule_config.json`

你可以直接编辑这个文件，调整多种报告行为。

当前已覆盖的规则族包括：

- `a_share_mapping_rules`
- `industry_chain_mapping_rules`
- `stock_pool_structure_summary`
- `stock_pool_comparison_tags`
- `tomorrow_plan_rules`
- `strength_label_rules`
- `position_bias_rules`
- `task_result_summary_rules`
- `stage_alignment_templates`
- `detailed_alert_display`
- `market_focus_snapshot_display`
- `monitor_universe_display`
- `console_overview_display`

## 编辑后会影响什么

- `a_share_mapping_rules`
  会影响早盘报告里 A 股映射方向的兜底文案

- `industry_chain_mapping_rules`
  会影响当最强板块能映射到股票池 `chain_group` 时，早盘报告的优先行业链表达方式

- `stock_pool_structure_summary`
  会影响股票池健康度总结文案
  同时用于：
  - `python -m app.main validate-stock-pool`
  - 仪表盘的 `stock_pool_health` 模块

- `stock_pool_comparison_tags`
  会影响股票池结构变化标签的显示文字
  同时用于：
  - `python -m app.main validate-stock-pool`
  - 仪表盘结构变化区

- `tomorrow_plan_rules`
  会影响收盘报告中的次日观察重点文案

- `strength_label_rules`
  会影响早盘报告里的强弱标签输出

- `position_bias_rules`
  会影响早盘报告里的仓位倾向标签

- `task_result_summary_rules`
  会影响终端顶部 `Result:` 那句摘要文案

- `detailed_alert_display`
  会影响详细告警区块的字段顺序、标题、优先级标签等显示方式

## 文件结构

这是一个顶层 JSON 对象，常见结构如下：

```json
{
  "a_share_mapping_rules": [],
  "industry_chain_mapping_rules": [],
  "stock_pool_structure_summary": {},
  "stock_pool_comparison_tags": {},
  "tomorrow_plan_rules": [],
  "strength_label_rules": [],
  "position_bias_rules": [],
  "task_result_summary_rules": {},
  "stage_alignment_templates": {},
  "detailed_alert_display": {},
  "market_focus_snapshot_display": {},
  "monitor_universe_display": {},
  "console_overview_display": {}
}
```

## 重点字段说明

### `detailed_alert_display`

这是详细告警区块的配置对象。

常见键：

- `block_title`
- `empty_message`
- `title_template`
- `priority_labels`
- `fields`
- `field_sets`
- `style_variants`

`title_template` 可用变量：

- `{level}`
- `{priority_label}`

这层的作用是：

- 不改 Python 代码也能改详细告警标题
- 高价值告警和普通观察告警可用不同标题
- 不同任务可使用不同字段集合和显示顺序

### `market_focus_snapshot_display`

这是市场焦点快照区块的配置对象。

常见键：

- `block_title`
- `fields`
- `style_variants`

作用：

- 调整区块标题
- 调整字段顺序
- 按任务切换展示风格

### `monitor_universe_display`

这是监控池/阶段链观察区块的配置对象。

常见键：

- `block_title`
- `stage_chain_fields`
- `style_variants`

作用：

- 调整监控池观察区标题
- 调整阶段链字段顺序
- 支持不同任务使用不同展示风格

### `console_overview_display`

这是终端最顶部摘要行的配置对象。

常见键：

- `fields`
- `style_variants`

作用：

- 调整顶部摘要字段顺序
- 调整不同任务的摘要轻重

## 规则细节

### `a_share_mapping_rules`

每条规则应包含：

- `keywords`：关键词数组
- `suffix`：命中后接在板块名后的文本

匹配方式：

- 从上到下顺序匹配
- 只要板块名包含任一关键词，就命中该规则
- 如果没有命中，系统会走默认兜底文案

### `industry_chain_mapping_rules`

每条规则应包含：

- `keywords`
- `template`

可用模板变量：

- `{sector}`
- `{chain_groups}`
- `{primary_chain_group}`

匹配方式：

- 从上到下依次匹配
- 只要板块名命中任一关键词，就使用该模板
- `chain_groups` 来自 `app/universe/stock_pool.json` 中该板块对应股票的 `chain_group`

### `tomorrow_plan_rules`

每条规则应包含：

- `minimum_risk_count`
- `template`

可用模板变量：

- `{strongest_sector}`
- `{secondary_sector}`

匹配方式：

- 从上到下匹配
- 第一条满足风险阈值的规则生效

### `strength_label_rules`

每条规则应包含：

- `minimum_strength`
- `label`

匹配方式：

- 从上到下匹配
- 第一条满足强度阈值的规则生效
- 若都不满足，使用默认弱势标签

### `position_bias_rules`

每条规则应包含：

- `minimum_strength`
- `maximum_risk_count`
- `label`

匹配方式：

- 必须同时满足强度和风险两个条件
- 若无命中，则回退到默认谨慎标签

### `stock_pool_structure_summary`

这是一个对象，不是数组。

常见键：

- `empty_template`
- `balanced_template`
- `chain_group_template`
- `pool_type_template`
- `separator`
- `suffix`

可用变量：

- `{top_chain_group}`
- `{top_chain_group_count}`
- `{top_pool_type}`
- `{top_pool_type_count}`
- `{record_count}`

作用：

- 控制股票池结构总结句如何拼装

### `stock_pool_comparison_tags`

这是一个对象，不是数组。

作用：

- 保持 Python 里内部比较标签键名稳定
- 允许终端和仪表盘各自显示成更可读的中文标签

### `task_result_summary_rules`

这是一个按任务摘要风格分组的对象。

当前常见风格：

- `full_monitor`
- `pre_open`
- `morning_check`
- `midday_check`
- `afternoon_review`

每种风格下会有多个结论模板分支，例如：

- `red_alert`
- `high_value`
- `light_alert`
- `strong`
- `mixed`
- `forming`
- `average`
- `constructive`
- `watchable`
- `quiet`

可用模板变量：

- `{red_count}`
- `{alert_count}`
- `{orange_count}`
- `{high_value_count}`

匹配方式：

- Python 先决定当前该使用哪个结果分支
- 这层只负责最终显示文案
- 如果你只想改语气、措辞、风格，就在这里改

### `stage_alignment_templates`

这是详细告警里“阶段一致性说明”的模板对象。

常见键：

- `aligned_with_strength`
- `aligned_without_strength`
- `not_aligned`

可用模板变量：

- `{chain_group}`
- `{strength}`
- `{preferred_chain_groups}`

### `detailed_alert_display`

这是详细告警字段顺序和标签的配置对象。

常见键：

- `title_template`
- `fields`

`fields` 是有序数组，每项通常包括：

- `key`
- `label`
- `default`
- `enabled`

当前支持的字段键：

- `timestamp`
- `direction`
- `related_stocks`
- `message`
- `trend_state`
- `focus`
- `stage_alignment`

### `market_focus_snapshot_display`

这是 `Market Focus Snapshot` 区块的标题、字段顺序、字段标签配置。

当前常见字段键：

- `market_state`
- `observation`
- `strongest_sector`
- `second_sector`
- `top_sector_average_move`
- `top_focus_stocks`
- `alert_mix`

### `monitor_universe_display`

这是 `Monitor Universe Observation` 区块的配置。

当前常见字段键：

- `stage_chain_focus`
- `pool_coverage`
- `live_strength`
- `coverage_gap`

### `console_overview_display`

这是终端标题下方摘要行的配置。

当前常见字段键：

- `focus`
- `result`
- `environment`
- `database`
- `quote_source`
- `total_stocks`
- `high_priority_stocks`

## 安全修改建议

- 保持 JSON 合法：
  逗号、引号、括号都要正确

- 规则顺序尽量从更具体到更一般

- 如果两条规则都可能命中，排在前面的优先生效

- 如果你希望早盘报告映射到新的产业链表达，先确认
  `app/universe/stock_pool.json` 里的相关股票已经带上正确的 `chain_group`

## 推荐验证方式

修改 `app/report_rule_config.json` 或股票池中的产业链字段后，建议运行：

```text
python -m unittest tests.test_reports tests.test_pipeline tests.test_stock_pool -v
```
