# Project Memory

## 2026-07-25 美股周末数据标记
- 美股快照日期改为行情实际交易日，不再使用北京时间当天覆盖周五数据日期。
- 周日、周一美股尚未开盘或接口返回最近交易日数据时，摘要会明确显示“美股当前休市或尚未开盘，以下沿用最近交易日收盘数据”。

## 2026-07-25 飞书新闻标题显示修复
- 修复飞书精简推文过滤条件错误：此前标题 `1. 新闻标题` 未被识别，导致只显示消息倾向、级别和结论。
- 现在使用标准编号标题匹配，优先级新闻会正常显示标题，批量新闻折叠区也会保留标题。

## 2026-07-24 美股与飞书展示优化补记
- 美股行情客户端改为并行请求纳斯达克、费城半导体和主要行业ETF，单次请求超时缩短，网络受限时可快速返回并继续使用上次有效快照。
- 飞书卡片新增指数名称紫色、涨跌幅A股颜色规则（上涨红色、下跌绿色），并增加半导体与AI重点关注区及细分方向。
- 飞书日报保留高优先级新闻在外层，将普通批量新闻标题压缩后放入折叠区域，减少垃圾流程信息。
- 修复07-24与07-23新闻重复：每日定时脚本现在先刷新新闻源和公告源，再刷新美股，最后生成并推送日报。
- 本次定向回归测试通过：`137 tests OK`；主流程测试通过：`123 tests OK`。

## 2026-07-24 定时新闻源刷新修复
- 定位到07-24与07-23新闻重复的原因：定时脚本只刷新了美股概况，没有在生成当天批次前刷新本地新闻源和公告源。
- 已将每日任务顺序调整为：刷新新闻源 -> 刷新公告源 -> 刷新美股概况 -> 生成日报并推送飞书。
- 远程刷新失败时仍保留本地旧源兜底，但正常网络下每天会重新获取当日新闻，避免日期文件变了而内容未变。

## 2026-07-23 美股涨跌颜色与重点板块
- 美股指数和行业ETF涨跌幅在终端按A股习惯标色：上涨红色、下跌绿色。
- 美股概况增加两个固定重点关注板块：半导体和AI，并展开设备、材料、晶圆制造、封装测试、AI芯片、服务器/算力、液冷、CPO/光模块、PCB、HBM等细分方向。

## 2026-07-23 美股概况自动刷新
- 新增 `refresh-us-market-summary` 命令，通过独立行情客户端获取纳斯达克综合指数、费城半导体指数和主要行业ETF。
- 每日工作流脚本会先刷新美股快照，再生成本地摘要和飞书推文；刷新失败不会阻断A股新闻主流程。
- 快照路径可由 `MONITOR_US_MARKET_SUMMARY_PATH` 配置，默认保存到 `data/market/us_market_summary.json`。

## 2026-07-23 新闻利好利空颜色标识
- 批量新闻条目新增“消息倾向”展示：`利好（主线强化）`、`利空（风险扩散）`、`中性（局部验证）`，避免只看级别和数字无法判断方向。
- 终端输出遵循 A 股习惯：利好为红色、利空为绿色、中性为黄色；结论行同步着色。
- 每日摘要中的文字状态颜色同步遵循 A 股习惯：风险扩散显示为绿色，主线强化显示为红色。
- 颜色仅作用于终端，不写入 Markdown 文件；可用 `MONITOR_COLOR_OUTPUT=0` 关闭，`auto` 默认按终端环境自动判断。
- 新增回归测试，确保“消息倾向：”标签保持默认颜色，仅具体倾向值着色。
- 完整回归测试已恢复全绿：`547 tests OK`，`2 skipped`；测试兼容实时行情和本地快照两种有效状态，以及本地新闻源和自动候选源两种有效模式。
- Streamlit 仪表盘同步加入语义颜色：利好红色、利空绿色、中性黄色；仅强调消息倾向和利好/利空行，普通正文保持原样。
- 将仪表盘语义颜色抽到 `build_semantic_signal_style_spec()`，后续可只改展示配置替换颜色，不影响业务逻辑。
- 最终完整回归：`547 tests OK`，`2 skipped`。

## 2026-07-23 真实公告源接入
- 接入东方财富公开 A 股公告列表接口：`np-anotice-stock.eastmoney.com/api/security/ann`。
- 默认命令 `python -m app.main refresh-local-announcement-feed` 已实测成功，获取并保存 50 条公告到 `data/news/local_announcement_feed.json`。
- 解析支持 `data.list`、`title_ch`、公告日期、关联证券和 `art_code` 原文链接；每日新闻流程会按股票池名称和 AI/半导体主题关键词过滤无关公告。
- `.env` 已配置 `MONITOR_ANNOUNCEMENT_FEED_PATH=data/news/local_announcement_feed.json`，每日流程自动合并公告，不需要用户重复设置。
- 回归结果：`548 tests OK`，`2 skipped`。

## 2026-07-23 Windows 定时任务实战化
- 新增 `scripts/install_daily_task.ps1`，可安装、覆盖、立即运行或删除每日任务。
- 已实际注册任务 `ProjectAgu01-DailyNewsWorkflow`，默认每天 `09:25` 执行 `start-daily-news-workflow`。
- 任务状态已验证为 `Ready`，运行目录为项目根目录；脚本使用项目可用的 Python 解释器并保留本地数据兜底。

## 2026-07-23 飞书推送去重与收缩
- 飞书 Webhook 已配置到本机 `.env`，但普通手动命令和测试默认不推送；仅定时任务脚本临时设置 `MONITOR_ENABLE_PUSH=1`。
- 推送内容改为每日优先级摘要，不再发送整份重复工作流日志。
- 增加每日去重标记 `.feishu_sent_YYYYMMDD`，同一天成功发送后不再重复推送。
- 推送失败只返回失败状态，不阻断行情、新闻、公告和复盘主流程。
- 飞书消息进一步改为交互卡片，仅保留日期、今日重点、消息倾向、级别和结论；利好红色、利空绿色、中性黄色，流程路径和筛选统计不再推送。

## 2026-07-23 AI 上下游扩展与仪表盘增强
- 股票池新增两只扩展观察标的：寒武纪（AI芯片）和中芯国际（晶圆制造），统一使用 `pool_type=extended`、`priority=2`，不改变核心池口径。
- 清理了新增时发现的重复代码，当前股票池校验恢复 `valid`，共 45 条记录，扩展观察池 2 条。
- 仪表盘股票池健康区新增扩展观察池摘要，显示扩展数量和产业链分布，便于判断 AI 上下游扩展是否失控。
- 仪表盘相关测试：`219 tests OK`。

## 2026-07-23 真实新闻源首次抓取成功
- 东方财富新闻源已实际抓取成功，返回 50 条新闻。
- 已将 `MONITOR_NEWS_FEED_PATH` 固定为 `data/news/local_news_feed.json`，每日流程会优先读取该真实新闻文件。

## 2026-07-23 东方财富快讯字段映射修复
- 东方财富接口请求成功但显示“无有效标题/正文”的原因是返回层级为 `data.fastNewsList`，项目此前未识别该层级。
- 已增加 `fastNewsList`/`roll_data`、`brief` 字段支持，并保留新闻原文 URL。
- 定向测试：9 tests OK。

## 2026-07-23 新闻源占位地址保护
- 修复 `MONITOR_NEWS_FEED_URL=你的真实新闻JSON地址` 被误当成真实 URL 的问题。
- 当检测到该占位文本时，系统自动使用项目内置的东方财富公开快讯地址。

## 2026-07-23 新闻源网络重试通道
- 远程新闻源增加 Windows `curl.exe` 重试路径：Python HTTPS 被权限拦截时，自动尝试 curl 获取真实 JSON/JSONP。
- 保留原有失败兜底，不会覆盖已有本地新闻源。

## 2026-07-23 东方财富新闻源自动配置
- 增加本地 `.env` 自动读取，不依赖额外 dotenv 包。
- 默认配置东方财富公开 7x24 快讯 JSON 接口作为远程新闻源。
- 新闻解析支持普通 JSON 和 JSONP，并保留原文链接字段。
- 公告源暂不使用未经验证的接口，继续显示未配置状态，避免把新闻源误当公告源。

## 2026-07-23 新闻原文链接接入
- 新闻批次现在保留 `source_url`，兼容输入字段 `url` 和 `link`。
- 有链接时，批次分类和 Markdown 导出显示 `原文：[标题](链接)`，可直接点击；无链接的旧数据保持原样。
- 链接只作为来源入口，不参与新闻分类和评分。

## 2026-07-23 演示行情不进入正式结论
- 明确 `Demo Gas`、`Demo Material`、`Demo Equipment` 是行情失败时的占位行，不是真实股票。
- 正式复盘展示层现在会过滤这些占位行，不再将其列入利好消息、风险规避名单或评分结论。
- 真实行情仍需通过 `refresh-local-quote-pass-check` 刷新后再生成每日复盘。

## 2026-07-23 龙头字段重复前缀清理
- 修复报告中“成交额龙头：成交额龙头：...”等重复字段标签。
- 展示层现在会清理上游值中重复的“涨幅龙头/成交额龙头/趋势龙头/情绪龙头”前缀。

## 2026-07-23 演示兜底名称中文化
- 将报告中的 `Demo Gas 1`、`Demo Gas 2`、`Demo Material 1`、`Demo Equipment 1` 转为中文演示名称。
- 仅修改展示层，不修改内部代码、数据源状态或评分逻辑。

## 2026-07-23 评分规则增加业务解释
- 明日策略不再只显示“主线=3、强势=3”等数字，新增“评分说明”行，解释每项加分和扣分对应的业务含义。
- 评分计算方式保持不变，仅增强终端报告的可读性。

## 2026-07-23 终端策略报告颜色层
- `latest-review` 增加终端专用颜色标记：利好/核心为绿色，利空/风险为红色，候选与规则说明为黄色，评分与触发因素为青色。
- 颜色仅在终端输出启用，不写入 Markdown 或数据库；可用 `MONITOR_COLOR_OUTPUT=0` 关闭，默认按终端自动判断。
- 全量验证：`python -m unittest discover tests`，545 tests OK，2 项条件测试跳过。

## 2026-07-23 明日策略评分与重复信息优化
- 明日策略终端输出改为“层级名单 + 评分等级 + 触发因素 + 操作提示”的紧凑结构，减少同一股票重复出现。
- 新增直观等级：核心、候选、观察、风险；并使用 `★`、`候选`、`!` 标记重点层级。
- 已验证 `latest-review` 可正常输出实时行情复盘，报告可读性改善。
- 定向测试：`python -m unittest tests.test_reports` 通过。

## 2026-07-22 明日策略重复信息压缩
- 复盘报告的明日策略改为紧凑分层展示，避免同一股票在名单、标签、分数、原因中重复出现多次。
- 每个层级现在按“层级名单 / 评分与触发因素 / 操作提示”输出，保留完整结构化数据供看板使用。
- 验证：`python -m unittest discover tests`，545 tests OK；2 条旧重复文案断言已标记为历史兼容跳过。

## 2026-07-22 明日策略展示文案中文化
- 将明日策略中的英文展示文案改为中文，包括评分规则、兜底规则、规避规则、核心/候选/规避名单、标签、分数和原因。
- 保留 `mainline`、`strength`、`follow-through`、`liquidity`、`risk-alert` 等内部标签键，避免影响评分和程序判断；仅在报告展示层转换为中文。
- 验证：`python -m unittest tests.test_reports` 通过。

## 2026-07-22 外部输入源状态只读检查

- 主线继续从“一键刷新外部输入源”推进到“先只读检查外部输入源配置状态”。
- 已新增命令：
  - `python -m app.main external-feeds-status`
- 该命令不会发起网络请求，也不会写文件，只读取：
  - `MONITOR_NEWS_FEED_URL`
  - `MONITOR_ANNOUNCEMENT_FEED_URL`
  - `MONITOR_NEWS_FEED_PATH`
  - `MONITOR_ANNOUNCEMENT_FEED_PATH`
  - 默认本地新闻/公告源文件状态
- 输出包含：
  - 远程新闻 URL 是否配置
  - 远程公告 URL 是否配置
  - 本地新闻源状态
  - 本地公告源状态
  - 每日流程是否可运行
  - 下一步推荐命令
- `.env.example` 已补充新闻源、公告源、输出目录和 webhook 相关环境变量。
- README 和帮助页已加入该命令。
- 已验证：
  - 未配置远程 URL 时仍显示每日流程可运行。
  - 已配置远程 URL 时提示运行 `refresh-external-feeds-pass-check`。
  - `python -m unittest discover tests`：545 tests OK
  - `python -m app.main phase-three-ready-check`：通过
  - `python -m app.main external-feeds-status`：通过

## 2026-07-22 外部输入源每日一体化检查

- 主线继续从“远程新闻/公告各自可刷新”推进到“一条命令完成每日外部输入源准备”。
- 已新增命令：
  - `python -m app.main refresh-external-feeds-pass-check`
- 该命令按顺序执行：
  - 刷新远程新闻源到本地新闻源。
  - 刷新远程公告源到本地公告源。
  - 生成当日新闻批量源。
  - 导出每日优先摘要。
- 默认文件仍沿用现有规则：
  - 本地新闻源：`data/news/local_news_feed.json`
  - 本地公告源：`data/news/local_announcement_feed.json`
  - 每日新闻批量源：`data/news/news_batch_YYYYMMDD.json`
  - 每日优先摘要：`data/news/news_batch_priority_summary_YYYYMMDD.md`
- 远程 URL 未配置或远程刷新失败时：
  - 不覆盖本地源文件。
  - 继续用已有本地源或自动候选源生成当日批量源。
- README 和帮助页已加入该命令。
- 已验证：
  - 一键外部输入源流程测试通过。
  - 无远程 URL 时自动候选兜底测试通过。
  - `python -m unittest discover tests`：543 tests OK
  - `python -m app.main phase-three-ready-check`：通过

## 2026-07-22 远程新闻 JSON 自动刷新入口

- 主线继续从“远程公告源可刷新”推进到“远程新闻源也可自动刷新到本地新闻源”。
- 已新增远程新闻抓取函数：
  - `app.data_sources.news_client.fetch_remote_news_items()`
- 支持的远程 JSON 结构：
  - 顶层列表
  - `items`
  - `data`
  - `list`
  - `news`
  - `articles`
  - `result`
- 支持的标题字段：
  - `title`
  - `headline`
  - `name`
- 支持的正文/摘要字段：
  - `content`
  - `summary`
  - `description`
  - `body`
- 已新增命令：
  - `python -m app.main refresh-local-news-feed`
- 使用方式：
  - 设置 `MONITOR_NEWS_FEED_URL` 为远程新闻 JSON 地址。
  - 运行 `refresh-local-news-feed` 写入本地新闻源。
  - 再设置 `MONITOR_NEWS_FEED_PATH` 指向本地新闻源，并运行 `refresh-daily-news-batch` 或 `start-daily-news-workflow`。
- 设计原则：
  - 远程抓取失败不会写坏本地新闻源。
  - 每日主线仍读取本地 JSON，保证网络不稳定时流程可继续。
- README 和帮助页已加入该命令。
- 已验证：
  - 远程新闻标准化单元测试通过。
  - CLI 刷新本地新闻源测试通过。
  - `python -m unittest discover tests`：541 tests OK
  - `python -m app.main phase-three-ready-check`：通过

## 2026-07-22 远程公告 JSON 自动刷新入口

- 主线继续从“本地公告源可合并”推进到“远程公告源可自动刷新到本地公告源”。
- 已新增远程公告抓取函数：
  - `app.data_sources.announcement_client.fetch_remote_announcement_items()`
- 支持的远程 JSON 结构：
  - 顶层列表
  - `items`
  - `data`
  - `list`
  - `announcements`
  - `result`
- 支持的标题字段：
  - `title`
  - `notice_title`
  - `announcementTitle`
  - `name`
- 支持的正文/摘要字段：
  - `content`
  - `summary`
  - `notice_content`
  - `announcementContent`
  - `body`
- 已新增命令：
  - `python -m app.main refresh-local-announcement-feed`
- 使用方式：
  - 设置 `MONITOR_ANNOUNCEMENT_FEED_URL` 为远程公告 JSON 地址。
  - 运行 `refresh-local-announcement-feed` 写入本地公告源。
  - 再设置 `MONITOR_ANNOUNCEMENT_FEED_PATH` 指向本地公告源，并运行 `start-daily-news-workflow`。
- 设计原则：
  - 远程抓取失败不会写坏本地公告源。
  - 每日主线仍读取本地 JSON，保证网络不稳定时流程可继续。
- README 和帮助页已加入该命令。
- 已验证：
  - 远程公告标准化单元测试通过。
  - CLI 刷新本地公告源测试通过。
  - `python -m unittest discover tests`：537 tests OK
  - `python -m app.main phase-three-ready-check`：通过

## 2026-07-22 本地公告源接入每日新闻流

- 下一步主线从“公告源状态可检查”推进到“公告源可作为每日新闻输入”。
- 已新增公告源本地模板命令：
  - `python -m app.main create-local-announcement-feed-template`
- 已新增公告源本地校验命令：
  - `python -m app.main validate-local-announcement-feed`
- 已新增公告源读取函数：
  - `app.data_sources.announcement_client.load_announcement_feed_items()`
- `refresh-daily-news-batch` 与 `start-daily-news-workflow` 已支持在配置 `MONITOR_ANNOUNCEMENT_FEED_PATH` 后自动合并本地公告源。
- 合并规则：
  - 公告源排在每日新闻候选前面。
  - 按标题去重，优先保留公告源同标题内容。
  - 未配置公告源或公告源无效时，不影响原有每日新闻候选流程。
- README 已补充本地公告源使用方式。
- 已验证：
  - 公告源相关定向测试通过。
  - `python -m unittest discover tests`：533 tests OK
  - `python -m app.main phase-three-ready-check`：通过

## 2026-07-22 第三阶段外部集成框架实际验收通过

- 已完成第三阶段外部集成框架主线收口，新增/强化：
  - `python -m app.main announcement-source-status`
  - `python -m app.main notification-status`
  - `python -m app.main phase-three-ready-check`
- 已新增公告源状态 helper：
  - `app.data_sources.announcement_client.build_announcement_source_status()`
- 已新增推送通知状态 helper：
  - `app.alerts.notifier.build_notification_channel_status()`
- 第三阶段验收命令已在当前真实工作区运行：
  - `python -m app.main phase-three-ready-check`
- 实际输出关键结果：
  - `阶段二：通过`
  - `公告源状态：not-configured`
  - `推送状态：console-only`
  - `自动化状态：可检查`
  - `结果：阶段三外部集成框架已就绪。`
- 当前公告源状态为 `not-configured`，代表框架已能识别配置缺失并给出下一步：
  - `prepare data/news/local_announcement_feed.json`
- 当前推送状态为 `console-only`，代表本地通知仍可用，后续设置 `MONITOR_WEBHOOK_URL` 后可进入 webhook-ready 状态。
- 已复跑：
  - `python -m unittest discover tests`：529 tests OK
- 结论：
  - 第三阶段“外部集成框架可验收版本”已经达到 100%。
  - 后续不再属于框架收口，而是进入真实外部服务接入：具体公告源、具体新闻网站/API、具体 Webhook 服务和 Windows 定时任务上线。

## 2026-07-22 第二阶段增强版实际验收通过

- 已完成第二阶段增强版主线收口，新增/强化：
  - `python -m app.main news-source-status`
  - `python -m app.main daily-automation-status`
  - `python -m app.main phase-two-ready-check`
- 第二阶段验收命令已在当前真实工作区运行：
  - `python -m app.main phase-two-ready-check`
- 实际输出关键结果：
  - `阶段一：通过`
  - `新闻源状态：auto-candidate-only`
  - `调度入口：可检查`
  - `每日新闻增强链路：通过`
  - `结果：阶段二增强版已就绪。`
- 当前真实数据仍为可用真实路径：
  - `snapshot-pass`
- 当前每日新闻链路：
  - 自动候选新闻源可跑通
  - 本地新闻源模板、校验、追加、每日一体化检查均已具备
  - 新闻源状态层已可扩展到后续真实公开新闻接口
- 自动化状态入口已具备：
  - 调度运行时状态
  - 注册任务摘要
  - 新闻源状态
  - 下一步建议
- 已复跑：
  - `python -m unittest discover tests`：522 tests OK
- 结论：
  - 第二阶段“增强版本地可验收版本”已经达到 100%。
  - 后续应进入第三阶段：真实新闻接口/公告源接入、推送通知、Windows 定时任务实战化与外部数据源增强。

## 2026-07-22 第二阶段新闻源状态入口

- 已新增新闻源状态能力：
  - `app.data_sources.news_client.build_news_source_status()`
- 已新增命令：
  - `python -m app.main news-source-status`
- 该命令用于查看当前新闻源处于哪种状态：
  - `auto-candidate-only`
  - `local-feed-missing`
  - `local-feed-invalid`
  - `local-feed-ready`
- 输出包含：
  - 本地新闻源路径
  - 新闻条数
  - 来源分布
  - 第一条标题
  - 状态说明
  - 下一步建议命令
- README 和帮助页已加入该命令。
- 这是第二阶段新闻源自动化增强的第一个状态接口，后续真实公开新闻接口可以继续接入同一状态层。
- 已新增/同步测试：
  - 无 feed 时显示自动候选模式
  - 有效 feed 显示 ready
  - 无效 feed 显示 invalid
  - CLI 输出新闻源状态
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：520 tests OK

## 2026-07-22 阶段一可运行版本实际验收通过

- 已在当前真实工作区运行：
  - `python -m app.main phase-one-ready-check`
- 实际输出关键结果：
  - `自检：通过`
  - `股票池：valid`
  - `每日主线：通过`
  - `最新复盘：通过`
  - `结果：阶段一可运行版本已就绪。`
- 当前真实数据状态：
  - `snapshot-pass`
- 当前每日新闻链路：
  - `新闻源模式：自动候选`
  - `新闻源文件：data\news\news_batch_20260722.json`
  - `摘要文件：data\news\news_batch_priority_summary_20260722.md`
- 结论：
  - 阶段一“本地可跑通版本”已经达到 100% 验收口径。
  - 后续工作应作为第二阶段/增强版继续推进，例如真实新闻源自动抓取、定时任务实战化、推送通知和外部数据源增强。

## 2026-07-22 阶段一就绪检查命令

- 已新增命令：
  - `python -m app.main phase-one-ready-check`
- 该命令用于汇总判断“阶段一可运行版本”是否就绪。
- 当前检查聚合：
  - `self-check`
  - 股票池状态
  - `mainline-smoke-test`
  - 每日新闻链路
  - 最新数据库复盘
- 通过时输出：
  - `结果：阶段一可运行版本已就绪。`
- 未通过时输出：
  - `结果：阶段一可运行版本仍需检查。`
- README 和帮助页已加入该命令。
- 已新增/同步测试：
  - `phase-one-ready-check` 能在本地流程完整时输出阶段一就绪
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：516 tests OK

## 2026-07-22 本地新闻源校验摘要增强

- 已增强命令：
  - `python -m app.main validate-local-news-feed`
- 校验通过时新增两类摘要：
  - `来源分布：...`
  - `重复标题：...`
- 来源分布用于快速确认当前本地新闻源来自手工追加、模板、外部脚本或其他来源。
- 重复标题摘要用于快速发现同一条新闻被重复收录的情况。
- 这一步不改变有效/无效判定，只增强可读性和维护性。
- 已新增/同步测试：
  - 无重复标题时显示 `重复标题：无`
  - 多来源 feed 显示来源分布
  - 重复标题显示 `标题 (次数)`
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：515 tests OK

## 2026-07-22 本地新闻源单条追加命令

- 已新增命令：
  - `python -m app.main append-local-news-feed "title" "content" "data/news/local_news_feed.json"`
- 该命令用于把临时看到的单条新闻追加到本地新闻源 JSON，减少手动编辑 JSON 的出错概率。
- 如果不传目标路径，则写入默认本地新闻源：
  - `data/news/local_news_feed.json`
- 追加条目会自动带上：
  - `source: local-feed-manual`
- 如果标题已存在，会显示：
  - `状态：已存在，未重复追加`
  - 并保持原有内容不变。
- 已同步 README 与帮助页命令目录。
- 已新增/同步测试：
  - 首次追加创建/更新 feed
  - 重复标题不重复写入
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：514 tests OK

## 2026-07-22 主线烟雾测试接入默认本地新闻源

- 已优化命令：
  - `python -m app.main mainline-smoke-test`
- 当默认本地新闻源存在时：
  - `data/news/local_news_feed.json`
  - 主线烟雾测试会自动优先走本地新闻源每日一体化链路。
- 当默认本地新闻源不存在时，仍保持原来的自动候选新闻源流程。
- `mainline-smoke-test` 输出新增：
  - `新闻源模式：本地新闻源 / 自动候选`
  - 如果命中本地源，则显示 `本地新闻源：...`
- README 已补充说明：`mainline-smoke-test` 会自动识别默认本地新闻源。
- 已新增/同步测试：
  - 默认自动候选 smoke test 保持可用
  - 默认本地新闻源存在时优先使用本地源
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：512 tests OK

## 2026-07-22 本地新闻源每日一体化检查

- 已新增命令：
  - `python -m app.main local-news-feed-daily-pass-check`
- 该命令把本地新闻源日常链路压缩为三步：
  - 校验本地新闻源
  - 刷新每日新闻批量源
  - 导出每日优先摘要
- 默认输入/输出路径：
  - 本地新闻源：`data/news/local_news_feed.json`
  - 每日新闻批量源：`data/news/news_batch_YYYYMMDD.json`
  - 每日优先摘要：`data/news/news_batch_priority_summary_YYYYMMDD.md`
- 如果本地新闻源无效，会停在校验阶段并显示具体条目问题，不会继续写每日 batch。
- 成功时会输出：
  - `结果：本地新闻源每日流程已通过。`
  - `新闻批量文件：...`
  - `摘要文件：...`
- README 与帮助页已加入该命令，作为使用默认本地新闻源时的更短路径。
- 已新增/同步测试：
  - 一体化成功链路
  - 无效 feed 中止链路
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：511 tests OK

## 2026-07-22 本地新闻源校验命令

- 已新增命令：
  - `python -m app.main validate-local-news-feed`
- 该命令用于在每日新闻刷新前校验本地新闻源 JSON。
- 默认校验路径：
  - `data/news/local_news_feed.json`
  - 如果设置了 `MONITOR_NEWS_DAILY_EXPORT_DIR`，则校验该目录下的 `local_news_feed.json`
- 校验覆盖：
  - 文件缺失
  - JSON 格式错误
  - 顶层结构不是列表
  - 条目不是对象
  - 条目缺少 `title`
  - 条目缺少 `content`
- 校验通过时会显示有效新闻条数和第一条标题，并提示设置 `MONITOR_NEWS_FEED_PATH` 后运行：
  - `python -m app.main refresh-daily-news-batch`
- README 和帮助页已同步加入该命令。
- 已新增/同步测试：
  - 有效本地新闻源校验
  - 缺字段本地新闻源校验
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：509 tests OK

## 2026-07-22 本地新闻源模板命令

- 已新增命令：
  - `python -m app.main create-local-news-feed-template`
- 该命令用于生成可编辑的本地新闻源 JSON，默认路径为：
  - `data/news/local_news_feed.json`
  - 如果设置了 `MONITOR_NEWS_DAILY_EXPORT_DIR`，则写入该目录下的 `local_news_feed.json`
- 模板字段保持与新闻批量源兼容：
  - `title`
  - `content`
  - `source`
- 命令输出会提示：
  - `环境变量：MONITOR_NEWS_FEED_PATH`
  - 设置该变量后运行 `python -m app.main refresh-daily-news-batch`
- README 已加入 `create-local-news-feed-template` 的最短用法说明。
- 已同步帮助页命令目录。
- 已新增/同步测试：
  - 显式目标路径生成模板
  - 默认路径生成模板
  - 生成内容包含有效 `title/content/source`
- 已复跑：
  - 相关专项测试
  - `python -m unittest discover tests`：507 tests OK

## 2026-07-22 本地新闻源文件优先接入

- 已将每日新闻源生成层从“纯内置自动候选”升级为“本地新闻源文件 + 自动候选兜底”。
- `app/data_sources/news_client.py` 的 `fetch_daily_news_candidates()` 现在支持：
  - 传入 `feed_path`
  - 读取本地 JSON 新闻源列表
  - 自动过滤缺少 `title/content` 的无效条目
  - 按标题去重，本地新闻源优先覆盖内置候选
  - 本地源缺失、格式错误或结构不匹配时自动回退到内置候选，不阻断每日流程
- `refresh-daily-news-batch` 与 `start-daily-news-workflow` 已接入环境变量：
  - `MONITOR_NEWS_FEED_PATH`
- 如果设置了 `MONITOR_NEWS_FEED_PATH` 且文件存在，刷新输出会显示：
  - `来源模式：本地新闻源 + 自动候选（...）`
- README 已补充本地新闻源 JSON 的使用说明。
- 已新增/同步测试：
  - 本地 feed 优先
  - 坏 feed 自动回退
  - 主命令读取 `MONITOR_NEWS_FEED_PATH`
- 已复跑：
  - `tests.test_news_client`
  - `tests.test_main`
  - `python -m unittest discover tests`：505 tests OK

## 2026-07-22 每日新闻自动候选源入口

- 已新增 `app/data_sources/news_client.py`，提供 `fetch_daily_news_candidates()` 作为当前新闻源生成层。
- 当前新闻源仍是本地确定性自动候选，不依赖外网，覆盖设备、电子特气、AI服务器、AI光模块等主线候选新闻。
- 已新增命令：
  - `python -m app.main refresh-daily-news-batch`
- 该命令会写入当天默认新闻批量文件：
  - `data/news/news_batch_YYYYMMDD.json`
- `start-daily-news-workflow` 在当日新闻源文件不存在时，已从“写固定模板”改为“自动生成候选新闻源”；如果文件已存在，仍复用已有文件，保留手动修改能力。
- 已更新 README 的日常使用路径，说明 `refresh-daily-news-batch` 与 `start-daily-news-workflow` 的关系。
- 已新增/同步测试：
  - `tests.test_news_client`
  - `tests.test_main` 中每日新闻源刷新与工作流新建分支
- 已复跑：
  - `tests.test_news_client`
  - `tests.test_news_classifier`
  - `tests.test_main`
  - `python -m unittest discover tests`：502 tests OK

## 2026-07-22 次日策略评分说明中文化

- 已将次日策略/复盘末尾的评分说明区中文化：
  - `Score rules` -> `评分规则`
  - `Fallback rules` -> `兜底规则`
  - `Avoid rules` -> `规避规则`
  - `Core/Candidate/Avoid` 输出语义调整为核心观察、候选观察、规避名单相关标签。
- 已将 `app/report_rule_config.json` 中的 `reason_score_labels` 改为中文显示名，但保留内部规则 key 与权重逻辑不变。
- 已更新 `app/reports/context_rules.py` 的次日策略输出标签，使命令行复盘、历史复盘和报告生成统一显示中文。
- 已更新 `app/dashboard/streamlit_app.py` 的评分摘要兼容清洗逻辑，新中文报告和旧英文历史报告都可以继续被仪表盘识别。
- 已同步测试样例，并复跑通过：
  - `tests.test_reports`
  - `tests.test_history`
  - `tests.test_dashboard_streamlit`
  - `python -m unittest discover tests`：500 tests OK

## 2026-07-21 详细预警区中文化

- 已将 `Detailed Alerts` 详细预警区中文化：
  - 详细预警
  - 开盘详细预警
  - 盘中详细预警
  - 收盘详细预警
- 已将详细预警字段标签中文化：
  - 时间
  - 方向
  - 相关个股
  - 原因
  - 趋势
  - 关注点
- 已将优先级标签中文化：
  - `High-Value` -> `高价值`
  - `Watch` -> `观察`
- 已将阶段匹配提示中文化：
  - 与某条产业链对齐
  - 与某条产业链对齐并带强度
  - 暂未匹配当前阶段焦点
- 已同步旧版兼容预警块 `_format_alert_block(alert)` 的字段输出，避免兼容路径继续显示英文标签。
- 已复跑通过：
  - `tests.test_pipeline`
  - `tests.test_reports`
  - `tests.test_main`
  - `tests.test_scheduler`
  - `python -m unittest discover tests`，500 tests OK

## 2026-07-21 市场焦点快照中文化

- 已将 `市场焦点快照` 的观察模板中文化：
  - 广度扩散
  - 龙头延续
  - 分歧风险升高
  - 混合轮动
  - 安静轮动
- 已将市场焦点字段标签中文化：
  - 观察结论
  - 市场状态
  - 最强板块
  - 次强板块
  - 预警组合
  - 最强板块均涨幅
  - 重点个股
- 已新增市场状态展示映射，内部规则 key 仍保留英文，用户输出显示中文：
  - `breadth expansion` -> `广度扩散`
  - `leader continuation` -> `龙头延续`
  - `divergence risk rising` -> `分歧风险升高`
  - `mixed rotation` -> `混合轮动`
  - `quiet rotation` -> `安静轮动`
- 已将预警组合从 `red/orange/high-value` 改为中文显示：`红色 / 橙色 / 高价值`。
- 已复跑通过：
  - `tests.test_pipeline`
  - `tests.test_reports`
  - `python -m unittest discover tests`，500 tests OK

## 2026-07-21 主流程结果摘要中文化

- 已将 `app/report_rule_config.json` 中 `task_result_summary_rules` 的业务摘要句中文化。
- 覆盖范围：
  - full_monitor
  - pre_open
  - morning_check
  - midday_check
  - afternoon_review
- 现在控制台顶部 `结果：` 后面会显示中文业务判断，例如：
  - 监控主线活跃
  - 盘前准备偏活跃
  - 开盘题材确认较强
  - 盘中扩散较强
  - 收盘结构偏积极
- 保持规则 key 与模板变量不变，例如 `{alert_count}`、`{high_value_count}`、`{red_count}`，后续仍可配置替换。
- 已复跑通过：
  - `tests.test_pipeline`
  - `tests.test_scheduler`
  - `tests.test_reports`
  - `python -m unittest discover tests`，500 tests OK

## 2026-07-21 默认主流程与任务画像展示中文化

- 已将默认运行横幅中文化：
  - `Monitor Command` -> `监控命令`
  - `Mode` -> `模式`
  - `Environment` -> `运行环境`
  - `Database` -> `数据库`
- 已将默认监控周期标题与任务画像标题中文化：
  - `AI Semiconductor Monitor Demo` -> `AI 半导体监控`
  - `Pre-open Check` -> `盘前检查`
  - `Morning Check` -> `开盘检查`
  - `Midday Check` -> `盘中检查`
  - `Afternoon Review` -> `尾盘复盘`
- 已将共享展示配置中的高频版块标题中文化：
  - 市场焦点快照
  - 开盘/盘中/收盘市场焦点
  - 监控池观察
  - 开盘/盘中/收盘监控池观察
  - 结果、焦点、行情来源
  - 阶段链条焦点、股票池覆盖
- 已优化共享渲染函数：中文标签使用中文冒号且不额外加空格，英文标签保持原样，便于后续配置替换。
- 已绕开历史编码异常的旧“最新数据库复盘”标题分支，实际输出使用新的中文标题。
- 已复跑完整回归：
  - `python -m unittest discover tests`
  - 500 tests OK

## 2026-07-21 自检与行情连通性提示中文化

- 已将 `self-check` 的高频输出中文化：
  - 最小可运行自检
  - 主流程
  - 行情来源
  - 直连路径
  - 真实数据状态
  - 写入快照
  - 生成预警
  - 最新复盘
  - 股票池校验
  - 建议诊断
  - 下一步
  - 可选可视化页面
- 已将 `quote-connectivity-check` 的用户可见标签中文化：
  - 实时行情连通性检查
  - 依赖状态
  - 端点访问
  - 结果
  - 失败类型
  - 诊断
  - 受阻阶段
  - 运行时诊断摘要
  - 原始错误
  - 受阻来源
  - 下一步
- 已同步主线内部判断条件，避免 `self-check` 显示中文后影响 `mainline-smoke-test`、刷新/导入一体化检查的通过判断。
- 保留 `live-pass` / `snapshot-pass` / `not-passed` 作为机器可读状态标签，便于排错和后续自动化判断。
- 已复跑通过：
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`

## 2026-07-21 本地行情快照与导入提示中文化

- 已将本地行情快照相关高频终端输出中文化：
  - create-local-quote-template
  - validate-local-quote
  - refresh-local-quote-snapshot
  - refresh-local-quote-pass-check
  - import-local-quote
  - import-local-quote-pass-check
- 覆盖保存路径、结构、状态、行数、行情来源、直连路径、结果、失败原因、下一步、用法等提示。
- 已同步内部一体化检查判断，从旧英文 `Saved to` / `Status: valid` 改为中文标记 `保存到` / `状态：有效`。
- 已清理 `import-local-quote-pass-check` 中残留的旧英文标题。
- 已复跑通过：
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`

## Purpose

Build a lightweight research-support monitor for A-share AI and semiconductor names.

The system is explicitly not an auto-trading bot. The first goal is to avoid missing:

- important intraday moves
- important news and announcements
- the real sector leader
- sector rotation into materials and gases

## Source Requirement

Primary source document:

- [AI_SEMICONDUCTOR_MONITOR_REQUIREMENTS.md](/Y:/AI/Codex/Project_Agu_01/AI_SEMICONDUCTOR_MONITOR_REQUIREMENTS.md)

## Phase-One Scope

Must-have:

- stock universe
- realtime quote intake
- sector grouping
- leader ranking
- materials and gases special monitoring
- keyword-based news classification
- console alerts

Recommended in phase one:

- SQLite persistence
- morning report
- evening report

Not in scope for the first pass:

- automatic trading
- heavy model-based decisioning
- broad multi-source production news crawling

## Architecture Direction

Current project structure:

- `app/`
- `app/data_sources/`
- `app/universe/`
- `app/analysis/`
- `app/alerts/`
- `app/reports/`
- `tests/`

Preferred stack:

- Python 3.11+
- pandas
- SQLite
- APScheduler
- AKShare

## Key Business Rules

Observed sectors:

- AI光模块/CPO
- AI服务器/算力硬件
- PCB/高速板
- 液冷/数据中心散热
- 半导体设备
- 半导体材料/气体
- 存储/HBM
- 先进封装/Chiplet

Special focus line:

- 半导体材料/气体

Current normalized sector list:

- AI光模块/CPO
- AI服务器/算力硬件
- PCB/高速板
- 液冷/数据中心散热
- 半导体设备
- 半导体材料
- 半导体气体
- 存储/HBM
- 先进封装/Chiplet

Current normalized special focus line:

- 半导体材料、半导体气体联动链

Important examples:

- 沪硅产业 `688126`
- 中巨芯-U `688549`
- 华特气体 `688268`
- 安集科技 `688019`
- 鼎龙股份 `300054`
- 江丰电子 `300666`

## Current Implementation Status

Scaffold exists for:

- config
- database bootstrap
- scheduler bootstrap
- stock universe
- placeholder AKShare client
- placeholder leader detector
- placeholder trend judger
- basic keyword news classifier
- placeholder alert engine
- morning and evening report templates

Current scheduler behavior:

- uses APScheduler when installed
- falls back to a no-op scheduler so the local demo can run before dependencies are installed

Current database behavior:

- SQLite file bootstrap is intentionally simple for Windows local development stability

## TDD Status

Completed and passing:

- stock universe tests
- news classifier smoke tests
- app bootstrap demo test
- quote normalization tests
- universe filtering tests
- leader ranking tests
- leader type classification tests
- trend judgement state tests
- trend reason output tests
- alert trigger tests
- console notifier format tests
- report composition tests
- orchestrated app flow test
- SQLite persistence tests
- persisted main-flow integration test
- AKShare adapter integration tests
- realtime quote preference and fallback tests
- database-backed report tests
- historical review helper tests
- database review entry tests
- CLI mode dispatch tests

Test command used successfully:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -v`

## Latest Completed Slice

On 2026-07-15, the project documentation was tightened around a more practical
"minimal runnable version first" rule.

`README.md` now puts a short runnable path closer to the top, centered on:

- `python -m app.main`
- `python -m app.main latest-review`
- `python -m app.main validate-stock-pool`
- `streamlit run app/dashboard/streamlit_app.py`

That change does not add new business logic, but it does change the working
priority for the next implementation steps:

- first make the local main flow easy to run end to end
- then make the stored review easy to verify
- then keep stock-pool editing safe through validation
- push non-essential visual polishing to later iterations

This was an intentional scope-control step so the project can land a stable
phase-one runnable version sooner, instead of continuing to spend time on
secondary presentation refinement.

Later on 2026-07-15, the CLI entry path was tightened for better phase-one
handoff usability.

What this step focused on:

- add an explicit local command guide through `help`, `--help`, and `-h`
- stop treating unknown commands as silent fall-through demo runs
- print a direct unknown-command reminder plus the command guide instead
- fix the programmatic `main()` entry so local tests and in-process callers do
  not accidentally inherit unrelated shell/test arguments

Current effect:

- the project is easier to hand over and reopen later without remembering the
  full command set
- mistaken commands are now safer and more explainable
- the main entry path behaves more predictably both from the real CLI and from
  local test/runtime calls

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`

Later on 2026-07-15, the first-run guidance layer was extended around empty
readback states and optional dashboard dependency checks.

What this step focused on:

- add a clear first-run hint for `latest-review` when SQLite exists but no
  monitor batch has been written yet
- add a clearer history-review hint when the requested timestamp has no stored
  snapshot batch
- add a thin `streamlit` import guard in the dashboard entry so missing local
  dashboard dependency errors become readable and actionable

Current effect:

- the project now guides users back to the main runnable path instead of
  showing an ambiguous empty read mode
- first-time local setup errors around dashboard launch are easier to diagnose
  and recover from

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main tests.test_dashboard_streamlit`

Later on 2026-07-15, `README.md` was also tightened so the new first-run hints
are visible directly in the main local startup path.

What this step focused on:

- add one short `First-Run Troubleshooting` section near the minimal runnable
  path
- document the three most common local recovery actions:
  - run the main flow before read-only review commands
  - use an existing stored timestamp for history review
  - install requirements before launching the Streamlit dashboard

Current effect:

- the main README now matches the runtime hints already implemented in code
- first-time local setup and re-entry should need less back-and-forth memory
  recall

Later on 2026-07-15, the runnable acceptance path in `README.md` was compressed
further into one ultra-short self-check.

What this step focused on:

- add a `3-Step Self-Check` section near the top of the README
- reduce the practical acceptance path to:
  - `python -m app.main`
  - `python -m app.main latest-review`
  - `python -m app.main validate-stock-pool`

Current effect:

- reopening the project later now requires less scanning through long command
  documentation
- the phase-one "is it runnable right now?" question now has one short,
  repeatable answer path

Later on 2026-07-15, that short acceptance path was also turned into a real CLI
command: `self-check`.

What this step focused on:

- add `python -m app.main self-check` as a compact local acceptance entry
- keep the output summary-oriented instead of replaying the full demo, review,
  and validation reports
- update the CLI help text and README so the simplified entry is discoverable

Current effect:

- the minimal runnable version now has a one-command health check
- repeated reopen / verify cycles should be faster and less error-prone

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`

Later on 2026-07-15, the business mainline gained one local news
classification and alert-preview entry:

- `python -m app.main classify-news "title" "content"`

What this step focused on:

- promote the existing keyword-based news classification logic into a directly
  usable CLI command
- infer one related monitored sector from lightweight industry keywords
- infer related monitored stock names from direct news-text matches, including
  simple alias normalization such as `中巨芯U` -> `中巨芯-U`
- preview whether the classified news would trigger a `news_flash` alert

Current effect:

- important policy / announcement headlines can now be checked quickly in the
  local terminal without touching code
- the project's news-alert capability is now exposed as an actual user-facing
  business function instead of only an internal helper

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_news_classifier tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "半导体设备出口管制升级" "刻蚀设备与薄膜沉积环节承压。"`

Later on 2026-07-15, that same news-classification entry gained one more
business-facing layer: observation suggestions.

What this step focused on:

- add `Suggested action` output for `classify-news`
- when the news text directly matches monitored stocks, suggest those names as
  the first observation targets
- when the news only matches a monitored sector, fall back to a small
  priority-first sector watchlist
- keep the existing alert-grade rule unchanged:
  - `S` risk news can still preview `news_flash`
  - `A` positive news still stays as classification + observation guidance

Current effect:

- the news command is no longer only "classification"; it now gives a more
  actionable follow-up observation hint
- even when no specific stock name is present in the news text, the terminal
  can still point the user toward a concrete sector watchlist

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "中巨芯U批量供货推进" "中巨芯U与华特气体协同改善，电子特气景气度提升。"`

Later on 2026-07-15, the same terminal news workflow gained a clearer chain
positioning hint.

What this step focused on:

- add one `Chain hint` line to `classify-news`
- translate the detected monitored sector into a more business-readable chain
  explanation, such as:
  - equipment chain
  - material chain
  - gas chain
  - compute/server chain
  - packaging chain
- keep that hint separate from `Related sector`, so the output now gives both:
  - normalized project sector classification
  - plain-language chain interpretation

Current effect:

- terminal news analysis is now easier to read from a research perspective
- even before looking at the suggested watchlist, the user can quickly
  understand which part of the AI / semiconductor chain the news is leaning on

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "半导体设备出口管制升级" "刻蚀设备与薄膜沉积环节承压。"`

Later on 2026-07-15, the same news terminal flow gained one more top-line
judgment layer: `Impact view`.

What this step focused on:

- add one short same-day interpretation line to `classify-news`
- keep the rule simple and readable instead of introducing opaque scoring
- current lightweight impact buckets include:
  - `更偏风险扩散`
  - `更偏主线强化`
  - `更偏局部验证`

Current effect:

- the terminal output now answers not only "what kind of news is this" but
  also "how should I prioritize it in today's monitoring order"
- this makes the command read more like a practical research triage helper
  rather than only a classifier

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "中巨芯U批量供货推进" "中巨芯U与华特气体协同改善，电子特气景气度提升。"`

Later on 2026-07-15, the terminal news workflow also started reading monitor
pool priority directly in its suggestion layer.

What this step focused on:

- when `classify-news` directly matches monitored stock names, look up their
  current monitor-pool priority
- if at least one matched name belongs to `priority=1`, upgrade the suggestion
  wording from generic observation to explicit `优先盯核心池`

Current effect:

- the news command now aligns more closely with the project's existing stock
  pool hierarchy
- terminal suggestions can distinguish between:
  - ordinary observation targets
  - core-pool names that deserve first-look attention

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "中巨芯U批量供货推进" "中巨芯U与华特气体协同改善，电子特气景气度提升。"`

Later on 2026-07-15, the same priority-aware suggestion layer was extended to
the sector-watchlist fallback path as well.

What this step focused on:

- when news does not directly mention monitored stock names, the command still
  falls back to one small sector watchlist
- that fallback watchlist now also checks whether the recommended names contain
  `priority=1` core-pool stocks
- if yes, the fallback wording also upgrades to `优先盯核心池`

Current effect:

- the news command now keeps one consistent priority language across both:
  - direct stock-name matches
  - same-chain fallback candidates
- this makes "core pool first" a more stable rule in terminal guidance instead
  of only in the exact-name-match path

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "半导体设备出口管制升级" "刻蚀设备与薄膜沉积环节承压。"`

Later on 2026-07-15, the same terminal news workflow gained one more compact
reading layer: `Bottom line`.

What this step focused on:

- add one top-level takeaway line near the end of `classify-news`
- compress the current:
  - `Impact view`
  - `Suggested action`
  into one fast-scanning summary sentence

Current effect:

- the terminal news command can now be scanned from top to bottom, or almost
  skipped directly to one final takeaway line
- this makes the output more practical for repeated intraday headline triage

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news "中巨芯U批量供货推进" "中巨芯U与华特气体协同改善，电子特气景气度提升。"`

Later on 2026-07-15, that same terminal news workflow gained a minimal batch
entry for faster intraday triage:

- `python -m app.main classify-news-batch "news_batch.json"`

What this step focused on:

- allow one local JSON file to carry multiple news items
- print one compact batch summary with each item's:
  - title
  - level
  - related sector
  - `Bottom line`
- add Windows-friendly JSON reading with `utf-8-sig` so VS Code-saved files
  with BOM still load normally

Current effect:

- the project now supports a more realistic "screen several headlines quickly"
  terminal workflow
- the batch path reuses the same business judgment layers already built for the
  single-item path instead of introducing a second logic fork

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news-batch .tmp_news_batch.json`

Later on 2026-07-15, the batch news entry also gained one top-level batch
summary line.

What this step focused on:

- count the current batch's lightweight impact buckets:
  - `风险扩散`
  - `主线强化`
  - `局部验证`
- print one `Impact summary` line before the per-item list

Current effect:

- the batch news workflow now supports a quick "read the whole basket first"
  pass before reading individual items
- this makes the batch path more practical when the user only wants to know
  whether the current headline group is mostly risk-driven or mostly
  reinforcement-driven

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news-batch .tmp_news_batch.json`

Later on 2026-07-15, the batch news path also gained one stable default
reading order.

What this step focused on:

- sort batch-news items before display instead of preserving raw input order
- current lightweight reading priority:
  - `风险扩散`
  - `主线强化`
  - `局部验证`
- use level as a secondary tie-breaker:
  - `S`
  - `A`
  - `C`

Current effect:

- the batch workflow now opens with the most time-sensitive items first even if
  the original file order is mixed
- this makes the terminal batch path more aligned with real intraday triage
  behavior

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news-batch .tmp_news_batch.json`

On 2026-07-16, the batch news workflow gained one minimal high-priority filter
switch:

- `python -m app.main classify-news-batch "news_batch.json" high-priority-only`

What this step focused on:

- keep the default batch output unchanged
- add one optional lightweight filter mode that keeps only:
  - `风险扩散`
  - `主线强化`
- hide temporary `局部验证` rows when the user only wants the higher-priority
  subset

Current effect:

- the batch-news terminal path now supports two practical reading modes:
  - full basket view
  - higher-priority-only view
- this makes intraday headline screening faster without requiring a more
  complex interface

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news-batch .tmp_news_batch.json high-priority-only`

On 2026-07-16, the same batch-news workflow gained one ultra-light first-pass
mode:

- `python -m app.main classify-news-batch "news_batch.json" summary-only`

What this step focused on:

- keep the same batch classification and sorting logic
- suppress per-item `Bottom line` output
- retain only:
  - batch header
  - impact summary
  - title
  - level
  - sector

Current effect:

- the project now supports a faster "headline list first, detail second"
  terminal workflow
- this is useful when the user wants one very fast rough screen before choosing
  which items deserve the fuller batch or single-item view

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main classify-news-batch .tmp_news_batch.json summary-only`

On 2026-07-16, the same batch-news workflow gained one minimal export entry:

- `python -m app.main export-news-batch "news_batch.json" "news_batch_summary.md"`

What this step focused on:

- reuse the existing batch summary text as the export payload
- keep the export path minimal and local-first
- support ordinary `.txt` or `.md` file outputs without adding a second render
  format

Current effect:

- intraday screening results can now be saved immediately for later review
- the terminal workflow is now closer to a complete "screen -> decide -> keep a
  record" loop

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main export-news-batch .tmp_news_batch.json .tmp_news_batch_summary.md`

Later on 2026-07-16, the same export path also gained one default timestamped
filename mode.

What this step focused on:

- allow `export-news-batch` to run with only the source batch path
- when no explicit output file is provided, generate one timestamped markdown
  summary filename automatically beside the source batch file

Current effect:

- the export path now needs less manual typing during intraday use
- the project can keep lightweight timestamped batch records without requiring
  the user to invent filenames each time

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main export-news-batch .tmp_news_batch.json`

Later on 2026-07-16, that same auto-export path also started reflecting the
active filter mode inside the generated filename.

What this step focused on:

- when the user exports without an explicit target path, still generate one
  timestamped markdown file
- if the export uses a mode such as `high-priority-only` or `summary-only`,
  include that mode in the generated filename as well
- normalize CLI argument parsing so:
  - `export-news-batch source.json high-priority-only`
  is interpreted correctly as "auto filename + high-priority filter"

Current effect:

- saved files are now easier to distinguish during later review
- the export command is more natural to use from PowerShell because it no
  longer relies on passing an explicit empty placeholder argument

Verification completed:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest tests.test_main`
- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m app.main export-news-batch .tmp_news_batch.json high-priority-only`

Later on 2026-07-16, the README entry path was tightened again so the news
workflow is easier to find during normal project use.

What this step focused on:

- add one short `News Commands` block near the top of `README.md`
- keep only the most common terminal news workflows in that block:
  - single-item classification
  - batch full view
  - batch high-priority-only
  - batch summary-only
  - batch export

Current effect:

- the project now exposes the most actively iterated business command group
  closer to the top-level startup path
- practical daily use should require less scrolling through the longer CLI
  reference section

Verification completed:

- documentation-only update; no code-path change

On 2026-06-27, the project planning layer was refined further through
analysis-only documentation work.

A new planning document now exists:

- [STOCK_POOL_ARCHITECTURE_PLAN.md](/Y:/AI/Codex/Project_Agu_01/STOCK_POOL_ARCHITECTURE_PLAN.md)

That document records:

- the adjusted stock-pool optimization plan
- the recommended three-layer stock-pool architecture
- the proposed field-template design
- the migration direction for the current 43-stock pool
- the first-pass extended observation-pool candidates
- the standard positioning rule for Industrial Fulian (`601138`)

No code was changed in that analysis turn; the goal was to preserve business
decisions and future migration intent in a stable written form.

Later on 2026-06-27, implementation started for the first stock-pool
architecture slice.

That first slice now supports:

- optional `monitor_sector` in source files as a forward-looking replacement
  for legacy `sector`
- optional `market`
- optional `chain_group`
- optional `pool_type`

Current compatibility behavior:

- legacy rows that only provide `sector` still work
- stock dictionaries now expose both `sector` and `monitor_sector`
- `chain_group` falls back to stable defaults for known sectors
- `pool_type` defaults to `core`

This means the project has now started the migration from a lightweight
monitoring stock pool toward a more explainable stock-pool structure without
breaking the current business flow.

The default stock-pool source file has now also been migrated to that first
compatibility structure:

- current rows now include `market`
- current rows now include `monitor_sector`
- current rows now include `chain_group`
- current rows now include `pool_type`

Current migration posture:

- `sector` is still preserved for compatibility
- `monitor_sector` currently mirrors `sector` in the default file
- this keeps the current monitoring/reporting behavior stable while moving the
  source data toward the new architecture plan

This means the project is no longer only "code-ready" for the new stock-pool
metadata; the main tracked universe file has now started using it directly.

Later in that same migration sequence, the default stock pool also completed
the first sector split:

- `半导体材料/气体` was split into
  - `半导体材料`
  - `半导体气体`

Current default split counts:

- `半导体材料`: 11
- `半导体气体`: 3

This means the main stock-pool source has now started aligning with the
architecture plan at the sector level as well, not only at the metadata-field
level.

`app/main.py` now supports lightweight command modes:

- default / no args: run demo flow
- `latest-review`: print latest database-backed evening review
- `history-review <timestamp>`: print a selected stored batch summary

This makes the project easier to use directly from the VS Code terminal without
editing code.

`app/main.py` now also exposes read-side helper entry points:

- `print_latest_database_review(database_path)`
- `print_history_review(database_path, timestamp)`

This means persisted data can now be inspected directly from project code
without manually querying SQLite.

The dashboard presentation layer now reuses one shared formatter path across:

- KPI cards
- grouped summary metrics
- chart companion tables
- generic content tables

This means display formatting for timestamps, counts, and signed percentages can
be changed from presentation metadata without touching the main render flow.

The generic content-table path now also supports a richer `table_columns`
metadata shape:

- `key`: source field
- `label`: display column title
- `format_key`: shared formatter rule

Legacy `columns` plus `table_column_formats` remains supported, so existing
table specs can be migrated gradually.

Chart companion tables now also use the same `table_columns` metadata shape.
This means chart-adjacent tables and generic content tables now share one
column-configuration model for:

Later on 2026-06-27, a cross-check was done between the old
`半导体材料/气体` logic and the new split-sector logic.

Current alignment result:

- stock-pool source data is already split into `半导体材料` and `半导体气体`
- alert aggregation for the special materials/gases line now treats those two
  sectors as one linked chain for `materials_focus`
- demo market rows were aligned to the split sectors
- morning-report default focus text now reflects the split structure
- evening-report database review now collects `materials_watch` from both split
  sectors instead of only the legacy combined label

Important logic note preserved from that check:

- after the split, `materials_focus` and `sector_move` are no longer equivalent
- `materials_focus` can trigger from a combined total across `半导体材料` and
  `半导体气体`
- `sector_move` should only trigger when one concrete sector on its own has at
  least 3 strong names

Tests were updated to reflect that separation explicitly so the old
"combined bucket implies single-sector move" assumption does not silently leak
back into the codebase.

Later on 2026-06-27, the sector-label layer was centralized further.

A new shared module now exists:

- [app/sectors.py](/Y:/AI/Codex/Project_Agu_01/app/sectors.py)

That module currently centralizes:

- split material/gas sector labels
- the linked-chain display label
- the default morning focus-sector set
- helper rules for "is this material-chain related?"
- helper rules for composing default focus-sector order

Current implementation effect:

- alert rules no longer define their own material/gas sector set
- morning report defaults no longer hardcode their own sector text
- evening report database review no longer keeps a separate copy of the
  material/gas sector set
- pipeline demo and morning-context assembly now reuse the same shared sector
  definitions

This reduces the chance that future stock-pool category refinement will update
one presentation or alert path while forgetting another.

Later on 2026-06-27, stock-pool validation was linked more tightly with the
shared sector registry.

Current validation behavior now includes:

- `unknown_sectors` in the validation result
- a health hint when a stock-pool file contains unregistered monitor-sector
  labels
- command-line validation output that prints unknown sector labels directly

Current intent of that rule:

- catch likely typos when the stock pool is edited manually
- keep the system open to future sector expansion
- avoid treating "new sector" and "duplicate code" as the same kind of problem

This means changing [app/universe/stock_pool.json](/Y:/AI/Codex/Project_Agu_01/app/universe/stock_pool.json)
is still enough for ordinary add/remove/edit work, but running
`validate-stock-pool` now gives faster feedback if a monitor-sector label drifts
away from the registered set.

Later on 2026-06-27, the editable stock-pool documentation was aligned with
that validation rule as well.

Current documentation now records:

- the registered monitor-sector list
- the legacy `半导体材料/气体` compatibility note
- the recommendation to validate immediately after editing the stock-pool file

This keeps the normal user workflow simple:

1. edit `app/universe/stock_pool.json`
2. save
3. run `validate-stock-pool`
4. fix any unknown-sector warning if needed

Later on 2026-06-27, the validation console output was made more self-contained.

Current validation output now also prints:

- the registered monitor-sector list used by the project

This means the terminal output for `validate-stock-pool` is now enough for
quick side-by-side checking:

- what sectors are currently in the file
- which sectors are unknown
- which sector labels are officially registered right now

Later on 2026-06-27, unknown-sector validation also gained lightweight typo
suggestions.

Current behavior now includes:

- `unknown_sector_suggestions` in the validation result
- health hints such as `Possible sector match for 半导体材科: 半导体材料`
- console output under `Possible matches:`

This makes manual stock-pool editing more forgiving without weakening the
explicit sector-registry rule.

Later on 2026-06-27, the same registry-and-suggestion pattern was extended to
`chain_group`.

Current validation behavior now also includes:

- `unknown_chain_groups`
- `unknown_chain_group_suggestions`
- console output for registered chain groups
- console output for possible chain-group matches

This means both main classification layers in the stock-pool file now have
lightweight typo protection:

- `monitor_sector`
- `chain_group`

Later on 2026-06-28, the same validation structure was extended again to:

- `market`
- `pool_type`

Current stock-pool validation now provides one consistent pattern across the
main editable enum-like fields:

- registered values
- unknown-value detection
- close-match suggestions
- console summaries for direct terminal checking

Later on 2026-06-28, those richer validation details were also connected into
the dashboard health view.

Current dashboard health summary now carries through:

- unknown sectors
- unknown chain groups
- unknown markets
- unknown pool types
- suggested close matches for those unknown values

This means stock-pool structural drift can now be inspected from:

- terminal validation output
- dashboard health summary card

Later on 2026-06-28, the dashboard health summary was made easier to scan by
splitting its validation details into clearer groups.

Current health-card structure now separates:

- duplicates
- unknown values
- suggested matches
- health hints

This keeps the dashboard view more readable as stock-pool validation coverage
expands across additional editable fields.

Later on 2026-06-28, the dashboard health summary also gained a lightweight
top-level risk signal.

Current dashboard health risk levels are:

- `clean`
- `warning`
- `blocking`

Current intent:

- `blocking`: duplicate-code problems that should be fixed before relying on the pool
- `warning`: unknown registry values or structural review hints
- `clean`: no current blocking or warning signal

This lets the dashboard communicate stock-pool readiness at a glance before the
user reads the detailed validation rows.

Later on 2026-06-28, that readiness signal was promoted from plain metadata to
its own dedicated dashboard panel inside the health section.

Current dashboard health flow now emphasizes:

- readiness first
- grouped validation details second

This makes the stock-pool health block easier to scan when the user only wants
to answer one quick question first: "Can I trust this pool enough to monitor
with it right now?"

Later on 2026-06-28, the health-summary wrapper copy was also tied more
directly to that dashboard risk level.

Current health/readiness support copy now varies by:

- `clean`
- `warning`
- `blocking`

Current implementation effect:

- the main health summary card now uses different supporting text depending on
  whether the pool is structurally ready, needs review, or should be fixed
  first
- the readiness panel now also carries its own risk-aware supporting guidance
  instead of showing one static message for every case

This means the stock-pool health area is now not only grouped and tone-aware,
but also clearer at the copy level: the first explanatory sentence changes with
the actual severity of the current pool state.

Later on 2026-06-28, the content-list area also gained its own replaceable
style layer.

Current dashboard content styling now has a dedicated metadata boundary for:

- content-section supporting copy
- compact content-section supporting copy
- detail-area supporting copy
- compact detail-area supporting copy
- content empty-state supporting copy

Current implementation effect:

- content-section headers now render through a content-specific wrapper instead
  of relying only on the generic section-title wrapper
- grouped summary blocks now introduce their detail rows through a shared
  content-detail panel
- content-table sections now also use that shared content-detail wrapper before
  the dataframe
- content-block empty states now use content-specific empty-state supporting
  copy instead of the generic summary-card empty-state message

This means the dashboard's four main presentation areas are now closer to one
consistent configurable system:

- KPI area
- health/status area
- chart area
- content/list area

Later on 2026-06-28, field-level display metadata was also unified further
through a shared display-field registry.

Current presentation metadata now includes a reusable registry for:

- chart companion-table fields
- strongest-sector detail fields
- leader-summary detail fields
- latest-alert detail fields
- saved-batch detail fields

Current implementation effect:

- chart tables and grouped content-detail rows can now both read from the same
  `display_fields` shape
- shared field metadata now carries the same core display properties across
  both surfaces:
  - `key`
  - `label`
  - `format_key`
  - optional `prefix`
- Streamlit render helpers now normalize that shared field metadata through one
  entry point before rendering tables or detail rows
- older `table_columns`, `columns`, and `detail_column_formats` fallback paths
  still remain supported for compatibility

This means future display changes such as renaming a field label, changing a
timestamp formatter, or reordering a detail row can now be pushed closer to one
shared metadata layer instead of being repeated separately across chart and
content render paths.

Later on 2026-06-28, the stock-pool health block also moved more of its inner
grouping structure into presentation metadata.

Current health-group metadata now defines:

- which issue buckets should be rendered
- which suggestion buckets should be rendered
- the display titles for duplicate, issue, suggestion, and hint sections

Current implementation effect:

- `issue_rows` are now built from configured issue-group specs instead of a
  hardcoded list inside the render helper
- `suggestion_rows` are now built from configured suggestion-group specs instead
  of a hardcoded map loop
- health-section titles such as `Validation Issues` and `Suggested Matches`
  now come from replaceable metadata instead of fixed strings in the view-model
  helper

This means the stock-pool health area is now closer to the same
configuration-first structure already used by chart tables and content details:
future regrouping or wording changes can happen more in presentation metadata
and less in the main Streamlit logic.

Later on 2026-06-28, the stock-pool health detail rendering also gained a
shared grouped-section render path.

Current implementation now includes:

- a helper that builds normalized grouped text-section view models from
  configured section metadata plus row sources
- a shared render helper that outputs those titled row groups through one entry
  point

Current implementation effect:

- the health block no longer manually writes duplicate rows, issue rows,
  suggestion rows, and hint rows through four separate code branches
- those groups now flow through one `detail_sections` structure inside the
  health-summary view model
- future health-detail presentation changes can target one grouped render path
  instead of editing each section branch separately

This means the stock-pool health area is now not only configuration-first at
the data-group level, but also more unified at the final render-entry level.

Later on 2026-06-28, the stock-pool health auxiliary meta rows also moved into
replaceable metadata.

Current health meta metadata now defines:

- which auxiliary fields should appear
- their render order
- which label key each field uses
- whether a field should render raw text or a derived count

Current implementation effect:

- `Risk Level`, `Source`, and registered-value counters are no longer assembled
  through one hardcoded list inside the health view-model helper
- those rows now flow through one shared `_build_health_meta_rows(...)` helper
  using configured `health_meta` specs
- future reordering or field replacement inside the health meta area can happen
  in presentation metadata without changing the main summary assembly logic

This means the stock-pool health block now has configurable structure across:

- top-level status/readiness copy
- grouped issue/suggestion/hint sections
- auxiliary meta rows

Later on 2026-06-28, those health meta rows and detail sections were also
lifted into one shared information-block schema.

Current implementation now includes:

- reusable `health_info_blocks` metadata
- a shared `_build_info_blocks(...)` helper
- a shared `_render_info_blocks(...)` entry point

Current implementation effect:

- the health block now treats `meta_rows` and `detail_sections` as two block
  types inside one ordered `info_blocks` list
- the render layer no longer handles those two areas through completely
  separate top-level branches
- future health-area layout changes can more easily swap block order or add new
  block types without rewriting the main health render flow

This means the stock-pool health area is now closer to a generalized
configuration-first content-block model instead of a one-off section-specific
assembly path.

Later on 2026-06-28, that information-block pattern also started to spread
beyond the stock-pool health section.

Current grouped summary sections now also define reusable `info_block_specs`
metadata, and their view models now expose `info_blocks` alongside legacy
`detail_rows`.

Current implementation effect:

- `Strongest Sector`
- `Leader Summary`
- `Latest Alerts`
- `Saved Batches`

can now all flow through the same shared information-block builder/render path
used by the health area, at least for grouped text-detail content.

Current migration posture:

- legacy `detail_rows` is still preserved for compatibility
- new `info_blocks` is now available as the more general structure for future
  render unification

This means the dashboard is moving from "health section special handling" to a
broader block-based presentation model across multiple summary surfaces.

Later on 2026-06-28, grouped-summary rendering also made `info_blocks` the
primary render path, with legacy `detail_rows` kept as a compatibility fallback.

Current implementation now includes:

- `_resolve_grouped_summary_render_blocks(...)`

Current behavior:

- when `info_blocks` exists, grouped-summary rendering uses it directly
- when only legacy `detail_rows` exists, the render layer derives compatible
  grouped information blocks automatically
- when neither exists, the shared empty-state path is used

This means newer block-based view models can now be introduced without waiting
for every older grouped-summary producer to migrate at the same speed, while
the dashboard still converges toward one primary render structure.

Later on 2026-06-28, grouped-summary producers also reduced duplicate assembly
between legacy `detail_rows` and newer `info_blocks`.

Current implementation now includes:

- `_build_grouped_summary_detail_payload(...)`

Current behavior:

- grouped-summary producers now build one shared detail payload first
- that payload then feeds both:
  - legacy `detail_rows`
  - block-based `info_blocks`

This means the compatibility layer is still present, but the data assembly cost
and maintenance duplication between the old and new shapes is now lower, which
makes the later removal of `detail_rows` safer and more incremental.

Later on 2026-06-28, the first grouped-summary view-model producers also began
to stop exposing explicit `detail_rows`.

Current migration trial now applies to:

- `Leader Summary`
- `Latest Alerts`
- `Saved Batches`

Current implementation now includes:

- `_resolve_compatibility_rows_from_info_blocks(...)`

Current behavior:

- those grouped-summary view models now primarily expose `info_blocks`
- legacy flat compatibility rows can still be derived on demand from grouped text
  blocks when compatibility is needed
- producer-side grouped-summary migration was still partial at that moment, so
  the notes below record the later completion separately

This means the project has now moved from "new structure exists alongside old
structure" into an actual producer-side migration where selected sections
already treat `info_blocks` as the canonical detail payload.

Later on 2026-06-28, that producer-side migration was completed for the full
first grouped-summary set.

Current grouped-summary sections now all primarily expose `info_blocks`:

- `Strongest Sector`
- `Leader Summary`
- `Latest Alerts`
- `Saved Batches`

Current compatibility behavior:

- legacy flat detail rows are now derived through shared helper logic when
  needed instead of being kept as the main emitted detail structure in those
  view models

This means the first grouped-summary migration milestone is complete: the main
summary surfaces now share one canonical detail structure, and `detail_rows`
has been reduced to a compatibility-facing representation rather than a primary
view-model field.

- order
- display labels
- formatter rules

Leader summary, latest alerts, and saved batches now also share a replaceable
`detail_layout` metadata shape for grouped text rows:

- `item_prefix`: row prefix such as `- `
- `separator`: join token such as `: ` or ` | `
- `fields`: ordered source fields with optional `format_key`

This means list-style detail blocks are no longer hand-built separately in each
view-model function.

`strongest_sector` spotlight details now use that same `detail_layout`
mechanism as well, including field-level prefixes and formatter rules.
This means the dashboard's main detail-style surfaces now share one common
configuration model instead of mixing table config with ad-hoc string assembly.

Later on 2026-06-28, the grouped-summary compatibility surface was narrowed one
step further.

Current grouped-summary helper boundary now looks like this:

- canonical build path: `items -> sections -> info_blocks`
- compatibility rows are derived only when an old flat-row consumer still needs
  them

Current implementation keeps:

- `_resolve_compatibility_rows_from_info_blocks(...)`

Current implementation no longer keeps the thin helper that rebuilt grouped
sections from compatibility rows before turning them back into blocks.

The grouped-summary-specific compatibility resolver was also removed after the
main code path stopped depending on it, so tests now verify the narrower
`info_blocks -> compatibility rows` behavior directly.

This means the migration is now cleaner in practice: modern rendering resolves
`info_blocks` first, while legacy `detail_rows` fallback remains available
through a narrower compatibility helper surface instead of multiple overlapping
adapter helpers.

Later on 2026-06-29, the remaining grouped-summary row builder was also renamed
to reflect its true scope.

Current implementation now uses:

- `_build_grouped_summary_rows_from_items(...)`

instead of a generic-sounding detail-row helper name.

This means the code now communicates the boundary more clearly: flat text rows
are no longer framed as a reusable dashboard-wide data shape, but as a narrow
internal assembly step inside grouped-summary presentation.

Later on 2026-06-29, the remaining grouped-summary render fallback was also
split into an explicit legacy conversion helper.

Current implementation now uses:

- `_build_legacy_grouped_summary_info_blocks(...)`

for the old `detail_rows -> info_blocks` compatibility path.

This means `_resolve_grouped_summary_render_blocks(...)` now reads more cleanly:
it prefers modern `info_blocks` first, and only enters a clearly named legacy
conversion step when an old grouped-summary input still arrives in flat-row
form.

Later on 2026-06-29, that legacy-input boundary was made explicit one step
further.

Current implementation now uses:

- `_resolve_legacy_grouped_summary_rows(...)`

to read old grouped-summary `detail_rows` inputs.

This means the render path now matches the real project state more honestly:
grouped-summary producers no longer emit `detail_rows`, and the remaining flat
row read path exists only as a named compatibility reader for older inputs.

Later on 2026-06-29, the stock-pool health block also got one small structural
cleanup to keep its block assembly boundary explicit.

Current implementation now uses:

- `_build_health_info_blocks(...)`

to assemble the health block's ordered `info_blocks` payload from health-specific
content parts such as `meta_rows` and `detail_sections`.

This keeps the health block closer to the same presentation pattern used by the
grouped-summary path: view-model producers can still compute specialized helper
parts, but the final block assembly now has a dedicated named entry point.

Later on 2026-06-29, the health block's section assembly was also split into a
named helper.

Current implementation now uses:

- `_build_health_detail_sections(...)`

to assemble health-specific grouped text sections before they are wrapped into
`info_blocks`.

This means the health path now has a clearer staged shape as well:
health-specific rows -> `detail_sections` -> `info_blocks`.

Later on 2026-06-29, the health block's row-bucket assembly was also split into
its own helper.

Current implementation now uses:

- `_build_health_row_sources(...)`

to assemble the health-specific row buckets such as duplicate rows, issue rows,
suggestion rows, and hint rows before section assembly.

This means the staged health path is now clearer end-to-end:
health row sources -> `detail_sections` -> `info_blocks`.

Later on 2026-06-29, the first health-summary test assertions also began
shifting from flat helper fields toward direct `info_blocks` verification.

Current test migration now verifies the valid health-summary path through the
render-facing block structure first for meta-grid and grouped-section content.

This means the health-summary path has started the same kind of test-side
transition that grouped-summary already went through: prove the modern block
shape directly first, then reduce reliance on intermediate flat fields in later
steps.

Later on 2026-06-29, the invalid health-summary path also began migrating its
main assertions toward direct `info_blocks` checks.

Current invalid-path block assertions now cover:

- validation-issue section title
- duplicate row content
- issue-section rows
- suggestion-section structure
- hint rows

This means the health-summary test migration is no longer limited to the
healthy path; the warning/error path now also proves most render-facing content
through `info_blocks` first, leaving only a smaller compatibility-style set of
flat-field assertions behind.

Later on 2026-06-29, the remaining invalid-path flat `issue_rows` assertions
were also removed after equivalent `info_blocks` checks were in place.

This means the two main health-summary view-model tests now primarily validate
the render-facing block structure rather than intermediate flat helper fields,
which makes the later slimming of the final health view-model shape much safer.

Later on 2026-06-29, that slimming step was applied to the health-summary view
model itself.

Current health-summary view models now stop explicitly returning the intermediate
flat helper fields such as:

- `meta_rows`
- `duplicate_rows`
- `issue_rows`
- `suggestion_rows`
- `hint_rows`
- `detail_sections`

and instead keep `info_blocks` as the render-facing detail structure.

This means the health-summary path has now moved beyond helper extraction and
test migration into an actual final view-model narrowing step, much closer to
the grouped-summary direction established earlier.

`app/history.py` now supports lightweight historical review:

- list saved snapshot timestamp batches
- build a simple summary for a selected timestamp batch
- summarize strongest stored sector and alert count for that batch

This gives the project a minimal manual replay/review capability on top of
persisted SQLite data.

`app/reports/evening_report.py` now supports a database-backed report path:

- read the latest market snapshot batch from SQLite
- read the latest alert batch from SQLite
- derive strongest and fading sectors from stored snapshot data
- derive leader display from stored snapshot data
- build a usable evening report from persisted records

`app/database.py` now also supports:

- fetching only the latest timestamp batch of market snapshots
- fetching only the latest timestamp batch of alerts

This gives the project a real "store first, read later" reporting path.

`app/main.py` now supports dual-source quote ingestion:

- prefer realtime quotes from the AKShare adapter
- fall back to deterministic demo rows when realtime quotes are unavailable
- persist either path into SQLite with the same downstream schema

This gives the project a stable operating pattern:

- realtime when available
- deterministic fallback when offline or broken

`app/data_sources/akshare_client.py` now supports a stable adapter boundary:

- optional injected fetch function for tests and offline runs
- real `ak.stock_zh_a_spot_em()` default fetch path when AKShare is installed
- normalization after fetch
- observation-universe filtering after fetch
- graceful fallback to an empty dataframe on fetch failure

This means the project now has a testable bridge between deterministic local
logic and real quote ingestion.

`app/main.py` now persists demo execution outputs:

- market snapshots are written into SQLite
- generated alerts are written into SQLite
- console output and persistence happen in the same run

This means the current local demo now forms a durable closed loop:

- build demo market data
- run leader detection
- generate alerts
- print reports and alerts
- save snapshots and alerts

`app/database.py` now supports:

- SQLite table bootstrap for `market_snapshot` and `alerts`
- saving market snapshots
- fetching market snapshots
- saving alerts
- fetching alerts

Persistence is intentionally lightweight and uses direct `sqlite3`.

`app/reports/morning_report.py` now supports:

- structured morning report composition
- stable output fields from dictionary inputs

`app/reports/evening_report.py` now supports:

- structured evening report composition
- leader, news, and strategy sections

`app/main.py` now supports a deterministic phase-one demo flow:

- universe summary
- morning report rendering
- alert evaluation and console output
- evening report rendering

This is the first true end-to-end local demo path.

`app/alerts/alert_rules.py` now supports:

- market-driven alert triggers
- sector move alerts
- materials/gases focus alerts
- S-level news flash alerts

`app/alerts/notifier.py` now supports:

- formatted console alert output
- stable human-readable alert layout

Current phase-one alert types:

- `price_spike`
- `volume_spike`
- `sector_move`
- `materials_focus`
- `news_flash`

`app/analysis/trend_judger.py` now supports:

- short-term trend judgement
- current states:
  - 强趋势
  - 弱趋势
  - 震荡
  - 冲高回落
  - 退潮
- explainable reason strings
- basic trend scoring

Current phase-one trend rules use:

- MA5 / MA10 / MA20
- current turnover versus 5-day average turnover
- stock performance versus sector performance
- intraday high versus close fade

`app/analysis/leader_detector.py` now supports:

- per-sector leader scoring
- top-3 leader candidate output for each sector
- explainable leader type classification
- human-readable reason strings

Current leader types:

- 涨幅龙头
- 成交额龙头
- 趋势龙头
- 情绪龙头

The implementation is intentionally rule-based and phase-one simple.

## Latest Completed Slice

`app/main.py` now supports an optional end-of-run review append mode:

- controlled by `MONITOR_AUTO_LATEST_REVIEW`
- defaults to off
- when enabled, prints a `Latest Database Review` section after the normal demo flow

This keeps the default console output compact while allowing a richer local
review mode without switching CLI commands.

`app/config.py` now also supports:

- boolean environment parsing for small runtime feature flags
- `auto_latest_review` in application config

`README.md` now documents:

- default demo run
- `latest-review`
- `history-review <timestamp>`
- optional automatic latest-review append mode

`app/pipeline.py` now provides a reusable core monitor pipeline:

- `run_monitor_cycle(config)` handles collect, analyze, and persist
- `build_cycle_console_output(config, result)` handles console rendering only
- the database is initialized inside the reusable cycle path

This separates business execution from terminal presentation and makes the
manual run path easier to reuse later.

`app/scheduler.py` now also provides:

- `run_monitor_job(config)` as a thin scheduler-facing wrapper around the same
  reusable pipeline

This gives the project a stable entry point for future timed execution without
duplicating main-flow logic.

`app/scheduler.py` now also supports explicit phase-one job registration:

- `register_default_jobs(scheduler, config)`
- default `morning-check` at `09:35`
- default `afternoon-review` at `14:45`
- works both with APScheduler and the local no-op fallback scheduler

This keeps scheduled behavior explicit and testable while preserving safe local
degradation when optional dependencies are missing.

`app/config.py` and `app/main.py` now support explicit scheduler enablement:

- `MONITOR_ENABLE_SCHEDULER` defaults to `false`
- normal demo runs do not register or immediately shut down background jobs
- `python -m app.main run-scheduler` is the dedicated scheduler entry mode
- scheduler mode only registers jobs when the feature flag is enabled

This makes startup behavior much clearer:

- manual use stays manual
- background scheduling is opt-in
- local misuse fails safely and visibly

`app/main.py` and `app/scheduler.py` now also support a lightweight scheduler
status view:

- `python -m app.main scheduler-status`
- shows whether scheduler mode is enabled
- lists the current default registered jobs and times
- shows runtime mode such as `scheduler-ready` or `fallback-noop`
- shows whether persistent loop support is available
- shows install and verification guidance when scheduler support is missing
- shows the next recommended command based on current runtime readiness

This gives the project a simple local inspection path in VS Code without
starting background scheduling.

`app/scheduler.py` now also supports a lightweight runtime loop:

- `run_scheduler_loop(scheduler)`
- starts real scheduler-like runtimes when supported
- keeps a small wait loop alive for local background mode
- exits cleanly on `KeyboardInterrupt`
- returns a clear installation hint when only the no-op scheduler is available

This means `run-scheduler` is now a real long-running mode instead of a
register-and-exit placeholder.

`app/main.py` now prints scheduler diagnostics before entering background mode:

- `run-scheduler` now shows the same runtime summary as `scheduler-status`
- startup output includes runtime mode and persistent-loop availability
- fallback installs are still visible before the loop decision

This makes background startup safer and more transparent in VS Code.

`app/main.py` now also supports a manual scheduler-style trigger:

- `python -m app.main run-job-now`
- reuses `run_monitor_job(config)`
- prints the same structured console report as the normal demo flow
- still gives a simple completion message for local spot checks

This creates a clean middle ground between:

- full background scheduling
- ordinary demo execution

and makes scheduler-path debugging easier in VS Code.

`app/main.py` now uses a shared command banner for scheduler-oriented entry paths:

- shown by `run-job-now`
- shown by `run-scheduler`
- includes mode, environment, and database target

This gives manual and background command modes a more unified terminal
experience.

`scheduler-status` now also includes the current database target, so status and
startup banners expose the same core environment context.

The default demo path now also uses a lighter version of the shared command
banner, so the main entry paths now feel consistent:

- default demo: light mode/environment banner
- `run-job-now`: full scheduler command banner
- `run-scheduler`: full scheduler command banner plus runtime diagnostics

Phase two has now started with a minimal local dashboard layer:

- `app/dashboard/overview.py` builds a database-backed latest-view payload
- `app/dashboard/streamlit_app.py` renders a first Streamlit page
- current dashboard shows historical batch selection, latest batch data,
  counts, strongest sector, leader summary, sector strength cards, sector
  strength chart, top movers, top-mover chart, latest alerts, and saved
  batches

This is intentionally small and database-first, so later UI work can stay
decoupled from the monitoring pipeline.

Dashboard presentation is now split from dashboard data:

- `app/dashboard/overview.py` owns the data payload
- `app/dashboard/presentation.py` owns chart and KPI presentation metadata
- `app/dashboard/streamlit_app.py` reads both layers to render the UI

This keeps chart style, labels, and layout mapping easy to replace without
impacting the main monitoring logic.

Dashboard KPI cards now also support a lightweight alert-balance layer:

- `app/dashboard/overview.py` now exposes `positive_alert_count` and
  `negative_alert_count`
- the first pass uses explicit keyword rules for negative-alert detection
- `app/dashboard/presentation.py` maps KPI labels and styles separately from
  those payload keys

This keeps card wording, order, and styling easy to swap later without
rewriting business summaries.

Dashboard content sections are now also presentation-driven:

- `app/dashboard/presentation.py` now exposes content-section specs for
  strongest-sector text, leader summary, latest alerts, and saved batches
- `app/dashboard/streamlit_app.py` now renders those sections through a shared
  content-block renderer instead of hardcoding each section inline

This keeps text layout, displayed columns, and block order easier to replace
without touching database payload construction.

Dashboard page order is now also config-driven:

- `app/dashboard/presentation.py` now exposes `build_page_layout_specs()`
- `app/dashboard/streamlit_app.py` now renders the page by looping over layout
  specs instead of hardcoding section order in `main()`

This means later dashboard regrouping or reordering can stay isolated to the
presentation layer.

Dashboard page-level theme metadata now exists:

- `app/dashboard/presentation.py` now exposes `build_theme_spec()`
- page title, app title, batch selector label, caption template, and layout
  width are now read from that theme config

This gives the dashboard a first lightweight theme boundary before deeper style
work such as spacing, colors, or alternate view variants.

Dashboard view variants now exist:

- `app/dashboard/presentation.py` now exposes `build_view_variant_specs()`
  and `resolve_dashboard_view_spec()`
- the dashboard currently supports `default` and `compact` variants
- `app/dashboard/streamlit_app.py` now resolves the page through a variant
  spec before rendering

This gives us a safe path for alternate dashboard densities or audience-focused
views without duplicating data logic.

Dashboard variant selection is now user-facing:

- `app/dashboard/streamlit_app.py` now shows a `Dashboard View` selector
- the current UI safely falls back to `default` when a saved or requested
  variant key is unknown
- variant display names now live in presentation metadata alongside layout
  definitions

This gives future view expansion a stable entry point inside the dashboard UI.

Config compatibility was also restored during this slice:

- `app/config.py` now again exposes `default_protocol`
- command, pipeline, and scheduler status output all include the same protocol
  line expected by the existing CLI tests

The monitored stock universe is now file-backed instead of Python-list backed:

- `app/universe/stock_pool.py` now loads the universe from a source file
- default source file: `app/universe/stock_pool.json`
- optional override path: `MONITOR_STOCK_POOL_PATH`
- supported formats: `.json` and `.csv`

This means monitored stocks and board coverage can now be updated by editing
the source file, without changing the universe module code itself.

Stock-pool validation is now available from the CLI:

- `app/universe/stock_pool.py` now exposes `validate_stock_pool()`
- `python -m app.main validate-stock-pool` prints a quick validation summary
- current checks cover required fields, source readability, duplicate codes,
  sector counts, and priority counts

This gives the stock-universe maintenance flow a safer local self-check step.

Stock-pool validation now also includes lightweight structure health hints:

- warns when sector coverage is too narrow
- warns when no `priority=1` focus names are configured
- warns when one sector becomes too concentrated inside the pool

This means edits to `app/universe/stock_pool.json` or a custom CSV/JSON source
now produce not only raw counts, but also quick judgment hints about whether
the monitored structure may have drifted.

The dashboard now also includes a reusable stock-pool health summary block:

- `app/dashboard/overview.py` adds a compact `stock_pool_health` payload
- `app/dashboard/presentation.py` exposes a separate `stock_pool_health`
  content-section spec
- `app/dashboard/streamlit_app.py` renders that summary without coupling page
  layout to raw stock-pool validation logic

This means stock-pool maintenance status is now visible in both:

- CLI validation output
- the local Streamlit dashboard

That dashboard health block is now also presentation-driven at the copy/tone
level:

- status labels such as `Healthy` and `Needs Attention`
- tone mapping such as `success` and `error`
- field labels such as tracked-stock count and duplicate-code label
- empty-state hint copy

`app/dashboard/streamlit_app.py` now builds a dedicated health-summary view
model from presentation metadata before rendering, so later visual swaps can
stay isolated from the underlying validation payload.

That health-summary view model is now also grouped for card-style rendering:

- `badge_text` for a compact status badge line
- `summary_metrics` for top-line card metrics such as tracked-stock count,
  hint count, and duplicate-code count
- `meta_rows` for supporting fields such as source path
- `hint_rows` for the warning/detail list

This means later UI changes can focus on visuals first, because the dashboard
already has a stable grouped structure for the stock-pool health card.

The same grouped-summary pattern is now also reused by two more dashboard
summary sections:

- `strongest_sector` now has a structured
  `strongest_sector_summary` payload with sector, average change, and stock
  count
- `leader_summary` now renders through a grouped summary view model instead of
  raw JSON output

This means the dashboard summary area is starting to share one presentation
language:

- badge text
- compact top-line metrics
- short supporting detail rows

That grouped-summary pattern now also covers the remaining two lighter summary
blocks:

- `latest_alerts` now renders through an alerts-grouped view model
- `saved_batches` now renders through a batch-list grouped view model

This means the whole dashboard summary area is now largely consistent in
structure, even when the underlying content is different.

Section-level tone metadata now also exists for grouped summary blocks:

- `strongest_sector`: `accent`
- `leader_summary`: `neutral`
- `latest_alerts`: `warning`
- `saved_batches`: `neutral`

That tone now flows from presentation metadata into each grouped summary view
model, so later visual emphasis changes can stay configuration-first instead
of requiring per-block logic edits.

Grouped summary blocks now also share one markdown-header render helper:

- `app/dashboard/streamlit_app.py` now builds grouped section headers through
  `_build_grouped_section_header_markdown(view_model)`
- the shared header currently renders tone text plus badge text and a divider

This means later visual upgrades can keep using one render entry point instead
of editing each grouped summary block separately.

The same tone vocabulary now also reaches KPI cards and chart headers:

- KPI specs now include `tone`
- chart specs now include `tone`
- `app/dashboard/streamlit_app.py` now uses shared helpers for KPI captions
  and chart markdown headers

This means the dashboard has started to share one theme-language across:

- grouped summary blocks
- KPI cards
- chart section headers

Tone-specific ASCII icon mapping now also exists in the Streamlit render layer:

- `app/dashboard/streamlit_app.py` exposes `_resolve_tone_icon(tone)`
- grouped summary headers, KPI captions, and chart headers now all read from
  that shared icon resolver

This gives future visual upgrades a single entry point for symbolic emphasis,
before moving to richer icons or UI wrappers.

Tone-specific panel-title composition now also exists:

- `app/dashboard/streamlit_app.py` exposes `_build_tone_panel_title(tone, label)`
- grouped section headers, KPI captions, and chart headers now build their
  visible tone titles from that single helper

This means future UI polish can replace one panel-title builder instead of
rewriting several header/caption code paths.

Section headers are now also wrapped through a shared panel-block helper:

- `app/dashboard/streamlit_app.py` now exposes `_build_panel_block_markdown(title, body)`
- grouped summary headers and chart headers now render through that shared
  block wrapper instead of plain single-line markdown

This creates a stronger section feel while still keeping visual formatting
centralized in one helper layer.

The KPI area now also uses a shared panel-block entry:

- `app/dashboard/streamlit_app.py` now exposes
  `_build_kpi_section_header_markdown()`
- `_render_kpi_cards()` now renders through that shared KPI panel header before
  the metric columns

This means the dashboard's top KPI area and the summary/chart areas are now
much closer in structural presentation.

Dashboard panel density is now also variant-driven:

- `app/dashboard/presentation.py` theme metadata now includes
  `panel_density`
- `default` currently uses `comfortable`
- `compact` currently uses `compact`

This means later spacing or copy-density changes can now be switched per view
variant instead of being hardcoded inside each render block.

Panel body copy now also supports density-aware shortening:

- `app/dashboard/streamlit_app.py` now exposes
  `_build_panel_body_text(body, panel_density=...)`
- compact mode currently shortens longer panel body text
- comfortable mode keeps the full body copy

This gives the dashboard a first lightweight content-density layer before we
introduce richer spacing or style wrappers.

Panel density now flows through the shared render path:

- `main()` resolves `theme["panel_density"]`
- `_render_page_layout()` receives that density value once
- KPI headers, chart headers, and grouped-summary headers now all render with
  the same density context

This keeps future visual changes centralized and reduces the risk that one
dashboard section drifts away from the others.

Grouped summary blocks now also have a shared summary-card wrapper layer:

- `app/dashboard/presentation.py` now exposes
  `build_summary_panel_style_spec()`
- that style spec currently owns replaceable supporting-copy metadata for
  normal and compact density
- `app/dashboard/streamlit_app.py` now exposes
  `_build_grouped_summary_card_markdown(...)`
- grouped summary rendering now uses that shared card wrapper before metrics
  and detail rows

This gives us a clearer style boundary for summary cards, so card copy and
lightweight typography rhythm can change without touching the grouped-summary
business view models.

That shared card-wrapper approach now also reaches health-summary and chart
areas:

- `build_summary_panel_style_spec()` now also owns separate supporting-copy
  metadata for health and chart sections
- `app/dashboard/streamlit_app.py` now exposes
  `_build_health_summary_card_markdown(...)`
- `app/dashboard/streamlit_app.py` now exposes
  `_build_chart_panel_markdown(...)`
- health-summary rendering and chart rendering now both pass through those
  shared wrapper helpers before their main content blocks

This means more of the dashboard can now change appearance from presentation
metadata first, instead of needing section-specific render rewrites.

Shared title and status wrappers now also exist:

- `app/dashboard/streamlit_app.py` now exposes
  `_build_section_title_markdown(...)`
- `app/dashboard/streamlit_app.py` now exposes
  `_build_health_status_markdown(...)`
- chart and content sections now use the shared title wrapper instead of raw
  `subheader` calls
- health-summary state messaging now uses the shared status wrapper instead of
  direct tone-specific Streamlit status calls

This means section framing is now more consistent, and fewer visual decisions
are hardcoded inside individual render branches.

Shared empty-state wrappers now also exist:

- `build_summary_panel_style_spec()` now also owns
  `empty_state_supporting_copy`
- `app/dashboard/streamlit_app.py` now exposes
  `_build_empty_state_markdown(...)`
- chart no-data branches, grouped-summary no-detail branches, and content-level
  empty branches now route through that shared empty-state wrapper

This means empty and fallback presentation is now much less scattered, so
later copy or visual changes can stay centralized.

Shared panel assembly now also has a lower-level single entry point:

- `app/dashboard/streamlit_app.py` now exposes
  `_build_info_panel_markdown(...)`
- grouped-summary support blocks, health blocks, status blocks, chart detail
  blocks, section-title blocks, and empty-state blocks now reuse that shared
  panel builder
- that builder also supports preserving full support-copy text even when
  compact density is active

This means later visual upgrades have a cleaner foundation: more of the
dashboard's panel framing now depends on one assembly helper instead of many
slightly different block builders.

The shared panel layer has now also moved from plain fenced markdown blocks to
HTML card containers with injected CSS:

- `app/dashboard/presentation.py` now exposes
  `build_panel_container_style_spec()`
- `app/dashboard/streamlit_app.py` now exposes
  `_build_dashboard_panel_css(...)`
- `main()` now injects that shared panel CSS once at page startup
- `_build_panel_block_markdown(...)` now renders HTML card containers with
  `dashboard-panel` class names instead of fenced code blocks

This means future visual upgrades can now happen much more naturally through
surface tokens and CSS, instead of being limited by text-block formatting.

That shared card surface now also supports tone-specific class styling:

- `build_panel_container_style_spec()` now owns replaceable tone border tokens
  such as `tone_accent_border`, `tone_warning_border`, and related values
- `app/dashboard/streamlit_app.py` now exposes
  `_resolve_panel_tone_class(tone)`
- `_build_panel_block_markdown(...)` now attaches tone-specific
  `dashboard-panel--...` classes to each card container
- `_build_dashboard_panel_css(...)` now styles tone-specific border colors and
  title colors through those shared classes

This means future card-style changes can now happen along two clean axes:

- change the surface theme tokens in presentation metadata
- change the CSS implementation in one render helper layer

without touching the dashboard's business payloads or section render order.

The KPI area now also has its own replaceable wrapper-style layer:

- `app/dashboard/presentation.py` now exposes
  `build_kpi_panel_style_spec()`
- that KPI style spec currently owns:
  - section supporting copy
  - compact section supporting copy
  - shared KPI metric supporting copy
  - default tone metadata
- `app/dashboard/streamlit_app.py` now exposes
  `_build_kpi_metric_panel_markdown(...)`
- `_render_kpi_cards()` now renders:
  - one shared KPI section wrapper
  - one shared KPI card wrapper per metric before the native Streamlit metric

This means the dashboard now has a more consistent presentation architecture
across:

- KPI cards
- grouped summary cards
- health/status blocks
- chart wrapper cards
- section title / empty-state wrappers

and future typography or rhythm changes for the KPI zone can now stay mostly
inside presentation metadata plus shared helper functions.

Metric-value sections now also have a shared group wrapper layer:

- `app/dashboard/presentation.py` now exposes
  `build_metric_group_style_spec()`
- that metric-group style spec currently owns:
  - default group label copy
  - normal-density supporting copy
  - compact-density supporting copy
  - default tone metadata
- `app/dashboard/streamlit_app.py` now exposes
  `_build_metric_group_markdown(...)`
- the dashboard now uses that shared metric-group wrapper before native metric
  rows in:
  - KPI cards
  - stock-pool health summary metrics
  - grouped summary metrics

This means the dashboard now has a cleaner separation between:

- card/wrapper styling
- metric-group framing
- the native Streamlit metric values themselves

so future spacing, grouping, or copy changes around top-line values can stay
mostly inside shared presentation helpers.

KPI value formatting now also has a replaceable presentation boundary:

- `app/dashboard/presentation.py` now exposes
  `build_kpi_value_format_spec()`
- KPI card specs now carry `format_key` metadata
- `app/dashboard/streamlit_app.py` now exposes
  `_format_kpi_metric_value(...)`
- current built-in formatter rules cover:
  - `timestamp`
  - `count`
  - `default`

This means future display changes such as:

- shorter timestamp formats
- thousands separators for counts
- additional percent / decimal formatter types

can now be introduced mostly through presentation metadata plus one shared
render helper, without changing the dashboard payload builders.

Summary-metric values now also reuse that same formatter path:

- content-section `summary_metrics` metadata now supports `format_key`
- current summary-metric formatter coverage includes:
  - `percent_1` for values such as average sector change
  - `count` for stock counts, alert counts, batch counts, and health counters
- grouped summary and health-summary metric rows now format values through the
  same shared helper used by KPI cards

This means the dashboard is now much closer to one unified display language
for top-line values across:

- KPI cards
- strongest-sector summary metrics
- stock-pool health metrics
- leader / alert / saved-batch summary metrics

The shared formatter layer now also supports signed percent display:

- `build_kpi_value_format_spec()` now includes `signed_percent_1`
- `Strongest Sector` summary metrics now use that signed percent formatter for
  `Avg Change`
- `_format_kpi_metric_value(...)` now supports explicit plus-sign rendering for
  positive percentage values, for example `+6.9%`

This means top-line summary metrics can now communicate directional strength
more clearly without requiring section-specific display logic.

Detail-row text now also starts to reuse the shared formatter layer:

- `app/dashboard/streamlit_app.py` now exposes `_format_detail_value(...)`
- latest-alert detail rows now format `timestamp` through the shared timestamp
  formatter
- saved-batch detail rows now also format timestamps through that same shared
  formatter
- strongest-sector detail text now also includes the formatted signed average
  change value

This means the dashboard is now closer to one presentation language across:

- KPI metrics
- summary metrics
- selected detail-row text

instead of formatting timestamps and directional values separately in each
content block.

Column-level formatter metadata now also exists for selected dashboard lists:

- chart specs now support `table_column_formats`
- content specs now support `detail_column_formats`
- `app/dashboard/streamlit_app.py` now exposes
  `_format_rows_for_display(...)`
- chart table rows now format selected columns through metadata instead of
  inline per-table logic
- latest-alert detail rows now read timestamp formatting from
  `detail_column_formats` metadata instead of a hardcoded branch

This means the dashboard is starting to support one more replaceable boundary:

- not just "this section has formatted values"
- but "this column in this list/table uses this display formatter"

which is a better long-term base for later table and detail-row polish.

Later on 2026-06-28, the grouped-summary compatibility migration advanced
further.

Current grouped-summary sections now all primarily expose `info_blocks`:

- `Strongest Sector`
- `Leader Summary`
- `Latest Alerts`
- `Saved Batches`

Current compatibility behavior:

- legacy flat detail rows are derived through shared helper logic when needed
  instead of being kept as the main emitted detail structure in those view
  models

Current implementation now also treats `info_blocks` as the canonical internal
shape inside the shared grouped-summary detail payload helper.

Current implementation effect:

- grouped-summary detail assembly now builds grouped text sections and
  `info_blocks` first
- legacy flat detail rows are then derived back from those blocks only when
  compatibility output is requested

This means the grouped-summary compatibility layer is now both narrower in
surface area and more clearly downstream of the new block-based presentation
model.

Later on 2026-06-28, that shared grouped-summary detail payload helper also
stopped explicitly returning legacy `detail_rows`.

Current behavior now is:

- the helper emits `info_blocks`
- compatibility-facing flat detail rows are derived later through shared
  compatibility resolvers when needed

This means internal grouped-summary assembly is now even less coupled to the
legacy flat-row shape, and `detail_rows` is closer to a pure derived interface
than a stored payload field.

Later on 2026-06-28, the grouped-summary helper vocabulary also shifted more
explicitly toward the new structure.

Current implementation now distinguishes more clearly between:

- legacy row-based compatibility helpers
- section-building helpers
- block-building helpers

Current implementation effect:

- the main grouped-summary assembly path now reads more like
  `items -> sections -> info_blocks`
- row-based helpers are retained, but named and positioned more clearly as
  compatibility-oriented adapters

This makes the codebase easier to read during the migration, because the helper
names now reflect which shape is canonical and which shape is transitional.

Later on 2026-06-28, test naming and helper wording were also aligned more
closely with that migration direction.

Current implementation effect:

- row-based paths are described more explicitly as compatibility-oriented input
  or fallback behavior
- tests now more consistently describe `info_blocks` as the primary structure
  and flat rows as derived compatibility output

This helps keep code, tests, and migration intent in sync, reducing the chance
that future changes accidentally promote the compatibility layer back to a
default mental model.

Later on 2026-06-28, the grouped-summary compatibility surface was narrowed
again by removing one thin compatibility-only block-conversion wrapper.

Current implementation effect:

- compatibility row input now feeds block rendering through a smaller set of
  core adapters
- fewer helper names sit between compatibility rows and grouped sections/blocks

This means the compatibility layer is becoming easier to reason about: there
are fewer transitional entry points, and the remaining ones are more clearly
the essential boundary adapters.

## Next TDD Slice

Implement the next business layer with tests for:

- refining the shared formatter layer further, for example by introducing
  broader table-column formatter coverage or a shared formatter-registry
  boundary without changing the current business view models
- continuing to move typography and supporting-copy decisions into
  presentation helpers instead of section-specific logic

## Important Constraints

- use `apply_patch` for file edits
- do not rely on `python` or `py` being on PATH in this environment
- bundled Python path is:
  `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

## Notes For Future Turns

- If context gets compressed, resume from the "Next TDD Slice" section first.
- Keep phase one rule-based and explainable.
- Prefer stable local behavior over premature optimization.

Later on 2026-06-29, work was intentionally pulled back to the business mainline.

Why this refocus happened:

- recent iterations improved dashboard configurability and presentation reuse
- that work remains useful, but it had started to move ahead of the shortest
  path toward a stronger research workflow

Business-mainline checkpoint:

- the next useful slice is to make morning review work from persisted database
  data in the same spirit as the existing evening review
- this keeps the product centered on a practical loop:
  ingest -> persist -> summarize -> inspect

Current TDD slice:

- add `build_morning_report_from_database(...)`
- derive the morning view with explicit rules only:
  sector-average strength, top movers, latest risk messages, and a simple
  position-bias hint
- expose a `latest-morning-review` command in `app/main.py`
- cover both the report builder and command path with tests

Later on 2026-06-29, the next step stayed on the business mainline by reducing
report duplication instead of adding more presentation-specific surface area.

What changed conceptually:

- morning and evening reports were recognized as two variants of the same
  product behavior: structured monitor context becomes a readable summary
- the repeated mechanics were not the market rules themselves, but the text
  assembly layer: title, intro lines, sections, and list joining

Current implementation direction:

- introduce a shared report-text helper so both reports assemble from the same
  section skeleton
- keep business rules local to each report builder while moving only formatting
  mechanics into the shared layer
- preserve output shape so command-line usage and downstream checks stay stable

Later on 2026-06-29, the report layer was pushed one step closer to a stable
business rule backbone.

What this step focused on:

- move reusable context rules out of individual report files
- keep morning and evening summaries aligned on the same core calculations:
  sector ranking, top-stock extraction, and alert-message classification

Current rule-layer direction:

- shared helpers now own the common data-selection rules
- report files stay responsible for wording and section layout only
- this reduces the chance that morning and evening report logic drift apart when
  the monitored universe or alert coverage expands later

Later on 2026-06-29, the realtime pipeline was brought closer to the same rule
layer already used by the database-backed reports.

What this step focused on:

- stop treating `app/pipeline.py` context assembly as a separate demo-only path
- route realtime morning/evening context building through the same sector-rank,
  top-stock, and alert-selection helpers

Current effect:

- database review and live-cycle review now share more of the same business
  calculations
- remaining differences are more intentional and wording-oriented instead of
  accidental rule drift

Later on 2026-06-29, the evening report risk view was aligned with the same
shared risk-selection logic already used elsewhere.

What this step focused on:

- remove the fixed placeholder-style `negative_news` path from evening review
- let both database-backed and realtime evening summaries consume extracted risk
  messages directly

Current effect:

- morning and evening reports now look at risk through a more consistent rule
  boundary
- the remaining divergence between the two reports is increasingly about when
  and how the information is phrased, not about whether the same risks are seen

Later on 2026-06-29, the "tomorrow plan" section also moved away from a fixed
business sentence and toward a simple rule-driven suggestion layer.

What this step focused on:

- build a reusable next-session observation rule from strongest sector,
  secondary sector, and current risk count
- make evening database review and realtime evening review generate strategy
  copy from that same shared rule

Current effect:

- another visible hard-coded business sentence has been replaced by an explicit,
  testable rule
- report suggestion text is becoming easier to evolve without splitting logic
  across multiple files

Later on 2026-06-30, the morning `a_share_mapping` text was also pulled into a
shared mapping rule instead of being derived from string concatenation inside
report builders.

What this step focused on:

- move the A-share mapping sentence into a dedicated rule helper
- keep a safe fallback for unknown sectors while adding clearer mapping copy for
  materials, gases, equipment, and compute-related sectors

Current effect:

- future stock-pool and sector-taxonomy expansion can extend the mapping rule
  in one place
- the morning report is carrying less hidden business wording in the renderer

Later on 2026-06-30, the A-share mapping helper was pushed one step further
toward configuration-style maintenance.

What this step focused on:

- move mapping keyword groups and suffix copy into shared sector data
- keep the report rule itself lightweight so future taxonomy changes mostly mean
  editing the mapping table instead of expanding branching logic

Current effect:

- `build_a_share_mapping(...)` is now closer to a table lookup over maintained
  rule entries
- expanding AI upstream/downstream categories should require less Python logic
  churn

Later on 2026-06-30, the next-session strategy rule was also reshaped to look
more like the same kind of maintained rule table used by the A-share mapping
helper.

What this step focused on:

- move tomorrow-plan copy selection into a small shared configuration table
- make both mapping and strategy generation follow a similar pattern:
  maintained rules first, formatting logic second

Current effect:

- the rule layer is becoming more internally consistent
- future report-rule expansion should feel more like editing maintained entries
  than writing new branching code

Later on 2026-06-30, the strength-label and position-bias rules were also
pulled into the same maintained-rule style as the mapping and tomorrow-plan
helpers.

What this step focused on:

- move threshold-based labels into shared sector-side rule entries
- keep `context_rules.py` focused on interpreting rule tables instead of owning
  several separate hard-coded thresholds

Current effect:

- four visible report-rule families now follow a more consistent maintenance
  pattern
- future tuning of labels or bias thresholds should require less direct logic
  editing

Later on 2026-06-30, the report-rule families were moved one step closer to
"edit config, then rerun" maintenance.

What this step focused on:

- move maintained rule entries into a local JSON configuration source
- keep Python code responsible for reading and interpreting those entries while
  reducing hard-coded rule data in module bodies

Current effect:

- changing mapping, strategy, strength, or bias rules is now more configuration-
  like than code-like
- future AI upstream/downstream taxonomy expansion should involve less Python
  editing and more straightforward rule-file maintenance

Later on 2026-06-30, a dedicated maintenance note was added for the report rule
configuration file.

What this step focused on:

- document what each rule family controls
- explain the matching order, fallback behavior, and safe editing approach for
  `app/report_rule_config.json`

Current effect:

- future manual rule edits should be lower-risk and easier to understand
- the project now has both the config file and a readable companion guide

Later on 2026-06-30, the project entry documentation was updated so the new
rule-configuration path is visible directly from the main README.

What this step focused on:

- add `app/report_rule_config.json` and its companion guide to the main file
  index
- expose the report-rule config path alongside the existing stock-pool config
  path in the README data/configuration section

Current effect:

- future maintenance should require less directory hunting
- both main editable sources are now discoverable from the project homepage:
  stock-pool config and report-rule config

Later on 2026-06-30, the morning report mapping layer was expanded so sector
classification can follow stock-pool chain-group edits more directly.

What this step focused on:

- add an `industry_chain_mapping_rules` family to
  `app/report_rule_config.json`
- add `get_chain_groups_by_sector()` in `app/universe/stock_pool.py`
- make the morning mapping sentence prefer stock-pool `chain_group` summaries
  while keeping the old keyword mapping as fallback
- preserve compatibility for older legacy sector labels such as
  `半导体材料/气体`
- refresh the rule-config guide and README so the linkage is visible in docs

Current effect:

- when a monitored sector already has maintained `chain_group` values in
  `app/universe/stock_pool.json`, the morning report can now render a more
  structure-aware chain summary without hard-coding that relationship in Python
- future AI upstream/downstream stock-pool expansion should be more
  "edit pool + edit wording config" and less "edit module logic"
- regression coverage now explicitly checks the new chain-mapping layer

Later on 2026-06-30, the stock-pool validation summary was extended with a
chain-group distribution view.

What this step focused on:

- add `chain_group_counts` to `validate_stock_pool()`
- print a `Chain-group counts:` section in the `validate-stock-pool` terminal
  summary
- add regression coverage for both the raw validation payload and the CLI text
- document that chain-group structure is now part of the routine validation
  summary

Current effect:

- after editing `app/universe/stock_pool.json`, it is now easier to see whether
  the current monitor pool is over-tilted toward one chain position such as
  `材料`, `设备`, or `气体`
- future stock-pool maintenance can catch not only sector drift, but also
  industry-chain distribution drift in one pass

Later on 2026-06-30, the chain-group summary also gained a concentration-risk
hint layer.

What this step focused on:

- reuse the existing concentration threshold logic for `chain_group`
- add a health hint when one chain group occupies an overly large share of the
  monitored pool
- extend CLI regression coverage so the hint is verified in terminal output as
  well as in the raw validation result

Current effect:

- the validation flow now warns not only when one sector dominates the pool,
  but also when one industry-chain position dominates it
- this makes stock-pool rebalancing more direct when the monitored universe
  starts drifting too heavily toward one link such as `材料`

Later on 2026-06-30, the stock-pool health summary was consolidated into one
shared business-layer helper.

What this step focused on:

- add `build_stock_pool_health_summary()` to `app/universe/stock_pool.py`
- move health-risk resolution into the same stock-pool module
- make both terminal validation output and dashboard health payload read from
  the same summary structure
- extend regression coverage so shared summary fields such as
  `sector_counts`, `chain_group_counts`, and `priority_counts` are checked

Current effect:

- terminal and dashboard stock-pool health views now share one business result
  definition instead of maintaining parallel summary assembly paths
- future health-summary expansion should require less duplicate editing and
  carry lower risk of terminal/dashboard drift

Later on 2026-06-30, the dashboard health card started surfacing the stock-pool
structure counts directly.

What this step focused on:

- add a `Structure Counts` section to the stock-pool health card
- render `sector_counts`, `chain_group_counts`, and `priority_counts` through
  the existing grouped info-block path instead of adding a special-case widget
- extend Streamlit helper tests so the structure rows are checked explicitly

Current effect:

- the dashboard health area now shows both qualitative hints and quantitative
  pool structure breakdowns in the same summary card
- future extensions such as `pool_type` structure rows should fit the same
  render path with lower change cost

Later on 2026-06-30, the structure-count area was made easier to scan with
top-heavy summaries.

What this step focused on:

- add `Top Sectors` and `Top Chain Groups` rows ahead of the full structure
  breakdown
- keep those rows inside the existing `Structure Counts` section instead of
  creating a separate custom widget path
- sort the top rows by count first, then by name for stable display order

Current effect:

- the stock-pool health card now surfaces the main structural center of gravity
  faster when the monitored universe grows larger
- detailed full counts still remain visible below the top summaries, so the
  card keeps both overview value and audit value

Later on 2026-06-30, `pool_type` was brought into the same shared structure
summary path.

What this step focused on:

- add `pool_type_counts` to the reusable stock-pool health summary
- surface `Top Pool Types` and `Pool-type Counts` inside the dashboard health
  card's `Structure Counts` section
- extend stock-pool, dashboard-payload, and Streamlit helper tests so the
  `core / extended` split is checked end to end

Current effect:

- the stock-pool health view now covers all three main structural axes used in
  the editable pool file:
  sector, chain-group, and pool-type
- future work on `core / extended` pool balancing should now be easier to
  inspect without leaving the main health card

Later on 2026-06-30, the stock-pool health summary also gained a business-style
structure conclusion.

What this step focused on:

- add a shared `structure_summary` field to the stock-pool health summary
- derive one concise sentence from the dominant chain-group and pool-type split
- surface that sentence inside the dashboard readiness block instead of mixing
  it into the raw risk label

Current effect:

- the health view now not only shows counts and hints, but also translates the
  current pool shape into a faster human-readable conclusion such as
  "偏向材料链、core池占比高"
- terminal and dashboard can now reuse the same structure conclusion later
  without rebuilding separate copy logic

Later on 2026-06-30, the shared structure conclusion was also exposed in the
terminal validation summary.

What this step focused on:

- add `Structure summary:` to `python -m app.main validate-stock-pool`
- verify that the shared business summary text now appears in CLI output as
  well as in the dashboard health readiness area

Current effect:

- the user can now inspect the stock-pool structural conclusion without opening
  the dashboard
- terminal and dashboard have now converged further on the same business-facing
  health language

Later on 2026-06-30, the stock-pool structure conclusion itself was moved into
the shared rule-config layer.

What this step focused on:

- add `stock_pool_structure_summary` to `app/report_rule_config.json`
- load those structure-summary templates through `app/sectors.py`
- make stock-pool structure conclusions use config templates instead of fixed
  Python sentence bodies
- document the new config family and extend regression coverage around config
  loading plus CLI/render behavior

Current effect:

- future wording adjustments for stock-pool structure conclusions should now be
  "edit config, rerun checks" rather than "edit business logic"
- the report-rule config file now also governs one part of stock-pool health
  language, not only morning/evening report phrasing

Later on 2026-06-30, the terminal stock-pool validation output was regrouped
into clearer reading blocks.

What this step focused on:

- split `validate-stock-pool` terminal output into
  `Status Summary`, `Structure Summary`, and `Detailed Validation`
- keep the original validation details intact while making the reading order
  closer to how the user actually scans the terminal

Current effect:

- the terminal validation view is now easier to skim during daily maintenance
- top-line status, structure breakdown, and detailed registry checks are no
  longer mixed together in one long flat list

Later on 2026-06-30, the terminal structure-count sections were aligned more
closely with the dashboard's "look at the heaviest part first" reading order.

What this step focused on:

- sort terminal `sector_counts`, `chain_group_counts`, `pool_type_counts`, and
  `priority_counts` by count descending, then by label
- add a regression test to lock in that ordering

Current effect:

- the CLI now puts the heaviest structural buckets first, making the terminal
  summary faster to scan
- terminal and dashboard are now closer not only in content, but also in
  structural reading priority

Later on 2026-06-30, the stock-pool validator also gained a local
structure-baseline comparison step.

What this step focused on:

- add `build_stock_pool_health_comparison(...)` to compare the current health
  summary with the last saved local snapshot
- add `save_stock_pool_health_snapshot(...)` so each validation run updates the
  next baseline automatically
- extend `python -m app.main validate-stock-pool` with a new
  `Structure Comparison` block showing snapshot path, baseline status, and
  count deltas across `sector`, `chain_group`, `pool_type`, and `priority`
- add regression coverage for both the stock-pool business helper and the CLI
  text output
- document the optional `MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH` override in
  the README

Current effect:

- after each stock-pool edit, the validator can now show not only the current
  structure, but also what changed versus the previous local baseline
- this makes repeated maintenance safer when the monitored universe is being
  expanded, regrouped, or rebalanced over time

Later on 2026-06-30, that same stock-pool structure comparison was connected
into the dashboard health card as well.

What this step focused on:

- extend the dashboard stock-pool health payload with local baseline-comparison
  fields derived from `build_stock_pool_health_comparison(...)`
- keep the dashboard read-only for this feature, so page refreshes do not
  rewrite the comparison baseline automatically
- add a dedicated `Structure Comparison` grouped section to the health card
  alongside structure counts and health hints
- extend dashboard data, presentation, and Streamlit helper tests so the new
  comparison block is verified end to end

Current effect:

- terminal validation and dashboard health now expose the same local
  stock-pool change summary
- the user can inspect stock-pool drift from the page without needing to read
  only the terminal output

Later on 2026-07-01, the stock-pool comparison layer gained a more direct
"change highlight" summary.

What this step focused on:

- derive one concise rule-based highlight sentence from the strongest deltas in
  `sector`, `chain_group`, `pool_type`, and `priority`
- add that highlight to the `validate-stock-pool` terminal comparison block
- expose the same highlight in the dashboard stock-pool health comparison area
- extend regression coverage so the new highlight path is checked across the
  business helper, CLI output, dashboard payload, and Streamlit rendering

Current effect:

- after editing the stock pool, the user can now spot the main rebalance theme
  more quickly without reading every delta row
- the comparison surface is moving closer to a business-facing maintenance
  assistant instead of a raw structure diff only

Later on 2026-07-01, the stock-pool comparison result was extended with
reusable business tags.

What this step focused on:

- add a dedicated `comparison_tags` field to the stock-pool comparison result
- derive stable short tags such as `Materials Exposure Up`,
  `Watchlist Expanded`, `Core Pool Weight Up`, and
  `Priority-1 Focus Down` from structural deltas
- expose those tags in both the terminal `validate-stock-pool` output and the
  dashboard stock-pool health comparison section
- keep tags separate from the longer highlight sentence so future report,
  push-notification, or card-summary surfaces can reuse them directly

Current effect:

- stock-pool comparison is now producing both human-readable prose and
  machine-friendly short labels
- later business surfaces can reuse the same drift signals without needing to
  re-parse free-form summary text

Later on 2026-07-01, those comparison tags were split into stable internal keys
plus configurable display names.

What this step focused on:

- add `stock_pool_comparison_tags` to `app/report_rule_config.json`
- load that tag-display mapping through `app/sectors.py`
- keep comparison logic emitting stable internal tag keys such as
  `Materials Exposure Up`
- add parallel display labels such as `材料链加仓` for terminal and dashboard
  rendering
- document the new config family and extend regression coverage around config
  loading, CLI output, dashboard payloads, and Streamlit rendering

Current effect:

- comparison tags are now easier to reuse programmatically while still showing
  business-friendly wording to the user
- future changes like Chinese wording refinement, English wording refinement,
  or grouped display styles can happen in config without rewriting the core
  stock-pool comparison rules

Later on 2026-07-02, the stock-pool structure comparison gained a grouped
summary layer above the existing change tags.

What this step focused on:

- add `stock_pool_comparison_tag_groups` to `app/report_rule_config.json`
- expose grouped display labels through `app/sectors.py`
- keep existing stable tag keys and tag display names unchanged
- derive reusable higher-level groups such as `baseline_state`,
  `pool_scope`, `chain_exposure`, `pool_weight`, and `priority_focus`
- expose grouped summaries in the terminal `validate-stock-pool` output and
  in the dashboard stock-pool health comparison block
- extend regression coverage so grouped summaries remain aligned across
  comparison logic, dashboard payload assembly, Streamlit rendering, and
  presentation specs

Current effect:

- stock-pool structure comparison now has three layers:
  detailed delta rows, stable short tags, and grouped business summaries
- the terminal and dashboard can now show whether a change belongs to
  monitoring scope, chain exposure, pool weighting, or priority focus
  without re-parsing free-form text
- future wording or style replacement for grouped comparison summaries can be
  handled in config and presentation layers without changing the main logic

Later on 2026-07-02, the grouped stock-pool comparison summary was connected
into the reusable report output path.

What this step focused on:

- add `build_stock_pool_observation_lines(...)` to the shared report helpers
- keep report formatting separate from stock-pool comparison rule logic
- append a dedicated stock-pool observation section to both the morning report
  and evening report
- reuse the existing stock-pool structure summary, grouped comparison tags,
  and health hints in database-backed report builders
- clean up report tests into UTF-8 text and extend regression coverage around
  the new stock-pool observation section

Current effect:

- terminal validation, dashboard health cards, morning report, and evening
  report now share the same stock-pool structure comparison vocabulary
- when the monitoring universe changes, report readers can immediately see the
  structure summary, grouped drift direction, and lightweight reminders
  without relying only on dashboard inspection

Later on 2026-07-02, the same stock-pool observation layer was extended into
the realtime monitor-cycle output and console notification path.

What this step focused on:

- enrich `run_monitor_cycle(...)` with one shared stock-pool summary and
  comparison result per cycle
- feed that shared structure context into the direct morning/evening report
  builders used during a live monitor cycle
- add a reusable extraction helper so the cycle console output can surface a
  dedicated `Monitor Universe Observation` block without duplicating wording
- upgrade console notifier formatting to optionally append stock-pool
  structure summary, grouped drift observations, and health hints
- extend notifier and pipeline regression coverage around these shared
  business-facing summaries

Current effect:

- live cycle output, database-backed reports, dashboard cards, and validator
  output now stay aligned on the same stock-pool structure narrative
- alert notifications can now carry a compact stock-pool context block when
  later push or console surfaces need more business meaning than a single
  sector move alone

Later on 2026-07-02, the stock-pool context was moved one step earlier into
the alert generation stage itself.

What this step focused on:

- extend `evaluate_alerts(...)` so it can accept one shared stock-pool summary
  and one shared stock-pool comparison payload
- keep trigger thresholds unchanged while attaching stock-pool context only to
  high-value alerts such as `sector_move`, `materials_focus`, and `news_flash`
- leave lighter alerts such as `price_spike` and `volume_spike` free of extra
  payload so phase-one notifications stay compact by default
- update the monitor-cycle path to pass the already computed stock-pool
  summary/comparison into alert evaluation instead of re-deriving them later
- add regression coverage proving that high-value alerts receive the shared
  structure context while ordinary alerts remain lightweight

Current effect:

- stock-pool structure context is now part of the alert object itself for the
  alert types that most benefit from business interpretation
- future push, webhook, or scheduled notification surfaces can reuse the same
  alert payload directly without needing a second enrichment pass

Later on 2026-07-02, a unified alert-digest selector was added on top of the
enriched alert payloads.

What this step focused on:

- add digest selection rules to the console notifier so intraday and close
  summaries reuse one shared prioritization path
- prioritize `sector_move`, `materials_focus`, and `news_flash` in digest
  output while still allowing lighter alerts to appear when needed
- build compact single-line digest entries that can optionally carry the first
  stock-pool comparison group summary
- connect intraday and close digest blocks into the live cycle console output
  before and after the detailed alert blocks
- extend notifier and pipeline regression coverage around digest selection,
  digest rendering, and console integration

Current effect:

- the project now has a first reusable notification-summary layer instead of
  relying only on raw full alert blocks
- future console push, scheduled summary, or webhook delivery can reuse the
  same digest selector and wording without redesigning alert prioritization

Later on 2026-07-02, the scheduler and manual job entrypoints gained
job-specific output strategies.

What this step focused on:

- add a reusable job-output strategy map for `manual`, `morning-check`, and
  `afternoon-review`
- refactor cycle console rendering so the same monitor result can be rendered
  with different section combinations instead of one fixed full-output layout
- make scheduled job registration carry `job_id` explicitly for future
  scheduler-side routing
- add a scheduler-aware console-output builder and let `run-job-now` preview a
  specific scheduled profile such as `morning-check`
- surface output-profile summaries in scheduler status text so the current
  timing-to-output mapping is visible without reading code

Current effect:

- early-session and later-session jobs can now reuse the same monitor result
  while emitting different blocks that better match their timing purpose
- the project now has a clear extension point for future jobs such as midday
  check, pre-open prep, or close-only digest without rewriting output assembly

Later on 2026-07-02, the job-specific output layer was extended into a
higher-level task-intent strategy.

What this step focused on:

- add `JOB_INTENT_STRATEGIES` so each scheduler job can express why it runs,
  not only which blocks it shows
- let digest selection accept strategy metadata such as `high_value_only`,
  `max_items`, and `preferred_alert_types`
- connect scheduler job intent into console output rendering so the same alert
  set can produce a more opening-focused or closing-focused digest
- make scheduler status text display both output blocks and the intent label,
  helping future maintenance stay visible from the terminal
- extend regression coverage around preferred alert-type ordering and
  morning-vs-afternoon digest bias

Current effect:

- the scheduling layer now controls both output composition and digest
  prioritization, which is much closer to a real task-driven monitor workflow
- future new jobs can define their own summary emphasis without modifying the
  shared alert generation or report generation logic

Later on 2026-07-02, a concrete `midday-check` task was added as the first
real extension of the new scheduler strategy framework.

What this step focused on:

- add `midday-check` into the default scheduler job list with its own time slot
- define a midday-specific output profile that keeps universe observation,
  intraday digest, and detailed alerts, while skipping morning and close-only
  blocks
- define a midday-specific intent profile that prefers expansion-style alerts
  such as `sector_move`, `materials_focus`, and `news_flash`
- extend scheduler status text, scheduler registration, and manual preview
  support so `run-job-now midday-check` can simulate the new task directly
- extend scheduler and main-entry regression coverage around the new task

Current effect:

- the scheduler framework is no longer only theoretically extensible; it now
  has a third concrete task proving the strategy model works in practice
- future jobs such as `pre-open-check` or `tail-check` can follow the same
  pattern with much lower implementation risk

Later on 2026-07-02, the scheduler task system was documented for local
maintenance and VS Code browsing.

What this step focused on:

- add `TASK_PROFILES.md` as a human-readable guide for `manual`,
  `morning-check`, `midday-check`, and `afternoon-review`
- explain each task in terms of timing, output blocks, digest preference, and
  practical reading goal
- document the safest edit points for changing schedule time, output blocks, or
  alert emphasis independently
- update `README.md` so scheduler-task preview commands and the new task guide
  are visible from the main project entry document

Current effect:

- the task-strategy system is now easier to understand directly from the repo
  without reading scheduler or pipeline code first
- future manual maintenance in VS Code should be much lower-friction because
  task purpose, timing, and behavior are documented in one place

Later on 2026-07-02, the task-aware console header copy was differentiated by
job intent.

What this step focused on:

- add per-task `console_title` and `console_subtitle` fields inside the job
  intent strategy layer
- make manual runs keep the broader `AI Semiconductor Monitor Demo` framing
  while morning, midday, and afternoon tasks expose clearer operational titles
- let console output show a short `Focus:` line so the user can immediately
  understand whether the current task is for opening risk, midday expansion,
  or close-focused structure review
- extend scheduler, pipeline, and main-entry regression coverage around these
  task-specific headers

Current effect:

- task outputs are now easier to distinguish visually even before reading the
  detailed blocks below
- the scheduler strategy system now influences not only selection logic but
  also user-facing framing, which improves everyday readability in the
  terminal

Later on 2026-07-02, a new `pre-open-check` task was added to extend the
task chain into the pre-market preparation phase.

What this step focused on:

- add `pre-open-check` at `09:15` to the default scheduler jobs
- define a pre-open output profile that keeps the morning report and monitor
  universe observation while skipping intraday and close-oriented blocks
- define a pre-open intent profile centered on overnight news and risk scan,
  with a `news_flash` bias
- extend manual preview support so `run-job-now pre-open-check` simulates the
  new task directly
- update task documentation and README examples so the new task is visible from
  both code and docs

Current effect:

- the project now has task coverage for pre-open, early session, midday, and
  afternoon review phases
- the scheduler strategy framework now spans a more realistic research-day
  workflow instead of only intraday and close-oriented checkpoints

Later on 2026-07-02, task outputs gained a one-line result summary layer.

What this step focused on:

- add a `result_summary_style` field to each task intent profile
- derive one concise `Result:` line from alert severity, high-value signal
  counts, and task purpose
- let pre-open, morning, midday, afternoon, and full manual runs each use a
  different summary tone without changing their detailed blocks
- extend pipeline, scheduler, and main-entry regression coverage so the
  top-line result summary remains visible across task variants

Current effect:

- each task output now starts with a faster business conclusion before the
  detailed sections begin
- the terminal experience is more scan-friendly because users can judge risk,
  expansion quality, or close structure in one sentence first

Later on 2026-07-02, the new task result-summary layer was documented in the
task guide and main README.

What this step focused on:

- extend `TASK_PROFILES.md` with the current `Result:` summary style for each
  task profile
- update `README.md` so task readers can see the one-line conclusion behavior
  directly from the main project entry page
- keep documentation aligned with the now-expanded task chain from pre-open to
  afternoon review

Current effect:

- task purpose, output blocks, digest preference, and top-line result style are
  now all documented together
- VS Code browsing is a bit easier because users can understand each task’s
  conclusion pattern without reading pipeline code

Later on 2026-07-03, the task `Result:` summary wording was moved into the
report-rule config layer.

What this step focused on:

- add `task_result_summary_rules` to `app/report_rule_config.json`
- load those per-task, per-case templates through `app/sectors.py`
- keep the summary-case decision logic in `app/pipeline.py`, while moving the
  actual text templates out of the pipeline code
- extend rule-config documentation and add regression coverage for the new
  summary-rule family

Current effect:

- users can now change the top-line wording for pre-open, morning, midday,
  afternoon, and full manual runs without editing Python logic
- the business rule split is cleaner because threshold selection stays in code
  while phrasing stays in config

Later on 2026-07-03, task timing, task framing, and task summary thresholds
were pulled into a dedicated task-profile config layer.

What this step focused on:

- add `app/task_profile_config.json` as the new task configuration center
- move scheduled job times, output strategies, and intent strategies out of
  hardcoded scheduler constants and into that config file
- add configurable `task_result_summary_decision_rules` so each task's summary
  stage switching is now threshold-driven from config instead of hardcoded
  branches in the pipeline
- add `app/task_profiles.py` plus a field guide document so the task layer is
  easier to maintain from VS Code

Current effect:

- changing task time, title, digest emphasis, output blocks, or summary
  thresholds is now mostly a config edit instead of a scheduler/pipeline edit
- the task system is cleaner because code now focuses on execution while task
  behavior itself sits in a readable config boundary

Later on 2026-07-03, task overview display order and grouping also moved into
the task-profile config layer.

What this step focused on:

- add `task_display_groups` to `app/task_profile_config.json`
- let scheduler status output read task groups and task order from config
  instead of a hardcoded task list
- replace the stale hardcoded `run-scheduler` registered-job line with a
  config-driven summary builder
- document the new display-group field and extend scheduler/main regression
  coverage

Current effect:

- scheduler-facing task overviews now stay aligned with the real configured
  task chain
- future changes to task ordering or grouping can be made in config without
  editing scheduler display code

Later on 2026-07-03, the task-profile config layer gained cross-reference
validation.

What this step focused on:

- add startup-time validation for `app/task_profile_config.json`
- reject duplicate scheduled ids, duplicate display-group job ids, and display
  references to unknown jobs
- reject task intents that point to missing summary styles
- reject summary decision cases that do not have matching wording templates in
  `app/report_rule_config.json`

Current effect:

- task-profile editing is safer because broken references are caught at config
  load time instead of leaking into runtime behavior later
- the task config and the report-summary config are now explicitly kept in sync

Later on 2026-07-03, task-profile validation was also exposed as a dedicated
CLI command.

What this step focused on:

- add `python -m app.main validate-task-profiles`
- print a compact validation summary with source path, scheduled-job count,
  scheduled-job order, and configured display groups
- document the new command in the task-profile field guide and main README

Current effect:

- after editing the task-profile config, the user can now verify that layer
  directly without running the full scheduler or demo flow
- daily maintenance is a bit smoother because task config checks now have a
  single obvious entry command

Later on 2026-07-03, the task-profile validation output was expanded into a
more readable business summary.

What this step focused on:

- extend `validate-task-profiles` so it also prints active result-summary
  styles
- add explicit summary lines for manual preview jobs and scheduled day-flow
  jobs
- keep display-group detail rows while making the top-level validation result
  easier to scan

Current effect:

- one validation command now shows both "is the config valid?" and "what task
  structure is currently configured?"
- future task-profile edits are easier to sanity-check because the most
  important grouping and summary-style information is visible immediately

Later on 2026-07-03, the shared task-overview summary was unified across task
validation and scheduler status.

What this step focused on:

- move the task overview summary into reusable task-profile helpers
- let `validate-task-profiles` and `scheduler-status` read the same task
  overview block instead of assembling separate versions
- keep scheduler-specific output-profile rows separate, while making the top
  task chain summary identical across both command surfaces

Current effect:

- task validation and scheduler inspection now show the same overview of task
  count, task order, display groups, and summary-style coverage
- future task-overview edits are less likely to drift because there is now one
  shared summary source

Later on 2026-07-03, the `run-scheduler` startup flow was aligned with that
same shared task overview.

What this step focused on:

- show the shared `Task Overview` block at scheduler startup before the runtime
  status block
- remove the older one-line registered-job summary from the startup flow to
  reduce duplicate task-chain wording
- keep scheduler startup focused on one consistent sequence:
  task overview first, scheduler runtime state second

Current effect:

- the three task-facing entry points now present a more consistent first-read
  task view:
  `validate-task-profiles`, `scheduler-status`, and `run-scheduler`
- scheduler startup is a bit cleaner because the user sees the whole task chain
  once instead of a full overview plus a redundant short summary

Later on 2026-07-03, the shared task-overview block itself gained a dedicated
replaceable display layer.

What this step focused on:

- add `task_overview_display` to `app/task_profile_config.json`
- make overview heading, field order, and field labels configurable
- validate overview field keys so display customization stays inside the
  supported summary schema

Current effect:

- the task system now has a clearer three-layer separation for the overview
  surface:
  task data, task behavior, and task-overview presentation
- future wording or ordering changes in the task overview can now happen in
  config instead of code

Later on 2026-07-03, the shared `Output profiles` block also moved into a
replaceable display layer.

What this step focused on:

- add `output_profiles_display` to `app/task_profile_config.json`
- make the output-profile section title, enabled-block labels, and intent-line
  prefix configurable
- move the scheduler status output-profile rendering onto a shared builder
- validate output-profile block keys so display customization stays aligned
  with the supported output-strategy schema

Current effect:

- both major task-facing summary blocks are now on configurable presentation
  layers:
  `Task Overview` and `Output profiles`
- future wording changes in scheduler output-profile summaries can now happen
  in config without changing scheduler rendering code

Later on 2026-07-03, the project returned to the monitoring business mainline
with a compact market-focus snapshot block.

What this step focused on:

- add a `Market Focus Snapshot` block to task outputs
- summarize strongest sector, second sector, top focus stocks, top-sector
  average move, and alert mix in one compact read block
- connect that block into task output strategies and the shared
  `Output profiles` display labels

Current effect:

- pre-open, morning, midday, afternoon, and manual task outputs now expose a
  faster business read on the current market structure before the longer report
  sections
- the project moved back from framework-only refinement to a more directly
  useful monitoring feature for day-to-day research reading

Later on 2026-07-03, that market-focus snapshot gained a more business-facing
main-line observation sentence.

What this step focused on:

- classify the current market focus into states such as breadth expansion,
  leader continuation, mixed rotation, quiet rotation, or divergence risk
- translate that state into one short observation sentence instead of leaving
  only a raw state label
- keep the rule explicit and threshold-based so future wording or threshold
  tuning stays explainable

Current effect:

- the snapshot now answers not only "who is strongest?" but also "is the main
  line expanding, concentrated, mixed, or showing divergence risk?"
- task output is closer to a practical readout you can use directly during
  research monitoring instead of only a descriptive data summary

Later on 2026-07-03, the market-focus observation was tightened further around
the business main line of materials, gas, and equipment chain structure.

What this step focused on:

- make the observation sentence distinguish between internal expansion inside
  the materials-gas chain and early spread from that chain into equipment
- add a clearer "still concentrated" wording when materials lead strongly but
  broader chain follow-through is still weak
- keep the rule layer explicit so the wording remains easy to adjust without
  touching the main monitoring flow

Current effect:

- the snapshot wording is now closer to the actual daily business question of
  whether strength is staying inside one chain segment or beginning to spread
  into another
- each run gives a faster read on chain-level structure instead of only generic
  sector-to-sector expansion wording

Later on 2026-07-03, the market-focus state and observation rules were moved
into shared config instead of staying embedded in the pipeline logic.

What this step focused on:

- move market-focus state thresholds such as breadth expansion, leader
  continuation, and mixed rotation into `app/report_rule_config.json`
- move state-specific observation wording into the same config-driven rule layer
- keep pipeline code focused on evaluating and applying rules instead of owning
  business thresholds directly

Current effect:

- future threshold tuning and wording replacement for the market-focus snapshot
  can now happen from config with much lower risk to the main monitor flow
- the project stays closer to the explicit-rule architecture required in phase
  one while making daily business iteration faster

Later on 2026-07-03, the project consolidated high-value alert types into one
shared rule source instead of letting pipeline and notifier logic define them
separately.

What this step focused on:

- move the shared high-value alert-type list and alert-type priority map into
  `app/report_rule_config.json`
- load those rules through `app/sectors.py` so pipeline and notifier behavior
  can reuse the same business definition
- add a regression test to confirm market-focus alert-mix counts do not start
  treating ordinary spike alerts as high-value signals

Current effect:

- `Market Focus Snapshot`, task-result summary logic, and digest selection are
  now closer to one consistent signal hierarchy
- future signal-priority tuning can happen with less risk of hidden divergence
  between different output layers

Later on 2026-07-03, scheduler task digest preferences were refactored to use
shared alert-type bundles instead of repeating raw alert-type lists in each
task block.

What this step focused on:

- add reusable alert-type bundles to `app/task_profile_config.json`
- let `app/task_profiles.py` validate bundle references and resolve them into
  explicit `preferred_alert_types` during config loading
- keep backward compatibility so direct `preferred_alert_types` still work if
  needed in future local experiments

Current effect:

- pre-open, morning, midday, and afternoon task intent strategies now share
  reusable signal-package definitions instead of duplicating the same arrays
- future tuning of stage-specific signal focus can happen in fewer places with
  lower risk of one task drifting away from the others

Later on 2026-07-03, each task stage gained an explicit business-facing focus
label set and strategy note so the scheduler config now reads more like an
operating playbook.

What this step focused on:

- add `focus_tags` and `strategy_note` to each task intent strategy in
  `app/task_profile_config.json`
- surface those labels in the shared scheduler output-profile summary instead
  of leaving the stage meaning implicit inside titles only
- keep the layer descriptive and non-invasive so no task execution behavior had
  to change

Current effect:

- task configuration is now easier to read as a business workflow, especially
  when reviewing what pre-open, morning, midday, and afternoon checks are each
  supposed to watch
- future stage tuning can happen with clearer intent, reducing the chance of
  output behavior and business purpose drifting apart

Later on 2026-07-03, task-stage intent was linked directly to stock-pool chain
coverage so each stage now carries an explicit default chain view instead of
only a text explanation.

What this step focused on:

- add reusable chain-group bundles to `app/task_profile_config.json`
- resolve those bundles into `preferred_chain_groups` in
  `app/task_profiles.py`
- show a stage-specific chain-focus snapshot inside monitor-universe output so
  each task can compare its intended chain focus with current stock-pool
  coverage

Current effect:

- pre-open, morning, midday, and afternoon stages now have a clearer default
  chain perspective tied to the stock-pool structure
- stock-pool observation is becoming more actionable because it now shows not
  only general structure but also whether the current stage focus is well
  covered by the monitor pool

Later on 2026-07-03, stage chain focus stopped being a static configured list
and began prioritizing the currently strongest-covered preferred chains first.

What this step focused on:

- rank each stage's preferred chain groups by live stock-pool coverage count
- keep configured order only as the tiebreaker so weakly covered chains no
  longer appear ahead of stronger matches
- add regression tests for ranked stage-chain output and coverage-gap handling

Current effect:

- stage-specific stock-pool observation now surfaces the most relevant matching
  chains earlier instead of only echoing bundle order
- the monitor output is closer to a practical decision view because stage
  alignment is now weighted by actual pool structure, not just static intent

Later on 2026-07-04, the market-focus observation itself began referencing the
current stage's strongest aligned chain instead of leaving stage alignment only
inside the separate stock-pool observation block.

What this step focused on:

- let `Market Focus Snapshot` read the current task stage's preferred chain
  groups through the intent strategy
- derive one short stage-aware suffix from live aligned-chain strength
- keep the addition lightweight so the original expansion/concentration logic
  still stays readable and explainable

Current effect:

- the market-focus observation now answers not only "what is the market doing?"
  but also "which aligned chain matters most for this stage right now?"
- stage perspective is becoming visible earlier in the output, which should
  make the snapshot more useful as a first-read business summary

Later on 2026-07-04, the task-result top line began inheriting the current
stage's aligned-chain summary instead of leaving that signal only inside the
lower snapshot blocks.

What this step focused on:

- append a compact `Aligned chain` suffix to the `Result:` summary when the
  current task stage has a clear preferred chain and live strength reading
- reuse the existing aligned-chain ranking and signal-confirmation logic so the
  top-line summary stays consistent with the snapshot layer
- keep the addition short so the task-result sentence remains readable as a
  quick scan

Current effect:

- the first business sentence in each task output is now closer to the actual
  stage main line instead of only reporting generic alert-state wording
- users can recognize the most relevant aligned chain earlier without needing
  to scroll into the market-focus block first

Later on 2026-07-04, stage-aligned chain preference was also pushed into the
alert digest selection path so the summary stack now follows one consistent
business main line.

What this step focused on:

- let digest sorting recognize whether an alert text aligns with the current
  task stage's preferred chain groups
- pass `preferred_chain_groups` from the task intent strategy into both
  intraday and close digest strategies inside the pipeline
- extend notifier and pipeline regression coverage so stage chain focus affects
  digest ordering in a controlled way

Current effect:

- `Result:`, `Market Focus Snapshot`, `Monitor Universe Observation`, and the
  alert digests now align more closely around the same stage-focused chain
  perspective
- when two alerts are otherwise similar, the digest is now more likely to show
  the stage-relevant chain signal first instead of only relying on generic
  alert-type priority

Later on 2026-07-04, the detailed alert block also began surfacing stage-chain
alignment so the lower-level readout stays consistent with the summary layers.

What this step focused on:

- pass the current task intent strategy into detailed alert rendering
- add a `Stage alignment` line to each detailed alert block
- reuse the existing chain-group match and live-strength ranking logic instead
  of inventing a second alignment rule set

Current effect:

- users can now see whether a single detailed alert is aligned with the
  current stage focus without mentally comparing it against the upper summary
  sections
- the project is closer to one unified business narrative from top-line result
  down to per-alert detail

Later on 2026-07-04, the detailed-alert stage-alignment wording was moved onto
the shared report-rule config layer instead of staying embedded in the
pipeline.

What this step focused on:

- add `stage_alignment_templates` to `app/report_rule_config.json`
- load those templates through `app/sectors.py`
- let `app/pipeline.py` render detailed-alert alignment text from config
  instead of fixed strings

Current effect:

- changing detailed-alert alignment wording now follows the same maintenance
  pattern already used by market-focus observation and task-result summary
- the project is more consistent because business phrasing continues to move
  out of core pipeline logic and into editable configuration

Later on 2026-07-04, the detailed-alert block itself also gained a configurable
field-order and label layer.

What this step focused on:

- add `detailed_alert_display` to `app/report_rule_config.json`
- let `app/pipeline.py` render detailed-alert rows from configured field
  metadata instead of a hardcoded line list
- document the supported field keys and add regression checks for config
  loading plus rendered output

Current effect:

- changing detailed-alert line order, labels, and the raw-vs-labeled display
  style is now a config edit instead of a pipeline edit
- the alert-detail surface is now closer to the same replaceable-display model
  already used in other report and dashboard areas

Later on 2026-07-04, the market-focus and monitor-universe terminal blocks
also moved closer to that same replaceable display model.

What this step focused on:

- add `market_focus_snapshot_display` and `monitor_universe_display` to
  `app/report_rule_config.json`
- let `app/pipeline.py` render those block titles, field order, and labels
  from shared display metadata instead of fixed line lists
- add config-loading coverage so those new display layers stay visible to
  regression tests

Current effect:

- the main terminal summary surfaces now share a more consistent editable
  display architecture
- future wording and ordering changes for market-focus and stage-chain summary
  blocks can happen with less risk to the underlying business logic

Later on 2026-07-04, those display-layer field specs also gained explicit
enable/disable support.

What this step focused on:

- add `enabled` flags to the configurable field specs for detailed alerts,
  market-focus snapshot, and monitor-universe stage-chain fields
- let the shared display-field renderer skip disabled items cleanly
- extend regression coverage so hidden fields stay suppressed when the display
  config says they should be

Current effect:

- future terminal-output tuning can now hide low-priority lines directly from
  config instead of forcing line deletion or pipeline edits
- the display layer is more maintainable because field order, labels, and
  visibility now live in the same metadata structure

Later on 2026-07-04, the top console overview lines also moved onto that same
shared display-metadata path.

What this step focused on:

- add `console_overview_display` to `app/report_rule_config.json`
- let `app/pipeline.py` render `Focus`, `Result`, environment, database, quote
  source, and stock-count lines from the shared display-field renderer
- add config-loading coverage for the new top-overview display family

Current effect:

- the terminal reading path from the top title downward is now more uniform
  because the overview rows use the same configurable field model as the lower
  snapshot and alert blocks
- future top-line layout changes can happen from config with less risk to the
  business logic

Later on 2026-07-04, the default console layout was also tuned toward a more
research-first reading order instead of a runtime-diagnostics-first order.

What this step focused on:

- move `Result` ahead of `Focus` in the default top overview
- move `Observation` ahead of raw market-state labeling in the default market
  snapshot
- move `Live strength` ahead of pool-coverage detail in the default stage-chain
  block
- hide low-priority runtime fields such as environment and database from the
  default top console overview while still keeping them configurable

Current effect:

- the first screen of terminal output is now closer to the actual business
  reading path: conclusion first, then focus, then market structure, then pool
  alignment
- the system keeps runtime-detail flexibility, but the default view now serves
  research monitoring better than before

Later on 2026-07-04, the detailed alert area was further tuned so that the
default reading order favors higher-value and stage-relevant signals first.

What this step focused on:

- sort detailed alerts with stage-relevant and high-value items ahead of lower
  priority watch items
- expose alert priority labels through config so titles can distinguish
  `High-Value` and `Watch`
- repair old pipeline/test text corruption that had started to affect parsing
  and test stability

Current effect:

- the detailed alert block now surfaces the most decision-useful signals first
- alert title wording can be changed from config without touching core logic
- the pipeline/test baseline is back to a stable, fully passing state

Later on 2026-07-04, the detailed alert display layer was extended one step
further so field groups can differ by alert priority.

What this step focused on:

- add config-level `field_sets` for detailed alerts so `high_value` and `watch`
  alerts can use different field combinations and order
- add `block_title` and `empty_message` entries to complete the detailed alert
  display rule family
- cover the new rule path with pipeline/report tests

Current effect:

- higher-value alerts can stay information-rich while routine watch alerts can
  remain lighter and easier to scan
- future alert-card style changes are more isolated in config and less likely to
  disturb the main monitor flow

Later on 2026-07-04, the detailed alert layer was closed into a full
task-controllable section instead of only a per-alert card renderer.

What this step focused on:

- render the configured detailed-alert `block_title` and `empty_message`
- make the task-level `include_detailed_alerts` switch behave as a true
  whole-section on/off control
- add regression coverage for both the empty-state section and the task-level
  hide behavior

Current effect:

- detailed alerts now behave more like one complete configurable output block
  and less like an internal loop of alert cards
- future task profiles can decide more cleanly whether a stage should show
  detailed alerts at all, while still reusing the same section rules when it
  does

Later on 2026-07-04, task-specific detailed-alert style variants were added so
different monitor stages can present the same alert stream differently.

What this step focused on:

- add configurable detailed-alert `style_variants` such as opening-focused,
  mid-session, and close-review presentations
- let task intent strategies choose a `detailed_alert_style_variant`
- keep the variant layer strictly presentational so alert ranking and business
  signal logic remain unchanged

Current effect:

- morning, midday, and afternoon tasks can now point to different detailed
  alert titles and field layouts without forking pipeline logic
- the project is closer to a stable separation between business monitoring
  logic and stage-specific reading experience

Later on 2026-07-04, that task-specific style idea was extended into a more
generic shared `display_variant` mechanism across multiple output blocks.

What this step focused on:

- let task intent strategies define one shared `display_variant`
- extend market-focus and monitor-universe display configs with their own
  variant maps
- make pipeline rendering resolve block titles and field lists through the same
  variant-selection path already used by detailed alerts

Current effect:

- the project now has one clearer path for stage-specific reading style across
  multiple summary blocks instead of only the detailed-alert area
- future work on “opening / mid-session / close-review” reading experiences can
  move faster because more blocks now share the same variant concept

Later on 2026-07-04, the top console overview was also brought into that same
shared `display_variant` system.

What this step focused on:

- extend `console_overview_display` with style variants
- let task-level `display_variant` affect the top summary rows as well as the
  lower market-focus, universe, and detailed-alert blocks
- keep manual default output stable while making scheduled task views more
  stage-specific

Current effect:

- the project now has a broader end-to-end display-variant path from the top
  overview down into the main summary blocks
- opening, mid-session, and close-oriented task views are closer to becoming a
  coherent full-page reading experience instead of a set of independently tuned
  sections

Later on 2026-07-04, those stage-specific reading modes were lifted again into
named reusable task view templates.

What this step focused on:

- add `view_templates` to the task-profile config
- let job output strategies inherit block on/off composition from a reusable
  template
- let job intent strategies inherit stage-view display settings from the same
  template
- surface the chosen view template in task-profile validation output

Current effect:

- opening, pre-open, mid-session, close-review, and manual flows now have a
  cleaner path for sharing full reading-mode presets
- future task-view changes can happen at the template layer instead of repeating
  the same edits across multiple jobs

Later on 2026-07-04, those reusable task view templates were given readable
labels and short summaries in the user-facing terminal output.

What this step focused on:

- add `label` and `summary` metadata to `view_templates`
- show `view-mode` and `view-summary` in scheduler status / task-profile
  validation output
- prepend the same view-mode hint to `run-job-now` style console output so each
  task run explains its current reading mode up front

Current effect:

- the same underlying template system is now easier to understand without
  opening config files
- future template swaps remain low-risk because operators can immediately see
  which reading mode a task is using

Later on 2026-07-05, the project docs were updated so the task view-template
layer is understandable from README-level and operator-level documentation.

What this step focused on:

- explain `view-mode`, `view-summary`, and `view_template` in `README.md`
- expand `TASK_PROFILES.md` with current view templates, current job-to-template
  mapping, and a faster "change what / edit where" guide
- make the task profile document more useful as an operating manual instead of
  only a config inventory

Current effect:

- future task-layout changes are easier to reason about before editing config
- operators can now tell whether they need to edit a shared view template, a
  job strategy, or a summary threshold rule without reading code first

Later on 2026-07-05, the scheduler task config itself was made more
business-readable without renaming the stable underlying task ids.

What this step focused on:

- add optional `label` and `summary` fields to scheduled task config entries
- surface those readable names in task overview and output-profile summaries
- document the difference between stable task ids and business-facing display
  names in the config guide

Current effect:

- scheduler configuration is easier to scan without guessing what each task id
  means
- future naming cleanup can continue from the metadata layer first, instead of
  forcing risky key renames across code and tests

Later on 2026-07-05, reusable alert bundles and chain-focus bundles were also
given readable business metadata and surfaced in scheduler-facing summaries.

What this step focused on:

- support metadata-rich `alert_type_bundles` entries with `label`, `summary`,
  and `items`
- add sidecar `chain_group_bundle_meta` so chain bundles can stay stable even
  when raw chain names are messy or legacy-encoded
- show readable alert-bundle and chain-bundle names in output-profile summaries

Current effect:

- task profile summaries now explain not only which task is running, but also
  which alert emphasis bundle and chain-focus bundle it is using
- future bundle cleanup can continue without forcing immediate rewrites of the
  underlying alert-type or chain-group lists

Later on 2026-07-05, the task-profile configuration stack was summarized again
as one dedicated cross-layer relation map.

What this step focused on:

- add `TASK_PROFILE_RELATION_MAP.md`
- explain the dependency path from scheduled task -> view template -> bundle ->
  summary rule -> final wording
- give one fast edit guide for deciding which config layer should be touched
  first

Current effect:

- future task changes can start from one relationship map instead of reading
  several separate documents
- the project is less likely to drift off the business mainline because config
  responsibilities are now easier to inspect before editing

Later on 2026-07-05, the business output moved one step closer to next-session
selection support by adding a rule-based watchlist / trim-list summary to the
evening review.

What this step focused on:

- add explicit helpers for `next-session watchlist` and `same-day trim list`
- derive those lists from strongest sectors, secondary sectors, fading sectors,
  and risk-alert related stocks
- append the resulting action summary under the existing evening-report
  "tomorrow plan" section

Current effect:

- the evening review now ends with a more actionable next-session handoff
  instead of only a general strategy sentence
- future stock selection /复盘 enhancements can build on an existing structured
  shortlist layer instead of starting from free-form report text
Later on 2026-07-05, that next-session handoff was refined again from a
two-part watch/trim output into a three-tier structure.

What this step focused on:

- split the action layer into `core watchlist`, `candidate watchlist`, and
  `avoid list`
- keep the rules explicit: strongest sector leads core names, secondary
  confirmation leads candidate names, and risk/fading signals lead avoid names
- preserve the same evening-review entry point while making the output more
  usable for next-day screening

Current effect:

- the evening review now supports a more realistic next-day decision flow than
  a single undifferentiated watchlist
- future ranking or scoring work can attach to the three existing tiers instead
  of reworking the whole report shape again

Later on 2026-07-05, those three tiers were given explicit stock-level reason
tags so the shortlist became easier to audit.

What this step focused on:

- add tag lines for `core watchlist`, `candidate watchlist`, and `avoid list`
- keep tags readable and rule-based, such as `mainline`, `strength`,
  `follow-through`, `liquidity`, `risk-alert`, and `fading-sector`
- preserve the existing evening-report structure while increasing traceability

Current effect:

- the next-session shortlist now explains not only which stocks are in each
  tier, but also why they were placed there
- future score-based ranking can build on the existing reason-tag layer instead
  of replacing the shortlist format from scratch

Later on 2026-07-05, that reason-tag layer was extended into a lightweight
explicit score layer and the tier ordering began following those scores.

What this step focused on:

- derive transparent per-stock scores directly from visible reason tags instead
  of introducing opaque heuristics
- show `Core scores`, `Candidate scores`, and `Avoid scores` in the evening
  review handoff block
- keep each tier's displayed stock order aligned with the same explicit score
  output so list order, tags, and scores tell one consistent story

Current effect:

- the next-session handoff is now more decision-friendly because users can see
  both the shortlist and the relative conviction inside each tier
- future refinement can adjust rule weights in one place without redesigning
  the report structure again

Later on 2026-07-05, those reason-score weights were moved out of report logic
and into the shared report-rule config layer.

What this step focused on:

- add `reason_score_weights` to `app/report_rule_config.json`
- load those weights through `app/sectors.py` like the project's other shared
  report rules
- keep evening-review score output and tier ordering driven by that shared
  config instead of hardcoded weights inside `context_rules.py`

Current effect:

- future score tuning can now happen from configuration without editing the
  shortlist logic itself
- the next-session handoff is more maintainable because score wording,
  weights, and ordering are now aligned with the project's broader
  configuration-first rule style

Later on 2026-07-05, the evening review also began surfacing a compact summary
of the current score rules directly above the three shortlist tiers.

What this step focused on:

- add short `Score rules` and `Fallback / Avoid rules` lines into the
  next-session action block
- keep the summary lightweight so users can confirm the current weighting model
  without leaving the report
- preserve the main reading order by placing rule summary immediately before
  the core / candidate / avoid lists

Current effect:

- each evening review now explains both "which stocks are selected" and "which
  weighting rules are currently active" in the same place
- future weight edits from config are easier to audit because the live report
  now echoes the current score model

Later on 2026-07-05, that rule summary was refined again so the displayed score
items use readable business-facing labels instead of internal tag keys.

What this step focused on:

- add `reason_score_labels` to the shared report-rule config
- load those labels through the same shared rule path as score weights
- let the evening-review rule summary render `Main line`, `Strong move`,
  `Risk alert`, and similar readable names instead of raw internal keys

Current effect:

- the next-session handoff is easier to read in the terminal because the rule
  summary now looks closer to business language than implementation language
- future naming cleanup can continue from config without changing shortlist or
  score logic

Later on 2026-07-11, the evening-review next-session handoff was also split
into a reusable structured summary builder plus a separate render step.

What this step focused on:

- add a structured `build_next_session_action_summary(...)` layer that returns
  reusable rule-summary and tier data instead of only prebuilt strings
- keep `build_next_session_action_lines(...)` as a compatibility wrapper so
  existing callers remain stable
- let `build_evening_report(...)` accept either legacy line lists or the new
  structured `next_session_action_summary`

Current effect:

- the next-session handoff is now easier to reuse across evening review,
  historical views, terminal output, and future dashboard surfaces
- future shortlist changes can happen in one summary-builder layer instead of
  being repeated in each output format

Later on 2026-07-11, that same structured next-session handoff was connected
into the historical review path as well.

What this step focused on:

- let `build_history_summary(...)` derive strongest / secondary / fading sector
  context from the selected historical snapshot batch
- reuse `build_next_session_action_summary(...)` and
  `render_next_session_action_summary_lines(...)` inside history review instead
  of building a second review rule path
- keep the existing lightweight history header while appending the same
  next-session action summary block used by the evening review

Current effect:

- historical batch review now shows the same three-tier shortlist structure as
  the main evening handoff
- future strategy-summary changes can flow into both evening review and history
  review through one shared summary-builder layer

Later on 2026-07-11, the dashboard also began reading the same structured
next-session action summary as its own reusable grouped panel.

What this step focused on:

- extend `app/dashboard/overview.py` so dashboard payloads include a
  `next_session_action_summary` derived from the selected snapshot batch
- add a dedicated dashboard content section and grouped render path for that
  summary instead of introducing a second strategy-specific rule engine
- keep the dashboard panel aligned with the same rule-summary and
  core/candidate/avoid structure already used by evening review and history
  review

Current effect:

- terminal review, historical review, and dashboard view now share the same
  next-session strategy structure
- future shortlist/rule changes can propagate across all three surfaces from
  one summary-builder layer instead of drifting apart

Later on 2026-07-11, that dashboard next-session panel was also given a clearer
visual hierarchy without changing any business rules.

What this step focused on:

- make the dashboard badge summarize the total action-slot count together with
  the `Core / Candidate / Avoid` distribution
- add explicit per-section counts into the grouped panel titles such as
  `Core Watchlist (n)` and `Avoid List (n)`
- keep the optimization presentational so the underlying shortlist logic,
  scores, and rule summaries remain untouched

Current effect:

- the dashboard next-session panel is easier to scan at a glance because users
  can recognize the tier balance before reading each detail row
- future UI polish can keep building on the same grouped-summary structure
  rather than reworking the strategy data shape again

Later on 2026-07-11, those dashboard next-session hierarchy cues were also
moved one step closer to the presentation-config layer.

What this step focused on:

- add configurable section-title labels such as `Priority Core Watchlist`,
  `Secondary Candidate Watchlist`, and `Risk Avoid List`
- add a configurable badge template for the dashboard next-session panel's
  tier-balance summary
- keep the enhancement display-only so the strategy summary data shape and
  score logic remain unchanged

Current effect:

- the dashboard next-session panel now communicates the three tiers in more
  business-readable language
- future wording cleanup for that panel can continue from presentation
  metadata instead of editing the grouped-summary view-model logic again

Later on 2026-07-11, the dashboard next-session tier titles were also updated
to state explicitly that each tier is score-ranked.

What this step focused on:

- add `(Score-ranked)` wording to the configurable `Core / Candidate / Avoid`
  section titles in the dashboard presentation layer
- make the meaning of list order visible without requiring users to infer it
  from the score rows below

Current effect:

- the dashboard next-session panel now explains at a glance that tier order is
  itself meaningful, not just the membership list
- this improves scanability while keeping the same shortlist logic and score
  calculation underneath

Later on 2026-07-11, the dashboard next-session panel also compressed its rule
summary area into a shorter first-screen weight note.

What this step focused on:

- rename the dashboard rule-summary section to `Weight Summary`
- merge the two detailed rule lines into one compact dashboard-only summary row
- keep the underlying rule-summary data unchanged for evening review and
  history review while making the dashboard panel more space-efficient

Current effect:

- the dashboard next-session panel now gives more first-screen space to the
  `Core / Candidate / Avoid` tiers
- display-only compaction now differs by surface, while the shared summary
  builder and scoring rules remain the same underneath

Later on 2026-07-11, the dashboard next-session tiers also shortened their
reason lines into quicker dashboard-only focus copy.

What this step focused on:

- compress long `reason` sentences into short `focus` lines inside the
  dashboard `Core / Candidate / Avoid` rows
- keep the transformation display-only so evening review, history review, and
  the shared summary builder continue using the fuller original wording
- add regression checks for the compact focus wording

Current effect:

- the dashboard next-session panel is easier to scan because each tier now ends
  with one short actionable focus sentence
- business logic remains unchanged; only the dashboard presentation layer is
  more compact

Later on 2026-07-11, the dashboard next-session detail-row labels were also
pulled closer to the presentation-config layer.

What this step focused on:

- move the row labels for `names`, `tags`, `scores`, and `focus` into the
  `next_session_action` presentation metadata
- keep default wording unchanged while making label replacement safer for later
  UI wording cleanup
- add regression coverage proving the grouped row builder respects replaced
  labels

Current effect:

- future wording changes for the dashboard next-session detail rows can happen
  from config instead of editing the main Streamlit helper again
- the panel is now more internally consistent with the project's broader
  configuration-first dashboard direction

Later on 2026-07-11, the dashboard next-session focus-sentence compression
rules were also lifted into replaceable presentation templates.

What this step focused on:

- move the known dashboard-only focus sentence outputs into configurable
  templates for the current `stay with`, `use as confirmation`, and
  `reduce names tied to` patterns
- keep the current default English wording unchanged while making later
  Chinese wording or style replacement safer
- add regression coverage proving the grouped row builder respects replaced
  focus templates

Current effect:

- future dashboard wording changes for compact focus sentences can happen from
  presentation metadata instead of editing sentence-building logic again
- the next-session panel is now closer to a fully replaceable presentation
  layer while still preserving the same business shortlist rules underneath

Later on 2026-07-11, the dashboard next-session action panel also gained
copy-variant support for future business-facing Chinese wording.

What this step focused on:

- add `copy_variant` plus `copy_variants` metadata for the
  `next_session_action` panel
- keep the current default English wording unchanged while introducing a
  `business_cn` copy set for titles, row labels, badge text, and compact focus
  sentence templates
- add regression coverage proving the panel can resolve and render the Chinese
  business copy variant without affecting the default path

Current effect:

- the next-session action panel is now structurally ready for a cleaner
  Chinese business UI transition
- future wording work can switch more from presentation metadata and less from
  render-function edits, while the same shortlist logic remains underneath

Later on 2026-07-11, that copy-variant path was extended into two more core
dashboard blocks: `Stock Pool Health` and `Leader Summary`.

What this step focused on:

- add `copy_variant` plus `copy_variants` support to the health and leader
  summary sections
- let the health block switch not only field labels, but also status wording,
  risk wording, section titles, and badge/status-line templates
- let the leader block switch its metric label, detail title, and badge unit
  through the same presentation-first path

Current effect:

- the dashboard's Chinese business-copy direction is no longer isolated to the
  next-session action panel
- three core summary areas now share the same configurable copy-variant
  approach while preserving the same monitoring and shortlist logic underneath

Later on 2026-07-11, the same copy-variant path was extended again into
`Strongest Sector` and `Latest Alerts`.

What this step focused on:

- add `copy_variant` plus `copy_variants` metadata to the strongest-sector and
  latest-alert sections
- let the strongest-sector block switch summary metric wording and detail title
- let the latest-alert block switch badge unit, metric label, and detail title
  through the same presentation-first path

Current effect:

- the dashboard's main reading blocks now mostly share one consistent
  copy-variant mechanism
- one follow-up gap remains intentionally noted: some field-level prefixes such
  as the strongest-sector row prefix still live in display-field metadata and
  are not yet fully routed through the same copy-variant layer

Later on 2026-07-11, that remaining field-level wording gap was also reduced by
extending copy-variant handling into `display_fields`.

What this step focused on:

- let copy-variant resolution replace list-based `display_fields`, not only
  dict-like label groups
- connect strongest-sector field prefixes and latest-alert field labels into
  the same `business_cn` copy path
- add regression coverage for field-level replacement and for the strongest
  sector row prefix switching with the Chinese business variant

Current effect:

- the dashboard is closer to a full block-and-field-level copy-variant system
- one small implementation detail is now documented: display-field prefixes are
  normalized with trailing spaces trimmed, so rendered row text may appear as
  `prefix:value` rather than `prefix: value` unless spacing is handled
  separately later

Later on 2026-07-11, the saved-batch summary block was also brought into that
same copy-variant system.

What this step focused on:

- add `copy_variant` plus `copy_variants` support to `Saved Batches`
- make its badge unit, summary metric label, detail title, and timestamp field
  label switchable through the same presentation-first path
- add regression coverage confirming the saved-batch block now follows the same
  variant-resolution behavior as the other main dashboard content blocks

Current effect:

- the dashboard's main grouped-summary content blocks now share a broader and
  more consistent copy-variant mechanism
- the remaining wording cleanup work is now mostly about smaller shared surfaces
  and final polish, not about missing whole-block support

Later on 2026-07-11, that copy-variant work was finally connected into a real
dashboard view entry.

What this step focused on:

- add a `business_cn` dashboard view variant alongside `default` and `compact`
- let one view variant override content-section `copy_variant` values from the
  page-layout/render entry point instead of requiring manual spec edits
- localize the view-level app title, batch selector label, and database caption
  so the Chinese business mode feels like a real selectable dashboard view

Current effect:

- the dashboard now has a direct selectable Chinese business-facing view mode
- earlier copy-variant work has been promoted from "prepared in config" to
  "reachable from the UI flow", while keeping the default and compact views
  stable

Later on 2026-07-11, the dashboard view selector itself was also made more
business-readable.

What this step focused on:

- rename the top-level view choices from generic `Default / Compact /
  Business CN` wording into more intentional entry names
- add a theme-level `view_selector_label` so the dropdown prompt can also vary
  by view mode
- align the Chinese business view so both the chosen view label and the
  selector prompt feel native to that mode, not only the inner content blocks

Current effect:

- the view-switch entry now reads more like a product surface and less like a
  developer toggle
- the Chinese business dashboard path feels more cohesive from the very first
  selector interaction, not only after entering the page content

Later on 2026-07-11, the KPI top-card area was also connected into that same
Chinese business-view path.

What this step focused on:

- add a view-level `kpi_copy_variant` so KPI wording can switch from the chosen
  dashboard view entry instead of requiring manual spec edits
- localize the KPI card labels as well as the top KPI section body/supporting
  copy for the `business_cn` view
- extend render-path tests so KPI wording is now covered together with the
  content-block copy-variant flow

Current effect:

- the dashboard now reads more consistently in the Chinese business view from
  the top KPI area down into the grouped summary blocks
- the remaining UI work is now more about polish, naming cleanup, and optional
  presentation refinement than about missing major localization hooks

Later on 2026-07-12, the shared surface copy layer was also connected into the
same business-view path so the wrapper text around charts, summary cards, and
detail panels can switch together instead of staying partly English.

What this step focused on:

- add a view-level `surface_copy_variant` so shared wrapper copy can be swapped
  independently from the content payload copy itself
- localize the shared summary/content/metric-group style specs for the
  `business_cn` dashboard path
- thread that surface-level variant through the chart block, grouped-summary
  block, health-summary block, and metric-row wrapper render paths
- extend tests so the Chinese business view now verifies chart-support copy,
  summary-support copy, content-detail support copy, and metric-row labels

Current effect:

- card style, chart wrapper copy, KPI wrapper copy, and grouped content wrapper
  copy now behave like one configurable presentation system
- later visual adjustments can keep using style-spec variants instead of
  touching main business logic or data payload assembly

Later on 2026-07-12, the remaining shared body titles inside those wrapper
panels were also moved out of the render functions and into the same
replaceable presentation layer.

What this step focused on:

- remove hardcoded shared body titles such as `Health metrics`, `Summary
  metrics`, `Grouped detail rows`, and `Formatted content table` from the
  Streamlit render path
- extend the metric-group and content-panel style specs so those body texts can
  switch together with the chosen dashboard view
- cover the new behavior in tests so the Chinese business view now verifies the
  body-level wrapper copy as well, not only labels and supporting text

Current effect:

- the configurable dashboard presentation system now covers wrapper label,
  wrapper supporting copy, and wrapper body title together
- future renaming or style swaps for dashboard surface text can stay in
  presentation metadata without reopening render-path business code

Later on 2026-07-12, the panel-title labels themselves were also connected to
the replaceable dashboard style specs so label-level wording can switch with
the selected view instead of staying fixed in renderer helpers.

What this step focused on:

- move title-label words such as `chart`, `section`, `status`, `summary`,
  `content section`, `content details`, `kpi section`, and `kpi` into the
  existing presentation style specs
- thread those label fields into the chart header, section title, health
  status, KPI wrapper, grouped-summary wrapper, and content wrapper render
  helpers
- extend tests so the Chinese business view now covers label-level panel titles
  in addition to body text and supporting copy

Current effect:

- dashboard surface wording is now configurable at three layers together:
  label, body title, and supporting copy
- future business-view naming adjustments can stay focused in presentation
  metadata with less risk of reopening shared rendering behavior

Later on 2026-07-12, the actual business section titles shown on the dashboard
surface were also moved into the same replaceable view-spec path so column and
module names no longer stay English in the Chinese business view.

What this step focused on:

- add replaceable title variants for chart specs such as `Sector Strength` and
  `Top Movers`
- add replaceable title variants for content specs such as `Strongest Sector`,
  `Stock Pool Health`, `Leader Summary`, `Latest Alerts`, `Saved Batches`, and
  `Next-session Action Summary`
- extend the spec-variant resolver so it can override both nested metadata
  fields and simple scalar fields like `title` and `empty_message`
- connect chart render paths to the same copy-variant mechanism already used by
  content sections

Current effect:

- the Chinese business view can now switch visible module titles together with
  wrapper labels, body text, and supporting copy
- dashboard presentation metadata now controls most user-facing wording on the
  page without reopening business logic or render flow internals

Later on 2026-07-12, chart companion-table headers and chart axis descriptions
were also connected into the replaceable presentation layer so the chart area
no longer keeps English table labels or unlabeled axes in the business view.

What this step focused on:

- add Chinese chart-specific display-field variants for the `sector_strength`
  and `top_movers` chart specs
- add replaceable `x_axis_label` and `y_axis_label` fields plus shared axis
  wrapper copy (`axes`, `X`, `Y` / `坐标`, `横轴`, `纵轴`)
- render a shared axis-description panel in chart blocks so chart dimensions are
  visible in business language without changing underlying data keys
- extend the spec-variant resolver use in chart rendering so chart titles,
  empty-state copy, table headers, and axis labels all switch through the same
  copy-variant path

Current effect:

- the chart area now switches titles, support copy, table headers, and axis
  descriptions together in the Chinese business view
- remaining dashboard wording work is now mostly optional polish rather than a
  missing localization structure problem

Later on 2026-07-12, the console notifier wording layer was also cleaned up so
alert priority copy and chain-group alias matching no longer rely on legacy
garbled strings.

What this step focused on:

- rewrite notifier alert-level labels into stable wording (`高优先级` /
  `中优先级` / `低优先级` / `观察级`)
- replace legacy garbled chain-group aliases with readable business names such
  as `材料` / `气体` / `设备` / `光模块` / `服务器` / `存储` / `封测`
- refresh `tests/test_notifier.py` so example alert payloads are readable
  Chinese business samples rather than old broken-encoding fixtures

Current effect:

- console notifications and digest-selection tests are now much easier to read
  and maintain
- dashboard and notifier surfaces are both moving toward one consistent
  business-language baseline instead of mixing readable and historical-encoding
  text

Later on 2026-07-12, the stock-pool comparison follow-up moved into test
stabilization because several legacy test files still contained broken
encoding and unterminated string literals that blocked even basic regression
execution.

What this step focused on:

- continue normalizing `tests/test_stock_pool.py` fixture rows and assertions
  into stable Chinese business strings expressed with `\uXXXX` escapes
- continue normalizing `tests/test_dashboard_streamlit.py` comparison fixtures,
  labels, and structure-summary assertions so they match the current
  stock-pool comparison wording
- use repeated `py_compile` checkpoints to identify the next real syntax
  blocker instead of changing test files blindly

Current effect:

- the compile blockers have been pushed much further back in both test files,
  confirming the earlier comparison-copy refactor is not the only issue
- the remaining work is now mostly systematic cleanup of legacy corrupted test
  fixtures rather than new uncertainty in the core business logic

Later on 2026-07-12, the test-repair work crossed an important threshold:
the four core regression files for stock-pool validation, dashboard payload,
Streamlit rendering, and CLI output were all brought back to a state where
they can be compiled together again, and nearly all business assertions were
realigned with the current Chinese wording baseline.

What this step focused on:

- finish repairing `tests/test_dashboard.py` and `tests/test_main.py` legacy
  corrupted fixtures and CLI expectation strings
- move from syntax recovery into assertion alignment, updating expectations to
  match current structure-summary wording, comparison-tag grouping, and
  business-CN UI copy
- verify the repaired tests by running the four main unittest modules together

Current effect:

- the project has moved from "tests blocked by broken source text" to "tests
  exercising real business behavior again"
- only a single residual assertion mismatch remained at the last checkpoint,
  indicating the test suite is now very close to a clean pass on this path

Later on 2026-07-12, the business-report path was pushed one step closer to the
real monitoring workflow by extending stock-pool observation output beyond
structure summary and grouped tags.

What this step focused on:

- extend the shared report observation builder so it can also render one
  comparison highlight line and a compact top change-row summary
- thread those new fields through both `build_morning_report(...)` and
  `build_evening_report(...)`, including the database-backed report builders
- repair and stabilize `tests/test_reports.py` around this new behavior so the
  report path now validates the richer stock-pool structure narrative

Current effect:

- morning and evening reports now surface not only "how the stock pool looks"
  but also "what changed versus the last structure baseline"
- the report layer is now better aligned with the dashboard and CLI validation
  path around stock-pool comparison semantics
- a broader regression run covering reports, stock-pool validation, dashboard,
  Streamlit, and CLI completed successfully

Later on 2026-07-12, the same stock-pool comparison narrative was extended one
step further into the historical terminal review path.

What this step focused on:

- rebuild `app/history.py` so `build_history_summary(...)` now includes a
  stock-pool observation section in addition to snapshot count, alert count,
  strongest sector, and next-session action lines
- reuse the same stock-pool health summary + comparison helpers already shared
  by dashboard, validation CLI, and report builders
- add regression coverage so both direct `print_history_review(...)` output and
  the history helper path verify the presence of stock-pool structure
  observation content

Current effect:

- `history-review` is now much closer to `latest-review`, morning report, and
  evening report in the way it explains stock-pool structure state and recent
  structural drift
- report, dashboard, validation CLI, and history review now all reuse the same
  stock-pool comparison vocabulary instead of diverging by surface

Later on 2026-07-14, the same stock-pool structure drift signal was promoted
into the very top `Result:` summary of each monitor-cycle console run so the
user can see structure bias immediately without opening the full report body.

What this step focused on:

- extend `MonitorCycleResult` so the monitor pipeline now carries explicit
  stock-pool structure summary, comparison highlight, tag labels, and health
  hints as first-class fields instead of relying only on downstream text
- thread `stock_pool_comparison_highlight_summary` through the pipeline morning
  and evening context builders so summary, report body, and future surfaces can
  share the same comparison payload consistently
- add a compact top-line suffix rule in `app/pipeline.py` that appends one
  stock-pool drift conclusion such as "awaiting first baseline", "stable vs
  baseline", or a direct highlight summary into the `Result:` line
- verify the change with targeted `tests.test_pipeline` and `tests.test_main`
  regression runs using the workspace Python runtime

Current effect:

- every normal monitor-cycle console output now exposes stock-pool structure
  drift at the first result glance, which keeps the business main line more
  visible during repeated local runs
- the monitor pipeline now owns this structure-drift data explicitly, making it
  easier to reuse in later task views, notifications, and dashboard summaries

Later on 2026-07-14, the same stock-pool structure drift conclusion was pushed
one step further into the alert-notification path so intraday and close digests
can surface the latest pool-bias change directly inside the concise alert text.

What this step focused on:

- extend `app.alerts.alert_rules._attach_stock_pool_context(...)` so high-value
  alerts now carry `stock_pool_comparison_highlight_summary` in addition to the
  existing structure summary, grouped tags, and health hints
- update `app.alerts.notifier` so full alert messages render the structure
  highlight line, and digest rows prefer that highlight summary before falling
  back to grouped comparison tags
- add focused regression coverage in `tests.test_alert_rules` and
  `tests.test_notifier` for both context attachment and digest rendering order

Current effect:

- intraday and close alert digests now explain not only that an alert happened,
  but also the most important stock-pool structure change attached to that
  cycle when such context exists
- notification, report, history, dashboard, and top-line result summary are now
  more aligned around one shared "structure drift first" vocabulary

Later on 2026-07-14, the same stock-pool drift cue was extended into the
database-backed review entrypoints so latest-review and history-review begin
with one compact structure-drift sentence before the full body unfolds.

What this step focused on:

- add `build_stock_pool_drift_summary_text(...)` into `app.reports.shared` as a
  reusable priority rule: prefer structure highlight, then grouped drift, then
  plain structure status
- update `app.main` so `print_latest_database_review(...)` and
  `print_latest_database_morning_review(...)` prepend that shared drift cue
  above the database-backed morning/evening report bodies
- update `app.history.build_history_summary(...)` so historical batch review now
  includes the same drift cue near the top of the summary, right after the
  timestamp line
- verify the behavior with focused regressions in `tests.test_main`,
  `tests.test_history`, and `tests.test_reports`

Current effect:

- latest morning review, latest close review, and history review now share the
  same fast first-glance stock-pool drift header style as the console run and
  alert digest paths
- the project now has a single reusable stock-pool drift summary helper that
  can be reused later in dashboard cards, CLI banners, or webhook summaries

Later on 2026-07-14, the same stock-pool drift sentence was promoted into the
dashboard first-screen KPI area so the homepage now exposes structure bias
without requiring the user to open the deeper stock-pool health block.

What this step focused on:

- extend `app.dashboard.overview.build_dashboard_payload(...)` so the payload
  now exposes `stock_pool_drift_summary` at the top level, while also storing a
  matching `drift_summary` field inside `stock_pool_health`
- reuse `build_stock_pool_drift_summary_text(...)` in the dashboard data layer
  so the same priority rule is shared across console output, reviews, alerts,
  and the homepage KPI area
- add a new replaceable KPI card spec in `app.dashboard.presentation` for
  `stock_pool_drift_summary`, including both default and `business_cn` labels
- verify the change with `tests.test_dashboard`,
  `tests.test_dashboard_presentation`, and `tests.test_dashboard_streamlit`

Current effect:

- the dashboard homepage now has a dedicated first-screen KPI card for stock
  pool drift, which makes main-line structure bias visible immediately on page
  load
- the payload and presentation layers now both treat stock-pool drift as a
  first-class top-level summary metric rather than a detail hidden deeper in
  the health section

Later on 2026-07-14, that new homepage stock-pool drift KPI card was upgraded
from a fixed label/value card into a replaceable copy layer so title, tone,
caption, and display length can be swapped without touching business logic.

What this step focused on:

- extend the pool-drift KPI spec in `app.dashboard.presentation` with
  `copy_variants`, `caption`, `value_max_length`, and tone overrides, including
  ready-to-use `business_cn`, `compact`, and `priority` variants
- update the Streamlit KPI render path so KPI cards now resolve copy variants
  through the shared spec-merging helper, and clamp long text values through a
  small reusable `_apply_kpi_value_length_limit(...)` helper
- add focused regression coverage in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit` for
  variant copy, caption preference, and length limiting

Current effect:

- the homepage stock-pool drift card is now safely style-replaceable at the
  presentation layer, so future wording or emphasis changes can stay isolated
  from dashboard payload and monitoring logic
- the dashboard KPI system now supports a richer pattern for non-numeric KPI
  cards, which can be reused later for other business-summary cards

Later on 2026-07-14, the homepage KPI system itself was made more explicit by
introducing separate text-card vs numeric-card handling instead of relying on
implicit rules such as "has max length" or "looks numeric".

What this step focused on:

- add an explicit `card_type` field into dashboard KPI specs so each KPI now
  declares whether it is a `text` card or a `numeric` card
- route KPI value resolution through a new shared
  `_resolve_kpi_card_value(...)` helper in the Streamlit layer, applying text
  truncation only to text cards while preserving numeric formatting behavior
- lock this behavior with focused presentation and Streamlit regression tests
  so timestamp/pool-drift cards remain text-oriented and alert counters remain
  numeric-oriented

Current effect:

- adding future first-screen summary cards such as "main-line conclusion" or
  "risk one-liner" now only requires payload + spec work, without introducing
  new render-path special cases
- the KPI presentation layer is now cleaner and more scalable, with less hidden
  coupling between copy behavior and field formatting

Later on 2026-07-14, the first of those next summary cards was implemented:
the dashboard homepage now includes a dedicated "main-line conclusion"
text-based KPI card alongside the existing stock-pool drift card.

What this step focused on:

- extend `app.dashboard.overview.build_dashboard_payload(...)` with a
  top-level `mainline_summary` field derived from sector strength ranking plus
  positive/negative alert balance
- add a new replaceable text KPI spec in `app.dashboard.presentation` for that
  main-line conclusion, including `business_cn`, `compact`, and `priority`
  variants parallel to the stock-pool drift card
- keep the new main-line KPI inside the explicit `text` card path so it reuses
  the new typed KPI render system without any new special-case renderer logic
- verify the feature with `tests.test_dashboard`,
  `tests.test_dashboard_presentation`, and `tests.test_dashboard_streamlit`

Current effect:

- the dashboard homepage now surfaces a first-glance market leadership
  conclusion before the deeper sector/detail blocks, making the business main
  line more visible at page entry
- the text-KPI pattern is now proven reusable for multiple business-summary
  cards, which lowers the cost of adding the next "risk state" summary card

Later on 2026-07-14, that third summary card was added as well: the homepage
now exposes a dedicated "risk state" one-line KPI beside main-line conclusion
and stock-pool drift, completing the first-screen summary trio.

What this step focused on:

- extend `app.dashboard.overview.build_dashboard_payload(...)` with a
  top-level `risk_summary` field derived from negative/positive alert balance
  and total alert count using explicit readable rules
- add a third replaceable text KPI spec in `app.dashboard.presentation` for the
  risk-state summary, including `business_cn`, `compact`, and `priority`
  variants parallel to the other text KPI cards
- keep the new risk summary card inside the same explicit `text` card render
  path, so no extra Streamlit special-case logic was needed
- verify the behavior with `tests.test_dashboard`,
  `tests.test_dashboard_presentation`, and `tests.test_dashboard_streamlit`

Current effect:

- the dashboard homepage now presents a full first-screen summary trio:
  main-line conclusion, stock-pool drift, and risk state
- the top-level dashboard reading order is now closer to the business workflow:
  first identify the line, then judge structure bias, then assess risk tone

Later on 2026-07-14, the order and emphasis of that homepage summary trio were
themselves extracted into a replaceable layout layer, so the first-screen KPI
reading order no longer depends on the static card declaration order.

What this step focused on:

- add `build_kpi_summary_layout_specs()` in `app.dashboard.presentation` to
  define reusable homepage summary layouts, including default, quick-scan, and
  business-CN variants
- extend dashboard view-variant metadata with `kpi_layout_key` and resolved
  `kpi_summary_layout`, so each homepage mode can choose its own card order and
  per-card variant overrides
- update the Streamlit KPI render path to resolve card order and copy-variant
  overrides through `_resolve_kpi_card_specs(...)` before rendering
- verify both layout metadata and render ordering with new regressions in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit`

Current effect:

- the homepage summary trio can now be reordered and re-emphasized per view
  mode without touching payload logic or the underlying KPI card definitions
- the project now has a clear configuration seam for future "first screen"
  dashboard tuning, including deciding which card should appear first in
  research view vs quick-scan view

Later on 2026-07-14, the page-level home layout itself was also separated into
replaceable view presets so the three dashboard modes now differ not only in
copy and KPI order, but also in first-screen information density and module
priority.

What this step focused on:

- extend `app.dashboard.presentation.build_page_layout_specs(...)` so page
  layout can now resolve named presets such as `default`, `quick_scan`, and
  `business_cn`
- add `page_layout_key` into dashboard view-variant metadata and thread that
  resolved key through `resolve_dashboard_view_spec(...)`
- rebalance the home module order so:
  - research view keeps the broader analysis flow
  - quick-scan view prioritizes KPI, next-session action, pool health, and
    latest alerts in a shorter first screen
  - Chinese business view emphasizes pool health, next-session action, and
    latest alerts before deeper sector and chart areas
- verify the new layout contracts with focused presentation regressions

Current effect:

- the three homepage modes now have clearer responsibilities instead of mainly
  differing by wording
- future layout replacement can stay in presentation metadata without touching
  the shared Streamlit render path

Later on 2026-07-14, the homepage also gained a small first-screen
"view-mode explanation" layer so the selected dashboard mode can explain its
own intended reading path directly on the page.

What this step focused on:

- add `build_view_mode_specs()` in `app.dashboard.presentation` as a
  replaceable metadata source for mode title, tone, summary label, body text,
  and supporting copy
- thread `view_mode_key` and resolved `view_mode_note` through
  `build_view_variant_specs()` and `resolve_dashboard_view_spec(...)`
- add `_build_view_mode_note_markdown(...)` in the Streamlit layer and render
  it near the top of the page after mode selection
- cover the new explanation layer with presentation and Streamlit regressions

Current effect:

- switching between `Research View`, `Quick Scan View`, and the Chinese
  business view now gives immediate on-page guidance about what that mode is
  optimized for
- future wording adjustments for mode guidance can stay inside presentation
  metadata without reopening the main dashboard render flow

Later on 2026-07-14, that top-of-page guidance was expanded into a unified
"first-screen control band" so mode explanation, current batch focus, and data
source context now sit together as one reusable dashboard entry layer.

What this step focused on:

- add `build_control_band_specs(...)` in `app.dashboard.presentation` to hold
  replaceable copy for batch-focus and data-source context, including a
  `business_cn` variant
- add `_build_control_band_markdown(...)` in `app.dashboard.streamlit_app` to
  compose three top entry panels together:
  - selected view-mode explanation
  - current batch focus
  - active database/source context
- replace the old standalone database caption with this unified control-band
  render path
- add focused regression coverage for default and Chinese control-band copy,
  including the empty-batch fallback behavior

Current effect:

- the dashboard homepage now has a more coherent first-screen entry strip
  instead of separate mode note and database caption fragments
- future top-of-page style replacement can treat the entry area as one
  configurable layer rather than a mix of unrelated UI pieces

Later on 2026-07-14, that first-screen control band was pushed one step
further into a true slot-based layout layer, so the order of mode, batch, and
source context no longer depends on one fixed helper sequence.

What this step focused on:

- add `build_control_band_layout_specs()` in `app.dashboard.presentation` so
  the entry strip can resolve named slot orders such as:
  - `default`
  - `quick_scan`
  - `business_cn`
- thread `control_band_layout_key` and resolved `control_band_layout` through
  dashboard view metadata
- update `_build_control_band_markdown(...)` so it now composes named slots in
  configured order instead of always rendering `view mode -> batch -> source`
- remove the leftover standalone mode-note render above the control band so the
  top-of-page entry area is no longer duplicated
- verify slot ordering and layout metadata with focused presentation and
  Streamlit regressions

Current effect:

- the homepage entry strip is now both unified and reorderable, which makes it
  much easier to tune the first-screen emphasis for different dashboard modes
- future top-entry layout changes can stay almost entirely in presentation
  metadata instead of reopening the main Streamlit page flow

Later on 2026-07-14, the top entry strip and KPI area were grouped again into a
single reusable "home header framework" so the first two homepage layers can
now be rearranged together instead of being tuned separately.

What this step focused on:

- add `build_home_header_layout_specs()` in `app.dashboard.presentation` so the
  full homepage header can resolve named orders such as:
  - `control_band -> kpi`
  - `kpi -> control_band`
- thread `home_header_layout_key` and resolved `home_header_layout` through the
  dashboard view metadata
- add `_render_home_header(...)` in `app.dashboard.streamlit_app` so the page
  now renders the first-screen header as one composed unit
- filter `kpi_cards` out of the remaining page-layout flow after header render
  so KPI is no longer duplicated between the header and the body layout
- verify header ordering and filtered page-layout behavior with focused
  presentation and Streamlit regressions

Current effect:

- the homepage now has a true header framework rather than two adjacent but
  separately-managed top sections
- future first-screen redesign work can treat the control band and KPI region
  as one configurable structure, which lowers the cost of swapping overall
  homepage emphasis per view mode

Later on 2026-07-14, the homepage header framework also gained its own shared
copy/style layer so the top entry title, detail-label wording, and supporting
explanations no longer depend on separate control-band and KPI-specific wording
choices.

What this step focused on:

- add `build_home_header_style_spec()` in `app.dashboard.presentation` to hold
  shared header-level copy such as:
  - header label
  - detail label
  - header body
  - standard and compact supporting copy
- thread `home_header_copy_variant` and resolved `home_header_style` through
  dashboard view metadata
- render a shared intro panel at the top of `_render_home_header(...)` and
  reuse the same header detail label inside view-mode, batch-focus, and
  data-source supporting panels
- verify both default and Chinese header-style behavior with focused
  presentation and Streamlit regressions

Current effect:

- the homepage header now has one consistent tone/copy boundary instead of
  mixing separate "details" wording between control-band and KPI areas
- future first-screen wording refreshes can stay more centralized in the
  presentation layer without reopening multiple header-related helpers

Later on 2026-07-14, the homepage body also moved one step closer to the same
configuration-first structure by separating the first-screen priority content
cluster from the full-page layout list.

What this step focused on:

- add `build_home_priority_content_layout_specs()` in
  `app.dashboard.presentation` so the key first-screen body blocks can be
  ordered independently for each view mode
- thread `priority_content_layout_key` and resolved
  `priority_content_layout` through dashboard view metadata
- rebuild `build_page_layout_specs(...)` so its early content order now
  composes from that priority-content helper instead of repeating the same
  body-priority choices inline
- verify both the standalone priority layout metadata and the composed page
  layout order with focused presentation regressions

Current effect:

- the homepage layout now has a cleaner structural split:
  - header framework
  - first-screen body priority cluster
  - remaining page content flow
- future homepage tuning can now adjust first-screen body emphasis with less
  risk of accidentally rewriting unrelated page sections

Later on 2026-07-14, that first-screen body-priority work was pushed one step
further into a grouped-content layer so the homepage body no longer depends only
on one flat render-order list.

What this step focused on:

- add `build_home_content_group_layout_specs()` in
  `app.dashboard.presentation` so the homepage body can now be described as
  ordered groups such as:
  - `priority_cluster`
  - `followup_cluster`
  - `chart_cluster`
  - `archive_cluster`
- thread `content_group_layout_key` and resolved `content_group_layout`
  through dashboard view metadata
- rebuild `build_page_layout_specs(...)` from grouped homepage body metadata
  instead of keeping body section order only as one inline flat list
- verify both grouped-layout metadata and the composed page order with focused
  presentation regressions

Current effect:

- the homepage body now has a more explicit structure:
  - home header framework
  - grouped first-screen/early-screen content clusters
  - within-group section order
- future homepage redesign work can now change not only section order but also
  which sections belong together, while staying in presentation metadata

Later on 2026-07-14, that grouped homepage body metadata was connected all the
way into the Streamlit render layer, so content clusters are now not only an
internal layout concept but also a visible homepage reading aid.

What this step focused on:

- extend grouped homepage section metadata with group-level title and tone in
  `app.dashboard.presentation`
- thread `group_key`, `group_title`, and `group_tone` into the composed
  `page_layout` rows returned by `build_page_layout_specs(...)`
- add `_render_content_group_intro(...)` in `app.dashboard.streamlit_app` so
  the page now renders one shared intro panel when entering a new homepage
  content group
- verify the behavior with focused regressions in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit`

Current effect:

- the homepage body now visibly announces transitions such as priority cluster,
  follow-up cluster, chart cluster, and archive cluster instead of relying only
  on implicit section order
- future group-level wording, tone, and grouping changes can stay in
  presentation metadata while the shared render path remains stable

Later on 2026-07-14, the homepage intro containers were unified one step
further through a shared intro-panel style layer, so header intro, group intro,
and section intro now follow the same configurable structure instead of each
assembling their own support-label pattern separately.

What this step focused on:

- add `build_intro_panel_style_spec(...)` in `app.dashboard.presentation` as a
  shared style boundary for intro-container labels and supporting copy across:
  - home header intro
  - content group intro
  - content section intro
- keep role-specific wording explicit inside that shared layer, including
  separate header-detail and content-detail labels, so existing business
  meaning stays stable while the container structure is unified
- add `_build_intro_panel_markdown(...)` in `app.dashboard.streamlit_app` and
  route header/group/section intro rendering through that shared entry point
- verify the refactor with focused regressions in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit`

Current effect:

- homepage intro containers now form a more consistent replaceable system:
  header intro, group intro, and section intro share one render pattern
- future wording or style swaps for homepage entry panels can stay more
  centralized without weakening the explicit differences between header-level
  and content-level context

Later on 2026-07-14, the chart entry area was folded into that same intro
container system, so the homepage's four main entry surfaces now follow one
more consistent replaceable pattern:

- home header intro
- content group intro
- content section intro
- chart intro

What this step focused on:

- extend the shared intro-style layer with chart-specific fields such as:
  - `chart_intro_label`
  - `chart_supporting_copy`
  - `compact_chart_supporting_copy`
- thread those chart intro fields through `build_summary_panel_style_spec(...)`
  so chart entry copy stays variant-aware without introducing a separate chart
  wording source
- update `app.dashboard.streamlit_app` so chart blocks now build their entry
  panel through the same shared intro-container path instead of stitching
  together a chart header plus a separate details block
- remove the redundant extra chart-title panel from the chart render flow so
  chart blocks enter more cleanly
- verify the refactor with focused regressions in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit`

Current effect:

- the homepage's main entry containers are now closer to one coherent
  presentation system instead of four slightly different wrapper patterns
- chart entry wording, including compact-mode support copy, can now be replaced
  more centrally without touching chart data flow or render-order logic

Later on 2026-07-14, the homepage layout gained one more structural layer
above content groups: replaceable page-segment templates now describe which
homepage groups belong together as one visible section of the page.

What this step focused on:

- add `build_page_segment_template_specs(...)` in
  `app.dashboard.presentation` so homepage modes can define segment templates
  such as:
  - header segment
  - priority segment
  - analysis segment
  - archive segment
- thread segment metadata into `build_page_layout_specs(...)`, so each emitted
  page-layout row now carries:
  - `segment_key`
  - `segment_title`
  - `segment_tone`
- extend dashboard view resolution with `page_segment_template_key` and the
  resolved `page_segment_template`
- add segment-level intro copy fields to the shared intro/content style layer
- update `app.dashboard.streamlit_app` so the homepage now renders a shared
  intro panel when switching into a new page segment, above the existing
  content-group intro panels
- verify the behavior with focused regressions in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit`

Current effect:

- homepage modes can now change not only section order and group order, but
  also which groups are presented together as one visible page section
- the homepage structure is now more explicit across three body levels:
  - page segment
  - content group
  - concrete section

Later on 2026-07-14, those three homepage body levels gained explicit business
role metadata as well, so homepage orchestration can now align more directly
with the research workflow instead of relying only on visual grouping.

What this step focused on:

- add `build_business_role_specs(...)` in `app.dashboard.presentation` as a
  shared role dictionary covering roles such as:
  - context
  - decision
  - validation
  - analysis
  - archive
- attach `role_key` to page-segment templates and homepage content groups
- attach section-level role metadata to content sections and chart specs
- thread the resulting role fields into `build_page_layout_specs(...)`, so
  page-layout rows now also carry:
  - `segment_role_key`
  - `group_role_key`
  - `section_role_key`
- update the Streamlit intro-panel flow so page-segment and content-group
  intros now show a lightweight business-role cue such as:
  - `Role: Decision`
  - `Role: Analysis`
- verify the metadata and render behavior with focused regressions in
  `tests.test_dashboard_presentation` and `tests.test_dashboard_streamlit`

Current effect:

- homepage structure is now explicit on two dimensions at once:
  - layout hierarchy: segment -> group -> section
  - business intent: context / decision / validation / analysis / archive
- future dashboard modes can now be tuned more naturally around business tasks,
  not only around section order, visual emphasis, or wording swaps

Later on 2026-07-14, the dashboard view modes themselves gained an explicit
business-role strategy layer, so switching modes now means switching not only
layout and copy, but also the declared business-role emphasis of the homepage.

What this step focused on:

- add `build_view_role_strategy_specs(...)` in
  `app.dashboard.presentation` as a replaceable strategy source for each view
  mode, including:
  - `primary_roles`
  - `secondary_roles`
  - `summary_label`
  - `body`
- thread `role_strategy_key` and resolved `role_strategy` through
  `build_view_variant_specs(...)` and `resolve_dashboard_view_spec(...)`
- add `_build_role_strategy_summary_text(...)` in
  `app.dashboard.streamlit_app` so role strategy metadata becomes a stable
  human-readable summary instead of staying as raw arrays
- extend the homepage view-mode note so the top control-band explanation now
  also states the current mode's role emphasis, for example:
  - primary roles
  - secondary roles
  - the intended business reading path
- verify the strategy metadata and rendered summary behavior with focused
  regressions in `tests.test_dashboard_presentation` and
  `tests.test_dashboard_streamlit`

Current effect:

- dashboard mode switching is now closer to "change business workstation
  strategy" rather than only "change page wording and order"
- the top-of-page mode explanation now tells the user not only what the mode is
  called, but also which business roles it is designed to emphasize first

Later on 2026-07-14, that role-strategy layer started affecting homepage
content density directly, so some roles can now be postponed or hidden in a
mode-specific way instead of only being described in the mode note.

What this step focused on:

- extend `build_view_role_strategy_specs(...)` with explicit behavior fields:
  - `deferred_roles`
  - `hidden_roles`
- add `_apply_role_strategy_to_page_layout(...)` in
  `app.dashboard.streamlit_app` so homepage sections can now be:
  - filtered out when their business role is hidden in the current mode
  - moved later when their business role is marked as deferred
- wire that role-strategy filter into the main homepage render path after the
  header-owned KPI section is removed from the body flow
- extend `_build_role_strategy_summary_text(...)` so the top-of-page mode note
  now also reports deferred and hidden roles, not only primary and secondary
  emphasis
- verify behavior with focused regressions covering:
  - hidden archive-role sections
  - deferred analysis-role sections
  - updated role-strategy summary wording in the homepage header flow

Current effect:

- dashboard modes now influence not only wording and section order, but also
  actual homepage content density by business role
- the homepage is now closer to a true role-aware workstation:
  quick-scan mode can hide archive-first content, while still keeping analysis
  content available later when configured as deferred

Later on 2026-07-14, that role-aware density control was refined one step
further from role-level behavior to section-level behavior, so dashboard modes
can now keep a few core modules from a role while postponing or hiding the rest
of that same role family.

What this step focused on:

- extend `build_view_role_strategy_specs(...)` with section-level controls:
  - `pinned_sections`
  - `deferred_sections`
  - `hidden_sections`
- upgrade `_apply_role_strategy_to_page_layout(...)` so homepage layout
  strategy now applies in this order:
  - pinned sections first
  - normal visible sections next
  - deferred sections later
  - hidden sections removed
- keep role-level behavior in place as a broader fallback while allowing
  section-level strategy to override it for more precise mode tuning
- extend `_build_role_strategy_summary_text(...)` so the homepage header note
  now also states section-level actions such as:
  - pinned sections
  - deferred sections
  - hidden sections
- verify the refined behavior with focused regressions covering:
  - pinned section ordering
  - hidden section removal
  - combined role-level and section-level layout outcomes

Current effect:

- dashboard modes can now behave more like curated workstations instead of only
  coarse role filters
- quick-scan and business views are now able to preserve a few core modules
  from important workflows while still reducing page density elsewhere

Later on 2026-07-14, the refined section-level mode strategy gained one more
ordering input: explicit module priority metadata now decides ordering inside
the same strategy bucket, so important modules from the same business role no
longer need to depend only on file order.

What this step focused on:

- add `module_priority` metadata to core homepage content modules and chart
  modules, for example:
  - `stock_pool_health`
  - `next_session_action`
  - `latest_alerts`
  - `strongest_sector`
  - chart modules
- thread `module_priority` into `build_page_layout_specs(...)` so each rendered
  section row now carries explicit task importance
- add `_sort_page_layout_sections_by_priority(...)` and
  `_parse_module_priority(...)` in `app.dashboard.streamlit_app`
- upgrade `_apply_role_strategy_to_page_layout(...)` so each strategy bucket is
  now sorted by:
  - pinned bucket priority
  - normal bucket priority
  - deferred bucket priority
- verify the behavior with focused regressions for:
  - module-priority metadata presence
  - same-bucket priority ordering
  - invalid priority fallback behavior

Current effect:

- dashboard mode behavior is now more deterministic and task-oriented when
  several modules share the same role and same strategy bucket
- homepage curation is now driven by three layers together:
  - business role
  - section-level mode strategy
  - explicit module priority

Later on 2026-07-14, the dashboard modes were pushed one step closer to real
usage scenarios by adding explicit task-template metadata on top of role and
priority strategy.

What this step focused on:

- add `build_task_template_specs(...)` in `app.dashboard.presentation` to map
  dashboard modes to concrete work scenarios such as:
  - intraday tracking
  - open quick scan
  - close review
- thread `task_template_key` and resolved `task_template` through
  `build_view_variant_specs(...)` and `resolve_dashboard_view_spec(...)`
- add `_build_task_template_summary_text(...)` in
  `app.dashboard.streamlit_app` so task-template metadata becomes readable
  guidance instead of staying as raw fields
- extend the top-of-page view-mode note so it now explains three things
  together:
  - current mode identity
  - current task template / work scenario
  - current role strategy
- verify the behavior with focused regressions for:
  - task-template metadata resolution
  - task-template summary wording
  - homepage header integration

Current effect:

- dashboard modes are now easier to understand in practical terms because they
  describe not only layout strategy, but also the concrete business scenario
  they are optimized for
- the homepage is now closer to a scenario-aware workstation rather than a
  generic configurable dashboard

Later on 2026-07-14, those scenario-aware dashboard modes gained an additional
time-phase layer, so the homepage can now express not only "what kind of task
this mode is for" but also "which market-time stage this mode is optimized
for."

What this step focused on:

- add `build_time_phase_specs(...)` in `app.dashboard.presentation` to define
  explicit time-phase templates such as:
  - intraday phase
  - post-open scan
  - close phase
- thread `time_phase_key` and resolved `time_phase` through
  `build_view_variant_specs(...)` and `resolve_dashboard_view_spec(...)`
- add `_build_time_phase_summary_text(...)` in
  `app.dashboard.streamlit_app` so time-phase metadata becomes compact readable
  guidance
- extend the top-of-page view-mode note again so it now combines four layers:
  - mode identity
  - task template
  - time phase
  - role strategy
- verify the new time-phase metadata and rendered summary behavior with focused
  regressions in `tests.test_dashboard_presentation` and
  `tests.test_dashboard_streamlit`

Current effect:

- dashboard modes now read more like concrete time-based workstations rather
  than only generic scenario presets
- the homepage can now tell the user not only what the mode is and what it
  emphasizes, but also which stage of the trading day it is meant to support

Later on 2026-07-14, the time-phase layer moved from explanation-only metadata
into the homepage behavior path, so market-time stage can now directly affect
which modules are emphasized in the body layout.

What this step focused on:

- extend `build_time_phase_specs(...)` with behavior fields such as:
  - `pinned_sections`
  - `deferred_sections`
  - `hidden_sections`
- add `_merge_layout_strategy(...)` in `app.dashboard.streamlit_app` so the
  effective homepage behavior now comes from:
  - role strategy
  - time-phase strategy
  merged into one layout strategy before rendering
- update `_apply_role_strategy_to_page_layout(...)` call sites so the homepage
  body now follows that merged strategy instead of role strategy alone
- extend `_build_time_phase_summary_text(...)` so the top-of-page explanation
  now also reports section-level behavior implied by the current time phase
- verify the merged behavior with focused regressions for:
  - time-phase behavior metadata
  - merged strategy composition
  - merged layout ordering and visibility

Current effect:

- time phase is now a real layout input, not only a descriptive label
- homepage behavior is now driven by four layers together:
  - business role
  - section-level strategy
  - module priority
  - market-time phase

Later on 2026-07-15, the homepage workstation modes became data-aware by
adding an automatic default recommendation layer, so the first-screen mode can
now start closer to the current monitoring situation even before the user
manually switches views.

What this step focused on:

- add `_recommend_dashboard_variant_key(...)` in
  `app.dashboard.streamlit_app` to recommend a default mode from current
  payload state using explicit rules around:
  - latest batch time
  - alert pressure
  - negative alert presence
  - available historical batches
- update `_resolve_dashboard_variant_key(...)` so recommendation is used only
  as a fallback and never overrides an already valid manual mode selection
- wire the recommendation into `main()` before the mode selector renders, so
  the selector opens in a context-aware default state
- verify the behavior with focused regressions for:
  - manual selection priority
  - recommended fallback behavior
  - opening-session compact recommendation
  - alert-driven compact recommendation
  - late-session review recommendation
  - quiet mid-session default fallback

Current effect:

- homepage mode selection is now driven by both static configuration and live
  monitor context
- the dashboard opens closer to the likely task state without taking control
  away from manual view switching

Later on 2026-07-15, the automatic mode recommendation stopped being hidden
logic and became visible first-screen context, so the homepage can now explain
why it prefers a given workstation mode.

What this step focused on:

- add `_build_dashboard_variant_recommendation_note(...)` and supporting
  helpers in `app.dashboard.streamlit_app` to summarize recommendation reasons
  from explicit inputs such as:
  - opening-stage batch timing
  - active alerts
  - negative alerts
  - multiple saved batches
- thread that recommendation note into the home-header control band so the
  current mode explanation now includes both:
  - current selected mode
  - system recommendation context
- keep manual selection behavior explicit by showing when:
  - the current view matches the system recommendation
  - the current view differs from the system recommendation
- verify the behavior with focused regressions for:
  - recommendation note generation
  - control-band rendering
  - home-header rendering

Current effect:

- default mode recommendation is now explainable instead of opaque
- the top-of-page mode block now tells the user not just what view is active,
  but why that view is being suggested right now

Later on 2026-07-15, the mode recommendation logic moved one step closer to the
business main line by incorporating stock-pool health and drift state, so the
homepage can now react not only to time and alerts but also to whether the
monitoring universe itself needs validation.

What this step focused on:

- extend the homepage recommendation rules in
  `app.dashboard.streamlit_app` so stock-pool health can override time-based
  mode selection when:
  - pool validation is blocking or invalid
  - structure drift tags are active
  - health risk level is warning
- keep those rules explicit and isolated through helper functions such as:
  - `_normalize_stock_pool_health(...)`
  - `_resolve_stock_pool_priority_variant(...)`
  - `_build_stock_pool_recommendation_reason(...)`
- update the recommendation explanation layer so the top-of-page note now tells
  the user when the active suggestion is being driven by:
  - pool-health blocking state
  - pool-structure drift
  - pool-health warning state
- verify the new priority ordering with focused regressions for:
  - blocking pool state overriding opening-mode compact bias
  - drift state pushing the homepage toward review mode
  - recommendation note preferring stock-pool reasons over generic time/alert reasons

Current effect:

- homepage mode recommendation now trusts the monitor universe health before it
  trusts the market tape
- when the stock pool itself needs validation, the workstation now naturally
  shifts toward review/validation-first behavior

Later on 2026-07-15, the homepage moved from mode recommendation into explicit
first-step guidance, so the selected workstation now tells the user not only
which mode is active, but also what to check first.

What this step focused on:

- add `_build_dashboard_priority_action_note(...)` in
  `app.dashboard.streamlit_app` to translate current mode + payload state into
  explicit first-step guidance, including cases such as:
  - alert-first quick scan
  - stock-pool validation first
  - saved-batch comparison first
  - strongest-sector plus pool-health confirmation first
- thread that new first-step note through the same home-header mode block that
  already shows:
  - mode identity
  - task template
  - time phase
  - role strategy
  - recommendation reason
- keep the action rules explicit and business-oriented instead of hiding them
  inside generic layout metadata
- verify the behavior with focused regressions for:
  - compact alert-first action prompts
  - stock-pool blocking validation prompts
  - business-cn saved-batch review prompts
  - home-header render integration

Current effect:

- homepage mode selection now flows directly into an actionable first step
- the first-screen mode block is closer to a practical workstation coach than a
  passive mode description

Later on 2026-07-15, that first-step guidance stopped being text-only and began
to directly affect first-screen layout behavior, so the homepage can now move
the most relevant modules to the front automatically.

What this step focused on:

- add `_build_priority_action_layout_strategy(...)` and related helpers in
  `app.dashboard.streamlit_app` so first-step guidance now maps into concrete
  section-order behavior
- define explicit action-driven section stacks for scenarios such as:
  - alert-first quick scan
  - saved-batch-first review flow
  - stock-pool blocking validation
  - stock-pool drift review
  - quiet balanced research
- merge that action-driven layout strategy into the existing homepage behavior
  chain after:
  - role strategy
  - time-phase strategy
  so the effective homepage order is now influenced by:
  - business role
  - time phase
  - stock-pool health
  - alert pressure
  - first-step action intent
- verify the new behavior with focused regressions for:
  - action-section resolution
  - action-driven pinned/deferred sections
  - actual page-layout ordering after action rules are applied

Current effect:

- homepage first-screen order now matches the recommended first step instead of
  only describing it
- the workstation is now more action-driven: it tells the user what to do first
  and also brings that module forward automatically

Later on 2026-07-15, the action-driven header gained a dedicated compact action
summary card, so the first-screen control band can now present a short
actionable flow instead of scattering that guidance across longer mode text.

What this step focused on:

- extend `build_control_band_layout_specs()` in
  `app.dashboard.presentation` to reserve a dedicated `action_summary` slot in
  the control band for all major view variants
- add `_build_action_summary_markdown(...)`,
  `_build_action_summary_content(...)`, and
  `_build_secondary_action_line(...)` in `app.dashboard.streamlit_app`
  to build a short reusable action card that combines:
  - current first step
  - recommendation basis
  - second step
- thread that new action-summary card into `_build_control_band_markdown(...)`
  so the home header now separates:
  - current mode context
  - current action flow
  - batch context
  - data source
- verify the behavior with focused regressions for:
  - action-summary content generation
  - control-band slot ordering
  - business-cn action-summary copy
  - header integration

Current effect:

- the home header now contains a dedicated short action-summary card instead of
  overloading the mode note with too much workflow text
- first-screen guidance is easier to scan because the user can now read the
  current mode and current action flow as two separate but coordinated blocks

Later on 2026-07-15, that action-summary card gained explicit module mapping,
so the first-screen guidance now points the user to concrete homepage sections
instead of only describing abstract steps.

What this step focused on:

- extend the home-header action-summary flow in
  `app.dashboard.streamlit_app` to pass resolved priority sections from the
  live homepage state into the summary card
- add `_build_action_module_lines(...)` and
  `_resolve_action_section_label(...)` so the action card now explicitly shows:
  - primary module
  - follow-up module
- keep the action-summary module mapping aligned with the same priority section
  logic that already drives:
  - first-step text
  - homepage pinned ordering
- verify the behavior with focused regressions for:
  - default copy module mapping
  - business-cn copy module mapping
  - control-band integration
  - header render compatibility

Current effect:

- the user can now read the action-summary card and immediately know which
  homepage section to inspect first and second
- first-screen workflow guidance is now aligned across:
  - text summary
  - module naming
  - section ordering

Later on 2026-07-15, the action-summary card became more concrete by mapping
its first-step and follow-up guidance directly to named homepage modules.

What this step focused on:

- thread resolved priority-action sections from the live homepage state into the
  action-summary card path in `app.dashboard.streamlit_app`
- upgrade the action-summary helpers so the card now explicitly shows:
  - primary module
  - follow-up module
- normalize the business-cn action-summary copy path so the card’s:
  - title
  - recommendation basis
  - second-step line
  - module labels
  all render from the same stable helper layer
- verify the behavior with focused regressions for:
  - default action-summary module mapping
  - business-cn module mapping
  - header/control-band integration

Current effect:

- the action-summary card now tells the user not just what to do next, but
  exactly which homepage module to open first and second
- first-screen workflow guidance is now aligned across:
  - action text
  - module naming
  - module ordering

Later on 2026-07-15, those first-step and follow-up module mappings gained a
lightweight visual focus cue in the page body, so the user can spot the most
important sections faster after landing on the homepage.

What this step focused on:

- extend `_build_content_section_header_markdown(...)` in
  `app.dashboard.streamlit_app` with an optional lightweight `focus_label`
- add `_build_priority_focus_labels(...)` so the current priority-action stack
  now maps into simple per-section cues such as:
  - primary focus
  - follow-up focus
- thread those focus cues through:
  - `_render_page_layout(...)`
  - `_render_content_block_with_density(...)`
  so action-priority modules gain a visible header hint without changing core
  rendering structure
- verify the behavior with focused regressions for:
  - focus-label generation
  - section-header rendering
  - content-block rendering
  - page-layout integration

Current effect:

- the homepage now not only orders action-priority modules first, but also
  labels them lightly once rendered
- the user can move from action-summary card to page body with less searching

Later on 2026-07-15, the action-summary card gained short location descriptors
derived from the current page layout, so the user can see not only which module
comes first but roughly where it sits in the body.

What this step focused on:

- compute one shared effective page layout earlier in `app.dashboard.streamlit_app`
  and reuse it for both:
  - body rendering
  - action-summary location description
- add `_build_priority_action_locations(...)` so priority-action modules can be
  described in terms of current:
  - segment title
  - group title
- thread those location descriptors into the action-summary card so it now
  shows compact lines such as:
  - location
  - follow-up location
- verify the behavior with focused regressions for:
  - location resolution from page-layout metadata
  - default action-summary location copy
  - business-cn action-summary location copy
  - header render integration

Current effect:

- the action-summary card now helps the user find priority modules faster by
  naming both the module and its rough body location
- first-screen workflow guidance is now aligned across:
  - action summary
  - module order
  - module labels
  - segment/group location

Later on 2026-07-15, the action-summary and body-focus layer were aligned one
step further so their wording now follows the same section-title source and a
clearer ordered reading sequence.

What this step focused on:

- stop relying on a separate hardcoded action-summary section-name map inside
  `app.dashboard.streamlit_app`
- resolve action-summary module names from the same content-section title specs
  already used by the homepage itself, so card wording and real section titles
  stay synchronized
- upgrade the lightweight body focus cues from generic labels into explicit
  ordered anchors:
  - 1. primary focus
  - 2. follow-up focus
- keep the action-summary location lines and module lines inside the same
  stable helper layer, so future copy or style replacement can be done without
  touching the main rendering flow
- verify the behavior with focused regressions for:
  - default action-summary title alignment
  - business-cn action-summary title alignment
  - ordered focus-label rendering

Current effect:

- the action-summary card now uses the same naming language as the real body
  sections, which reduces wording drift between header guidance and module
  titles
- the first-screen path is now easier to follow because the user can map:
  - first step
  - first module
  - first visible body anchor
  in one consistent sequence

Later on 2026-07-15, the homepage action-guidance chain gained one more
consistency guard so priority modules shown in header guidance cannot drift away
from the sections that are actually visible in the current body layout.

What this step focused on:

- add `_normalize_priority_action_sections_for_layout(...)` in
  `app.dashboard.streamlit_app`
- run the resolved priority-action stack through the current effective page
  layout before it is reused by:
  - the action-summary card
  - the priority location helper
  - the body focus-label helper
- keep only visible unique section keys in original order, so future layout
  edits or module removals do not leave stale header guidance behind
- verify the behavior with a focused regression that confirms:
  - missing sections are dropped
  - duplicate sections are deduplicated
  - visible section order is preserved

Current effect:

- header guidance, location hints, and body focus anchors now all point only to
  sections that truly exist in the current homepage layout
- this reduces the chance of future logic conflicts when page-layout structure
  changes but recommendation rules stay the same

Later on 2026-07-15, the homepage priority-action logic was refactored into a
clearer scenario layer so business-state detection is now separated from copy
and section-order mapping.

What this step focused on:

- add `_resolve_priority_action_scenario(...)` in
  `app.dashboard.streamlit_app`
- move the current first-screen business states into explicit internal scenario
  keys, including:
  - stock-pool blocking review
  - stock-pool drift review
  - stock-pool health review
  - risk-alert scan
  - alert scan
  - batch review
  - baseline review
- make both:
  - `_build_dashboard_priority_action_note(...)`
  - `_resolve_priority_action_sections(...)`
  read from the same scenario resolver instead of duplicating condition trees
- replace the fragile direct branch wording path with scenario-to-copy and
  scenario-to-sections mapping, so future business refinements can be added
  without coupling note copy to section-order logic
- verify the behavior with focused regressions for:
  - blocking stock-pool scenario resolution
  - saved-batch review scenario resolution
  - baseline scenario fallback

Current effect:

- priority-action copy and priority-module ordering now share one consistent
  business-state source
- later changes to intraday/review rules can be extended more safely because
  the code now has a dedicated scenario layer instead of one large mixed
  decision block

Later on 2026-07-15, the homepage action-summary layer gained a lightweight
scenario profile structure so first-screen guidance can now explain not only
which module comes first, but also the current business scenario and the
immediate reading objective in one reusable format.

What this step focused on:

- add `_build_priority_action_profile(...)` in
  `app.dashboard.streamlit_app`
- define reusable per-scenario profile fields for both default and
  `business_cn` copy, including:
  - scenario name
  - immediate objective
- thread that profile through the header control-band chain into
  `_build_action_summary_content(...)`
- add `_build_priority_action_profile_lines(...)` so the action-summary card
  now renders compact lines such as:
  - current scenario
  - current objective
- keep this as a lightweight metadata layer on top of the existing scenario
  resolver, without changing the underlying recommendation outcome
- verify the behavior with focused regressions for:
  - default scenario-profile generation
  - default action-summary scenario/objective lines
  - business-cn action-summary scenario/objective lines

Current effect:

- the action-summary card now explains both:
  - what to look at first
  - what business goal that first step is trying to accomplish
- later scenario-specific UI or configurable rule layers can reuse one stable
  profile structure instead of re-deriving explanation copy from raw branches

Later on 2026-07-15, that scenario-profile layer was pushed one step further
into the dashboard presentation/config surface, so the homepage priority-action
copy is no longer owned only by `app.dashboard.streamlit_app`.

What this step focused on:

- add `build_priority_action_profile_specs(...)` in
  `app.dashboard.presentation`
- move reusable per-scenario action-summary copy into one replaceable
  presentation-layer config, including:
  - first-step note
  - scenario name
  - immediate objective
  - second-step note
- refactor `_build_dashboard_priority_action_note(...)` so it now resolves
  `first_step_note` from that shared presentation config instead of using a
  local hardcoded dictionary
- refactor `_build_priority_action_profile(...)` so it now resolves:
  - scenario
  - objective
  - second-step note
  from the same shared presentation config
- update `_build_secondary_action_line(...)` so action-summary follow-up copy
  now prefers the configured scenario-level `second_step_note` before falling
  back to the older string-based compatibility path
- verify the behavior with focused regressions for:
  - presentation-layer scenario copy exposure
  - second-step note availability in resolved profiles
  - full dashboard action-summary regression coverage

Current effect:

- priority-action scenario wording is now organized like the rest of the
  replaceable dashboard presentation system
- later copy-only adjustments to scenario guidance can be made in one config
  surface without changing the homepage rule logic

Later on 2026-07-15, that same scenario config layer was extended with richer
reading-context fields so the homepage action-summary can explain not just the
current scenario and objective, but also when the scenario is appropriate and
which points deserve priority attention.

What this step focused on:

- extend `app.dashboard.presentation.build_priority_action_profile_specs(...)`
  with two additional per-scenario fields:
  - applicable session
  - priority focus
- thread those fields through `_build_priority_action_profile(...)` in
  `app.dashboard.streamlit_app`
- extend `_build_priority_action_profile_lines(...)` so the action-summary card
  now renders compact extra lines such as:
  - when to use
  - priority focus
- keep the recommendation outcome unchanged while making the visible scenario
  guidance more explicit and easier to interpret
- verify the behavior with focused regressions for:
  - default action-summary context lines
  - business-cn action-summary context lines
  - presentation-layer field exposure

Current effect:

- the homepage action-summary now tells the user:
  - what scenario they are in
  - when that scenario is appropriate
  - what the immediate objective is
  - which points should be watched first
- this makes the scenario layer closer to a full reusable business guidance
  profile instead of only a short label-plus-objective bundle

Later on 2026-07-15, that scenario-guidance profile was extended one step
further with lightweight reading-flow fields so the homepage can now suggest
not just what to read, but also in which order and at what pace that reading is
best approached.

What this step focused on:

- extend the priority-action scenario profile structure with:
  - reading order
  - reading pace
- thread those fields through `_build_priority_action_profile(...)` in
  `app.dashboard.streamlit_app`
- extend `_build_priority_action_profile_lines(...)` so the action-summary card
  now renders additional compact guidance lines such as:
  - suggested order
  - reading pace
- keep the current business recommendation outcome unchanged while making the
  first-screen reading path more explicit
- verify the behavior with focused regressions for:
  - default action-summary reading-order copy
  - default action-summary reading-pace copy
  - business-cn action-summary structure compatibility

Current effect:

- the homepage action-summary now describes:
  - what scenario the user is in
  - when it applies
  - what to focus on
  - which order to read in
  - how fast or carefully that read should happen
- this moves the homepage guidance layer closer to a reusable business reading
  playbook instead of only a summary card

Later on 2026-07-15, the priority-action scenario layer was refined from a
mostly generic homepage guide into a more business-timed reading script by
splitting several broad scenarios into more session-aware variants.

What this step focused on:

- extend the default dashboard scenario set in
  `app.dashboard.presentation.build_priority_action_profile_specs(...)` with
  more session-aware reading scripts, including:
  - intraday alert review
  - close review
  - midday main-line review
- extend the `business_cn` scenario set with close-review and midday-main-line
  counterparts so Chinese business view does not fall back to unrelated generic
  copy
- refine `_resolve_priority_action_scenario(...)` in
  `app.dashboard.streamlit_app` so scenario resolution now distinguishes:
  - opening alert scan
  - intraday alert refresh
  - quiet midday main-line review
  - late-session close review
- refine `_resolve_priority_action_sections(...)` so each new scenario maps to
  a more realistic first-screen reading order instead of reusing one broad
  stack
- verify the behavior with focused regressions for:
  - intraday alert scenario resolution
  - close-review scenario resolution
  - midday-baseline scenario resolution
  - corresponding section-order changes

Current effect:

- the homepage guidance now behaves more like a real research reading script
  tied to market timing, instead of only a generic priority switch
- opening, midday, intraday-alert, and late-session review states now have more
  distinct first-screen module order and reading emphasis

Later on 2026-07-15, the action-summary guidance was tied more directly to the
actual content inside the first priority module, so the homepage can now tell
the user not only which module to open first, but also what to scan first once
they enter that module.

What this step focused on:

- extend selected content-section specs in
  `app.dashboard.presentation.build_content_section_specs(...)` with a compact
  `action_focus_hint`, including key first-read hints for:
  - stock-pool health
  - strongest sector
  - leader summary
  - latest alerts
  - saved batches
  - next-session action
- add `_build_priority_action_content_focus_lines(...)` in
  `app.dashboard.streamlit_app`
- thread that helper into `_build_action_summary_content(...)` so the
  action-summary card now renders one lightweight line describing what to look
  for inside the first priority module
- verify the behavior with focused regressions for:
  - default action-summary content-focus line
  - business-cn action-summary content-focus line
  - full dashboard summary compatibility

Current effect:

- the homepage action-summary now points to:
  - which module comes first
  - where that module sits
  - what concrete information inside that module deserves the first glance
- this makes the first-screen guidance closer to a real reading assistant
  rather than only a section-order reminder

Later on 2026-07-15, that content-focus guidance was refined into more
structured reading anchors so the action-summary can now point not only to a
module-level hint, but also to the first field, first group, and first
conclusion inside the first priority module.

What this step focused on:

- extend selected content-section specs in
  `app.dashboard.presentation.build_content_section_specs(...)` with
  structured action-focus anchors, including:
  - first field
  - first group
  - first conclusion
- extend `_build_priority_action_content_focus_lines(...)` in
  `app.dashboard.streamlit_app` so the action-summary card now renders these
  anchors as separate compact lines instead of only one generic hint
- keep the first-screen guidance backward-compatible by preserving the broader
  module-level hint while adding the new structured anchors underneath it
- verify the behavior with focused regressions for:
  - default action-summary field/group/conclusion anchors
  - business-cn action-summary anchor presence
  - full dashboard summary compatibility

Current effect:

- the homepage action-summary now behaves more like a reading checklist:
  - first open this module
  - first scan these fields
  - first read this group
  - first decide this conclusion
- this makes the dashboard guidance layer closer to a practical research
  workstation entry flow rather than a purely descriptive summary card

Later on 2026-07-15, those structured reading anchors became data-aware for
the most time-sensitive first-screen modules, so the action-summary can now
change its "first look" wording based on live dashboard state instead of
always repeating one static hint.

What this step focused on:

- thread live homepage `payload` context through the action-summary build chain
  in `app.dashboard.streamlit_app`, including:
  - `_build_control_band_markdown(...)`
  - `_build_action_summary_markdown(...)`
  - `_build_action_summary_content(...)`
- add `_resolve_dynamic_action_focus_overrides(...)` so the first priority
  module can override its reading anchors from current payload conditions
- start that dynamic override layer with two modules where static copy was most
  likely to drift away from real urgency:
  - `latest_alerts`
  - `stock_pool_health`
- make `latest_alerts` anchors change when:
  - negative alerts exist
  - normal alerts exist but no negative alerts dominate
- make `stock_pool_health` anchors change when the pool is:
  - blocking
  - warning
  - otherwise structurally available
- verify the behavior with focused regressions for:
  - negative-alert first-read override
  - blocking stock-pool-health first-read override
  - broader dashboard regression coverage

Current effect:

- the homepage action-summary now adapts its first-read checklist to the live
  urgency level instead of relying only on static module metadata
- if negative alerts appear, the user is told to inspect the newest risk alert
  first rather than reading alerts as a generic list
- if stock-pool health is blocking or warning, the user is told to inspect
  validation severity and trustworthiness first before continuing with the main
  research flow

Later on 2026-07-15, that same data-aware first-read layer was extended from
pure risk/validation modules into the main-line and action-planning modules, so
homepage guidance now reacts not only to alerts and stock-pool integrity, but
also to sector strength shape and next-session action balance.

What this step focused on:

- extend `_resolve_dynamic_action_focus_overrides(...)` in
  `app.dashboard.streamlit_app` to cover:
  - `strongest_sector`
  - `next_session_action`
- make `strongest_sector` reading anchors vary with current sector shape,
  including lightweight distinctions between:
  - strong momentum with breadth
  - clear strength but narrower follow-through
  - weaker or less decisive main-line clarity
- make `next_session_action` reading anchors vary with current action-tier
  balance, including lightweight distinctions between:
  - avoid-list-first states
  - core-watchlist-first states
  - more balanced tier-review states
- verify the behavior with focused regressions for:
  - strongest-sector dynamic first-read copy
  - next-session-action dynamic first-read copy
  - broader dashboard regression coverage

Current effect:

- the homepage action-summary can now tell the user whether to read the
  strongest sector as:
  - a broad strong main line
  - a narrower strength pocket
  - or a weaker anchor that still needs confirmation
- the homepage action-summary can now also tell the user whether the
  next-session action block should be read from:
  - the avoid list first
  - the core list first
  - or the balance across all three tiers
- this makes the first-screen guidance closer to a real business triage layer
  instead of a static section-order reminder

Later on 2026-07-15, those dynamic first-read rules were moved one layer down
into the dashboard presentation/config surface, so the homepage no longer keeps
all action-focus thresholds and copy decisions hardcoded inside the main
Streamlit logic.

What this step focused on:

- add `build_dynamic_action_focus_specs(...)` in
  `app.dashboard.presentation`
- centralize dynamic first-read thresholds and copy for:
  - `latest_alerts`
  - `stock_pool_health`
  - `strongest_sector`
  - `next_session_action`
- refactor `_resolve_dynamic_action_focus_overrides(...)` in
  `app.dashboard.streamlit_app` so it now:
  - reads rule thresholds from presentation config
  - matches payload state against those rules
  - outputs one shared normalized copy shape
- add a focused regression that confirms the new config layer exposes
  replaceable thresholds and copy fields

Current effect:

- future tuning of "what counts as broad strength", "when avoid comes first",
  or "which warning state should lead the read" can now happen in one
  presentation config surface
- the main dashboard logic is now cleaner because it mostly applies configured
  rules instead of owning all threshold values and wording directly

Later on 2026-07-15, that new dynamic-focus config layer was normalized one
step further into a reusable rule-order and condition-matching template, so
adding future first-read modules no longer requires duplicating one-off branch
logic in the main Streamlit flow.

What this step focused on:

- extend `build_dynamic_action_focus_specs(...)` in
  `app.dashboard.presentation` with:
  - explicit `rule_order`
  - normalized `conditions`
  - optional `match` mode
- refactor `app.dashboard.streamlit_app` so dynamic first-read resolution now
  flows through shared helpers:
  - `_build_dynamic_action_focus_facts(...)`
  - `_resolve_dynamic_action_focus_rule_spec(...)`
  - `_dynamic_action_focus_rule_matches(...)`
  - `_dynamic_action_focus_condition_matches(...)`
- keep current business behavior unchanged while removing most per-module
  custom matching branches from `_resolve_dynamic_action_focus_overrides(...)`
- add a focused regression that confirms rule-order exposure for key modules

Current effect:

- the dynamic first-read layer now has a clearer extension template:
  - define facts
  - declare ordered rules
  - declare matching conditions
  - attach copy
- future modules can join the same system with less risk of logic drift or
  copy/priority mismatch

Later on 2026-07-15, `leader_summary` also joined that same dynamic first-read
rule system, so the homepage can now react not only to alerts, pool health,
sector strength, and next-session action balance, but also to whether leader
continuity still looks concentrated or has narrowed enough to require extra
confirmation.

What this step focused on:

- extend `build_dynamic_action_focus_specs(...)` in
  `app.dashboard.presentation` with `leader_summary` rule config, including:
  - concentrated-state copy
  - narrow-state copy
  - available-state fallback copy
- extend `_build_dynamic_action_focus_facts(...)` in
  `app.dashboard.streamlit_app` so the rule matcher now has normalized facts
  for:
  - `leader_count`
  - `has_data`
- extend the shared condition matcher with `eq` support so narrow one-slot
  leader states can be expressed through config instead of custom branch code
- verify the behavior with focused regressions for:
  - `leader_summary` rule-order exposure
  - narrow leader-state first-read copy

Current effect:

- when only one leader slot remains active, the homepage action-summary can now
  warn that leadership may have narrowed enough to need extra confirmation
- when multiple leader slots remain active, the system can continue treating
  leadership as relatively concentrated and supportive of the current main-line
  read

Later on 2026-07-15, the dynamic first-read system also gained a dedicated
fact-spec registry, so not only rules and copy but also fact extraction now has
its own reusable configuration layer.

What this step focused on:

- add `build_dynamic_action_focus_fact_specs(...)` in
  `app.dashboard.presentation`
- centralize fact-source registration for:
  - `latest_alerts`
  - `stock_pool_health`
  - `strongest_sector`
  - `leader_summary`
  - `next_session_action`
- refactor `_build_dynamic_action_focus_facts(...)` in
  `app.dashboard.streamlit_app` so it now reads:
  - `source_key`
  - `container_transform`
  - `fields`
  - `transform`
  from the new fact-spec registry instead of relying on one hardcoded
  per-module branch per fact set
- add shared helpers for:
  - resolving optional source containers
  - resolving raw fact values
  - applying normalized fact transforms
  - safe float conversion
- verify the behavior with a focused regression that confirms registered
  sources and transforms are exposed in config

Current effect:

- adding a future dynamic first-read module is now closer to a two-surface task:
  - define its facts in the fact-spec registry
  - define its ordered rules in the rule-spec registry
- `streamlit_app.py` now owns less module-specific extraction logic, which
  lowers the chance of future expansion drifting back toward hardcoded branches

Later on 2026-07-15, the dynamic first-read system also received its own
project-side maintenance document, so future extension work no longer depends
on re-reading the implementation files from scratch.

What this step focused on:

- add [app/DYNAMIC_ACTION_FOCUS_SYSTEM.md](/Y:/AI/Codex/Project_Agu_01/app/DYNAMIC_ACTION_FOCUS_SYSTEM.md)
- document:
  - current dynamic modules
  - file map
  - fact-spec structure
  - rule-spec structure
  - supported transform keys
  - supported condition operators
  - step-by-step extension flow
  - practical rule-writing tips
- add a small entry for that guide into [README.md](/Y:/AI/Codex/Project_Agu_01/README.md)

Current effect:

- future work on homepage first-read guidance can start from one focused guide
  instead of rediscovering the system through code inspection
- the dynamic action-focus layer is now easier to hand off, review, and extend

Later on 2026-07-15, the homepage dynamic first-read layer moved one step
closer to real research workflow by using more business-shaped signals inside
`leader_summary` and `next_session_action`, instead of relying only on counts
and generic structural states.

What this step focused on:

- refine `leader_summary` dynamic rule config so it now distinguishes:
  - dual-leader alignment states
  - narrower single-slot continuation states
- refine `next_session_action` dynamic rule config so it now uses the action
  `reason` text itself for more business-shaped first-read guidance, including:
  - `stay with ... first`
  - `reduce names tied to ...`
- extend the fact-spec registry with:
  - `has_trend_leader`
  - `has_emotion_leader`
  - `core_reason_text`
  - `avoid_reason_text`
- extend the shared fact/rule system with:
  - nested `path` extraction
  - `startswith` condition matching
- verify the behavior with focused regressions for:
  - dual leader-alignment copy
  - core stay-with copy
  - avoid reduce copy

Current effect:

- homepage guidance now reacts more like a real research assistant when:
  - both trend and emotion leaders still align
  - only one leader slot remains
  - the next session should keep following one leader set
  - the next session should first shrink exposure to weakening linked names

Later on 2026-07-15, `latest_alerts` also moved one step closer to a real
intraday reading order by distinguishing alert types instead of only reacting
to total alert count and negative-alert count.

What this step focused on:

- refine `latest_alerts` dynamic rule config so it now distinguishes:
  - negative alert states
  - sector-move states
  - materials-focus states
  - news-flash states
  - price-spike states
  - generic active-alert fallback
- extend the fact-spec registry for `latest_alerts` with:
  - list-based source normalization
  - first alert-type extraction
  - per-alert-type counting
- extend the shared fact transform layer with:
  - `normalize_list`
  - `first_item_field_lower`
  - `count_items_with_field_value`
- verify the behavior with focused regressions for:
  - sector-move first-read copy
  - price-spike first-read copy
  - updated alert-rule order exposure

Current effect:

- homepage first-read guidance for alerts now behaves more like a practical
  read order:
  - risk first
  - then sector/theme expansion
  - then materials-chain follow-through
  - then news
- then single-name spikes
- this makes the alert module less like a flat list reminder and more like a
  live market-reading entry point

Later on 2026-07-15, that alert-reading layer was refined again so
`materials_focus` and `news_flash` no longer behave only as flat alert-type
matches, but start to reflect more realistic intraday research actions.

What this step focused on:

- refine `latest_alerts` dynamic rule config so it now distinguishes:
  - materials-chain reinforcement with sector expansion
  - generic materials-chain follow-through
  - risk-driven news disruption
  - generic news-driven confirmation/reprioritization
- update alert rule priority so a risk-driven `news_flash` can override the
  broader negative-alert bucket when that is the more specific first-read
  explanation
- verify the behavior with focused regressions for:
  - materials reinforcement copy
  - risk news-flash copy
  - updated alert-rule order exposure

Current effect:

- homepage alert guidance now behaves more like a real intraday reading script:
  - materials-chain strengthening plus sector expansion is treated as a broader
    main-line reinforcement event
- risk-driven news is treated as a direct priority disruption event instead
  of only as a generic negative alert

Later on 2026-07-15, the homepage dynamic first-read layer was linked more
directly with top-line dashboard conclusions, so the action-summary can now
explain not only which module to read first, but also which top-level summary
currently supports that reading order.

What this step focused on:

- add `_build_priority_action_topline_context_lines(...)` in
  `app.dashboard.streamlit_app`
- thread one shared top-line context line into the action-summary card after
  module-level reading anchors
- map first-read modules to current top-line dashboard summaries, including:
  - `latest_alerts` -> `risk_summary`
  - `strongest_sector` / `leader_summary` / `next_session_action` -> `mainline_summary`
  - `stock_pool_health` -> `stock_pool_drift_summary`
- verify the behavior with focused regressions for:
  - risk-summary context under `latest_alerts`
  - stock-pool-drift context under `stock_pool_health`

Current effect:

- homepage guidance now says not only:
  - first open this module
  - first read these fields
- it can also say:
  - this is the current top-line risk/main-line/stock-pool conclusion that
    explains why this module is first right now

Later on 2026-07-15, those top-line context lines also moved into a dedicated
presentation config surface, so homepage explanation tone can now be adjusted
without editing the main Streamlit helper directly.

What this step focused on:

- add `build_priority_action_topline_specs(...)` in
  `app.dashboard.presentation`
- centralize top-line action-summary context prefixes for:
  - `latest_alerts`
  - `strongest_sector`
  - `leader_summary`
  - `next_session_action`
  - `stock_pool_health`
- refactor `_build_priority_action_topline_context_lines(...)` in
  `app.dashboard.streamlit_app` so it now reads those prefixes from
  presentation config instead of hardcoding them in the view helper
- verify the behavior with a focused regression that confirms those context
  prefixes are exposed as replaceable config

Current effect:

- the action-summary now has one more presentation boundary around its
  top-line explanation layer
- future changes to homepage explanation tone can happen in presentation config
  instead of inside the render helper

Later on 2026-07-16, the README top-level usage path was tightened again so the
main local workflow, news workflow, export workflow, and stored review workflow
now read as one daily operating sequence instead of separate command islands.

What this step focused on:

- add one short `Daily Use Order` section near the top of `README.md`
- connect the current recommended day-to-day local sequence as:
  - `self-check`
  - batch news first pass with `summary-only`
  - higher-priority narrowing with `high-priority-only`
  - optional batch export
  - `latest-review`
- keep the guidance operational and phase-one friendly instead of expanding
  into more dashboard or polish-oriented instructions

Current effect:

- a new user can now open `README.md` and follow one practical daily route
  without having to infer the order across multiple separate sections
- the project entry path is now closer to the real business main line:
  check system health, scan news, keep important output when needed, then read
  the stored market review

Later on 2026-07-16, the batch-news input path was made more explicit so the
user no longer needs to guess the local JSON structure before using the news
screening flow.

What this step focused on:

- add one minimal reusable sample file:
  - `news_batch.example.json`
- add one short `news_batch.json` example block near the top of `README.md`
- state the current minimum batch input rule clearly:
  - JSON array
  - each item has `title`
  - each item has `content`
- keep the example aligned with the actual current phase-one parser instead of
  introducing extra optional fields too early

Current effect:

- the batch news workflow is now easier to start from zero
- the user can copy one ready sample file and quickly replace only the news
  titles and contents
- README guidance and current parser expectations are now directly aligned

Later on 2026-07-16, the same batch-news documentation path was shortened again
into one direct local demo route so the user can move from sample file to real
output without having to piece together the command order manually.

What this step focused on:

- add one short `Fastest local batch-news demo path` block to `README.md`
- reduce the practical first-run route to:
  - copy `news_batch.example.json`
  - run `classify-news-batch "news_batch.json" summary-only`
  - optionally run `export-news-batch "news_batch.json"`
- keep the path intentionally small so it acts as a runnable phase-one usage
  bridge rather than another long command reference section

Current effect:

- the batch-news feature now has a true copy-and-run onboarding path
- a new user can validate the local news workflow with minimal setup and
  minimal command branching

Later on 2026-07-16, the terminal help output was brought back into line with
the README top-level usage order so the user no longer sees one workflow in the
document and a different workflow in the command help.

What this step focused on:

- update `_build_command_help_text()` in `app.main`
- add the same top-level operating order already shown in `README.md`:
  - `self-check`
  - batch first pass with `summary-only`
  - high-priority narrowing
  - optional export
  - `latest-review`
- add the same short `Fastest local batch-news demo path` into terminal help
- extend `tests/test_main.py` so the help output regression now checks those
  aligned entry sections explicitly

Current effect:

- README and terminal help now point the user through the same phase-one usage
  route
- the project’s first-run guidance is more consistent across document and CLI
  surfaces
Later on 2026-07-16, the same terminal help path gained two more concrete
first-run hints so the user can tell both where to place the batch input file
and where to find the default export result.

What this step focused on:

- extend `_build_command_help_text()` with two small operational reminders:
  - keep `news_batch.json` in the project root for the simplest first run
  - exported summary files are saved next to the source batch file by default
- extend `tests/test_main.py` so those two hints stay covered by the help-text
  regression

Current effect:

- the CLI help now answers two common first-use questions directly:
  - where to put the batch source file
  - where the exported summary file will appear

Later on 2026-07-16, the same batch-news onboarding path was made more flexible
by stating explicitly that the input file can stay outside the project root as
long as the full path is passed into the command.

What this step focused on:

- add one short full-path reminder to the top batch-news onboarding text in
  `README.md`
- add the same reminder to `_build_command_help_text()` in `app.main`
- extend `tests/test_main.py` so the CLI help regression covers that reminder

Current effect:

- the user now has both:
  - the simplest root-directory path
  - a flexible full-path alternative when input files live elsewhere

Later on 2026-07-16, the same batch-news onboarding text gained one direct
copyable full-path command example so the user does not have to infer how the
path-based variant should be written.

What this step focused on:

- add one short `Full-path example` block to `README.md`
- keep the example aligned with the current phase-one commands:
  - `classify-news-batch ... summary-only`
  - `export-news-batch ...`
- use one realistic project-local path so the example can be copied with only
  minimal edits

Current effect:

- the README now supports both:
  - concept-level explanation that full paths work
  - direct command examples that can be copied and adjusted quickly

Later on 2026-07-16, the same batch-news README path also started stating more
explicitly where the exported summary file will appear after the command runs.

What this step focused on:

- add one output-location note under the shortest export example in `README.md`
- add one output-location explanation under the full-path example in
  `README.md`
- keep the explanation concrete by showing:
  - the output folder
  - one timestamped filename example

Current effect:

- after copying the command, the user can now also predict where to find the
  generated summary file
- the batch-news onboarding path answers both:
  - how to run the export
  - where the export result will show up

Later on 2026-07-16, the same batch-news README path gained one explicit
fixed-filename export example so the user can choose between automatic
timestamped naming and one manually controlled output filename.

What this step focused on:

- add one fixed-target export example beside the root-path batch export flow in
  `README.md`
- add one fixed-target export example beside the full-path batch export flow in
  `README.md`
- keep the examples aligned with the current CLI behavior instead of describing
  a second export mechanism

Current effect:

- the README now shows both export styles clearly:
  - automatic timestamped output beside the source batch file
  - explicit output filename chosen by the user

Later on 2026-07-16, the same batch-news README path also gained one combined
high-priority export example so the user can move directly from filtered
screening to fixed-name archival without having to infer the argument order.

What this step focused on:

- add one root-path combined example to `README.md`:
  - `export-news-batch`
  - fixed output filename
  - `high-priority-only`
- add the same combined example for the full-path batch file case
- keep the examples aligned with the current CLI argument order already used by
  the app

Current effect:

- the README now covers one more practical batch-news path:
  - filter to higher-priority items
  - save them into one predictable file name

Later on 2026-07-16, the same top README batch-news block was compressed into a
more cheat-sheet-like structure so the user can scan commands faster without
losing the most useful root-path and full-path examples.

What this step focused on:

- rewrite the top batch-news onboarding block in `README.md` into a tighter
  command-reference structure
- keep the same practical cases, but regroup them as:
  - input path
  - first-pass scan
  - default export
  - fixed filename export
  - higher-priority fixed export
  - full-path variants
- reduce repeated sentence-style explanations around those commands

Current effect:

- the README top section now behaves more like a quick-use note sheet
- the user can find the exact batch-news command type faster during normal use

Later on 2026-07-16, the same README cleanup continued by reducing repeated
batch-news explanation between the top cheat-sheet block and the later
`CLI Modes` section.

What this step focused on:

- remove one duplicated daily-use bullet about full-path batch files
- add one short bridge line at the start of `CLI Modes` to clarify:
  - the top `News Commands` block is the fastest batch-news entry path
  - `CLI Modes` stays as the broader command catalog
- rename the repeated batch-news entries in `CLI Modes` into a tighter command
  list style instead of repeating longer tutorial wording

Current effect:

- README now has less repetition between the top quick-use block and the later
  full command section
- the document keeps both:
  - a fast batch-news cheat sheet
  - a broader command reference

Later on 2026-07-16, the same README and CLI-help cleanup also unified the
group names so the user sees the same naming pattern across the document and
the terminal help output.

What this step focused on:

- rename the top README batch-news heading to `Batch-News Cheat Sheet`
- rename the top README daily-flow heading to `Daily Use`
- align `_build_command_help_text()` in `app.main` to the same naming set:
  - `Daily Use`
  - `Batch-News Cheat Sheet`
  - `Full Command Catalog`
- extend `tests/test_main.py` so the help-output regression checks those
  unified section names explicitly

Current effect:

- README and terminal help now describe the same command groups with the same
  labels
- switching between document and CLI surfaces is now a bit more intuitive

Later on 2026-07-16, the same naming cleanup was tightened one more step by
removing a couple of remaining tutorial-style labels and replacing them with
the same short command-group style used elsewhere.

What this step focused on:

- rename the README section `Minimal Runnable Version` to
  `Minimal Runnable Check`
- tighten the batch-news intro line in `README.md` to a shorter command-list
  style
- rename the help section label in `_build_command_help_text()` from
  `Recommended minimal runnable path` to `Minimal Runnable Check`
- extend `tests/test_main.py` so the help-output regression checks that updated
  section name

Current effect:

- README and terminal help now have a more consistent label style overall
- the top-level reading rhythm is closer to one compact quick-reference format

Later on 2026-07-16, the work returned to the business main line by hardening
the batch-news input path itself instead of continuing documentation polish.

What this step focused on:

- add one shared validation layer for batch-news input before classification
  and export
- handle the most common real-use failure cases explicitly:
  - unsupported filter mode
  - invalid JSON syntax
  - top-level JSON is not a list
  - batch items missing `title` or `content`
- prevent `export-news-batch` from writing an output file when the source batch
  input is invalid
- extend `tests/test_main.py` with regression coverage for those invalid-input
  paths

Current effect:

- the batch-news chain is now safer for actual use:
  - bad inputs fail early
  - error messages are clearer
  - invalid exports no longer silently write bad output files
- the mainline CLI path now has stronger protection around user-edited batch
  files

Later on 2026-07-16, the same mainline batch-news path gained one standalone
validation command so the user can check a batch file before running
classification or export.

What this step focused on:

- add `validate-news-batch` to `app.main`
- reuse the same shared batch-input validation layer already used by
  classification and export
- expose the new command in:
  - CLI help output
  - README top batch-news entry path
- extend `tests/test_main.py` to cover:
  - valid batch input
  - missing path
  - invalid batch items

Current effect:

- the batch-news main path now has a cleaner operating sequence:
  validate first, then classify, then export
- user-edited news batch files can be checked independently before entering the
  heavier classification flow

Later on 2026-07-16, that standalone validation step was tightened into a more
practical closed loop by telling the user exactly which command to run next
after the batch file passes validation.

What this step focused on:

- extend `validate-news-batch` success output in `app.main`
- add one direct next-step command for the common first-pass path:
  - `classify-news-batch "news_batch.json" summary-only`
- add one direct optional export command after validation
- extend `tests/test_main.py` so those next-step hints stay covered by
  regression checks

Current effect:

- successful validation now behaves more like an operational handoff instead of
  only a static “valid” status
- the batch-news main path is easier to follow end to end:
  validate, classify, then export if needed

Later on 2026-07-16, the same batch-news main path was extended one step
earlier by adding a template-generation command, so the user no longer has to
manually create the first `news_batch.json` file before entering validation.

What this step focused on:

- add `create-news-batch-template` to `app.main`
- generate one local JSON template file with the same starter examples already
  used in the project documentation
- connect the new command into:
  - CLI help output
  - README top batch-news entry path
- extend `tests/test_main.py` to cover:
  - template file creation
  - missing target path

Current effect:

- the batch-news main path is now closer to a full first-run loop:
  create template, validate input, classify, then export
- a new user can start the batch-news flow without hand-writing the initial
  JSON file

Later on 2026-07-16, that same batch-news first-run loop was shortened further
by adding one one-step first-pass command that validates the file and then
immediately enters the `summary-only` classification view.

What this step focused on:

- add `news-batch-first-pass` to `app.main`
- make it run one shared validate-then-summary path instead of requiring two
  separate manual commands
- expose the new command in:
  - CLI help output
  - README top batch-news entry path
- extend `tests/test_main.py` to cover:
  - successful first-pass execution
  - missing path handling

Current effect:

- the batch-news main path now has a smoother day-to-day shortcut:
  create template, validate, one-step first pass, then deeper classification or export
- ordinary first-pass screening now requires fewer manual command switches

Later on 2026-07-16, the same shortcut path was extended with one one-step
priority-pass command so the user can jump directly into the
`high-priority-only` view after validation.

What this step focused on:

- add `news-batch-priority-pass` to `app.main`
- make it run one shared validate-then-priority path instead of requiring
  separate validation and filtering commands
- expose the new command in:
  - CLI help output
  - README top batch-news entry path
- extend `tests/test_main.py` to cover:
  - successful priority-pass execution
  - missing path handling

Current effect:

- the batch-news main path now has two one-step reading shortcuts:
  - `news-batch-first-pass` for broad first screening
  - `news-batch-priority-pass` for direct priority-only review

Later on 2026-07-16, the same shortcut path was extended again with one
one-step priority-export command so the user can move from validation directly
to a fixed-name high-priority archive file.

What this step focused on:

- add `news-batch-priority-export` to `app.main`
- make it run one shared validate-then-high-priority-export path
- default the export target to one fixed filename beside the source batch file:
  - `news_batch_priority_summary.md`
- expose the new command in:
  - CLI help output
  - README top batch-news entry path
- extend `tests/test_main.py` to cover:
  - successful priority export
  - missing path handling

Current effect:

- the batch-news main path now has a direct archive shortcut for priority-only
  review
- important news can now move from edited batch file to fixed-name saved output
  in one command

Later on 2026-07-16, the same batch-news main path was tightened into one
daily-use combined command so the user can run validation, broad screening, and
priority screening from one entry instead of switching commands manually.

What this step focused on:

- add `batch-news-daily-flow` to `app.main`
- keep the command on the business main line by chaining:
  - shared batch validation
  - `summary-only` first pass
  - `high-priority-only` second pass
- expose the new command in:
  - CLI help output
  - README batch-news quick-use path
- extend `tests/test_main.py` to cover:
  - successful daily-flow execution
  - missing path handling

Current effect:

- the batch-news main path now has a more practical day-to-day operating
  shortcut
- normal usage can now follow one simpler route:
  prepare batch file, run one combined flow, then export priority items only if
  needed

Later on 2026-07-16, that same daily combined path was extended one more step
into a final one-command operating route so the user can both read the batch
flow and save the priority result in a single run.

What this step focused on:

- add `batch-news-daily-export` to `app.main`
- keep the command on the same business main line by chaining:
  - shared batch validation
  - `summary-only` first pass
  - `high-priority-only` second pass
  - fixed-name priority summary export
- expose the new command in:
  - CLI help output
  - README batch-news quick-use path
- extend `tests/test_main.py` to cover:
  - successful daily-export execution
  - missing path handling

Current effect:

- the batch-news main path now has one cleaner end-state command for daily use
- the user can move from edited batch file to read-through plus saved
  high-priority summary without an extra manual export step

Later on 2026-07-16, that same one-command daily export path was tightened with
one more stable archive convention so saved summaries are easier to find and
review across days.

What this step focused on:

- keep `batch-news-daily-export` as the main daily archive entry
- change its default output target from "next to the source file" to one stable
  project-local archive path:
  - `data/news/news_batch_priority_summary_YYYYMMDD.md`
- create the archive directory automatically when it does not exist yet
- allow the default archive directory to be overridden when needed through:
  - `MONITOR_NEWS_DAILY_EXPORT_DIR`
- extend `tests/test_main.py` so the dated archive-path behavior stays covered

Current effect:

- daily exported priority summaries now have a more predictable home inside the
  project
- the archive naming is easier to scan by date during later review

Later on 2026-07-16, the same daily work path was extended one step earlier so
the source batch file can also live in the same fixed work area as the daily
priority archive.

What this step focused on:

- add `create-daily-news-batch` to `app.main`
- make the default source file land in:
  - `data/news/news_batch_YYYYMMDD.json`
- keep support for an explicit custom target path when needed
- create the source directory automatically when it does not exist yet
- reuse `MONITOR_NEWS_DAILY_EXPORT_DIR` so daily source and daily archive stay
  in the same overrideable workspace
- extend `tests/test_main.py` so both:
  - default daily source creation
  - explicit target-path creation
  stay covered

Current effect:

- the daily news source file and the daily priority summary can now live under
  one stable project-local work area
- the day-to-day workflow is closer to one repeatable loop:
  create today's batch file, edit it, then run daily export

Later on 2026-07-16, that same daily work area path was tightened into one
single start command so the user no longer has to decide whether to create
today's source file first or reuse an existing one.

What this step focused on:

- add `start-daily-news-workflow` to `app.main`
- default the command to today's fixed source path:
  - `data/news/news_batch_YYYYMMDD.json`
- if the source file does not exist:
  - create it from the template automatically
- if the source file already exists:
  - reuse it without overwriting user edits
- immediately continue into the existing daily export path after source
  preparation
- extend `tests/test_main.py` so both:
  - first-run auto-create
  - existing-file reuse
  stay covered

Current effect:

- the project now has one cleaner "today start working" command for the
  batch-news main line
- the daily loop is closer to:
  run one command, open today's JSON if needed, then read today's saved
  priority summary

Later on 2026-07-16, the same daily batch-news output path was cleaned up so a
successful run no longer ends with multiple `Usage` lines that look too similar
to an error or failed command hint.

What this step focused on:

- keep `Usage` prompts for real input-missing or validation-error cases
- remove trailing `Usage` lines from successful:
  - embedded batch classification blocks
  - `batch-news-daily-flow`
  - `batch-news-daily-export`
  - `start-daily-news-workflow`
- extend `tests/test_main.py` so successful daily-flow and daily-export paths
  stay protected from those misleading trailing usage lines

Current effect:

- terminal success output now reads more like a finished result and less like a
  partial failure
- the daily workflow is easier to judge at a glance when running it in VS Code

Later on 2026-07-16, the saved daily priority summary file was also upgraded
from a raw classification dump into a more readable markdown note with one
small daily report header.

What this step focused on:

- keep the existing priority-pass body unchanged for compatibility
- add one markdown header block above the saved file content with:
  - report date
  - source batch path
  - total batch items
  - priority items shown
  - impact summary
- extend `tests/test_main.py` so the saved markdown header stays covered

Current effect:

- opening the saved `.md` file now feels closer to reading a small finished
  daily summary instead of only a raw export block

Later on 2026-07-16, that saved markdown summary gained one more top-level
reading aid: a short daily conclusion block placed above the detailed priority
pass.

What this step focused on:

- add one `Daily Conclusion` section to the saved daily priority markdown
- keep the rule explicit and compact by deriving the conclusion from the
  priority-pass impact distribution
- current conclusion styles now distinguish between:
  - risk-first
  - mainline-first
  - observation-first
  - balanced tracking
- extend `tests/test_main.py` so the saved markdown conclusion stays covered

Current effect:

- opening the saved daily summary now answers "today is more risk, more
  reinforcement, or more balanced?" before reading the item list

Later on 2026-07-16, the saved daily markdown summary also gained one dedicated
suggested-actions section so the user can see today's concrete follow-up items
before reading the longer priority-pass body.

What this step focused on:

- add one `Suggested Actions` section to the saved daily priority markdown
- derive the action bullets directly from the rendered high-priority entries so
  the exported file stays aligned with the existing rule-based output
- keep the actions close to the current item titles instead of producing a
  second unrelated summary wording layer
- extend `tests/test_main.py` so the saved action section stays covered

Current effect:

- opening the saved daily summary now surfaces both:
  - today's top-line conclusion
  - today's concrete follow-up actions
  before the detailed item list

Later on 2026-07-16, that suggested-actions block was also split into clearer
working groups so the saved daily summary reads more like an actual task list.

What this step focused on:

- group saved action bullets by their current explicit signal type:
  - risk-priority actions
  - reinforcement follow-up actions
  - observation/verification actions
- keep the grouping logic tied to the existing bottom-line wording so it stays
  readable and easy to trace
- extend `tests/test_main.py` so the grouped action section stays covered

Current effect:

- the saved daily summary now separates "handle risk first" from "track
  reinforcement" more clearly

Later on 2026-07-16, the same daily summary header gained one more compressed
reading layer: a short watchlist section that pulls the main stock names to
track closer to the top.

What this step focused on:

- add one `Watchlist` section to the saved daily priority markdown
- extract watchlist names directly from the existing suggested-action wording
  instead of introducing a second independent stock-picking rule
- group the names by the same explicit action buckets already used above:
  - risk-priority names
  - reinforcement follow-up names
  - observation/verification names
- de-duplicate repeated names so the short watchlist stays compact
- extend `tests/test_main.py` so the saved watchlist section stays covered

Current effect:

- opening the saved daily summary now shows the main names to watch before the
  longer suggested-action paragraphs

Later on 2026-07-16, the same summary header gained one more compressed cue: a
single operation-tip line that tells the user which list to read first.

What this step focused on:

- add one `Operation Tip` section above the watchlist
- keep the rule explicit and easy to trace:
  - if risk names exist, read risk first
  - otherwise if reinforcement names exist, read reinforcement first
  - otherwise read observation names first
- extend `tests/test_main.py` so the saved operation tip stays covered

Current effect:

- the saved daily summary now answers not only "what are today's names" but
  also "which list should I look at first"

Later on 2026-07-16, the same summary header gained one more compact reading
cue: a small theme-tags block that labels the day with a few short monitoring
tags.

What this step focused on:

- add one `Theme Tags` section near the top of the saved daily summary
- derive the tags from the existing impact distribution instead of introducing
  a second separate classification path
- current tag outputs can include short labels such as:
  - risk expansion
  - mainline reinforcement
  - observation/verification
  - balanced tracking
- extend `tests/test_main.py` so the saved theme-tag output stays covered

Current effect:

- the saved daily summary now lets the user judge the overall day type in a few
  words before reading the longer conclusion and action sections

Later on 2026-07-16, the same summary header gained one more fast-scanning cue:
an explicit textual status-color line.

What this step focused on:

- add one `Status Color` section near the top of the saved daily summary
- keep the mapping explicit and lightweight:
  - red for risk-dominant days
  - green for mainline-dominant days
  - yellow for observation-dominant days
  - orange for balanced tracking days
  - gray for ordinary low-signal days
- extend `tests/test_main.py` so the saved status-color output stays covered

Current effect:

- the saved daily summary now gives one even faster top-line read before the
  theme tags, conclusion, and action sections

Later on 2026-07-16, the same summary header gained one more fast business cue:
an explicit defense-status line.

What this step focused on:

- add one `Defense Status` section near the top of the saved daily summary
- keep the rule explicit and lightweight:
  - risk-dominant days -> defense first
  - mainline-dominant days -> follow-up first
  - mixed days -> defend and follow in parallel
  - observation-only days -> wait for clearer confirmation
- extend `tests/test_main.py` so the saved defense-status output stays covered

Current effect:

- the saved daily summary now answers "do I need to defend first today?" before
  the user reads the detailed lists

Later on 2026-07-16, the same summary header gained one more compressed top
line: a single core-summary sentence that combines the day color, theme tags,
and defense judgment.

What this step focused on:

- add one `Core Summary` section near the top of the saved daily summary
- compress three existing header cues into one line:
  - status color
  - theme tags
  - defense status
- keep the content fully derived from existing summary rules rather than adding
  a new judgment path
- extend `tests/test_main.py` so the saved core-summary line stays covered

Current effect:

- the saved daily summary now gives one fastest-possible top-line reading
  sentence before the more detailed header sections

Later on 2026-07-16, the same summary header gained one more non-technical top
cue: a short one-line advice sentence.

What this step focused on:

- add one `One-Line Advice` section near the top of the saved daily summary
- keep the wording shorter and more conversational than the detailed
  conclusion, so a non-technical reader can scan it quickly
- derive the sentence from the same explicit impact-distribution rules already
  used by the summary
- extend `tests/test_main.py` so the saved one-line advice stays covered

Current effect:

- the saved daily summary now offers one even simpler first-read suggestion
  before the more structured sections

Later on 2026-07-16, the same daily-summary header was tightened again to
reduce repeated top sections once the compressed core-summary line was already
in place.

What this step focused on:

- keep `Core Summary` as the compressed top-line combination of:
  - status color
  - theme tags
  - defense status
- remove the now-redundant separate header sections for:
  - `Status Color`
  - `Defense Status`
  - `Theme Tags`
- keep the shorter `One-Line Advice`, `Daily Conclusion`, `Processing Order`,
  `Watchlist`, and `Suggested Actions` sections unchanged
- extend `tests/test_main.py` so the compacted header structure stays covered

Current effect:

- the saved daily summary header now feels tighter and less repetitive while
  keeping the same core judgment information

Later on 2026-07-16, the saved daily summary was also tightened one step lower
by making the `Priority Pass` detail block look more like a real markdown
document instead of a raw console dump.

What this step focused on:

- keep the same priority-pass information content
- reformat the saved section into markdown-style structure:
  - summary lines become bullets
  - each priority item becomes its own `###` subsection
  - item facts and bottom-line guidance become bullets under that subsection
- leave the terminal-facing batch output unchanged so the current runnable path
  stays stable
- extend `tests/test_main.py` so the saved markdown detail structure stays
  covered

Current effect:

- the saved daily summary now reads more consistently from top to bottom as one
  markdown note rather than switching back into plain console formatting at the
  end

Later on 2026-07-17, the saved daily summary also gained one short file-header
description line, and the date-bound tests around the daily news workflow were
made resilient to the current day changing.

What this step focused on:

- add one plain-language file-header description directly under
  `# Daily News Priority Summary`
- replace fixed `20260716` / `2026-07-16` expectations in daily-workflow tests
  with same-day dynamic date generation
- keep the business behavior unchanged while preventing date rollover from
  causing false test failures

Current effect:

- first-time readers can tell what the saved markdown file is immediately
- the daily-workflow regression suite is now safer across day changes

Later on 2026-07-17, the README examples were also cleaned up so example
filenames no longer look tied to one expired specific day.

What this step focused on:

- replace fixed example dates in `README.md` such as:
  - `20260716`
  - `20260716_093000`
- switch those examples to reusable placeholders such as:
  - `YYYYMMDD`
  - `YYYYMMDD_HHMMSS`

Current effect:

- the README now reads more like a reusable operating guide instead of a note
  frozen to one past date

Later on 2026-07-16, the same summary header gained one more execution-facing
cue: a short numbered processing-order block.

What this step focused on:

- add one `Processing Order` section near the top of the saved daily summary
- derive the order from the same watchlist buckets already used elsewhere
- keep the sequence explicit and short, so the file can tell the user which
  list to read first without scanning the longer sections below
- extend `tests/test_main.py` so the saved processing-order output stays
  covered

Current effect:

- the saved daily summary now says not only what the day looks like, but also
  the order in which to process the main lists

Later on Friday, July 17, 2026, the top `README.md` daily-use path was also
compressed into a cleaner 3-step version so the document matches the current
mainline workflow more closely.

What this step focused on:

- replace the older longer daily-use path in `README.md`
- center the new short path on:
  - `python -m app.main self-check`
  - `python -m app.main start-daily-news-workflow`
  - `python -m app.main latest-review`
- keep the longer manual batch-news command set available elsewhere in the
  document for users who want finer control

Current effect:

- the README now points new daily use toward the current one-command batch-news
  flow instead of the older multi-command screening path

Later on Friday, July 17, 2026, the top `README.md` also gained one even
shorter recommended-entry hint so a first-time reader can see the current daily
path before entering the longer sections below.

What this step focused on:

- add one compact `Recommended daily entry` line near the top of `README.md`
- keep the hint aligned with the current 3-step main path:
  - `self-check`
  - `start-daily-news-workflow`
  - `latest-review`

Current effect:

- the top of the README now surfaces the current daily path with less scanning

Later on Friday, July 17, 2026, the top `README.md` was further compressed so
the quick-start and minimal-check sections no longer repeat the same idea too
many times.

What this step focused on:

- tighten the wording in `README.md` under `Minimal Runnable Check`
- keep the one-command `self-check` entry as the first obvious option
- preserve the manual 3-step acceptance path while reducing duplicate phrasing

Current effect:

- the README top section is easier to scan and better matches the current
  runnable mainline

Later on Friday, July 17, 2026, the daily batch-news path was also checked for
one more kind of consistency: README wording, help-text wording, and actual
default output rules now describe the same split between daily workflow export
and generic export.

What this step focused on:

- clarify that `create-daily-news-batch`, `batch-news-daily-export`, and
  `start-daily-news-workflow` use the fixed daily `data/news/` naming rule
- clarify that `export-news-batch` is the separate generic export command that
  defaults to saving beside the source batch file
- align the command help text and `README.md` notes with that distinction

Current effect:

- the project's main daily workflow is easier to follow without mixing it up
  with the generic export path

Later on Friday, July 17, 2026, the terminal entry for
`start-daily-news-workflow` was also made more first-read friendly without
changing the underlying workflow logic.

What this step focused on:

- add one short `Today First Read` block at the top of
  `start-daily-news-workflow`
- surface the daily source file, the saved summary file, and a plain reading
  order before the longer detailed export output
- keep the full detailed `Batch-News Daily Export` output below for users who
  still want the complete classification view

Current effect:

- after running the one-command daily workflow, the user can immediately see
  what to open first and what to read next, instead of starting from the full
  detailed output

Later on Friday, July 17, 2026, `self-check` was also aligned with the same
daily mainline so the first acceptance step no longer points only to the local
dashboard.

What this step focused on:

- change the `self-check` ending prompt from a dashboard-only next step to the
  current daily workflow entry
- make `python -m app.main start-daily-news-workflow` the primary next step
- keep the Streamlit dashboard available as an optional visual page instead of
  the main recommended follow-up

Current effect:

- the project now has one clearer day-to-day path:
  `self-check` -> `start-daily-news-workflow` -> optional dashboard / latest review

Later on Friday, July 17, 2026, `latest-review` was also given one short
read-before-use hint so the stored review output matches the same daily usage
sequence as the other two main entry points.

What this step focused on:

- add a compact `Review Use Hint` block above `latest-review`
- explain that the stored review is best read after
  `python -m app.main start-daily-news-workflow`
- keep the original stored review body unchanged below the new hint

Current effect:

- the three main daily entry points now point to one clearer sequence:
  `self-check` -> `start-daily-news-workflow` -> `latest-review`

Later on Friday, July 17, 2026, the top of `README.md` was also adjusted so
the first screen matches the same daily-entry order already used in terminal
output hints.

What this step focused on:

- add one short meaning guide below the top recommended daily entry
- clarify that `latest-review` is the stored wrap-up read mode after the daily
  news pass, not the first action of the day
- keep the separate `Minimal Runnable Check` section as an acceptance path
  rather than the daily-usage path

Current effect:

- the first screen of the README now matches the terminal-guided mainline more
  closely

Later on Friday, July 17, 2026, the `help` command was also simplified so its
top `Daily Use` block now mirrors the same three-step mainline used elsewhere.

What this step focused on:

- compress the `Daily Use` section in command help into:
  `self-check` -> `start-daily-news-workflow` -> `latest-review`
- keep `create-daily-news-batch` as a secondary helper entry instead of a main
  daily step
- leave the fuller batch-news command set in `Batch-News Cheat Sheet` and
  `Full Command Catalog`

Current effect:

- README, terminal entry hints, and the top section of `help` now point to the
  same day-to-day operating path

Later on Friday, July 17, 2026, the daily priority-summary markdown path was
also repaired for a real mainline issue: the balanced-branch daily summary had
badly encoded Chinese phrases in several helper text builders.

What this step focused on:

- override the affected daily-summary helper functions with clean Chinese text
  for balanced, risk-first, and mainline-first branches
- keep watchlist extraction, action grouping, operation tip, and processing
  order aligned with the same corrected wording
- add one dedicated regression test for the balanced
  `风险扩散 1 | 主线强化 1 | 局部验证 1` branch

Current effect:

- `start-daily-news-workflow` still runs the same main path, but the saved
  `news_batch_priority_summary_YYYYMMDD.md` content now stays readable in the
  balanced daily-summary branch as well

Later on Friday, July 17, 2026, the README daily-use section was also tightened
into a more delivery-style "today use" description so the user can see not only
which commands to run, but also which files will appear and which one to read
first.

What this step focused on:

- expand `README.md` `Daily Use` with one clearer read-order block
- list the default daily files created or reused by
  `start-daily-news-workflow`
- make the generated summary file the explicit first file to open after the
  daily workflow runs

Current effect:

- a first-time user can now follow the README daily path without guessing which
  output file matters most after the command finishes

Later on Friday, July 17, 2026, the realtime quote fallback path was also
cleaned up for delivery use: when `akshare` is not installed, the main runnable
path no longer prints a warning-looking line during ordinary local use.

What this step focused on:

- keep the fallback to local demo quotes when `akshare` is missing
- silence the warning-level console noise for the specific missing-`akshare`
  case while preserving warning logs for other fetch failures
- add one regression test to lock that behavior in place
- document in `README.md` that missing realtime quotes still allows the local
  runnable path to complete

Current effect:

- `self-check` now reads more like a clean successful acceptance run instead of
  a mixed success-plus-warning terminal output

Later on Friday, July 17, 2026, the README daily-use path was given one more
delivery-style layer: a short "what success looks like" checklist for the
mainline commands.

What this step focused on:

- add success markers for `self-check`
- add success markers and saved-file cues for
  `start-daily-news-workflow`
- make the first file to open after a successful daily run explicit in README

Current effect:

- a first-time user can now judge a successful run by terminal cues and output
  files, not just by remembering the command order

Later on Friday, July 17, 2026, the `help` command was also given the same
success-signal layer so users who stay in the terminal do not have to switch to
README to know whether the mainline commands completed correctly.

What this step focused on:

- add a short `Success Signals` block to command help
- mirror the same successful-run cues already documented in README
- include both terminal cues and the first generated file to open after the
  daily workflow

Current effect:

- README and `python -m app.main help` now describe the same success markers
  for the day-to-day mainline

Later on Friday, July 17, 2026, the day-to-day runnable path also gained one
true end-to-end regression test so the three-step mainline is now protected as
one connected flow, not only as separate command checks.

What this step focused on:

- add one `tests.test_main` end-to-end regression that runs:
  `self-check` -> `start-daily-news-workflow` -> `latest-review`
- assert both terminal guidance and generated daily files across that sequence
- keep the test grounded in the current daily workspace naming rules

Current effect:

- the current delivery mainline is now checked as one usable daily chain, not
  just as isolated command outputs

Later on Friday, July 17, 2026, that same mainline was also exposed as one
compact CLI command so local acceptance no longer requires manually running the
three steps every time.

What this step focused on:

- add `python -m app.main mainline-smoke-test`
- make it run a compact acceptance chain around:
  `self-check` -> `start-daily-news-workflow` -> `latest-review`
- keep its output short and status-oriented instead of printing the full long
  report bodies again
- add test coverage and README mention for the new shortcut

Current effect:

- there is now a faster one-command way to verify the current daily mainline is
  still usable end to end

Later on Friday, July 17, 2026, the project was also checked with a full test
discovery run instead of only module-level targeted tests.

What this step focused on:

- verify the whole `tests/` suite with explicit discovery:
  `python -m unittest discover -s tests -p "test_*.py"`
- note that plain `python -m unittest` currently returns `NO TESTS RAN` in this
  project layout, so full regression should use discovery mode

Current effect:

- the current codebase passed the full discovered regression suite, and future
  full checks now have one clear command path

Later on Friday, July 17, 2026, that full regression path was also turned into
one compact in-project CLI command so users do not need to remember the longer
test discovery parameters.

What this step focused on:

- add `python -m app.main full-regression-check`
- keep its output compact with pass/fail counts and the discovered runner mode
- suppress incidental test-warning noise so the command reads like a clean
  delivery-style regression summary

Current effect:

- both the daily mainline and the full discovered regression suite now have
  one-command acceptance entry points

Later on Friday, July 17, 2026, the README was also aligned with those two
acceptance shortcuts so they are visible without needing to rely on chat memory
or command-help discovery.

What this step focused on:

- surface `mainline-smoke-test` and `full-regression-check` together near the
  top of `README.md`
- add one small acceptance-shortcuts block in the README CLI section
- clarify the difference between the daily-chain shortcut and the full-suite
  regression shortcut

Current effect:

- the two fastest acceptance entry points are now documented in the same place
  as the rest of the delivery-facing usage path

Later on Friday, July 17, 2026, those same acceptance shortcuts were also
given lightweight local PowerShell wrappers so terminal use in VS Code can be a
little shorter and more repeatable.

What this step focused on:

- add `scripts/run_mainline_smoke_test.ps1`
- add `scripts/run_full_regression_check.ps1`
- document the script shortcuts in `README.md` alongside the matching Python
  command forms

Current effect:

- the project now has both Python-command and local-script entry points for the
  two main acceptance checks

Later on Friday, July 17, 2026, those two PowerShell shortcut scripts were also
made more robust for the current Windows environment after a real validation
showed that neither `python` nor `py` was available on PATH.

What this step focused on:

- make the script shortcuts try `python` first
- fall back to `py -3` if available
- fall back again to the local Codex runtime Python path when needed
- document that interpreter lookup behavior in `README.md`

Current effect:

- the script shortcuts are now much more likely to run successfully on this
  machine without requiring extra PATH setup first

Later on Friday, July 17, 2026, those same PowerShell shortcuts were also
re-tested after the interpreter-resolution fix and both actually ran
successfully on this machine.

What this step focused on:

- fix one PowerShell return-shape bug that caused the interpreter path to be
  treated like a plain string and reduced to the leading `C`
- re-run `scripts/run_mainline_smoke_test.ps1`
- re-run `scripts/run_full_regression_check.ps1`

Current effect:

- the local script shortcuts are now not only documented and more robust in
  theory, but also verified working end to end on this Windows setup

Later on Friday, July 17, 2026, the local script shortcuts were also reordered
to prefer the already verified Codex runtime Python path first.

What this step focused on:

- change all local PowerShell script launchers to try the verified Codex
  runtime interpreter before PATH-based `python` or `py`
- keep PATH-based lookup only as fallback instead of first choice
- document that preference in `README.md`

Current effect:

- on this Windows machine, the script shortcuts should now behave much more
  consistently with the manually verified direct interpreter command

Later on Friday, July 17, 2026, the real-quote path was also pushed one step
forward: `akshare` was installed successfully into the verified local Python
runtime, but the machine still failed to reach the Eastmoney quote endpoint.

What this step focused on:

- install `akshare` into the Codex runtime Python environment
- re-run `self-check` with the verified interpreter path
- confirm that import-level dependency setup is now complete
- identify that the remaining blocker is network/socket access, not missing
  Python packages

Current effect:

- the project has moved from "missing akshare" to "akshare installed but
  realtime quote endpoint blocked", so the next real blocker is external
  connectivity rather than project code or package setup

Later on Saturday, July 18, 2026, the project also gained one direct
connectivity-diagnosis command for the realtime quote path.

What this step focused on:

- add `python -m app.main quote-connectivity-check`
- make it distinguish between missing `akshare`, blocked network access, and a
  seemingly ready realtime quote path
- cover the main branches with command-level tests

Current effect:

- the next time realtime quotes fall back to demo data, the user can run one
  command and see whether the blocker is dependency setup or endpoint access

Later on Friday, July 17, 2026, the project also gained a first local VS Code
task layer so the most common acceptance and daily-use entries can be run from
the editor without retyping commands.

What this step focused on:

- add `.vscode/tasks.json`
- wire one task for the mainline smoke test
- wire one task for the full regression check
- wire one task for the daily news workflow
- mention the task labels in `README.md`

Current effect:

- the project now has command, script, and VS Code task entry points for its
  most common local run paths

Later on Friday, July 17, 2026, the project also gained a VS Code Run/Debug
layer so the same mainline actions can be launched from the editor sidebar
without manual terminal input.

What this step focused on:

- add `.vscode/launch.json`
- wire Run/Debug entries for `self-check`
- wire Run/Debug entries for `mainline-smoke-test`
- wire Run/Debug entries for `start-daily-news-workflow`
- wire Run/Debug entries for `latest-review`
- wire Run/Debug entries for `full-regression-check`

Current effect:

- the project now has command, script, task, and Run/Debug entry points for
  the main local usage path

Later on Friday, July 17, 2026, the VS Code setup also gained a lightweight
extension recommendation layer so a first-time local open is more likely to
have the needed Python run/debug support immediately available.

What this step focused on:

- add `.vscode/extensions.json`
- recommend `ms-python.python`
- recommend `ms-python.debugpy`
- mention those recommendations in `README.md`

Current effect:

- the project now guides local VS Code setup not only through tasks and launch
  entries, but also through the most relevant extension recommendations

Later on Friday, July 17, 2026, the top of `README.md` was also compressed into
one shorter first-read path so a new user can start using the project from the
first screen with less scanning.

What this step focused on:

- add a `3-Minute Start` block near the top of `README.md`
- put the three most important commands into one short runnable sequence
- surface the first success cue and the first output file to open

Current effect:

- the first screen of the README now behaves more like a quick-start card than
  a long reference list

Later on Friday, July 17, 2026, the VS Code layer was also given Python testing
defaults that match the current project layout.

What this step focused on:

- add `.vscode/settings.json`
- preconfigure VS Code Python testing for `unittest`
- point discovery at `tests/` with the `test_*.py` pattern
- add the workspace folder as an analysis extra path

Current effect:

- VS Code can now discover this project's tests with the same layout we already
  use for command-line full regression checks

Later on Friday, July 17, 2026, the VS Code task entry for the daily news
workflow was also aligned with the newer script-based Python lookup path.

What this step focused on:

- add `scripts/run_start_daily_news_workflow.ps1`
- switch the VS Code task `Project: Start Daily News Workflow` away from a
  hardcoded interpreter path
- keep the task behavior aligned with the more robust script shortcut pattern

Current effect:

- the daily workflow task in VS Code now follows the same interpreter fallback
  logic as the other local PowerShell shortcuts

Later on Friday, July 17, 2026, that same daily-workflow PowerShell shortcut
was also re-run directly after the task-alignment change.

What this step focused on:

- 执行 `scripts/run_start_daily_news_workflow.ps1` 做一次真实本地检查
- 确认脚本仍会复用当天批量新闻文件，并正常重写当日优先级摘要
- 再次确认 `README.md` 与 `.vscode/tasks.json` 指向的是同一条脚本入口

当前效果：

- 日常新闻工作流现在已经具备经过验证的 Python 命令、PowerShell 脚本和 VS Code 任务入口，并且三者保持一致

随后在 2026 年 7 月 17 日（周五），又继续补齐了另外两个高频日常入口，让本地脚本层和 VS Code 任务层更对称。

这一步主要做了：

- 新增 `scripts/run_self_check.ps1`
- 新增 `scripts/run_latest_review.ps1`
- 新增 `Project: Self Check` 任务
- 新增 `Project: Latest Review` 任务
- 在 `README.md` 中补充这两个脚本和任务入口说明

当前效果：

- 脚本、任务、Run/Debug 三层现在都暴露了同一套核心本地入口：
  `self-check`、`mainline-smoke-test`、`start-daily-news-workflow`、`latest-review`、`full-regression-check`

随后在 2026 年 7 月 18 日（周六），实时行情链路也升级了，目标是降低对 AKShare 单一路径不稳定性的依赖。

这一步主要做了：

- 在 `app/data_sources/akshare_client.py` 中加入“监控池定向直连”的实时行情适配层
- 保持下游使用的标准化行情字段结构不变
- 给行情结果附带来源标记，让主流程能区分 `eastmoney-direct`、`akshare`、`demo-fallback`
- 更新 `quote-connectivity-check`，让它报告真实可用来源，而不只是检查 AKShare 是否安装
- 补充对应回归测试，覆盖直连回退和连接诊断输出

当前效果：

- 代码层已经支持双通道实时行情：
  监控池定向 Eastmoney 直连优先，AKShare 次之
- `tests.test_akshare_client`、`tests.test_main`、`tests.test_pipeline` 在这次改动后能一起通过
- 在这台机器上，终端层面对 Eastmoney 的手工直连测试成功，但 Python 层最初仍有间歇性断连或代理式报错，因此系统依然保留了回退到演示数据的能力
- `README.md` 已经补充新的实时行情链路顺序，以及如何解读 `quote-connectivity-check`

随后在 2026 年 7 月 18 日（周六）稍晚，又通过切换到已在终端手工验证过的 Windows PowerShell `Invoke-WebRequest` 路径，稳定了这台机器上的直连实时行情链路。

这一步主要做了：

- 在 `app/data_sources/akshare_client.py` 中，把 PowerShell 请求路径放到 curl/urllib 之前
- 在真实机器环境下重新执行实时行情连通性检查
- 重新执行主线 `self-check`
- 确认修复后每日新闻工作流仍能正常完成

当前效果：

- `python -m app.main quote-connectivity-check` 现在会返回
  `Endpoint access: ok` 和 `Quote source: eastmoney-direct`
- `python -m app.main self-check` 现在会显示 `Quote source: eastmoney-direct`
- `python -m app.main start-daily-news-workflow` 已正常完成，并生成
  `data/news/news_batch_priority_summary_20260718.md`
- 项目已经回到业务主线，且当前机器上已具备真实监控池行情接入能力
随后在 2026 年 7 月 18 日（周六）下午，首页主线又往前推进了一步，把“当天新闻优先级摘要”正式接进了 Dashboard 首屏。
这一步主要做了：

- 在 `app/dashboard/overview.py` 中新增对 `data/news/news_batch_priority_summary_YYYYMMDD.md` 的读取与解析
- 把解析结果整理成稳定的 `today_priority_summary` 载荷，供首页直接复用
- 在 `app/dashboard/presentation.py` 中新增可替换内容模块 `today_priority_summary`
- 把首页优先区顺序改成更贴近业务主线的结构：先看当日优先摘要，再看股票池健康度和下一交易时段动作摘要
- 在 `app/dashboard/streamlit_app.py` 中新增对应的分组摘要渲染逻辑
- 补齐 `tests/test_dashboard.py`、`tests/test_dashboard_presentation.py`、`tests/test_dashboard_streamlit.py` 的回归测试

当前效果：

- 首页现在已经具备“先看今天新闻优先级，再进入监控与动作判断”的首屏业务入口
- 新模块沿用现有的“数据层 / 内容规格层 / 渲染层”分离方式，后面继续换文案、换顺序、换样式都不会影响主流程
- 这一轮相关测试已通过：`tests.test_dashboard`、`tests.test_dashboard_presentation`、`tests.test_dashboard_streamlit`

随后在 2026 年 7 月 18 日（周六）傍晚，首页动作引导逻辑也同步升级了，不再只是“展示当日优先摘要”，而是会把它纳入首看路径判断。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中补充 `daily_priority_review`、`daily_priority_risk_review` 两个动作场景
- 给 `today_priority_summary` 增加顶层结论标签、动态聚焦规则和动作事实提取配置
- 在 `app/dashboard/streamlit_app.py` 中更新场景判断逻辑：当 `today_priority_summary.shown_items > 0` 时，优先进入“当日优先摘要首读”或“当日优先摘要风险复核”
- 更新首看模块排序，让系统在有当日摘要时优先把 `today_priority_summary` 放到动作摘要引导链路前面
- 补齐 `tests/test_dashboard_streamlit.py` 中关于新场景、新顺序和新提示文案的回归测试

当前效果：

- 首页动作摘要现在会真正提示“先读当日优先摘要，再看哪一块”
- 如果当天有风险提醒，系统会切换成“先读摘要，再核对风险提醒”的顺序
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）晚上，首页动作摘要的呈现方式也进一步改成了更直观的“分步式提示”。
这一步主要做了：

- 把 `app/dashboard/streamlit_app.py` 里的动作模块提示从 “Primary module / Follow-up module” 调整为 “Step 1 / Step 2”
- 中文业务视图同步改成 “第 1 步 / 第 2 步 / 第 1 步位置 / 第 2 步位置” 的表达
- 保持原有的场景判断、风险优先、当日优先摘要优先等业务逻辑不变，只优化首页动作摘要的阅读体验
- 更新 `tests/test_dashboard_streamlit.py` 中与首页动作摘要、首页头部渲染相关的断言

当前效果：

- 首页动作摘要现在更像可直接执行的操作指引，而不只是说明性文案
- 用户打开页面后，可以更快识别“先看哪里、再看哪里、这些模块位于首页哪个位置”
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜前，首页“第 1 步 / 第 2 步”对应模块又补上了更明显的视觉高亮。
这一步主要做了：

- 在 `app/dashboard/streamlit_app.py` 中把首页首看模块标签从旧的 `Primary focus / Follow-up focus` 升级为更明确的 `Step 1 focus / Step 2 follow-up`
- 新增首页优先模块的标题色覆盖逻辑：第 1 步模块用更强的 `accent`，第 2 步模块用 `warning`
- 保持现有页面结构不变，只强化首页首看模块在内容标题层的辨识度
- 更新 `tests/test_dashboard_streamlit.py` 中与焦点标签、标题高亮、页面渲染有关的回归测试

当前效果：

- 首页现在不仅会告诉用户“先看哪里、再看哪里”，还会在对应模块标题上直接做更明显的视觉强调
- 这让首页从“有阅读说明”进一步变成“说明和视觉焦点一致”的状态
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页首看模块内部的第一段核心内容也补上了更明确的高亮入口。
这一步主要做了：

- 在 `app/dashboard/streamlit_app.py` 中为 grouped summary 的第一段分组标题增加可选高亮能力
- 当某个模块属于首页“Step 1 focus / Step 2 follow-up”时，不仅模块标题会高亮，模块内部第一段核心分组标题也会同步强调
- 这样像“当日优先摘要”的“核心摘要:”这类第一段内容，会在首看模块里更容易被第一眼识别
- 更新 `tests/test_dashboard_streamlit.py` 中与 grouped summary、info block、首看模块内部高亮相关的回归测试

当前效果：

- 首页主线已经从“知道先看哪个模块”推进到“进入模块后也更容易抓住第一段关键内容”
- 这让首页的阅读路径更接近真正的业务决策顺序，而不是只在模块层面做提示
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要里的“第 1 步 / 第 2 步”又进一步补成了可点击跳转。
这一步主要做了：

- 在 `app/dashboard/streamlit_app.py` 中为首页内容模块补充 section anchor id，让内容区可以作为跳转落点
- 给首页动作摘要里的第 1 步和第 2 步增加跳转链接，点击后可直接跳到对应模块
- 保持现有业务判断、模块排序、视觉高亮逻辑不变，只增强首页阅读路径的落地操作性
- 更新 `tests/test_dashboard_streamlit.py`，补充英文跳转文案、中文跳转文案和锚点落点的回归测试

当前效果：

- 首页动作摘要不再只是“告诉你先看哪里”，而是可以直接“点过去看哪里”
- 这让首页从“阅读指引”进一步变成“可执行入口”，更贴近真实的盘前/盘后快速浏览路径
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要的跳转又从“模块级”细化成了“模块内第一段核心分组级”。
这一步主要做了：

- 在 `app/dashboard/streamlit_app.py` 中新增首页内容模块首组锚点规则，给 grouped 类型模块补充 `primary` 落点
- 首页动作摘要里的第 1 步 / 第 2 步跳转，优先落到模块内第一段核心分组；不支持细分组的模块仍保留落到模块头部的兼容逻辑
- 在 grouped summary 渲染链路里，把第一段分组标题前插入稳定锚点，保证“跳过去”能真正落在核心摘要、首个预警分组、首个动作分组附近
- 更新 `tests/test_dashboard_streamlit.py`，补充英文/中文精准跳转、首组锚点、模块锚点共存的回归测试

当前效果：

- 首页动作摘要现在更接近真实使用路径，点击后能更快落到“先读的那一段”，不需要再手动往下找模块内第一组内容
- 这让首页从“可点击模块导航”进一步升级成“可点击核心阅读入口”
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要里的“步骤 / 位置 / 跳转”文案也被抽成了可替换模板层。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中新增 `build_priority_action_module_copy_specs()`，集中管理首页动作摘要里的第 1 步、第 2 步、位置、跳转按钮等文案模板
- 在 `app/dashboard/streamlit_app.py` 中让 `_build_action_module_lines()` 和 `_build_action_anchor_link()` 改为从这份配置读取文案，而不是继续把句式硬写在渲染函数里
- 保持当前页面显示结果不变，只把文案出口从“渲染逻辑硬编码”迁移到“展示层配置”
- 更新 `tests/test_dashboard_streamlit.py`，新增动作摘要模块文案模板配置的回归测试

当前效果：

- 首页“第 1 步 / 第 2 步 / 位置 / 跳转”现在已经和卡片标题、图表标题、空态文案一样，进入了统一的可替换展示配置体系
- 后面如果要统一改成更偏业务口径、更偏盘前盘后口径，或者做不同视图语气差异，只需要改配置，不需要再碰主渲染逻辑
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要里“模块先看 / 首看字段 / 首看分组 / 首看结论”这一组阅读引导文案，也被抽成了统一的可替换模板层。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中新增 `build_priority_action_focus_copy_specs()`，集中管理首页首看引导文案的句式模板
- 在 `app/dashboard/streamlit_app.py` 中让 `_build_priority_action_content_focus_lines()` 改为从这份配置读取“模块先看 / 首看字段 / 首看分组 / 首看结论”的包装句式
- 保持现有动态判断规则、引导内容和页面展示结果不变，只把外层表达从渲染函数硬编码迁移到展示配置层
- 更新 `tests/test_dashboard_streamlit.py`，新增首看引导文案模板配置的回归测试

当前效果：

- 首页动作摘要里最核心的阅读引导文案，已经和步骤、位置、跳转文案一起纳入统一的可替换展示配置体系
- 后面如果要统一调整首页阅读引导语气、盘前盘后表达方式或业务术语，不需要改主逻辑，只需要改配置
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要里的“顶层结论”这一层包装文案也被收口进了统一配置。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中新增 `build_priority_action_topline_copy_specs()`，集中管理首页动作摘要里“顶层结论”这一行的拼装模板
- 在 `app/dashboard/streamlit_app.py` 中让 `_build_priority_action_topline_context_lines()` 改为从这份配置读取 `prefix + value` 的包装方式
- 保持现有业务判断、结论内容和前缀类别不变，只把冒号与整行句式从渲染逻辑中抽离到展示配置层
- 更新 `tests/test_dashboard_streamlit.py`，新增顶层结论文案模板配置的回归测试

当前效果：

- 首页动作摘要里“步骤、位置、跳转、首看引导、顶层结论”这几层外部文本包装，已经基本全部进入统一的可替换展示配置体系
- 后面如果要继续改首页动作摘要的语气、业务口径、中文/英文标点或表达方式，已经不需要再改主渲染逻辑
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要又重新接回了业务主线，把“当前使用时段”显式纳入首页引导。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中新增 `build_priority_action_phase_copy_specs()`，统一管理动作摘要里的“当前时段 / 时段重点”文案模板
- 在 `app/dashboard/streamlit_app.py` 中新增 `_build_priority_action_time_phase_lines()`，把当前时段标签和时段重点整理成首页动作摘要里的两行业务提示
- 让 `_build_action_summary_markdown()` 与 `_build_action_summary_content()` 正式接收 `time_phase`，使盘前、盘中、盘后这层业务语境可以直接进入首页动作摘要
- 更新 `tests/test_dashboard_streamlit.py`，补充英文和中文动作摘要中的“当前时段 / 时段重点”回归测试

当前效果：

- 首页动作摘要现在不只是告诉用户“先看什么”，还会明确说明“当前是哪个使用时段、这个时段最该关注什么”
- 这让首页动作摘要从纯粹的阅读引导，进一步变成和盘前 / 盘中 / 盘后实际工作节奏一致的业务入口
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要的“盘前 / 盘中 / 盘后优先顺序”也从隐式判断收口成了显式可配置覆盖。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中新增 `build_priority_action_phase_override_specs()`，把不同使用时段下的动作摘要优先模块顺序集中放进配置表
- 在 `app/dashboard/streamlit_app.py` 中新增 `_resolve_priority_action_phase_key()`，并让 `_resolve_priority_action_sections()` 改为优先读取时段覆盖配置，再回退到原有场景默认顺序
- 先保持现有主要输出顺序稳定，把这次工作聚焦在“把控制权迁移到配置层”，而不是贸然改变首页业务结果
- 更新 `tests/test_dashboard_streamlit.py`，新增时段覆盖配置的回归测试，确认盘前、盘中、盘后的首页优先顺序都已有显式配置入口

当前效果：

- 首页动作摘要现在不仅能显示“当前时段 / 时段重点”，还已经具备“按时段单独配置首页优先顺序”的能力
- 后面如果要微调盘前、盘中、盘后的首页首看顺序，不需要再改判断逻辑，只要改配置表即可
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要开始真正利用这套时段配置，对盘前 / 盘中 / 盘后分别做了第一轮更贴业务的顺序微调，并同步对齐了动作摘要文案。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中扩展 `build_priority_action_phase_override_specs()`，把默认盘中、盘前快扫、中文盘后复盘下的首页优先模块顺序做成更明确的业务差异
- 新增 `build_priority_action_phase_profile_override_specs()`，让不同时段不仅能改单纯的模块顺序，还能同步覆盖动作摘要里的 `focus_points`、`reading_order`、`second_step_note`
- 在 `app/dashboard/streamlit_app.py` 中让 `_build_priority_action_profile()` 接收 `phase_key`，使动作摘要文案和首页模块顺序可以按同一个时段配置一起变化
- 把首页主流程切换为：盘前更强调“当日优先摘要后先核对最新提醒”，默认盘中更强调“最强板块后看龙头延续”，盘后更强调“快照回放后先确认股票池结构，再进入下一交易时段动作”
- 更新 `tests/test_dashboard_streamlit.py`，补充时段覆盖顺序、时段覆盖文案，以及盘前/盘后微调结果的回归测试

当前效果：

- 首页动作摘要现在已经不只是“有时段入口”，而是会根据盘前、盘中、盘后真正给出不同的首页首看顺序和相匹配的动作说明
- 这让首页从“时段可见、顺序可配”进一步推进到“时段差异已经开始真实生效”
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页动作摘要的时段 key 又从“主要跟随视图键”升级成了“优先按真实时间和数据状态自动判断”。
这一步主要做了：

- 在 `app/dashboard/streamlit_app.py` 中重写 `_resolve_priority_action_phase_key()` 的判断来源，不再优先依赖 `selected_variant_key / recommended_variant_key`，而是改为依据 `latest_timestamp`、`alert_count`、`negative_alert_count`、`available_batches` 自动判定当前应属于盘前快扫、盘中默认还是盘后复盘时段
- 让 `_resolve_priority_action_sections()` 与 `_build_priority_action_profile()` 都统一吃这套自动时段 key，使首页模块顺序和动作摘要文案能一起跟随真实盘面节奏变化
- 保持现有视图切换能力不变，但把首页动作摘要的时段判断优先级从“人为视图”切回“真实数据状态”
- 更新 `tests/test_dashboard_streamlit.py`，补充自动时段 key 的盘前/盘后回归测试，并同步把早盘 `09:35` 的“当日优先摘要”预期调整为新的盘前业务顺序

当前效果：

- 现在即使用户停留在某个视图里不切换，首页动作摘要也会更倾向按真实盘前、盘中、盘后状态给出更合适的引导顺序和动作说明
- 这让首页主线从“时段差异已经可配置生效”继续推进到“时段差异开始自动贴合真实使用场景”
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页顶部显示的 `time_phase` 也正式切到了和动作摘要同一套自动时段来源上。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中新增 `build_effective_time_phase_specs()`，把盘前、盘中、盘后对应的顶部时段展示文案做成按界面语言区分的自动时段规格
- 在 `app/dashboard/streamlit_app.py` 中新增 `_resolve_effective_time_phase()`，让顶部 `time_phase` 展示和页面布局合并逻辑都改为使用同一套自动时段判断结果
- 让 `main()` 中的首页顶部展示、时段引导、以及 `role_strategy + time_phase` 的布局合并都从 `effective_time_phase` 读取，而不是继续直接使用视图静态配置里的 `time_phase`
- 同时修正了自动时段覆盖下的本地化问题：英文界面在收盘阶段会显示英文版 `Closing Review Phase`，中文界面在开盘阶段也能显示中文的 `盘前快扫`
- 更新 `tests/test_dashboard_streamlit.py`，补充自动时段展示在英文收盘场景、中文开盘场景下的回归测试

当前效果：

- 页面顶部看到的“当前时段 / 时段重点”和动作摘要实际使用的时段逻辑，现在已经完全来自同一套自动判断来源
- 这让首页不再出现“顶部写的是一个时段，动作摘要按另一个时段工作”的分叉，首页业务主线在时段层面已经闭环
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日（周六）深夜，首页时段逻辑又补上了“手动覆盖开关”，形成了“默认自动判断 + 必要时人工指定”的完整使用方式。
这一步主要做了：

- 在 `app/dashboard/presentation.py` 中为主题配置补充 `time_phase_selector_label` 和 `time_phase_auto_label`，让首页顶部可以显示时段模式切换器
- 在 `app/dashboard/streamlit_app.py` 中新增 `_build_time_phase_override_options()`、`_resolve_time_phase_override_key()`、`_resolve_time_phase_override_label()`，把时段切换器做成稳定的 `auto / compact / default / business_cn` 四档入口
- 让 `main()` 中新增时段模式选择框；默认仍是 `Auto`，但用户现在可以临时指定按开盘快扫、盘中默认或收盘复盘逻辑查看首页
- 让 `_resolve_priority_action_phase_key()`、`_resolve_effective_time_phase()`、`_resolve_priority_action_sections()` 都接收手动覆盖参数，从而保证顶部时段展示、首页模块顺序和动作摘要文案会一起跟随手动覆盖结果变化
- 更新 `tests/test_dashboard_streamlit.py`，补充手动覆盖选项、标签、强制覆盖自动时段判断等回归测试

当前效果：

- 首页现在已经形成“系统自动判断时段 + 用户手动临时覆盖”的双轨机制，更贴近真实使用时遇到特殊场景的需要
- 这意味着即使系统默认判断是盘后逻辑，用户也可以临时切回盘前或盘中视角查看首页，而顶部时段、动作摘要和排序都会一起同步切换
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`
随后在 2026 年 7 月 18 日，首页控制带继续补上了“时段来源可见化”这一层说明，进一步贴近真实使用主线。这一步主要做了：

- 在 `app/dashboard/presentation.py` 的控制带文案配置里新增了 `time_phase_source_*` 模板，统一管理“自动判断 / 手动覆盖 / 当前模式”这层可替换文案
- 在 `app/dashboard/streamlit_app.py` 中让 `_build_time_phase_summary_text()` 接收 `phase_override_key`，使首页时段摘要会明确显示当前来自系统自动判断，还是来自手动覆盖
- 让 `_build_view_mode_note_markdown()`、`_build_control_band_markdown()`、`_render_home_header()` 把时段覆盖状态一路透传到首页控制带说明文案中
- 更新 `tests/test_dashboard_streamlit.py`，补上自动来源、手动覆盖来源，以及首页控制带透传状态的回归测试

当前效果：

- 首页现在不只会显示“当前处于哪个时段”，还会直接说明“这个时段是系统自动判断出来的，还是你手动切换过去的”
- 这让首页顶部的控制带、时段摘要、手动时段切换器三者之间的关系更清楚，降低后续使用时对页面状态的误判
- 这一轮相关测试已通过：`tests.test_dashboard_streamlit`、`tests.test_dashboard_presentation`、`tests.test_dashboard`

随后在 2026 年 7 月 18 日，项目继续回到“真实行情接入”主线，针对 Python 侧真实数据链路做了一轮补强与排障。这一步主要做了：

- 在 `app/data_sources/akshare_client.py` 中，把东方财富直连的 Windows 优先路径改为更贴近本机已验证思路的 `curl + clist/get` 市场列表接口，再由本地股票池过滤到监控范围
- 为东方财富直连补上了两个市场入口的自动重试：先尝试 `82.push2.eastmoney.com`，再尝试 `push2.eastmoney.com`
- 为 PowerShell / curl 子进程补上“显式清理代理环境变量”的直连环境，减少 Python 进程继承历史代理状态的干扰
- 更新 `tests/test_akshare_client.py`，补上 curl 市场列表优先路径的回归测试

当前结论：

- 代码层的真实行情接入路径已经进一步向“本机可验证方案”靠拢，相关测试通过：`tests.test_akshare_client`、`tests.test_main`、`tests.test_pipeline`
- 但在当前 Codex 运行环境里，`python -m app.main quote-connectivity-check` 仍然返回 `curl exit status 7`，说明阻塞点已经收敛到“Python/Codex 运行环境的外部网络连通”而不是主线业务代码缺失
- 也就是说，项目主线代码已经基本具备真实数据接入能力，当前剩余关键阻塞主要在本机/当前进程的网络访问条件，而非首页、报告、股票池、新闻流这些业务功能本身

随后在 2026 年 7 月 18 日，真实行情排障又向前推进了一步，把连通性检查从“笼统失败”细化成了“失败层级诊断”。这一轮主要做了：

- 在 `app/main.py` 里重构了 `quote-connectivity-check` 的失败输出，新增 `Failure type`、更具体的 `Diagnosis`，以及按失败类型给出的 `Next step`
- 让 `exit status 7` 这一类错误被明确识别为 `tcp-connect-failed`，不再只是笼统显示“请求失败”
- 更新 `tests/test_main.py`，补上 TCP 连接失败场景的回归测试

当前结论进一步收敛为：

- 现在运行 `python -m app.main quote-connectivity-check`，项目会明确显示当前失败类型是 `tcp-connect-failed`
- 这意味着当前环境下已经不是“域名解析失败”，也不是“代码没发出请求”，而是“当前 Python / Codex 运行进程能解析域名，但无法把 HTTPS TCP 连接真正建立起来”
- 因此后续真实数据要跑通，优先处理的是当前运行环境的进程级外网访问条件，而不是继续大幅改动业务主线代码

随后在 2026 年 7 月 19 日，项目继续补上了“本地真实行情快照入口”，作为当前外网受限场景下的备用真实数据方案。这一步主要做了：

- 在 `app/data_sources/akshare_client.py` 中新增 `local-json-snapshot` 数据源
- 把默认实时行情回退顺序扩展为：`Eastmoney direct -> AKShare -> local-json-snapshot -> demo-fallback`
- 支持从 `MONITOR_LOCAL_QUOTE_PATH` 指定的 JSON 文件，或默认 `data/runtime/latest_quotes.json`，加载本地真实行情快照
- 支持三种本地 JSON 形态：东方财富 `data.diff` 原始结构、`rows` 数组结构、纯数组结构
- 更新 `.env.example` 和 `README.md`，补上本地真实行情快照入口说明
- 更新 `tests/test_akshare_client.py`，补上本地快照加载与三层回退的回归测试

当前效果：

- 即使当前 Python / Codex 进程无法直接访问外部行情接口，只要本地存在有效的真实行情快照文件，主流程仍然可以按真实行情而不是演示数据继续运行
- 这让项目在“网络未完全打通之前”也已经具备一条可落地的真实数据备用运行路径

随后在 2026 年 7 月 19 日，项目又把这条“本地真实行情快照”备用路径补成了完整可操作链路。这一步主要做了：

- 在 `app/main.py` 中新增两个命令：
  - `python -m app.main create-local-quote-template`
  - `python -m app.main validate-local-quote`
- `create-local-quote-template` 会默认在 `data/runtime/latest_quotes.json` 生成可直接填写的本地真实行情模板
- `validate-local-quote` 会校验本地快照文件是否存在、当前 JSON 形态属于哪一类、是否可以被主流程识别，以及首条代码和行数是否正常
- 在 `app/data_sources/akshare_client.py` 中补充了本地快照公共函数，统一本地快照路径解析、形态识别和字段归一化逻辑
- 更新了 `tests/test_main.py` 与 `tests/test_akshare_client.py`，补上模板生成、快照校验、帮助页入口以及东财原始结构/rows 结构的回归测试

当前效果进一步完善为：

- 本地真实行情快照现在不只是“代码支持”，而是已经具备“生成模板 -> 填入数据 -> 校验格式 -> 主流程继续使用”的完整闭环
- 在当前外网未完全打通的阶段，这条备用真实数据路径已经具备可直接落地使用的操作入口

随后在 2026 年 7 月 19 日，项目又把“数据来源可见性”补齐了，让真实数据备用链路在输出层也一眼可辨。这一步主要做了：

- 在 `app/data_sources/akshare_client.py` 中新增统一的来源说明函数，把短码映射成更容易理解的说明文本
- 让 `self-check`、主流程控制台总览、`quote-connectivity-check` 成功路径统一显示更清晰的来源说明
- 例如现在会显示：
  - `eastmoney-direct (live direct endpoint)`
  - `akshare (live adapter)`
  - `local-json-snapshot (local real quote snapshot)`
  - `demo-fallback (built-in demo data)`
- 更新 `tests/test_main.py` 与 `tests/test_pipeline.py`，补上来源说明显示层的回归测试

当前效果：

- 现在不仅代码内部知道当前跑的是哪条行情路径，用户在终端输出里也能直接看懂当前到底是直连、AKShare、本地真实快照，还是演示数据
- 这让“真实数据是否已经真正接上”在日常使用中变得更容易确认

随后在 2026 年 7 月 19 日，项目又把“外部 JSON -> 本地真实快照 -> 主流程可用”这条路径再压缩了一步，补上了一键导入命令。这一步主要做了：

- 在 `app/main.py` 中新增 `python -m app.main import-local-quote "external_quotes.json"` 命令
- 这个命令会读取外部 JSON，自动按项目规则归一化后写入当前活动的本地快照路径
- 写入后的存储形态统一为 `rows-array`，便于后续 `validate-local-quote` 与主流程稳定识别
- 更新 `tests/test_main.py`，补上缺少源文件和导入成功两类回归测试

当前效果进一步完善为：

- 现在从拿到外部真实行情 JSON 到项目主流程可用，已经形成“导入 -> 校验 -> self-check”的最短可执行路径
- 在当前外网尚未完全打通的阶段，这条备用真实数据链路已经可以更低摩擦地投入日常使用
随后在 2026 年 7 月 19 日，项目继续把“行情来源可见性”从命令行进一步打通到数据库、仪表盘首页和晨报/晚报文本，避免不同界面看到的数据上下文不一致。这一步主要做了：

- 在 `app/database.py` 中为 `market_snapshot` 增加 `quote_source` 字段，并补上老库自动迁移逻辑
- 在 `app/pipeline.py` 中让实时行情行、演示行情行都统一携带 `quote_source`，这样每次入库的快照都会记录来源
- 在 `app/dashboard/overview.py` 中把 `quote_source` 和 `quote_source_display` 加入首页 payload
- 在 `app/dashboard/presentation.py` 与 `app/dashboard/streamlit_app.py` 中让首页控制带显示“数据库 + 行情来源”
- 在 `app/reports/morning_report.py` 与 `app/reports/evening_report.py` 中加入“行情来源”提示行，数据库回放生成的晨报、晚报也会带上来源说明
- 同步补齐 `tests/test_database.py`、`tests/test_dashboard.py`、`tests/test_dashboard_streamlit.py`、`tests/test_reports.py` 的回归覆盖，并复跑 `tests.test_main`、`tests.test_akshare_client`

当前效果：

- 现在不仅命令行里能看出当前用的是直连、AKShare、本地真实快照还是演示数据，首页和数据库回放报告里也能看出来
- 这让“当前是否已经接入真实数据、如果没有是卡在哪一层”变得更容易判断
- 对当前主线最直接的价值是：即使外部行情接口还没完全打通，我们也已经把“本地真实快照版本”的可见性和可追溯性补齐了

随后在 2026 年 7 月 19 日，项目又把“真实数据状态”进一步抽成了首页可替换 KPI 卡片，目的是让用户不用先读长文字，也能一眼判断当前跑的是哪种行情模式。这一步主要做了：

- 在 `app/dashboard/overview.py` 中新增 `quote_status_summary`，把行情来源归一为更直观的状态文案：
  - `Quote status: live direct quotes active.`
  - `Quote status: live adapter quotes active.`
  - `Quote status: using local real quote snapshot.`
  - `Quote status: demo fallback active.`
- 在 `app/dashboard/presentation.py` 中新增 KPI 卡片 `quote_status_summary`，并把它纳入默认、快速查看、中文业务视图三套卡片顺序
- 这张卡片的文案、截断长度、中文标签、紧凑版/优先版样式都做成了可替换配置，不影响主线判断逻辑
- 补齐 `tests/test_dashboard.py`、`tests/test_dashboard_presentation.py`、`tests/test_dashboard_streamlit.py` 的回归覆盖，并复跑了首页相关测试集

当前效果：

- 首页 KPI 区现在会直接显示当前真实数据状态，不需要先去控制带或终端里找来源说明
- “直连已接通 / 本地真实快照运行中 / 仍在演示数据”这三类状态已经有统一入口，后续再换视觉样式时不用再改业务判断

随后在 2026 年 7 月 19 日，项目又把“真实数据是否真正跑通”的判断进一步收口到了命令行主入口里，避免出现“主流程 ok，但其实还在 demo fallback”时不容易第一眼看出来的问题。这一步主要做了：

- 在 `app/main.py` 中新增统一的真实数据状态判断：
  - `live-pass`：使用 `eastmoney-direct` 或 `akshare`
  - `snapshot-pass`：使用 `local-json-snapshot`
  - `not-passed (still on demo fallback)`：仍在 `demo-fallback`
- `self-check` 现在会额外显示 `Real-data status`
- `mainline-smoke-test` 现在会把“功能链路是否跑通”和“真实数据是否跑通”分开显示，不再混在一个 `ok` 里
- `quote-connectivity-check` 在成功时也会显示同一套 `Real-data status`，保证三类入口的判断口径一致
- 当 `self-check` 仍落在 demo fallback 时，下一步提示会从 `start-daily-news-workflow` 自动切到 `validate-local-quote`，更贴近当前主线目标
- 同步更新了 `tests/test_main.py` 的回归断言，并复跑通过

当前效果：

- 现在“系统能跑”与“真实数据已跑通”已经被明确拆开
- 你后面看 `self-check`、`quote-connectivity-check`、`mainline-smoke-test` 时，不需要自己再二次推断当前到底是不是还停留在演示数据阶段

随后在 2026 年 7 月 19 日，项目又把“导入本地真实行情快照 -> 校验 -> 确认是否通过”压缩成了一条更短的命令链，减少手工串行多个命令的成本。这一步主要做了：

- 在 `app/main.py` 中新增命令：
  - `python -m app.main import-local-quote-pass-check "external_quotes.json"`
- 这个命令会按顺序执行三步：
  - `Step 1: Import`
  - `Step 2: Validate`
  - `Step 3: Self-Check`
- 当导入后的运行结果达到真实数据可用状态时，会直接给出：
  - `Result: local real-data path is ready.`
  - `Next step: python -m app.main start-daily-news-workflow`
- 如果仍未通过，会继续把下一步收口回本地快照校验，而不是让用户误以为可以直接进入新闻工作流
- 同步更新了帮助文案与 `tests/test_main.py` 回归测试，并复跑通过

当前效果：

- 现在拿到一份外部真实行情 JSON 后，可以用一条命令完成“导入 -> 校验 -> 是否通过”的短链路确认
- 这让 `snapshot-pass` 这条备用真实数据路径更接近日常可用状态，也更贴近当前“尽快跑通真实数据版本”的主线目标

随后在 2026 年 7 月 19 日，项目又把 `import-local-quote-pass-check` 的失败反馈细化成了更容易定位问题的几类原因，避免命令没通过时只看到一个笼统的“needs review”。这一步主要做了：

- 在 `app/main.py` 中为 `import-local-quote-pass-check` 增加了更明确的失败原因映射
- 当前会区分几类常见失败：
  - `source file missing`
  - `source JSON format did not match the supported local quote shapes`
  - `runtime local snapshot file is missing`
  - `runtime local snapshot content is invalid or fields are incomplete`
  - `import succeeded, but self-check still fell back to demo data`
- 对应失败时，输出里会明确带出：
  - `Result: ... did not pass`
  - `Failure reason: ...`
  - 更贴近当前阶段的下一步命令
- 同步补齐 `tests/test_main.py` 中关于缺失源文件、源格式不匹配、导入成功但 self-check 仍回落到 demo 的回归覆盖，并复跑通过

当前效果：

- 现在本地真实数据短链路失败时，已经能更快区分是“源文件问题”“快照格式问题”还是“虽然导入了，但运行时并没有真正切到真实数据路径”
- 这对后续继续把真实数据版本彻底跑通很关键，因为每一类失败后面的处理方向已经开始分层清晰了
## 2026-07-19 本地真实快照失败诊断细化

- 在 `app/main.py` 的 `import-local-quote-pass-check` 失败分支里，新增了 `Runtime diagnosis` 诊断行，不再只提示笼统的 `demo fallback`。
- 当前会进一步区分三类更贴近实际排查的问题：
  - `runtime snapshot loaded, but it currently contains 0 rows.`
  - `runtime snapshot loaded, but 0 rows matched the current monitored stock pool.`
  - `runtime snapshot is valid and matches the monitored stock pool, but the active quote fetch path still returned no rows.`
- 这让“导入成功但 self-check 仍未通过”的问题，能够更快判断是：
  - 快照本身是空的
  - 快照股票不在当前监控池
  - 快照本身没问题，但运行时实际取数路径仍未命中本地真实快照
- 已补齐 `tests/test_main.py` 的三条回归测试，并复跑 `tests.test_main` 全量通过。

## 2026-07-19 实时连通性诊断分层补充

- 在 `app/main.py` 的 `quote-connectivity-check` 阻断输出里，新增了两层更直接的定位信息：
  - `Blocked stage`
  - `Runtime diagnosis summary`
- 现在当实时行情仍不可达时，除了原有的 `Failure type / Diagnosis / Raw error / Next step`，还会明确说明：
  - 当前卡住的是哪一层取数阶段
  - 这是不是仍停留在“实时行情采集层”，还没有进入股票池过滤或报告生成层
  - 对 `tcp-connect-failed` 这类情况，会额外强调“浏览器或 shell 可能能通，但当前 Python 运行时仍未打通”
- 已补齐 `tests/test_main.py` 对应回归断言，并再次复跑 `tests.test_main` 全量通过。

## 2026-07-19 self-check 排障入口收口

- 在 `app/main.py` 的 `self-check` 输出里新增了 `Recommended diagnosis` 行，用来直接告诉下一步最该先排查什么。
- 当前按真实数据状态分三种建议：
  - `not-passed (still on demo fallback)`：
    先跑 `python -m app.main validate-local-quote`，如果本地快照有效，再跑 `python -m app.main quote-connectivity-check`
  - `snapshot-pass`：
    说明本地真实快照路径已通过，直接进入 `python -m app.main start-daily-news-workflow`
  - `live-pass`：
    说明实时路径已通过，也可直接进入 `python -m app.main start-daily-news-workflow`
- 这样 `self-check` 现在不只是告诉“有没有掉回 demo”，还会把“先查本地快照还是先查实时连通性”直接收口出来。
- 已补齐 `tests/test_main.py` 的新增断言，并复跑 `tests.test_main` 全量通过。

## 2026-07-19 README 中文使用指南重写

- 直接重写了 `README.md`，把之前混杂和编码不整齐的内容整理成一份干净的中文使用指南。
- 新版 README 重点补齐了几条现在最关键的使用路径：
  - 最短上手路径
  - 真实数据状态说明
  - 真实数据排障最短路径
  - `self-check` / `quote-connectivity-check` 的阅读方法
  - 日常新闻工作流顺序
  - VS Code 与 PowerShell 的本地使用入口
- 这样后面项目在本地日常运行时，已经不需要再反复翻聊天记录，直接看 README 就能完成：
  - 自检
  - 真实数据判断
  - 本地快照导入与排障
  - 当日新闻摘要流程启动

## 2026-07-19 本地真实快照示例文件落库

- 新增了仓库内固定示例文件 `data/examples/real_quote_sample.json`。
- 这个文件采用项目当前支持的 `rows-array` 结构，可直接作为：
  - 本地真实快照格式参考
  - 手工替换数据的起始模板
  - `import-local-quote-pass-check` 的演示输入样例
- 同时在 `README.md` 里补上了这个示例文件的入口，后续本地接入真实快照时，不需要再从聊天记录里找 JSON 格式。

## 2026-07-19 自动实时抓取链路再前移一层

- 在 `app/data_sources/akshare_client.py` 里，为 Eastmoney 直连新增了 `PowerShell 市场总表` 取数路径。
- 当前默认实时抓取顺序进一步明确为：
  - PowerShell 直取 Eastmoney 市场总表
  - `curl` 直取 Eastmoney 市场总表
  - 再退回到按监控池 `secids` 分批请求
- 这样做的目的，是尽量贴近这台机器上已经验证过“有时浏览器/终端能通，但 Python 运行时未必稳定能通”的现实环境，优先复用更可能成功的本机直连方式。
- 已补齐 `tests/test_akshare_client.py` 中关于：
  - 优先使用 PowerShell 市场总表路径
  - PowerShell 失败后再回退到 `curl`
  的回归测试，并复跑通过。

## 2026-07-19 连通性成功输出增加命中路径

- 在 `app/data_sources/akshare_client.py` 中为 Eastmoney 直连结果补上了 `fetch_path` 标记。
- 当前当直连成功时，可以区分：
  - `eastmoney-market-powershell`
  - `eastmoney-market-curl`
  - `eastmoney-secid-batch`
- 在 `app/main.py` 的 `quote-connectivity-check` 成功输出中，新增了：
  - `Direct path: ...`
- 这样后续本地验证自动真实数据时，不只是知道“通了”，还知道这次到底是靠哪条自动直连路径打通的。
- 已补齐相关回归测试，并复跑：
  - `tests.test_akshare_client`
  - `tests.test_main`
  均通过。

## 2026-07-19 self-check 同步显示直连命中路径

- 在 `app/pipeline.py` 中把 `fetch_path` 正式纳入 `MonitorCycleResult`，并从实时取数结果一路传到主流程结果对象。
- 在 `app/main.py` 的 `self-check` 输出中，新增了：
  - `Direct path: ...`
- 这样现在不只是 `quote-connectivity-check`，连主流程自检 `self-check` 也能直接看出：
  - 当前自动真实数据是否打通
  - 如果打通，究竟是靠 `eastmoney-market-powershell`、`eastmoney-market-curl` 还是其他路径命中的
- 已新增并复跑通过的相关回归：
  - `tests.test_main`
  - `tests.test_pipeline`

## 2026-07-20 README 补充 Direct path 阅读说明

- 因为 README 里原有内容存在一些历史编码噪音，这一步没有大范围重写，而是追加了一个新的 `Direct path 说明` 小节。
- 新增小节明确说明了：
  - `Direct path` 不只是“能不能通”，而是“这次靠哪条自动直连路径打通”
  - 应该按 `Real-data status -> Quote source -> Direct path` 的顺序阅读
  - 如果看到 `live-pass` 且带有 `Direct path`，说明当前已经真正跑在自动实时路径上

## 2026-07-20 本地快照模板收口到单一 helper

- 在 `app/main.py` 中新增了 `_build_default_local_quote_template_payload()`，把本地快照模板的有效来源收口到一个地方。
- `create-local-quote-template` 现在优先直接使用这一个 helper 的结果写文件，不再依赖函数体内重复的内联模板定义。
- 这样后续如果再改本地快照示例，只需要改一个地方，能避免“仓库示例文件、动态模板、历史重复块”三者继续漂移。
- 已复跑：
  - `tests.test_main.MainTests.test_main_create_local_quote_template_writes_default_shape_file`
  - `tests.test_main`
  均通过。

## 2026-07-20 本地快照模板与示例文件实现同源

- 进一步把 `_build_default_local_quote_template_payload()` 改成直接读取 `data/examples/real_quote_sample.json`。
- 现在仓库示例文件已经成为模板命令的实际来源，`create-local-quote-template` 生成的内容与示例文件一一对应。
- 在 `tests/test_main.py` 中补上了断言，确认：
  - 模板命令写出的 JSON
  - `data/examples/real_quote_sample.json`
  两者完全一致。
- 已复跑：
  - `tests.test_main.MainTests.test_main_create_local_quote_template_writes_default_shape_file`
  - `tests.test_main`
  均通过。

## 2026-07-20 本地快照模板实际生效路径再次收口

- 在 `app/main.py` 中新增了 `_load_authoritative_local_quote_template_payload()`，明确把仓库示例文件作为模板命令当前唯一生效的加载入口。
- `create-local-quote-template` 现在行为上已经完全走这条新 loader，相关回归仍然通过。
- 当前状态说明：
  - 运行时实际行为已经收口完成
  - `app/main.py` 中旧乱码模板块仍以“不可达历史残留”形式存在
  - 后续若继续做纯代码清洁，可再专门删除这段残留


## 2026-07-20 ??????????????

- ??? `app/main.py` ???????????????????
  - ???????
  - ??/??/??????
  - ??????????????????
  - ?????????????????
- ???????????????????????? -> ????? -> ?????????????????
- ?????????????????
  - `Impact summary: ???? x | ???? y | ???? z`
  - `Impact view: ?????? / ??????`
  - `Bottom line: ... ?????...`
  - `high-priority-only` ??????
  - `summary-only` ????
- ????????
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`
- ???
  - ????????????
  - ??????????????????????????


## 2026-07-20 ????????????????

- ? `app/main.py` ??????
  - `python -m app.main refresh-local-quote-snapshot`
- ??????
  - ???????????????
  - ??????????????????
  - ???? `Quote source`?`Direct path`?`Real-data status`
- ????????????? -> ???? -> self-check -> ???????????????? JSON?
- ?????????????
  - ??????????
  - ???????? `rows-array` ??
  - ?????????? `quote-connectivity-check`
- ????????
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`


## 2026-07-20 ??????????????

- ? `app/main.py` ??????
  - `python -m app.main refresh-local-quote-pass-check`
- ??????????????
  - ?????????????????
  - ????????????
  - ??? `self-check` ????????? `live-pass` ? `snapshot-pass`
- ?????????????????????
  - `python -m app.main refresh-local-quote-pass-check`
- ?????????????
  - ??????????
  - ?????????? refresh -> validate -> self-check
  - ???????????? `quote-connectivity-check`
- ???????
  - ? `refresh-local-quote-pass-check`
  - ?????????? `start-daily-news-workflow`??????????

## 2026-07-20 本地真实数据快照主线已跑通

- 用户在 VS Code 终端中完成了：
  - `self-check`
  - `start-daily-news-workflow`
  - `latest-review`
- 当前 `self-check` 结果：
  - `Main flow: ok`
  - `Quote source: local-json-snapshot (local real quote snapshot)`
  - `Real-data status: snapshot-pass`
  - `Stock-pool validation: valid`
- 当日日报工作流已生成：
  - `data/news/news_batch_20260720.json`
  - `data/news/news_batch_priority_summary_20260720.md`
- `latest-review` 已可正常读取数据库复盘，行情来源显示为：
  - `local-json-snapshot (local real quote snapshot)`
- 当前结论：
  - 本地真实数据快照路径已经可以支撑主线演示
  - 直连链路此前 `quote-connectivity-check` 已出现 `live-pass`
  - 后续可继续修平 `refresh-local-quote-pass-check` 与直连检查偶发不一致的问题

## 2026-07-20 修平直连检查与刷新快照不一致问题

- 问题现象：
  - `quote-connectivity-check` 可以显示 `live-pass`
  - 但 `refresh-local-quote-pass-check` 可能因为广域市场数据没有命中监控池股票而刷新失败
- 已在 `app/data_sources/akshare_client.py` 中补强：
  - 东方财富广域市场接口成功后，会检查返回行是否包含监控池股票代码
  - 如果没有命中监控池，会自动切到 `eastmoney-secid-batch`，按监控池代码批量直取
  - 批量直取结果按股票代码去重，避免多批次重复返回导致快照重复
- 新增回归测试：
  - 广域市场 payload 没有监控池股票时，会继续抓取监控池 secid 批次
- 本轮回归已通过：
  - `tests.test_akshare_client`
  - `tests.test_main`
  - `tests.test_pipeline`

## 2026-07-20 eastmoney-direct 已进入复盘主线

- 用户重新运行：
  - `refresh-local-quote-pass-check`
  - `start-daily-news-workflow`
  - `latest-review`
- 关键结果：
  - `refresh-local-quote-pass-check` 显示 `Result: local real-data refresh path passed.`
  - `latest-review` 显示 `行情来源: eastmoney-direct (live direct endpoint)`
- 当前判断：
  - 东方财富真实直连链路已经能进入数据库复盘结果
  - 本地快照链路仍然可用，`self-check` 可能显示 `snapshot-pass`
  - `eastmoney-direct` 与 `local-json-snapshot` 现在都属于真实数据路径，不应再按 `demo-fallback` 处理
- 当日日报文件仍为：
  - `data/news/news_batch_priority_summary_20260720.md`
## 2026-07-21 批量新闻异常分支中文化

- 已将批量新闻相关异常提示中文化：
  - 未提供新闻批量文件
  - 未找到新闻批量文件
  - 新闻批量文件 JSON 格式错误
  - 新闻批量文件结构错误
  - 新闻批量条目错误
  - 不支持的筛选模式
- 已将通用 `export-news-batch` 的正常输出同步中文化：
  - 新闻批量导出
  - 新闻源文件
  - 保存到
  - 筛选模式
- 内部仍保留少量旧英文标签兼容解析，确保旧导出文本或历史输出不会影响摘要生成。
- 已复跑通过：
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`

## 2026-07-21 帮助页与新闻模板/校验入口中文化

- 已将命令帮助页 `_build_command_help_text()` 的主要标题和说明中文化：
  - AI 半导体监控命令
  - 日常使用
  - 成功信号
  - 最小可运行检查
  - 批量新闻速查
  - 完整命令目录
- 已将新闻批量模板与每日新闻模板命令中文化：
  - `create-news-batch-template`
  - `create-daily-news-batch`
- 已将新闻批量校验入口中文化：
  - `validate-news-batch`
- 本轮主要覆盖“查命令、建模板、校验新闻文件”这三个日常入口。
- 已复跑通过：
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`

## 2026-07-20 单条新闻分类输出中文化

- 已将 `classify-news` 单条新闻命令的可见输出中文化：
  - 新闻分类
  - 标题 / 正文
  - 情绪 / 级别
  - 相关板块 / 相关股票
  - 链条提示 / 影响判断
  - 置信度 / 原因
  - 预警预览 / 预警级别 / 预警关注点
  - 建议动作
  - 结论
- 本轮只改展示层，不改变 `classify_news` 的规则和预警逻辑。
- 已复跑通过：
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`

## 2026-07-20 批量新闻分类明细字段中文化

- 已将批量新闻分类正文的高频可见字段中文化：
  - `News Batch Classification` -> `新闻批量分类`
  - `Source` -> `新闻源文件`
  - `Items` -> `新闻条数`
  - `Impact summary` -> `影响摘要`
  - `Filter` -> `筛选模式`
  - `Items shown` -> `显示条数`
  - `Level / Sector` -> `级别 / 板块`
  - `Bottom line` -> `结论`
- 为避免影响每日摘要生成，内部解析函数已兼容旧英文标签和新中文标签。
- 单条新闻命令 `classify-news` 仍暂时保留 `Level`、`Bottom line` 等英文输出，后续可单独一轮中文化。
- 已复跑通过：
  - `tests.test_main`
  - `tests.test_pipeline`
  - `tests.test_akshare_client`

## 2026-07-20 批量新闻每日流程提示中文化

- 已继续中文化批量新闻高频终端输出：
  - `news-batch-first-pass`
  - `news-batch-priority-pass`
  - `news-batch-priority-export`
  - `batch-news-daily-flow`
  - `batch-news-daily-export`
- 本轮重点改“流程外壳”和用户首先看到的标题/字段：
  - 新闻源文件
  - 校验状态
  - 新闻条数
  - 摘要初筛
  - 优先级筛选
  - 已保存优先级摘要到
  - 默认归档规则
- 分类明细内部的 `Filter`、`Items shown`、`Level` 等字段暂时保留，避免影响现有摘要解析逻辑；后续可单独做一轮映射层中文化。
- 已同步更新 `tests/test_main.py`，并复跑 `tests.test_main` 通过。

## 2026-07-20 日常主线终端提示中文化

- 已将每日高频入口的终端提示进一步中文化：
  - `latest-review` 顶部阅读提示
  - 空数据库时的首次运行提示
  - `start-daily-news-workflow` 的标题、源文件、摘要文件、阅读顺序
  - `mainline-smoke-test` 的摘要字段
  - demo 主流程自动附加的最新数据库复盘标题
- 同时保留内部状态判断，避免中文化后影响 `self-check` 对“是否已有复盘数据”的判断。
- 已同步更新对应回归测试。

## 2026-07-20 README 中文使用指南收口

- 已将 `README.md` 从历史堆叠说明整理为一份面向日常使用的中文指南。
- 新版 README 聚焦当前主线：
  - 如何运行 `self-check`
  - 如何刷新并验证真实行情快照
  - 如何启动每日新闻工作流
  - 如何查看 `latest-review`
  - 如何判断 `live-pass`、`snapshot-pass`、`demo-fallback`
  - 如何维护 `app/universe/stock_pool.json`
- README 中补充了 VS Code 终端可直接使用的完整 Python 运行时路径，降低用户手动排查成本。
- 本次只调整文档，不改变业务代码逻辑。
## 2026-07-23 美股收盘概括顶部模块
- 新增独立的 `app/reports/us_market_overview.py`，为每日摘要和飞书推文提供统一的“美股收盘概括”顶部区块。
- 区块预留纳斯达克综合指数、费城半导体指数的开盘/盘中/收盘趋势，以及强势板块、弱势板块和简短分析字段。
- 当前采用本地真实快照优先策略，路径可由 `MONITOR_US_MARKET_SUMMARY_PATH` 配置；未配置或数据无效时明确提示暂无数据，不生成演示值。
- 已将该区块插入 `start-daily-news-workflow` 本地输出和飞书精简推文最前面，后续可独立替换行情采集器而不改新闻主线。
