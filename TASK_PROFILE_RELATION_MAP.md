# 任务画像关系图

这份文档用于解释：一个任务从配置到最终输出，中间会经过哪些层。

它主要回答一个实际问题：

“如果我想改一个任务，第一步应该先改哪一层配置？”

## 一个任务的完整路径

以 `morning-check` 这类调度任务为例，当前依赖路径大致是：

1. `scheduled_jobs`
   决定任务什么时候运行，以及在调度视图里显示什么名字和说明。
2. `task_display_groups`
   决定任务在调度状态页里归到哪个分组、按什么顺序显示。
3. `job_output_strategies`
   决定任务继承哪个 `view_template`，也就是使用哪套输出区块组合。
4. `view_templates`
   决定共享阅读模式：
   包括区块开关、展示变体、终端可读模式名。
5. `job_intent_strategies`
   决定任务的业务框架：
   标题、副标题、关注标签、告警包、产业链包、结果摘要风格。
6. `alert_type_bundles`
   决定某类摘要重点强调哪些告警类型。
7. `chain_group_bundles`
   决定某类任务重点盯哪些产业链分组。
8. `chain_group_bundle_meta`
   给这些产业链分组包补上可读名称和一句话说明。
9. `task_result_summary_decision_rules`
   决定在实时计数和上下文下，应该落到哪种摘要结果分支。
10. `app/report_rule_config.json`
   提供最终显示出来的那句中文文案。

## 各层职责

| 配置层 | 主要职责 | 适合改什么 |
| --- | --- | --- |
| `scheduled_jobs` | 任务时间与显示名称 | 调度时间、任务标签、一句话用途 |
| `task_display_groups` | 调度视图里的分组与顺序 | 任务在状态页的展示位置 |
| `view_templates` | 可复用阅读模式 | 共享版式、共享区块、共享阶段强调 |
| `job_output_strategies` | 任务与模板的绑定关系 | 某个任务应该用哪种阅读模式 |
| `alert_type_bundles` | 可复用告警重点集合 | 某类摘要里强调哪些告警 |
| `chain_group_bundles` | 可复用产业链范围集合 | 某个任务重点看哪些产业链分组 |
| `chain_group_bundle_meta` | 产业链包的可读名称 | 面向业务阅读的一句话标签和说明 |
| `job_intent_strategies` | 任务级业务意图 | 标题、副标题、关注点、策略提示 |
| `task_result_summary_decision_rules` | 结果摘要切换规则 | 何时判定为强、谨慎、安静等状态 |

## 当前任务映射

| 任务 ID | 视图模板 | 告警重点包 | 产业链包 | 摘要风格 |
| --- | --- | --- | --- | --- |
| `manual` | `manual_full_view` | 无固定限制 | `full_monitor_chains` | `full_monitor` |
| `pre-open-check` | `pre_open_view` | `overnight_news_only` | `overnight_news_impact` | `pre_open` |
| `morning-check` | `opening_task_view` | `opening_theme_confirmation` | `opening_confirmation_chains` | `morning_check` |
| `midday-check` | `mid_session_task_view` | `mid_session_expansion`、`mid_session_structure_focus` | `mid_session_expansion_chains` | `midday_check` |
| `afternoon-review` | `close_review_task_view` | `mid_session_structure_focus`、`mid_session_expansion` | `close_retention_chains` | `afternoon_review` |

## 快速修改指引

如果你想：

- 改任务运行时间：
  改 `scheduled_jobs`
- 改任务在调度视图里的显示名：
  改 `scheduled_jobs.label` 或 `scheduled_jobs.summary`
- 让多个任务共用一套新版式：
  新增或修改一个 `view_template`
- 让某个任务切换到另一套现成版式：
  改该任务在 `job_output_strategies` 里的模板绑定
- 改某个阶段重点强调哪些告警：
  改 `alert_type_bundles`
- 改某个阶段重点强调哪些产业链范围：
  改 `chain_group_bundles`，或切换 `job_intent_strategies` 里的引用
- 只改可读名称，不改底层逻辑：
  改 `alert_type_bundles.label`、`summary` 或 `chain_group_bundle_meta`
- 改顶部任务文案和业务语气：
  改 `job_intent_strategies`
- 改结果什么时候变强、变谨慎、变安静：
  改 `task_result_summary_decision_rules`

## 更稳妥的修改顺序

当一个任务需要业务调整时，通常建议按这个顺序改：

1. 先改标签和摘要说明
2. 再改告警包或产业链包成员
3. 再改任务和模板的绑定关系
4. 最后再改结果摘要阈值

这样可以减少“表现层改动”和“行为层改动”混在同一次修改里，便于定位问题。
