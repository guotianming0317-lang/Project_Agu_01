# 任务画像说明

本文档说明当前阶段调度任务和手动任务使用的任务画像结构。

如果你更关心“一个任务究竟受哪些配置层影响”，请看：

- `TASK_PROFILE_RELATION_MAP.md`

## 这份文档的作用

当前项目把任务输出拆成了几层：

- 监控周期数据生成
- 输出区块组合策略
- 任务意图策略
- 任务画像配置

这样做的好处是：

- 不同任务可以复用同一份底层监控结果
- 但可以展示不同的标题、摘要、告警重点和阅读顺序
- 调整调度行为时，不必反复修改主流程代码

## 阅读模式

系统在原始监控结果和最终终端输出之间，增加了一层可复用的“阅读模板”。

终端里常见的几个概念：

- `view-mode`：终端显示的可读模式名
- `view-summary`：这个模式适合做什么的简短说明
- `view_template`：配置文件中的底层模板键名

这意味着一个任务不再只靠任务 ID 决定输出内容，而是可以继承某个共享阅读模板，同时保留自己的时间和业务意图。

## 当前阅读模板

### `manual_full_view`

- 终端模式名：`Manual Full View`
- 含义：用于手动全流程预览，输出最完整
- 当前使用任务：`manual`

### `pre_open_view`

- 终端模式名：`Pre-open View`
- 含义：聚焦隔夜风险和开盘前准备
- 当前使用任务：`pre-open-check`

### `opening_task_view`

- 终端模式名：`Opening Task View`
- 含义：聚焦开盘风险、主题确认、早盘告警
- 当前使用任务：`morning-check`

### `mid_session_task_view`

- 终端模式名：`Mid-session Task View`
- 含义：聚焦盘中扩散、结构强度、盘中告警
- 当前使用任务：`midday-check`

### `close_review_task_view`

- 终端模式名：`Close Review View`
- 含义：聚焦收盘结构、尾盘风险和复盘总结
- 当前使用任务：`afternoon-review`

## 当前任务说明

### `manual`

典型用途：

- 本地完整演示
- 手动抽查
- 端到端验证

当前时间：

- 默认不自动调度

当前阅读模式：

- `Manual Full View`
- 配置键：`manual_full_view`

当前输出区块：

- 早盘报告
- 市场焦点快照
- 监控池结构观察
- 盘中告警摘要
- 详细告警
- 收盘报告
- 收盘告警摘要

当前结果摘要风格：

- 用 `risk elevated`、`flow active`、`flow light`、`flow quiet` 这类结果键生成结论

### `pre-open-check`

典型用途：

- 开盘前准备
- 隔夜新闻与风险扫描
- 开盘前快速确认

当前时间：

- `09:15`

当前阅读模式：

- `Pre-open View`
- 配置键：`pre_open_view`

当前输出区块：

- 早盘报告
- 市场焦点快照
- 监控池结构观察

当前任务意图：

- 标签：`pre-open-preparation-check`
- 告警重点：`news_flash`
- 风格：更短、更偏隔夜风险

### `morning-check`

典型用途：

- 开盘后风险检查
- 判断主题龙头是否开始明确

当前时间：

- `09:35`

当前阅读模式：

- `Opening Task View`
- 配置键：`opening_task_view`

当前输出区块：

- 早盘报告
- 市场焦点快照
- 监控池结构观察
- 盘中告警摘要
- 详细告警

当前任务意图：

- 标签：`opening-risk-and-theme-check`
- 告警重点：`news_flash`、`materials_focus`
- 风格：只保留高价值、短列表输出

### `midday-check`

典型用途：

- 盘中扩散检查
- 判断行情是否从个股走向板块扩散

当前时间：

- `11:30`

当前阅读模式：

- `Mid-session Task View`
- 配置键：`mid_session_task_view`

当前输出区块：

- 市场焦点快照
- 监控池结构观察
- 盘中告警摘要
- 详细告警

当前任务意图：

- 标签：`mid-session-expansion-check`
- 告警重点：`sector_move`、`materials_focus`、`news_flash`
- 风格：中等长度，更关注扩散

### `afternoon-review`

典型用途：

- 尾盘与收盘复盘
- 判断强度是否保持到收盘

当前时间：

- `14:45`

当前阅读模式：

- `Close Review View`
- 配置键：`close_review_task_view`

当前输出区块：

- 市场焦点快照
- 监控池结构观察
- 详细告警
- 收盘报告
- 收盘告警摘要

当前任务意图：

- 标签：`close-review-and-structure-check`
- 告警重点：`sector_move`、`materials_focus`、`news_flash`
- 风格：更偏收盘总结，覆盖更广

## 本地手动预览

你可以直接在本地运行这些任务输出：

```bash
python -m app.main run-job-now
python -m app.main run-job-now pre-open-check
python -m app.main run-job-now morning-check
python -m app.main run-job-now midday-check
python -m app.main run-job-now afternoon-review
```

## 后续改行为时去哪里改

如果你后面要调整任务行为，主要入口在：

- `app/task_profile_config.json`
  - `scheduled_jobs`
  - `task_display_groups`
  - `view_templates`
  - `job_output_strategies`
  - `job_intent_strategies`
  - `task_result_summary_decision_rules`
- `app/TASK_PROFILE_CONFIG_FORMAT.md`
  - 任务画像配置字段说明
- `app/scheduler.py`
  - 调度注册与任务画像加载
- `app/pipeline.py`
  - 控制终端输出构建和结果摘要选择
- `app/alerts/notifier.py`
  - 控制告警摘要筛选与生成

## 安全修改原则

如果你只想改：

- 任务运行时间：改 `scheduled_jobs`
- 任务列表分组和顺序：改 `task_display_groups`
- 某种阅读模板的版式和区块：改 `view_templates`
- 某个任务用哪种模板：改 `job_output_strategies`
- 某个任务强调哪些告警：改 `job_intent_strategies`
- 结果摘要什么时候从一般变强或变谨慎：改 `task_result_summary_decision_rules`

这样可以尽量避免“只是想调度输出，却误动主业务逻辑”。

## 快速决策建议

如果你的目标是：

- 让多个任务一起增删某个输出区块：优先改一个 `view_template`
- 只让某个任务改用另一种现成版式：改该任务的模板引用
- 只改某个任务的告警偏好，不改版式：改该任务的意图策略
- 只改顶部总结句的判定阈值：改结果摘要判定规则
- 不动业务逻辑，只改终端可读标签：改模板里的 `label` 或 `summary`
