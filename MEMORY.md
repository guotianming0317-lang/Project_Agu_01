# Project Memory

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

Test command used successfully:

- `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m unittest discover -s tests -v`

## Latest Completed Slice

`app/data_sources/akshare_client.py` now supports:

- normalized English output fields
- stable required column ordering
- tolerant handling of partial rows
- filtering quotes to the configured observation universe

This is still the local normalization layer only. Real AKShare fetching remains
the next integration step.

## Next TDD Slice

Implement the next business layer with tests for:

- sector aggregation from quote rows
- leader scoring and top-3 output per sector
- explainable leader type classification

## Important Constraints

- use `apply_patch` for file edits
- do not rely on `python` or `py` being on PATH in this environment
- bundled Python path is:
  `C:\Users\NO.1\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`

## Notes For Future Turns

- If context gets compressed, resume from the "Next TDD Slice" section first.
- Keep phase one rule-based and explainable.
- Prefer stable local behavior over premature optimization.
