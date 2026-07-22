"""Tests for dashboard presentation configs."""

from __future__ import annotations

import unittest

from app.dashboard.presentation import (
    build_business_role_specs,
    build_chart_specs,
    build_content_panel_style_spec,
    build_control_band_layout_specs,
    build_control_band_specs,
    build_display_field_registry,
    build_health_group_specs,
    build_health_info_block_specs,
    build_health_meta_specs,
    build_home_content_group_layout_specs,
    build_home_header_layout_specs,
    build_home_header_style_spec,
    build_home_priority_content_layout_specs,
    build_intro_panel_style_spec,
    build_page_segment_template_specs,
    build_grouped_summary_info_block_specs,
    build_content_section_specs,
    build_kpi_card_specs,
    build_kpi_summary_layout_specs,
    build_kpi_value_format_spec,
    build_metric_group_style_spec,
    build_kpi_panel_style_spec,
    build_page_layout_specs,
    build_panel_container_style_spec,
    build_summary_panel_style_spec,
    build_task_template_specs,
    build_time_phase_specs,
    build_theme_spec,
    build_view_mode_specs,
    build_view_role_strategy_specs,
    build_view_variant_specs,
    resolve_dashboard_view_spec,
)


class DashboardPresentationTests(unittest.TestCase):
    """Verify dashboard presentation metadata stays easy to replace."""

    def test_build_chart_specs_returns_separate_style_metadata(self) -> None:
        specs = build_chart_specs()

        self.assertIn("sector_strength", specs)
        self.assertIn("top_movers", specs)
        self.assertEqual("default", specs["sector_strength"]["copy_variant"])
        self.assertEqual("bar", specs["sector_strength"]["chart_type"])
        self.assertEqual("accent", specs["sector_strength"]["tone"])
        self.assertEqual("warning", specs["top_movers"]["tone"])
        self.assertEqual(
            "\u677f\u5757\u5f3a\u5ea6",
            specs["sector_strength"]["copy_variants"]["business_cn"]["title"],
        )
        self.assertEqual(
            "\u677f\u5757",
            specs["sector_strength"]["copy_variants"]["business_cn"]["display_fields"][0]["label"],
        )
        self.assertEqual(
            "\u5e73\u5747\u6da8\u8dcc",
            specs["sector_strength"]["copy_variants"]["business_cn"]["y_axis_label"],
        )
        self.assertEqual(
            "\u9886\u6da8\u4e2a\u80a1",
            specs["top_movers"]["copy_variants"]["business_cn"]["title"],
        )
        self.assertEqual(
            "\u540d\u79f0",
            specs["top_movers"]["copy_variants"]["business_cn"]["display_fields"][0]["label"],
        )
        self.assertEqual(
            "\u6da8\u8dcc\u5e45",
            specs["top_movers"]["copy_variants"]["business_cn"]["y_axis_label"],
        )
        self.assertEqual("sector", specs["sector_strength"]["x_key"])
        self.assertEqual("avg_pct_chg", specs["sector_strength"]["y_key"])
        self.assertIn("accent", specs["sector_strength"]["palette"])
        self.assertEqual("sector", specs["sector_strength"]["display_fields"][0]["key"])
        self.assertEqual("avg_pct_chg", specs["sector_strength"]["display_fields"][1]["key"])
        self.assertEqual("signed_percent_1", specs["sector_strength"]["display_fields"][1]["format_key"])
        self.assertEqual("analysis", specs["sector_strength"]["role_key"])
        self.assertEqual(5, specs["sector_strength"]["module_priority"])
        self.assertEqual("name", specs["top_movers"]["display_fields"][0]["key"])
        self.assertEqual("pct_chg", specs["top_movers"]["display_fields"][1]["key"])
        self.assertEqual("signed_percent_1", specs["top_movers"]["display_fields"][1]["format_key"])
        self.assertEqual("analysis", specs["top_movers"]["role_key"])
        self.assertEqual(6, specs["top_movers"]["module_priority"])

    def test_build_business_role_specs_returns_shared_role_labels(self) -> None:
        specs = build_business_role_specs()

        self.assertEqual("Decision", specs["decision"]["label"])
        self.assertIn("next action", specs["decision"]["supporting_copy"])
        self.assertEqual("\u51b3\u7b56", specs["business_cn:decision"]["label"])
        self.assertEqual("\u5f52\u6863", specs["business_cn:archive"]["label"])

    def test_build_kpi_card_specs_returns_replaceable_copy(self) -> None:
        specs_a = build_kpi_card_specs()
        specs_b = build_kpi_card_specs()

        self.assertEqual("Latest Batch", specs_a[0]["label"])
        self.assertEqual("latest_timestamp", specs_a[0]["value_key"])
        self.assertEqual("text", specs_a[0]["card_type"])
        self.assertEqual("neutral", specs_a[0]["tone"])
        self.assertEqual("Data Status", specs_a[1]["label"])
        self.assertEqual("quote_status_summary", specs_a[1]["value_key"])
        self.assertEqual("text", specs_a[1]["card_type"])
        self.assertEqual("info", specs_a[1]["tone"])
        self.assertEqual("Main-Line View", specs_a[2]["label"])
        self.assertEqual("mainline_summary", specs_a[2]["value_key"])
        self.assertEqual("text", specs_a[2]["card_type"])
        self.assertEqual("accent", specs_a[2]["tone"])
        self.assertEqual("Pool Drift", specs_a[3]["label"])
        self.assertEqual("stock_pool_drift_summary", specs_a[3]["value_key"])
        self.assertEqual("text", specs_a[3]["card_type"])
        self.assertEqual("info", specs_a[3]["tone"])
        self.assertEqual("Risk State", specs_a[4]["label"])
        self.assertEqual("risk_summary", specs_a[4]["value_key"])
        self.assertEqual("text", specs_a[4]["card_type"])
        self.assertEqual("warning", specs_a[4]["tone"])
        self.assertEqual("numeric", specs_a[5]["card_type"])
        self.assertEqual("accent", specs_a[5]["tone"])
        self.assertEqual("numeric", specs_a[6]["card_type"])
        self.assertEqual("warning", specs_a[6]["tone"])
        self.assertEqual("positive_alert_count", specs_a[5]["value_key"])
        self.assertEqual("negative_alert_count", specs_a[6]["value_key"])
        self.assertIsNot(specs_a, specs_b)
        self.assertIsNot(specs_a[0], specs_b[0])
        self.assertEqual("timestamp", specs_a[0]["format_key"])
        self.assertEqual("default", specs_a[1]["format_key"])
        self.assertEqual("default", specs_a[2]["format_key"])
        self.assertEqual("default", specs_a[3]["format_key"])
        self.assertEqual("default", specs_a[4]["format_key"])
        self.assertEqual("count", specs_a[5]["format_key"])

    def test_build_kpi_card_specs_returns_business_cn_copy(self) -> None:
        specs = build_kpi_card_specs("business_cn")

        self.assertEqual("\u6700\u65b0\u6279\u6b21", specs[0]["label"])
        self.assertEqual("\u6570\u636e\u72b6\u6001", specs[1]["label"])
        self.assertEqual("\u4e3b\u7ebf\u7ed3\u8bba", specs[2]["label"])
        self.assertEqual("\u76d1\u63a7\u6c60\u6f02\u79fb", specs[3]["label"])
        self.assertEqual("\u98ce\u9669\u72b6\u6001", specs[4]["label"])
        self.assertEqual("\u6b63\u5411\u63d0\u9192", specs[5]["label"])
        self.assertEqual("\u8d1f\u5411\u63d0\u9192", specs[6]["label"])
        self.assertEqual("\u63d0\u9192\u603b\u6570", specs[7]["label"])
        self.assertEqual("business_cn", specs[1]["copy_variant"])
        self.assertEqual("business_cn", specs[2]["copy_variant"])
        self.assertEqual("business_cn", specs[3]["copy_variant"])
        self.assertEqual("business_cn", specs[1]["copy_variant"])
        self.assertIn("copy_variants", specs[1])
        self.assertIn("copy_variants", specs[2])
        self.assertIn("copy_variants", specs[3])
        self.assertIn("copy_variants", specs[4])

    def test_build_kpi_card_specs_exposes_replaceable_pool_drift_copy_layers(self) -> None:
        data_status_spec = build_kpi_card_specs()[1]
        mainline_spec = build_kpi_card_specs()[2]
        drift_spec = build_kpi_card_specs()[3]
        risk_spec = build_kpi_card_specs()[4]

        self.assertEqual("Current quote-source readiness state", data_status_spec["caption"])
        self.assertEqual(38, data_status_spec["value_max_length"])
        self.assertIn("compact", data_status_spec["copy_variants"])
        self.assertIn("priority", data_status_spec["copy_variants"])
        self.assertEqual("Data Mode", data_status_spec["copy_variants"]["compact"]["label"])
        self.assertEqual("warning", data_status_spec["copy_variants"]["priority"]["tone"])

        self.assertEqual("Top-line market leadership conclusion", mainline_spec["caption"])
        self.assertEqual(46, mainline_spec["value_max_length"])
        self.assertIn("compact", mainline_spec["copy_variants"])
        self.assertIn("priority", mainline_spec["copy_variants"])
        self.assertEqual("Main Line", mainline_spec["copy_variants"]["compact"]["label"])
        self.assertEqual("warning", mainline_spec["copy_variants"]["priority"]["tone"])

        self.assertEqual("Top-line stock-pool structure drift cue", drift_spec["caption"])
        self.assertEqual(42, drift_spec["value_max_length"])
        self.assertIn("compact", drift_spec["copy_variants"])
        self.assertIn("priority", drift_spec["copy_variants"])
        self.assertEqual("Pool Bias", drift_spec["copy_variants"]["compact"]["label"])
        self.assertEqual("warning", drift_spec["copy_variants"]["priority"]["tone"])

        self.assertEqual("Top-line risk balance conclusion", risk_spec["caption"])
        self.assertEqual(42, risk_spec["value_max_length"])
        self.assertIn("compact", risk_spec["copy_variants"])
        self.assertIn("priority", risk_spec["copy_variants"])
        self.assertEqual("Risk", risk_spec["copy_variants"]["compact"]["label"])
        self.assertEqual("error", risk_spec["copy_variants"]["priority"]["tone"])

    def test_build_kpi_summary_layout_specs_returns_replaceable_summary_layouts(self) -> None:
        specs_a = build_kpi_summary_layout_specs()
        specs_b = build_kpi_summary_layout_specs()

        self.assertIn("default", specs_a)
        self.assertIn("quick_scan", specs_a)
        self.assertIn("business_cn", specs_a)
        self.assertEqual("latest_timestamp", specs_a["default"]["card_order"][0])
        self.assertEqual("quote_status_summary", specs_a["default"]["card_order"][1])
        self.assertEqual("mainline_summary", specs_a["quick_scan"]["card_order"][0])
        self.assertEqual("quote_status_summary", specs_a["quick_scan"]["card_order"][1])
        self.assertEqual(
            "priority",
            specs_a["quick_scan"]["card_variant_overrides"]["mainline_summary"],
        )
        self.assertEqual(
            "compact",
            specs_a["quick_scan"]["card_variant_overrides"]["quote_status_summary"],
        )
        self.assertEqual(
            "business_cn",
            specs_a["business_cn"]["card_variant_overrides"]["risk_summary"],
        )
        self.assertIsNot(specs_a, specs_b)

    def test_build_kpi_value_format_spec_returns_replaceable_formatter_rules(self) -> None:
        format_spec_a = build_kpi_value_format_spec()
        format_spec_b = build_kpi_value_format_spec()

        self.assertIn("timestamp", format_spec_a)
        self.assertIn("count", format_spec_a)
        self.assertIn("percent_1", format_spec_a)
        self.assertIn("signed_percent_1", format_spec_a)
        self.assertEqual("No data", format_spec_a["timestamp"]["empty_value"])
        self.assertEqual("%Y-%m-%d %H:%M", format_spec_a["timestamp"]["datetime_format"])
        self.assertTrue(format_spec_a["count"]["thousands_separator"])
        self.assertEqual("%", format_spec_a["percent_1"]["suffix"])
        self.assertTrue(format_spec_a["signed_percent_1"]["show_plus"])
        self.assertIsNot(format_spec_a, format_spec_b)

    def test_build_kpi_panel_style_spec_returns_business_cn_copy(self) -> None:
        style_spec = build_kpi_panel_style_spec("business_cn")

        self.assertEqual("\u6307\u6807\u533a", style_spec["section_label"])
        self.assertEqual("\u6307\u6807\u5361", style_spec["metric_label"])
        self.assertEqual("\u5f53\u524d\u6279\u6b21\u4e0e\u63d0\u9192\u6982\u89c8", style_spec["section_body"])
        self.assertEqual("\u5f53\u524d\u76d1\u63a7\u9876\u5c42\u6982\u89c8", style_spec["section_supporting_copy"])
        self.assertEqual("\u5173\u952e\u6307\u6807", style_spec["metric_group_body"])
        self.assertEqual("\u6838\u5fc3\u76d1\u63a7\u6307\u6807", style_spec["compact_section_supporting_copy"])
        self.assertEqual("\u9876\u90e8\u5173\u952e\u8ba1\u6570\u5361", style_spec["metric_supporting_copy"])

    def test_build_display_field_registry_returns_reusable_field_sets(self) -> None:
        registry_a = build_display_field_registry()
        registry_b = build_display_field_registry()

        self.assertIn("sector_strength_table", registry_a)
        self.assertIn("latest_alerts_detail", registry_a)
        self.assertEqual("sector", registry_a["sector_strength_table"][0]["key"])
        self.assertEqual("signed_percent_1", registry_a["sector_strength_table"][1]["format_key"])
        self.assertEqual("timestamp", registry_a["latest_alerts_detail"][0]["key"])
        self.assertEqual("timestamp", registry_a["latest_alerts_detail"][0]["format_key"])
        self.assertEqual("Leading group: ", registry_a["strongest_sector_detail"][0]["prefix"])
        self.assertIsNot(registry_a, registry_b)

    def test_build_health_group_specs_returns_reusable_health_sections(self) -> None:
        specs_a = build_health_group_specs()
        specs_b = build_health_group_specs()

        self.assertEqual("unknown_sectors", specs_a["issue_groups"][0]["value_key"])
        self.assertEqual("unknown_markets", specs_a["issue_groups"][2]["value_key"])
        self.assertEqual("unknown_sector_suggestions", specs_a["suggestion_groups"][0]["value_key"])
        self.assertEqual("market", specs_a["suggestion_groups"][2]["item_label"])
        self.assertEqual("Validation Issues", specs_a["group_titles"]["issue_title"])
        self.assertEqual("Structure Comparison", specs_a["group_titles"]["comparison_title"])
        self.assertEqual("Health Hints", specs_a["group_titles"]["hint_title"])
        self.assertEqual("duplicate_title", specs_a["detail_sections"][0]["title_key"])
        self.assertEqual("comparison_rows", specs_a["detail_sections"][4]["rows_key"])
        self.assertEqual("hint_rows", specs_a["detail_sections"][5]["rows_key"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_health_meta_specs_returns_reusable_meta_rows(self) -> None:
        specs_a = build_health_meta_specs()
        specs_b = build_health_meta_specs()

        self.assertEqual("risk_label", specs_a[0]["value_key"])
        self.assertEqual("risk_level", specs_a[0]["label_key"])
        self.assertEqual("source_path", specs_a[1]["value_key"])
        self.assertEqual("registered_sectors", specs_a[2]["value_key"])
        self.assertEqual("count", specs_a[2]["value_mode"])
        self.assertEqual("Registered Pool Types", specs_a[5]["fallback_label"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_health_info_block_specs_returns_reusable_info_block_order(self) -> None:
        specs_a = build_health_info_block_specs()
        specs_b = build_health_info_block_specs()

        self.assertEqual("meta_rows", specs_a[0]["block_key"])
        self.assertEqual("meta_grid", specs_a[0]["block_type"])
        self.assertEqual("detail_sections", specs_a[1]["block_key"])
        self.assertEqual("grouped_text_sections", specs_a[1]["block_type"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_grouped_summary_info_block_specs_returns_reusable_block_order(self) -> None:
        specs_a = build_grouped_summary_info_block_specs()
        specs_b = build_grouped_summary_info_block_specs()

        self.assertEqual("detail_sections", specs_a[0]["block_key"])
        self.assertEqual("grouped_text_sections", specs_a[0]["block_type"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_content_section_specs_returns_replaceable_layout_map(self) -> None:
        specs_a = build_content_section_specs()
        specs_b = build_content_section_specs()

        self.assertIn("today_priority_summary", specs_a)
        self.assertEqual("today_priority_grouped", specs_a["today_priority_summary"]["render_type"])
        self.assertEqual(2, specs_a["today_priority_summary"]["module_priority"])
        self.assertEqual(
            "当日优先摘要",
            specs_a["today_priority_summary"]["copy_variants"]["business_cn"]["title"],
        )
        self.assertIn("stock_pool_health", specs_a)
        self.assertEqual("accent", specs_a["strongest_sector"]["tone"])
        self.assertEqual("\u6700\u5f3a\u677f\u5757", specs_a["strongest_sector"]["copy_variants"]["business_cn"]["title"])
        self.assertEqual("default", specs_a["strongest_sector"]["copy_variant"])
        self.assertEqual(4, specs_a["strongest_sector"]["module_priority"])
        self.assertEqual(
            "\u5e73\u5747\u6da8\u8dcc",
            specs_a["strongest_sector"]["copy_variants"]["business_cn"]["labels"]["avg_pct_chg"],
        )
        self.assertEqual(
            "\u9886\u6da8\u677f\u5757: ",
            specs_a["strongest_sector"]["copy_variants"]["business_cn"]["display_fields"][0]["prefix"],
        )
        self.assertEqual("neutral", specs_a["leader_summary"]["tone"])
        self.assertEqual("warning", specs_a["latest_alerts"]["tone"])
        self.assertEqual("default", specs_a["latest_alerts"]["copy_variant"])
        self.assertEqual(3, specs_a["latest_alerts"]["module_priority"])
        self.assertEqual(
            "\u6761\u63d0\u9192",
            specs_a["latest_alerts"]["copy_variants"]["business_cn"]["labels"]["badge_unit"],
        )
        self.assertEqual(
            "\u65f6\u95f4",
            specs_a["latest_alerts"]["copy_variants"]["business_cn"]["display_fields"][0]["label"],
        )
        self.assertEqual("neutral", specs_a["saved_batches"]["tone"])
        self.assertEqual("default", specs_a["saved_batches"]["copy_variant"])
        self.assertEqual(7, specs_a["saved_batches"]["module_priority"])
        self.assertEqual(
            "\u4e2a\u5df2\u4fdd\u5b58\u6279\u6b21",
            specs_a["saved_batches"]["copy_variants"]["business_cn"]["labels"]["badge_unit"],
        )
        self.assertEqual(
            "\u6279\u6b21\u65f6\u95f4",
            specs_a["saved_batches"]["copy_variants"]["business_cn"]["display_fields"][0]["label"],
        )
        self.assertEqual("accent", specs_a["next_session_action"]["tone"])
        self.assertEqual("spotlight_summary", specs_a["strongest_sector"]["render_type"])
        self.assertEqual("leader_grouped", specs_a["leader_summary"]["render_type"])
        self.assertEqual("next_session_action_grouped", specs_a["next_session_action"]["render_type"])
        self.assertIn("leader_summary", specs_a)
        self.assertIn("next_session_action", specs_a)
        self.assertIn("latest_alerts", specs_a)
        self.assertEqual("alerts_grouped", specs_a["latest_alerts"]["render_type"])
        self.assertEqual("batch_list_grouped", specs_a["saved_batches"]["render_type"])
        self.assertEqual("health_summary", specs_a["stock_pool_health"]["render_type"])
        self.assertEqual(1, specs_a["stock_pool_health"]["module_priority"])
        self.assertEqual(
            "\u80a1\u7968\u6c60\u5065\u5eb7\u5ea6",
            specs_a["stock_pool_health"]["copy_variants"]["business_cn"]["title"],
        )
        self.assertEqual("default", specs_a["stock_pool_health"]["copy_variant"])
        self.assertNotEqual(
            specs_a["stock_pool_health"]["labels"]["risk_level"],
            specs_a["stock_pool_health"]["copy_variants"]["business_cn"]["labels"]["risk_level"],
        )
        self.assertIn("status_variants", specs_a["stock_pool_health"])
        self.assertIn("summary_metrics", specs_a["stock_pool_health"])
        self.assertIn("health_groups", specs_a["stock_pool_health"])
        self.assertIn("health_meta", specs_a["stock_pool_health"])
        self.assertIn("health_info_blocks", specs_a["stock_pool_health"])
        self.assertEqual(
            "Change Tags",
            specs_a["stock_pool_health"]["labels"]["comparison_tags"],
        )
        self.assertEqual(
            "Change Groups",
            specs_a["stock_pool_health"]["labels"]["comparison_tag_groups"],
        )
        self.assertEqual("record_count", specs_a["stock_pool_health"]["summary_metrics"][0]["value_key"])
        self.assertIn("valid", specs_a["stock_pool_health"]["status_variants"])
        self.assertIn("invalid", specs_a["stock_pool_health"]["status_variants"])
        self.assertEqual("leader_grouped", specs_a["leader_summary"]["render_type"])
        self.assertEqual("\u9f99\u5934\u6458\u8981", specs_a["leader_summary"]["copy_variants"]["business_cn"]["title"])
        self.assertEqual("default", specs_a["leader_summary"]["copy_variant"])
        self.assertEqual(5, specs_a["leader_summary"]["module_priority"])
        self.assertNotEqual(
            specs_a["leader_summary"]["labels"]["badge_unit"],
            specs_a["leader_summary"]["copy_variants"]["business_cn"]["labels"]["badge_unit"],
        )
        self.assertEqual(
            "Priority Core Watchlist (Score-ranked)",
            specs_a["next_session_action"]["labels"]["core_section_title"],
        )
        self.assertEqual(
            "Weight Summary",
            specs_a["next_session_action"]["labels"]["rule_section_title"],
        )
        self.assertIn(
            "{core}",
            specs_a["next_session_action"]["labels"]["badge_template"],
        )
        self.assertEqual(
            "names",
            specs_a["next_session_action"]["labels"]["names_row_label"],
        )
        self.assertEqual(
            "focus",
            specs_a["next_session_action"]["labels"]["focus_row_label"],
        )
        self.assertEqual(
            "Stay with {target} leaders first.",
            specs_a["next_session_action"]["labels"]["focus_templates"]["stay_with_first"],
        )
        self.assertEqual("default", specs_a["next_session_action"]["copy_variant"])
        self.assertEqual(2, specs_a["next_session_action"]["module_priority"])
        self.assertEqual(
            "\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u6458\u8981",
            specs_a["next_session_action"]["copy_variants"]["business_cn"]["title"],
        )
        self.assertNotEqual(
            specs_a["next_session_action"]["labels"]["rule_section_title"],
            specs_a["next_session_action"]["copy_variants"]["business_cn"]["labels"]["rule_section_title"],
        )
        self.assertNotEqual(
            specs_a["next_session_action"]["labels"]["focus_row_label"],
            specs_a["next_session_action"]["copy_variants"]["business_cn"]["labels"]["focus_row_label"],
        )
        self.assertEqual(["timestamp", "alert_type", "message"], specs_a["latest_alerts"]["columns"])
        self.assertEqual("signed_percent_1", specs_a["strongest_sector"]["summary_metrics"][0]["format_key"])
        self.assertEqual("count", specs_a["strongest_sector"]["summary_metrics"][1]["format_key"])
        self.assertIn("info_block_specs", specs_a["strongest_sector"])
        self.assertIn("info_block_specs", specs_a["leader_summary"])
        self.assertIn("info_block_specs", specs_a["latest_alerts"])
        self.assertIn("info_block_specs", specs_a["saved_batches"])
        self.assertEqual(" | ", specs_a["strongest_sector"]["detail_layout"]["separator"])
        self.assertEqual("sector", specs_a["strongest_sector"]["display_fields"][0]["key"])
        self.assertEqual("avg_pct_chg", specs_a["strongest_sector"]["display_fields"][1]["key"])
        self.assertEqual(
            "signed_percent_1",
            specs_a["strongest_sector"]["display_fields"][1]["format_key"],
        )
        self.assertEqual("count", specs_a["stock_pool_health"]["summary_metrics"][0]["format_key"])
        self.assertEqual(": ", specs_a["leader_summary"]["detail_layout"]["separator"])
        self.assertEqual("leader_type", specs_a["leader_summary"]["display_fields"][0]["key"])
        self.assertEqual(" | ", specs_a["latest_alerts"]["detail_layout"]["separator"])
        self.assertEqual("timestamp", specs_a["latest_alerts"]["display_fields"][0]["format_key"])
        self.assertEqual("timestamp", specs_a["saved_batches"]["display_fields"][0]["format_key"])
        self.assertEqual("core_count", specs_a["next_session_action"]["summary_metrics"][0]["value_key"])
        self.assertIsNot(specs_a, specs_b)
        self.assertIsNot(specs_a["leader_summary"], specs_b["leader_summary"])

    def test_build_page_layout_specs_returns_replaceable_render_order(self) -> None:
        specs_a = build_page_layout_specs()
        specs_b = build_page_layout_specs()
        quick_scan_specs = build_page_layout_specs("quick_scan")
        business_cn_specs = build_page_layout_specs("business_cn")

        self.assertEqual("kpi_cards", specs_a[0]["section_key"])
        self.assertEqual("header_segment", specs_a[0]["segment_key"])
        self.assertEqual("content", specs_a[1]["section_type"])
        self.assertEqual("today_priority_summary", specs_a[1]["section_key"])
        self.assertEqual("priority_segment", specs_a[1]["segment_key"])
        self.assertEqual("decision", specs_a[1]["segment_role_key"])
        self.assertEqual("2", specs_a[1]["module_priority"])
        self.assertEqual("Priority Segment", specs_a[1]["segment_title"])
        self.assertEqual("stock_pool_health", specs_a[2]["section_key"])
        self.assertEqual("validation", specs_a[2]["section_role_key"])
        self.assertEqual("1", specs_a[2]["module_priority"])
        self.assertEqual("next_session_action", specs_a[3]["section_key"])
        self.assertEqual("decision", specs_a[3]["section_role_key"])
        self.assertEqual("2", specs_a[3]["module_priority"])
        self.assertEqual("content", specs_a[3]["section_type"])
        self.assertEqual("strongest_sector", specs_a[4]["section_key"])
        self.assertEqual("analysis_segment", specs_a[4]["segment_key"])
        self.assertEqual("leader_summary", specs_a[5]["section_key"])
        self.assertEqual("latest_alerts", specs_a[6]["section_key"])
        self.assertEqual("sector_strength", specs_a[7]["section_key"])
        self.assertEqual("top_movers", specs_a[8]["section_key"])
        self.assertEqual("priority_cluster", specs_a[1]["group_key"])
        self.assertEqual("decision", specs_a[1]["group_role_key"])
        self.assertEqual("Priority Cluster", specs_a[1]["group_title"])
        self.assertEqual("followup_cluster", specs_a[4]["group_key"])
        self.assertEqual("analysis", specs_a[4]["group_role_key"])
        self.assertEqual("Follow-up Cluster", specs_a[4]["group_title"])
        self.assertEqual("kpi_cards", quick_scan_specs[0]["section_key"])
        self.assertEqual("today_priority_summary", quick_scan_specs[1]["section_key"])
        self.assertEqual("next_session_action", quick_scan_specs[2]["section_key"])
        self.assertEqual("stock_pool_health", quick_scan_specs[3]["section_key"])
        self.assertEqual("validation", quick_scan_specs[3]["section_role_key"])
        self.assertEqual("saved_batches", quick_scan_specs[4]["section_key"])
        self.assertEqual("priority_cluster", quick_scan_specs[1]["group_key"])
        self.assertEqual("action_segment", quick_scan_specs[1]["segment_key"])
        self.assertEqual("archive_cluster", quick_scan_specs[4]["group_key"])
        self.assertEqual("archive_segment", quick_scan_specs[4]["segment_key"])
        self.assertEqual("today_priority_summary", business_cn_specs[1]["section_key"])
        self.assertEqual("stock_pool_health", business_cn_specs[2]["section_key"])
        self.assertEqual("next_session_action", business_cn_specs[3]["section_key"])
        self.assertEqual("latest_alerts", business_cn_specs[4]["section_key"])
        self.assertEqual("\u4f18\u5148\u5206\u7ec4", business_cn_specs[1]["group_title"])
        self.assertEqual("\u4f18\u5148\u6bb5\u843d", business_cn_specs[1]["segment_title"])
        self.assertEqual("\u8ddf\u8fdb\u5206\u7ec4", business_cn_specs[4]["group_title"])
        self.assertIsNot(specs_a, specs_b)
        self.assertIsNot(specs_a[0], specs_b[0])

    def test_build_summary_panel_style_spec_returns_replaceable_card_metadata(self) -> None:
        style_spec_a = build_summary_panel_style_spec()
        style_spec_b = build_summary_panel_style_spec()

        self.assertEqual("summary", style_spec_a["summary_label"])
        self.assertEqual("details", style_spec_a["details_label"])
        self.assertEqual("health", style_spec_a["health_label"])
        self.assertEqual("status", style_spec_a["status_label"])
        self.assertEqual("chart", style_spec_a["chart_label"])
        self.assertEqual("axes", style_spec_a["axes_label"])
        self.assertEqual("X", style_spec_a["x_axis_prefix"])
        self.assertEqual("Y", style_spec_a["y_axis_prefix"])
        self.assertEqual("Metrics first, details below", style_spec_a["supporting_copy"])
        self.assertEqual("Metrics + details", style_spec_a["compact_supporting_copy"])
        self.assertEqual("Status first, health details below", style_spec_a["health_supporting_copy"])
        self.assertEqual(
            "Pool is structurally ready for monitoring.",
            style_spec_a["health_supporting_copy_clean"],
        )
        self.assertEqual(
            "Review drift signals before relying on the pool.",
            style_spec_a["health_supporting_copy_warning"],
        )
        self.assertEqual(
            "Fix blocking stock-pool issues before monitoring.",
            style_spec_a["health_supporting_copy_blocking"],
        )
        self.assertEqual(
            "No action needed before the next monitor cycle.",
            style_spec_a["readiness_supporting_copy_clean"],
        )
        self.assertEqual("Data table and chart follow", style_spec_a["chart_supporting_copy"])
        self.assertEqual("Chart + data table", style_spec_a["compact_chart_supporting_copy"])
        self.assertEqual("No data available yet", style_spec_a["empty_state_supporting_copy"])
        self.assertEqual("neutral", style_spec_a["default_tone"])
        self.assertIsNot(style_spec_a, style_spec_b)

    def test_build_summary_panel_style_spec_returns_business_cn_copy(self) -> None:
        style_spec = build_summary_panel_style_spec("business_cn")

        self.assertEqual("\u6458\u8981", style_spec["summary_label"])
        self.assertEqual("\u660e\u7ec6", style_spec["details_label"])
        self.assertEqual("\u5065\u5eb7", style_spec["health_label"])
        self.assertEqual("\u72b6\u6001", style_spec["status_label"])
        self.assertEqual("\u56fe\u8868", style_spec["chart_label"])
        self.assertEqual("\u5750\u6807", style_spec["axes_label"])
        self.assertEqual("\u6a2a\u8f74", style_spec["x_axis_prefix"])
        self.assertEqual("\u7eb5\u8f74", style_spec["y_axis_prefix"])
        self.assertEqual("\u5148\u770b\u6307\u6807\uff0c\u518d\u770b\u660e\u7ec6", style_spec["supporting_copy"])
        self.assertEqual("\u6307\u6807 + \u660e\u7ec6", style_spec["compact_supporting_copy"])
        self.assertEqual("\u4e0b\u65b9\u5c55\u793a\u6570\u636e\u8868\u4e0e\u56fe\u8868", style_spec["chart_supporting_copy"])
        self.assertEqual("\u56fe\u8868 + \u6570\u636e\u8868", style_spec["compact_chart_supporting_copy"])
        self.assertEqual("\u6682\u65f6\u8fd8\u6ca1\u6709\u53ef\u5c55\u793a\u7684\u6570\u636e", style_spec["empty_state_supporting_copy"])

    def test_build_kpi_panel_style_spec_returns_replaceable_kpi_copy(self) -> None:
        style_spec_a = build_kpi_panel_style_spec()
        style_spec_b = build_kpi_panel_style_spec()

        self.assertEqual("kpi section", style_spec_a["section_label"])
        self.assertEqual("kpi", style_spec_a["metric_label"])
        self.assertEqual("Primary monitor snapshot", style_spec_a["section_supporting_copy"])
        self.assertEqual("Top-line monitor metrics", style_spec_a["compact_section_supporting_copy"])
        self.assertEqual("Primary dashboard counter", style_spec_a["metric_supporting_copy"])
        self.assertEqual("neutral", style_spec_a["default_tone"])
        self.assertIsNot(style_spec_a, style_spec_b)

    def test_build_content_panel_style_spec_returns_replaceable_content_copy(self) -> None:
        style_spec_a = build_content_panel_style_spec()
        style_spec_b = build_content_panel_style_spec()

        self.assertEqual("content section", style_spec_a["section_label"])
        self.assertEqual("content details", style_spec_a["detail_label"])
        self.assertEqual("section", style_spec_a["section_title_label"])
        self.assertEqual("Structured monitor summary", style_spec_a["section_supporting_copy"])
        self.assertEqual("Content summary", style_spec_a["compact_section_supporting_copy"])
        self.assertEqual("Grouped detail rows", style_spec_a["grouped_detail_body"])
        self.assertEqual("Formatted content table", style_spec_a["table_detail_body"])
        self.assertEqual("Review grouped details below", style_spec_a["detail_supporting_copy"])
        self.assertEqual("Grouped details", style_spec_a["compact_detail_supporting_copy"])
        self.assertEqual(
            "Content rows will appear here when available.",
            style_spec_a["empty_state_supporting_copy"],
        )
        self.assertEqual("neutral", style_spec_a["default_tone"])
        self.assertIsNot(style_spec_a, style_spec_b)

    def test_build_content_panel_style_spec_returns_business_cn_copy(self) -> None:
        style_spec = build_content_panel_style_spec("business_cn")

        self.assertEqual("\u5185\u5bb9\u533a", style_spec["section_label"])
        self.assertEqual("\u5185\u5bb9\u660e\u7ec6", style_spec["detail_label"])
        self.assertEqual("\u677f\u5757", style_spec["section_title_label"])
        self.assertEqual("\u7ed3\u6784\u5316\u76d1\u63a7\u6458\u8981", style_spec["section_supporting_copy"])
        self.assertEqual("\u5206\u7ec4\u660e\u7ec6", style_spec["grouped_detail_body"])
        self.assertEqual("\u683c\u5f0f\u5316\u5185\u5bb9\u8868", style_spec["table_detail_body"])
        self.assertEqual("\u5206\u7ec4\u660e\u7ec6", style_spec["compact_detail_supporting_copy"])
        self.assertEqual(
            "\u6709\u6548\u5185\u5bb9\u51fa\u73b0\u540e\u4f1a\u5728\u8fd9\u91cc\u663e\u793a\u3002",
            style_spec["empty_state_supporting_copy"],
        )

    def test_build_metric_group_style_spec_returns_replaceable_metric_group_copy(self) -> None:
        style_spec_a = build_metric_group_style_spec()
        style_spec_b = build_metric_group_style_spec()

        self.assertEqual("Metric Row", style_spec_a["default_label"])
        self.assertEqual("Health metrics", style_spec_a["health_metrics_body"])
        self.assertEqual("Summary metrics", style_spec_a["summary_metrics_body"])
        self.assertEqual("Top-line values", style_spec_a["default_supporting_copy"])
        self.assertEqual("Compact metric strip", style_spec_a["compact_supporting_copy"])
        self.assertEqual("neutral", style_spec_a["default_tone"])
        self.assertIsNot(style_spec_a, style_spec_b)

    def test_build_metric_group_style_spec_returns_business_cn_copy(self) -> None:
        style_spec = build_metric_group_style_spec("business_cn")

        self.assertEqual("\u6307\u6807\u884c", style_spec["default_label"])
        self.assertEqual("\u5065\u5eb7\u6307\u6807", style_spec["health_metrics_body"])
        self.assertEqual("\u6458\u8981\u6307\u6807", style_spec["summary_metrics_body"])
        self.assertEqual("\u9876\u5c42\u5173\u952e\u6570\u503c", style_spec["default_supporting_copy"])
        self.assertEqual("\u7d27\u51d1\u6307\u6807\u6761", style_spec["compact_supporting_copy"])

    def test_build_panel_container_style_spec_returns_replaceable_card_surface(self) -> None:
        style_spec = build_panel_container_style_spec()

        self.assertEqual("#f7f4ea", style_spec["background"])
        self.assertEqual("#1f1f1f", style_spec["text_color"])
        self.assertEqual("18px", style_spec["radius"])
        self.assertEqual("#c87b2a", style_spec["tone_accent_border"])
        self.assertEqual("#b24d3f", style_spec["tone_warning_border"])

    def test_build_theme_spec_returns_replaceable_page_theme(self) -> None:
        theme_a = build_theme_spec()
        theme_b = build_theme_spec()

        self.assertEqual("AI Semiconductor Monitor", theme_a["page_title"])
        self.assertEqual("wide", theme_a["layout"])
        self.assertEqual("Dashboard View", theme_a["view_selector_label"])
        self.assertEqual("Snapshot Batch", theme_a["batch_selector_label"])
        self.assertIn("{database_url}", theme_a["caption_template"])
        self.assertIsNot(theme_a, theme_b)

    def test_build_view_mode_specs_returns_replaceable_view_explanations(self) -> None:
        specs_a = build_view_mode_specs()
        specs_b = build_view_mode_specs()

        self.assertEqual("Research View", specs_a["default"]["title"])
        self.assertEqual("neutral", specs_a["default"]["tone"])
        self.assertEqual("Quick Scan View", specs_a["compact"]["title"])
        self.assertEqual("accent", specs_a["compact"]["tone"])
        self.assertEqual("\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe", specs_a["business_cn"]["title"])
        self.assertIn("\u76d1\u63a7\u6c60\u5065\u5eb7", specs_a["business_cn"]["body"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_task_template_specs_returns_explicit_business_scenarios(self) -> None:
        specs = build_task_template_specs()

        self.assertEqual("Intraday Tracking", specs["default"]["label"])
        self.assertEqual("Open Quick Scan", specs["compact"]["label"])
        self.assertEqual("\u6536\u76d8\u590d\u76d8", specs["business_cn"]["label"])
        self.assertIn("main line continuity", specs["default"]["focus_points"])

    def test_build_time_phase_specs_returns_explicit_market_stage_scenarios(self) -> None:
        specs = build_time_phase_specs()

        self.assertEqual("Intraday Phase", specs["default"]["label"])
        self.assertEqual("Post-open Scan", specs["compact"]["label"])
        self.assertEqual("\u6536\u76d8\u9636\u6bb5", specs["business_cn"]["label"])
        self.assertEqual(["latest_alerts", "next_session_action"], specs["compact"]["pinned_sections"])
        self.assertEqual(
            ["saved_batches", "stock_pool_health"],
            specs["business_cn"]["pinned_sections"],
        )

    def test_build_control_band_specs_returns_replaceable_batch_and_source_copy(self) -> None:
        specs_a = build_control_band_specs()
        specs_b = build_control_band_specs("business_cn")

        self.assertEqual("batch focus", specs_a["batch_label"])
        self.assertIn("{selected_batch}", specs_a["batch_body_template"])
        self.assertEqual("data source", specs_a["source_label"])
        self.assertIn("{database_caption}", specs_a["source_body_template"])
        self.assertEqual("\u6279\u6b21\u7126\u70b9", specs_b["batch_label"])
        self.assertEqual("\u6570\u636e\u6765\u6e90", specs_b["source_label"])

    def test_build_control_band_layout_specs_returns_replaceable_slot_orders(self) -> None:
        specs_a = build_control_band_layout_specs()
        specs_b = build_control_band_layout_specs()

        self.assertEqual(
            ["view_mode", "action_summary", "batch_focus", "data_source"],
            specs_a["default"],
        )
        self.assertEqual(
            ["action_summary", "batch_focus", "view_mode", "data_source"],
            specs_a["quick_scan"],
        )
        self.assertEqual(
            ["view_mode", "action_summary", "data_source", "batch_focus"],
            specs_a["business_cn"],
        )
        self.assertIsNot(specs_a, specs_b)

    def test_build_home_header_layout_specs_returns_replaceable_header_orders(self) -> None:
        specs_a = build_home_header_layout_specs()
        specs_b = build_home_header_layout_specs()

        self.assertEqual(["control_band", "kpi"], specs_a["default"])
        self.assertEqual(["kpi", "control_band"], specs_a["quick_scan"])
        self.assertEqual(["control_band", "kpi"], specs_a["business_cn"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_home_header_style_spec_returns_replaceable_header_copy(self) -> None:
        style_a = build_home_header_style_spec()
        style_b = build_home_header_style_spec("business_cn")

        self.assertEqual("home header", style_a["header_label"])
        self.assertEqual("header details", style_a["detail_label"])
        self.assertEqual("First-screen workspace entry", style_a["header_body"])
        self.assertEqual("Header context + KPI", style_a["compact_supporting_copy"])
        self.assertEqual("\u9996\u5c4f\u5934\u90e8", style_b["header_label"])
        self.assertEqual("\u5934\u90e8\u8bf4\u660e", style_b["detail_label"])
        self.assertEqual("\u9996\u5c4f\u5de5\u4f5c\u53f0\u5165\u53e3", style_b["header_body"])

    def test_build_intro_panel_style_spec_returns_shared_intro_copy(self) -> None:
        style_a = build_intro_panel_style_spec()
        style_b = build_intro_panel_style_spec("business_cn")

        self.assertEqual("details", style_a["detail_label"])
        self.assertEqual("header details", style_a["header_detail_label"])
        self.assertEqual("content details", style_a["content_detail_label"])
        self.assertEqual("home header", style_a["header_intro_label"])
        self.assertEqual("content group", style_a["group_intro_label"])
        self.assertEqual("content section", style_a["section_intro_label"])
        self.assertEqual("\u7ec6\u8282\u8bf4\u660e", style_b["detail_label"])
        self.assertEqual("\u5934\u90e8\u8bf4\u660e", style_b["header_detail_label"])
        self.assertEqual("\u5185\u5bb9\u660e\u7ec6", style_b["content_detail_label"])
        self.assertEqual("chart", style_a["chart_intro_label"])
        self.assertEqual("Data table and chart follow", style_a["chart_supporting_copy"])
        self.assertEqual("\u56fe\u8868", style_b["chart_intro_label"])
        self.assertEqual(
            "\u4e0b\u65b9\u5c55\u793a\u6570\u636e\u8868\u4e0e\u56fe\u8868",
            style_b["chart_supporting_copy"],
        )

    def test_build_home_priority_content_layout_specs_returns_replaceable_body_orders(self) -> None:
        specs_a = build_home_priority_content_layout_specs()
        specs_b = build_home_priority_content_layout_specs()

        self.assertEqual(
            ["today_priority_summary", "stock_pool_health", "next_session_action"],
            specs_a["default"],
        )
        self.assertEqual(
            ["today_priority_summary", "next_session_action", "stock_pool_health"],
            specs_a["quick_scan"],
        )
        self.assertEqual(
            ["today_priority_summary", "stock_pool_health", "next_session_action"],
            specs_a["business_cn"],
        )
        self.assertIsNot(specs_a, specs_b)

    def test_build_home_content_group_layout_specs_returns_replaceable_group_orders(self) -> None:
        specs_a = build_home_content_group_layout_specs()
        specs_b = build_home_content_group_layout_specs()

        self.assertEqual("priority_cluster", specs_a["default"][0]["group_key"])
        self.assertEqual("decision", specs_a["default"][0]["role_key"])
        self.assertEqual(
            ["today_priority_summary", "stock_pool_health", "next_session_action"],
            specs_a["default"][0]["sections"],
        )
        self.assertEqual("archive_cluster", specs_a["quick_scan"][1]["group_key"])
        self.assertEqual("archive", specs_a["quick_scan"][1]["role_key"])
        self.assertEqual(
            ["today_priority_summary", "stock_pool_health", "next_session_action"],
            specs_a["business_cn"][0]["sections"],
        )
        self.assertIsNot(specs_a, specs_b)

    def test_build_page_segment_template_specs_returns_replaceable_segment_templates(self) -> None:
        specs_a = build_page_segment_template_specs()
        specs_b = build_page_segment_template_specs()

        self.assertEqual("header_segment", specs_a["default"][0]["segment_key"])
        self.assertEqual("context", specs_a["default"][0]["role_key"])
        self.assertEqual("priority_segment", specs_a["default"][1]["segment_key"])
        self.assertEqual("decision", specs_a["default"][1]["role_key"])
        self.assertEqual(["priority_cluster"], specs_a["quick_scan"][1]["group_keys"])
        self.assertEqual("\u56fe\u8868\u6bb5\u843d", specs_a["business_cn"][3]["segment_title"])
        self.assertEqual("analysis", specs_a["business_cn"][3]["role_key"])
        self.assertIsNot(specs_a, specs_b)

    def test_build_view_variant_specs_returns_default_and_compact_options(self) -> None:
        specs_a = build_view_variant_specs()
        specs_b = build_view_variant_specs()

        self.assertIn("default", specs_a)
        self.assertIn("compact", specs_a)
        self.assertIn("business_cn", specs_a)
        self.assertEqual("Research View", specs_a["default"]["label"])
        self.assertEqual("Quick Scan View", specs_a["compact"]["label"])
        self.assertEqual("\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe", specs_a["business_cn"]["label"])
        self.assertEqual("default", specs_a["default"]["theme_key"])
        self.assertEqual("compact", specs_a["compact"]["theme_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["theme_key"])
        self.assertEqual("default", specs_a["default"]["page_layout_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["page_layout_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["page_layout_key"])
        self.assertEqual("default", specs_a["default"]["priority_content_layout_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["priority_content_layout_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["priority_content_layout_key"])
        self.assertEqual("default", specs_a["default"]["content_group_layout_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["content_group_layout_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["content_group_layout_key"])
        self.assertEqual("default", specs_a["default"]["page_segment_template_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["page_segment_template_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["page_segment_template_key"])
        self.assertEqual("default", specs_a["default"]["kpi_layout_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["kpi_layout_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["kpi_layout_key"])
        self.assertEqual("default", specs_a["default"]["view_mode_key"])
        self.assertEqual("compact", specs_a["compact"]["view_mode_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["view_mode_key"])
        self.assertEqual("default", specs_a["default"]["task_template_key"])
        self.assertEqual("compact", specs_a["compact"]["task_template_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["task_template_key"])
        self.assertEqual("default", specs_a["default"]["time_phase_key"])
        self.assertEqual("compact", specs_a["compact"]["time_phase_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["time_phase_key"])
        self.assertEqual("default", specs_a["default"]["role_strategy_key"])
        self.assertEqual("compact", specs_a["compact"]["role_strategy_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["role_strategy_key"])
        self.assertEqual("default", specs_a["default"]["control_band_layout_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["control_band_layout_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["control_band_layout_key"])
        self.assertEqual("default", specs_a["default"]["home_header_layout_key"])
        self.assertEqual("quick_scan", specs_a["compact"]["home_header_layout_key"])
        self.assertEqual("business_cn", specs_a["business_cn"]["home_header_layout_key"])
        self.assertEqual("default", specs_a["default"]["home_header_copy_variant"])
        self.assertEqual("default", specs_a["compact"]["home_header_copy_variant"])
        self.assertEqual("business_cn", specs_a["business_cn"]["home_header_copy_variant"])
        self.assertEqual("business_cn", specs_a["business_cn"]["kpi_copy_variant"])
        self.assertEqual("business_cn", specs_a["business_cn"]["surface_copy_variant"])
        self.assertEqual(
            "business_cn",
            specs_a["business_cn"]["content_variant_overrides"]["latest_alerts"],
        )
        self.assertIsNot(specs_a, specs_b)
        self.assertIsNot(specs_a["default"], specs_b["default"])

    def test_resolve_dashboard_view_spec_returns_variant_specific_theme_and_layout(self) -> None:
        default_spec = resolve_dashboard_view_spec("default")
        compact_spec = resolve_dashboard_view_spec("compact")
        business_cn_spec = resolve_dashboard_view_spec("business_cn")

        self.assertEqual("AI Semiconductor Monitor", default_spec["theme"]["app_title"])
        self.assertEqual("AI Semi Monitor Compact", compact_spec["theme"]["app_title"])
        self.assertEqual("A股AI半导体监控台", business_cn_spec["theme"]["app_title"])
        self.assertEqual("business_cn", business_cn_spec["kpi_copy_variant"])
        self.assertEqual("business_cn", business_cn_spec["surface_copy_variant"])
        self.assertEqual("comfortable", default_spec["theme"]["panel_density"])
        self.assertEqual("compact", compact_spec["theme"]["panel_density"])
        self.assertEqual("快照批次", business_cn_spec["theme"]["batch_selector_label"])
        self.assertGreater(len(default_spec["page_layout"]), len(compact_spec["page_layout"]))
        self.assertEqual("default", default_spec["page_layout_key"])
        self.assertEqual("quick_scan", compact_spec["page_layout_key"])
        self.assertEqual("business_cn", business_cn_spec["page_layout_key"])
        self.assertEqual("default", default_spec["priority_content_layout_key"])
        self.assertEqual("quick_scan", compact_spec["priority_content_layout_key"])
        self.assertEqual("business_cn", business_cn_spec["priority_content_layout_key"])
        self.assertEqual("default", default_spec["content_group_layout_key"])
        self.assertEqual("quick_scan", compact_spec["content_group_layout_key"])
        self.assertEqual("business_cn", business_cn_spec["content_group_layout_key"])
        self.assertEqual("default", default_spec["page_segment_template_key"])
        self.assertEqual("quick_scan", compact_spec["page_segment_template_key"])
        self.assertEqual("business_cn", business_cn_spec["page_segment_template_key"])
        self.assertEqual("default", default_spec["view_mode_key"])
        self.assertEqual("compact", compact_spec["view_mode_key"])
        self.assertEqual("business_cn", business_cn_spec["view_mode_key"])
        self.assertEqual("default", default_spec["task_template_key"])
        self.assertEqual("compact", compact_spec["task_template_key"])
        self.assertEqual("business_cn", business_cn_spec["task_template_key"])
        self.assertEqual("default", default_spec["time_phase_key"])
        self.assertEqual("compact", compact_spec["time_phase_key"])
        self.assertEqual("business_cn", business_cn_spec["time_phase_key"])
        self.assertEqual("default", default_spec["role_strategy_key"])
        self.assertEqual("compact", compact_spec["role_strategy_key"])
        self.assertEqual("business_cn", business_cn_spec["role_strategy_key"])
        self.assertEqual("default", default_spec["control_band_layout_key"])
        self.assertEqual("quick_scan", compact_spec["control_band_layout_key"])
        self.assertEqual("business_cn", business_cn_spec["control_band_layout_key"])
        self.assertEqual("default", default_spec["home_header_layout_key"])
        self.assertEqual("quick_scan", compact_spec["home_header_layout_key"])
        self.assertEqual("business_cn", business_cn_spec["home_header_layout_key"])
        self.assertEqual("default", default_spec["home_header_copy_variant"])
        self.assertEqual("default", compact_spec["home_header_copy_variant"])
        self.assertEqual("business_cn", business_cn_spec["home_header_copy_variant"])
        self.assertEqual(
            ["action_summary", "batch_focus", "view_mode", "data_source"],
            compact_spec["control_band_layout"],
        )
        self.assertEqual(
            ["today_priority_summary", "next_session_action", "stock_pool_health"],
            compact_spec["priority_content_layout"],
        )
        self.assertEqual("priority_cluster", compact_spec["content_group_layout"][0]["group_key"])
        self.assertEqual("action_segment", compact_spec["page_segment_template"][1]["segment_key"])
        self.assertEqual(
            ["view_mode", "action_summary", "data_source", "batch_focus"],
            business_cn_spec["control_band_layout"],
        )
        self.assertEqual(
            ["today_priority_summary", "stock_pool_health", "next_session_action"],
            business_cn_spec["priority_content_layout"],
        )
        self.assertEqual("followup_cluster", business_cn_spec["content_group_layout"][1]["group_key"])
        self.assertEqual("\u56fe\u8868\u6bb5\u843d", business_cn_spec["page_segment_template"][3]["segment_title"])
        self.assertEqual(["kpi", "control_band"], compact_spec["home_header_layout"])
        self.assertEqual(["control_band", "kpi"], business_cn_spec["home_header_layout"])
        self.assertEqual("home header", default_spec["home_header_style"]["header_label"])
        self.assertEqual("\u9996\u5c4f\u5934\u90e8", business_cn_spec["home_header_style"]["header_label"])
        self.assertEqual("Priority Cluster", default_spec["page_layout"][1]["group_title"])
        self.assertEqual("Quick Priority Cluster", compact_spec["page_layout"][1]["group_title"])
        self.assertEqual("\u4f18\u5148\u5206\u7ec4", business_cn_spec["page_layout"][1]["group_title"])
        self.assertEqual("Research View", default_spec["view_mode_note"]["title"])
        self.assertEqual("Quick Scan View", compact_spec["view_mode_note"]["title"])
        self.assertEqual("\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe", business_cn_spec["view_mode_note"]["title"])
        self.assertEqual("Open Quick Scan", compact_spec["task_template"]["label"])
        self.assertEqual("Post-open Scan", compact_spec["time_phase"]["label"])
        self.assertEqual("\u6536\u76d8\u590d\u76d8", business_cn_spec["task_template"]["label"])
        self.assertEqual("\u6536\u76d8\u9636\u6bb5", business_cn_spec["time_phase"]["label"])
        self.assertEqual(["decision", "validation"], compact_spec["role_strategy"]["primary_roles"])
        self.assertEqual(["validation", "decision"], business_cn_spec["role_strategy"]["primary_roles"])
        self.assertEqual("today_priority_summary", compact_spec["page_layout"][1]["section_key"])
        self.assertEqual("saved_batches", compact_spec["page_layout"][-1]["section_key"])
        self.assertEqual("stock_pool_health", business_cn_spec["page_layout"][2]["section_key"])
        self.assertEqual("next_session_action", business_cn_spec["page_layout"][3]["section_key"])
        self.assertEqual(
            "business_cn",
            business_cn_spec["content_variant_overrides"]["saved_batches"],
        )

    def test_resolve_dashboard_view_spec_includes_kpi_summary_layout_metadata(self) -> None:
        default_spec = resolve_dashboard_view_spec("default")
        compact_spec = resolve_dashboard_view_spec("compact")
        business_cn_spec = resolve_dashboard_view_spec("business_cn")

        self.assertEqual("default", default_spec["kpi_layout_key"])
        self.assertEqual("quick_scan", compact_spec["kpi_layout_key"])
        self.assertEqual("business_cn", business_cn_spec["kpi_layout_key"])
        self.assertEqual(
            "mainline_summary",
            compact_spec["kpi_summary_layout"]["card_order"][0],
        )
        self.assertEqual(
            "business_cn",
            business_cn_spec["kpi_summary_layout"]["card_variant_overrides"]["risk_summary"],
        )

    def test_build_view_role_strategy_specs_returns_explicit_role_emphasis(self) -> None:
        specs = build_view_role_strategy_specs()

        self.assertEqual(["analysis", "validation"], specs["default"]["primary_roles"])
        self.assertEqual(["decision", "validation"], specs["compact"]["primary_roles"])
        self.assertEqual(["analysis"], specs["compact"]["deferred_roles"])
        self.assertEqual(["archive"], specs["compact"]["hidden_roles"])
        self.assertEqual(
            ["next_session_action", "stock_pool_health", "latest_alerts"],
            specs["compact"]["pinned_sections"],
        )
        self.assertEqual(["saved_batches"], specs["compact"]["hidden_sections"])
        self.assertEqual("\u89d2\u8272\u7b56\u7565", specs["business_cn"]["summary_label"])
        self.assertEqual(["archive"], specs["business_cn"]["deferred_roles"])
        self.assertEqual(["saved_batches"], specs["business_cn"]["deferred_sections"])


if __name__ == "__main__":
    unittest.main()
