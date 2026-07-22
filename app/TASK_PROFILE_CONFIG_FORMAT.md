# 任务画像配置说明

当前项目把调度任务画像配置存放在：

- `app/task_profile_config.json`

相关辅助说明：

- `TASK_PROFILE_RELATION_MAP.md`

你可以通过编辑这个文件，调整：

- 任务执行时间
- 任务列表分组与顺序
- 输出区块组合
- 任务标题与意图
- 结果摘要判定阈值

## 当前主要配置族

- `scheduled_jobs`
- `task_display_groups`
- `task_overview_display`
- `output_profiles_display`
- `view_templates`
- `job_output_strategies`
- `alert_type_bundles`
- `chain_group_bundles`
- `chain_group_bundle_meta`
- `job_intent_strategies`
- `task_result_summary_decision_rules`

## 编辑后会影响什么

- `scheduled_jobs`
  会影响默认调度任务的注册时间

- `task_display_groups`
  会影响调度状态页中的分组和显示顺序

- `task_overview_display`
  会影响共享任务总览区块的标题、字段顺序和字段名称

- `output_profiles_display`
  会影响共享输出画像区块的标题、区块标签和意图前缀

- `view_templates`
  会影响可复用的阶段视图模板，例如开盘版、盘中版、收盘版

- `job_output_strategies`
  会影响每个任务打印哪些主要输出区块

- `job_intent_strategies`
  会影响任务标题、关注副标题、摘要偏好和结果摘要风格

- `task_result_summary_decision_rules`
  会影响一个任务在什么情况下变成 `red_alert`、`strong`、`forming`、`quiet`

## 文件结构

整个文件是一个顶层 JSON 对象，大致结构如下：

```json
{
  "scheduled_jobs": [],
  "task_display_groups": [],
  "task_overview_display": {},
  "output_profiles_display": {},
  "view_templates": {},
  "job_output_strategies": {},
  "alert_type_bundles": {},
  "chain_group_bundles": {},
  "chain_group_bundle_meta": {},
  "job_intent_strategies": {},
  "task_result_summary_decision_rules": {}
}
```

## 关键字段说明

### `scheduled_jobs`

每条任务至少应包含：

- `id`：稳定任务 ID
- `hour`：本地小时
- `minute`：本地分钟

建议补充的业务字段：

- `label`：可读任务名称
- `summary`：一句话说明它主要检查什么

示例：

```json
{
  "id": "midday-check",
  "label": "Midday Check",
  "summary": "Breadth expansion and mid-session structure scan.",
  "hour": 11,
  "minute": 30
}
```

### `job_output_strategies`

这是一个按任务 ID 分组的对象。

常见布尔字段：

- `include_morning_report`
- `include_market_focus_snapshot`
- `include_monitor_universe_observation`
- `include_intraday_digest`
- `include_detailed_alerts`
- `include_evening_report`
- `include_close_digest`
- `include_latest_review`
- `view_template`

作用：

- 不改主流程代码也能改任务输出区块组合
- `include_detailed_alerts` 控制整个详细告警区，不只是单条告警卡片
- 一个任务可以直接继承某个可复用视图模板

### `task_display_groups`

这是一个有序数组，用于定义任务显示分组。

每项通常包含：

- `key`
- `label`
- `job_ids`

作用：

- 控制调度状态页和类似概览页里的任务顺序
- 让手动任务和自动任务在视觉上分开

校验规则：

- 不允许同一个任务 ID 出现在多个分组里
- 分组只能引用已存在的任务

### `job_intent_strategies`

这是一个按任务 ID 分组的对象。

常见字段：

- `intraday_digest`
- `close_digest`
- `intent_label`
- `console_title`
- `console_subtitle`
- `result_summary_style`
- `display_variant`
- `detailed_alert_style_variant`
- `view_template`

作用：

- 控制每个任务的业务语气和关注重点
- 允许同一个任务在多个区块上共享一种显示变体
- 允许详细告警使用任务专属风格

### `alert_type_bundles`

这是一个按“可复用告警组合包名称”分组的对象。

支持两种形态：

1. 旧版数组形式：

```json
["news_flash", "materials_focus"]
```

2. 带元信息的对象形式：

```json
{
  "label": "Opening Theme Confirmation",
  "summary": "Focus on early news and materials-theme confirmation during the open.",
  "items": ["news_flash", "materials_focus"]
}
```

作用：

- 让多个任务复用同一套告警重点组合
- 缩短任务层配置长度
- 可选地给组合包补上可读名称和一句话说明

### `chain_group_bundles`

这是一个按“可复用产业链组合包名称”分组的对象。

当前常见形式是数组：

```json
["材料", "气体", "设备"]
```

作用：

- 让多个任务复用同一套产业链关注范围
- 避免在多个任务里重复写同一串链条列表

### `chain_group_bundle_meta`

这是 `chain_group_bundles` 的可读元信息层。

示例：

```json
{
  "opening_confirmation_chains": {
    "label": "Opening Confirmation Chains",
    "summary": "Prioritize materials, gases, and equipment during opening confirmation."
  }
}
```

作用：

- 保持底层 ID 稳定
- 同时让终端摘要更容易阅读

### `view_templates`

这是一个按模板名分组的对象。

常见字段：

- `display_variant`
- `detailed_alert_style_variant`
- `output_strategy`

作用：

- 定义开盘、盘中、收盘等可复用阅读模板
- 把输出区块开关和显示风格打包在一起
- 防止多个任务共享版式时出现漂移

### `task_overview_display`

这是任务总览展示层配置。

常见键：

- `heading`
- `display_groups_heading`
- `fields`

每个 `fields` 项通常包含：

- `key`
- `label`

当前支持的字段键包括：

- `scheduled_job_count`
- `scheduled_jobs`
- `scheduled_job_labels`
- `scheduled_timings`
- `result_summary_styles`
- `manual_preview_jobs`
- `scheduled_day_flow_jobs`

作用：

- 控制任务总览标题
- 控制总览字段顺序
- 控制字段显示名称

### `output_profiles_display`

这是输出画像展示层配置。

常见键：

- `heading`
- `intent_label_prefix`
- `block_labels`

当前支持的区块标签键：

- `include_morning_report`
- `include_market_focus_snapshot`
- `include_monitor_universe_observation`
- `include_intraday_digest`
- `include_detailed_alerts`
- `include_evening_report`
- `include_close_digest`

作用：

- 控制输出画像标题
- 控制各输出区块的可读名称
- 控制任务意图行前缀

### `task_result_summary_decision_rules`

这是一个按摘要风格分组的对象。

每种风格下是一组有顺序的规则。

每条规则至少应包含：

- `case`

可选阈值字段：

- `minimum_red_count`
- `minimum_alert_count`
- `minimum_orange_count`
- `minimum_high_value_count`

匹配方式：

- 从上到下匹配
- 第一条满足条件的规则生效
- 只有 `case` 没有阈值的规则，相当于最终兜底分支
- 最终显示文案在 `app/report_rule_config.json`

## 安全修改原则

如果你只想改：

- 任务运行时间：改 `scheduled_jobs`
- 调度视图里的任务名称：改该任务的 `label` 或 `summary`
- 输出哪些区块：改 `job_output_strategies`
- 标题和关注点：改 `job_intent_strategies`
- 什么时候从 `mixed` 变成 `strong`：改 `task_result_summary_decision_rules`
- 最终显示那句中文文案：改 `app/report_rule_config.json`

## 推荐验证方式

修改 `app/task_profile_config.json` 后，建议运行：

```text
python -m app.main validate-task-profiles
```

如果要跑更完整的验证，可以运行：

```text
python -m unittest tests.test_scheduler tests.test_pipeline tests.test_main -v
```

当前 `validate-task-profiles` 会摘要显示：

- 源文件路径
- 已配置调度任务数量
- 调度任务顺序
- 当前启用的结果摘要风格
- 手动预览任务
- 日间调度主链任务
- 当前分组配置
