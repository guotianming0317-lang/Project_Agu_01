"""Tests for dashboard Streamlit helpers."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.dashboard.presentation import (
    build_chart_specs,
    build_content_panel_style_spec,
    build_content_section_specs,
    build_dynamic_action_focus_fact_specs,
    build_dynamic_action_focus_specs,
    build_kpi_panel_style_spec,
    build_kpi_value_format_spec,
    build_metric_group_style_spec,
    build_panel_container_style_spec,
    build_priority_action_focus_copy_specs,
    build_priority_action_module_copy_specs,
    build_priority_action_phase_copy_specs,
    build_priority_action_phase_override_specs,
    build_priority_action_phase_profile_override_specs,
    build_priority_action_profile_specs,
    build_priority_action_topline_copy_specs,
    build_priority_action_topline_specs,
    build_summary_panel_style_spec,
    build_view_variant_specs,
)
from app.dashboard import streamlit_app as dashboard_streamlit_app
from app.dashboard.streamlit_app import (
    _apply_kpi_value_length_limit,
    _merge_layout_strategy,
    _apply_role_strategy_to_page_layout,
    _build_priority_focus_labels,
    _build_priority_focus_tones,
    _build_priority_action_locations,
    _build_priority_action_layout_strategy,
    _parse_module_priority,
    _build_alerts_grouped_view_model,
    _build_business_role_support_text,
    _build_task_template_summary_text,
    _build_time_phase_summary_text,
    _build_today_priority_grouped_view_model,
    _build_role_strategy_summary_text,
    _build_batch_list_grouped_view_model,
    _build_info_blocks,
    _build_chart_panel_markdown,
    _build_chart_axes_markdown,
    _build_chart_section_header_markdown,
    _build_content_detail_markdown,
    _build_content_section_header_markdown,
    _build_grouped_summary_detail_payload,
    _build_grouped_summary_info_blocks_from_sections,
    _build_grouped_summary_rows_from_items,
    _build_grouped_summary_sections_from_items,
    _build_grouped_count_badge,
    _build_health_detail_sections,
    _build_health_info_blocks,
    _build_count_summary_rows,
    _build_top_count_row,
    _build_health_row_sources,
    _build_health_section_titles,
    _build_summary_metrics,
    _build_health_status_copy,
    _build_legacy_grouped_summary_info_blocks,
    _resolve_legacy_grouped_summary_rows,
    _resolve_compatibility_rows_from_info_blocks,
    _resolve_grouped_summary_render_blocks,
    _build_grouped_summary_card_markdown,
    _build_grouped_section_header_markdown,
    _build_health_comparison_rows,
    _build_health_meta_rows,
    _build_grouped_text_section_view_models,
    _build_action_summary_content,
    _build_action_summary_markdown,
    _build_dashboard_panel_css,
    _build_dashboard_priority_action_note,
    _build_priority_action_profile,
    _build_time_phase_override_options,
    _resolve_effective_time_phase,
    _resolve_time_phase_override_key,
    _resolve_time_phase_override_label,
    _resolve_priority_action_phase_key,
    _resolve_priority_action_scenario,
    _resolve_priority_action_sections,
    _build_control_band_markdown,
    _build_dashboard_variant_recommendation_note,
    _build_info_panel_markdown,
    _build_intro_panel_markdown,
    _build_empty_state_markdown,
    _build_health_readiness_markdown,
    _build_health_summary_card_markdown,
    _build_health_status_markdown,
    _build_kpi_metric_caption,
    _build_kpi_metric_panel_markdown,
    _build_kpi_section_header_markdown,
    _build_view_mode_note_markdown,
    _build_metric_group_markdown,
    _resolve_spec_copy_variant,
    _resolve_next_session_action_labels,
    _normalize_priority_action_sections_for_layout,
    _build_next_session_action_section_rows,
    _build_next_session_action_grouped_view_model,
    _format_kpi_metric_value,
    _format_rows_for_display,
    _build_panel_block_markdown,
    _build_panel_body_text,
    _build_section_title_markdown,
    _build_table_rows_for_display,
    _build_tone_panel_title,
    _normalize_display_field_specs,
    _render_info_blocks,
    _render_grouped_text_sections,
    _resolve_tone_icon,
    _resolve_kpi_card_value,
    _resolve_kpi_card_specs,
    _build_leader_grouped_view_model,
    _build_health_summary_view_model,
    _build_spotlight_summary_view_model,
    _render_chart_block,
    _render_content_group_intro,
    _render_page_segment_intro,
    _render_home_header,
    _render_page_layout,
    _render_content_block_with_density,
    _recommend_dashboard_variant_key,
    _resolve_dashboard_variant_key,
)


class _FakeStreamlit:
    """Tiny Streamlit stand-in for render-path tests."""

    def __init__(self) -> None:
        self.dataframe_rows: list[dict[str, object]] | None = None
        self.dataframe_use_container_width: bool | None = None
        self.bar_chart_rows: list[dict[str, object]] | None = None
        self.bar_chart_x: str | None = None
        self.bar_chart_y: str | None = None
        self.markdown_calls: list[str] = []
        self.write_calls: list[str] = []
        self.subheader_calls: list[str] = []
        self.metric_calls: list[tuple[str, str]] = []
        self.caption_calls: list[str] = []

    def markdown(self, *args: object, **_kwargs: object) -> None:
        """Capture markdown calls for render-path verification."""
        if args:
            self.markdown_calls.append(str(args[0]))

    def dataframe(self, rows: list[dict[str, object]], *, use_container_width: bool) -> None:
        """Capture dataframe payloads for assertions."""
        self.dataframe_rows = rows
        self.dataframe_use_container_width = use_container_width

    def write(self, *_args: object, **_kwargs: object) -> None:
        """Capture non-table writes in this lightweight fake."""
        if _args:
            self.write_calls.append(str(_args[0]))

    def subheader(self, *_args: object, **_kwargs: object) -> None:
        """Capture subheaders for legacy render-path completeness."""
        if _args:
            self.subheader_calls.append(str(_args[0]))

    def metric(self, *_args: object, **_kwargs: object) -> None:
        """Accept metric calls from grouped-summary render paths."""
        if len(_args) >= 2:
            self.metric_calls.append((str(_args[0]), str(_args[1])))

    def caption(self, *_args: object, **_kwargs: object) -> None:
        """Accept caption calls from KPI render paths."""
        if _args:
            self.caption_calls.append(str(_args[0]))

    def columns(self, count: int) -> list["_FakeStreamlit"]:
        """Return lightweight column stand-ins that share write capture."""
        return [self for _ in range(count)]

    def json(self, *_args: object, **_kwargs: object) -> None:
        """Ignore JSON writes in this lightweight fake."""

    def bar_chart(
        self,
        rows: list[dict[str, object]],
        *,
        x: str,
        y: str,
    ) -> None:
        """Capture chart payloads for assertions."""
        self.bar_chart_rows = rows
        self.bar_chart_x = x
        self.bar_chart_y = y


class DashboardStreamlitTests(unittest.TestCase):
    """Verify view-variant selection logic stays stable."""

    def test_import_streamlit_returns_module_when_available(self) -> None:
        fake_module = object()

        with patch(
            "app.dashboard.streamlit_app.import_module",
            return_value=fake_module,
        ):
            loaded = dashboard_streamlit_app._import_streamlit()

        self.assertIs(fake_module, loaded)

    def test_import_streamlit_raises_helpful_runtime_error_when_missing(self) -> None:
        with patch(
            "app.dashboard.streamlit_app.import_module",
            side_effect=ModuleNotFoundError("No module named 'streamlit'"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Streamlit is not installed. Run `pip install -r requirements.txt` first.",
            ):
                dashboard_streamlit_app._import_streamlit()

    def test_resolve_dashboard_variant_key_keeps_known_variant(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _resolve_dashboard_variant_key(variant_specs, "compact")

        self.assertEqual("compact", selected)

    def test_resolve_dashboard_variant_key_falls_back_to_default(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _resolve_dashboard_variant_key(variant_specs, "missing")

        self.assertEqual("default", selected)

    def test_resolve_dashboard_variant_key_uses_recommended_variant_when_request_missing(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _resolve_dashboard_variant_key(
            variant_specs,
            "missing",
            recommended_variant="business_cn",
        )

        self.assertEqual("business_cn", selected)

    def test_resolve_dashboard_variant_key_keeps_business_cn_variant(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _resolve_dashboard_variant_key(variant_specs, "business_cn")

        self.assertEqual("business_cn", selected)

    def test_recommend_dashboard_variant_key_prefers_compact_for_opening_batch(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _recommend_dashboard_variant_key(
            variant_specs,
            {
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("compact", selected)

    def test_recommend_dashboard_variant_key_prefers_compact_when_alerts_exist(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _recommend_dashboard_variant_key(
            variant_specs,
            {
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 2,
                "negative_alert_count": 1,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("compact", selected)

    def test_build_today_priority_grouped_view_model_returns_localized_sections(self) -> None:
        spec = build_content_section_specs()["today_priority_summary"]

        view_model = _build_today_priority_grouped_view_model(
            {
                "summary_date": "2026-07-18",
                "shown_items": 2,
                "total_items": 3,
                "core_summary": "先看风险扩散，再看主线强化。",
                "one_line_advice": "先防守，再确认跟随。",
                "daily_conclusion": "风险与强化并存。",
                "operation_tips": "先读风险名单。",
                "read_order": ["1. 先看风险优先名单", "2. 再看强化跟踪名单"],
                "watch_rows": ["- 风险优先名单：中微公司、北方华创"],
                "action_rows": ["- 风险优先动作", "- 先确认设备链是否同步承压"],
                "source_batch": "data/news/news_batch_20260718.json",
                "impact_summary": "风险扩散 1 | 主线强化 1",
                "filter_mode": "high-priority-only",
                "watch_group_count": 1,
            },
            {
                **spec,
                "copy_variant": "business_cn",
            },
        )

        self.assertIn("2026-07-18", view_model["badge_text"])
        self.assertEqual(2, view_model["summary_metrics"][0]["value"])
        self.assertEqual(1, view_model["summary_metrics"][1]["value"])
        info_blocks = view_model["info_blocks"]
        self.assertTrue(info_blocks)
        detail_sections = info_blocks[0]["content"]
        self.assertEqual("核心摘要:", detail_sections[0]["title"])
        self.assertIn("先看风险扩散", detail_sections[0]["rows"][0])

    def test_recommend_dashboard_variant_key_prefers_business_cn_for_late_review_state(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _recommend_dashboard_variant_key(
            variant_specs,
            {
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("business_cn", selected)

    def test_recommend_dashboard_variant_key_falls_back_to_default_for_quiet_mid_session(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _recommend_dashboard_variant_key(
            variant_specs,
            {
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("default", selected)

    def test_recommend_dashboard_variant_key_prefers_business_cn_when_stock_pool_is_blocking(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _recommend_dashboard_variant_key(
            variant_specs,
            {
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 1,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "invalid",
                    "risk_level": "blocking",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("business_cn", selected)

    def test_recommend_dashboard_variant_key_prefers_business_cn_when_stock_pool_drift_is_active(self) -> None:
        variant_specs = build_view_variant_specs()

        selected = _recommend_dashboard_variant_key(
            variant_specs,
            {
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Materials Exposure Up", "Priority-1 Focus Down"],
                },
            },
        )

        self.assertEqual("business_cn", selected)

    def test_build_view_mode_note_markdown_uses_replaceable_mode_copy(self) -> None:
        markdown = _build_view_mode_note_markdown(
            {
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Quick Scan View",
                "body": "Fast first-screen layout for KPI and latest alerts.",
                "supporting_copy": "Use this mode when time is limited.",
            },
            panel_density="comfortable",
            task_template={
                "label": "Open Quick Scan",
                "summary_label": "task template",
                "body": "Best for deciding what deserves immediate attention near the open.",
                "focus_points": ["next-session action", "pool health check", "latest alerts first"],
            },
            time_phase={
                "label": "Post-open Scan",
                "summary_label": "time phase",
                "body": "Designed for the opening window when rapid prioritization matters most.",
                "focus_points": ["opening strength", "early alerts", "quick validation"],
                "pinned_sections": ["latest_alerts", "next_session_action"],
                "deferred_sections": ["saved_batches"],
            },
            role_strategy={
                "primary_roles": ["decision", "validation"],
                "secondary_roles": ["analysis"],
                "deferred_roles": ["analysis"],
                "hidden_roles": ["archive"],
                "pinned_sections": ["next_session_action", "stock_pool_health", "latest_alerts"],
                "deferred_sections": ["strongest_sector", "leader_summary"],
                "hidden_sections": ["saved_batches"],
                "summary_label": "role strategy",
                "body": "Prioritizes fast decision support and stock-pool trust checks before deeper analysis.",
            },
            recommendation_note="Recommendation: Quick Scan View now. Reason: this is still near the open, so fast prioritization is more useful",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            home_header_style={"detail_label": "header details"},
        )

        self.assertIn("ACCENT VIEW MODE", markdown)
        self.assertIn("Quick Scan View | Fast first-screen layout for KPI and latest alerts.", markdown)
        self.assertIn("= NEUTRAL HEADER DETAILS", markdown)
        self.assertIn("Use this mode when time is limited.", markdown)
        self.assertIn("task template: Open Quick Scan", markdown)
        self.assertIn("Focus: next-session action / pool health check / latest alerts first", markdown)
        self.assertIn("time phase: Phase source: Automatic | Post-open Scan", markdown)
        self.assertIn("opening strength / early alerts / quick validation", markdown)
        self.assertIn("Pinned sections: latest_alerts / next_session_action", markdown)
        self.assertIn("role strategy: Prioritizes fast decision support", markdown)
        self.assertIn("Primary: Decision / Validation", markdown)
        self.assertIn("Hidden: Archive", markdown)
        self.assertIn("Pinned sections: next_session_action / stock_pool_health / latest_alerts", markdown)
        self.assertIn("Hidden sections: saved_batches", markdown)
        self.assertIn("Recommendation: Quick Scan View now.", markdown)
        self.assertIn("First step: scan the latest alerts", markdown)

    def test_build_intro_panel_markdown_uses_shared_detail_label(self) -> None:
        markdown = _build_intro_panel_markdown(
            tone="accent",
            label="content group",
            body="Priority Cluster",
            panel_density="comfortable",
            detail_label="content details",
            supporting_body="Related homepage sections stay grouped here",
        )

        self.assertIn("ACCENT CONTENT GROUP", markdown)
        self.assertIn("Priority Cluster", markdown)
        self.assertIn("= NEUTRAL CONTENT DETAILS", markdown)

    def test_build_priority_focus_labels_returns_primary_and_follow_up_markers(self) -> None:
        labels = _build_priority_focus_labels(
            ["latest_alerts", "next_session_action", "stock_pool_health"],
            copy_variant="default",
        )

        self.assertEqual("1. Step 1 focus", labels["latest_alerts"])
        self.assertEqual("2. Step 2 follow-up", labels["next_session_action"])
        self.assertNotIn("stock_pool_health", labels)

    def test_build_priority_focus_tones_returns_visual_priority_overrides(self) -> None:
        tones = _build_priority_focus_tones(
            ["today_priority_summary", "next_session_action", "stock_pool_health"]
        )

        self.assertEqual("accent", tones["today_priority_summary"])
        self.assertEqual("warning", tones["next_session_action"])
        self.assertNotIn("stock_pool_health", tones)

    def test_build_priority_action_locations_uses_segment_and_group_titles(self) -> None:
        locations = _build_priority_action_locations(
            [
                {
                    "section_key": "latest_alerts",
                    "segment_title": "Action Segment",
                    "group_title": "Quick Priority Cluster",
                },
                {
                    "section_key": "next_session_action",
                    "segment_title": "Action Segment",
                    "group_title": "Quick Priority Cluster",
                },
            ],
            priority_action_sections=["latest_alerts", "next_session_action"],
            copy_variant="default",
        )

        self.assertEqual(
            "Action Segment > Quick Priority Cluster",
            locations["latest_alerts"],
        )

    def test_build_business_role_support_text_uses_default_role_copy(self) -> None:
        support_text = _build_business_role_support_text(
            "decision",
            copy_variant="default",
            style_spec={"role_prefix": "Role"},
        )

        self.assertIn("Role: Decision", support_text)
        self.assertIn("next action", support_text)

    def test_build_task_template_summary_text_uses_business_cn_copy(self) -> None:
        summary = _build_task_template_summary_text(
            {
                "label": "\u6536\u76d8\u590d\u76d8",
                "summary_label": "\u4efb\u52a1\u6a21\u677f",
                "body": "\u66f4\u9002\u5408\u4e2d\u6587\u4e1a\u52a1\u590d\u76d8\u3002",
                "focus_points": ["\u6821\u9a8c\u72b6\u6001", "\u52a8\u4f5c\u7ed3\u8bba"],
            },
            copy_variant="business_cn",
        )

        self.assertIn("\u4efb\u52a1\u6a21\u677f", summary)
        self.assertIn("\u6536\u76d8\u590d\u76d8", summary)
        self.assertIn("\u5173\u6ce8\u70b9", summary)

    def test_build_time_phase_summary_text_uses_business_cn_copy(self) -> None:
        summary = _build_time_phase_summary_text(
            {
                "label": "\u6536\u76d8\u9636\u6bb5",
                "summary_label": "\u65f6\u6bb5\u6a21\u677f",
                "body": "\u9002\u5408\u6536\u76d8\u540e\u590d\u76d8\u3002",
                "focus_points": ["\u5f53\u65e5\u7ed3\u8bba", "\u5feb\u7167\u5bf9\u7167"],
                "pinned_sections": ["saved_batches"],
            },
            copy_variant="business_cn",
        )

        self.assertIn("\u65f6\u6bb5\u6a21\u677f", summary)
        self.assertIn("\u6536\u76d8\u9636\u6bb5", summary)
        self.assertIn("\u5173\u6ce8\u70b9", summary)
        self.assertIn("\u7f6e\u9876\u6a21\u5757", summary)
        self.assertIn("\u65f6\u6bb5\u6765\u6e90\uff1a\u81ea\u52a8\u5224\u65ad", summary)

    def test_build_time_phase_summary_text_shows_manual_override_source(self) -> None:
        summary = _build_time_phase_summary_text(
            {
                "label": "Closing Review Phase",
                "summary_label": "time phase",
                "body": "Designed for the late-session replay.",
            },
            copy_variant="default",
            phase_override_key="business_cn",
        )

        self.assertIn("time phase", summary)
        self.assertIn("Phase source: Manual override | Active mode: Closing Review Phase", summary)

    def test_build_view_mode_note_markdown_includes_time_phase_override_state(self) -> None:
        markdown = _build_view_mode_note_markdown(
            {
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Quick Scan View",
                "body": "Fast first-screen layout for KPI and latest alerts.",
            },
            panel_density="comfortable",
            time_phase={
                "label": "Post-open Scan",
                "summary_label": "time phase",
                "body": "Designed for the opening window when rapid prioritization matters most.",
            },
            time_phase_override_key="compact",
            home_header_style={"detail_label": "header details"},
        )

        self.assertIn("Phase source: Manual override | Active mode: Post-open Scan", markdown)

    def test_merge_layout_strategy_combines_role_and_time_phase_behavior(self) -> None:
        merged = _merge_layout_strategy(
            {
                "primary_roles": ["decision"],
                "pinned_sections": ["next_session_action"],
                "hidden_sections": ["saved_batches"],
            },
            {
                "primary_roles": ["validation"],
                "pinned_sections": ["latest_alerts"],
                "deferred_sections": ["sector_strength"],
            },
        )

        self.assertEqual(["decision", "validation"], merged["primary_roles"])
        self.assertEqual(["next_session_action", "latest_alerts"], merged["pinned_sections"])
        self.assertEqual(["sector_strength"], merged["deferred_sections"])

    def test_build_role_strategy_summary_text_uses_business_cn_labels(self) -> None:
        summary = _build_role_strategy_summary_text(
            {
                "primary_roles": ["validation", "decision"],
                "secondary_roles": ["analysis"],
                "deferred_roles": ["archive"],
                "deferred_sections": ["saved_batches"],
                "summary_label": "\u89d2\u8272\u7b56\u7565",
                "body": "\u4f18\u5148\u7a81\u51fa\u6821\u9a8c\u4e0e\u51b3\u7b56\u3002",
            },
            copy_variant="business_cn",
        )

        self.assertIn("\u89d2\u8272\u7b56\u7565", summary)
        self.assertIn("\u4e3b\u8981\uff1a\u6821\u9a8c / \u51b3\u7b56", summary)
        self.assertIn("\u540e\u7f6e\uff1a\u5f52\u6863", summary)
        self.assertIn("\u540e\u7f6e\u6a21\u5757\uff1asaved_batches", summary)

    def test_apply_role_strategy_to_page_layout_can_hide_and_defer_roles(self) -> None:
        resolved = _apply_role_strategy_to_page_layout(
            [
                {
                    "section_type": "content",
                    "section_key": "saved_batches",
                    "section_role_key": "archive",
                },
                {
                    "section_type": "content",
                    "section_key": "leader_summary",
                    "section_role_key": "analysis",
                },
                {
                    "section_type": "content",
                    "section_key": "next_session_action",
                    "section_role_key": "decision",
                },
                {
                    "section_type": "content",
                    "section_key": "stock_pool_health",
                    "section_role_key": "validation",
                },
            ],
            role_strategy={
                "pinned_sections": ["next_session_action"],
                "deferred_sections": ["leader_summary"],
                "deferred_roles": ["analysis"],
                "hidden_roles": ["archive"],
            },
        )

        self.assertEqual(
            ["next_session_action", "stock_pool_health", "leader_summary"],
            [section["section_key"] for section in resolved],
        )

    def test_apply_role_strategy_to_page_layout_compact_mode_hides_archive_sections(self) -> None:
        filtered = _apply_role_strategy_to_page_layout(
            [
                {
                    "section_type": "content",
                    "section_key": "next_session_action",
                    "section_role_key": "decision",
                },
                {
                    "section_type": "content",
                    "section_key": "saved_batches",
                    "section_role_key": "archive",
                },
            ],
            role_strategy={
                "pinned_sections": ["next_session_action"],
                "deferred_roles": ["analysis"],
                "hidden_roles": ["archive"],
                "hidden_sections": ["saved_batches"],
            },
        )

        self.assertEqual(["next_session_action"], [section["section_key"] for section in filtered])

    def test_apply_role_strategy_to_page_layout_can_pin_sections_ahead_of_other_roles(self) -> None:
        resolved = _apply_role_strategy_to_page_layout(
            [
                {
                    "section_type": "content",
                    "section_key": "leader_summary",
                    "section_role_key": "analysis",
                },
                {
                    "section_type": "content",
                    "section_key": "stock_pool_health",
                    "section_role_key": "validation",
                },
                {
                    "section_type": "content",
                    "section_key": "next_session_action",
                    "section_role_key": "decision",
                },
            ],
            role_strategy={
                "pinned_sections": ["next_session_action"],
                "deferred_sections": ["leader_summary"],
            },
        )

        self.assertEqual(
            ["next_session_action", "stock_pool_health", "leader_summary"],
            [section["section_key"] for section in resolved],
        )

    def test_apply_role_strategy_to_page_layout_sorts_same_bucket_by_module_priority(self) -> None:
        resolved = _apply_role_strategy_to_page_layout(
            [
                {
                    "section_type": "content",
                    "section_key": "leader_summary",
                    "section_role_key": "analysis",
                    "module_priority": "5",
                },
                {
                    "section_type": "content",
                    "section_key": "latest_alerts",
                    "section_role_key": "analysis",
                    "module_priority": "3",
                },
                {
                    "section_type": "content",
                    "section_key": "strongest_sector",
                    "section_role_key": "analysis",
                    "module_priority": "4",
                },
            ],
            role_strategy={},
        )

        self.assertEqual(
            ["latest_alerts", "strongest_sector", "leader_summary"],
            [section["section_key"] for section in resolved],
        )

    def test_parse_module_priority_falls_back_when_value_is_invalid(self) -> None:
        self.assertEqual(2, _parse_module_priority("2"))
        self.assertEqual(99, _parse_module_priority("bad-priority"))

    def test_apply_role_strategy_to_page_layout_uses_merged_time_phase_behavior(self) -> None:
        merged_strategy = _merge_layout_strategy(
            {
                "pinned_sections": ["stock_pool_health"],
                "deferred_sections": ["leader_summary"],
            },
            {
                "pinned_sections": ["latest_alerts"],
            },
        )
        resolved = _apply_role_strategy_to_page_layout(
            [
                {
                    "section_type": "content",
                    "section_key": "leader_summary",
                    "section_role_key": "analysis",
                    "module_priority": "5",
                },
                {
                    "section_type": "content",
                    "section_key": "stock_pool_health",
                    "section_role_key": "validation",
                    "module_priority": "1",
                },
                {
                    "section_type": "content",
                    "section_key": "latest_alerts",
                    "section_role_key": "analysis",
                    "module_priority": "3",
                },
            ],
            role_strategy=merged_strategy,
        )

        self.assertEqual(
            ["stock_pool_health", "latest_alerts", "leader_summary"],
            [section["section_key"] for section in resolved],
        )

    def test_build_control_band_markdown_combines_mode_batch_and_source_context(self) -> None:
        markdown = _build_control_band_markdown(
            {
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Quick Scan View",
                "body": "Fast first-screen layout for KPI and latest alerts.",
                "supporting_copy": "Use this mode when time is limited.",
            },
            payload={
                "quote_source_display": "local-json-snapshot (local real quote snapshot)",
            },
            selected_batch="2026-06-20 14:45:00",
            database_caption="Database: sqlite:///monitor.db",
            copy_variant="default",
            control_band_layout=["view_mode", "action_summary", "batch_focus", "data_source"],
            panel_density="comfortable",
            recommendation_note="Recommendation: Quick Scan View now. Reason: active alerts exist, so a fast scan mode should stay forward",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_sections=["latest_alerts", "next_session_action", "stock_pool_health"],
            home_header_style={"detail_label": "header details"},
        )

        self.assertIn("Quick Scan View | Fast first-screen layout for KPI and latest alerts.", markdown)
        self.assertIn("INFO BATCH FOCUS", markdown)
        self.assertIn("Current batch | 2026-06-20 14:45:00", markdown)
        self.assertIn("NEUTRAL DATA SOURCE", markdown)
        self.assertIn(
            "Database | Database: sqlite:///monitor.db | Quote source: local-json-snapshot (local real quote snapshot)",
            markdown,
        )
        self.assertIn("Recommendation: Quick Scan View now.", markdown)
        self.assertIn("First step: scan the latest alerts", markdown)
        self.assertIn("ACCENT ACTION SUMMARY", markdown)
        self.assertIn("Current Suggested Flow", markdown)

    def test_build_control_band_markdown_uses_business_cn_copy(self) -> None:
        markdown = _build_control_band_markdown(
            {
                "tone": "accent",
                "summary_label": "\u89c6\u56fe\u6a21\u5f0f",
                "title": "\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe",
                "body": "\u4f18\u5148\u663e\u793a\u76d1\u63a7\u6c60\u5065\u5eb7\u3001\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u548c\u6700\u65b0\u63d0\u9192\u3002",
                "supporting_copy": "\u9002\u5408\u5148\u770b\u5c31\u7eea\u5ea6\u4e0e\u52a8\u4f5c\u7ed3\u8bba\u3002",
            },
            payload={
                "quote_source_display": "local-json-snapshot (local real quote snapshot)",
            },
            selected_batch=None,
            database_caption="\u6570\u636e\u5e93: sqlite:///monitor.db",
            copy_variant="business_cn",
            control_band_layout=["view_mode", "action_summary", "data_source", "batch_focus"],
            panel_density="comfortable",
            time_phase={
                "label": "\u6536\u76d8\u9636\u6bb5",
                "summary_label": "\u65f6\u6bb5\u6a21\u677f",
                "body": "\u9002\u5408\u6536\u76d8\u540e\u590d\u76d8\u3002",
            },
            time_phase_override_key="business_cn",
            recommendation_note="System suggestion: \u590d\u76d8\u5de5\u4f5c\u53f0 now. Current view stays on \u76d8\u4e2d\u901f\u89c8. Reason: late-session batches are available, so review mode is more useful",
            priority_action_note="\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21\uff0c\u518d\u56de\u5230\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            priority_action_sections=["saved_batches", "next_session_action", "stock_pool_health"],
            home_header_style={"detail_label": "\u5934\u90e8\u8bf4\u660e"},
        )

        self.assertIn("\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe", markdown)
        self.assertIn("\u6279\u6b21\u7126\u70b9", markdown)
        self.assertIn("\u5f53\u524d\u6279\u6b21 | \u6700\u65b0\u53ef\u7528\u5feb\u7167", markdown)
        self.assertIn("\u6570\u636e\u6765\u6e90", markdown)
        self.assertIn(
            "\u6570\u636e\u5e93 | \u6570\u636e\u5e93: sqlite:///monitor.db | \u884c\u60c5\u6765\u6e90\uff1alocal-json-snapshot (local real quote snapshot)",
            markdown,
        )
        self.assertIn("\u65f6\u6bb5\u6765\u6e90\uff1a\u624b\u52a8\u8986\u76d6 | \u5f53\u524d\u6a21\u5f0f\uff1a\u6536\u76d8\u9636\u6bb5", markdown)
        self.assertIn("System suggestion: \u590d\u76d8\u5de5\u4f5c\u53f0 now.", markdown)
        self.assertIn("\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21", markdown)
        self.assertIn("\u52a8\u4f5c\u6458\u8981", markdown)
        self.assertIn("\u5f53\u524d\u5efa\u8bae\u52a8\u4f5c", markdown)

    def test_build_control_band_markdown_applies_slot_order_override(self) -> None:
        markdown = _build_control_band_markdown(
            {
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Quick Scan View",
                "body": "Fast first-screen layout for KPI and latest alerts.",
                "supporting_copy": "Use this mode when time is limited.",
            },
            payload={
                "quote_source_display": "local-json-snapshot (local real quote snapshot)",
            },
            selected_batch="2026-06-20 14:45:00",
            database_caption="Database: sqlite:///monitor.db",
            copy_variant="default",
            control_band_layout=["action_summary", "batch_focus", "data_source", "view_mode"],
            panel_density="comfortable",
            recommendation_note="Recommendation: Quick Scan View now. Reason: active alerts exist, so a fast scan mode should stay forward",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_sections=["latest_alerts", "next_session_action", "stock_pool_health"],
            home_header_style={"detail_label": "header details"},
        )

        action_summary_index = markdown.index("Current Suggested Flow")
        batch_index = markdown.index("Current batch | 2026-06-20 14:45:00")
        source_index = markdown.index(
            "Database | Database: sqlite:///monitor.db | Quote source: local-json-snapshot (local real quote snapshot)"
        )
        view_mode_index = markdown.index("Quick Scan View | Fast first-screen layout for KPI and latest alerts.")

        self.assertLess(action_summary_index, batch_index)
        self.assertLess(batch_index, source_index)
        self.assertLess(source_index, view_mode_index)

    def test_build_action_summary_content_composes_primary_basis_and_second_step(self) -> None:
        title, body = _build_action_summary_content(
            recommendation_note="Recommendation: Quick Scan View now. Reason: active alerts exist, so a fast scan mode should stay forward",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_profile={
                "scenario": "Opening Alert Scan",
                "applicable_session": "Use near the open when fresh alerts deserve a fast first-pass review.",
                "objective": "Quickly scan fresh alerts and lock the first pass of the next-session watchlist.",
                "focus_points": "fresh alerts / opening strength / first-pass watchlist",
                "reading_order": "latest alerts -> next-session action -> stock-pool health",
                "reading_pace": "quick first pass",
                "second_step_note": "Second step: review the next-session action summary to confirm core, candidate, and avoid names.",
            },
            priority_action_sections=["latest_alerts", "next_session_action"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "next_session_action": "Action Segment > Quick Priority Cluster",
            },
            time_phase={
                "label": "Post-open Scan",
                "focus_points": ["opening strength", "early alerts", "quick validation"],
            },
            copy_variant="default",
        )

        self.assertEqual("Current Suggested Flow", title)
        self.assertIn("First step: scan the latest alerts", body)
        self.assertIn("Current scenario: Opening Alert Scan", body)
        self.assertIn("When to use: Use near the open", body)
        self.assertIn("Current objective: Quickly scan fresh alerts", body)
        self.assertIn("Priority focus: fresh alerts / opening strength / first-pass watchlist", body)
        self.assertIn("Suggested order: latest alerts -> next-session action -> stock-pool health", body)
        self.assertIn("Reading pace: quick first pass", body)
        self.assertIn("Current phase: Post-open Scan", body)
        self.assertIn("Phase focus: opening strength / early alerts / quick validation", body)
        self.assertIn("Step 1: Open Latest Alerts (`latest_alerts`)", body)
        self.assertIn("Step 1 location: Action Segment > Quick Priority Cluster", body)
        self.assertIn("Step 1 jump: [Jump to section](#section-latest-alerts-primary)", body)
        self.assertIn("Step 2: Then review Next-session Action Summary (`next_session_action`)", body)
        self.assertIn("Step 2 location: Action Segment > Quick Priority Cluster", body)
        self.assertIn("Step 2 jump: [Jump to section](#section-next-session-action-primary)", body)
        self.assertIn("In the first module, look for: Check the newest alert type, timestamp, and message first.", body)
        self.assertIn("First field: newest timestamp, alert type, and message.", body)
        self.assertIn("First group: alert detail rows.", body)
        self.assertIn("First conclusion: whether the newest alerts change today's priority read.", body)
        self.assertIn("Recommendation basis:", body)
        self.assertIn("Second step:", body)

    def test_build_action_summary_content_uses_chinese_jump_links(self) -> None:
        title, body = _build_action_summary_content(
            recommendation_note="建议：先看归档批次，再确认下一交易日动作。",
            priority_action_note="先看已保存批次，再确认下一交易日动作。",
            priority_action_profile={
                "scenario": "归档回看",
                "applicable_session": "适合收盘后快速回看当天沉淀。",
                "objective": "先看归档结果，再锁定下一步动作。",
                "focus_points": "归档批次 / 当日结论 / 下一步动作",
                "reading_order": "saved batches -> next-session action",
                "reading_pace": "总结优先",
                "second_step_note": "第二步：再看下一交易日动作。",
            },
            priority_action_sections=["saved_batches", "next_session_action"],
            priority_action_locations={
                "saved_batches": "归档区 > 批次模块",
                "next_session_action": "动作区 > 下一交易日动作",
            },
            time_phase={
                "label": "收盘阶段",
                "focus_points": ["当日结论", "快照对照", "下一时段准备"],
            },
            copy_variant="business_cn",
        )

        self.assertEqual("当前建议动作", title)
        self.assertIn("当前时段：收盘阶段", body)
        self.assertIn("时段重点：当日结论 / 快照对照 / 下一时段准备", body)
        self.assertIn("第 1 步：先看 已保存批次（saved_batches）", body)
        self.assertIn("第 1 步跳转：[跳到对应模块](#section-saved-batches-primary)", body)
        self.assertIn("第 2 步：再看 下一交易时段动作摘要（next_session_action）", body)
        self.assertIn("第 2 步跳转：[跳到对应模块](#section-next-session-action-primary)", body)

    def test_build_action_summary_content_uses_dynamic_negative_alert_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: Quick Scan View now.",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_profile={
                "scenario": "Risk Alert Scan",
                "applicable_session": "Use when negative alerts require immediate triage.",
                "objective": "Check risk names before widening the read.",
                "focus_points": "negative alerts / avoid list / first-pass triage",
                "reading_order": "latest alerts -> next-session action -> stock-pool health",
                "reading_pace": "fast but risk-aware",
                "second_step_note": "Second step: review the next-session action summary to confirm core, candidate, and avoid names.",
            },
            priority_action_sections=["latest_alerts", "next_session_action"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "next_session_action": "Action Segment > Quick Priority Cluster",
            },
            payload={
                "alert_count": 3,
                "negative_alert_count": 2,
                "risk_summary": "Risk state: elevated; 2 warning signal(s) need review.",
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the newest negative alert timestamp, type, and risk message first.",
            body,
        )
        self.assertIn(
            "First field: newest negative alert timestamp, alert type, and risk message.",
            body,
        )
        self.assertIn("First group: negative alert detail rows.", body)
        self.assertIn(
            "First conclusion: whether these negative alerts change today's first-read priority.",
            body,
        )
        self.assertIn(
            "Top-line risk view: Risk state: elevated; 2 warning signal(s) need review.",
            body,
        )

    def test_build_action_summary_content_uses_sector_move_alert_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: alert review now.",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_profile={
                "scenario": "Sector Expansion Review",
                "applicable_session": "Use when sector-level expansion may change the main-line read.",
                "objective": "Check whether sector expansion deserves a higher place in today's read.",
                "focus_points": "sector move / breadth / main-line shift",
                "reading_order": "latest alerts -> strongest sector -> next-session action",
                "reading_pace": "theme-first scan",
                "second_step_note": "Second step: compare the strongest sector before widening the research conclusion.",
            },
            priority_action_sections=["latest_alerts", "strongest_sector"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "strongest_sector": "Action Segment > Quick Priority Cluster",
            },
            payload={
                "alert_count": 2,
                "negative_alert_count": 0,
                "latest_alerts": [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "sector_move",
                        "message": "Materials line is strengthening",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "price_spike",
                        "message": "GiantChip-U surged intraday",
                    },
                ],
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the newest sector-move alert first.",
            body,
        )
        self.assertIn("First field: sector-move timestamp, alert type, and message.", body)
        self.assertIn(
            "First conclusion: whether sector strength is broadening enough to change today's main-line read.",
            body,
        )

    def test_build_action_summary_content_uses_materials_reinforcement_alert_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: chain review now.",
            priority_action_note="First step: scan the latest alerts, then confirm the strongest sector.",
            priority_action_profile={
                "scenario": "Materials Reinforcement Review",
                "applicable_session": "Use when materials-chain strength may be expanding into a broader main line.",
                "objective": "Check whether materials-chain follow-through is broadening enough to move forward.",
                "focus_points": "materials chain / expansion / main-line reinforcement",
                "reading_order": "latest alerts -> strongest sector -> leader summary",
                "reading_pace": "chain-first scan",
                "second_step_note": "Second step: compare the strongest sector before widening the research conclusion.",
            },
            priority_action_sections=["latest_alerts", "strongest_sector"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "strongest_sector": "Action Segment > Quick Priority Cluster",
            },
            payload={
                "alert_count": 2,
                "negative_alert_count": 0,
                "latest_alerts": [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "materials_focus",
                        "message": "Materials chain is strengthening",
                    },
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "sector_move",
                        "message": "Semi Materials is broadening",
                    },
                ],
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the newest materials-focus alert first.",
            body,
        )
        self.assertIn(
            "First conclusion: whether materials-chain strength is now reinforcing and broadening into a larger main-line read.",
            body,
        )

    def test_build_action_summary_content_uses_risk_news_flash_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: news review now.",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_profile={
                "scenario": "Risk News Review",
                "applicable_session": "Use when fresh news may be disrupting today's read order.",
                "objective": "Check whether risk news is interrupting sector or name priority.",
                "focus_points": "news risk / disruption / priority shift",
                "reading_order": "latest alerts -> next-session action -> strongest sector",
                "reading_pace": "risk-news scan",
                "second_step_note": "Second step: compare the next-session action summary before widening the research conclusion.",
            },
            priority_action_sections=["latest_alerts", "next_session_action"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "next_session_action": "Action Segment > Quick Priority Cluster",
            },
            payload={
                "alert_count": 1,
                "negative_alert_count": 1,
                "latest_alerts": [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "news_flash",
                        "message": "Export control risk is disturbing chip sentiment",
                    }
                ],
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the newest risk-driven news-flash alert first.",
            body,
        )
        self.assertIn(
            "First conclusion: whether fresh news is disrupting today's sector or name priority.",
            body,
        )

    def test_build_action_summary_content_uses_price_spike_alert_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: alert review now.",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_profile={
                "scenario": "Single-name Spike Review",
                "applicable_session": "Use when single-name moves may deserve promotion into the main read.",
                "objective": "Check whether a single-stock move should become part of the main research path.",
                "focus_points": "price spike / single-name strength / promotion decision",
                "reading_order": "latest alerts -> next-session action -> strongest sector",
                "reading_pace": "single-name scan",
                "second_step_note": "Second step: compare the next-session action summary before widening the research conclusion.",
            },
            priority_action_sections=["latest_alerts", "next_session_action"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "next_session_action": "Action Segment > Quick Priority Cluster",
            },
            payload={
                "alert_count": 1,
                "negative_alert_count": 0,
                "latest_alerts": [
                    {
                        "timestamp": "2026-06-20 14:45:00",
                        "alert_type": "price_spike",
                        "message": "GiantChip-U surged intraday",
                    }
                ],
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the newest price-spike alert first.",
            body,
        )
        self.assertIn("First field: price-spike timestamp, alert type, and message.", body)
        self.assertIn(
            "First conclusion: whether a single-stock move deserves promotion into the main read.",
            body,
        )

    def test_build_action_summary_content_uses_dynamic_stock_pool_blocking_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: business review now.",
            priority_action_note="First step: validate the stock-pool health block before widening the read.",
            priority_action_profile={
                "scenario": "Stock-pool Blocking Review",
                "applicable_session": "Use when pool integrity is not trustworthy.",
                "objective": "Fix blocking pool issues before relying on monitor output.",
                "focus_points": "duplicates / validation issues / trustworthiness",
                "reading_order": "stock-pool health -> latest alerts -> next-session action",
                "reading_pace": "careful validation first",
                "second_step_note": "Second step: compare the latest alerts and strongest sector before widening the research conclusion.",
            },
            priority_action_sections=["stock_pool_health", "latest_alerts"],
            priority_action_locations={
                "stock_pool_health": "Priority Segment > Validation Cluster",
                "latest_alerts": "Priority Segment > Validation Cluster",
            },
            payload={
                "stock_pool_health": {
                    "status": "invalid",
                    "risk_level": "blocking",
                },
                "stock_pool_drift_summary": "Pool drift: structure has changed vs baseline and should be reviewed first.",
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check blocking issues, duplicate codes, and validation hints first.",
            body,
        )
        self.assertIn("First field: risk level, duplicate codes, and validation hints.", body)
        self.assertIn("First group: validation issue groups.", body)
        self.assertIn(
            "First conclusion: whether the stock pool must be fixed before you rely on it today.",
            body,
        )
        self.assertIn(
            "Top-line stock-pool drift view: Pool drift: structure has changed vs baseline and should be reviewed first.",
            body,
        )

    def test_build_action_summary_content_uses_dynamic_strongest_sector_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: baseline review now.",
            priority_action_note="First step: review the strongest sector, then confirm the next-session action summary.",
            priority_action_profile={
                "scenario": "Midday Main-line Review",
                "applicable_session": "Use when the market is quiet enough to compare current strength.",
                "objective": "Confirm whether today's leading line is strong and broad enough to anchor the read.",
                "focus_points": "main line / breadth / follow-through",
                "reading_order": "strongest sector -> leader summary -> stock-pool health",
                "reading_pace": "measured comparison",
                "second_step_note": "Second step: review the leader summary to confirm whether sector leadership is coherent.",
            },
            priority_action_sections=["strongest_sector", "leader_summary"],
            priority_action_locations={
                "strongest_sector": "Analysis Segment > Main-line Cluster",
                "leader_summary": "Analysis Segment > Main-line Cluster",
            },
            payload={
                "strongest_sector_summary": {
                    "sector": "Semi Materials",
                    "avg_pct_chg": 6.3,
                    "stock_count": 4,
                }
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the leading sector name, average change, and member count first.",
            body,
        )
        self.assertIn(
            "First conclusion: whether this main line has both strong momentum and enough breadth today.",
            body,
        )

    def test_build_action_summary_content_uses_dynamic_next_session_action_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: action review now.",
            priority_action_note="First step: confirm the next-session action summary before widening the read.",
            priority_action_profile={
                "scenario": "Risk Follow-through Review",
                "applicable_session": "Use when the watchlist needs a tighter next-session filter.",
                "objective": "Decide which names must be reduced before tomorrow's follow-through read.",
                "focus_points": "avoid names / risk tags / action tiers",
                "reading_order": "next-session action -> latest alerts -> stock-pool health",
                "reading_pace": "risk-first review",
                "second_step_note": "Second step: compare the latest alerts before widening tomorrow's candidate list.",
            },
            priority_action_sections=["next_session_action", "latest_alerts"],
            priority_action_locations={
                "next_session_action": "Decision Segment > Action Cluster",
                "latest_alerts": "Decision Segment > Action Cluster",
            },
            payload={
                "next_session_action_summary": {
                    "core_count": 1,
                    "candidate_count": 1,
                    "avoid_count": 2,
                }
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the avoid list and risk reasons first.",
            body,
        )
        self.assertIn("First field: avoid names, risk tags, and score rows.", body)
        self.assertIn("First group: avoid section.", body)
        self.assertIn(
            "First conclusion: which names should be reduced or avoided before widening tomorrow's read.",
            body,
        )

    def test_build_dynamic_action_focus_specs_exposes_replaceable_thresholds_and_copy(self) -> None:
        specs = build_dynamic_action_focus_specs()

        self.assertEqual(
            1,
            specs["latest_alerts"]["negative_alert_state"]["min_negative_alert_count"],
        )
        self.assertEqual(
            5.0,
            specs["strongest_sector"]["broad_strength_state"]["min_avg_pct_chg"],
        )
        self.assertEqual(
            3,
            specs["strongest_sector"]["broad_strength_state"]["min_stock_count"],
        )
        self.assertTrue(
            bool(specs["next_session_action"]["avoid_first_state"]["require_avoid_priority"])
        )
        self.assertIn(
            "validation hints",
            str(specs["stock_pool_health"]["blocking_state"]["hint"]),
        )
        self.assertIn(
            "concentrated enough",
            str(specs["leader_summary"]["concentrated_state"]["conclusion_hint"]),
        )

    def test_build_dynamic_action_focus_specs_exposes_rule_order(self) -> None:
        specs = build_dynamic_action_focus_specs()

        self.assertEqual(
            [
                "news_flash_risk_state",
                "negative_alert_state",
                "materials_focus_reinforcement_state",
                "sector_move_state",
                "materials_focus_state",
                "news_flash_state",
                "price_spike_state",
                "active_alert_state",
            ],
            specs["latest_alerts"]["rule_order"],
        )
        self.assertEqual(
            ["blocking_state", "warning_state", "available_state"],
            specs["stock_pool_health"]["rule_order"],
        )
        self.assertEqual(
            [
                "coherent_dual_leader_state",
                "concentrated_state",
                "narrow_state",
                "available_state",
            ],
            specs["leader_summary"]["rule_order"],
        )
        self.assertEqual(
            [
                "avoid_reduce_state",
                "avoid_first_state",
                "core_stay_with_state",
                "core_first_state",
                "available_state",
            ],
            specs["next_session_action"]["rule_order"],
        )

    def test_build_dynamic_action_focus_fact_specs_exposes_registered_sources_and_transforms(self) -> None:
        fact_specs = build_dynamic_action_focus_fact_specs()

        self.assertEqual(
            "stock_pool_health",
            fact_specs["stock_pool_health"]["source_key"],
        )
        self.assertEqual(
            "today_priority_summary",
            fact_specs["today_priority_summary"]["source_key"],
        )
        self.assertEqual(
            "normalize_list",
            fact_specs["latest_alerts"]["container_transform"],
        )
        self.assertEqual(
            "normalize_dict",
            fact_specs["today_priority_summary"]["container_transform"],
        )
        self.assertEqual(
            "normalize_dict",
            fact_specs["stock_pool_health"]["container_transform"],
        )
        self.assertEqual(
            "safe_float",
            fact_specs["strongest_sector"]["fields"][0]["transform"],
        )
        self.assertEqual(
            "len",
            fact_specs["leader_summary"]["fields"][0]["transform"],
        )
        self.assertEqual(
            "safe_int",
            fact_specs["next_session_action"]["fields"][0]["transform"],
        )
        self.assertEqual(
            ["core", "reason"],
            fact_specs["next_session_action"]["fields"][3]["path"],
        )

    def test_build_priority_action_topline_specs_exposes_replaceable_context_prefixes(self) -> None:
        specs = build_priority_action_topline_specs()

        self.assertEqual(
            "Top-line daily priority conclusion",
            specs["today_priority_summary"]["context_prefix"],
        )
        self.assertEqual("Top-line risk view", specs["latest_alerts"]["context_prefix"])
        self.assertEqual(
            "Top-line main-line view",
            specs["leader_summary"]["context_prefix"],
        )
        self.assertEqual(
            "Top-line stock-pool drift view",
            specs["stock_pool_health"]["context_prefix"],
        )

    def test_build_action_summary_content_uses_dynamic_leader_summary_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: midday review now.",
            priority_action_note="First step: confirm the leader summary before widening the read.",
            priority_action_profile={
                "scenario": "Leader Continuity Review",
                "applicable_session": "Use when main-line continuity needs a quick leader check.",
                "objective": "Decide whether the current main line still has enough leader continuity.",
                "focus_points": "leader continuity / concentration / confirmation need",
                "reading_order": "leader summary -> strongest sector -> stock-pool health",
                "reading_pace": "targeted continuity check",
                "second_step_note": "Second step: compare the strongest sector before widening the main-line conclusion.",
            },
            priority_action_sections=["leader_summary", "strongest_sector"],
            priority_action_locations={
                "leader_summary": "Analysis Segment > Follow-up Cluster",
                "strongest_sector": "Analysis Segment > Follow-up Cluster",
            },
            payload={
                "leader_summary": {
                    "Trend Leader": "GiantChip-U",
                }
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the remaining active leader name first.",
            body,
        )
        self.assertIn("First field: remaining leader name and slot count.", body)
        self.assertIn("First group: leader detail rows.", body)
        self.assertIn(
            "First conclusion: whether leadership has narrowed enough that the main line now needs extra confirmation.",
            body,
        )

    def test_build_action_summary_content_uses_dual_leader_alignment_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: leader alignment review now.",
            priority_action_note="First step: confirm the leader summary before widening the read.",
            priority_action_profile={
                "scenario": "Leader Alignment Review",
                "applicable_session": "Use when leader continuity can confirm the current main line.",
                "objective": "Check whether trend and emotion leaders still point in the same direction.",
                "focus_points": "trend leader / emotion leader / leader continuity",
                "reading_order": "leader summary -> strongest sector -> next-session action",
                "reading_pace": "quick alignment check",
                "second_step_note": "Second step: compare the strongest sector before widening the main-line conclusion.",
            },
            priority_action_sections=["leader_summary", "strongest_sector"],
            priority_action_locations={
                "leader_summary": "Analysis Segment > Follow-up Cluster",
                "strongest_sector": "Analysis Segment > Follow-up Cluster",
            },
            payload={
                "leader_summary": {
                    "Trend Leader": "GiantChip-U",
                    "Emotion Leader": "NorthGas",
                }
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check whether trend and emotion leaders are both still active first.",
            body,
        )
        self.assertIn(
            "First field: trend leader, emotion leader, and active slot count.",
            body,
        )
        self.assertIn(
            "First conclusion: whether leadership is still aligned enough to confirm the current main line.",
            body,
        )

    def test_build_action_summary_content_uses_core_stay_with_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: action review now.",
            priority_action_note="First step: confirm the next-session action summary before widening the read.",
            priority_action_profile={
                "scenario": "Core Watch Review",
                "applicable_session": "Use when the next session still has a clear core leader set.",
                "objective": "Keep the front-of-watchlist names stable when the core reason stays clear.",
                "focus_points": "core names / stay-with reason / score order",
                "reading_order": "next-session action -> strongest sector -> latest alerts",
                "reading_pace": "core-first review",
                "second_step_note": "Second step: compare the strongest sector before widening tomorrow's candidate list.",
            },
            priority_action_sections=["next_session_action", "strongest_sector"],
            priority_action_locations={
                "next_session_action": "Decision Segment > Action Cluster",
                "strongest_sector": "Decision Segment > Action Cluster",
            },
            payload={
                "next_session_action_summary": {
                    "core_count": 2,
                    "candidate_count": 1,
                    "avoid_count": 0,
                    "core": {
                        "reason": "stay with Materials first.",
                    },
                }
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the core watchlist and stay-with reason first.",
            body,
        )
        self.assertIn(
            "First conclusion: which leaders should remain at the front of tomorrow's core watchlist.",
            body,
        )

    def test_build_action_summary_content_uses_avoid_reduce_focus_copy(self) -> None:
        _title, body = _build_action_summary_content(
            recommendation_note="Recommendation: risk review now.",
            priority_action_note="First step: confirm the next-session action summary before widening the read.",
            priority_action_profile={
                "scenario": "Avoid Reduction Review",
                "applicable_session": "Use when linked risk names should be cut back first.",
                "objective": "Reduce exposure to weakening linked names before tomorrow's read expands.",
                "focus_points": "avoid names / reduction reason / linked exposure",
                "reading_order": "next-session action -> latest alerts -> strongest sector",
                "reading_pace": "risk-reduction review",
                "second_step_note": "Second step: compare the latest alerts before widening tomorrow's candidate list.",
            },
            priority_action_sections=["next_session_action", "latest_alerts"],
            priority_action_locations={
                "next_session_action": "Decision Segment > Action Cluster",
                "latest_alerts": "Decision Segment > Action Cluster",
            },
            payload={
                "next_session_action_summary": {
                    "core_count": 1,
                    "candidate_count": 1,
                    "avoid_count": 1,
                    "avoid": {
                        "reason": "reduce names tied to fading strength.",
                    },
                }
            },
            copy_variant="default",
        )

        self.assertIn(
            "In the first module, look for: Check the avoid list and the reduction reason first.",
            body,
        )
        self.assertIn(
            "First conclusion: which linked names should be cut back before tomorrow's follow-through read.",
            body,
        )

    def test_build_action_summary_markdown_uses_business_cn_copy(self) -> None:
        markdown = _build_action_summary_markdown(
            panel_density="comfortable",
            recommendation_note="System suggestion: \u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe now. Current view stays on \u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe. Reason: late-session batches are available, so review mode is more useful",
            priority_action_note="\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21\uff0c\u518d\u56de\u5230\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            priority_action_profile={
                "scenario": "\u6279\u6b21\u5bf9\u6bd4\u590d\u76d8",
                "applicable_session": "\u9002\u7528\u4e8e\u5c3e\u76d8\u6216\u76d8\u540e\uff0c\u5df2\u7ecf\u79ef\u7d2f\u591a\u4e2a\u5feb\u7167\u53ef\u4ee5\u5bf9\u6bd4\u7684\u65f6\u6bb5\u3002",
                "objective": "\u5148\u5bf9\u6bd4\u6700\u8fd1\u5feb\u7167\u53d8\u5316\uff0c\u518d\u786e\u5b9a\u54ea\u4e9b\u6807\u7684\u503c\u5f97\u7ee7\u7eed\u8ddf\u8e2a\u3002",
                "focus_points": "\u5feb\u7167\u53d8\u5316 / \u5ef6\u7eed\u6807\u7684 / \u8ddf\u8e2a\u5019\u9009",
                "reading_order": "\u5df2\u4fdd\u5b58\u6279\u6b21 -> \u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c -> \u76d1\u63a7\u6c60\u5065\u5eb7",
                "reading_pace": "\u5bf9\u6bd4\u590d\u76d8",
                "second_step_note": "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u786e\u8ba4\u54ea\u4e9b\u53d8\u5316\u503c\u5f97\u7ee7\u7eed\u8ddf\u8e2a\u3002",
            },
            priority_action_sections=["saved_batches", "next_session_action"],
            priority_action_locations={
                "saved_batches": "\u5f52\u6863\u6bb5\u843d > \u5feb\u7167\u5f52\u6863",
                "next_session_action": "\u4f18\u5148\u6bb5\u843d > \u4f18\u5148\u5206\u7ec4",
            },
            copy_variant="business_cn",
            detail_label="\u5934\u90e8\u8bf4\u660e",
        )

        self.assertIn("\u52a8\u4f5c\u6458\u8981", markdown)
        self.assertIn("\u5f53\u524d\u5efa\u8bae\u52a8\u4f5c", markdown)
        self.assertIn("\u5f53\u524d\u573a\u666f\uff1a\u6279\u6b21\u5bf9\u6bd4\u590d\u76d8", markdown)
        self.assertIn("\u9002\u7528\u65f6\u6bb5\uff1a", markdown)
        self.assertIn("\u5f53\u524d\u76ee\u6807\uff1a\u5148\u5bf9\u6bd4\u6700\u8fd1\u5feb\u7167\u53d8\u5316", markdown)
        self.assertIn("\u63a8\u8350\u5173\u6ce8\uff1a", markdown)
        self.assertIn("\u5efa\u8bae\u987a\u5e8f\uff1a", markdown)
        self.assertIn("\u9605\u8bfb\u8282\u594f\uff1a", markdown)
        self.assertIn("\u7b2c 1 \u6b65\uff1a\u5148\u770b \u5df2\u4fdd\u5b58\u6279\u6b21\uff08saved_batches\uff09", markdown)
        self.assertIn("\u6a21\u5757\u5148\u770b\uff1a\u5148\u770b\u6700\u8fd1\u4e24\u4e2a\u5feb\u7167\u65f6\u95f4", markdown)
        self.assertIn("\u9996\u770b\u5b57\u6bb5\uff1a", markdown)
        self.assertIn("\u9996\u770b\u5206\u7ec4\uff1a", markdown)
        self.assertIn("\u9996\u770b\u7ed3\u8bba\uff1a", markdown)
        self.assertIn("\u7b2c 1 \u6b65\u4f4d\u7f6e\uff1a\u5f52\u6863\u6bb5\u843d > \u5feb\u7167\u5f52\u6863", markdown)
        self.assertIn("\u7b2c 2 \u6b65\uff1a\u518d\u770b \u4e0b\u4e00\u4ea4\u6613\u65f6\u6bb5\u52a8\u4f5c\u6458\u8981\uff08next_session_action\uff09", markdown)
        self.assertIn("\u7b2c 2 \u6b65\u4f4d\u7f6e\uff1a\u4f18\u5148\u6bb5\u843d > \u4f18\u5148\u5206\u7ec4", markdown)
        self.assertIn("\u7b2c\u4e8c\u6b65", markdown)

    def test_build_priority_action_profile_returns_business_scenario_and_objective(self) -> None:
        profile = _build_priority_action_profile(
            "risk_alert_scan",
            copy_variant="default",
        )

        self.assertEqual("Risk Alert Scan", profile["scenario"])
        self.assertIn("most urgent risk names", profile["objective"])
        self.assertIn("core, candidate, and avoid names", profile["second_step_note"])

    def test_build_priority_action_profile_can_apply_phase_specific_overrides(self) -> None:
        default_profile = _build_priority_action_profile(
            "daily_priority_review",
            copy_variant="default",
            phase_key="compact",
        )
        business_profile = _build_priority_action_profile(
            "close_review",
            copy_variant="business_cn",
            phase_key="business_cn",
        )

        self.assertEqual(
            "today priority summary -> latest alerts -> next-session action",
            default_profile["reading_order"],
        )
        self.assertIn("fresh alerts", default_profile["focus_points"])
        self.assertEqual(
            "已保存批次 -> 股票池健康度 -> 下一交易时段动作摘要",
            business_profile["reading_order"],
        )
        self.assertIn("结构是否稳定", business_profile["second_step_note"])

    def test_build_priority_action_profile_specs_exposes_replaceable_first_and_second_step_copy(self) -> None:
        specs = build_priority_action_profile_specs("business_cn")

        self.assertIn("daily_priority_review", specs)
        self.assertIn("batch_review", specs)
        self.assertIn("\u9996\u6b65\u52a8\u4f5c", specs["batch_review"]["first_step_note"])
        self.assertIn("\u7b2c\u4e8c\u6b65", specs["batch_review"]["second_step_note"])
        self.assertIn("\u9002\u7528\u4e8e", specs["batch_review"]["applicable_session"])
        self.assertIn("\u5feb\u7167\u53d8\u5316", specs["batch_review"]["focus_points"])
        self.assertIn("\u5f53\u65e5\u4f18\u5148\u6458\u8981", specs["daily_priority_review"]["first_step_note"])
        self.assertIn("saved batches", build_priority_action_profile_specs()["batch_review"]["reading_order"])
        self.assertIn("comparison", build_priority_action_profile_specs()["batch_review"]["reading_pace"])

    def test_build_priority_action_module_copy_specs_exposes_replaceable_step_and_jump_copy(self) -> None:
        default_specs = build_priority_action_module_copy_specs()
        business_specs = build_priority_action_module_copy_specs("business_cn")

        self.assertEqual("Step 1: Open {label}", default_specs["step_1_line_template"])
        self.assertEqual("Step 2 jump: {link}", default_specs["step_2_jump_template"])
        self.assertEqual("Jump to section", default_specs["jump_link_label"])
        self.assertEqual("第 1 步：先看 {label}", business_specs["step_1_line_template"])
        self.assertEqual("第 2 步位置：{location}", business_specs["step_2_location_template"])
        self.assertEqual("跳到对应模块", business_specs["jump_link_label"])

    def test_build_priority_action_focus_copy_specs_exposes_replaceable_focus_line_copy(self) -> None:
        default_specs = build_priority_action_focus_copy_specs()
        business_specs = build_priority_action_focus_copy_specs("business_cn")

        self.assertEqual(
            "In the first module, look for: {value}",
            default_specs["hint_line_template"],
        )
        self.assertEqual("First field: {value}", default_specs["field_line_template"])
        self.assertIn("First field: ", default_specs["strip_prefixes"])
        self.assertEqual("模块先看：{value}", business_specs["hint_line_template"])
        self.assertEqual("首看字段：{value}", business_specs["field_line_template"])
        self.assertIn("先看字段：", business_specs["strip_prefixes"])

    def test_build_priority_action_topline_copy_specs_exposes_replaceable_context_line_copy(self) -> None:
        default_specs = build_priority_action_topline_copy_specs()
        business_specs = build_priority_action_topline_copy_specs("business_cn")

        self.assertEqual("{prefix}: {value}", default_specs["context_line_template"])
        self.assertEqual("{prefix}：{value}", business_specs["context_line_template"])

    def test_build_priority_action_phase_copy_specs_exposes_replaceable_phase_line_copy(self) -> None:
        default_specs = build_priority_action_phase_copy_specs()
        business_specs = build_priority_action_phase_copy_specs("business_cn")

        self.assertEqual("Current phase: {label}", default_specs["phase_line_template"])
        self.assertEqual("Phase focus: {value}", default_specs["phase_focus_line_template"])
        self.assertEqual("当前时段：{label}", business_specs["phase_line_template"])
        self.assertEqual("时段重点：{value}", business_specs["phase_focus_line_template"])

    def test_build_priority_action_phase_override_specs_exposes_explicit_phase_section_order(self) -> None:
        specs = build_priority_action_phase_override_specs()

        self.assertEqual(
            ["latest_alerts", "next_session_action", "stock_pool_health"],
            specs["compact"]["scenario_sections"]["alert_scan"],
        )
        self.assertEqual(
            ["strongest_sector", "leader_summary", "next_session_action"],
            specs["default"]["scenario_sections"]["baseline_review"],
        )
        self.assertEqual(
            ["strongest_sector", "leader_summary", "stock_pool_health"],
            specs["default"]["scenario_sections"]["midday_baseline_review"],
        )
        self.assertEqual(
            ["saved_batches", "stock_pool_health", "next_session_action"],
            specs["business_cn"]["scenario_sections"]["close_review"],
        )

    def test_build_priority_action_phase_profile_override_specs_exposes_phase_specific_profile_adjustments(self) -> None:
        default_specs = build_priority_action_phase_profile_override_specs()
        business_specs = build_priority_action_phase_profile_override_specs("business_cn")

        self.assertEqual(
            "today priority summary -> latest alerts -> next-session action",
            default_specs["compact"]["daily_priority_review"]["reading_order"],
        )
        self.assertIn(
            "leader summary",
            default_specs["default"]["baseline_review"]["reading_order"],
        )
        self.assertEqual(
            "已保存批次 -> 股票池健康度 -> 下一交易时段动作摘要",
            business_specs["business_cn"]["close_review"]["reading_order"],
        )

    def test_resolve_priority_action_phase_key_prefers_compact_for_opening_or_alert_phase(self) -> None:
        phase_key = _resolve_priority_action_phase_key(
            payload={
                "latest_timestamp": "2026-07-18 09:35:00",
                "alert_count": 1,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 09:35:00"],
            }
        )

        self.assertEqual("compact", phase_key)

    def test_build_time_phase_override_options_and_labels_expose_manual_override_choices(self) -> None:
        options = _build_time_phase_override_options()

        self.assertEqual(["auto", "compact", "default", "business_cn"], options)
        self.assertEqual("auto", _resolve_time_phase_override_key("unknown"))
        self.assertEqual(
            "Auto",
            _resolve_time_phase_override_label(
                "auto",
                copy_variant="default",
                auto_label="Auto",
            ),
        )
        self.assertEqual(
            "盘前快扫",
            _resolve_time_phase_override_label(
                "compact",
                copy_variant="business_cn",
                auto_label="自动判断",
            ),
        )

    def test_resolve_priority_action_phase_key_prefers_business_cn_for_late_multi_batch_phase(self) -> None:
        phase_key = _resolve_priority_action_phase_key(
            payload={
                "latest_timestamp": "2026-07-18 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 14:45:00", "2026-07-18 13:30:00"],
            }
        )

        self.assertEqual("business_cn", phase_key)

    def test_resolve_priority_action_phase_key_allows_manual_override_to_win(self) -> None:
        phase_key = _resolve_priority_action_phase_key(
            payload={
                "latest_timestamp": "2026-07-18 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 14:45:00", "2026-07-18 13:30:00"],
            },
            phase_override_key="default",
        )

        self.assertEqual("default", phase_key)

    def test_resolve_effective_time_phase_uses_english_closing_copy_for_default_surface(self) -> None:
        phase = _resolve_effective_time_phase(
            payload={
                "latest_timestamp": "2026-07-18 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 14:45:00", "2026-07-18 13:30:00"],
            },
            copy_variant="default",
        )

        self.assertEqual("Closing Review Phase", phase["label"])
        self.assertIn("late-session replay", str(phase["body"]))
        self.assertIn("day-end conclusion", list(phase["focus_points"]))

    def test_resolve_effective_time_phase_allows_manual_override_to_replace_auto_phase(self) -> None:
        phase = _resolve_effective_time_phase(
            payload={
                "latest_timestamp": "2026-07-18 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 14:45:00", "2026-07-18 13:30:00"],
            },
            copy_variant="default",
            phase_override_key="default",
        )

        self.assertEqual("Intraday Phase", phase["label"])

    def test_resolve_effective_time_phase_uses_chinese_opening_copy_for_business_surface(self) -> None:
        phase = _resolve_effective_time_phase(
            payload={
                "latest_timestamp": "2026-07-18 09:35:00",
                "alert_count": 1,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 09:35:00"],
            },
            copy_variant="business_cn",
        )

        self.assertEqual("盘前快扫", phase["label"])
        self.assertIn("快速确认", str(phase["body"]))
        self.assertIn("开盘强度", list(phase["focus_points"]))

    def test_build_dashboard_variant_recommendation_note_uses_recommended_copy_for_matching_view(self) -> None:
        note = _build_dashboard_variant_recommendation_note(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
            variant_specs=build_view_variant_specs(),
        )

        self.assertIn("Recommendation: Quick Scan View now.", note)
        self.assertIn("near the open", note)

    def test_build_dashboard_variant_recommendation_note_keeps_manual_view_context(self) -> None:
        note = _build_dashboard_variant_recommendation_note(
            selected_variant_key="default",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
            variant_specs=build_view_variant_specs(),
        )

        self.assertIn("System suggestion: 中文业务视图 now.", note)
        self.assertIn("Current view stays on Research View.", note)
        self.assertIn("late-session batches are available", note)

    def test_build_dashboard_variant_recommendation_note_uses_stock_pool_reason_first(self) -> None:
        note = _build_dashboard_variant_recommendation_note(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 2,
                "negative_alert_count": 1,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "invalid",
                    "risk_level": "blocking",
                    "comparison_tags": ["Materials Exposure Up"],
                },
            },
            variant_specs=build_view_variant_specs(),
        )

        self.assertIn("Recommendation: 中文业务视图 now.", note)
        self.assertIn("stock-pool health is blocking", note)

    def test_build_dashboard_priority_action_note_prefers_alert_scan_for_compact_mode(self) -> None:
        note = _build_dashboard_priority_action_note(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 2,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
            copy_variant="default",
        )

        self.assertIn("First step: scan the latest alerts", note)

    def test_build_dashboard_priority_action_note_prefers_today_priority_summary_when_available(self) -> None:
        note = _build_dashboard_priority_action_note(
            selected_variant_key="default",
            recommended_variant_key="default",
            payload={
                "latest_timestamp": "2026-07-18 09:35:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 09:35:00"],
                "today_priority_summary": {
                    "shown_items": 2,
                    "daily_conclusion": "先看风险扩散，再看主线强化。",
                },
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
            copy_variant="business_cn",
        )

        self.assertIn("先读当日优先摘要", note)

    def test_build_dashboard_priority_action_note_prefers_stock_pool_validation_when_blocking(self) -> None:
        note = _build_dashboard_priority_action_note(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 2,
                "negative_alert_count": 1,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "invalid",
                    "risk_level": "blocking",
                    "comparison_tags": ["Materials Exposure Up"],
                },
            },
            copy_variant="default",
        )

        self.assertIn("validate stock-pool health", note)

    def test_build_dashboard_priority_action_note_prefers_close_review_for_late_business_cn(self) -> None:
        note = _build_dashboard_priority_action_note(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
            copy_variant="business_cn",
        )

        self.assertIn("\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21", note)
        self.assertIn("\u6700\u5f3a\u677f\u5757", note)

    def test_resolve_priority_action_scenario_prefers_stock_pool_blocking_review(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 2,
                "negative_alert_count": 1,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "invalid",
                    "risk_level": "blocking",
                    "comparison_tags": ["Materials Exposure Up"],
                },
            },
        )

        self.assertEqual("stock_pool_blocking_review", scenario)

    def test_resolve_priority_action_scenario_prefers_daily_priority_review_when_summary_exists(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="default",
            recommended_variant_key="default",
            payload={
                "latest_timestamp": "2026-07-18 09:35:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 09:35:00"],
                "today_priority_summary": {
                    "shown_items": 2,
                },
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("daily_priority_review", scenario)

    def test_resolve_priority_action_scenario_prefers_daily_priority_risk_review_when_summary_and_risk_exist(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="default",
            recommended_variant_key="default",
            payload={
                "latest_timestamp": "2026-07-18 10:15:00",
                "alert_count": 2,
                "negative_alert_count": 1,
                "available_batches": ["2026-07-18 10:15:00"],
                "today_priority_summary": {
                    "shown_items": 2,
                },
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("daily_priority_risk_review", scenario)

    def test_resolve_priority_action_scenario_prefers_close_review_when_saved_batches_accumulate_late(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("close_review", scenario)

    def test_resolve_priority_action_scenario_prefers_intraday_alert_review_during_mid_session_alerts(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 2,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("intraday_alert_review", scenario)

    def test_resolve_priority_action_scenario_prefers_close_review_for_late_business_cn_batches(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("close_review", scenario)

    def test_resolve_priority_action_scenario_prefers_midday_baseline_review_for_quiet_mid_session(self) -> None:
        scenario = _resolve_priority_action_scenario(
            selected_variant_key="default",
            recommended_variant_key="default",
            payload={
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual("midday_baseline_review", scenario)

    def test_resolve_priority_action_sections_prefers_alert_stack_for_compact_flow(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 2,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["latest_alerts", "next_session_action", "stock_pool_health"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_opening_priority_stack_when_summary_exists_early(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="default",
            recommended_variant_key="default",
            payload={
                "latest_timestamp": "2026-07-18 09:35:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 09:35:00"],
                "today_priority_summary": {
                    "shown_items": 2,
                },
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["today_priority_summary", "latest_alerts", "next_session_action"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_close_review_stack_for_late_review_flow(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["saved_batches", "stock_pool_health", "next_session_action"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_stock_pool_drift_stack_when_pool_drifts(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="default",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Materials Exposure Up"],
                },
            },
        )

        self.assertEqual(
            ["stock_pool_health", "saved_batches", "next_session_action"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_intraday_alert_stack_during_mid_session_alerts(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 2,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["latest_alerts", "strongest_sector", "next_session_action"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_close_review_stack_for_late_business_cn_batches(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="business_cn",
            recommended_variant_key="business_cn",
            payload={
                "latest_timestamp": "2026-06-20 14:45:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": [
                    "2026-06-20 14:45:00",
                    "2026-06-20 13:30:00",
                ],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["saved_batches", "stock_pool_health", "next_session_action"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_daily_priority_alert_crosscheck_for_compact_phase(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-07-18 09:35:00",
                "alert_count": 1,
                "negative_alert_count": 0,
                "available_batches": ["2026-07-18 09:35:00"],
                "today_priority_summary": {
                    "shown_items": 2,
                },
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["today_priority_summary", "latest_alerts", "next_session_action"],
            sections,
        )

    def test_resolve_priority_action_sections_prefers_midday_baseline_stack_for_quiet_mid_session(self) -> None:
        sections = _resolve_priority_action_sections(
            selected_variant_key="default",
            recommended_variant_key="default",
            payload={
                "latest_timestamp": "2026-06-20 11:15:00",
                "alert_count": 0,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 11:15:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["strongest_sector", "leader_summary", "stock_pool_health"],
            sections,
        )

    def test_normalize_priority_action_sections_for_layout_keeps_visible_unique_order(self) -> None:
        sections = _normalize_priority_action_sections_for_layout(
            [
                {"section_key": "latest_alerts"},
                {"section_key": "next_session_action"},
                {"section_key": "stock_pool_health"},
            ],
            priority_action_sections=[
                "latest_alerts",
                "missing_section",
                "next_session_action",
                "latest_alerts",
                "",
                "stock_pool_health",
            ],
        )

        self.assertEqual(
            ["latest_alerts", "next_session_action", "stock_pool_health"],
            sections,
        )

    def test_build_priority_action_layout_strategy_generates_pins_and_deferred_sections(self) -> None:
        strategy = _build_priority_action_layout_strategy(
            selected_variant_key="compact",
            recommended_variant_key="compact",
            payload={
                "latest_timestamp": "2026-06-20 09:35:00",
                "alert_count": 2,
                "negative_alert_count": 0,
                "available_batches": ["2026-06-20 09:35:00"],
                "stock_pool_health": {
                    "status": "valid",
                    "risk_level": "clean",
                    "comparison_tags": ["Structure Stable"],
                },
            },
        )

        self.assertEqual(
            ["latest_alerts", "next_session_action", "stock_pool_health"],
            strategy["pinned_sections"],
        )
        self.assertIn("saved_batches", strategy["deferred_sections"])

    def test_apply_role_strategy_to_page_layout_can_use_priority_action_pins(self) -> None:
        resolved = _apply_role_strategy_to_page_layout(
            [
                {
                    "section_type": "content",
                    "section_key": "stock_pool_health",
                    "section_role_key": "validation",
                    "module_priority": "3",
                },
                {
                    "section_type": "content",
                    "section_key": "saved_batches",
                    "section_role_key": "archive",
                    "module_priority": "1",
                },
                {
                    "section_type": "content",
                    "section_key": "next_session_action",
                    "section_role_key": "decision",
                    "module_priority": "2",
                },
                {
                    "section_type": "content",
                    "section_key": "latest_alerts",
                    "section_role_key": "validation",
                    "module_priority": "4",
                },
            ],
            role_strategy=_build_priority_action_layout_strategy(
                selected_variant_key="business_cn",
                recommended_variant_key="business_cn",
                payload={
                    "latest_timestamp": "2026-06-20 14:45:00",
                    "alert_count": 0,
                    "negative_alert_count": 0,
                    "available_batches": [
                        "2026-06-20 14:45:00",
                        "2026-06-20 13:30:00",
                    ],
                    "stock_pool_health": {
                        "status": "valid",
                        "risk_level": "clean",
                        "comparison_tags": ["Structure Stable"],
                    },
                },
            ),
        )

        self.assertEqual(
            ["saved_batches", "next_session_action", "stock_pool_health", "latest_alerts"],
            [section["section_key"] for section in resolved],
        )

    def test_filter_page_layout_sections_excludes_header_owned_sections(self) -> None:
        from app.dashboard.streamlit_app import _filter_page_layout_sections

        filtered = _filter_page_layout_sections(
            [
                {"section_type": "kpi", "section_key": "kpi_cards"},
                {"section_type": "content", "section_key": "latest_alerts"},
            ],
            excluded_section_keys={"kpi_cards"},
        )

        self.assertEqual([{"section_type": "content", "section_key": "latest_alerts"}], filtered)

    def test_render_home_header_can_render_control_band_before_kpi(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "latest_timestamp": "2026-06-20 14:45:00",
            "mainline_summary": "Main line: Semi Materials remains the clearest strength.",
            "stock_pool_drift_summary": "Pool drift: stable vs baseline.",
            "risk_summary": "Risk state: stable; no dominant warning signal is active.",
            "positive_alert_count": 3,
            "negative_alert_count": 1,
            "alert_count": 4,
        }

        _render_home_header(
            fake_st,
            payload,
            home_header_layout=["control_band", "kpi"],
            home_header_style={
                "header_label": "home header",
                "detail_label": "header details",
                "header_body": "First-screen workspace entry",
                "supporting_copy": "Mode context, batch focus, data source, and KPI stay grouped here.",
                "compact_supporting_copy": "Header context + KPI",
                "default_tone": "neutral",
            },
            view_mode_note={
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Research View",
                "body": "Balanced research layout for main line and structure health.",
                "supporting_copy": "Use this mode when you want the fuller analysis path.",
            },
            role_strategy={
                "primary_roles": ["analysis", "validation"],
                "secondary_roles": ["decision", "archive"],
                "deferred_roles": [],
                "hidden_roles": [],
                "summary_label": "role strategy",
                "body": "Balanced across analysis and validation.",
            },
            recommendation_note="Recommendation: Research View now. Reason: the session is relatively quiet, so the balanced default view is enough",
            priority_action_note="First step: confirm the strongest sector and stock-pool health, then expand into deeper analysis.",
            priority_action_sections=["strongest_sector", "stock_pool_health", "next_session_action"],
            priority_action_locations={
                "strongest_sector": "Priority Segment > Priority Cluster",
                "stock_pool_health": "Priority Segment > Priority Cluster",
            },
            task_template={
                "label": "Intraday Tracking",
                "summary_label": "task template",
                "body": "Best for following the evolving main line.",
                "focus_points": ["main line continuity", "leader follow-through"],
            },
            time_phase={
                "label": "Intraday Phase",
                "summary_label": "time phase",
                "body": "Designed for live-session tracking.",
                "focus_points": ["leadership continuity", "intraday drift"],
            },
            selected_batch="2026-06-20 14:45:00",
            database_caption="Database: sqlite:///monitor.db",
            control_band_copy_variant="default",
            control_band_layout=["view_mode", "action_summary", "batch_focus", "data_source"],
            kpi_copy_variant="default",
            kpi_summary_layout={"card_order": ["latest_timestamp", "mainline_summary"]},
            panel_density="comfortable",
        )

        self.assertIn("HOME HEADER", fake_st.markdown_calls[0])
        self.assertIn("Research View", fake_st.markdown_calls[1])
        self.assertTrue(any("First step: confirm the strongest sector" in call for call in fake_st.markdown_calls[1:]))
        self.assertTrue(any("Step 1 location: Priority Segment > Priority Cluster" in call for call in fake_st.markdown_calls[1:]))
        self.assertTrue(any("KPI SECTION" in call for call in fake_st.markdown_calls[2:]))

    def test_render_home_header_can_render_kpi_before_control_band(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "latest_timestamp": "2026-06-20 14:45:00",
            "mainline_summary": "Main line: Semi Materials remains the clearest strength.",
            "stock_pool_drift_summary": "Pool drift: stable vs baseline.",
            "risk_summary": "Risk state: stable; no dominant warning signal is active.",
            "positive_alert_count": 3,
            "negative_alert_count": 1,
            "alert_count": 4,
        }

        _render_home_header(
            fake_st,
            payload,
            home_header_layout=["kpi", "control_band"],
            home_header_style={
                "header_label": "home header",
                "detail_label": "header details",
                "header_body": "First-screen workspace entry",
                "supporting_copy": "Mode context, batch focus, data source, and KPI stay grouped here.",
                "compact_supporting_copy": "Header context + KPI",
                "default_tone": "neutral",
            },
            view_mode_note={
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Quick Scan View",
                "body": "Fast first-screen layout for KPI and latest alerts.",
                "supporting_copy": "Use this mode when time is limited.",
            },
            role_strategy={
                "primary_roles": ["decision", "validation"],
                "secondary_roles": ["analysis"],
                "deferred_roles": ["analysis"],
                "hidden_roles": ["archive"],
                "pinned_sections": ["next_session_action", "stock_pool_health", "latest_alerts"],
                "deferred_sections": ["strongest_sector", "leader_summary", "sector_strength", "top_movers"],
                "hidden_sections": ["saved_batches"],
                "summary_label": "role strategy",
                "body": "Prioritizes fast decision support and stock-pool trust checks before deeper analysis.",
            },
            recommendation_note="Recommendation: Quick Scan View now. Reason: active alerts exist, so a fast scan mode should stay forward",
            priority_action_note="First step: scan the latest alerts, then confirm the next-session action summary.",
            priority_action_sections=["latest_alerts", "next_session_action", "stock_pool_health"],
            priority_action_locations={
                "latest_alerts": "Action Segment > Quick Priority Cluster",
                "next_session_action": "Action Segment > Quick Priority Cluster",
            },
            task_template={
                "label": "Open Quick Scan",
                "summary_label": "task template",
                "body": "Best for deciding what deserves immediate attention near the open.",
                "focus_points": ["next-session action", "pool health check", "latest alerts first"],
            },
            time_phase={
                "label": "Post-open Scan",
                "summary_label": "time phase",
                "body": "Designed for the opening window when rapid prioritization matters most.",
                "focus_points": ["opening strength", "early alerts", "quick validation"],
            },
            selected_batch="2026-06-20 14:45:00",
            database_caption="Database: sqlite:///monitor.db",
            control_band_copy_variant="default",
            control_band_layout=["action_summary", "batch_focus", "view_mode", "data_source"],
            kpi_copy_variant="default",
            kpi_summary_layout={"card_order": ["mainline_summary", "risk_summary"]},
            panel_density="compact",
        )

        self.assertIn("HOME HEADER", fake_st.markdown_calls[0])
        self.assertTrue("KPI SECTION" in fake_st.markdown_calls[1])
        self.assertTrue(any("Quick Scan View" in call for call in fake_st.markdown_calls[3:]))
        self.assertTrue(any("task template: Open Quick Scan" in call for call in fake_st.markdown_calls[3:]))
        self.assertTrue(
            any(
                "time phase: Phase source: Automatic | Post-open Scan" in call
                for call in fake_st.markdown_calls[3:]
            )
        )
        self.assertTrue(any("Primary: Decision / Validation" in call for call in fake_st.markdown_calls[3:]))
        self.assertTrue(any("Hidden: Archive" in call for call in fake_st.markdown_calls[3:]))
        self.assertTrue(any("Pinned sections: next_session_action / stock_pool_health / latest_alerts" in call for call in fake_st.markdown_calls[3:]))
        self.assertTrue(any("First step: scan the latest alerts" in call for call in fake_st.markdown_calls[3:]))
        self.assertTrue(any("Step 1 location: Action Segment > Quick Priority Cluster" in call for call in fake_st.markdown_calls[3:]))

    def test_render_home_header_can_use_business_cn_header_style(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "latest_timestamp": "2026-06-20 14:45:00",
            "mainline_summary": "Main line: Semi Materials remains the clearest strength.",
            "stock_pool_drift_summary": "Pool drift: stable vs baseline.",
            "risk_summary": "Risk state: stable; no dominant warning signal is active.",
            "positive_alert_count": 3,
            "negative_alert_count": 1,
            "alert_count": 4,
        }

        _render_home_header(
            fake_st,
            payload,
            home_header_layout=["control_band", "kpi"],
            home_header_style={
                "header_label": "\u9996\u5c4f\u5934\u90e8",
                "detail_label": "\u5934\u90e8\u8bf4\u660e",
                "header_body": "\u9996\u5c4f\u5de5\u4f5c\u53f0\u5165\u53e3",
                "supporting_copy": "\u89c6\u56fe\u4e0a\u4e0b\u6587\u3001\u6279\u6b21\u7126\u70b9\u3001\u6570\u636e\u6765\u6e90\u548c KPI \u4f1a\u5728\u8fd9\u91cc\u7ec4\u5408\u663e\u793a\u3002",
                "compact_supporting_copy": "\u5934\u90e8\u4e0a\u4e0b\u6587 + KPI",
                "default_tone": "neutral",
            },
            view_mode_note={
                "tone": "accent",
                "summary_label": "\u89c6\u56fe\u6a21\u5f0f",
                "title": "\u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe",
                "body": "\u4f18\u5148\u663e\u793a\u76d1\u63a7\u6c60\u5065\u5eb7\u3001\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u548c\u6700\u65b0\u63d0\u9192\u3002",
                "supporting_copy": "\u9002\u5408\u5148\u770b\u5c31\u7eea\u5ea6\u4e0e\u52a8\u4f5c\u7ed3\u8bba\u3002",
            },
            role_strategy={
                "primary_roles": ["validation", "decision"],
                "secondary_roles": ["analysis", "archive"],
                "deferred_roles": ["archive"],
                "hidden_roles": [],
                "pinned_sections": ["stock_pool_health", "next_session_action", "latest_alerts"],
                "deferred_sections": ["saved_batches"],
                "hidden_sections": [],
                "summary_label": "\u89d2\u8272\u7b56\u7565",
                "body": "\u4f18\u5148\u7a81\u51fa\u6821\u9a8c\u4e0e\u51b3\u7b56\u3002",
            },
            recommendation_note="System suggestion: \u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe now. Current view stays on \u4e2d\u6587\u4e1a\u52a1\u89c6\u56fe. Reason: late-session batches are available, so review mode is more useful",
            priority_action_note="\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21\uff0c\u518d\u56de\u5230\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\u3002",
            priority_action_sections=["saved_batches", "next_session_action", "stock_pool_health"],
            priority_action_locations={
                "saved_batches": "\u5f52\u6863\u6bb5\u843d > \u5feb\u7167\u5f52\u6863",
                "next_session_action": "\u4f18\u5148\u6bb5\u843d > \u4f18\u5148\u5206\u7ec4",
            },
            task_template={
                "label": "\u6536\u76d8\u590d\u76d8",
                "summary_label": "\u4efb\u52a1\u6a21\u677f",
                "body": "\u66f4\u9002\u5408\u4e2d\u6587\u4e1a\u52a1\u590d\u76d8\u3002",
                "focus_points": ["\u6821\u9a8c\u72b6\u6001", "\u52a8\u4f5c\u7ed3\u8bba"],
            },
            time_phase={
                "label": "\u6536\u76d8\u9636\u6bb5",
                "summary_label": "\u65f6\u6bb5\u6a21\u677f",
                "body": "\u9002\u5408\u6536\u76d8\u540e\u590d\u76d8\u3002",
                "focus_points": ["\u5f53\u65e5\u7ed3\u8bba", "\u5feb\u7167\u5bf9\u7167"],
            },
            selected_batch=None,
            database_caption="\u6570\u636e\u5e93: sqlite:///monitor.db",
            control_band_copy_variant="business_cn",
            control_band_layout=["view_mode", "action_summary", "data_source", "batch_focus"],
            kpi_copy_variant="business_cn",
            kpi_summary_layout={"card_order": ["latest_timestamp", "mainline_summary"]},
            panel_density="comfortable",
        )

        self.assertIn("\u9996\u5c4f\u5934\u90e8", fake_st.markdown_calls[0])
        self.assertTrue(any("\u5934\u90e8\u8bf4\u660e" in call for call in fake_st.markdown_calls[:4]))
        self.assertTrue(any("\u9996\u6b65\u52a8\u4f5c\uff1a\u5148\u5bf9\u7167\u5df2\u4fdd\u5b58\u6279\u6b21" in call for call in fake_st.markdown_calls[1:]))
        self.assertTrue(any("\u4f4d\u7f6e\uff1a\u5f52\u6863\u6bb5\u843d > \u5feb\u7167\u5f52\u6863" in call for call in fake_st.markdown_calls[1:]))

    def test_render_content_group_intro_uses_group_metadata_and_surface_copy(self) -> None:
        fake_st = _FakeStreamlit()

        _render_content_group_intro(
            fake_st,
            {
                "group_key": "priority_cluster",
                "group_title": "Priority Cluster",
                "group_tone": "accent",
                "group_role_key": "decision",
            },
            panel_density="comfortable",
            surface_copy_variant="default",
        )

        self.assertTrue(any("CONTENT GROUP" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("Priority Cluster" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("Role: Decision" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("Related homepage sections stay grouped here" in call for call in fake_st.markdown_calls))

    def test_render_page_segment_intro_uses_segment_metadata_and_surface_copy(self) -> None:
        fake_st = _FakeStreamlit()

        _render_page_segment_intro(
            fake_st,
            {
                "segment_key": "priority_segment",
                "segment_title": "Priority Segment",
                "segment_tone": "accent",
                "segment_role_key": "decision",
            },
            panel_density="comfortable",
            surface_copy_variant="default",
        )

        self.assertTrue(any("PAGE SEGMENT" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("Priority Segment" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("Role: Decision" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("Related homepage groups stay together in this segment" in call for call in fake_st.markdown_calls))

    def test_render_page_layout_renders_group_intro_when_group_changes(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "leader_summary": {"Trend Leader": "GiantChip-U"},
            "latest_alerts": [],
        }

        _render_page_layout(
            fake_st,
            payload,
            [
                {
                    "section_type": "content",
                    "section_key": "leader_summary",
                    "segment_key": "analysis_segment",
                    "segment_title": "Analysis Segment",
                    "segment_tone": "neutral",
                    "group_key": "followup_cluster",
                    "group_title": "Follow-up Cluster",
                    "group_tone": "neutral",
                },
                {
                    "section_type": "content",
                    "section_key": "latest_alerts",
                    "segment_key": "analysis_segment",
                    "segment_title": "Analysis Segment",
                    "segment_tone": "neutral",
                    "group_key": "followup_cluster",
                    "group_title": "Follow-up Cluster",
                    "group_tone": "neutral",
                },
            ],
            kpi_copy_variant="default",
            surface_copy_variant="default",
            content_variant_overrides={},
            panel_density="comfortable",
        )

        followup_group_calls = [call for call in fake_st.markdown_calls if "Follow-up Cluster" in call]
        self.assertEqual(1, len(followup_group_calls))

    def test_render_page_layout_renders_segment_intro_when_segment_changes(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "leader_summary": {"Trend Leader": "GiantChip-U"},
            "saved_batches": [],
        }

        _render_page_layout(
            fake_st,
            payload,
            [
                {
                    "section_type": "content",
                    "section_key": "leader_summary",
                    "segment_key": "analysis_segment",
                    "segment_title": "Analysis Segment",
                    "segment_tone": "neutral",
                    "group_key": "followup_cluster",
                    "group_title": "Follow-up Cluster",
                    "group_tone": "neutral",
                },
                {
                    "section_type": "content",
                    "section_key": "saved_batches",
                    "segment_key": "archive_segment",
                    "segment_title": "Archive Segment",
                    "segment_tone": "neutral",
                    "group_key": "archive_cluster",
                    "group_title": "Archive Cluster",
                    "group_tone": "neutral",
                },
            ],
            kpi_copy_variant="default",
            surface_copy_variant="default",
            content_variant_overrides={},
            panel_density="comfortable",
        )

        analysis_segment_calls = [call for call in fake_st.markdown_calls if "Analysis Segment" in call]
        archive_segment_calls = [call for call in fake_st.markdown_calls if "Archive Segment" in call]
        self.assertEqual(1, len(analysis_segment_calls))
        self.assertEqual(1, len(archive_segment_calls))

    def test_build_health_summary_view_model_uses_valid_variant_copy(self) -> None:
        spec = build_content_section_specs()["stock_pool_health"]
        value = {
            "status": "valid",
            "risk_level": "clean",
            "risk_text": "No blocking or warning signals were found.",
            "structure_summary": "\u5f53\u524d\u76d1\u63a7\u6c60\u504f\u5411\u6750\u6599\u94fe\uff0ccore\u6c60\u5360\u6bd4\u7ea6 1/3\u3002",
            "record_count": 43,
            "source_path": "app/universe/stock_pool.json",
            "duplicate_codes": [],
            "unknown_sectors": [],
            "unknown_chain_groups": [],
            "unknown_markets": [],
            "unknown_pool_types": [],
            "unknown_sector_suggestions": {},
            "unknown_chain_group_suggestions": {},
            "unknown_market_suggestions": {},
            "unknown_pool_type_suggestions": {},
            "sector_counts": {"\u534a\u5bfc\u4f53\u6750\u6599": 2, "\u534a\u5bfc\u4f53\u6c14\u4f53": 1},
            "chain_group_counts": {"\u6750\u6599": 2, "\u6c14\u4f53": 1},
            "pool_type_counts": {"core": 2, "extended": 1},
            "priority_counts": {1: 2, 2: 1},
            "comparison_snapshot_path": "data/stock_pool_health_snapshot.json",
            "comparison_baseline_exists": False,
            "comparison_baseline_saved_at": "",
            "comparison_tags": ["Awaiting baseline"],
            "comparison_tag_labels": ["Awaiting baseline"],
            "comparison_tag_groups": [
                {
                    "group_key": "baseline_state",
                    "group_label": "\u57fa\u7ebf\u72b6\u6001",
                    "tag_labels": ["Awaiting baseline"],
                    "summary": "\u57fa\u7ebf\u72b6\u6001\uff1aAwaiting baseline",
                }
            ],
            "comparison_highlight_summary": "?????????????????????",
            "comparison_summary": "?????????????????????????",
            "comparison_change_rows": [],
            "hint_count": 0,
            "health_hints": [],
        }

        view_model = _build_health_summary_view_model(value, spec)

        self.assertEqual("success", view_model["tone"])
        self.assertEqual("Healthy | CLEAN", view_model["badge_text"])
        self.assertEqual("CLEAN", view_model["risk_label"])
        self.assertEqual("No blocking or warning signals were found.", view_model["risk_text"])
        self.assertEqual(
            "\u5f53\u524d\u76d1\u63a7\u6c60\u504f\u5411\u6750\u6599\u94fe\uff0ccore\u6c60\u5360\u6bd4\u7ea6 1/3\u3002",
            view_model["structure_summary"],
        )
        self.assertEqual(3, len(view_model["summary_metrics"]))
        self.assertEqual("Tracked Stocks", view_model["summary_metrics"][0]["label"])
        self.assertEqual(43, view_model["summary_metrics"][0]["value"])
        self.assertEqual("count", view_model["summary_metrics"][0]["format_key"])
        self.assertEqual("meta_grid", view_model["info_blocks"][0]["block_type"])
        self.assertEqual("grouped_text_sections", view_model["info_blocks"][1]["block_type"])
        self.assertIn("Risk Level: CLEAN", view_model["info_blocks"][0]["content"][0])
        self.assertIn("Registered Sectors: 0", view_model["info_blocks"][0]["content"][2])
        self.assertEqual("Duplicate Codes:", view_model["info_blocks"][1]["content"][0]["title"])
        self.assertEqual(["- none"], view_model["info_blocks"][1]["content"][0]["rows"])
        self.assertEqual("Structure Counts:", view_model["info_blocks"][1]["content"][3]["title"])
        self.assertIn("Top Sectors:", view_model["info_blocks"][1]["content"][3]["rows"][0])
        self.assertIn("Top Chain Groups:", view_model["info_blocks"][1]["content"][3]["rows"][1])
        self.assertIn("Top Pool Types:", view_model["info_blocks"][1]["content"][3]["rows"][2])
        self.assertIn("Sector Counts:", view_model["info_blocks"][1]["content"][3]["rows"][3])
        self.assertEqual("Structure Comparison:", view_model["info_blocks"][1]["content"][4]["title"])
        self.assertIn("Awaiting baseline", view_model["info_blocks"][1]["content"][4]["rows"][0])
        self.assertIn("Change Groups:", view_model["info_blocks"][1]["content"][4]["rows"][1])
        self.assertIn("Change Highlight:", view_model["info_blocks"][1]["content"][4]["rows"][2])
        self.assertIn("Comparison Summary:", view_model["info_blocks"][1]["content"][4]["rows"][3])
        self.assertIn("Snapshot Path:", view_model["info_blocks"][1]["content"][4]["rows"][4])

    def test_build_health_summary_view_model_uses_invalid_variant_copy(self) -> None:
        spec = build_content_section_specs()["stock_pool_health"]
        value = {
            "status": "invalid",
            "risk_level": "blocking",
            "risk_text": "Duplicate stock codes need to be fixed before monitoring.",
            "structure_summary": "\u5f53\u524d\u76d1\u63a7\u6c60\u504f\u5411\u6750\u6599\u94fe\uff0ccore\u6c60\u5360\u6bd4\u7ea6 7/8\u3002",
            "record_count": 10,
            "source_path": "custom.json",
            "duplicate_codes": ["600001"],
            "unknown_sectors": ["\u534a\u5bfc\u4f53\u6750\u79d1"],
            "unknown_chain_groups": ["\u6750\u79d1"],
            "unknown_markets": ["\u6caaB"],
            "unknown_pool_types": ["cores"],
            "unknown_sector_suggestions": {"\u534a\u5bfc\u4f53\u6750\u79d1": "\u534a\u5bfc\u4f53\u6750\u6599"},
            "unknown_chain_group_suggestions": {"\u6750\u79d1": "\u6750\u6599"},
            "unknown_market_suggestions": {"\u6caaB": "\u6caaA"},
            "unknown_pool_type_suggestions": {"cores": "core"},
            "sector_counts": {"\u534a\u5bfc\u4f53\u6750\u6599": 8},
            "chain_group_counts": {"\u6750\u6599": 8},
            "pool_type_counts": {"core": 8},
            "priority_counts": {2: 8},
            "comparison_snapshot_path": "data/stock_pool_health_snapshot.json",
            "comparison_baseline_exists": True,
            "comparison_baseline_saved_at": "2026-06-30 15:20:00",
            "comparison_tags": ["Materials Exposure Up", "Priority-1 Focus Down"],
            "comparison_tag_labels": ["\u6750\u6599\u94fe\u52a0\u4ed3", "\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d"],
            "comparison_tag_groups": [
                {
                    "group_key": "chain_exposure",
                    "group_label": "\u4ea7\u4e1a\u94fe\u66b4\u9732",
                    "tag_labels": ["\u6750\u6599\u94fe\u52a0\u4ed3"],
                    "summary": "\u4ea7\u4e1a\u94fe\u66b4\u9732\uff1a\u6750\u6599\u94fe\u52a0\u4ed3",
                },
                {
                    "group_key": "priority_focus",
                    "group_label": "\u4f18\u5148\u7ea7\u7126\u70b9",
                    "tag_labels": ["\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d"],
                    "summary": "\u4f18\u5148\u7ea7\u7126\u70b9\uff1a\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d",
                },
            ],
            "comparison_highlight_summary": "\u91cd\u70b9\u53d8\u5316\uff1a\u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599\u589e\u52a0 (+2)\uff1b\u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599\u589e\u52a0 (+2)\u3002",
            "comparison_summary": "\u4e0e 2026-06-30 15:20:00 \u7684\u57fa\u7ebf\u76f8\u6bd4\uff0c\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316\u3002",
            "comparison_change_rows": [
                "- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +2",
                "- \u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599: +2",
            ],
            "hint_count": 2,
            "health_hints": ["No priority-1 stocks are configured."],
        }

        view_model = _build_health_summary_view_model(value, spec)

        self.assertEqual("error", view_model["tone"])
        self.assertEqual("Needs Attention | BLOCKING", view_model["badge_text"])
        self.assertEqual("BLOCKING", view_model["risk_label"])
        self.assertEqual(2, view_model["summary_metrics"][1]["value"])
        self.assertEqual(1, view_model["summary_metrics"][2]["value"])
        self.assertEqual("Validation Issues:", view_model["info_blocks"][1]["content"][1]["title"])
        self.assertIn("600001", view_model["info_blocks"][1]["content"][0]["rows"][0])
        self.assertIn("Unknown Sectors:", view_model["info_blocks"][1]["content"][1]["rows"][0])
        self.assertIn("Unknown Chain Groups:", view_model["info_blocks"][1]["content"][1]["rows"][1])
        self.assertIn("Unknown Markets:", view_model["info_blocks"][1]["content"][1]["rows"][2])
        self.assertIn("cores", view_model["info_blocks"][1]["content"][1]["rows"][3])
        self.assertIn("sector:", view_model["info_blocks"][1]["content"][2]["rows"][0])
        self.assertIn("->", view_model["info_blocks"][1]["content"][2]["rows"][0])
        self.assertEqual("Structure Counts:", view_model["info_blocks"][1]["content"][3]["title"])
        self.assertIn("Top Chain Groups:", view_model["info_blocks"][1]["content"][3]["rows"][1])
        self.assertIn("Top Pool Types:", view_model["info_blocks"][1]["content"][3]["rows"][2])
        self.assertIn("Chain-group Counts:", view_model["info_blocks"][1]["content"][3]["rows"][4])
        self.assertEqual("Structure Comparison:", view_model["info_blocks"][1]["content"][4]["title"])
        self.assertIn("\u6750\u6599\u94fe\u52a0\u4ed3", view_model["info_blocks"][1]["content"][4]["rows"][0])
        self.assertIn("Change Groups:", view_model["info_blocks"][1]["content"][4]["rows"][1])
        self.assertIn("Change Highlight:", view_model["info_blocks"][1]["content"][4]["rows"][2])
        self.assertIn("Baseline Saved At:", view_model["info_blocks"][1]["content"][4]["rows"][5])
        self.assertIn("- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +2", view_model["info_blocks"][1]["content"][4]["rows"][6])
        self.assertIn("No priority-1 stocks are configured.", view_model["info_blocks"][1]["content"][5]["rows"][0])
        self.assertEqual("Suggested Matches:", view_model["info_blocks"][1]["content"][2]["title"])

    def test_resolve_spec_copy_variant_merges_health_business_cn_copy(self) -> None:
        spec = build_content_section_specs()["stock_pool_health"]
        spec["copy_variant"] = "business_cn"

        resolved_spec = _resolve_spec_copy_variant(
            spec,
            merge_keys=("labels", "status_variants", "risk_variants"),
        )

        self.assertEqual("\u98ce\u9669\u7b49\u7ea7", resolved_spec["labels"]["risk_level"])
        self.assertEqual("\u5065\u5eb7\u53ef\u7528", resolved_spec["status_variants"]["valid"]["status_label"])
        self.assertEqual("\u963b\u585e", resolved_spec["risk_variants"]["blocking"]["label"])

    def test_build_health_summary_view_model_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["stock_pool_health"]
        spec["copy_variant"] = "business_cn"
        value = {
            "status": "valid",
            "risk_level": "clean",
            "risk_text": "No blocking or warning signals were found.",
            "structure_summary": "Current pool remains material-chain heavy.",
            "record_count": 12,
            "source_path": "app/universe/stock_pool.json",
            "duplicate_codes": [],
            "unknown_sectors": [],
            "unknown_chain_groups": [],
            "unknown_markets": [],
            "unknown_pool_types": [],
            "unknown_sector_suggestions": {},
            "unknown_chain_group_suggestions": {},
            "unknown_market_suggestions": {},
            "unknown_pool_type_suggestions": {},
            "sector_counts": {},
            "chain_group_counts": {},
            "pool_type_counts": {},
            "priority_counts": {},
            "comparison_snapshot_path": "data/stock_pool_health_snapshot.json",
            "comparison_baseline_exists": False,
            "comparison_baseline_saved_at": "",
            "comparison_tags": [],
            "comparison_tag_labels": [],
            "comparison_tag_groups": [],
            "comparison_highlight_summary": "",
            "comparison_summary": "",
            "comparison_change_rows": [],
            "hint_count": 0,
            "health_hints": [],
        }

        view_model = _build_health_summary_view_model(value, spec)

        self.assertEqual("\u5065\u5eb7\u53ef\u7528 | \u6b63\u5e38", view_model["badge_text"])
        self.assertEqual("\u6b63\u5e38", view_model["risk_label"])
        self.assertEqual("\u76d1\u63a7\u80a1\u7968\u6570", view_model["summary_metrics"][0]["label"])
        self.assertEqual(
            "\u72b6\u6001\uff1a\u5065\u5eb7\u53ef\u7528\uff08valid\uff09 | \u98ce\u9669\uff1a\u6b63\u5e38",
            view_model["status_line"],
        )
        self.assertIn("\u98ce\u9669\u7b49\u7ea7: \u6b63\u5e38", view_model["info_blocks"][0]["content"][0])
        self.assertEqual("\u91cd\u590d\u4ee3\u7801:", view_model["info_blocks"][1]["content"][0]["title"])

    def test_build_health_meta_rows_uses_replaceable_meta_specs(self) -> None:
        meta_rows = _build_health_meta_rows(
            {
                "source_path": "app/universe/stock_pool.json",
                "registered_sectors": ["A", "B"],
            },
            {
                "risk_level": "Risk Level",
                "source_path": "Source",
                "registered_sectors": "Registered Sectors",
            },
            meta_specs=[
                {
                    "value_key": "risk_label",
                    "label_key": "risk_level",
                    "fallback_label": "Risk Level",
                },
                {
                    "value_key": "source_path",
                    "label_key": "source_path",
                    "fallback_label": "Source",
                },
                {
                    "value_key": "registered_sectors",
                    "label_key": "registered_sectors",
                    "fallback_label": "Registered Sectors",
                    "value_mode": "count",
                },
            ],
            derived_values={
                "risk_label": "CLEAN",
            },
        )

        self.assertEqual("Risk Level: CLEAN", meta_rows[0])
        self.assertEqual("Source: app/universe/stock_pool.json", meta_rows[1])
        self.assertEqual("Registered Sectors: 2", meta_rows[2])

    def test_build_health_info_blocks_uses_health_block_specs(self) -> None:
        spec = build_content_section_specs()["stock_pool_health"]

        info_blocks = _build_health_info_blocks(
            ["Risk Level: CLEAN", "Source: app/universe/stock_pool.json"],
            [{"title": "Validation Issues:", "rows": ["- Unknown Sectors: none"]}],
            info_block_specs=list(spec["health_info_blocks"]),
        )

        self.assertEqual("meta_grid", info_blocks[0]["block_type"])
        self.assertEqual("grouped_text_sections", info_blocks[1]["block_type"])
        self.assertEqual("Risk Level: CLEAN", info_blocks[0]["content"][0])
        self.assertEqual("Validation Issues:", info_blocks[1]["content"][0]["title"])

    def test_build_health_detail_sections_uses_group_titles_and_rows(self) -> None:
        detail_sections = _build_health_detail_sections(
            {
                "detail_sections": [
                    {"title_key": "duplicate_title", "rows_key": "duplicate_rows"},
                    {"title_key": "hint_title", "rows_key": "hint_rows"},
                ]
            },
            {
                "duplicate_rows": ["- none"],
                "hint_rows": ["- No structural drift hints."],
            },
            title_values={
                "duplicate_title": "Duplicate Codes:",
                "hint_title": "Health Hints:",
            },
        )

        self.assertEqual("Duplicate Codes:", detail_sections[0]["title"])
        self.assertEqual(["- none"], detail_sections[0]["rows"])
        self.assertEqual("Health Hints:", detail_sections[1]["title"])

    def test_build_health_row_sources_uses_none_text_for_empty_suggestions(self) -> None:
        row_sources = _build_health_row_sources(
            duplicate_text="none",
            issue_rows=["- Unknown Sectors: none"],
            suggested_matches=[],
            structure_rows=["- Sector Counts: A: 1"],
            comparison_rows=["- Comparison Summary: No previous snapshot."],
            hint_rows=["- No structural drift hints."],
            none_text="none",
        )

        self.assertEqual(["- none"], row_sources["duplicate_rows"])
        self.assertEqual(["- Unknown Sectors: none"], row_sources["issue_rows"])
        self.assertEqual(["- none"], row_sources["suggestion_rows"])
        self.assertEqual(["- Sector Counts: A: 1"], row_sources["structure_rows"])
        self.assertEqual(["- Comparison Summary: No previous snapshot."], row_sources["comparison_rows"])
        self.assertEqual(["- No structural drift hints."], row_sources["hint_rows"])

    def test_build_count_summary_rows_formats_structure_counts(self) -> None:
        rows = _build_count_summary_rows(
            {
                "sector_counts": {"\u534a\u5bfc\u4f53\u6750\u6599": 2, "\u534a\u5bfc\u4f53\u6c14\u4f53": 1},
                "chain_group_counts": {"\u6750\u6599": 2, "\u6c14\u4f53": 1},
                "pool_type_counts": {"core": 2, "extended": 1},
                "priority_counts": {1: 2, 2: 1},
            },
            {
                "top_sector_counts": "Top Sectors",
                "top_chain_group_counts": "Top Chain Groups",
                "top_pool_type_counts": "Top Pool Types",
                "sector_counts": "Sector Counts",
                "chain_group_counts": "Chain-group Counts",
                "pool_type_counts": "Pool-type Counts",
                "priority_counts": "Priority Counts",
            },
        )

        self.assertEqual(
            [
                "- Top Sectors: \u534a\u5bfc\u4f53\u6750\u6599: 2, \u534a\u5bfc\u4f53\u6c14\u4f53: 1",
                "- Top Chain Groups: \u6750\u6599: 2, \u6c14\u4f53: 1",
                "- Top Pool Types: core: 2, extended: 1",
                "- Sector Counts: \u534a\u5bfc\u4f53\u6750\u6599: 2, \u534a\u5bfc\u4f53\u6c14\u4f53: 1",
                "- Chain-group Counts: \u6750\u6599: 2, \u6c14\u4f53: 1",
                "- Pool-type Counts: core: 2, extended: 1",
                "- Priority Counts: 1: 2, 2: 1",
            ],
            rows,
        )

    def test_build_top_count_row_sorts_by_count_then_name(self) -> None:
        row = _build_top_count_row(
            {"B": 2, "A": 2, "C": 1, "D": 5},
            label="Top Sectors",
        )

        self.assertEqual("- Top Sectors: D: 5, A: 2, B: 2", row)

    def test_build_health_status_copy_uses_variant_and_risk_labels(self) -> None:
        status_copy = _build_health_status_copy(
            status="invalid",
            status_label="Needs Attention",
            risk_label="BLOCKING",
        )

        self.assertEqual(
            {
                "status_line": "Status: Needs Attention (invalid) | Risk: BLOCKING",
                "badge_text": "Needs Attention | BLOCKING",
            },
            status_copy,
        )

    def test_build_health_section_titles_prefers_group_titles_then_labels(self) -> None:
        title_values = _build_health_section_titles(
            {
                "duplicate_title": "Duplicate Codes",
                "suggested_matches": "Suggested Matches",
                "health_hints": "Health Hints",
            },
            {
                "duplicate_title": "Duplicate Registry",
                "issue_title": "Validation Issues",
            },
        )

        self.assertEqual("Duplicate Registry:", title_values["duplicate_title"])
        self.assertEqual("Validation Issues:", title_values["issue_title"])
        self.assertEqual("Suggested Matches:", title_values["suggestion_title"])
        self.assertEqual("Structure Comparison:", title_values["comparison_title"])
        self.assertEqual("Health Hints:", title_values["hint_title"])

    def test_build_health_comparison_rows_formats_snapshot_and_change_rows(self) -> None:
        rows = _build_health_comparison_rows(
            {
                "comparison_tags": ["Materials Exposure Up", "Priority-1 Focus Down"],
                "comparison_tag_labels": ["\u6750\u6599\u94fe\u52a0\u4ed3", "\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d"],
                "comparison_tag_groups": [
                    {
                        "group_key": "chain_exposure",
                        "group_label": "\u4ea7\u4e1a\u94fe\u66b4\u9732",
                        "tag_labels": ["\u6750\u6599\u94fe\u52a0\u4ed3"],
                        "summary": "\u4ea7\u4e1a\u94fe\u66b4\u9732\uff1a\u6750\u6599\u94fe\u52a0\u4ed3",
                    },
                    {
                        "group_key": "priority_focus",
                        "group_label": "\u4f18\u5148\u7ea7\u7126\u70b9",
                        "tag_labels": ["\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d"],
                        "summary": "\u4f18\u5148\u7ea7\u7126\u70b9\uff1a\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d",
                    },
                ],
                "comparison_snapshot_path": "data/stock_pool_health_snapshot.json",
                "comparison_baseline_saved_at": "2026-06-30 15:20:00",
                "comparison_highlight_summary": "\u91cd\u70b9\u53d8\u5316\uff1a\u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599\u589e\u52a0 (+2)\uff1b\u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599\u589e\u52a0 (+2)\u3002",
                "comparison_summary": "\u4e0e 2026-06-30 15:20:00 \u7684\u57fa\u7ebf\u76f8\u6bd4\uff0c\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316\u3002",
                "comparison_change_rows": [
                    "- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +2",
                    "- \u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599: +2",
                ],
            },
            {
                "comparison_tags": "Change Tags",
                "comparison_tag_groups": "Change Groups",
                "comparison_highlight_summary": "Change Highlight",
                "comparison_summary": "Comparison Summary",
                "comparison_snapshot_path": "Snapshot Path",
                "comparison_baseline_saved_at": "Baseline Saved At",
            },
        )

        self.assertEqual(
            [
                "- Change Tags: \u6750\u6599\u94fe\u52a0\u4ed3, \u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d",
                "- Change Groups: \u4ea7\u4e1a\u94fe\u66b4\u9732\uff1a\u6750\u6599\u94fe\u52a0\u4ed3 | \u4f18\u5148\u7ea7\u7126\u70b9\uff1a\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d",
                "- Change Highlight: \u91cd\u70b9\u53d8\u5316\uff1a\u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599\u589e\u52a0 (+2)\uff1b\u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599\u589e\u52a0 (+2)\u3002",
                "- Comparison Summary: \u4e0e 2026-06-30 15:20:00 \u7684\u57fa\u7ebf\u76f8\u6bd4\uff0c\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316\u3002",
                "- Snapshot Path: data/stock_pool_health_snapshot.json",
                "- Baseline Saved At: 2026-06-30 15:20:00",
                "- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +2",
                "- \u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599: +2",
            ],
            rows,
        )

    def test_build_summary_metrics_uses_labels_and_resolver_values(self) -> None:
        summary_metrics = _build_summary_metrics(
            {
                "summary_metrics": [
                    {
                        "value_key": "record_count",
                        "label_key": "tracked_stocks",
                        "format_key": "count",
                    },
                    {
                        "value_key": "duplicate_count",
                        "label_key": "duplicate_codes",
                        "format_key": "count",
                    },
                ]
            },
            {
                "tracked_stocks": "Tracked Stocks",
                "duplicate_codes": "Duplicate Codes",
            },
            value_resolver=lambda value_key: {"record_count": 43, "duplicate_count": 2}.get(
                value_key,
                0,
            ),
        )

        self.assertEqual("Tracked Stocks", summary_metrics[0]["label"])
        self.assertEqual(43, summary_metrics[0]["value"])
        self.assertEqual("count", summary_metrics[0]["format_key"])
        self.assertEqual("Duplicate Codes", summary_metrics[1]["label"])
        self.assertEqual(2, summary_metrics[1]["value"])

    def test_build_grouped_count_badge_uses_count_and_suffix(self) -> None:
        self.assertEqual(
            "2 alert row(s)",
            _build_grouped_count_badge(2, "alert row(s)"),
        )

    def test_build_grouped_text_section_view_models_uses_title_map_and_rows(self) -> None:
        section_view_models = _build_grouped_text_section_view_models(
            [
                {
                    "title_key": "issue_title",
                    "rows_key": "issue_rows",
                },
                {
                    "title": "Fallback Title:",
                    "rows_key": "hint_rows",
                },
            ],
            {
                "issue_rows": ["- Unknown Sectors: none"],
                "hint_rows": ["- No structural drift hints."],
            },
            title_values={
                "issue_title": "Validation Issues:",
            },
        )

        self.assertEqual("Validation Issues:", section_view_models[0]["title"])
        self.assertEqual(["- Unknown Sectors: none"], section_view_models[0]["rows"])
        self.assertEqual("Fallback Title:", section_view_models[1]["title"])

    def test_build_info_blocks_uses_block_specs_and_sources(self) -> None:
        info_blocks = _build_info_blocks(
            [
                {
                    "block_key": "meta_rows",
                    "block_type": "meta_grid",
                },
                {
                    "block_key": "detail_sections",
                    "block_type": "grouped_text_sections",
                },
            ],
            block_sources={
                "meta_rows": ["Risk Level: CLEAN"],
                "detail_sections": [{"title": "Health Hints:", "rows": ["- none"]}],
            },
        )

        self.assertEqual("meta_rows", info_blocks[0]["block_key"])
        self.assertEqual("meta_grid", info_blocks[0]["block_type"])
        self.assertEqual(["Risk Level: CLEAN"], info_blocks[0]["content"])
        self.assertEqual("grouped_text_sections", info_blocks[1]["block_type"])

    def test_build_grouped_summary_info_blocks_from_sections_uses_spec_labels(self) -> None:
        spec = build_content_section_specs()["leader_summary"]
        labels = dict(spec.get("labels", {}))
        info_blocks = _build_grouped_summary_info_blocks_from_sections(
            [
                {
                    "title": f"{labels.get('detail_section_title', 'Details')}:",
                    "rows": ["- Trend Leader: GiantChip-U"],
                }
            ],
            spec,
        )

        self.assertEqual("grouped_text_sections", info_blocks[0]["block_type"])
        self.assertEqual("Leader Details:", info_blocks[0]["content"][0]["title"])
        self.assertEqual(["- Trend Leader: GiantChip-U"], info_blocks[0]["content"][0]["rows"])

    def test_build_grouped_summary_sections_from_items_uses_section_title_metadata(self) -> None:
        spec = build_content_section_specs()["latest_alerts"]
        detail_sections = _build_grouped_summary_sections_from_items(
            [
                {
                    "timestamp": "2026-06-20 14:45:00",
                    "alert_type": "price_spike",
                    "message": "Alert text",
                }
            ],
            spec,
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("Alert Details:", detail_sections[0]["title"])
        self.assertIn("2026-06-20 14:45 | price_spike", detail_sections[0]["rows"][0])

    def test_build_grouped_summary_rows_from_items_uses_detail_layout_formats(self) -> None:
        spec = build_content_section_specs()["saved_batches"]

        detail_rows = _build_grouped_summary_rows_from_items(
            [{"timestamp": "2026-06-20 14:45:00"}],
            spec=spec,
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual(["- 2026-06-20 14:45"], detail_rows)

    def test_build_grouped_summary_detail_payload_keeps_compatibility_and_block_shapes_aligned(self) -> None:
        spec = build_content_section_specs()["latest_alerts"]
        detail_payload = _build_grouped_summary_detail_payload(
            [
                {
                    "timestamp": "2026-06-20 14:45:00",
                    "alert_type": "price_spike",
                    "message": "Alert text",
                }
            ],
            spec,
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("grouped_text_sections", detail_payload["info_blocks"][0]["block_type"])
        derived_detail_rows = _resolve_compatibility_rows_from_info_blocks(
            detail_payload["info_blocks"]
        )
        self.assertIn("2026-06-20 14:45 | price_spike", derived_detail_rows[0])
        self.assertEqual(
            list(derived_detail_rows),
            detail_payload["info_blocks"][0]["content"][0]["rows"],
        )

    def test_resolve_grouped_summary_render_blocks_prefers_info_blocks(self) -> None:
        spec = build_content_section_specs()["leader_summary"]
        resolved_blocks = _resolve_grouped_summary_render_blocks(
            {
                "info_blocks": [
                    {
                        "block_key": "detail_sections",
                        "block_type": "grouped_text_sections",
                        "content": [{"title": "Custom Details:", "rows": ["- row"]}],
                    }
                ],
                "detail_rows": ["- legacy row"],
            },
            spec,
        )

        self.assertEqual("Custom Details:", resolved_blocks[0]["content"][0]["title"])
        self.assertEqual(["- row"], resolved_blocks[0]["content"][0]["rows"])

    def test_build_legacy_grouped_summary_info_blocks_uses_detail_section_label(self) -> None:
        spec = build_content_section_specs()["latest_alerts"]

        resolved_blocks = _build_legacy_grouped_summary_info_blocks(
            ["- 2026-06-20 14:45 | price_spike | Alert text"],
            spec,
        )

        self.assertEqual("grouped_text_sections", resolved_blocks[0]["block_type"])
        self.assertEqual("Alert Details:", resolved_blocks[0]["content"][0]["title"])
        self.assertEqual(
            ["- 2026-06-20 14:45 | price_spike | Alert text"],
            resolved_blocks[0]["content"][0]["rows"],
        )

    def test_resolve_legacy_grouped_summary_rows_reads_legacy_detail_rows_only(self) -> None:
        legacy_rows = _resolve_legacy_grouped_summary_rows(
            {
                "info_blocks": [
                    {
                        "block_key": "detail_sections",
                        "block_type": "grouped_text_sections",
                        "content": [{"title": "Custom Details:", "rows": ["- modern row"]}],
                    }
                ],
                "detail_rows": ["- legacy row"],
            }
        )

        self.assertEqual(["- legacy row"], legacy_rows)

    def test_resolve_grouped_summary_render_blocks_falls_back_to_compatibility_rows(self) -> None:
        spec = build_content_section_specs()["latest_alerts"]
        resolved_blocks = _resolve_grouped_summary_render_blocks(
            {
                "detail_rows": ["- 2026-06-20 14:45 | price_spike | Alert text"],
            },
            spec,
        )

        self.assertEqual("grouped_text_sections", resolved_blocks[0]["block_type"])
        self.assertEqual("Alert Details:", resolved_blocks[0]["content"][0]["title"])
        self.assertEqual(
            ["- 2026-06-20 14:45 | price_spike | Alert text"],
            resolved_blocks[0]["content"][0]["rows"],
        )

    def test_resolve_compatibility_rows_from_info_blocks_flattens_grouped_sections(self) -> None:
        detail_rows = _resolve_compatibility_rows_from_info_blocks(
            [
                {
                    "block_key": "detail_sections",
                    "block_type": "grouped_text_sections",
                    "content": [
                        {
                            "title": "Leader Details:",
                            "rows": ["- Trend Leader: GiantChip-U"],
                        }
                    ],
                }
            ]
        )

        self.assertEqual(["- Trend Leader: GiantChip-U"], detail_rows)

    def test_render_grouped_text_sections_writes_titles_and_rows(self) -> None:
        fake_st = _FakeStreamlit()

        _render_grouped_text_sections(
            fake_st,
            [
                {
                    "title": "Validation Issues:",
                    "rows": ["- Unknown Sectors: none"],
                },
                {
                    "title": "Health Hints:",
                    "rows": ["- No structural drift hints."],
                },
            ],
        )

        self.assertEqual("Validation Issues:", fake_st.write_calls[0])
        self.assertEqual("- Unknown Sectors: none", fake_st.write_calls[1])
        self.assertEqual("Health Hints:", fake_st.write_calls[2])
        self.assertEqual("- No structural drift hints.", fake_st.write_calls[3])

    def test_render_grouped_text_sections_can_highlight_first_group_title(self) -> None:
        fake_st = _FakeStreamlit()

        _render_grouped_text_sections(
            fake_st,
            [
                {
                    "title": "核心摘要:",
                    "rows": ["- 先看风险扩散，再看主线强化。"],
                },
                {
                    "title": "阅读顺序:",
                    "rows": ["- 1. 先看风险优先名单"],
                },
            ],
            first_group_tone="accent",
            surface_copy_variant="business_cn",
        )

        self.assertTrue(any("dashboard-panel--accent" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("核心摘要:" in call for call in fake_st.markdown_calls))
        self.assertIn("- 先看风险扩散，再看主线强化。", fake_st.write_calls)
        self.assertIn("阅读顺序:", fake_st.write_calls)

    def test_render_grouped_text_sections_can_add_anchor_to_first_group(self) -> None:
        fake_st = _FakeStreamlit()

        _render_grouped_text_sections(
            fake_st,
            [
                {
                    "title": "核心摘要:",
                    "rows": ["- 先看风险扩散。"],
                },
                {
                    "title": "阅读顺序:",
                    "rows": ["- 1. 先看风险优先名单"],
                },
            ],
            first_group_anchor_id="section-today-priority-summary-primary",
        )

        self.assertTrue(
            any('id="section-today-priority-summary-primary"' in call for call in fake_st.markdown_calls)
        )

    def test_render_info_blocks_renders_meta_grid_and_grouped_sections(self) -> None:
        fake_st = _FakeStreamlit()

        _render_info_blocks(
            fake_st,
            [
                {
                    "block_key": "meta_rows",
                    "block_type": "meta_grid",
                    "content": ["Risk Level: CLEAN", "Source: app/universe/stock_pool.json"],
                },
                {
                    "block_key": "detail_sections",
                    "block_type": "grouped_text_sections",
                    "content": [{"title": "Health Hints:", "rows": ["- none"]}],
                },
            ],
        )

        self.assertIn("Risk Level: CLEAN", fake_st.write_calls)
        self.assertIn("Source: app/universe/stock_pool.json", fake_st.write_calls)
        self.assertIn("Health Hints:", fake_st.write_calls)
        self.assertIn("- none", fake_st.write_calls)

    def test_render_info_blocks_can_apply_first_group_highlight(self) -> None:
        fake_st = _FakeStreamlit()

        _render_info_blocks(
            fake_st,
            [
                {
                    "block_key": "detail_sections",
                    "block_type": "grouped_text_sections",
                    "content": [{"title": "核心摘要:", "rows": ["- 先看风险扩散。"]}],
                },
            ],
            first_group_tone="accent",
            surface_copy_variant="business_cn",
        )

        self.assertTrue(any("dashboard-panel--accent" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("核心摘要:" in call for call in fake_st.markdown_calls))

    def test_build_spotlight_summary_view_model_uses_sector_metrics(self) -> None:
        spec = build_content_section_specs()["strongest_sector"]
        value = {
            "sector": "Semi Materials",
            "avg_pct_chg": 6.9,
            "stock_count": 2,
        }

        view_model = _build_spotlight_summary_view_model(value, spec)

        self.assertEqual("accent", view_model["tone"])
        self.assertEqual("Semi Materials", view_model["badge_text"])
        self.assertEqual(2, len(view_model["summary_metrics"]))
        self.assertEqual("Avg Change", view_model["summary_metrics"][0]["label"])
        self.assertEqual(6.9, view_model["summary_metrics"][0]["value"])
        self.assertEqual("signed_percent_1", view_model["summary_metrics"][0]["format_key"])
        self.assertNotIn("detail_rows", view_model)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )
        self.assertIn("Semi Materials", compatibility_rows[0])
        self.assertIn("+6.9%", compatibility_rows[0])
        self.assertEqual("grouped_text_sections", view_model["info_blocks"][0]["block_type"])
        self.assertEqual("Sector Details:", view_model["info_blocks"][0]["content"][0]["title"])

    def test_build_spotlight_summary_view_model_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["strongest_sector"]
        spec["copy_variant"] = "business_cn"
        value = {
            "sector": "Semi Materials",
            "avg_pct_chg": 6.9,
            "stock_count": 2,
        }

        view_model = _build_spotlight_summary_view_model(value, spec)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )

        self.assertEqual("\u5e73\u5747\u6da8\u8dcc", view_model["summary_metrics"][0]["label"])
        self.assertEqual("\u677f\u5757\u660e\u7ec6:", view_model["info_blocks"][0]["content"][0]["title"])
        self.assertIn("\u9886\u6da8\u677f\u5757:Semi Materials", compatibility_rows[0])

    def test_build_leader_grouped_view_model_summarizes_leader_map(self) -> None:
        spec = build_content_section_specs()["leader_summary"]
        value = {
            "Trend Leader": "GiantChip-U",
            "Emotion Leader": "NorthGas",
        }

        view_model = _build_leader_grouped_view_model(value, spec)

        self.assertEqual("neutral", view_model["tone"])
        self.assertEqual("2 leader slot(s)", view_model["badge_text"])
        self.assertEqual(2, view_model["summary_metrics"][0]["value"])
        self.assertNotIn("detail_rows", view_model)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )
        self.assertIn(
            "Trend Leader: GiantChip-U",
            compatibility_rows[0],
        )
        self.assertEqual("Leader Details:", view_model["info_blocks"][0]["content"][0]["title"])

    def test_build_leader_grouped_view_model_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["leader_summary"]
        spec["copy_variant"] = "business_cn"
        value = {
            "Trend Leader": "GiantChip-U",
            "Emotion Leader": "NorthGas",
        }

        view_model = _build_leader_grouped_view_model(value, spec)

        self.assertEqual("2 \u4e2a\u9f99\u5934\u69fd\u4f4d", view_model["badge_text"])
        self.assertEqual("\u9f99\u5934\u69fd\u4f4d\u6570", view_model["summary_metrics"][0]["label"])
        self.assertEqual("\u9f99\u5934\u660e\u7ec6:", view_model["info_blocks"][0]["content"][0]["title"])

    def test_build_alerts_grouped_view_model_summarizes_latest_alerts(self) -> None:
        spec = build_content_section_specs()["latest_alerts"]
        value = [
            {
                "timestamp": "2026-06-20 14:45:00",
                "alert_type": "price_spike",
                "message": "GiantChip-U surged 8.6% intraday",
            },
            {
                "timestamp": "2026-06-20 14:45:00",
                "alert_type": "sector_move",
                "message": "Materials line is strengthening",
            },
        ]

        view_model = _build_alerts_grouped_view_model(value, spec)

        self.assertEqual("warning", view_model["tone"])
        self.assertEqual("2 alert row(s)", view_model["badge_text"])
        self.assertEqual(2, view_model["summary_metrics"][0]["value"])
        self.assertNotIn("detail_rows", view_model)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )
        self.assertIn("price_spike", compatibility_rows[0])
        self.assertIn(
            "2026-06-20 14:45 | price_spike",
            compatibility_rows[0],
        )
        self.assertEqual("Alert Details:", view_model["info_blocks"][0]["content"][0]["title"])

    def test_build_alerts_grouped_view_model_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["latest_alerts"]
        spec["copy_variant"] = "business_cn"
        value = [
            {
                "timestamp": "2026-06-20 14:45:00",
                "alert_type": "price_spike",
                "message": "GiantChip-U surged 8.6% intraday",
            },
            {
                "timestamp": "2026-06-20 14:45:00",
                "alert_type": "sector_move",
                "message": "Materials line is strengthening",
            },
        ]

        view_model = _build_alerts_grouped_view_model(value, spec)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )

        self.assertEqual("2 \u6761\u63d0\u9192", view_model["badge_text"])
        self.assertEqual("\u63d0\u9192\u6761\u6570", view_model["summary_metrics"][0]["label"])
        self.assertEqual("\u63d0\u9192\u660e\u7ec6:", view_model["info_blocks"][0]["content"][0]["title"])
        self.assertIn("2026-06-20 14:45 | price_spike", compatibility_rows[0])

    def test_resolve_spec_copy_variant_replaces_display_fields_for_business_cn(self) -> None:
        spec = build_content_section_specs()["strongest_sector"]
        spec["copy_variant"] = "business_cn"

        resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels", "display_fields"))

        self.assertEqual("\u677f\u5757", resolved_spec["display_fields"][0]["label"])
        self.assertEqual("\u9886\u6da8\u677f\u5757: ", resolved_spec["display_fields"][0]["prefix"])

    def test_build_batch_list_grouped_view_model_summarizes_saved_batches(self) -> None:
        spec = build_content_section_specs()["saved_batches"]
        value = ["2026-06-20 14:45:00", "2026-06-20 09:35:00"]

        view_model = _build_batch_list_grouped_view_model(value, spec)

        self.assertEqual("neutral", view_model["tone"])
        self.assertEqual("2 saved batch(es)", view_model["badge_text"])
        self.assertEqual(2, view_model["summary_metrics"][0]["value"])
        self.assertNotIn("detail_rows", view_model)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )
        self.assertIn("2026-06-20 14:45", compatibility_rows[0])
        self.assertNotIn(
            "2026-06-20 14:45:00",
            compatibility_rows[0],
        )
        self.assertEqual("Batch Details:", view_model["info_blocks"][0]["content"][0]["title"])

    def test_build_batch_list_grouped_view_model_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["saved_batches"]
        spec["copy_variant"] = "business_cn"
        value = ["2026-06-20 14:45:00", "2026-06-20 09:35:00"]

        view_model = _build_batch_list_grouped_view_model(value, spec)

        self.assertEqual("2 \u4e2a\u5df2\u4fdd\u5b58\u6279\u6b21", view_model["badge_text"])
        self.assertEqual("\u5df2\u4fdd\u5b58\u6279\u6b21\u6570", view_model["summary_metrics"][0]["label"])
        self.assertEqual("\u6279\u6b21\u660e\u7ec6:", view_model["info_blocks"][0]["content"][0]["title"])

    def test_resolve_spec_copy_variant_replaces_saved_batch_display_fields_for_business_cn(self) -> None:
        spec = build_content_section_specs()["saved_batches"]
        spec["copy_variant"] = "business_cn"

        resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels", "display_fields"))

        self.assertEqual("\u6279\u6b21\u65f6\u95f4", resolved_spec["display_fields"][0]["label"])

    def test_build_next_session_action_grouped_view_model_summarizes_strategy_tiers(self) -> None:
        spec = build_content_section_specs()["next_session_action"]
        value = {
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
            "core_count": 1,
            "candidate_count": 1,
            "avoid_count": 1,
        }

        view_model = _build_next_session_action_grouped_view_model(value, spec)

        self.assertEqual("accent", view_model["tone"])
        self.assertEqual(
            "3 action slot(s) | Core 1 / Candidate 1 / Avoid 1",
            view_model["badge_text"],
        )
        self.assertEqual(3, len(view_model["summary_metrics"]))
        self.assertEqual(1, view_model["summary_metrics"][0]["value"])
        self.assertEqual(
            "Weight Summary:",
            view_model["info_blocks"][0]["content"][0]["title"],
        )
        self.assertEqual(
            "Priority Core Watchlist (Score-ranked) (1):",
            view_model["info_blocks"][0]["content"][1]["title"],
        )
        self.assertEqual(
            "Secondary Candidate Watchlist (Score-ranked) (1):",
            view_model["info_blocks"][0]["content"][2]["title"],
        )
        self.assertEqual(
            "Risk Avoid List (Score-ranked) (1):",
            view_model["info_blocks"][0]["content"][3]["title"],
        )
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )
        self.assertIn("主线=3, 强势=3, 跟随=2, 流动性=1", compatibility_rows[0])
        self.assertIn("核心兜底=1, 候选确认=1, 规避兜底=1", compatibility_rows[0])
        self.assertTrue(any("- Core names: Alpha" in row for row in compatibility_rows))
        self.assertTrue(any("- Core focus: Stay with Materials leaders first." in row for row in compatibility_rows))
        self.assertTrue(any("- Candidate focus: Use Equipment as first confirmation." in row for row in compatibility_rows))
        self.assertTrue(any("- Avoid focus: Reduce fading strength names." in row for row in compatibility_rows))
        self.assertIn("- Avoid scores: Delta (-5)", compatibility_rows[-2])

    def test_build_next_session_action_section_rows_uses_replaceable_row_labels(self) -> None:
        rows = _build_next_session_action_section_rows(
            "Core",
            {
                "watchlist": ["Alpha"],
                "tags": {"Alpha": ["mainline"]},
                "scores": {"Alpha": 3},
                "reason": "stay with Materials first.",
            },
            labels={
                "names_row_label": "watchlist",
                "tags_row_label": "signals",
                "scores_row_label": "ranking",
                "focus_row_label": "strategy",
            },
        )

        self.assertEqual("- Core watchlist: Alpha", rows[0])
        self.assertEqual("- Core signals: Alpha (mainline)", rows[1])
        self.assertEqual("- Core ranking: Alpha (3)", rows[2])
        self.assertEqual("- Core strategy: Stay with Materials leaders first.", rows[3])

    def test_build_next_session_action_section_rows_uses_replaceable_focus_templates(self) -> None:
        rows = _build_next_session_action_section_rows(
            "Avoid",
            {
                "watchlist": ["Delta"],
                "tags": {"Delta": ["risk-alert", "fading-sector"]},
                "scores": {"Delta": -5},
                "reason": "reduce names tied to fading strength.",
            },
            labels={
                "focus_templates": {
                    "reduce_names_tied_to": "Trim {target} exposure first.",
                }
            },
        )

        self.assertEqual("- Avoid focus: Trim fading strength exposure first.", rows[3])

    def test_resolve_next_session_action_labels_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["next_session_action"]
        spec["copy_variant"] = "business_cn"

        labels = _resolve_next_session_action_labels(spec)

        self.assertEqual("\u6743\u91cd\u6458\u8981", labels["rule_section_title"])
        self.assertEqual("\u540d\u5355", labels["names_row_label"])
        self.assertEqual("\u5148\u76ef\u4f4f {target} \u9f99\u5934\u3002", labels["focus_templates"]["stay_with_first"])

    def test_build_next_session_action_grouped_view_model_uses_business_cn_variant(self) -> None:
        spec = build_content_section_specs()["next_session_action"]
        spec["copy_variant"] = "business_cn"
        value = {
            "rule_summary_lines": (
                "评分规则：主线=3, 强势=3, 跟随=2, 流动性=1",
            ),
            "core": {
                "watchlist": ["Alpha"],
                "tags": {"Alpha": ["mainline", "strength"]},
                "scores": {"Alpha": 6},
                "reason": "stay with Materials first.",
            },
            "candidate": {},
            "avoid": {},
            "core_count": 1,
            "candidate_count": 0,
            "avoid_count": 0,
        }

        view_model = _build_next_session_action_grouped_view_model(value, spec)
        compatibility_rows = _resolve_compatibility_rows_from_info_blocks(
            view_model["info_blocks"]
        )

        self.assertEqual(
            "\u5171 1 \u4e2a\u52a8\u4f5c\u69fd\u4f4d | \u6838\u5fc3 1 / \u5019\u9009 0 / \u56de\u907f 0",
            view_model["badge_text"],
        )
        self.assertEqual("\u6743\u91cd\u6458\u8981:", view_model["info_blocks"][0]["content"][0]["title"])
        self.assertEqual(
            "\u6838\u5fc3\u4f18\u5148\u89c2\u5bdf\u6c60\uff08\u6309\u5206\u6570\u6392\u5e8f\uff09 (1):",
            view_model["info_blocks"][0]["content"][1]["title"],
        )
        self.assertTrue(any("- Core \u540d\u5355: Alpha" in row for row in compatibility_rows))
        self.assertTrue(any("- Core \u64cd\u4f5c\u91cd\u70b9: \u5148\u76ef\u4f4f Materials \u9f99\u5934\u3002" in row for row in compatibility_rows))

    def test_build_grouped_section_header_markdown_uses_tone_and_badge_text(self) -> None:
        header = _build_grouped_section_header_markdown(
            {
                "tone": "warning",
                "badge_text": "2 alert row(s)",
            }
        )

        self.assertIn("WARNING", header)
        self.assertIn("2 alert row(s)", header)
        self.assertIn("dashboard-panel__title", header)

    def test_build_grouped_summary_card_markdown_uses_shared_style_spec(self) -> None:
        card_markdown = _build_grouped_summary_card_markdown(
            {
                "tone": "accent",
                "badge_text": "Semi Materials",
            },
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("ACCENT SUMMARY", card_markdown)
        self.assertIn("Semi Materials", card_markdown)
        self.assertIn("Metrics first, details below", card_markdown)

    def test_build_grouped_summary_card_markdown_uses_compact_supporting_copy(self) -> None:
        card_markdown = _build_grouped_summary_card_markdown(
            {
                "tone": "warning",
                "badge_text": "2 alert row(s)",
            },
            panel_density="compact",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("Metrics + details", card_markdown)

    def test_build_health_summary_card_markdown_uses_health_supporting_copy(self) -> None:
        card_markdown = _build_health_summary_card_markdown(
            {
                "tone": "success",
                "risk_level": "clean",
                "badge_text": "Healthy | valid",
            },
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("SUCCESS HEALTH", card_markdown)
        self.assertIn("Healthy | valid", card_markdown)
        self.assertIn("Pool is structurally ready for monitoring.", card_markdown)

    def test_build_chart_panel_markdown_uses_chart_supporting_copy(self) -> None:
        card_markdown = _build_chart_panel_markdown(
            {
                "tone": "accent",
                "title": "Sector Strength",
            },
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("ACCENT CHART", card_markdown)
        self.assertIn("Sector Strength", card_markdown)
        self.assertIn("= NEUTRAL DETAILS", card_markdown)
        self.assertIn("Data table and chart follow", card_markdown)

    def test_build_chart_panel_markdown_uses_compact_chart_supporting_copy(self) -> None:
        card_markdown = _build_chart_panel_markdown(
            {
                "tone": "accent",
                "title": "Sector Strength",
            },
            panel_density="compact",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("Chart + data table", card_markdown)

    def test_build_section_title_markdown_uses_shared_panel_wrapper(self) -> None:
        title_markdown = _build_section_title_markdown(
            "Leader Summary",
            tone="neutral",
        )

        self.assertIn("NEUTRAL SECTION", title_markdown)
        self.assertIn("Leader Summary", title_markdown)

    def test_build_section_title_markdown_uses_business_cn_section_label(self) -> None:
        title_markdown = _build_section_title_markdown(
            "Leader Summary",
            tone="neutral",
            style_spec=build_content_panel_style_spec("business_cn"),
        )

        self.assertIn("NEUTRAL \u677f\u5757", title_markdown)

    def test_build_health_status_markdown_uses_tone_and_status_line(self) -> None:
        status_markdown = _build_health_status_markdown(
            {
                "tone": "error",
                "status_line": "Status: Needs Attention (invalid)",
            },
            panel_density="comfortable",
        )

        self.assertIn("ERROR STATUS", status_markdown)
        self.assertIn("Needs Attention", status_markdown)

    def test_build_health_status_markdown_uses_business_cn_status_label(self) -> None:
        status_markdown = _build_health_status_markdown(
            {
                "tone": "error",
                "status_line": "\u72b6\u6001\uff1a\u9700\u8981\u5904\u7406",
            },
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec("business_cn"),
        )

        self.assertIn("ERROR \u72b6\u6001", status_markdown)

    def test_build_health_readiness_markdown_uses_risk_label_and_text(self) -> None:
        readiness_markdown = _build_health_readiness_markdown(
            {
                "tone": "warning",
                "risk_level": "warning",
                "risk_label": "WARNING",
                "risk_text": "Unknown registry values were found and should be checked.",
                "structure_summary": "\u5f53\u524d\u76d1\u63a7\u6c60\u504f\u5411\u6750\u6599\u94fe\uff0ccore\u6c60\u5360\u6bd4\u7ea6 1/10\u3002",
            },
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("WARNING READINESS", readiness_markdown)
        self.assertIn("WARNING | Unknown registry values were found", readiness_markdown)
        self.assertIn("Structure: \u5f53\u524d\u76d1\u63a7\u6c60\u504f\u5411\u6750\u6599\u94fe\uff0ccore\u6c60\u5360\u6bd4\u7ea6 1/10\u3002", readiness_markdown)
        self.assertIn("A quick validation review is recommended now.", readiness_markdown)

    def test_build_empty_state_markdown_uses_shared_wrapper(self) -> None:
        empty_markdown = _build_empty_state_markdown(
            "No latest alerts available yet.",
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec(),
        )

        self.assertIn("INFO EMPTY STATE", empty_markdown)
        self.assertIn("No latest alerts available yet.", empty_markdown)
        self.assertIn("No data available yet", empty_markdown)

    def test_build_info_panel_markdown_builds_consistent_multi_block_panel(self) -> None:
        panel_markdown = _build_info_panel_markdown(
            tone="accent",
            label="chart",
            body="Sector Strength",
            supporting_title="! WARNING DETAILS",
            supporting_body="Data table and chart follow",
            panel_density="comfortable",
        )

        self.assertIn("dashboard-panel", panel_markdown)
        self.assertIn("dashboard-panel--accent", panel_markdown)
        self.assertIn("dashboard-panel__title", panel_markdown)
        self.assertIn("+ ACCENT CHART", panel_markdown)
        self.assertIn("Sector Strength", panel_markdown)
        self.assertIn("! WARNING DETAILS", panel_markdown)
        self.assertIn("Data table and chart follow", panel_markdown)

    def test_build_dashboard_panel_css_uses_replaceable_surface_tokens(self) -> None:
        css = _build_dashboard_panel_css(build_panel_container_style_spec())

        self.assertIn(".dashboard-panel", css)
        self.assertIn(".dashboard-panel--accent", css)
        self.assertIn(".dashboard-panel--warning", css)
        self.assertIn("#f7f4ea", css)
        self.assertIn("border-radius: 18px", css)
        self.assertIn("#c87b2a", css)

    def test_build_kpi_metric_caption_uses_tone_and_label(self) -> None:
        caption = _build_kpi_metric_caption(
            {
                "tone": "accent",
                "label": "Positive Alerts",
            }
        )

        self.assertIn("ACCENT", caption)
        self.assertIn("Positive Alerts", caption)

    def test_build_kpi_metric_caption_can_prefer_configured_caption(self) -> None:
        caption = _build_kpi_metric_caption(
            {
                "tone": "info",
                "label": "Pool Drift",
                "caption": "Top-line stock-pool structure drift cue",
            }
        )

        self.assertIn("INFO", caption)
        self.assertIn("Top-line stock-pool structure drift cue", caption)

    def test_build_kpi_section_header_markdown_uses_panel_block(self) -> None:
        header = _build_kpi_section_header_markdown(
            panel_density="comfortable",
            style_spec=build_kpi_panel_style_spec(),
        )

        self.assertIn("dashboard-panel", header)
        self.assertIn("= NEUTRAL KPI SECTION", header)
        self.assertIn("Latest snapshot and alert counters", header)
        self.assertIn("Primary monitor snapshot", header)

    def test_build_kpi_section_header_markdown_uses_business_cn_section_label(self) -> None:
        header = _build_kpi_section_header_markdown(
            panel_density="comfortable",
            style_spec=build_kpi_panel_style_spec("business_cn"),
        )

        self.assertIn("NEUTRAL \u6307\u6807\u533a", header)

    def test_build_kpi_section_header_markdown_uses_compact_supporting_copy(self) -> None:
        header = _build_kpi_section_header_markdown(
            panel_density="compact",
            style_spec=build_kpi_panel_style_spec(),
        )

        self.assertIn("Top-line monitor metrics", header)

    def test_build_kpi_metric_panel_markdown_uses_shared_kpi_style_spec(self) -> None:
        card_markdown = _build_kpi_metric_panel_markdown(
            {
                "tone": "warning",
                "label": "Negative Alerts",
            },
            panel_density="comfortable",
            style_spec=build_kpi_panel_style_spec(),
        )

        self.assertIn("dashboard-panel--warning", card_markdown)
        self.assertIn("! WARNING KPI", card_markdown)
        self.assertIn("Negative Alerts", card_markdown)
        self.assertIn("Primary dashboard counter", card_markdown)

    def test_build_kpi_metric_panel_markdown_uses_business_cn_metric_label(self) -> None:
        card_markdown = _build_kpi_metric_panel_markdown(
            {
                "tone": "warning",
                "label": "璐熷悜鎻愰啋",
            },
            panel_density="comfortable",
            style_spec=build_kpi_panel_style_spec("business_cn"),
        )

        self.assertIn("WARNING \u6307\u6807\u5361", card_markdown)

    def test_build_content_section_header_markdown_uses_shared_content_style_spec(self) -> None:
        header = _build_content_section_header_markdown(
            "Leader Summary",
            tone="neutral",
            panel_density="comfortable",
            style_spec=build_content_panel_style_spec(),
        )

        self.assertIn("NEUTRAL CONTENT SECTION", header)
        self.assertIn("Leader Summary", header)
        self.assertIn("Structured monitor summary", header)

    def test_build_content_section_header_markdown_uses_business_cn_section_label(self) -> None:
        header = _build_content_section_header_markdown(
            "\u9f99\u5934\u6458\u8981",
            tone="neutral",
            panel_density="comfortable",
            style_spec=build_content_panel_style_spec("business_cn"),
        )

        self.assertIn("NEUTRAL \u5185\u5bb9\u533a", header)

    def test_build_content_section_header_markdown_can_include_focus_label(self) -> None:
        header = _build_content_section_header_markdown(
            "Latest Alerts",
            tone="accent",
            panel_density="comfortable",
            focus_label="Primary focus",
            style_spec=build_content_panel_style_spec(),
        )

        self.assertIn("Primary focus", header)

    def test_build_content_section_header_markdown_can_apply_focus_tone_override(self) -> None:
        header = _build_content_section_header_markdown(
            "Latest Alerts",
            tone="neutral",
            panel_density="comfortable",
            focus_label="1. Step 1 focus",
            focus_tone="accent",
            style_spec=build_content_panel_style_spec(),
        )

        self.assertIn("ACCENT CONTENT SECTION", header)

    def test_build_content_detail_markdown_uses_compact_content_style_spec(self) -> None:
        detail_markdown = _build_content_detail_markdown(
            tone="warning",
            body=build_content_panel_style_spec()["grouped_detail_body"],
            panel_density="compact",
            style_spec=build_content_panel_style_spec(),
        )

        self.assertIn("WARNING CONTENT DETAILS", detail_markdown)
        self.assertIn("Grouped detail ...", detail_markdown)
        self.assertIn("Grouped details", detail_markdown)

    def test_build_content_detail_markdown_uses_business_cn_detail_label(self) -> None:
        detail_markdown = _build_content_detail_markdown(
            tone="warning",
            body="\u5206\u7ec4\u660e\u7ec6",
            panel_density="comfortable",
            style_spec=build_content_panel_style_spec("business_cn"),
        )

        self.assertIn("WARNING \u5185\u5bb9\u660e\u7ec6", detail_markdown)

    def test_build_metric_group_markdown_uses_shared_metric_group_style_spec(self) -> None:
        group_markdown = _build_metric_group_markdown(
            tone="accent",
            label="metric row",
            body="KPI values",
            panel_density="comfortable",
            style_spec=build_metric_group_style_spec(),
        )

        self.assertIn("dashboard-panel--accent", group_markdown)
        self.assertIn("+ ACCENT METRIC ROW", group_markdown)
        self.assertIn("KPI values", group_markdown)
        self.assertIn("Top-line values", group_markdown)

    def test_build_metric_group_markdown_uses_compact_metric_group_copy(self) -> None:
        group_markdown = _build_metric_group_markdown(
            tone="neutral",
            label="metric row",
            body="KPI values",
            panel_density="compact",
            style_spec=build_metric_group_style_spec(),
        )

        self.assertIn("Compact metric strip", group_markdown)

    def test_build_metric_group_markdown_uses_business_cn_default_label(self) -> None:
        group_markdown = _build_metric_group_markdown(
            tone="accent",
            label="metric row",
            body="\u5173\u952e\u6307\u6807",
            panel_density="comfortable",
            style_spec=build_metric_group_style_spec("business_cn"),
        )

        self.assertIn("ACCENT \u6307\u6807\u884c", group_markdown)
        self.assertIn("\u9876\u5c42\u5173\u952e\u6570\u503c", group_markdown)

    def test_format_kpi_metric_value_formats_timestamp_values(self) -> None:
        formatted = _format_kpi_metric_value(
            "2026-06-21 14:45:00",
            format_key="timestamp",
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("2026-06-21 14:45", formatted)

    def test_format_kpi_metric_value_formats_count_values(self) -> None:
        formatted = _format_kpi_metric_value(
            12345,
            format_key="count",
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("12,345", formatted)

    def test_format_kpi_metric_value_formats_percent_values(self) -> None:
        formatted = _format_kpi_metric_value(
            6.94,
            format_key="percent_1",
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("6.9%", formatted)

    def test_format_kpi_metric_value_formats_signed_percent_values(self) -> None:
        positive_formatted = _format_kpi_metric_value(
            6.94,
            format_key="signed_percent_1",
            format_spec=build_kpi_value_format_spec(),
        )
        negative_formatted = _format_kpi_metric_value(
            -2.41,
            format_key="signed_percent_1",
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("+6.9%", positive_formatted)
        self.assertEqual("-2.4%", negative_formatted)

    def test_format_kpi_metric_value_falls_back_to_empty_copy(self) -> None:
        formatted = _format_kpi_metric_value(
            None,
            format_key="timestamp",
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("No data", formatted)

    def test_apply_kpi_value_length_limit_truncates_long_copy(self) -> None:
        limited = _apply_kpi_value_length_limit(
            "Pool drift: materials exposure increased and equipment weight rose.",
            max_length=24,
        )

        self.assertEqual("Pool drift: materials...", limited)

    def test_resolve_kpi_card_value_uses_text_card_path(self) -> None:
        resolved = _resolve_kpi_card_value(
            {"stock_pool_drift_summary": "Pool drift: materials exposure increased sharply."},
            {
                "value_key": "stock_pool_drift_summary",
                "empty_value": "No drift summary",
                "card_type": "text",
                "format_key": "default",
                "value_max_length": 24,
            },
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("Pool drift: materials...", resolved)

    def test_resolve_kpi_card_value_uses_quote_status_text_path(self) -> None:
        resolved = _resolve_kpi_card_value(
            {"quote_status_summary": "Quote status: using local real quote snapshot."},
            {
                "value_key": "quote_status_summary",
                "empty_value": "Quote status: unavailable.",
                "card_type": "text",
                "format_key": "default",
                "value_max_length": 30,
            },
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("Quote status: using local r...", resolved)

    def test_resolve_kpi_card_value_uses_numeric_card_path(self) -> None:
        resolved = _resolve_kpi_card_value(
            {"alert_count": 12345},
            {
                "value_key": "alert_count",
                "empty_value": 0,
                "card_type": "numeric",
                "format_key": "count",
                "value_max_length": 4,
            },
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("12,345", resolved)

    def test_resolve_kpi_card_specs_applies_layout_order_and_variant_overrides(self) -> None:
        specs = _resolve_kpi_card_specs(
            "default",
            kpi_summary_layout={
                "card_order": [
                    "mainline_summary",
                    "quote_status_summary",
                    "risk_summary",
                    "stock_pool_drift_summary",
                ],
                "card_variant_overrides": {
                    "mainline_summary": "priority",
                    "quote_status_summary": "compact",
                    "risk_summary": "compact",
                },
            },
        )

        self.assertEqual("mainline_summary", specs[0]["value_key"])
        self.assertEqual("warning", specs[0]["tone"])
        self.assertEqual("quote_status_summary", specs[1]["value_key"])
        self.assertEqual("Data Mode", specs[1]["label"])
        self.assertEqual("risk_summary", specs[2]["value_key"])
        self.assertEqual("Risk", specs[2]["label"])
        self.assertEqual("stock_pool_drift_summary", specs[3]["value_key"])

    def test_format_rows_for_display_applies_column_format_metadata(self) -> None:
        rows = [
            {
                "timestamp": "2026-06-20 14:45:00",
                "avg_pct_chg": 6.94,
                "name": "Semi Materials",
            }
        ]

        formatted_rows = _format_rows_for_display(
            rows,
            column_formats={
                "timestamp": "timestamp",
                "avg_pct_chg": "signed_percent_1",
            },
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual("2026-06-20 14:45", formatted_rows[0]["timestamp"])
        self.assertEqual("+6.9%", formatted_rows[0]["avg_pct_chg"])
        self.assertEqual("Semi Materials", formatted_rows[0]["name"])

    def test_normalize_display_field_specs_returns_shared_field_shape(self) -> None:
        normalized = _normalize_display_field_specs(
            [
                {
                    "key": "timestamp",
                    "label": "Batch Time",
                    "format_key": "timestamp",
                },
                {
                    "key": "sector",
                    "prefix": "Leading group: ",
                },
            ]
        )

        self.assertEqual("timestamp", normalized[0]["key"])
        self.assertEqual("Batch Time", normalized[0]["label"])
        self.assertEqual("timestamp", normalized[0]["format_key"])
        self.assertEqual("", normalized[0]["prefix"])
        self.assertEqual("sector", normalized[1]["key"])
        self.assertEqual("sector", normalized[1]["label"])
        self.assertEqual("Leading group:", normalized[1]["prefix"])

    def test_render_content_block_with_density_formats_table_columns_from_metadata(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "custom_table": [
                {
                    "timestamp": "2026-06-20 14:45:00",
                    "pct_chg": 6.94,
                    "name": "Semi Materials",
                }
            ]
        }
        spec = {
            "title": "Custom Table",
            "data_key": "custom_table",
            "render_type": "table",
            "tone": "accent",
            "table_columns": [
                {
                    "key": "timestamp",
                    "label": "Batch Time",
                    "format_key": "timestamp",
                },
                {
                    "key": "pct_chg",
                    "label": "Change",
                    "format_key": "signed_percent_1",
                },
                {
                    "key": "name",
                    "label": "Sector Name",
                },
            ],
            "empty_message": "No custom table data available yet.",
        }

        _render_content_block_with_density(
            fake_st,
            payload,
            spec,
            panel_density="comfortable",
        )

        self.assertIsNotNone(fake_st.dataframe_rows)
        self.assertTrue(bool(fake_st.dataframe_use_container_width))
        self.assertEqual(
            ["Batch Time", "Change", "Sector Name"],
            list(fake_st.dataframe_rows[0].keys()),
        )
        self.assertEqual("2026-06-20 14:45", fake_st.dataframe_rows[0]["Batch Time"])
        self.assertEqual("+6.9%", fake_st.dataframe_rows[0]["Change"])
        self.assertEqual("Semi Materials", fake_st.dataframe_rows[0]["Sector Name"])
        self.assertTrue(
            any("ACCENT CONTENT SECTION" in call for call in fake_st.markdown_calls)
        )
        self.assertTrue(
            any("ACCENT CONTENT DETAILS" in call for call in fake_st.markdown_calls)
        )

    def test_render_content_block_with_density_can_show_focus_label_in_section_header(self) -> None:
        fake_st = _FakeStreamlit()

        _render_content_block_with_density(
            fake_st,
            {"latest_alerts": []},
            {
                "title": "Latest Alerts",
                "data_key": "latest_alerts",
                "render_type": "alerts_grouped",
                "empty_message": "No latest alerts",
                "tone": "accent",
            },
            panel_density="comfortable",
            focus_label="1. Step 1 focus",
        )

        self.assertTrue(any("1. Step 1 focus" in call for call in fake_st.markdown_calls))

    def test_render_content_block_with_density_can_apply_focus_tone_to_section_header(self) -> None:
        fake_st = _FakeStreamlit()

        _render_content_block_with_density(
            fake_st,
            {"latest_alerts": []},
            {
                "title": "Latest Alerts",
                "data_key": "latest_alerts",
                "render_type": "alerts_grouped",
                "empty_message": "No latest alerts",
                "tone": "neutral",
            },
            panel_density="comfortable",
            focus_label="1. Step 1 focus",
            focus_tone="accent",
        )

        self.assertTrue(any("ACCENT CONTENT SECTION" in call for call in fake_st.markdown_calls))

    def test_render_content_block_with_density_adds_anchor_target_for_section_key(self) -> None:
        fake_st = _FakeStreamlit()

        _render_content_block_with_density(
            fake_st,
            {"latest_alerts": []},
            {
                "title": "Latest Alerts",
                "data_key": "latest_alerts",
                "render_type": "alerts_grouped",
                "empty_message": "No latest alerts",
                "tone": "neutral",
            },
            panel_density="comfortable",
            section_key="latest_alerts",
        )

        self.assertTrue(any('id="section-latest-alerts"' in call for call in fake_st.markdown_calls))

    def test_render_content_block_with_density_adds_primary_group_anchor_for_grouped_section(self) -> None:
        fake_st = _FakeStreamlit()
        spec = build_content_section_specs()["today_priority_summary"]

        _render_content_block_with_density(
            fake_st,
            {
                "today_priority_summary": {
                    "summary_date": "2026-07-18",
                    "shown_items": 1,
                    "total_items": 1,
                    "core_summary": "先看风险扩散。",
                    "one_line_advice": "先防守，再确认。",
                    "daily_conclusion": "风险优先。",
                    "operation_tips": "先读风险名单。",
                    "read_order": ["1. 先看风险优先名单"],
                    "watch_rows": ["- 风险优先名单：中微公司、北方华创"],
                    "action_rows": ["- 风险优先动作"],
                    "source_batch": "data/news/news_batch_20260718.json",
                    "impact_summary": "风险扩散 1",
                    "filter_mode": "high-priority-only",
                    "watch_group_count": 1,
                }
            },
            {
                **spec,
                "copy_variant": "business_cn",
            },
            panel_density="comfortable",
            surface_copy_variant="business_cn",
            section_key="today_priority_summary",
        )

        self.assertTrue(any('id="section-today-priority-summary"' in call for call in fake_st.markdown_calls))
        self.assertTrue(
            any('id="section-today-priority-summary-primary"' in call for call in fake_st.markdown_calls)
        )

    def test_render_content_block_with_density_can_highlight_first_group_inside_focus_module(self) -> None:
        fake_st = _FakeStreamlit()
        spec = build_content_section_specs()["today_priority_summary"]

        _render_content_block_with_density(
            fake_st,
            {
                "today_priority_summary": {
                    "summary_date": "2026-07-18",
                    "shown_items": 2,
                    "total_items": 3,
                    "core_summary": "先看风险扩散，再看主线强化。",
                    "one_line_advice": "先防守，再确认跟随。",
                    "daily_conclusion": "风险与强化并存。",
                    "operation_tips": "先读风险名单。",
                    "read_order": ["1. 先看风险优先名单"],
                    "watch_rows": ["- 风险优先名单：中微公司、北方华创"],
                    "action_rows": ["- 风险优先动作"],
                    "source_batch": "data/news/news_batch_20260718.json",
                    "impact_summary": "风险扩散 1 | 主线强化 1",
                    "filter_mode": "high-priority-only",
                    "watch_group_count": 1,
                }
            },
            {
                **spec,
                "copy_variant": "business_cn",
            },
            panel_density="comfortable",
            surface_copy_variant="business_cn",
            focus_label="1. 第 1 步重点模块",
            focus_tone="accent",
        )

        self.assertTrue(any("核心摘要:" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("ACCENT 内容区" in call for call in fake_st.markdown_calls))

    def test_render_page_layout_applies_business_cn_copy_variant_overrides(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "strongest_sector_summary": {
                "sector": "Semi Materials",
                "avg_pct_chg": 6.9,
                "stock_count": 2,
            }
        }

        _render_page_layout(
            fake_st,
            payload,
            [
                {
                    "section_type": "content",
                    "section_key": "strongest_sector",
                }
            ],
            kpi_copy_variant="default",
            surface_copy_variant="default",
            content_variant_overrides={"strongest_sector": "business_cn"},
            panel_density="comfortable",
        )

        self.assertTrue(any("\u677f\u5757\u660e\u7ec6:" in call for call in fake_st.write_calls))

    def test_render_page_layout_can_mark_priority_focus_sections(self) -> None:
        fake_st = _FakeStreamlit()

        _render_page_layout(
            fake_st,
            {
                "latest_alerts": [],
                "next_session_action_summary": {},
                "stock_pool_health": {},
            },
            [
                {
                    "section_type": "content",
                    "section_key": "latest_alerts",
                },
                {
                    "section_type": "content",
                    "section_key": "next_session_action",
                },
                {
                    "section_type": "content",
                    "section_key": "stock_pool_health",
                },
            ],
            kpi_copy_variant="default",
            surface_copy_variant="default",
            content_variant_overrides={},
            priority_action_sections=["latest_alerts", "next_session_action", "stock_pool_health"],
            panel_density="comfortable",
        )

        self.assertTrue(any("1. Step 1 focus" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("2. Step 2 follow-up" in call for call in fake_st.markdown_calls))

    def test_render_page_layout_applies_business_cn_kpi_copy_variant(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "latest_timestamp": "2026-06-20 14:45:00",
            "mainline_summary": "Main line: Semi Materials remains the clearest strength.",
            "stock_pool_drift_summary": "Pool drift: stable vs baseline.",
            "risk_summary": "Risk state: stable; no dominant warning signal is active.",
            "positive_alert_count": 3,
            "negative_alert_count": 1,
            "alert_count": 4,
        }

        _render_page_layout(
            fake_st,
            payload,
            [
                {
                    "section_type": "kpi",
                    "section_key": "kpi_cards",
                }
            ],
            kpi_summary_layout={"card_order": ["latest_timestamp", "mainline_summary"]},
            kpi_copy_variant="business_cn",
            surface_copy_variant="business_cn",
            content_variant_overrides={},
            panel_density="comfortable",
        )

        self.assertTrue(any("\u5f53\u524d\u76d1\u63a7\u9876\u5c42\u6982\u89c8" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u5f53\u524d\u6279\u6b21\u4e0e\u63d0\u9192\u6982\u89c8" in call for call in fake_st.markdown_calls))

    def test_render_page_layout_applies_quick_scan_kpi_layout_order(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "latest_timestamp": "2026-06-20 14:45:00",
            "mainline_summary": "Main line: Semi Materials remains the clearest strength.",
            "stock_pool_drift_summary": "Pool drift: stable vs baseline.",
            "risk_summary": "Risk state: stable; no dominant warning signal is active.",
            "positive_alert_count": 3,
            "negative_alert_count": 1,
            "alert_count": 4,
        }

        _render_page_layout(
            fake_st,
            payload,
            [
                {
                    "section_type": "kpi",
                    "section_key": "kpi_cards",
                }
            ],
            kpi_summary_layout={
                "card_order": [
                    "mainline_summary",
                    "risk_summary",
                    "stock_pool_drift_summary",
                    "latest_timestamp",
                ],
                "card_variant_overrides": {
                    "mainline_summary": "priority",
                    "risk_summary": "priority",
                },
            },
            kpi_copy_variant="default",
            surface_copy_variant="default",
            content_variant_overrides={},
            panel_density="comfortable",
        )

        self.assertEqual("Main-Line View", fake_st.metric_calls[0][0])
        self.assertEqual("Risk State", fake_st.metric_calls[1][0])
        self.assertEqual("Pool Drift", fake_st.metric_calls[2][0])
        self.assertTrue(any("Priority main-line conclusion" in call for call in fake_st.caption_calls))

    def test_render_page_layout_applies_business_cn_surface_copy_variant(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "sector_cards": [
                {
                    "sector": "Semi Materials",
                    "avg_pct_chg": 6.94,
                    "stock_count": 2,
                }
            ],
            "sector_chart": [
                {
                    "sector": "Semi Materials",
                    "avg_pct_chg": 6.94,
                }
            ],
            "strongest_sector_summary": {
                "sector": "Semi Materials",
                "avg_pct_chg": 6.9,
                "stock_count": 2,
            },
        }

        _render_page_layout(
            fake_st,
            payload,
            [
                {
                    "section_type": "chart",
                    "section_key": "sector_strength",
                },
                {
                    "section_type": "content",
                    "section_key": "strongest_sector",
                }
            ],
            kpi_copy_variant="default",
            surface_copy_variant="business_cn",
            content_variant_overrides={"strongest_sector": "business_cn"},
            panel_density="comfortable",
        )

        self.assertTrue(any("\u4e0b\u65b9\u5c55\u793a\u6570\u636e\u8868\u4e0e\u56fe\u8868" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u5148\u770b\u6307\u6807\uff0c\u518d\u770b\u660e\u7ec6" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u677f\u5757\u5f3a\u5ea6" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u6700\u5f3a\u677f\u5757" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u6a2a\u8f74: \u677f\u5757" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u7eb5\u8f74: \u5e73\u5747\u6da8\u8dcc" in call for call in fake_st.markdown_calls))
        self.assertTrue(any("\u8bf7\u7ee7\u7eed\u67e5\u770b\u4e0b\u65b9\u5206\u7ec4\u660e\u7ec6" in call for call in fake_st.markdown_calls))

    def test_render_page_layout_can_precede_sections_with_view_mode_note(self) -> None:
        fake_st = _FakeStreamlit()
        note_markdown = _build_view_mode_note_markdown(
            {
                "tone": "accent",
                "summary_label": "view mode",
                "title": "Quick Scan View",
                "body": "Fast first-screen layout for KPI and latest alerts.",
                "supporting_copy": "Use this mode when time is limited.",
            },
            panel_density="compact",
        )

        fake_st.markdown(note_markdown, unsafe_allow_html=True)
        _render_page_layout(
            fake_st,
            {"latest_alerts": []},
            [
                {
                    "section_type": "content",
                    "section_key": "latest_alerts",
                }
            ],
            kpi_copy_variant="default",
            surface_copy_variant="default",
            content_variant_overrides={},
            panel_density="compact",
        )

        self.assertIn("Quick Scan View", fake_st.markdown_calls[0])
        self.assertTrue(any("Latest Alerts" in call for call in fake_st.markdown_calls[1:]))


    def test_render_content_block_with_density_applies_business_cn_table_surface_copy(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "custom_table": [
                {
                    "timestamp": "2026-06-20 14:45:00",
                    "pct_chg": 6.94,
                    "name": "Semi Materials",
                }
            ]
        }
        spec = {
            "title": "Custom Table",
            "data_key": "custom_table",
            "render_type": "table",
            "tone": "accent",
            "table_columns": [
                {
                    "key": "timestamp",
                    "label": "Batch Time",
                    "format_key": "timestamp",
                },
                {
                    "key": "pct_chg",
                    "label": "Change",
                    "format_key": "signed_percent_1",
                },
                {
                    "key": "name",
                    "label": "Sector Name",
                },
            ],
            "empty_message": "No custom table data available yet.",
        }

        _render_content_block_with_density(
            fake_st,
            payload,
            spec,
            panel_density="comfortable",
            surface_copy_variant="business_cn",
        )

        self.assertTrue(any("\u683c\u5f0f\u5316\u5185\u5bb9\u8868" in call for call in fake_st.markdown_calls))

    def test_build_table_rows_for_display_keeps_legacy_column_metadata_working(self) -> None:
        rows = [
            {
                "timestamp": "2026-06-20 14:45:00",
                "pct_chg": 6.94,
                "name": "Semi Materials",
            }
        ]
        spec = {
            "columns": ["timestamp", "pct_chg", "name"],
            "table_column_formats": {
                "timestamp": "timestamp",
                "pct_chg": "signed_percent_1",
            },
        }

        display_rows = _build_table_rows_for_display(
            rows,
            spec=spec,
            format_spec=build_kpi_value_format_spec(),
        )

        self.assertEqual(["timestamp", "pct_chg", "name"], list(display_rows[0].keys()))
        self.assertEqual("2026-06-20 14:45", display_rows[0]["timestamp"])
        self.assertEqual("+6.9%", display_rows[0]["pct_chg"])
        self.assertEqual("Semi Materials", display_rows[0]["name"])

    def test_render_chart_block_uses_table_columns_metadata_for_companion_table(self) -> None:
        fake_st = _FakeStreamlit()
        payload = {
            "sector_cards": [
                {
                    "sector": "Semi Materials",
                    "avg_pct_chg": 6.94,
                    "stock_count": 2,
                }
            ],
            "sector_chart": [
                {
                    "sector": "Semi Materials",
                    "avg_pct_chg": 6.94,
                }
            ],
        }
        spec = build_chart_specs()["sector_strength"]

        _render_chart_block(
            fake_st,
            payload,
            spec,
            panel_density="comfortable",
            surface_copy_variant="default",
        )

        self.assertEqual(
            ["Sector", "Avg Change", "Stock Count"],
            list(fake_st.dataframe_rows[0].keys()),
        )
        self.assertEqual("Semi Materials", fake_st.dataframe_rows[0]["Sector"])
        self.assertEqual("+6.9%", fake_st.dataframe_rows[0]["Avg Change"])
        self.assertEqual("2", fake_st.dataframe_rows[0]["Stock Count"])
        self.assertEqual("sector", fake_st.bar_chart_x)
        self.assertEqual("avg_pct_chg", fake_st.bar_chart_y)

    def test_build_chart_axes_markdown_uses_business_cn_axis_copy(self) -> None:
        axis_markdown = _build_chart_axes_markdown(
            {
                "tone": "accent",
                "x_axis_label": "\u677f\u5757",
                "y_axis_label": "\u5e73\u5747\u6da8\u8dcc",
            },
            panel_density="comfortable",
            style_spec=build_summary_panel_style_spec("business_cn"),
        )

        self.assertIn("ACCENT \u5750\u6807", axis_markdown)
        self.assertIn("\u6a2a\u8f74: \u677f\u5757", axis_markdown)
        self.assertIn("\u7eb5\u8f74: \u5e73\u5747\u6da8\u8dcc", axis_markdown)

    def test_build_chart_section_header_markdown_uses_tone_and_title(self) -> None:
        header = _build_chart_section_header_markdown(
            {
                "tone": "warning",
                "title": "Top Movers",
            }
        )

        self.assertIn("! ", header)
        self.assertIn("WARNING CHART", header)
        self.assertIn("Top Movers", header)

    def test_build_chart_section_header_markdown_uses_business_cn_chart_label(self) -> None:
        header = _build_chart_section_header_markdown(
            {
                "tone": "warning",
                "title": "Top Movers",
            },
            style_spec=build_summary_panel_style_spec("business_cn"),
        )

        self.assertIn("WARNING \u56fe\u8868", header)

    def test_resolve_tone_icon_returns_expected_symbol(self) -> None:
        self.assertEqual("+", _resolve_tone_icon("accent"))
        self.assertEqual("!", _resolve_tone_icon("warning"))
        self.assertEqual("=", _resolve_tone_icon("neutral"))

    def test_build_tone_panel_title_uses_icon_tone_and_label(self) -> None:
        title = _build_tone_panel_title("accent", "summary")

        self.assertEqual("+ ACCENT SUMMARY", title)

    def test_build_panel_block_markdown_wraps_title_and_body(self) -> None:
        block = _build_panel_block_markdown(
            "+ ACCENT SUMMARY",
            "Semi Materials",
        )

        self.assertIn("dashboard-panel", block)
        self.assertIn("+ ACCENT SUMMARY", block)
        self.assertIn("Semi Materials", block)

    def test_build_panel_body_text_varies_by_density(self) -> None:
        verbose = _build_panel_body_text(
            "Latest snapshot and alert counters",
            panel_density="comfortable",
        )
        compact = _build_panel_body_text(
            "Latest snapshot and alert counters",
            panel_density="compact",
        )

        self.assertEqual("Latest snapshot and alert counters", verbose)
        self.assertEqual("Latest snapshot...", compact)


if __name__ == "__main__":
    unittest.main()
