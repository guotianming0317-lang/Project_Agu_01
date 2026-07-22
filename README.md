# Project Agu 01

Project Agu 01 是一个轻量级的 AI + A 股半导体监控项目，用于研究辅助、每日复盘和股票池跟踪。

它的目标不是自动交易，而是帮你更稳定地完成三件事：

- 自动获取或读取真实行情数据
- 按股票池和产业链分类生成监控结论
- 输出每日新闻优先级摘要和市场复盘

## 当前可用状态

当前项目已经进入“本地可跑通版本”：

- 主流程可以运行
- 股票池校验可以运行
- 本地真实行情快照可以运行
- 东方财富直连行情在可连接时可以进入真实数据链路
- 每日新闻工作流可以生成当日摘要文件
- 最新复盘可以从本地数据库读取

真实数据链路通过时，`self-check` 会显示：

- `Real-data status: live-pass`
- 或 `Real-data status: snapshot-pass`

如果仍显示 `demo-fallback`，说明主流程能跑，但当前没有拿到可用真实行情。

## 运行环境

建议使用 Python 3.11+。

如果你的终端可以直接使用 `python`，命令可以写成：

```bash
python -m app.main self-check
```

如果 VS Code 终端里 `python` 没反应，使用当前已经验证过的项目运行时：

```powershell
& "C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -m app.main self-check
```

后续文档默认写 `python -m app.main ...`。如果你本机的 `python` 不可用，把命令开头替换成上面的完整 Python 路径即可。

## 最短日常使用路径

每天最推荐按这个顺序运行：

```bash
python -m app.main refresh-local-quote-pass-check
python -m app.main refresh-daily-news-batch
python -m app.main start-daily-news-workflow
python -m app.main latest-review
python -m app.main phase-one-ready-check
python -m app.main phase-two-ready-check
python -m app.main phase-three-ready-check
python -m app.main daily-automation-status
```

这几步分别表示：

- 刷新并验证真实行情快照
- 刷新当日自动新闻候选源
- 生成当日新闻优先级摘要
- 查看最近一次市场复盘
- 汇总确认阶段一可运行版本是否就绪
- 汇总确认阶段二增强版是否就绪
- 汇总确认阶段三外部集成框架是否就绪
- 查看每日自动化、调度和新闻源状态

如果你不单独运行 `refresh-daily-news-batch`，`start-daily-news-workflow` 在当日新闻源文件不存在时也会自动生成一份候选新闻源。

## 一键自检

```bash
python -m app.main self-check
```

重点看这几行：

- `Main flow: ok`
- `Quote source: ...`
- `Real-data status: live-pass` 或 `snapshot-pass`
- `Stock-pool validation: valid`
- `Next step: ...`

含义：

- `live-pass`：已经走通自动实时行情路径
- `snapshot-pass`：已经走通本地真实行情快照路径
- `not-passed` 或 `demo-fallback`：还没有拿到真实行情，正在用演示数据兜底

## 真实行情检查

检查当前网络和行情接口是否可用：

```bash
python -m app.main quote-connectivity-check
```

如果成功，通常会看到：

- `Endpoint access: ok`
- `Rows fetched: ...`
- `Quote source: eastmoney-direct`
- `Real-data status: live-pass`

如果失败，优先看：

- `Diagnosis`
- `Raw error`
- `Next step`

常见原因包括网络限制、代理残留、防火墙、行情接口临时断开。

## 刷新真实行情快照

推荐使用这个命令：

```bash
python -m app.main refresh-local-quote-pass-check
```

它会自动执行：

- 刷新真实行情
- 保存到 `data/runtime/latest_quotes.json`
- 校验快照是否可用
- 再跑一次主流程自检

通过时会显示：

```text
Result: local real-data refresh path passed.
Failure reason: none
Next step: python -m app.main start-daily-news-workflow
```

## 每日新闻工作流

启动当日新闻工作流：

```bash
python -m app.main start-daily-news-workflow
```

它会生成或复用：

- `data/news/news_batch_YYYYMMDD.json`
- `data/news/news_batch_priority_summary_YYYYMMDD.md`

如果想先单独刷新当日新闻源，可以运行：

```bash
python -m app.main news-source-status
python -m app.main announcement-source-status
python -m app.main notification-status
python -m app.main external-feeds-status
python -m app.main refresh-daily-news-batch
python -m app.main refresh-external-feeds-pass-check
```

当前这一步使用的是本地自动候选源，作用是先把“新闻源生成层”接入主流程；后续接入真实公开新闻接口时，会优先替换这一层。

如果已经配置远程新闻或公告 JSON 源，可以直接运行 `refresh-external-feeds-pass-check`。它会按顺序刷新新闻源、刷新公告源、生成当日新闻批量源并导出每日优先摘要；远程源未配置时，会继续使用当前本地源或自动候选源。

如果只想先确认配置情况，不想写文件或发起抓取，可以运行 `external-feeds-status`。它只读取环境变量和本地文件状态，用来判断远程新闻、远程公告、本地源和每日流程是否处于可运行状态。

如果需要一份可编辑的本地新闻源模板，可以先运行：

```bash
python -m app.main create-local-news-feed-template
python -m app.main append-local-news-feed "新闻标题" "新闻正文"
python -m app.main refresh-local-news-feed
python -m app.main validate-local-news-feed
python -m app.main local-news-feed-daily-pass-check
```

如果你已经有一份本地新闻源 JSON，可以先设置 `MONITOR_NEWS_FEED_PATH` 指向它，再运行 `refresh-daily-news-batch`。系统会优先读取这份本地新闻源，再补充内置自动候选。

如果你有远程新闻 JSON 源，可以把 `MONITOR_NEWS_FEED_URL` 指向这个 URL，再运行 `refresh-local-news-feed`。命令会先把远程新闻标准化写入本地新闻源文件，每日主线仍读取本地文件，因此远程网络失败不会破坏当日流程。

如果你使用的是 `data/news/local_news_feed.json` 这份默认本地新闻源，可以直接运行 `local-news-feed-daily-pass-check`，它会一次完成校验、刷新每日新闻批量源、导出每日优先摘要。

如果需要把公司公告也并入每日新闻流，可以先生成并编辑本地公告源：

```bash
python -m app.main create-local-announcement-feed-template
python -m app.main validate-local-announcement-feed
python -m app.main refresh-local-announcement-feed
```

然后设置 `MONITOR_ANNOUNCEMENT_FEED_PATH` 指向 `data/news/local_announcement_feed.json`，再运行 `refresh-daily-news-batch` 或 `start-daily-news-workflow`。系统会把公告源放在每日新闻候选前面，并按标题去重。

如果你有远程公告 JSON 源，可以把 `MONITOR_ANNOUNCEMENT_FEED_URL` 指向这个 URL，再运行 `refresh-local-announcement-feed`。命令会先把远程公告标准化写入本地公告源文件，每日主线仍读取本地文件，因此远程网络失败不会破坏当日流程。

`mainline-smoke-test` 也会自动识别这份默认本地新闻源；如果它存在，烟雾测试会优先用本地新闻源跑每日新闻链路。

建议阅读顺序：

1. 先看 `data/news/news_batch_priority_summary_YYYYMMDD.md`
2. 如需完整市场复盘，再运行 `python -m app.main latest-review`
3. 如需补充新闻，修改当日 `news_batch_YYYYMMDD.json` 后重新运行工作流

## 查看最新复盘

```bash
python -m app.main latest-review
```

重点看：

- 行情来源
- 今日主线
- 龙头判断
- 材料/气体线索
- 监控池结构变化
- 明日策略

如果行情来源显示 `eastmoney-direct`，说明最近一次复盘使用的是东方财富实时链路。

如果显示 `local-json-snapshot`，说明使用的是本地真实行情快照，也属于真实数据路径。

## 股票池维护

股票池文件：

```text
app/universe/stock_pool.json
```

以后添加、删除、修改股票，主要改这个文件。

修改后运行：

```bash
python -m app.main validate-stock-pool
```

如果结果显示 `valid`，说明股票池结构正常。

这个校验会帮助检查：

- 是否有重复代码
- 是否缺少必要字段
- 板块分布是否偏移
- 优先级分布是否异常

## 常用命令

```bash
python -m app.main self-check
python -m app.main quote-connectivity-check
python -m app.main refresh-local-quote-pass-check
python -m app.main start-daily-news-workflow
python -m app.main latest-review
python -m app.main validate-stock-pool
python -m app.main full-regression-check
```

## 可视化页面

如果要打开本地仪表盘：

```bash
streamlit run app/dashboard/streamlit_app.py
```

仪表盘适合查看结果，但日常判断项目是否跑通，优先看终端里的 `self-check` 和 `latest-review`。

## PowerShell 脚本被阻止怎么办

如果直接运行 `.ps1` 脚本时出现“禁止执行脚本”，可以用：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_self_check.ps1
```

这只是临时绕过当前脚本执行限制，不会永久修改系统策略。

## 当前最重要结论

现在项目的主线已经从“能不能运行”推进到“真实数据能不能稳定进入每日复盘”。

日常最短记忆就是：

```bash
python -m app.main refresh-local-quote-pass-check
python -m app.main start-daily-news-workflow
python -m app.main latest-review
```

只要 `Real-data status` 是 `live-pass` 或 `snapshot-pass`，就可以继续进入每日阅读和复盘流程。
