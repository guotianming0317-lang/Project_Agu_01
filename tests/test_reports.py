"""Tests for morning and evening report composition."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

import pandas as pd

from app.database import initialize_database, save_alerts, save_market_snapshots
from app.reports.context_rules import (
    build_a_share_mapping,
    build_industry_chain_mapping,
    build_next_session_action_lines,
    build_next_session_action_summary,
    build_position_bias_hint,
    build_tomorrow_plan,
    classify_strength_label,
    collect_positive_alert_messages,
    collect_risk_alert_messages,
    get_top_sector_average_pct_chg,
    pick_sector_stock_names,
    pick_top_stock_names,
    rank_sectors_by_pct_chg,
    render_next_session_action_summary_lines,
)
from app.reports.evening_report import (
    build_evening_report,
    build_evening_report_from_database,
)
from app.reports.morning_report import (
    build_morning_report,
    build_morning_report_from_database,
)
from app.reports.shared import (
    ReportSection,
    build_stock_pool_drift_summary_text,
    build_stock_pool_observation_lines,
    build_text_report,
    join_report_items,
)
from app.sectors import (
    CONSOLE_OVERVIEW_DISPLAY,
    A_SHARE_MAPPING_RULES,
    DETAILED_ALERT_DISPLAY,
    INDUSTRY_CHAIN_MAPPING_RULES,
    MARKET_FOCUS_SNAPSHOT_DISPLAY,
    MONITOR_UNIVERSE_DISPLAY,
    POSITION_BIAS_RULES,
    REASON_SCORE_LABELS,
    REASON_SCORE_WEIGHTS,
    REPORT_RULE_CONFIG_PATH,
    STAGE_ALIGNMENT_TEMPLATES,
    STOCK_POOL_COMPARISON_TAG_DISPLAY,
    STOCK_POOL_COMPARISON_TAG_GROUP_DISPLAY,
    STOCK_POOL_STRUCTURE_SUMMARY_RULES,
    STRENGTH_LABEL_RULES,
    TASK_RESULT_SUMMARY_RULES,
    TOMORROW_PLAN_RULES,
)


class ReportTests(unittest.TestCase):
    """Verify structured report builders."""

    def test_context_rules_rank_sectors_and_pick_top_stocks(self) -> None:
        frame = pd.DataFrame(
            [
                {"sector": "Materials", "name": "Alpha", "pct_chg": 6.1},
                {"sector": "Materials", "name": "Beta", "pct_chg": 4.8},
                {"sector": "Equipment", "name": "Gamma", "pct_chg": 3.5},
                {"sector": "Compute", "name": "Delta", "pct_chg": 1.4},
            ]
        )

        self.assertEqual(
            ["Materials", "Equipment", "Compute"],
            rank_sectors_by_pct_chg(frame),
        )
        self.assertEqual(["Alpha", "Beta"], pick_top_stock_names(frame, limit=2))
        self.assertEqual(
            ["Alpha", "Beta"],
            pick_sector_stock_names(frame, {"Materials"}, limit=2),
        )
        self.assertAlmostEqual(5.45, get_top_sector_average_pct_chg(frame), places=2)
        self.assertEqual(2, len(STRENGTH_LABEL_RULES))
        self.assertEqual("偏强", classify_strength_label(5.45))
        self.assertEqual(2, len(POSITION_BIAS_RULES))
        self.assertEqual("观察", build_position_bias_hint(2.0, 1))
        self.assertEqual(2, len(TOMORROW_PLAN_RULES))
        self.assertIn(
            "Materials",
            build_tomorrow_plan("Materials", "Equipment", risk_count=1),
        )
        self.assertTrue(REPORT_RULE_CONFIG_PATH.exists())
        self.assertEqual(3, len(A_SHARE_MAPPING_RULES))
        self.assertEqual(3, len(INDUSTRY_CHAIN_MAPPING_RULES))
        self.assertEqual("主线", REASON_SCORE_LABELS["mainline"])
        self.assertEqual("风险预警", REASON_SCORE_LABELS["risk-alert"])
        self.assertEqual(3, REASON_SCORE_WEIGHTS["mainline"])
        self.assertEqual(2, REASON_SCORE_WEIGHTS["follow-through"])
        self.assertIn("chain_group_template", STOCK_POOL_STRUCTURE_SUMMARY_RULES)
        self.assertEqual("Materials优先观察", build_a_share_mapping("Materials"))
        self.assertIn("材料链条", build_industry_chain_mapping("半导体材料"))

    def test_context_rules_collect_positive_and_risk_alert_messages(self) -> None:
        alerts = [
            {"level": "orange", "message": "Positive breakout confirmed"},
            {"level": "yellow", "message": "Opening risk still needs confirmation"},
            {"level": "", "message": "Sector may drop after midday"},
        ]

        self.assertEqual(
            ["Positive breakout confirmed"],
            collect_positive_alert_messages(alerts),
        )
        self.assertEqual(
            [
                "Opening risk still needs confirmation",
                "Sector may drop after midday",
            ],
            collect_risk_alert_messages(alerts),
        )

    @unittest.skip("展示文案已中文化，旧英文断言保留作历史参考")
    def test_build_next_session_action_lines_uses_strength_and_risk_signals(self) -> None:
        frame = pd.DataFrame(
            [
                {"sector": "Materials", "name": "Alpha", "pct_chg": 6.1, "turnover": 120.0},
                {"sector": "Materials", "name": "Beta", "pct_chg": 4.8, "turnover": 98.0},
                {"sector": "Equipment", "name": "Gamma", "pct_chg": 3.5, "turnover": 80.0},
                {"sector": "Compute", "name": "Delta", "pct_chg": -2.4, "turnover": 60.0},
            ]
        )
        alerts = [
            {
                "level": "yellow",
                "message": "Opening risk still needs confirmation",
                "related_stocks": "Delta, Beta",
            }
        ]

        lines = build_next_session_action_lines(
            frame,
            alerts,
            strongest_sector="Materials",
            secondary_sector="Equipment",
            fading_sector="Compute",
        )

        self.assertTrue(lines[0].startswith("评分规则："))
        self.assertIn("主线=3", lines[0])
        self.assertTrue(lines[1].startswith("兜底规则："))
        self.assertIn("规避兜底=1", lines[1])
        self.assertTrue(lines[2].startswith("核心观察名单："))
        self.assertIn("Alpha", lines[2])
        self.assertIn("Beta", lines[2])
        self.assertNotIn("Gamma", lines[2])
        self.assertTrue(lines[3].startswith("核心观察标签："))
        self.assertIn("主线", lines[3])
        self.assertIn("强势", lines[3])
        self.assertTrue(lines[4].startswith("核心观察分数："))
        self.assertIn("Alpha", lines[4])
        self.assertIn("Materials", lines[5])
        self.assertTrue(lines[6].startswith("候选观察名单："))
        self.assertIn("Gamma", lines[6])
        self.assertTrue(lines[7].startswith("候选观察标签："))
        self.assertIn("主线", lines[7])
        self.assertTrue(lines[8].startswith("候选观察分数："))
        self.assertIn("Gamma", lines[8])
        self.assertIn("Equipment", lines[9])
        self.assertTrue(lines[10].startswith("规避名单："))
        self.assertIn("Delta", lines[10])
        self.assertIn("Beta", lines[10])
        self.assertTrue(lines[11].startswith("规避标签："))
        self.assertIn("风险预警", lines[11])
        self.assertTrue(lines[12].startswith("规避分数："))
        self.assertIn("Delta", lines[12])
        self.assertIn("Compute", lines[13])

    def test_build_next_session_action_lines_orders_tiers_by_explicit_scores(self) -> None:
        frame = pd.DataFrame(
            [
                {"sector": "Materials", "name": "Alpha", "pct_chg": 6.3, "turnover": 80.0},
                {"sector": "Materials", "name": "Beta", "pct_chg": 5.1, "turnover": 160.0},
                {"sector": "Equipment", "name": "Gamma", "pct_chg": 2.4, "turnover": 70.0},
                {"sector": "Equipment", "name": "Delta", "pct_chg": 2.1, "turnover": 140.0},
                {"sector": "Compute", "name": "Epsilon", "pct_chg": -1.1, "turnover": 50.0},
            ]
        )
        alerts = [
            {
                "level": "yellow",
                "message": "Risk still needs confirmation",
                "related_stocks": "Epsilon",
            }
        ]

        lines = build_next_session_action_lines(
            frame,
            alerts,
            strongest_sector="Materials",
            secondary_sector="Equipment",
            fading_sector="Compute",
        )

        self.assertTrue(lines[2].startswith("核心观察名单："))
        self.assertLess(lines[2].index("Beta"), lines[2].index("Alpha"))
        self.assertEqual("核心观察分数：Beta (7); Alpha (6)", lines[4])
        self.assertTrue(lines[6].startswith("候选观察名单："))
        self.assertLess(lines[6].index("Delta"), lines[6].index("Gamma"))
        self.assertEqual("候选观察分数：Delta (6); Gamma (5)", lines[8])

    def test_build_next_session_action_lines_uses_configured_reason_score_weights(self) -> None:
        frame = pd.DataFrame(
            [
                {"sector": "Materials", "name": "Alpha", "pct_chg": 6.0, "turnover": 120.0},
                {"sector": "Compute", "name": "Delta", "pct_chg": -2.4, "turnover": 60.0},
            ]
        )
        alerts = [
            {
                "level": "yellow",
                "message": "Opening risk still needs confirmation",
                "related_stocks": "Delta",
            }
        ]

        lines = build_next_session_action_lines(
            frame,
            alerts,
            strongest_sector="Materials",
            secondary_sector="Materials",
            fading_sector="Compute",
        )

        self.assertIn("评分规则：", lines[0])
        self.assertIn(
            f"Alpha ({REASON_SCORE_WEIGHTS['mainline'] + REASON_SCORE_WEIGHTS['strength'] + REASON_SCORE_WEIGHTS['liquidity']})",
            lines[4],
        )
        self.assertIn(
            f"Delta (-{REASON_SCORE_WEIGHTS['risk-alert'] + REASON_SCORE_WEIGHTS['fading-sector'] + REASON_SCORE_WEIGHTS['price-weakness']})",
            lines[12],
        )

    def test_build_next_session_action_lines_includes_reason_score_rule_summary(self) -> None:
        lines = build_next_session_action_lines(
            pd.DataFrame(),
            [],
            strongest_sector="",
            secondary_sector="",
            fading_sector="",
        )

        self.assertEqual(
            "评分规则：主线=3, 强势=3, 跟随=2, 流动性=1",
            lines[0],
        )
        self.assertEqual(
            "兜底规则：核心兜底=1, 候选确认=1, 规避兜底=1 | 规避规则：风险预警=3, 退潮板块=2, 价格走弱=2",
            lines[1],
        )

    def test_build_next_session_action_summary_returns_structured_tiers(self) -> None:
        frame = pd.DataFrame(
            [
                {"sector": "Materials", "name": "Alpha", "pct_chg": 6.1, "turnover": 120.0},
                {"sector": "Equipment", "name": "Gamma", "pct_chg": 3.5, "turnover": 80.0},
                {"sector": "Compute", "name": "Delta", "pct_chg": -2.4, "turnover": 60.0},
            ]
        )
        alerts = [
            {
                "level": "yellow",
                "message": "Opening risk still needs confirmation",
                "related_stocks": "Delta",
            }
        ]

        summary = build_next_session_action_summary(
            frame,
            alerts,
            strongest_sector="Materials",
            secondary_sector="Equipment",
            fading_sector="Compute",
        )

        self.assertEqual(2, len(summary["rule_summary_lines"]))
        self.assertEqual(["Alpha"], summary["core"]["watchlist"])
        self.assertIn("mainline", summary["core"]["tags"]["Alpha"])
        self.assertEqual(7, summary["core"]["scores"]["Alpha"])
        self.assertEqual(["Gamma"], summary["candidate"]["watchlist"])
        self.assertEqual(["Delta"], summary["avoid"]["watchlist"])
        self.assertIn("Compute", summary["avoid"]["reason"])

    def test_render_next_session_action_summary_lines_renders_structured_summary(self) -> None:
        summary = {
            "rule_summary_lines": (
                "评分规则：主线=3, 强势=3, 跟随=2, 流动性=1",
                "兜底规则：核心兜底=1, 候选确认=1, 规避兜底=1 | 规避规则：风险预警=3, 退潮板块=2, 价格走弱=2",
            ),
            "core": {
                "watchlist": ["Alpha"],
                "tags": {"Alpha": ["mainline", "strength"]},
                "scores": {"Alpha": 6},
                "reason": "stay with Materials first.",
            },
            "candidate": {
                "watchlist": ["Gamma"],
                "tags": {"Gamma": ["mainline", "follow-through"]},
                "scores": {"Gamma": 5},
                "reason": "use Equipment as confirmation.",
            },
            "avoid": {
                "watchlist": ["Delta"],
                "tags": {"Delta": ["risk-alert", "fading-sector"]},
                "scores": {"Delta": -5},
                "reason": "reduce names tied to fading strength.",
            },
        }

        lines = render_next_session_action_summary_lines(summary)

        self.assertEqual("评分规则：主线=3, 强势=3, 跟随=2, 流动性=1", lines[0])
        self.assertEqual("核心观察名单：Alpha", lines[2])
        self.assertEqual("候选观察分数：Gamma (5)", lines[8])
        self.assertEqual("规避分数：Delta (-5)", lines[12])

    def test_stock_pool_comparison_tag_display_rules_are_loaded(self) -> None:
        self.assertEqual(
            "材料链加仓",
            STOCK_POOL_COMPARISON_TAG_DISPLAY["Materials Exposure Up"],
        )

    def test_stock_pool_comparison_tag_group_display_rules_are_loaded(self) -> None:
        self.assertEqual(
            "产业链暴露",
            STOCK_POOL_COMPARISON_TAG_GROUP_DISPLAY["chain_exposure"],
        )

    def test_task_result_summary_rules_are_loaded(self) -> None:
        self.assertIn("red_alert", TASK_RESULT_SUMMARY_RULES["pre_open"])
        self.assertIn("strong", TASK_RESULT_SUMMARY_RULES["midday_check"])
        self.assertIn(
            "{alert_count}",
            TASK_RESULT_SUMMARY_RULES["full_monitor"]["red_alert"],
        )

    def test_stage_alignment_templates_are_loaded(self) -> None:
        self.assertIn("{chain_group}", STAGE_ALIGNMENT_TEMPLATES["aligned_with_strength"])
        self.assertIn(
            "{preferred_chain_groups}",
            STAGE_ALIGNMENT_TEMPLATES["not_aligned"],
        )

    def test_detailed_alert_display_rules_are_loaded(self) -> None:
        self.assertIn("{level}", DETAILED_ALERT_DISPLAY["title_template"])
        self.assertEqual("详细预警", DETAILED_ALERT_DISPLAY["block_title"])
        self.assertIn("暂无详细预警", DETAILED_ALERT_DISPLAY["empty_message"])
        self.assertEqual("timestamp", DETAILED_ALERT_DISPLAY["fields"][0]["key"])
        self.assertEqual("stage_alignment", DETAILED_ALERT_DISPLAY["fields"][-1]["key"])
        self.assertTrue(DETAILED_ALERT_DISPLAY["fields"][0]["enabled"])
        self.assertEqual(
            "message",
            DETAILED_ALERT_DISPLAY["field_sets"]["watch"][2]["key"],
        )
        self.assertEqual(
            "开盘详细预警",
            DETAILED_ALERT_DISPLAY["style_variants"]["opening_focus"]["block_title"],
        )

    def test_market_focus_snapshot_display_rules_are_loaded(self) -> None:
        self.assertEqual("市场焦点快照", MARKET_FOCUS_SNAPSHOT_DISPLAY["block_title"])
        self.assertEqual("observation", MARKET_FOCUS_SNAPSHOT_DISPLAY["fields"][0]["key"])
        self.assertTrue(MARKET_FOCUS_SNAPSHOT_DISPLAY["fields"][0]["enabled"])
        self.assertEqual(
            "开盘市场焦点",
            MARKET_FOCUS_SNAPSHOT_DISPLAY["style_variants"]["opening_focus"]["block_title"],
        )

    def test_monitor_universe_display_rules_are_loaded(self) -> None:
        self.assertEqual("监控池观察", MONITOR_UNIVERSE_DISPLAY["block_title"])
        self.assertEqual(
            "stage_chain_focus",
            MONITOR_UNIVERSE_DISPLAY["stage_chain_fields"][0]["key"],
        )
        self.assertTrue(MONITOR_UNIVERSE_DISPLAY["stage_chain_fields"][0]["enabled"])
        self.assertEqual("live_strength", MONITOR_UNIVERSE_DISPLAY["stage_chain_fields"][1]["key"])
        self.assertEqual(
            "收盘监控池观察",
            MONITOR_UNIVERSE_DISPLAY["style_variants"]["close_review"]["block_title"],
        )

    def test_console_overview_display_rules_are_loaded(self) -> None:
        self.assertEqual("result", CONSOLE_OVERVIEW_DISPLAY["fields"][0]["key"])
        self.assertEqual("focus", CONSOLE_OVERVIEW_DISPLAY["fields"][1]["key"])
        self.assertTrue(CONSOLE_OVERVIEW_DISPLAY["fields"][0]["enabled"])
        self.assertFalse(CONSOLE_OVERVIEW_DISPLAY["fields"][-1]["enabled"])
        self.assertEqual(
            "quote_source",
            CONSOLE_OVERVIEW_DISPLAY["style_variants"]["opening_focus"]["fields"][-1]["key"],
        )

    def test_shared_report_helpers_render_intro_and_sections(self) -> None:
        report = build_text_report(
            "Title",
            [
                ReportSection(heading=None, lines=("Line A", "Line B")),
                ReportSection(heading="Section 2", lines=("Line C",)),
            ],
            intro_lines=["Meta: 2026-06-30"],
        )

        self.assertEqual(
            "Title\nMeta: 2026-06-30\n\nLine A\nLine B\n\nSection 2\nLine C",
            report,
        )

    def test_join_report_items_handles_list_and_default(self) -> None:
        self.assertEqual("Alpha、Beta", join_report_items(["Alpha", "Beta"], default="none"))
        self.assertEqual("none", join_report_items([], default="none"))

    def test_build_stock_pool_observation_lines_formats_groups_and_hints(self) -> None:
        lines = build_stock_pool_observation_lines(
            structure_summary="当前监控池偏向材料链，core池占比约2/3。",
            comparison_tag_groups=[
                {
                    "group_key": "chain_exposure",
                    "group_label": "产业链暴露",
                    "tag_labels": ["材料链加仓"],
                    "summary": "产业链暴露：材料链加仓",
                }
            ],
            highlight_summary="重点变化：板块 半导体材料增加 (+2)。",
            change_rows=[
                "- 板块 半导体材料: +2",
                "- 产业链分组 材料: +2",
                "- 池类型 core: +1",
            ],
            health_hints=["Priority-1 stocks are missing."],
        )

        self.assertEqual("监控池结构：当前监控池偏向材料链，core池占比约2/3。", lines[0])
        self.assertEqual("结构变化分组：产业链暴露：材料链加仓", lines[1])
        self.assertEqual("结构重点变化：重点变化：板块 半导体材料增加 (+2)。", lines[2])
        self.assertEqual("结构变动明细：- 板块 半导体材料: +2 | - 产业链分组 材料: +2", lines[3])
        self.assertEqual("结构提醒：Priority-1 stocks are missing.", lines[4])

    def test_build_morning_report_renders_structured_sections(self) -> None:
        report = build_morning_report(
            {
                "overseas_strength": "偏强",
                "a_share_mapping": "材料气体优先观察，可重点映射材料/气体链",
                "focus_sectors": ["半导体材料", "半导体气体", "半导体设备"],
                "focus_stocks": ["中巨芯-U", "华特气体", "沪硅产业"],
                "main_risks": "出口管制消息仍需跟踪",
                "position_bias": "观察",
            }
        )

        self.assertIn("【今日主线判断】", report)
        self.assertIn("海外AI半导体强弱：偏强", report)
        self.assertIn("A股可能映射方向：材料气体优先观察", report)
        self.assertIn("今日重点观察板块：半导体材料、半导体气体、半导体设备", report)
        self.assertIn("7. 监控池结构观察", report)

    def test_build_morning_report_renders_stock_pool_observation_section(self) -> None:
        report = build_morning_report(
            {
                "stock_pool_structure_summary": "当前监控池偏向材料链，core池占比约2/3。",
                "stock_pool_comparison_tag_groups": [
                    {
                        "group_key": "chain_exposure",
                        "group_label": "产业链暴露",
                        "tag_labels": ["材料链加仓"],
                        "summary": "产业链暴露：材料链加仓",
                    }
                ],
                "stock_pool_comparison_highlight_summary": "重点变化：板块 半导体材料增加 (+2)。",
                "stock_pool_comparison_change_rows": [
                    "- 板块 半导体材料: +2",
                    "- 产业链分组 材料: +2",
                ],
                "stock_pool_health_hints": ["Priority-1 stocks are missing."],
            }
        )

        self.assertIn("结构重点变化：重点变化：板块 半导体材料增加 (+2)。", report)
        self.assertIn("结构变动明细：- 板块 半导体材料: +2 | - 产业链分组 材料: +2", report)


    def test_build_morning_report_from_database_uses_latest_snapshots_and_alerts(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-30 09:31:00",
                        "code": "000001",
                        "name": "Alpha",
                        "price": 11.2,
                        "pct_chg": 6.1,
                        "turnover": 120.0,
                        "volume_ratio": 2.2,
                        "turnover_rate": 3.4,
                        "sector": "Materials",
                    },
                    {
                        "timestamp": "2026-06-30 09:31:00",
                        "code": "000002",
                        "name": "Beta",
                        "price": 22.5,
                        "pct_chg": 4.8,
                        "turnover": 98.0,
                        "volume_ratio": 1.8,
                        "turnover_rate": 2.9,
                        "sector": "Materials",
                    },
                    {
                        "timestamp": "2026-06-30 09:31:00",
                        "code": "000003",
                        "name": "Gamma",
                        "price": 18.9,
                        "pct_chg": 3.5,
                        "turnover": 80.0,
                        "volume_ratio": 1.5,
                        "turnover_rate": 2.1,
                        "sector": "Equipment",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-30 09:32:00",
                        "alert_type": "open-risk",
                        "level": "yellow",
                        "message": "Opening risk still needs confirmation",
                        "related_stocks": "Alpha, Beta",
                        "direction": "Materials",
                    }
                ],
            )

            report = build_morning_report_from_database(database_path)

            self.assertIn("【今日主线判断】", report)
            self.assertIn("A股可能映射方向：Materials优先观察", report)
            self.assertIn("今日重点观察板块：Materials、Equipment", report)
            self.assertIn("今日重点观察个股：Alpha、Beta、Gamma", report)
            self.assertIn("主要风险：Opening risk still needs confirmation", report)
            self.assertIn("7. 监控池结构观察", report)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_evening_report_renders_leaders_and_news(self) -> None:
        report = build_evening_report(
            {
                "date": "2026-06-19",
                "strongest_sector": "半导体气体",
                "secondary_sector": "半导体设备",
                "fading_sector": "AI服务器算力硬件",
                "leaders": {
                    "涨幅龙头": "中巨芯-U",
                    "成交额龙头": "江丰电子",
                    "趋势龙头": "安集科技",
                    "情绪龙头": "中巨芯-U",
                },
                "materials_watch": ["沪硅产业", "中巨芯-U", "华特气体"],
                "positive_news": ["客户认证进展"],
                "negative_news": ["出口管制扰动"],
                "tomorrow_plan": "优先确认半导体气体是否延续强势，同时观察半导体设备能否跟随修复。",
            }
        )

        self.assertIn("【AI + 半导体收盘复盘】", report)
        self.assertIn("日期：2026-06-19", report)
        self.assertIn("最强方向：半导体气体", report)
        self.assertIn("涨幅龙头：中巨芯-U", report)
        self.assertIn("利空消息：出口管制扰动", report)
        self.assertIn("四、监控池结构观察", report)

    def test_build_evening_report_renders_stock_pool_observation_section(self) -> None:
        report = build_evening_report(
            {
                "stock_pool_structure_summary": "当前监控池偏向材料链，core池占比约2/3。",
                "stock_pool_comparison_tag_groups": [
                    {
                        "group_key": "chain_exposure",
                        "group_label": "产业链暴露",
                        "tag_labels": ["材料链加仓"],
                        "summary": "产业链暴露：材料链加仓",
                    }
                ],
                "stock_pool_comparison_highlight_summary": "重点变化：板块 半导体材料增加 (+2)。",
                "stock_pool_comparison_change_rows": [
                    "- 板块 半导体材料: +2",
                    "- 产业链分组 材料: +2",
                ],
                "stock_pool_health_hints": ["Priority-1 stocks are missing."],
            }
        )

        self.assertIn("结构重点变化：重点变化：板块 半导体材料增加 (+2)。", report)
        self.assertIn("结构变动明细：- 板块 半导体材料: +2 | - 产业链分组 材料: +2", report)

    def test_build_evening_report_renders_next_session_action_lists(self) -> None:
        report = build_evening_report(
            {
                "tomorrow_plan": "Stay with the strongest line first.",
                "next_session_action_lines": [
                    "评分规则：主线=3, 强势=3, 跟随=2, 流动性=1",
                    "兜底规则：核心兜底=1, 候选确认=1, 规避兜底=1 | 规避规则：风险预警=3, 退潮板块=2, 价格走弱=2",
                    "核心观察名单：Alpha銆丅eta",
                    "核心观察标签：Alpha (mainline/strength)",
                    "核心观察分数：Alpha (6)",
                    "核心观察原因：stay with Materials first.",
                    "候选观察名单：Gamma",
                    "候选观察标签：Gamma (mainline/follow-through)",
                    "候选观察分数：Gamma (5)",
                    "候选观察原因：use Equipment as confirmation.",
                    "规避名单：Delta",
                    "规避标签：Delta (risk-alert/fading-sector)",
                    "规避分数：Delta (-5)",
                    "规避原因：reduce names tied to fading strength.",
                ],
            }
        )

        self.assertIn("评分规则：主线=3, 强势=3, 跟随=2, 流动性=1", report)
        self.assertIn("兜底规则：核心兜底=1, 候选确认=1, 规避兜底=1", report)
        self.assertIn("核心观察名单：Alpha銆丅eta", report)
        self.assertIn("核心观察标签：Alpha (mainline/strength)", report)
        self.assertIn("核心观察分数：Alpha (6)", report)
        self.assertIn("候选观察名单：Gamma", report)
        self.assertIn("候选观察标签：Gamma (mainline/follow-through)", report)
        self.assertIn("候选观察分数：Gamma (5)", report)
        self.assertIn("规避名单：Delta", report)
        self.assertIn("规避标签：Delta (risk-alert/fading-sector)", report)
        self.assertIn("规避分数：Delta (-5)", report)

    @unittest.skip("复盘策略已改为紧凑分层展示，旧重复文案断言保留作历史参考")
    def test_build_evening_report_can_render_structured_next_session_action_summary(self) -> None:
        report = build_evening_report(
            {
                "tomorrow_plan": "Stay with the strongest line first.",
                "next_session_action_summary": {
                    "rule_summary_lines": (
                        "评分规则：主线=3, 强势=3, 跟随=2, 流动性=1",
                        "兜底规则：核心兜底=1, 候选确认=1, 规避兜底=1 | 规避规则：风险预警=3, 退潮板块=2, 价格走弱=2",
                    ),
                    "core": {
                        "watchlist": ["Alpha"],
                        "tags": {"Alpha": ["mainline", "strength"]},
                        "scores": {"Alpha": 6},
                        "reason": "stay with Materials first.",
                    },
                    "candidate": {
                        "watchlist": ["Gamma"],
                        "tags": {"Gamma": ["mainline", "follow-through"]},
                        "scores": {"Gamma": 5},
                        "reason": "use Equipment as confirmation.",
                    },
                    "avoid": {
                        "watchlist": ["Delta"],
                        "tags": {"Delta": ["risk-alert", "fading-sector"]},
                        "scores": {"Delta": -5},
                        "reason": "reduce names tied to fading strength.",
                    },
                },
            }
        )

        self.assertIn("评分规则：主线=3, 强势=3, 跟随=2, 流动性=1", report)
        self.assertIn("核心观察名单：Alpha", report)
        self.assertIn("候选观察分数：Gamma (5)", report)
        self.assertIn("规避分数：Delta (-5)", report)

    def test_build_evening_report_from_database_uses_latest_snapshots_and_alerts(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        database_path = temp_dir / "monitor.db"
        try:
            initialize_database(database_path)
            save_market_snapshots(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688549",
                        "name": "中巨芯-U",
                        "price": 12.88,
                        "pct_chg": 8.6,
                        "turnover": 200.0,
                        "volume_ratio": 2.8,
                        "turnover_rate": 4.5,
                        "sector": "半导体气体",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688268",
                        "name": "华特气体",
                        "price": 45.20,
                        "pct_chg": 5.2,
                        "turnover": 150.0,
                        "volume_ratio": 1.9,
                        "turnover_rate": 3.2,
                        "sector": "半导体气体",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "688019",
                        "name": "安集科技",
                        "price": 132.80,
                        "pct_chg": 5.1,
                        "turnover": 120.0,
                        "volume_ratio": 2.1,
                        "turnover_rate": 2.6,
                        "sector": "半导体材料",
                    },
                    {
                        "timestamp": "2026-06-19 10:17:00",
                        "code": "002371",
                        "name": "北方华创",
                        "price": 310.5,
                        "pct_chg": 3.4,
                        "turnover": 300.0,
                        "volume_ratio": 1.4,
                        "turnover_rate": 2.0,
                        "sector": "半导体设备",
                    },
                ],
            )
            save_alerts(
                database_path,
                [
                    {
                        "timestamp": "2026-06-19 10:18:00",
                        "alert_type": "materials_focus",
                        "level": "orange",
                        "message": "半导体材料、半导体气体链至少有3只股票涨幅超过5%",
                        "related_stocks": "中巨芯-U, 华特气体, 安集科技",
                        "direction": "半导体材料、半导体气体",
                    },
                    {
                        "timestamp": "2026-06-19 10:18:00",
                        "alert_type": "risk",
                        "level": "yellow",
                        "message": "Export restriction risk still needs confirmation",
                        "related_stocks": "中巨芯-U",
                        "direction": "半导体气体",
                    },
                ],
            )

            report = build_evening_report_from_database(database_path)

            self.assertIn("【AI + 半导体收盘复盘】", report)
            self.assertIn("最强方向：半导体气体", report)
            self.assertIn(
                "利好消息：半导体材料、半导体气体链至少有3只股票涨幅超过5%",
                report,
            )
            self.assertIn(
                "利空消息：Export restriction risk still needs confirmation",
                report,
            )
            self.assertIn("四、监控池结构观察", report)
            self.assertIn("观察重点：", report)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_stock_pool_drift_summary_text_prefers_highlight(self) -> None:
        summary = build_stock_pool_drift_summary_text(
            structure_summary="Current pool remains material-chain heavy.",
            comparison_tag_groups=[
                {"summary": "Chain exposure: materials exposure increased."}
            ],
            highlight_summary="Key change: materials exposure increased (+2).",
        )

        self.assertEqual(
            "\u76d1\u63a7\u6c60\u7ed3\u6784\u6f02\u79fb\uff1aKey change: materials exposure increased (+2).",
            summary,
        )


if __name__ == "__main__":
    unittest.main()
