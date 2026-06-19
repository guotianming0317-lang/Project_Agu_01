# Project Notes For Codex

## Purpose

Build a lightweight AI + semiconductor A-share monitoring system for research support.

## Phase one priorities

- keep the code easy to read and extend
- prefer explicit rules over opaque heuristics
- keep external integrations optional until the local demo is stable

## Conventions

- Python 3.11+
- SQLite first, PostgreSQL later
- APScheduler for timed jobs
- pandas for tabular data
- console notifications before webhook integrations
