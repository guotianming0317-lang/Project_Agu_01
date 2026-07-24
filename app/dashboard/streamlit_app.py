"""Minimal Streamlit dashboard for latest monitor results."""

from __future__ import annotations

from datetime import datetime
from html import escape
from importlib import import_module

from app.config import load_config
from app.dashboard.overview import build_dashboard_payload
from app.dashboard.presentation import (
    build_business_role_specs,
    build_chart_specs,
    build_content_panel_style_spec,
    build_control_band_specs,
    build_dynamic_action_focus_fact_specs,
    build_dynamic_action_focus_specs,
    build_effective_time_phase_specs,
    build_home_header_style_spec,
    build_intro_panel_style_spec,
    build_content_section_specs,
    build_kpi_card_specs,
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
    build_semantic_signal_style_spec,
    build_view_variant_specs,
    resolve_dashboard_view_spec,
)

DEFAULT_DASHBOARD_VARIANT = "default"


def main() -> None:
    """Run the minimal local dashboard."""
    st = _import_streamlit()

    config = load_config()
    variant_specs = build_view_variant_specs()
    latest_payload = build_dashboard_payload(config.database_path)
    recommended_variant = _recommend_dashboard_variant_key(
        variant_specs,
        latest_payload,
    )
    recommendation_note = _build_dashboard_variant_recommendation_note(
        selected_variant_key=recommended_variant,
        recommended_variant_key=recommended_variant,
        payload=latest_payload,
        variant_specs=variant_specs,
    )
    selected_variant = _resolve_dashboard_variant_key(
        variant_specs,
        st.session_state.get("dashboard_variant"),
        recommended_variant=recommended_variant,
    )
    view_spec = resolve_dashboard_view_spec(selected_variant)
    theme = view_spec["theme"]

    st.set_page_config(
        page_title=str(theme["page_title"]),
        layout=str(theme["layout"]),
    )
    st.markdown(
        _build_dashboard_panel_css(build_panel_container_style_spec()),
        unsafe_allow_html=True,
    )
    st.title(str(theme["app_title"]))
    selected_variant = st.selectbox(
        str(theme.get("view_selector_label", "Dashboard View")),
        options=list(variant_specs.keys()),
        index=list(variant_specs.keys()).index(selected_variant),
        format_func=lambda key: str(variant_specs[key]["label"]),
        key="dashboard_variant",
    )
    recommendation_note = _build_dashboard_variant_recommendation_note(
        selected_variant_key=selected_variant,
        recommended_variant_key=recommended_variant,
        payload=latest_payload,
        variant_specs=variant_specs,
    )
    priority_action_note = _build_dashboard_priority_action_note(
        selected_variant_key=selected_variant,
        recommended_variant_key=recommended_variant,
        payload=latest_payload,
        copy_variant="business_cn" if selected_variant == "business_cn" else "default",
    )
    priority_action_scenario = _resolve_priority_action_scenario(
        selected_variant_key=selected_variant,
        recommended_variant_key=recommended_variant,
        payload=latest_payload,
    )
    view_spec = resolve_dashboard_view_spec(selected_variant)
    theme = view_spec["theme"]
    time_phase_override = st.selectbox(
        str(theme.get("time_phase_selector_label", "Time Phase")),
        options=_build_time_phase_override_options(),
        index=_build_time_phase_override_options().index(
            _resolve_time_phase_override_key(st.session_state.get("time_phase_override"))
        ),
        format_func=lambda key: _resolve_time_phase_override_label(
            key,
            copy_variant=str(view_spec.get("surface_copy_variant", "default")),
            auto_label=str(theme.get("time_phase_auto_label", "Auto")),
        ),
        key="time_phase_override",
    )
    batches = latest_payload["available_batches"]
    selected_batch = None
    if batches:
        selected_batch = st.selectbox(
            str(theme["batch_selector_label"]),
            batches,
            index=0,
        )
    payload = build_dashboard_payload(
        config.database_path,
        selected_timestamp=selected_batch,
    )
    effective_time_phase = _resolve_effective_time_phase(
        payload=payload,
        copy_variant=str(view_spec.get("surface_copy_variant", "default")),
        phase_override_key=time_phase_override,
    )
    priority_action_sections = _resolve_priority_action_sections(
        selected_variant_key=selected_variant,
        recommended_variant_key=recommended_variant,
        payload=payload,
        phase_override_key=time_phase_override,
    )
    effective_page_layout = _apply_role_strategy_to_page_layout(
        _filter_page_layout_sections(
            list(view_spec["page_layout"]),
            excluded_section_keys={"kpi_cards"},
        ),
        role_strategy=_merge_layout_strategy(
            _merge_layout_strategy(
                dict(view_spec.get("role_strategy", {})),
                effective_time_phase,
            ),
            {
                "pinned_sections": list(priority_action_sections),
                "deferred_sections": _resolve_priority_action_deferred_sections(
                    list(priority_action_sections)
                ),
            },
        ),
    )
    priority_action_sections = _normalize_priority_action_sections_for_layout(
        effective_page_layout,
        priority_action_sections=priority_action_sections,
    )
    _render_home_header(
        st,
        payload,
        home_header_layout=list(view_spec.get("home_header_layout", [])),
        home_header_style=dict(view_spec.get("home_header_style", {})),
        view_mode_note=dict(view_spec.get("view_mode_note", {})),
        task_template=dict(view_spec.get("task_template", {})),
        time_phase=effective_time_phase,
        time_phase_override_key=time_phase_override,
        role_strategy=dict(view_spec.get("role_strategy", {})),
        recommendation_note=recommendation_note,
        priority_action_note=priority_action_note,
        priority_action_profile=_build_priority_action_profile(
            priority_action_scenario,
            copy_variant=str(view_spec.get("surface_copy_variant", "default")),
            phase_key=_resolve_priority_action_phase_key(
                payload=payload,
                phase_override_key=time_phase_override,
            ),
        ),
        priority_action_sections=priority_action_sections,
        priority_action_locations=_build_priority_action_locations(
            effective_page_layout,
            priority_action_sections=priority_action_sections,
            copy_variant=str(view_spec.get("surface_copy_variant", "default")),
        ),
        selected_batch=selected_batch,
        database_caption=str(theme["caption_template"]).format(
            database_url=config.database_url,
        ),
        control_band_copy_variant=str(view_spec.get("surface_copy_variant", "default")),
        control_band_layout=list(view_spec.get("control_band_layout", [])),
        kpi_copy_variant=str(view_spec.get("kpi_copy_variant", "default")),
        kpi_summary_layout=dict(view_spec.get("kpi_summary_layout", {})),
        panel_density=str(theme.get("panel_density", "comfortable")),
    )

    _render_page_layout(
        st,
        payload,
        effective_page_layout,
        kpi_summary_layout=dict(view_spec.get("kpi_summary_layout", {})),
        kpi_copy_variant=str(view_spec.get("kpi_copy_variant", "default")),
        surface_copy_variant=str(view_spec.get("surface_copy_variant", "default")),
        content_variant_overrides=dict(view_spec.get("content_variant_overrides", {})),
        priority_action_sections=priority_action_sections,
        panel_density=str(theme.get("panel_density", "comfortable")),
    )


def _import_streamlit() -> object:
    """Import Streamlit with a clearer first-run error for local users."""
    try:
        return import_module("streamlit")
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Streamlit is not installed. Run `pip install -r requirements.txt` first."
        ) from exc


def _resolve_dashboard_variant_key(
    variant_specs: dict[str, dict[str, object]],
    requested_variant: object,
    *,
    recommended_variant: object | None = None,
) -> str:
    """Resolve a safe dashboard variant key from UI state."""
    if isinstance(requested_variant, str) and requested_variant in variant_specs:
        return requested_variant
    if isinstance(recommended_variant, str) and recommended_variant in variant_specs:
        return recommended_variant
    return DEFAULT_DASHBOARD_VARIANT


def _recommend_dashboard_variant_key(
    variant_specs: dict[str, dict[str, object]],
    payload: dict[str, object] | None,
) -> str:
    """Recommend a default dashboard mode from current market state."""
    if not payload:
        return DEFAULT_DASHBOARD_VARIANT

    latest_timestamp = _parse_dashboard_timestamp(payload.get("latest_timestamp"))
    alert_count = _safe_int(payload.get("alert_count"))
    negative_alert_count = _safe_int(payload.get("negative_alert_count"))
    available_batches = list(payload.get("available_batches", []))
    stock_pool_health = _normalize_stock_pool_health(payload.get("stock_pool_health"))
    stock_pool_priority_variant = _resolve_stock_pool_priority_variant(
        variant_specs,
        stock_pool_health,
    )

    if stock_pool_priority_variant:
        return stock_pool_priority_variant

    if latest_timestamp is not None:
        if latest_timestamp.hour >= 14 and len(available_batches) >= 2:
            return "business_cn" if "business_cn" in variant_specs else DEFAULT_DASHBOARD_VARIANT
        if latest_timestamp.hour < 10 or alert_count > 0 or negative_alert_count > 0:
            return "compact" if "compact" in variant_specs else DEFAULT_DASHBOARD_VARIANT

    if len(available_batches) >= 3 and alert_count <= 0:
        return "business_cn" if "business_cn" in variant_specs else DEFAULT_DASHBOARD_VARIANT
    if alert_count > 0 or negative_alert_count > 0:
        return "compact" if "compact" in variant_specs else DEFAULT_DASHBOARD_VARIANT
    return DEFAULT_DASHBOARD_VARIANT


def _parse_dashboard_timestamp(value: object) -> datetime | None:
    """Parse dashboard timestamps using the local batch format."""
    if not isinstance(value, str):
        return None
    raw_value = value.strip()
    if not raw_value:
        return None
    try:
        return datetime.strptime(raw_value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _safe_int(value: object) -> int:
    """Return a safe integer for lightweight recommendation rules."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: object, *, fallback: object = 0.0) -> float:
    """Return a safe float for lightweight presentation-rule matching."""
    try:
        return float(value if value not in (None, "") else fallback or 0.0)
    except (TypeError, ValueError):
        try:
            return float(fallback or 0.0)
        except (TypeError, ValueError):
            return 0.0


def _build_time_phase_override_options() -> list[str]:
    """Return stable option keys for manual time-phase override control."""
    return ["auto", "compact", "default", "business_cn"]


def _resolve_time_phase_override_key(value: object) -> str:
    """Normalize one manual time-phase override key to a safe supported value."""
    normalized_value = str(value or "").strip()
    if normalized_value in _build_time_phase_override_options():
        return normalized_value
    return "auto"


def _resolve_time_phase_override_label(
    override_key: str,
    *,
    copy_variant: str,
    auto_label: str,
) -> str:
    """Resolve one user-facing label for the manual time-phase override selector."""
    normalized_key = _resolve_time_phase_override_key(override_key)
    if normalized_key == "auto":
        return str(auto_label).strip() or "Auto"
    phase_specs = build_effective_time_phase_specs(copy_variant)
    return str(dict(phase_specs.get(normalized_key, {})).get("label", normalized_key)).strip()


def _build_view_mode_note_markdown(
    note_spec: dict[str, object],
    *,
    panel_density: str,
    task_template: dict[str, object] | None = None,
    time_phase: dict[str, object] | None = None,
    time_phase_override_key: str = "auto",
    role_strategy: dict[str, object] | None = None,
    recommendation_note: str = "",
    priority_action_note: str = "",
    home_header_style: dict[str, object] | None = None,
) -> str:
    """Build a small first-screen note that explains the selected dashboard mode."""
    tone = str(note_spec.get("tone", "neutral")).strip() or "neutral"
    label = str(note_spec.get("summary_label", "view mode")).strip() or "view mode"
    title = str(note_spec.get("title", "")).strip()
    body = str(note_spec.get("body", "")).strip()
    supporting_copy = str(note_spec.get("supporting_copy", "")).strip()
    header_style = home_header_style or build_home_header_style_spec()
    copy_variant = (
        "business_cn"
        if str(note_spec.get("summary_label", "")).strip() == "\u89c6\u56fe\u6a21\u5f0f"
        else "default"
    )
    task_template_body = _build_task_template_summary_text(
        task_template or {},
        copy_variant=copy_variant,
    )
    time_phase_body = _build_time_phase_summary_text(
        time_phase or {},
        copy_variant=copy_variant,
        phase_override_key=time_phase_override_key,
    )
    role_strategy_body = _build_role_strategy_summary_text(
        role_strategy or {},
        copy_variant=copy_variant,
    )
    primary_body = title if not body else f"{title} | {body}"
    if task_template_body:
        supporting_copy = (
            f"{supporting_copy}\n{task_template_body}" if supporting_copy else task_template_body
        )
    if time_phase_body:
        supporting_copy = (
            f"{supporting_copy}\n{time_phase_body}" if supporting_copy else time_phase_body
        )
    if role_strategy_body:
        supporting_copy = (
            f"{supporting_copy}\n{role_strategy_body}" if supporting_copy else role_strategy_body
        )
    recommendation_note = recommendation_note.strip()
    if recommendation_note:
        supporting_copy = (
            f"{supporting_copy}\n{recommendation_note}"
            if supporting_copy
            else recommendation_note
        )
    priority_action_note = priority_action_note.strip()
    if priority_action_note:
        supporting_copy = (
            f"{supporting_copy}\n{priority_action_note}"
            if supporting_copy
            else priority_action_note
        )
    return _build_intro_panel_markdown(
        tone=tone,
        label=label,
        body=primary_body,
        panel_density=panel_density,
        detail_label=str(header_style.get("detail_label", "header details")),
        supporting_body=supporting_copy,
    )


def _build_control_band_markdown(
    note_spec: dict[str, object],
    *,
    payload: dict[str, object] | None = None,
    selected_batch: object,
    database_caption: str,
    copy_variant: str,
    control_band_layout: list[object] | None,
    panel_density: str,
    task_template: dict[str, object] | None = None,
    time_phase: dict[str, object] | None = None,
    time_phase_override_key: str = "auto",
    role_strategy: dict[str, object] | None = None,
    recommendation_note: str = "",
    priority_action_note: str = "",
    priority_action_profile: dict[str, str] | None = None,
    priority_action_sections: list[str] | None = None,
    priority_action_locations: dict[str, str] | None = None,
    home_header_style: dict[str, object] | None = None,
) -> str:
    """Build the unified first-screen control band for mode, batch, and source context."""
    control_spec = build_control_band_specs(copy_variant)
    header_style = home_header_style or build_home_header_style_spec()
    batch_value = "" if selected_batch in (None, "") else str(selected_batch).strip()
    batch_body = (
        str(control_spec.get("batch_body_template", "Current batch | {selected_batch}")).format(
            selected_batch=batch_value,
        )
        if batch_value
        else str(
            control_spec.get("batch_empty_body", "Current batch | Latest available snapshot")
        ).strip()
    )
    quote_source = str(dict(payload or {}).get("quote_source_display", "")).strip()
    source_template_key = (
        "source_with_quote_body_template"
        if quote_source
        else "source_body_template"
    )
    source_body = str(
        control_spec.get(source_template_key, "Database | {database_caption}")
    ).format(
        database_caption=str(database_caption).strip(),
        quote_source=quote_source,
    )
    slot_markdowns = {
        "view_mode": _build_view_mode_note_markdown(
            note_spec,
            panel_density=panel_density,
            task_template=task_template,
            time_phase=time_phase,
            time_phase_override_key=time_phase_override_key,
            role_strategy=role_strategy,
            recommendation_note=recommendation_note,
            priority_action_note=priority_action_note,
            home_header_style=header_style,
        ),
        "action_summary": _build_action_summary_markdown(
            panel_density=panel_density,
            recommendation_note=recommendation_note,
            priority_action_note=priority_action_note,
            priority_action_profile=dict(priority_action_profile or {}),
            priority_action_sections=list(priority_action_sections or []),
            priority_action_locations=dict(priority_action_locations or {}),
            payload=dict(payload or {}),
            time_phase=dict(time_phase or {}),
            copy_variant=copy_variant,
            detail_label=str(header_style.get("detail_label", "header details")),
        ),
        "batch_focus": _build_intro_panel_markdown(
            tone="info",
            label=str(control_spec.get("batch_label", "batch focus")),
            body=batch_body,
            panel_density=panel_density,
            detail_label=str(header_style.get("detail_label", "header details")),
            supporting_body=str(control_spec.get("batch_supporting_copy", "")).strip(),
        ),
        "data_source": _build_intro_panel_markdown(
            tone="neutral",
            label=str(control_spec.get("source_label", "data source")),
            body=source_body,
            panel_density=panel_density,
            detail_label=str(header_style.get("detail_label", "header details")),
            supporting_body=str(control_spec.get("source_supporting_copy", "")).strip(),
        ),
    }
    ordered_slots = [
        str(slot).strip()
        for slot in (
            control_band_layout
            or ("view_mode", "action_summary", "batch_focus", "data_source")
        )
        if str(slot).strip() in slot_markdowns
    ]
    if not ordered_slots:
        ordered_slots = ["view_mode", "action_summary", "batch_focus", "data_source"]
    return "".join(slot_markdowns[slot] for slot in ordered_slots)


def _filter_page_layout_sections(
    page_layout: list[dict[str, str]],
    *,
    excluded_section_keys: set[str],
) -> list[dict[str, str]]:
    """Return page-layout rows excluding sections that moved into the home header."""
    return [
        dict(section)
        for section in page_layout
        if str(section.get("section_key", "")).strip() not in excluded_section_keys
    ]


def _apply_role_strategy_to_page_layout(
    page_layout: list[dict[str, str]],
    *,
    role_strategy: dict[str, object],
) -> list[dict[str, str]]:
    """Reorder or hide homepage sections based on role and section strategy."""
    hidden_roles = {
        str(role_key).strip()
        for role_key in list(role_strategy.get("hidden_roles", []))
        if str(role_key).strip()
    }
    deferred_roles = {
        str(role_key).strip()
        for role_key in list(role_strategy.get("deferred_roles", []))
        if str(role_key).strip()
    }
    pinned_sections = {
        str(section_key).strip()
        for section_key in list(role_strategy.get("pinned_sections", []))
        if str(section_key).strip()
    }
    deferred_section_keys = {
        str(section_key).strip()
        for section_key in list(role_strategy.get("deferred_sections", []))
        if str(section_key).strip()
    }
    hidden_section_keys = {
        str(section_key).strip()
        for section_key in list(role_strategy.get("hidden_sections", []))
        if str(section_key).strip()
    }
    visible_sections = [
        dict(section)
        for section in page_layout
        if str(section.get("section_key", "")).strip() not in hidden_section_keys
        and str(section.get("section_role_key", "")).strip() not in hidden_roles
    ]
    pinned_items: list[dict[str, str]] = []
    immediate_sections: list[dict[str, str]] = []
    deferred_sections: list[dict[str, str]] = []
    for section in visible_sections:
        section_key = str(section.get("section_key", "")).strip()
        section_role_key = str(section.get("section_role_key", "")).strip()
        if section_key and section_key in pinned_sections:
            pinned_items.append(section)
            continue
        if section_key and section_key in deferred_section_keys:
            deferred_sections.append(section)
            continue
        if section_role_key and section_role_key in deferred_roles:
            deferred_sections.append(section)
            continue
        immediate_sections.append(section)
    return (
        _sort_page_layout_sections_by_priority(pinned_items)
        + _sort_page_layout_sections_by_priority(immediate_sections)
        + _sort_page_layout_sections_by_priority(deferred_sections)
    )


def _merge_layout_strategy(
    role_strategy: dict[str, object],
    time_phase: dict[str, object],
) -> dict[str, object]:
    """Merge role strategy and time-phase behavior into one effective layout strategy."""

    def merge_unique_lists(*values: object) -> list[str]:
        merged: list[str] = []
        seen: set[str] = set()
        for value in values:
            for item in list(value or []):
                normalized_item = str(item).strip()
                if not normalized_item or normalized_item in seen:
                    continue
                seen.add(normalized_item)
                merged.append(normalized_item)
        return merged

    merged_strategy = dict(role_strategy)
    merged_strategy["primary_roles"] = merge_unique_lists(
        role_strategy.get("primary_roles", []),
        time_phase.get("primary_roles", []),
    )
    merged_strategy["secondary_roles"] = merge_unique_lists(
        role_strategy.get("secondary_roles", []),
        time_phase.get("secondary_roles", []),
    )
    merged_strategy["deferred_roles"] = merge_unique_lists(
        role_strategy.get("deferred_roles", []),
        time_phase.get("deferred_roles", []),
    )
    merged_strategy["hidden_roles"] = merge_unique_lists(
        role_strategy.get("hidden_roles", []),
        time_phase.get("hidden_roles", []),
    )
    merged_strategy["pinned_sections"] = merge_unique_lists(
        role_strategy.get("pinned_sections", []),
        time_phase.get("pinned_sections", []),
    )
    merged_strategy["deferred_sections"] = merge_unique_lists(
        role_strategy.get("deferred_sections", []),
        time_phase.get("deferred_sections", []),
    )
    merged_strategy["hidden_sections"] = merge_unique_lists(
        role_strategy.get("hidden_sections", []),
        time_phase.get("hidden_sections", []),
    )
    return merged_strategy


def _sort_page_layout_sections_by_priority(
    sections: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Sort one page-layout bucket by explicit module priority, keeping original ties stable."""
    indexed_sections = list(enumerate(sections))
    sorted_sections = sorted(
        indexed_sections,
        key=lambda item: (
            _parse_module_priority(item[1].get("module_priority")),
            item[0],
        ),
    )
    return [dict(section) for _index, section in sorted_sections]


def _parse_module_priority(raw_value: object) -> int:
    """Parse module-priority metadata into a stable integer sort key."""
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError):
        return 99


def _render_home_header(
    st: object,
    payload: dict[str, object],
    *,
    home_header_layout: list[object] | None,
    home_header_style: dict[str, object] | None,
    view_mode_note: dict[str, object],
    task_template: dict[str, object] | None,
    time_phase: dict[str, object] | None,
    time_phase_override_key: str = "auto",
    role_strategy: dict[str, object] | None,
    recommendation_note: str,
    priority_action_note: str,
    priority_action_sections: list[str] | None,
    priority_action_locations: dict[str, str] | None,
    selected_batch: object,
    database_caption: str,
    control_band_copy_variant: str,
    control_band_layout: list[object] | None,
    kpi_copy_variant: str,
    kpi_summary_layout: dict[str, object] | None,
    panel_density: str,
    priority_action_profile: dict[str, str] | None = None,
) -> None:
    """Render the unified first-screen header framework for the homepage."""
    header_style = home_header_style or build_home_header_style_spec()
    ordered_slots = [
        str(slot).strip()
        for slot in (home_header_layout or ("control_band", "kpi"))
        if str(slot).strip() in {"control_band", "kpi"}
    ]
    if not ordered_slots:
        ordered_slots = ["control_band", "kpi"]
    support_key = (
        "compact_supporting_copy"
        if panel_density == "compact"
        else "supporting_copy"
    )
    st.markdown(
        _build_intro_panel_markdown(
            tone=str(header_style.get("default_tone", "neutral")),
            label=str(header_style.get("header_label", "home header")),
            body=str(header_style.get("header_body", "First-screen workspace entry")),
            panel_density=panel_density,
            detail_label=str(header_style.get("detail_label", "header details")),
            supporting_body=str(header_style.get(support_key, "")).strip(),
        ),
        unsafe_allow_html=True,
    )
    for slot in ordered_slots:
        if slot == "control_band":
            st.markdown(
                _build_control_band_markdown(
                    view_mode_note,
                    payload=payload,
                    selected_batch=selected_batch,
                    database_caption=database_caption,
                    copy_variant=control_band_copy_variant,
                    control_band_layout=control_band_layout,
                    panel_density=panel_density,
                    task_template=task_template,
                    time_phase=time_phase,
                    time_phase_override_key=time_phase_override_key,
                    role_strategy=role_strategy,
                    recommendation_note=recommendation_note,
                    priority_action_note=priority_action_note,
                    priority_action_profile=priority_action_profile,
                    priority_action_sections=priority_action_sections,
                    priority_action_locations=priority_action_locations,
                    home_header_style=header_style,
                ),
                unsafe_allow_html=True,
            )
            continue
        if slot == "kpi":
            _render_kpi_cards(
                st,
                payload,
                copy_variant=kpi_copy_variant,
                panel_density=panel_density,
                kpi_summary_layout=kpi_summary_layout,
            )


def _build_dashboard_variant_recommendation_note(
    *,
    selected_variant_key: str,
    recommended_variant_key: str,
    payload: dict[str, object] | None,
    variant_specs: dict[str, dict[str, object]],
) -> str:
    """Build a compact explanation for the current automatic mode recommendation."""
    recommended_label = _resolve_variant_label(variant_specs, recommended_variant_key)
    selected_label = _resolve_variant_label(variant_specs, selected_variant_key)
    reason = _build_dashboard_variant_recommendation_reason(payload)
    if not reason:
        return ""
    if selected_variant_key == recommended_variant_key:
        return f"Recommendation: {recommended_label} now. Reason: {reason}"
    return (
        f"System suggestion: {recommended_label} now. "
        f"Current view stays on {selected_label}. Reason: {reason}"
    )


def _build_dashboard_variant_recommendation_reason(
    payload: dict[str, object] | None,
) -> str:
    """Summarize the explicit rule that drove the current recommendation."""
    if not payload:
        return ""

    latest_timestamp = _parse_dashboard_timestamp(payload.get("latest_timestamp"))
    alert_count = _safe_int(payload.get("alert_count"))
    negative_alert_count = _safe_int(payload.get("negative_alert_count"))
    available_batches = list(payload.get("available_batches", []))
    stock_pool_health = _normalize_stock_pool_health(payload.get("stock_pool_health"))

    stock_pool_reason = _build_stock_pool_recommendation_reason(stock_pool_health)
    if stock_pool_reason:
        return stock_pool_reason

    if latest_timestamp is not None and latest_timestamp.hour >= 14 and len(available_batches) >= 2:
        return "late-session batches are available, so review mode is more useful"
    if latest_timestamp is not None and latest_timestamp.hour < 10:
        return "this is still near the open, so fast prioritization is more useful"
    if negative_alert_count > 0:
        return "negative alerts are active, so quick risk review should stay forward"
    if alert_count > 0:
        return "active alerts exist, so a fast scan mode should stay forward"
    if len(available_batches) >= 3:
        return "multiple saved batches are available, so comparison and review become more valuable"
    return "the session is relatively quiet, so the balanced default view is enough"


def _build_dashboard_priority_action_note(
    *,
    selected_variant_key: str,
    recommended_variant_key: str,
    payload: dict[str, object] | None,
    copy_variant: str,
) -> str:
    """Build a small first-step action prompt aligned with the current mode suggestion."""
    scenario_key = _resolve_priority_action_scenario(
        selected_variant_key=selected_variant_key,
        recommended_variant_key=recommended_variant_key,
        payload=payload,
    )
    specs = build_priority_action_profile_specs(copy_variant)
    fallback_spec = dict(specs.get("baseline_review", {}))
    resolved_spec = dict(specs.get(scenario_key, fallback_spec))
    return str(resolved_spec.get("first_step_note", "")).strip()


def _resolve_priority_action_scenario(
    *,
    selected_variant_key: str,
    recommended_variant_key: str,
    payload: dict[str, object] | None,
) -> str:
    """Resolve the current homepage action scenario before mapping it to copy or layout."""
    stock_pool_health = _normalize_stock_pool_health((payload or {}).get("stock_pool_health"))
    stock_pool_reason = _build_stock_pool_recommendation_reason(stock_pool_health)
    available_batches = list((payload or {}).get("available_batches", []))
    latest_timestamp = _parse_dashboard_timestamp((payload or {}).get("latest_timestamp"))
    alert_count = _safe_int((payload or {}).get("alert_count"))
    negative_alert_count = _safe_int((payload or {}).get("negative_alert_count"))
    today_priority_summary = dict((payload or {}).get("today_priority_summary", {}))
    today_priority_count = _safe_int(today_priority_summary.get("shown_items"))

    if stock_pool_reason:
        if "blocking" in stock_pool_reason:
            return "stock_pool_blocking_review"
        if "drift" in stock_pool_reason:
            return "stock_pool_drift_review"
        return "stock_pool_health_review"

    if today_priority_count > 0:
        if negative_alert_count > 0:
            return "daily_priority_risk_review"
        return "daily_priority_review"

    if recommended_variant_key == "compact" or selected_variant_key == "compact":
        if negative_alert_count > 0:
            return "risk_alert_scan"
        if (
            alert_count > 0
            and latest_timestamp is not None
            and 10 <= latest_timestamp.hour < 14
        ):
            return "intraday_alert_review"
        if alert_count > 0 or (latest_timestamp is not None and latest_timestamp.hour < 10):
            return "alert_scan"

    if recommended_variant_key == "business_cn" or selected_variant_key == "business_cn":
        if len(available_batches) >= 2:
            if latest_timestamp is not None and latest_timestamp.hour >= 14:
                return "close_review"
            return "batch_review"

    if latest_timestamp is not None and 10 <= latest_timestamp.hour < 14:
        return "midday_baseline_review"

    return "baseline_review"


def _build_action_summary_markdown(
    *,
    panel_density: str,
    recommendation_note: str,
    priority_action_note: str,
    priority_action_profile: dict[str, str] | None = None,
    priority_action_sections: list[str] | None = None,
    priority_action_locations: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
    time_phase: dict[str, object] | None = None,
    copy_variant: str,
    detail_label: str,
) -> str:
    """Build a compact action-summary card for the home-header control band."""
    label = "action summary" if copy_variant != "business_cn" else "\u52a8\u4f5c\u6458\u8981"
    title, supporting_body = _build_action_summary_content(
        recommendation_note=recommendation_note,
        priority_action_note=priority_action_note,
        priority_action_profile=priority_action_profile,
        priority_action_sections=priority_action_sections,
        priority_action_locations=priority_action_locations,
        payload=payload,
        time_phase=time_phase,
        copy_variant=copy_variant,
    )
    return _build_intro_panel_markdown(
        tone="accent",
        label=label,
        body=title,
        panel_density=panel_density,
        detail_label=detail_label,
        supporting_body=supporting_body,
    )


def _build_action_summary_content(
    *,
    recommendation_note: str,
    priority_action_note: str,
    priority_action_profile: dict[str, str] | None = None,
    priority_action_sections: list[str] | None = None,
    priority_action_locations: dict[str, str] | None = None,
    payload: dict[str, object] | None = None,
    time_phase: dict[str, object] | None = None,
    copy_variant: str,
) -> tuple[str, str]:
    """Resolve the compact action-summary title and supporting lines."""
    recommendation_body = recommendation_note.strip()
    priority_body = priority_action_note.strip()
    scenario_lines = _build_priority_action_profile_lines(
        dict(priority_action_profile or {}),
        copy_variant=copy_variant,
    )
    time_phase_lines = _build_priority_action_time_phase_lines(
        time_phase=dict(time_phase or {}),
        copy_variant=copy_variant,
    )
    content_focus_lines = _build_priority_action_content_focus_lines(
        priority_action_sections=list(priority_action_sections or []),
        payload=dict(payload or {}),
        copy_variant=copy_variant,
    )
    topline_context_lines = _build_priority_action_topline_context_lines(
        priority_action_sections=list(priority_action_sections or []),
        payload=dict(payload or {}),
        copy_variant=copy_variant,
    )
    module_lines = _build_action_module_lines(
        priority_action_sections=list(priority_action_sections or []),
        priority_action_locations=dict(priority_action_locations or {}),
        copy_variant=copy_variant,
    )

    if copy_variant == "business_cn":
        title = "\u5f53\u524d\u5efa\u8bae\u52a8\u4f5c"
        lines = []
        if priority_body:
            lines.append(priority_body)
        lines.extend(scenario_lines)
        lines.extend(time_phase_lines)
        lines.extend(module_lines)
        lines.extend(content_focus_lines)
        lines.extend(topline_context_lines)
        if recommendation_body:
            lines.append(f"\u63a8\u8350\u4f9d\u636e\uff1a{recommendation_body}")
        second_step = _build_secondary_action_line(
            priority_action_note=priority_body,
            priority_action_profile=priority_action_profile,
            copy_variant=copy_variant,
        )
        if second_step:
            lines.append(second_step)
        return title, "\n".join(lines)

    title = "Current Suggested Flow"
    lines = []
    if priority_body:
        lines.append(priority_body)
    lines.extend(scenario_lines)
    lines.extend(time_phase_lines)
    lines.extend(module_lines)
    lines.extend(content_focus_lines)
    lines.extend(topline_context_lines)
    if recommendation_body:
        lines.append(f"Recommendation basis: {recommendation_body}")
    second_step = _build_secondary_action_line(
        priority_action_note=priority_body,
        priority_action_profile=priority_action_profile,
        copy_variant=copy_variant,
    )
    if second_step:
        lines.append(second_step)
    return title, "\n".join(lines)


def _build_secondary_action_line(
    *,
    priority_action_note: str,
    priority_action_profile: dict[str, str] | None = None,
    copy_variant: str,
) -> str:
    """Build a small second-step action hint based on the first-step guidance."""
    configured_second_step = str(
        dict(priority_action_profile or {}).get("second_step_note", "")
    ).strip()
    if configured_second_step:
        return configured_second_step

    note = priority_action_note.casefold()
    if copy_variant == "business_cn":
        if "\u6700\u65b0\u98ce\u9669\u63d0\u9192" in priority_action_note or "\u6700\u65b0\u63d0\u9192" in priority_action_note:
            return "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u786e\u8ba4\u6838\u5fc3/\u5019\u9009/\u56de\u907f\u540d\u5355\u3002"
        if "\u76d1\u63a7\u6c60" in priority_action_note:
            return "\u7b2c\u4e8c\u6b65\uff1a\u7ed3\u5408\u6700\u65b0\u63d0\u9192\u4e0e\u6700\u5f3a\u677f\u5757\uff0c\u786e\u8ba4\u4eca\u5929\u662f\u5426\u9700\u8981\u8c03\u6574\u7814\u7a76\u91cd\u70b9\u3002"
        if "\u5df2\u4fdd\u5b58\u6279\u6b21" in priority_action_note:
            return "\u7b2c\u4e8c\u6b65\uff1a\u56de\u5230\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u7ed3\u8bba\uff0c\u786e\u8ba4\u54ea\u4e9b\u53d8\u5316\u503c\u5f97\u7ee7\u7eed\u8ddf\u8e2a\u3002"
        return "\u7b2c\u4e8c\u6b65\uff1a\u518d\u770b\u4e0b\u4e00\u65f6\u6bb5\u52a8\u4f5c\u4e0e\u6700\u5f3a\u677f\u5757\uff0c\u8865\u5168\u4e3b\u7ebf\u5224\u65ad\u3002"

    if "latest risk alerts" in note or "latest alerts" in note:
        return "Second step: review the next-session action summary to confirm core, candidate, and avoid names."
    if "stock-pool" in note:
        return "Second step: compare the latest alerts and strongest sector before widening the research conclusion."
    if "saved batches" in note:
        return "Second step: return to the next-session action summary and confirm which changes deserve follow-through."
    return "Second step: review the next-session action summary and strongest sector to complete the main-line read."


def _build_priority_action_profile(
    scenario_key: str,
    *,
    copy_variant: str,
    phase_key: str = "",
) -> dict[str, str]:
    """Build a lightweight reusable profile for the current priority-action scenario."""
    specs = build_priority_action_profile_specs(copy_variant)
    fallback_spec = dict(specs.get("baseline_review", {}))
    resolved_spec = dict(specs.get(scenario_key, fallback_spec))
    phase_override_specs = build_priority_action_phase_profile_override_specs(copy_variant)
    resolved_phase_key = str(phase_key).strip() or "default"
    scenario_phase_overrides = dict(phase_override_specs.get(resolved_phase_key, {}))
    resolved_spec.update(dict(scenario_phase_overrides.get(scenario_key, {})))
    return {
        "scenario": str(resolved_spec.get("scenario", "")).strip(),
        "applicable_session": str(resolved_spec.get("applicable_session", "")).strip(),
        "objective": str(resolved_spec.get("objective", "")).strip(),
        "focus_points": str(resolved_spec.get("focus_points", "")).strip(),
        "reading_order": str(resolved_spec.get("reading_order", "")).strip(),
        "reading_pace": str(resolved_spec.get("reading_pace", "")).strip(),
        "second_step_note": str(resolved_spec.get("second_step_note", "")).strip(),
    }


def _build_priority_action_profile_lines(
    profile: dict[str, str],
    *,
    copy_variant: str,
) -> list[str]:
    """Build reusable scenario-description lines for the action-summary card."""
    scenario = str(profile.get("scenario", "")).strip()
    applicable_session = str(profile.get("applicable_session", "")).strip()
    objective = str(profile.get("objective", "")).strip()
    focus_points = str(profile.get("focus_points", "")).strip()
    reading_order = str(profile.get("reading_order", "")).strip()
    reading_pace = str(profile.get("reading_pace", "")).strip()
    lines: list[str] = []
    if copy_variant == "business_cn":
        if scenario:
            lines.append(f"\u5f53\u524d\u573a\u666f\uff1a{scenario}")
        if applicable_session:
            lines.append(f"\u9002\u7528\u65f6\u6bb5\uff1a{applicable_session}")
        if objective:
            lines.append(f"\u5f53\u524d\u76ee\u6807\uff1a{objective}")
        if focus_points:
            lines.append(f"\u63a8\u8350\u5173\u6ce8\uff1a{focus_points}")
        if reading_order:
            lines.append(f"\u5efa\u8bae\u987a\u5e8f\uff1a{reading_order}")
        if reading_pace:
            lines.append(f"\u9605\u8bfb\u8282\u594f\uff1a{reading_pace}")
        return lines
    if scenario:
        lines.append(f"Current scenario: {scenario}")
    if applicable_session:
        lines.append(f"When to use: {applicable_session}")
    if objective:
        lines.append(f"Current objective: {objective}")
    if focus_points:
        lines.append(f"Priority focus: {focus_points}")
    if reading_order:
        lines.append(f"Suggested order: {reading_order}")
    if reading_pace:
        lines.append(f"Reading pace: {reading_pace}")
    return lines


def _build_action_module_lines(
    *,
    priority_action_sections: list[str],
    priority_action_locations: dict[str, str],
    copy_variant: str,
) -> list[str]:
    """Build short module-mapping lines for the action-summary card."""
    copy_specs = build_priority_action_module_copy_specs(copy_variant)
    normalized_sections = [
        str(section_key).strip()
        for section_key in priority_action_sections
        if str(section_key).strip()
    ]
    if not normalized_sections:
        return []

    lines: list[str] = []
    primary_label = _resolve_action_section_label(normalized_sections[0], copy_variant)
    lines.append(
        str(copy_specs.get("step_1_line_template", "Step 1: Open {label}")).format(
            label=primary_label
        )
    )
    primary_location = str(priority_action_locations.get(normalized_sections[0], "")).strip()
    if primary_location:
        lines.append(
            str(copy_specs.get("step_1_location_template", "Step 1 location: {location}")).format(
                location=primary_location
            )
        )
    lines.append(
        str(copy_specs.get("step_1_jump_template", "Step 1 jump: {link}")).format(
            link=_build_action_anchor_link(normalized_sections[0], copy_variant=copy_variant)
        )
    )

    if len(normalized_sections) >= 2:
        followup_label = _resolve_action_section_label(normalized_sections[1], copy_variant)
        lines.append(
            str(copy_specs.get("step_2_line_template", "Step 2: Then review {label}")).format(
                label=followup_label
            )
        )
        followup_location = str(priority_action_locations.get(normalized_sections[1], "")).strip()
        if followup_location:
            lines.append(
                str(copy_specs.get("step_2_location_template", "Step 2 location: {location}")).format(
                    location=followup_location
                )
            )
        lines.append(
            str(copy_specs.get("step_2_jump_template", "Step 2 jump: {link}")).format(
                link=_build_action_anchor_link(normalized_sections[1], copy_variant=copy_variant)
            )
        )
    return lines


def _build_section_anchor_id(section_key: str) -> str:
    """Build a stable in-page anchor id for one homepage section."""
    normalized_key = str(section_key).strip().replace("_", "-")
    return f"section-{normalized_key}" if normalized_key else "section"


def _build_primary_group_anchor_id(section_key: str) -> str:
    """Build a stable in-page anchor id for the first core group inside one section."""
    section_anchor_id = _build_section_anchor_id(section_key)
    return f"{section_anchor_id}-primary" if section_anchor_id else ""


def _supports_primary_group_anchor(section_key: str) -> bool:
    """Return whether a section can expose a first-group anchor within grouped content."""
    return str(section_key).strip() in {
        "strongest_sector",
        "leader_summary",
        "latest_alerts",
        "saved_batches",
        "next_session_action",
        "today_priority_summary",
    }


def _build_action_anchor_link(
    section_key: str,
    *,
    copy_variant: str,
) -> str:
    """Build a lightweight jump link that points to one homepage section anchor."""
    anchor_id = _build_section_anchor_id(section_key)
    if _supports_primary_group_anchor(section_key):
        anchor_id = _build_primary_group_anchor_id(section_key)
    if copy_variant == "business_cn":
        return f"[跳到对应模块](#{anchor_id})"
    return f"[Jump to section](#{anchor_id})"


def _build_action_anchor_link(
    section_key: str,
    *,
    copy_variant: str,
) -> str:
    """Build a lightweight jump link that points to one homepage section anchor."""
    copy_specs = build_priority_action_module_copy_specs(copy_variant)
    anchor_id = _build_section_anchor_id(section_key)
    if _supports_primary_group_anchor(section_key):
        anchor_id = _build_primary_group_anchor_id(section_key)
    jump_link_label = str(copy_specs.get("jump_link_label", "Jump to section")).strip()
    return f"[{jump_link_label}](#{anchor_id})"


def _build_priority_action_content_focus_lines(
    *,
    priority_action_sections: list[str],
    payload: dict[str, object] | None = None,
    copy_variant: str,
) -> list[str]:
    """Build lightweight content-level reading anchors for the first priority module."""
    copy_specs = build_priority_action_focus_copy_specs(copy_variant)
    normalized_sections = [
        str(section_key).strip()
        for section_key in priority_action_sections
        if str(section_key).strip()
    ]
    if not normalized_sections:
        return []

    primary_section_key = normalized_sections[0]
    content_specs = build_content_section_specs()
    spec = dict(content_specs.get(primary_section_key, {}))
    if not spec:
        return []
    resolved_spec = _resolve_spec_copy_variant(
        {
            **spec,
            "copy_variant": copy_variant,
        },
        merge_keys=(
            "title",
            "action_focus_hint",
            "action_focus_anchor_field",
            "action_focus_anchor_group",
            "action_focus_anchor_conclusion",
        ),
    )
    hint = str(resolved_spec.get("action_focus_hint", "")).strip()
    field_hint = str(resolved_spec.get("action_focus_anchor_field", "")).strip()
    group_hint = str(resolved_spec.get("action_focus_anchor_group", "")).strip()
    conclusion_hint = str(resolved_spec.get("action_focus_anchor_conclusion", "")).strip()
    dynamic_focus_overrides = _resolve_dynamic_action_focus_overrides(
        primary_section_key,
        payload=dict(payload or {}),
        copy_variant=copy_variant,
    )
    hint = str(dynamic_focus_overrides.get("hint", hint)).strip()
    field_hint = str(dynamic_focus_overrides.get("field_hint", field_hint)).strip()
    group_hint = str(dynamic_focus_overrides.get("group_hint", group_hint)).strip()
    conclusion_hint = str(
        dynamic_focus_overrides.get("conclusion_hint", conclusion_hint)
    ).strip()
    for prefix in ("First field: ", "First group: ", "First conclusion: "):
        if field_hint.startswith(prefix):
            field_hint = field_hint[len(prefix):].strip()
        if group_hint.startswith(prefix):
            group_hint = group_hint[len(prefix):].strip()
        if conclusion_hint.startswith(prefix):
            conclusion_hint = conclusion_hint[len(prefix):].strip()
    for prefix in ("\u5148\u770b\u5b57\u6bb5\uff1a", "\u5148\u770b\u5206\u7ec4\uff1a", "\u5148\u770b\u7ed3\u8bba\uff1a"):
        if field_hint.startswith(prefix):
            field_hint = field_hint[len(prefix):].strip()
        if group_hint.startswith(prefix):
            group_hint = group_hint[len(prefix):].strip()
        if conclusion_hint.startswith(prefix):
            conclusion_hint = conclusion_hint[len(prefix):].strip()
    for prefix in list(copy_specs.get("strip_prefixes", [])):
        normalized_prefix = str(prefix).strip()
        if not normalized_prefix:
            continue
        if field_hint.startswith(normalized_prefix):
            field_hint = field_hint[len(normalized_prefix):].strip()
        if group_hint.startswith(normalized_prefix):
            group_hint = group_hint[len(normalized_prefix):].strip()
        if conclusion_hint.startswith(normalized_prefix):
            conclusion_hint = conclusion_hint[len(normalized_prefix):].strip()
    lines: list[str] = []
    if hint:
        lines.append(
            str(copy_specs.get("hint_line_template", "In the first module, look for: {value}")).format(
                value=hint
            )
        )
    if field_hint:
        lines.append(
            str(copy_specs.get("field_line_template", "First field: {value}")).format(
                value=field_hint
            )
        )
    if group_hint:
        lines.append(
            str(copy_specs.get("group_line_template", "First group: {value}")).format(
                value=group_hint
            )
        )
    if conclusion_hint:
        lines.append(
            str(copy_specs.get("conclusion_line_template", "First conclusion: {value}")).format(
                value=conclusion_hint
            )
        )
    return lines


def _build_priority_action_time_phase_lines(
    *,
    time_phase: dict[str, object],
    copy_variant: str,
) -> list[str]:
    """Build compact market-phase guidance lines for the action-summary card."""
    copy_specs = build_priority_action_phase_copy_specs(copy_variant)
    label = str(time_phase.get("label", "")).strip()
    focus_points = [
        str(item).strip()
        for item in list(time_phase.get("focus_points", []))
        if str(item).strip()
    ]
    lines: list[str] = []
    if label:
        lines.append(
            str(copy_specs.get("phase_line_template", "Current phase: {label}")).format(
                label=label
            )
        )
    if focus_points:
        lines.append(
            str(copy_specs.get("phase_focus_line_template", "Phase focus: {value}")).format(
                value=" / ".join(focus_points)
            )
        )
    return lines


def _build_priority_action_topline_context_lines(
    *,
    priority_action_sections: list[str],
    payload: dict[str, object] | None,
    copy_variant: str,
) -> list[str]:
    """Build one lightweight top-line context line so first-read guidance explains why now."""
    copy_specs = build_priority_action_topline_copy_specs(copy_variant)
    normalized_sections = [
        str(section_key).strip()
        for section_key in priority_action_sections
        if str(section_key).strip()
    ]
    if not normalized_sections:
        return []
    primary_section_key = normalized_sections[0]
    resolved_payload = dict(payload or {})
    topline_specs = build_priority_action_topline_specs(copy_variant)
    context_prefix = str(
        dict(topline_specs.get(primary_section_key, {})).get("context_prefix", "")
    ).strip()
    context_body = ""
    if primary_section_key == "latest_alerts":
        context_body = str(resolved_payload.get("risk_summary", "")).strip()
        if context_body and context_prefix:
            return [
                str(copy_specs.get("context_line_template", "{prefix}: {value}")).format(
                    prefix=context_prefix,
                    value=context_body,
                )
            ]
        return []
    if primary_section_key == "today_priority_summary":
        summary_block = dict(resolved_payload.get("today_priority_summary", {}))
        context_body = str(summary_block.get("daily_conclusion", "")).strip()
        if not context_body:
            context_body = str(summary_block.get("core_summary", "")).strip()
        if context_body and context_prefix:
            return [
                str(copy_specs.get("context_line_template", "{prefix}: {value}")).format(
                    prefix=context_prefix,
                    value=context_body,
                )
            ]
        return []
    if primary_section_key in {"strongest_sector", "leader_summary", "next_session_action"}:
        context_body = str(resolved_payload.get("mainline_summary", "")).strip()
        if context_body and context_prefix:
            return [
                str(copy_specs.get("context_line_template", "{prefix}: {value}")).format(
                    prefix=context_prefix,
                    value=context_body,
                )
            ]
        return []
    if primary_section_key == "stock_pool_health":
        context_body = str(resolved_payload.get("stock_pool_drift_summary", "")).strip()
        if context_body and context_prefix:
            return [
                str(copy_specs.get("context_line_template", "{prefix}: {value}")).format(
                    prefix=context_prefix,
                    value=context_body,
                )
            ]
    return []


def _resolve_dynamic_action_focus_overrides(
    section_key: str,
    *,
    payload: dict[str, object],
    copy_variant: str,
) -> dict[str, str]:
    """Resolve lightweight action-focus overrides from live dashboard payload state."""
    normalized_section_key = str(section_key).strip()
    dynamic_specs = build_dynamic_action_focus_specs(copy_variant)
    section_spec = dict(dynamic_specs.get(normalized_section_key, {}))
    if not section_spec:
        return {}
    facts = _build_dynamic_action_focus_facts(
        normalized_section_key,
        payload=dict(payload or {}),
    )
    if not facts:
        return {}
    rule_spec = _resolve_dynamic_action_focus_rule_spec(
        section_spec,
        facts=facts,
    )
    if not rule_spec:
        return {}
    return _build_dynamic_action_focus_copy(rule_spec)


def _build_dynamic_action_focus_copy(spec: dict[str, object]) -> dict[str, str]:
    """Normalize one dynamic focus rule into the shared copy shape."""
    return {
        "hint": str(spec.get("hint", "")).strip(),
        "field_hint": str(spec.get("field_hint", "")).strip(),
        "group_hint": str(spec.get("group_hint", "")).strip(),
        "conclusion_hint": str(spec.get("conclusion_hint", "")).strip(),
    }


def _build_dynamic_action_focus_facts(
    section_key: str,
    *,
    payload: dict[str, object],
) -> dict[str, object]:
    """Build normalized rule-matching facts for one action-focus module."""
    normalized_section_key = str(section_key).strip()
    fact_specs = build_dynamic_action_focus_fact_specs()
    section_fact_spec = dict(fact_specs.get(normalized_section_key, {}))
    if not section_fact_spec:
        return {}
    container = _resolve_dynamic_action_focus_fact_container(
        section_fact_spec,
        payload=dict(payload or {}),
    )
    facts: dict[str, object] = {}
    for field_spec in list(section_fact_spec.get("fields", [])):
        if not isinstance(field_spec, dict):
            continue
        fact_key = str(field_spec.get("fact_key", "")).strip()
        if not fact_key:
            continue
        raw_value = _resolve_dynamic_action_focus_fact_raw_value(
            dict(field_spec),
            payload=dict(payload or {}),
            container=container,
        )
        facts[fact_key] = _transform_dynamic_action_focus_fact_value(
            raw_value,
            transform_key=str(field_spec.get("transform", "")).strip(),
            field_spec=dict(field_spec),
            fallback=field_spec.get("fallback"),
        )
    return facts


def _resolve_dynamic_action_focus_fact_container(
    section_fact_spec: dict[str, object],
    *,
    payload: dict[str, object],
) -> object:
    """Resolve one optional container object used by dynamic action-focus facts."""
    source_key = str(section_fact_spec.get("source_key", "")).strip()
    container_transform = str(section_fact_spec.get("container_transform", "")).strip()
    raw_container = payload.get(source_key) if source_key else payload
    if container_transform == "normalize_dict":
        return _normalize_dynamic_action_focus_dict(raw_container)
    if container_transform == "normalize_list":
        return _normalize_dynamic_action_focus_list(raw_container)
    return raw_container


def _resolve_dynamic_action_focus_fact_raw_value(
    field_spec: dict[str, object],
    *,
    payload: dict[str, object],
    container: object,
) -> object:
    """Resolve the raw source value for one dynamic action-focus fact field."""
    derive_from = str(field_spec.get("derive_from", "")).strip()
    if derive_from == "container":
        return container
    path = [
        str(path_part).strip()
        for path_part in list(field_spec.get("path", []))
        if str(path_part).strip()
    ]
    if path:
        return _resolve_dynamic_action_focus_nested_value(container, path)
    source_key = str(field_spec.get("source_key", "")).strip()
    if isinstance(container, dict) and source_key:
        return container.get(source_key)
    if source_key:
        return payload.get(source_key)
    return None


def _transform_dynamic_action_focus_fact_value(
    raw_value: object,
    *,
    transform_key: str,
    field_spec: dict[str, object] | None = None,
    fallback: object,
) -> object:
    """Apply one normalized transform to a dynamic action-focus fact value."""
    resolved_field_spec = field_spec or {}
    if transform_key == "safe_int":
        return _safe_int(raw_value if raw_value not in (None, "") else fallback)
    if transform_key == "safe_float":
        return _safe_float(raw_value, fallback=fallback)
    if transform_key == "normalized_lower_str":
        if raw_value is None:
            return str(fallback or "").strip().lower()
        return str(raw_value).strip().lower()
    if transform_key == "bool":
        return bool(raw_value)
    if transform_key == "len":
        try:
            return len(raw_value or [])
        except TypeError:
            return _safe_int(fallback)
    if transform_key == "first_item_field_lower":
        field_key = str(resolved_field_spec.get("field_key", "")).strip()
        if not field_key or not isinstance(raw_value, list) or not raw_value:
            return str(fallback or "").strip().lower()
        first_item = raw_value[0]
        if not isinstance(first_item, dict):
            return str(fallback or "").strip().lower()
        return str(first_item.get(field_key, fallback or "")).strip().lower()
    if transform_key == "count_items_with_field_value":
        field_key = str(resolved_field_spec.get("field_key", "")).strip()
        match_value = str(resolved_field_spec.get("match_value", "")).strip().lower()
        if not field_key or not isinstance(raw_value, list) or not match_value:
            return _safe_int(fallback)
        return sum(
            1
            for item in raw_value
            if isinstance(item, dict)
            and str(item.get(field_key, "")).strip().lower() == match_value
        )
    return raw_value if raw_value is not None else fallback


def _normalize_dynamic_action_focus_dict(value: object) -> dict[str, object]:
    """Normalize one dynamic action-focus container into a dictionary."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _normalize_dynamic_action_focus_list(value: object) -> list[object]:
    """Normalize one dynamic action-focus container into a list."""
    if isinstance(value, list):
        return list(value)
    return []


def _resolve_dynamic_action_focus_nested_value(
    container: object,
    path: list[str],
) -> object:
    """Resolve one nested value from a dict-like action-focus container."""
    current_value = container
    for path_part in path:
        if not isinstance(current_value, dict):
            return None
        current_value = current_value.get(path_part)
    return current_value


def _resolve_dynamic_action_focus_rule_spec(
    section_spec: dict[str, object],
    *,
    facts: dict[str, object],
) -> dict[str, object]:
    """Resolve the first matching dynamic action-focus rule from configured rule order."""
    rule_order = [
        str(rule_name).strip()
        for rule_name in list(section_spec.get("rule_order", []))
        if str(rule_name).strip()
    ]
    for rule_name in rule_order:
        rule_spec = dict(section_spec.get(rule_name, {}))
        if rule_spec and _dynamic_action_focus_rule_matches(rule_spec, facts=facts):
            return rule_spec
    return {}


def _dynamic_action_focus_rule_matches(
    rule_spec: dict[str, object],
    *,
    facts: dict[str, object],
) -> bool:
    """Check whether one dynamic action-focus rule matches normalized facts."""
    conditions = [
        dict(condition)
        for condition in list(rule_spec.get("conditions", []))
        if isinstance(condition, dict)
    ]
    if not conditions:
        return False
    match_mode = str(rule_spec.get("match", "all")).strip().lower() or "all"
    condition_results = [
        _dynamic_action_focus_condition_matches(condition, facts=facts)
        for condition in conditions
    ]
    if match_mode == "any":
        return any(condition_results)
    return all(condition_results)


def _dynamic_action_focus_condition_matches(
    condition: dict[str, object],
    *,
    facts: dict[str, object],
) -> bool:
    """Evaluate one dynamic action-focus condition against normalized facts."""
    field_name = str(condition.get("field", "")).strip()
    operator = str(condition.get("op", "")).strip().lower()
    if not field_name or not operator:
        return False
    field_value = facts.get(field_name)
    if operator == "truthy":
        return bool(field_value)
    if operator == "in":
        allowed_values = {
            str(item).strip().lower()
            for item in list(condition.get("value", []))
            if str(item).strip()
        }
        return str(field_value).strip().lower() in allowed_values
    if operator == "startswith":
        prefix = str(condition.get("value", "")).strip().lower()
        return str(field_value or "").strip().lower().startswith(prefix)
    if operator == "gte":
        return float(field_value or 0) >= float(condition.get("value", 0) or 0)
    if operator == "gt":
        return float(field_value or 0) > float(condition.get("value", 0) or 0)
    if operator == "eq":
        return float(field_value or 0) == float(condition.get("value", 0) or 0)
    if operator == "lte":
        return float(field_value or 0) <= float(condition.get("value", 0) or 0)
    if operator == "gte_field":
        other_field = str(condition.get("value_field", "")).strip()
        return float(field_value or 0) >= float(facts.get(other_field, 0) or 0)
    if operator == "lte_field":
        other_field = str(condition.get("value_field", "")).strip()
        return float(field_value or 0) <= float(facts.get(other_field, 0) or 0)
    return False


def _resolve_action_section_label(section_key: str, copy_variant: str) -> str:
    """Resolve a readable action-summary label for one section key."""
    content_specs = build_content_section_specs()
    spec = dict(content_specs.get(section_key, {}))
    if not spec:
        return section_key

    resolved_spec = _resolve_spec_copy_variant(
        {
            **spec,
            "copy_variant": copy_variant,
        },
        merge_keys=("title",),
    )
    resolved_title = str(resolved_spec.get("title", "")).strip()
    if not resolved_title:
        return section_key
    if copy_variant == "business_cn":
        return f"{resolved_title}\uff08{section_key}\uff09"
    return f"{resolved_title} (`{section_key}`)"


def _build_priority_focus_labels(
    priority_action_sections: list[str],
    *,
    copy_variant: str,
) -> dict[str, str]:
    """Build lightweight per-section focus labels for current homepage action priorities."""
    normalized_sections = [
        str(section_key).strip()
        for section_key in priority_action_sections
        if str(section_key).strip()
    ]
    labels: dict[str, str] = {}
    if not normalized_sections:
        return labels

    if copy_variant == "business_cn":
        labels[normalized_sections[0]] = "1. \u7b2c 1 \u6b65\u91cd\u70b9\u6a21\u5757"
        if len(normalized_sections) >= 2:
            labels[normalized_sections[1]] = "2. \u7b2c 2 \u6b65\u8ddf\u8fdb\u6a21\u5757"
        return labels

    labels[normalized_sections[0]] = "1. Step 1 focus"
    if len(normalized_sections) >= 2:
        labels[normalized_sections[1]] = "2. Step 2 follow-up"
    return labels


def _build_priority_focus_tones(
    priority_action_sections: list[str],
) -> dict[str, str]:
    """Build lightweight tone overrides so the first two focus modules stand out visually."""
    normalized_sections = [
        str(section_key).strip()
        for section_key in priority_action_sections
        if str(section_key).strip()
    ]
    tones: dict[str, str] = {}
    if not normalized_sections:
        return tones
    tones[normalized_sections[0]] = "accent"
    if len(normalized_sections) >= 2:
        tones[normalized_sections[1]] = "warning"
    return tones


def _build_priority_action_locations(
    page_layout: list[dict[str, str]],
    *,
    priority_action_sections: list[str],
    copy_variant: str,
) -> dict[str, str]:
    """Build short location descriptions for priority-action modules from current page layout."""
    normalized_targets = {
        str(section_key).strip()
        for section_key in priority_action_sections
        if str(section_key).strip()
    }
    if not normalized_targets:
        return {}

    locations: dict[str, str] = {}
    for section in page_layout:
        section_key = str(section.get("section_key", "")).strip()
        if not section_key or section_key not in normalized_targets or section_key in locations:
            continue
        segment_title = str(section.get("segment_title", "")).strip()
        group_title = str(section.get("group_title", "")).strip()
        if copy_variant == "business_cn":
            if segment_title and group_title:
                locations[section_key] = f"{segment_title} > {group_title}"
            elif group_title:
                locations[section_key] = group_title
            else:
                locations[section_key] = segment_title
            continue
        if segment_title and group_title:
            locations[section_key] = f"{segment_title} > {group_title}"
        elif group_title:
            locations[section_key] = group_title
        else:
            locations[section_key] = segment_title
    return {key: value for key, value in locations.items() if value}

def _build_priority_action_layout_strategy(
    *,
    selected_variant_key: str,
    recommended_variant_key: str,
    payload: dict[str, object] | None,
) -> dict[str, object]:
    """Convert the first-step action recommendation into concrete section-order behavior."""
    action_sections = _resolve_priority_action_sections(
        selected_variant_key=selected_variant_key,
        recommended_variant_key=recommended_variant_key,
        payload=payload,
    )
    return {
        "pinned_sections": action_sections,
        "deferred_sections": _resolve_priority_action_deferred_sections(action_sections),
    }


def _resolve_priority_action_sections(
    *,
    selected_variant_key: str,
    recommended_variant_key: str,
    payload: dict[str, object] | None,
    phase_override_key: str = "",
) -> list[str]:
    """Resolve which homepage sections should move to the front for the current first step."""
    scenario_key = _resolve_priority_action_scenario(
        selected_variant_key=selected_variant_key,
        recommended_variant_key=recommended_variant_key,
        payload=payload,
    )
    scenario_sections = {
        "daily_priority_review": ["today_priority_summary", "next_session_action", "stock_pool_health"],
        "daily_priority_risk_review": ["today_priority_summary", "latest_alerts", "next_session_action"],
        "stock_pool_blocking_review": ["stock_pool_health", "latest_alerts", "next_session_action"],
        "stock_pool_drift_review": ["stock_pool_health", "saved_batches", "next_session_action"],
        "stock_pool_health_review": ["stock_pool_health", "next_session_action", "latest_alerts"],
        "risk_alert_scan": ["latest_alerts", "next_session_action", "stock_pool_health"],
        "alert_scan": ["latest_alerts", "next_session_action", "stock_pool_health"],
        "intraday_alert_review": ["latest_alerts", "strongest_sector", "next_session_action"],
        "batch_review": ["saved_batches", "next_session_action", "stock_pool_health"],
        "close_review": ["saved_batches", "strongest_sector", "next_session_action"],
        "baseline_review": ["strongest_sector", "stock_pool_health", "next_session_action"],
        "midday_baseline_review": ["strongest_sector", "leader_summary", "stock_pool_health"],
    }
    resolved_sections = list(
        scenario_sections.get(scenario_key, scenario_sections["baseline_review"])
    )
    phase_override_specs = build_priority_action_phase_override_specs()
    phase_key = _resolve_priority_action_phase_key(
        payload=payload,
        phase_override_key=phase_override_key,
    )
    phase_override = dict(phase_override_specs.get(phase_key, {}))
    scenario_override_sections = dict(phase_override.get("scenario_sections", {}))
    override_sections = scenario_override_sections.get(scenario_key)
    if isinstance(override_sections, list) and override_sections:
        return [str(section_key).strip() for section_key in override_sections if str(section_key).strip()]
    return resolved_sections


def _resolve_priority_action_phase_key(
    *,
    payload: dict[str, object] | None,
    phase_override_key: str = "",
) -> str:
    """Resolve the active action-summary time-phase key from real timestamp and batch state."""
    resolved_override_key = _resolve_time_phase_override_key(phase_override_key)
    if resolved_override_key != "auto":
        return resolved_override_key
    latest_timestamp = _parse_dashboard_timestamp((payload or {}).get("latest_timestamp"))
    alert_count = _safe_int((payload or {}).get("alert_count"))
    negative_alert_count = _safe_int((payload or {}).get("negative_alert_count"))
    available_batches = list((payload or {}).get("available_batches", []))

    if latest_timestamp is not None:
        if latest_timestamp.hour >= 14 and len(available_batches) >= 2:
            return "business_cn"
        if latest_timestamp.hour < 10 or alert_count > 0 or negative_alert_count > 0:
            return "compact"
        if 10 <= latest_timestamp.hour < 14:
            return "default"
    if len(available_batches) >= 2:
        return "business_cn"
    return "default"


def _resolve_effective_time_phase(
    *,
    payload: dict[str, object] | None,
    copy_variant: str,
    phase_override_key: str = "",
) -> dict[str, object]:
    """Resolve the effective time-phase spec from real data state plus UI locale."""
    phase_key = _resolve_priority_action_phase_key(
        payload=payload,
        phase_override_key=phase_override_key,
    )
    phase_specs = build_effective_time_phase_specs(copy_variant)
    return dict(phase_specs.get(phase_key, phase_specs["default"]))


def _resolve_priority_action_deferred_sections(
    pinned_sections: list[str],
) -> list[str]:
    """Push non-first-step archive/detail blocks slightly back when action focus is explicit."""
    deferred_candidates = [
        "saved_batches",
        "leader_summary",
        "top_movers",
        "sector_strength",
    ]
    return [section_key for section_key in deferred_candidates if section_key not in pinned_sections]


def _normalize_priority_action_sections_for_layout(
    page_layout: list[dict[str, object]],
    *,
    priority_action_sections: list[str],
) -> list[str]:
    """Keep only visible layout sections in the priority-action guidance stack."""
    available_section_keys = {
        str(section.get("section_key", "")).strip()
        for section in page_layout
        if str(section.get("section_key", "")).strip()
    }
    normalized_sections: list[str] = []
    seen_section_keys: set[str] = set()
    for section_key in priority_action_sections:
        normalized_key = str(section_key).strip()
        if (
            not normalized_key
            or normalized_key not in available_section_keys
            or normalized_key in seen_section_keys
        ):
            continue
        normalized_sections.append(normalized_key)
        seen_section_keys.add(normalized_key)
    return normalized_sections


def _resolve_variant_label(
    variant_specs: dict[str, dict[str, object]],
    variant_key: str,
) -> str:
    """Resolve a display label for one dashboard variant key."""
    variant = dict(variant_specs.get(variant_key, {}))
    return str(variant.get("label", variant_key)).strip() or variant_key


def _normalize_stock_pool_health(value: object) -> dict[str, object]:
    """Return a normalized stock-pool health payload for recommendation rules."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def _resolve_stock_pool_priority_variant(
    variant_specs: dict[str, dict[str, object]],
    stock_pool_health: dict[str, object],
) -> str:
    """Resolve whether stock-pool health should override time-based mode selection."""
    if not stock_pool_health:
        return ""
    if _build_stock_pool_recommendation_reason(stock_pool_health):
        return "business_cn" if "business_cn" in variant_specs else DEFAULT_DASHBOARD_VARIANT
    return ""


def _build_stock_pool_recommendation_reason(
    stock_pool_health: dict[str, object],
) -> str:
    """Explain when stock-pool health should push the homepage into review mode."""
    if not stock_pool_health:
        return ""

    status = str(stock_pool_health.get("status", "")).strip().lower()
    risk_level = str(stock_pool_health.get("risk_level", "")).strip().lower()
    comparison_tags = [
        str(tag).strip()
        for tag in list(stock_pool_health.get("comparison_tags", []))
        if str(tag).strip()
    ]
    meaningful_drift_tags = [
        tag
        for tag in comparison_tags
        if tag not in {"Awaiting baseline", "Structure Stable"}
    ]

    if status == "invalid" or risk_level == "blocking":
        return "stock-pool health is blocking, so validation and review should come first"
    if meaningful_drift_tags:
        return "stock-pool drift is active, so structure review should come first"
    if risk_level == "warning":
        return "stock-pool health shows warning signals, so validation should stay forward"
    return ""


def _render_kpi_cards(
    st: object,
    payload: dict[str, object],
    *,
    copy_variant: str,
    panel_density: str,
    kpi_summary_layout: dict[str, object] | None = None,
) -> None:
    """Render KPI cards from replaceable presentation specs."""
    specs = _resolve_kpi_card_specs(
        copy_variant,
        kpi_summary_layout=kpi_summary_layout,
    )
    style_spec = build_kpi_panel_style_spec(copy_variant)
    format_spec = build_kpi_value_format_spec()
    st.markdown(
        _build_kpi_section_header_markdown(
            panel_density=panel_density,
            style_spec=style_spec,
            body=str(style_spec.get("section_body", "Latest snapshot and alert counters")),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        _build_metric_group_markdown(
            tone="neutral",
            label="metric row",
            body=str(style_spec.get("metric_group_body", "KPI values")),
            panel_density=panel_density,
            style_spec=build_metric_group_style_spec(copy_variant),
        ),
        unsafe_allow_html=True,
    )
    columns = st.columns(len(specs))
    for column, spec in zip(columns, specs):
        value = _resolve_kpi_card_value(
            payload,
            spec,
            format_spec=format_spec,
        )
        column.markdown(
            _build_kpi_metric_panel_markdown(
                spec,
                panel_density=panel_density,
                style_spec=style_spec,
            ),
            unsafe_allow_html=True,
        )
        column.caption(_build_kpi_metric_caption(spec))
        column.metric(str(spec["label"]), str(value))


def _render_chart_block(
    st: object,
    payload: dict[str, object],
    spec: dict[str, object],
    *,
    panel_density: str,
    surface_copy_variant: str,
) -> None:
    """Render one chart/table block from replaceable presentation specs."""
    resolved_spec = _resolve_spec_copy_variant(
        spec,
        merge_keys=("title", "empty_message", "display_fields", "x_axis_label", "y_axis_label"),
    )
    chart_style_spec = build_summary_panel_style_spec(surface_copy_variant)
    st.markdown(
        _build_chart_panel_markdown(
            resolved_spec,
            panel_density=panel_density,
            style_spec=chart_style_spec,
        )
        ,
        unsafe_allow_html=True,
    )
    st.markdown(
        _build_chart_axes_markdown(
            resolved_spec,
            panel_density=panel_density,
            style_spec=chart_style_spec,
        ),
        unsafe_allow_html=True,
    )
    table_rows = payload.get(str(resolved_spec["table_key"]), [])
    chart_rows = payload.get(str(resolved_spec["data_key"]), [])
    if table_rows:
        st.dataframe(
            _build_table_rows_for_display(
                table_rows,
                spec=resolved_spec,
                format_spec=build_kpi_value_format_spec(),
            ),
            use_container_width=True,
        )
        if resolved_spec.get("chart_type") == "bar":
            st.bar_chart(
                chart_rows,
                x=str(resolved_spec["x_key"]),
                y=str(resolved_spec["y_key"]),
            )
    else:
        st.markdown(
            _build_empty_state_markdown(
                str(resolved_spec["empty_message"]),
                panel_density=panel_density,
                style_spec=chart_style_spec,
            ),
            unsafe_allow_html=True,
        )


def _render_content_block(st: object, payload: dict[str, object], spec: dict[str, object]) -> None:
    """Render one content block from replaceable presentation specs."""
    st.subheader(str(spec["title"]))
    value = payload.get(str(spec["data_key"]))
    if value in (None, "", [], {}):
        st.info(str(spec["empty_message"]))
        return

    render_type = str(spec["render_type"])
    if render_type == "text":
        st.write(value)
        return
    if render_type == "health_summary":
        _render_health_summary_block(st, value, spec)
        return
    if render_type == "spotlight_summary":
        _render_grouped_summary_block(
            st,
            _build_spotlight_summary_view_model(value, spec),
            spec,
        )
        return
    if render_type == "leader_grouped":
        _render_grouped_summary_block(
            st,
            _build_leader_grouped_view_model(value, spec),
            spec,
        )
        return
    if render_type == "next_session_action_grouped":
        _render_grouped_summary_block(
            st,
            _build_next_session_action_grouped_view_model(value, spec),
            spec,
        )
        return
    if render_type == "today_priority_grouped":
        _render_grouped_summary_block(
            st,
            _build_today_priority_grouped_view_model(value, spec),
            spec,
        )
        return
    if render_type == "alerts_grouped":
        _render_grouped_summary_block(
            st,
            _build_alerts_grouped_view_model(value, spec),
            spec,
        )
        return
    if render_type == "batch_list_grouped":
        _render_grouped_summary_block(
            st,
            _build_batch_list_grouped_view_model(value, spec),
            spec,
        )
        return
    if render_type == "key_value":
        st.json(value)
        return
    if render_type == "table":
        rows = value
        columns = spec.get("columns")
        if columns:
            rows = [
                {column: row.get(column) for column in columns}
                for row in value
            ]
        st.dataframe(rows, use_container_width=True)
        return
    if render_type == "list":
        st.write(value)
        return

    st.info(str(spec["empty_message"]))


def _render_health_summary_block(
    st: object,
    value: dict[str, object],
    spec: dict[str, object],
    *,
    panel_density: str,
    surface_copy_variant: str,
) -> None:
    """Render the stock-pool health block from a replaceable view model."""
    view_model = _build_health_summary_view_model(value, spec)
    metric_style_spec = build_metric_group_style_spec(surface_copy_variant)
    st.markdown(
        _build_health_summary_card_markdown(
            view_model,
            panel_density=panel_density,
            style_spec=build_summary_panel_style_spec(surface_copy_variant),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        _build_health_status_markdown(
            view_model,
            panel_density=panel_density,
            style_spec=build_summary_panel_style_spec(surface_copy_variant),
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        _build_health_readiness_markdown(
            view_model,
            panel_density=panel_density,
            style_spec=build_summary_panel_style_spec(surface_copy_variant),
        ),
        unsafe_allow_html=True,
    )

    st.caption(view_model["badge_text"])

    st.markdown(
        _build_metric_group_markdown(
            tone=str(view_model.get("tone", "neutral")),
            label="metric row",
            body=str(metric_style_spec.get("health_metrics_body", "Health metrics")),
            panel_density=panel_density,
            style_spec=metric_style_spec,
        ),
        unsafe_allow_html=True,
    )
    summary_columns = st.columns(len(view_model["summary_metrics"]))
    for column, metric in zip(summary_columns, view_model["summary_metrics"]):
        column.metric(
            str(metric["label"]),
            _format_kpi_metric_value(
                metric.get("value"),
                format_key=str(metric.get("format_key", "default")),
                format_spec=build_kpi_value_format_spec(),
            ),
        )

    _render_info_blocks(
        st,
        list(view_model.get("info_blocks", [])),
    )


def _render_grouped_summary_block(
    st: object,
    view_model: dict[str, object],
    spec: dict[str, object],
    *,
    panel_density: str,
    surface_copy_variant: str,
    focus_tone: str = "",
    first_group_anchor_id: str = "",
) -> None:
    """Render grouped summary blocks with shared card-like structure."""
    metric_style_spec = build_metric_group_style_spec(surface_copy_variant)
    header_markdown = _build_grouped_summary_card_markdown(
        view_model,
        panel_density=panel_density,
        style_spec=build_summary_panel_style_spec(surface_copy_variant),
    )
    if header_markdown:
        st.markdown(header_markdown, unsafe_allow_html=True)

    summary_metrics = list(view_model.get("summary_metrics", []))
    if summary_metrics:
        st.markdown(
            _build_metric_group_markdown(
                tone=str(view_model.get("tone", "neutral")),
                label="metric row",
                body=str(metric_style_spec.get("summary_metrics_body", "Summary metrics")),
                panel_density=panel_density,
                style_spec=metric_style_spec,
            ),
            unsafe_allow_html=True,
        )
        summary_columns = st.columns(len(summary_metrics))
        for column, metric in zip(summary_columns, summary_metrics):
            column.metric(
                str(metric["label"]),
                _format_kpi_metric_value(
                    metric.get("value"),
                    format_key=str(metric.get("format_key", "default")),
                    format_spec=build_kpi_value_format_spec(),
                ),
            )

    content_style_spec = build_content_panel_style_spec(surface_copy_variant)
    st.markdown(
        _build_content_detail_markdown(
            tone=str(view_model.get("tone", "neutral")),
            body=str(content_style_spec.get("grouped_detail_body", "Grouped detail rows")),
            panel_density=panel_density,
            style_spec=content_style_spec,
        ),
        unsafe_allow_html=True,
    )

    info_blocks = _resolve_grouped_summary_render_blocks(
        view_model,
        spec,
    )
    if info_blocks:
        _render_info_blocks(
            st,
            info_blocks,
            first_group_tone=focus_tone,
            surface_copy_variant=surface_copy_variant,
            first_group_anchor_id=first_group_anchor_id,
        )
        return

    st.markdown(
        _build_empty_state_markdown(
            str(spec["empty_message"]),
            panel_density=panel_density,
            style_spec=content_style_spec,
        ),
        unsafe_allow_html=True,
    )


def _build_grouped_summary_card_markdown(
    view_model: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared summary-card wrapper from grouped-section metadata."""
    header_markdown = _build_grouped_section_header_markdown(
        view_model,
        panel_density=panel_density,
        style_spec=style_spec,
    )
    if not header_markdown:
        return ""

    support_key = "compact_supporting_copy" if panel_density == "compact" else "supporting_copy"
    supporting_copy = str(style_spec.get(support_key, "")).strip()
    return header_markdown + _build_info_panel_markdown(
        tone=str(view_model.get("tone", style_spec.get("default_tone", "neutral"))),
        label=str(style_spec.get("details_label", "details")),
        body=supporting_copy,
        panel_density=panel_density,
        apply_density=False,
    )


def _build_health_summary_card_markdown(
    view_model: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared card wrapper for health-summary sections."""
    badge_text = str(view_model.get("badge_text", "")).strip()
    tone = str(view_model.get("tone", style_spec.get("default_tone", "neutral"))).strip()
    header_markdown = _build_info_panel_markdown(
        tone=tone,
        label=str(style_spec.get("health_label", "health")),
        body=badge_text,
        panel_density=panel_density,
    )
    risk_level = str(view_model.get("risk_level", "unknown")).strip().lower()
    support_key = f"health_supporting_copy_{risk_level}"
    return header_markdown + _build_info_panel_markdown(
        tone=tone,
        label=str(style_spec.get("details_label", "details")),
        body=str(
            style_spec.get(
                support_key,
                style_spec.get("health_supporting_copy", ""),
            )
        ).strip(),
        panel_density=panel_density,
        apply_density=False,
    )


def _build_health_status_markdown(
    view_model: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a shared status block for health-summary state messages."""
    tone = str(view_model.get("tone", "info")).strip()
    status_line = str(view_model.get("status_line", "")).strip()
    effective_style_spec = style_spec or build_summary_panel_style_spec()
    return _build_info_panel_markdown(
        tone=tone,
        label=str(effective_style_spec.get("status_label", "status")),
        body=status_line,
        panel_density=panel_density,
    )


def _build_health_readiness_markdown(
    view_model: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a dedicated readiness block for stock-pool health status."""
    tone = str(view_model.get("tone", "info")).strip()
    readiness_label = str(view_model.get("risk_label", "UNKNOWN")).strip()
    readiness_text = str(view_model.get("risk_text", "")).strip()
    structure_summary = str(view_model.get("structure_summary", "")).strip()
    extension_summary = str(view_model.get("extension_summary", "")).strip()
    risk_level = str(view_model.get("risk_level", "unknown")).strip().lower()
    body_lines = [f"{readiness_label} | {readiness_text}"]
    if structure_summary:
        body_lines.append(f"Structure: {structure_summary}")
    if extension_summary:
        body_lines.append(extension_summary)
    return _build_info_panel_markdown(
        tone=tone,
        label=str(style_spec.get("readiness_label", "readiness")),
        body="\n".join(body_lines),
        supporting_title=_build_tone_panel_title(
            "neutral",
            str(style_spec.get("details_label", "details")),
        ),
        supporting_body=str(
            style_spec.get(
                f"readiness_supporting_copy_{risk_level}",
                "",
            )
        ).strip(),
        panel_density=panel_density,
    )


def _build_empty_state_markdown(
    message: str,
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared empty-state block for no-data branches."""
    empty_message = str(message).strip()
    return _build_info_panel_markdown(
        tone="info",
        label=str(style_spec.get("empty_state_label", "empty state")),
        body=empty_message,
        supporting_title=_build_tone_panel_title(
            "neutral",
            str(style_spec.get("details_label", "details")),
        ),
        supporting_body=str(style_spec.get("empty_state_supporting_copy", "")).strip(),
        panel_density=panel_density,
    )


def _build_grouped_section_header_markdown(
    view_model: dict[str, object],
    *,
    panel_density: str = "comfortable",
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a reusable markdown header block from grouped-summary tone metadata."""
    tone_key = str(view_model.get("tone", "neutral")).strip().lower()
    badge_text = str(view_model.get("badge_text", "")).strip()
    if not badge_text:
        return ""
    effective_style_spec = style_spec or build_summary_panel_style_spec()
    panel_title = _build_tone_panel_title(
        tone_key,
        str(effective_style_spec.get("summary_label", "summary")),
    )
    return _build_panel_block_markdown(
        panel_title,
        _build_panel_body_text(badge_text, panel_density=panel_density),
    )


def _build_kpi_metric_caption(spec: dict[str, object]) -> str:
    """Build a lightweight tone caption for one KPI card."""
    tone_key = str(spec.get("tone", "neutral")).strip().lower()
    label = str(spec.get("caption", spec.get("label", ""))).strip()
    panel_title = _build_tone_panel_title(tone_key, "kpi")
    return f"{panel_title} | {label}"


def _apply_kpi_value_length_limit(value: object, *, max_length: int) -> str:
    """Clamp long KPI value text so copy-only cards can stay first-screen readable."""
    normalized_value = str(value).strip()
    if max_length <= 0 or len(normalized_value) <= max_length:
        return normalized_value
    if max_length <= 3:
        return normalized_value[:max_length]
    return normalized_value[: max_length - 3] + "..."


def _resolve_kpi_card_value(
    payload: dict[str, object],
    spec: dict[str, object],
    *,
    format_spec: dict[str, dict[str, object]],
) -> str:
    """Resolve one KPI card value using explicit numeric/text card typing."""
    raw_value = payload.get(str(spec["value_key"]), spec["empty_value"])
    card_type = str(spec.get("card_type", "numeric")).strip().lower() or "numeric"
    formatted_value = _format_kpi_metric_value(
        raw_value,
        format_key=str(spec.get("format_key", "default")),
        format_spec=format_spec,
    )
    if card_type == "text":
        return _apply_kpi_value_length_limit(
            formatted_value,
            max_length=int(spec.get("value_max_length", 0) or 0),
        )
    return str(formatted_value)


def _resolve_kpi_card_specs(
    copy_variant: str,
    *,
    kpi_summary_layout: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    """Resolve KPI card specs after applying summary-layout ordering and overrides."""
    raw_specs = build_kpi_card_specs(copy_variant)
    layout = dict(kpi_summary_layout or {})
    ordered_value_keys = [
        str(value_key).strip()
        for value_key in list(layout.get("card_order", []))
        if str(value_key).strip()
    ]
    variant_overrides = {
        str(value_key).strip(): str(variant_key).strip()
        for value_key, variant_key in dict(
            layout.get("card_variant_overrides", {})
        ).items()
        if str(value_key).strip() and str(variant_key).strip()
    }

    spec_map = {
        str(spec.get("value_key", "")).strip(): dict(spec)
        for spec in raw_specs
        if str(spec.get("value_key", "")).strip()
    }
    resolved_specs: list[dict[str, object]] = []
    consumed_keys: set[str] = set()

    for value_key in ordered_value_keys:
        spec = spec_map.get(value_key)
        if not spec:
            continue
        if value_key in variant_overrides:
            spec["copy_variant"] = variant_overrides[value_key]
        resolved_specs.append(
            _resolve_spec_copy_variant(
                spec,
                merge_keys=("label", "caption", "value_max_length", "tone"),
            )
        )
        consumed_keys.add(value_key)

    for spec in raw_specs:
        value_key = str(spec.get("value_key", "")).strip()
        if not value_key or value_key in consumed_keys:
            continue
        trailing_spec = dict(spec)
        if value_key in variant_overrides:
            trailing_spec["copy_variant"] = variant_overrides[value_key]
        resolved_specs.append(
            _resolve_spec_copy_variant(
                trailing_spec,
                merge_keys=("label", "caption", "value_max_length", "tone"),
            )
        )

    return resolved_specs


def _build_kpi_section_header_markdown(
    *,
    body: str = "Latest snapshot and alert counters",
    panel_density: str = "comfortable",
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a shared KPI section panel using replaceable style metadata."""
    effective_style_spec = style_spec or build_kpi_panel_style_spec()
    support_key = (
        "compact_section_supporting_copy"
        if panel_density == "compact"
        else "section_supporting_copy"
    )
    return _build_info_panel_markdown(
        tone=str(effective_style_spec.get("default_tone", "neutral")),
        label=str(effective_style_spec.get("section_label", "kpi section")),
        body=str(body).strip(),
        supporting_title=_build_tone_panel_title("neutral", "details"),
        supporting_body=str(effective_style_spec.get(support_key, "")).strip(),
        panel_density=panel_density,
    )


def _build_kpi_metric_panel_markdown(
    spec: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared KPI card wrapper before the native Streamlit metric."""
    tone = str(spec.get("tone", style_spec.get("default_tone", "neutral"))).strip()
    return _build_info_panel_markdown(
        tone=tone,
        label=str(style_spec.get("metric_label", "kpi")),
        body=str(spec.get("label", "")).strip(),
        supporting_title=_build_tone_panel_title("neutral", "details"),
        supporting_body=str(style_spec.get("metric_supporting_copy", "")).strip(),
        panel_density=panel_density,
    )


def _build_content_section_header_markdown(
    title: str,
    *,
    tone: str = "neutral",
    panel_density: str = "comfortable",
    focus_label: str = "",
    focus_tone: str = "",
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a shared content-section panel using replaceable style metadata."""
    effective_style_spec = style_spec or build_content_panel_style_spec()
    support_key = (
        "compact_section_supporting_copy"
        if panel_density == "compact"
        else "section_supporting_copy"
    )
    supporting_body = str(effective_style_spec.get(support_key, "")).strip()
    focus_label = str(focus_label).strip()
    effective_tone = str(focus_tone).strip() or tone or str(
        effective_style_spec.get("default_tone", "neutral")
    )
    if focus_label:
        supporting_body = (
            f"{focus_label}\n{supporting_body}" if supporting_body else focus_label
        )
    return _build_intro_panel_markdown(
        tone=effective_tone,
        label=str(effective_style_spec.get("section_label", "content section")),
        body=str(title).strip(),
        panel_density=panel_density,
        detail_label=str(effective_style_spec.get("detail_label", "content details")),
        supporting_body=supporting_body,
    )


def _build_content_detail_markdown(
    *,
    tone: str,
    body: str,
    panel_density: str,
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a shared content-detail wrapper for grouped rows and tables."""
    effective_style_spec = style_spec or build_content_panel_style_spec()
    support_key = (
        "compact_detail_supporting_copy"
        if panel_density == "compact"
        else "detail_supporting_copy"
    )
    return _build_info_panel_markdown(
        tone=tone or str(effective_style_spec.get("default_tone", "neutral")),
        label=str(effective_style_spec.get("detail_label", "content details")),
        body=str(body).strip(),
        supporting_title=_build_tone_panel_title("neutral", "details"),
        supporting_body=str(effective_style_spec.get(support_key, "")).strip(),
        panel_density=panel_density,
    )


def _build_intro_panel_markdown(
    *,
    tone: str,
    label: str,
    body: str,
    panel_density: str,
    detail_label: str = "",
    supporting_body: str = "",
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a shared intro-container panel for header/group/section entry blocks."""
    effective_style_spec = style_spec or build_intro_panel_style_spec()
    resolved_detail_label = detail_label or str(
        effective_style_spec.get("detail_label", "details")
    )
    return _build_info_panel_markdown(
        tone=tone,
        label=label,
        body=body,
        supporting_title=_build_tone_panel_title("neutral", resolved_detail_label),
        supporting_body=supporting_body,
        panel_density=panel_density,
    )


def _build_grouped_text_section_view_models(
    section_specs: list[object],
    source_rows: dict[str, list[str]],
    title_values: dict[str, str] | None = None,
) -> list[dict[str, object]]:
    """Build normalized grouped text sections from replaceable row sources."""
    section_view_models: list[dict[str, object]] = []
    effective_title_values = title_values or {}
    for section_spec in section_specs:
        title_key = str(getattr(section_spec, "get", lambda *_args: "")("title_key", "")).strip()
        title = str(
            effective_title_values.get(
                title_key,
                getattr(section_spec, "get", lambda *_args: "")("title", ""),
            )
        ).strip()
        rows_key = str(getattr(section_spec, "get", lambda *_args: "")("rows_key", "")).strip()
        if not title or not rows_key:
            continue
        section_view_models.append(
            {
                "title": title,
                "rows": list(source_rows.get(rows_key, [])),
            }
        )
    return section_view_models


def _build_single_text_section_view_models(
    rows: list[str],
    *,
    title: str,
) -> list[dict[str, object]]:
    """Build one grouped text section from a flat list of detail rows."""
    clean_title = str(title).strip()
    if not clean_title:
        return []
    return [
        {
            "title": clean_title,
            "rows": list(rows),
        }
    ]


def _to_grouped_rows(value: object) -> list[str]:
    """Convert one short text value into grouped-summary bullet rows."""
    text = str(value or "").strip()
    return [f"- {text}"] if text else []


def _to_bulleted_rows(values: object) -> list[str]:
    """Normalize a list-like payload into grouped-summary bullet rows."""
    return [
        row if str(row).strip().startswith("-") else f"- {str(row).strip()}"
        for row in list(values or [])
        if str(row).strip()
    ]


def _build_health_meta_rows(
    value: dict[str, object],
    labels: dict[str, object],
    *,
    meta_specs: list[object],
    derived_values: dict[str, object] | None = None,
) -> list[str]:
    """Build ordered health meta rows from replaceable metadata specs."""
    effective_derived_values = derived_values or {}
    meta_rows: list[str] = []
    for meta_spec in meta_specs:
        value_key = str(getattr(meta_spec, "get", lambda *_args: "")("value_key", "")).strip()
        if not value_key:
            continue
        label_key = str(
            getattr(meta_spec, "get", lambda *_args: "")("label_key", value_key)
        ).strip() or value_key
        fallback_label = str(
            getattr(meta_spec, "get", lambda *_args: "")("fallback_label", value_key)
        ).strip() or value_key
        value_mode = str(
            getattr(meta_spec, "get", lambda *_args: "")("value_mode", "raw")
        ).strip() or "raw"
        raw_value = effective_derived_values.get(value_key, value.get(value_key, ""))
        if value_mode == "count":
            resolved_value = len(list(raw_value)) if isinstance(raw_value, list) else 0
        else:
            resolved_value = raw_value
        meta_rows.append(f"{labels.get(label_key, fallback_label)}: {resolved_value}")
    return meta_rows


def _build_info_blocks(
    block_specs: list[object],
    *,
    block_sources: dict[str, object],
) -> list[dict[str, object]]:
    """Build normalized information blocks from configured source mappings."""
    info_blocks: list[dict[str, object]] = []
    for block_spec in block_specs:
        block_key = str(getattr(block_spec, "get", lambda *_args: "")("block_key", "")).strip()
        block_type = str(getattr(block_spec, "get", lambda *_args: "")("block_type", "")).strip()
        if not block_key or not block_type:
            continue
        info_blocks.append(
            {
                "block_key": block_key,
                "block_type": block_type,
                "content": block_sources.get(block_key),
            }
        )
    return info_blocks


def _build_health_info_blocks(
    meta_rows: list[str],
    detail_sections: list[dict[str, object]],
    *,
    info_block_specs: list[object],
) -> list[dict[str, object]]:
    """Build stock-pool health info blocks from normalized health content parts."""
    return _build_info_blocks(
        info_block_specs,
        block_sources={
            "meta_rows": meta_rows,
            "detail_sections": detail_sections,
        },
    )


def _build_health_detail_sections(
    health_group_specs: dict[str, object],
    row_sources: dict[str, list[str]],
    *,
    title_values: dict[str, str],
) -> list[dict[str, object]]:
    """Build stock-pool health detail sections from health-specific row sources."""
    return _build_grouped_text_section_view_models(
        list(health_group_specs.get("detail_sections", [])),
        row_sources,
        title_values=title_values,
    )


def _build_health_row_sources(
    *,
    duplicate_text: str,
    issue_rows: list[str],
    suggested_matches: list[str],
    structure_rows: list[str],
    comparison_rows: list[str],
    hint_rows: list[str],
    none_text: str,
) -> dict[str, list[str]]:
    """Build stock-pool health row buckets before section/block assembly."""
    return {
        "duplicate_rows": [f"- {duplicate_text}"],
        "issue_rows": issue_rows,
        "suggestion_rows": (
            [f"- {row}" for row in suggested_matches]
            if suggested_matches
            else [f"- {none_text}"]
        ),
        "structure_rows": structure_rows if structure_rows else [f"- {none_text}"],
        "comparison_rows": comparison_rows if comparison_rows else [f"- {none_text}"],
        "hint_rows": hint_rows,
    }


def _build_health_status_copy(
    *,
    status: str,
    status_label: str,
    risk_label: str,
    templates: dict[str, object] | None = None,
) -> dict[str, str]:
    """Build shared health status display copy for badge and status-line surfaces."""
    resolved_templates = templates or {}
    return {
        "status_line": str(
            resolved_templates.get(
                "status_line_template",
                "Status: {status_label} ({status}) | Risk: {risk_label}",
            )
        ).format(
            status=status,
            status_label=status_label,
            risk_label=risk_label,
        ),
        "badge_text": str(
            resolved_templates.get(
                "badge_text_template",
                "{status_label} | {risk_label}",
            )
        ).format(
            status=status,
            status_label=status_label,
            risk_label=risk_label,
        ),
    }


def _resolve_spec_copy_variant(
    spec: dict[str, object],
    *,
    merge_keys: tuple[str, ...],
) -> dict[str, object]:
    """Resolve one spec with an optional copy variant merged into selected keys."""
    resolved_spec = dict(spec)
    selected_variant = str(spec.get("copy_variant", "default")).strip() or "default"
    copy_variants = dict(spec.get("copy_variants", {}))
    if selected_variant == "default":
        return resolved_spec

    variant_payload = dict(copy_variants.get(selected_variant, {}))
    for key in merge_keys:
        raw_base_value = spec.get(key, {} if key != "display_fields" else [])
        raw_variant_value = variant_payload.get(key, {} if key != "display_fields" else [])
        if isinstance(raw_base_value, list) and isinstance(raw_variant_value, list):
            resolved_spec[key] = list(raw_variant_value) if raw_variant_value else list(raw_base_value)
            continue
        if not isinstance(raw_base_value, dict) or not isinstance(raw_variant_value, dict):
            if key in variant_payload:
                resolved_spec[key] = raw_variant_value
            continue
        base_value = dict(raw_base_value)
        variant_value = dict(raw_variant_value)
        merged_value = dict(base_value)
        for nested_key, nested_value in variant_value.items():
            existing_nested = merged_value.get(nested_key)
            if isinstance(existing_nested, dict) and isinstance(nested_value, dict):
                nested_merged = dict(existing_nested)
                nested_merged.update(nested_value)
                merged_value[nested_key] = nested_merged
                continue
            merged_value[nested_key] = nested_value
        resolved_spec[key] = merged_value
    return resolved_spec


def _build_health_section_titles(
    labels: dict[str, object],
    group_titles: dict[str, object],
) -> dict[str, str]:
    """Build shared titled-section copy for stock-pool health sections."""
    return {
        "duplicate_title": (
            f"{group_titles.get('duplicate_title', labels.get('duplicate_codes', 'Duplicate Codes'))}:"
        ),
        "issue_title": f"{group_titles.get('issue_title', 'Validation Issues')}:",
        "suggestion_title": (
            f"{group_titles.get('suggestion_title', labels.get('suggested_matches', 'Suggested Matches'))}:"
        ),
        "structure_title": (
            f"{group_titles.get('structure_title', 'Structure Counts')}:"
        ),
        "comparison_title": (
            f"{group_titles.get('comparison_title', labels.get('structure_comparison', 'Structure Comparison'))}:"
        ),
        "hint_title": f"{group_titles.get('hint_title', labels.get('health_hints', 'Health Hints'))}:",
    }


def _build_health_comparison_rows(
    value: dict[str, object],
    labels: dict[str, object],
) -> list[str]:
    """Build stock-pool comparison rows from the saved local baseline."""
    comparison_tag_labels = [
        str(tag_label).strip()
        for tag_label in list(value.get("comparison_tag_labels", []))
        if str(tag_label).strip()
    ]
    comparison_highlight_summary = str(
        value.get("comparison_highlight_summary", "")
    ).strip()
    comparison_summary = str(value.get("comparison_summary", "")).strip()
    snapshot_path = str(value.get("comparison_snapshot_path", "")).strip()
    baseline_saved_at = str(value.get("comparison_baseline_saved_at", "")).strip()
    comparison_tag_groups = list(value.get("comparison_tag_groups", []))
    change_rows = [str(row).strip() for row in list(value.get("comparison_change_rows", []))]
    rows: list[str] = []
    if comparison_tag_labels:
        rows.append(
            f"- {labels.get('comparison_tags', 'Change Tags')}: {', '.join(comparison_tag_labels)}"
        )
    group_summaries = [
        str(group.get("summary", "")).strip()
        for group in comparison_tag_groups
        if isinstance(group, dict) and str(group.get("summary", "")).strip()
    ]
    if group_summaries:
        rows.append(
            f"- {labels.get('comparison_tag_groups', 'Change Groups')}: {' | '.join(group_summaries)}"
        )
    if comparison_highlight_summary:
        rows.append(
            f"- {labels.get('comparison_highlight_summary', 'Change Highlight')}: {comparison_highlight_summary}"
        )
    if comparison_summary:
        rows.append(
            f"- {labels.get('comparison_summary', 'Comparison Summary')}: {comparison_summary}"
        )
    if snapshot_path:
        rows.append(
            f"- {labels.get('comparison_snapshot_path', 'Snapshot Path')}: {snapshot_path}"
        )
    if baseline_saved_at:
        rows.append(
            f"- {labels.get('comparison_baseline_saved_at', 'Baseline Saved At')}: {baseline_saved_at}"
        )
    rows.extend(change_rows)
    return rows


def _build_count_summary_rows(
    value: dict[str, object],
    labels: dict[str, object],
) -> list[str]:
    """Build compact count-summary rows for structural stock-pool distributions."""
    sector_counts = dict(value.get("sector_counts", {}))
    chain_group_counts = dict(value.get("chain_group_counts", {}))
    pool_type_counts = dict(value.get("pool_type_counts", {}))
    row_specs = (
        ("sector_counts", "Sector Counts"),
        ("chain_group_counts", "Chain-group Counts"),
        ("pool_type_counts", "Pool-type Counts"),
        ("priority_counts", "Priority Counts"),
    )
    rows: list[str] = []
    top_sector_row = _build_top_count_row(
        sector_counts,
        label=str(labels.get("top_sector_counts", "Top Sectors")),
    )
    if top_sector_row:
        rows.append(top_sector_row)
    top_chain_group_row = _build_top_count_row(
        chain_group_counts,
        label=str(labels.get("top_chain_group_counts", "Top Chain Groups")),
    )
    if top_chain_group_row:
        rows.append(top_chain_group_row)
    top_pool_type_row = _build_top_count_row(
        pool_type_counts,
        label=str(labels.get("top_pool_type_counts", "Top Pool Types")),
    )
    if top_pool_type_row:
        rows.append(top_pool_type_row)
    for value_key, fallback_label in row_specs:
        counts = dict(value.get(value_key, {}))
        if not counts:
            continue
        label = str(labels.get(value_key, fallback_label))
        formatted_items = ", ".join(f"{key}: {count}" for key, count in counts.items())
        rows.append(f"- {label}: {formatted_items}")
    return rows


def _build_top_count_row(
    counts: dict[object, object],
    *,
    label: str,
    limit: int = 3,
) -> str:
    """Build one top-N count row for fast visual scanning."""
    if not counts:
        return ""
    ranked_items = sorted(
        ((str(key), int(count)) for key, count in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )[:limit]
    formatted_items = ", ".join(f"{key}: {count}" for key, count in ranked_items)
    return f"- {label}: {formatted_items}"


def _build_summary_metrics(
    spec: dict[str, object],
    labels: dict[str, object],
    *,
    value_resolver: object,
) -> list[dict[str, object]]:
    """Build summary metric view models from shared metric metadata and one resolver."""
    summary_metrics: list[dict[str, object]] = []
    for metric_spec in list(spec.get("summary_metrics", [])):
        value_key = str(metric_spec.get("value_key", ""))
        metric_value = getattr(value_resolver, "__call__", lambda *_args: 0)(value_key)
        summary_metrics.append(
            {
                "label": str(labels.get(str(metric_spec.get("label_key", value_key)), value_key)),
                "value": metric_value,
                "format_key": str(metric_spec.get("format_key", "default")),
            }
    )
    return summary_metrics


def _build_grouped_count_badge(count: int, suffix: str) -> str:
    """Build shared count-style badge text for grouped summary blocks."""
    return f"{count} {suffix}"


def _build_grouped_summary_info_blocks_from_sections(
    detail_sections: list[dict[str, object]],
    spec: dict[str, object],
) -> list[dict[str, object]]:
    """Build shared grouped-summary info blocks from grouped text sections."""
    return _build_info_blocks(
        list(spec.get("info_block_specs", [])),
        block_sources={
            "detail_sections": detail_sections,
        },
    )


def _build_priority_channel_rows(
    value: dict[str, object],
    *,
    labels: dict[str, object],
) -> list[str]:
    """Build stable source/meta rows for the daily priority-summary block."""
    rows: list[str] = []
    source_batch = str(value.get("source_batch", "")).strip()
    if source_batch:
        rows.append(
            f"- {labels.get('source_batch_label', 'Source Batch')}: {source_batch}"
        )
    impact_summary = str(value.get("impact_summary", "")).strip()
    if impact_summary:
        rows.append(
            f"- {labels.get('impact_summary_label', 'Impact Mix')}: {impact_summary}"
        )
    filter_mode = str(value.get("filter_mode", "")).strip()
    if filter_mode:
        rows.append(
            f"- {labels.get('filter_mode_label', 'Filter Mode')}: {filter_mode}"
        )
    rows.extend(_to_bulleted_rows(value.get("priority_channel_rows")))
    return rows


def _build_grouped_summary_sections_from_items(
    items: list[dict[str, object]],
    spec: dict[str, object],
    *,
    format_spec: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Build grouped summary text sections directly from source items."""
    labels = dict(spec.get("labels", {}))
    return _build_single_text_section_view_models(
        _build_grouped_summary_rows_from_items(
            items,
            spec=spec,
            format_spec=format_spec,
        ),
        title=f"{labels.get('detail_section_title', 'Details')}:",
    )


def _build_grouped_summary_detail_payload(
    items: list[dict[str, object]],
    spec: dict[str, object],
    *,
    format_spec: dict[str, dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """Build grouped-summary detail payload with info blocks as the canonical shape."""
    detail_sections = _build_grouped_summary_sections_from_items(
        items,
        spec=spec,
        format_spec=format_spec,
    )
    info_blocks = _build_grouped_summary_info_blocks_from_sections(
        detail_sections,
        spec,
    )
    return {
        "info_blocks": info_blocks,
    }


def _resolve_compatibility_rows_from_info_blocks(
    info_blocks: list[dict[str, object]],
) -> list[str]:
    """Derive compatibility flat rows from grouped information blocks."""
    compatibility_rows: list[str] = []
    for info_block in info_blocks:
        if str(info_block.get("block_type", "")).strip() != "grouped_text_sections":
            continue
        section_items = info_block.get("content")
        if not isinstance(section_items, list):
            continue
        for section_item in section_items:
            rows = getattr(section_item, "get", lambda *_args: [])("rows", [])
            if isinstance(rows, list):
                compatibility_rows.extend(str(row) for row in rows)
    return compatibility_rows


def _build_legacy_grouped_summary_info_blocks(
    compatibility_rows: list[str],
    spec: dict[str, object],
) -> list[dict[str, object]]:
    """Convert legacy grouped-summary flat rows into the modern info-block shape."""
    labels = dict(spec.get("labels", {}))
    return _build_grouped_summary_info_blocks_from_sections(
        _build_single_text_section_view_models(
            compatibility_rows,
            title=f"{labels.get('detail_section_title', 'Details')}:",
        ),
        spec,
    )


def _resolve_legacy_grouped_summary_rows(view_model: dict[str, object]) -> list[str]:
    """Read legacy flat grouped-summary rows from old view-model inputs only."""
    return list(view_model.get("detail_rows", []))


def _resolve_grouped_summary_render_blocks(
    view_model: dict[str, object],
    spec: dict[str, object],
) -> list[dict[str, object]]:
    """Resolve grouped-summary info blocks, using legacy rows only for old inputs."""
    info_blocks = list(view_model.get("info_blocks", []))
    if info_blocks:
        return info_blocks

    compatibility_rows = _resolve_legacy_grouped_summary_rows(view_model)
    if compatibility_rows:
        return _build_legacy_grouped_summary_info_blocks(compatibility_rows, spec)

    return []


def _render_grouped_text_sections(
    st: object,
    section_view_models: list[dict[str, object]],
    *,
    first_group_tone: str = "",
    surface_copy_variant: str = "default",
    first_group_anchor_id: str = "",
) -> None:
    """Render a sequence of titled text-row sections through one shared entry point."""
    resolved_first_group_tone = str(first_group_tone).strip()
    content_style_spec = build_content_panel_style_spec(surface_copy_variant)
    for index, section_view_model in enumerate(section_view_models):
        title = str(section_view_model.get("title", "")).strip()
        if index == 0 and title and str(first_group_anchor_id).strip():
            st.markdown(
                f'<div id="{str(first_group_anchor_id).strip()}"></div>',
                unsafe_allow_html=True,
            )
        if index == 0 and title and resolved_first_group_tone:
            st.markdown(
                _build_section_title_markdown(
                    title,
                    tone=resolved_first_group_tone,
                    style_spec=content_style_spec,
                ),
                unsafe_allow_html=True,
            )
        else:
            st.write(title)
        for row in list(section_view_model.get("rows", [])):
            _render_semantic_dashboard_row(st, row)


def _render_semantic_dashboard_row(st: object, row: object) -> None:
    """Color only sentiment keywords while keeping the rest of the row unchanged."""
    text = str(row)
    signal_colors = build_semantic_signal_style_spec()
    if text.startswith("消息倾向："):
        prefix = "消息倾向："
        value = text[len(prefix):]
        if value.startswith("利好"):
            color = signal_colors["positive"]
        elif value.startswith("利空"):
            color = signal_colors["negative"]
        elif value.startswith("中性"):
            color = signal_colors["neutral"]
        else:
            color = "inherit"
        st.markdown(
            f'<div>{escape(prefix)}<strong style="color:{color}">{escape(value)}</strong></div>',
            unsafe_allow_html=True,
        )
        return
    if text.startswith("利好消息：") or text.startswith("利空消息："):
        color = signal_colors["positive"] if text.startswith("利好消息：") else signal_colors["negative"]
        st.markdown(
            f'<div style="color:{color}">{escape(text)}</div>',
            unsafe_allow_html=True,
        )
        return
    st.write(row)


def _render_info_blocks(
    st: object,
    info_blocks: list[dict[str, object]],
    *,
    first_group_tone: str = "",
    surface_copy_variant: str = "default",
    first_group_anchor_id: str = "",
) -> None:
    """Render normalized information blocks through one shared entry point."""
    for info_block in info_blocks:
        block_type = str(info_block.get("block_type", "")).strip()
        content = info_block.get("content")
        if block_type == "meta_grid":
            rows = list(content) if isinstance(content, list) else []
            columns = st.columns(2)
            for index, row in enumerate(rows):
                _render_semantic_dashboard_row(columns[index % 2], row)
            continue
        if block_type == "grouped_text_sections":
            _render_grouped_text_sections(
                st,
                list(content) if isinstance(content, list) else [],
                first_group_tone=first_group_tone,
                surface_copy_variant=surface_copy_variant,
                first_group_anchor_id=first_group_anchor_id,
            )


def _build_chart_section_header_markdown(
    spec: dict[str, object],
    *,
    panel_density: str = "comfortable",
    style_spec: dict[str, object] | None = None,
    ) -> str:
    """Build a lightweight tone header for chart sections."""
    tone_key = str(spec.get("tone", "neutral")).strip().lower()
    title = str(spec.get("title", "")).strip()
    effective_style_spec = style_spec or build_summary_panel_style_spec()
    panel_title = _build_tone_panel_title(
        tone_key,
        str(effective_style_spec.get("chart_label", "chart")),
    )
    return _build_panel_block_markdown(
        panel_title,
        _build_panel_body_text(title, panel_density=panel_density),
    )


def _build_chart_intro_markdown(
    spec: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared intro-container panel for chart entry blocks."""
    support_key = (
        "compact_chart_supporting_copy"
        if panel_density == "compact"
        else "chart_supporting_copy"
    )
    return _build_intro_panel_markdown(
        tone=str(spec.get("tone", style_spec.get("default_tone", "neutral"))).strip(),
        label=str(style_spec.get("chart_label", "chart")),
        body=str(spec.get("title", "")).strip(),
        panel_density=panel_density,
        detail_label=str(style_spec.get("details_label", "details")),
        supporting_body=str(style_spec.get(support_key, "")).strip(),
    )


def _build_metric_group_markdown(
    *,
    tone: str,
    label: str,
    body: str,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared wrapper that introduces one metric-value group."""
    support_key = (
        "compact_supporting_copy"
        if panel_density == "compact"
        else "default_supporting_copy"
    )
    resolved_label = str(style_spec.get("default_label", label)).strip() or str(label).strip()
    return _build_info_panel_markdown(
        tone=str(tone).strip() or str(style_spec.get("default_tone", "neutral")),
        label=resolved_label,
        body=body,
        supporting_title=_build_tone_panel_title("neutral", "details"),
        supporting_body=str(style_spec.get(support_key, "")).strip(),
        panel_density=panel_density,
    )


def _format_kpi_metric_value(
    value: object,
    *,
    format_key: str,
    format_spec: dict[str, dict[str, object]],
) -> str:
    """Format one KPI metric value from replaceable presentation rules."""
    rule = dict(format_spec.get(format_key, format_spec.get("default", {})))
    empty_value = str(rule.get("empty_value", "-"))
    if value in (None, ""):
        return empty_value

    if format_key == "timestamp":
        raw_value = str(value).strip()
        for input_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                parsed = datetime.strptime(raw_value, input_format)
                return parsed.strftime(str(rule.get("datetime_format", "%Y-%m-%d %H:%M")))
            except ValueError:
                continue
        return raw_value

    if format_key == "count":
        if isinstance(value, bool):
            return str(int(value))
        if isinstance(value, int):
            return f"{value:,}" if bool(rule.get("thousands_separator")) else str(value)
        if isinstance(value, float) and value.is_integer():
            integer_value = int(value)
            return f"{integer_value:,}" if bool(rule.get("thousands_separator")) else str(integer_value)
        return str(value)

    if format_key == "percent_1":
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return str(value)
        decimals = int(rule.get("decimals", 1))
        suffix = str(rule.get("suffix", "%"))
        return f"{numeric_value:.{decimals}f}{suffix}"

    if format_key == "signed_percent_1":
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return str(value)
        decimals = int(rule.get("decimals", 1))
        suffix = str(rule.get("suffix", "%"))
        sign = "+" if numeric_value >= 0 and bool(rule.get("show_plus")) else ""
        return f"{sign}{numeric_value:.{decimals}f}{suffix}"

    return str(value)


def _format_detail_value(
    value: object,
    *,
    format_key: str,
    format_spec: dict[str, dict[str, object]],
) -> str:
    """Format one detail-row value through the shared dashboard formatter path."""
    return _format_kpi_metric_value(
        value,
        format_key=format_key,
        format_spec=format_spec,
    )


def _format_rows_for_display(
    rows: list[dict[str, object]],
    *,
    column_formats: dict[str, str],
    format_spec: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Format selected row columns for display while preserving source rows."""
    formatted_rows: list[dict[str, object]] = []
    for row in rows:
        formatted_row = dict(row)
        for column, format_key in column_formats.items():
            if column not in formatted_row:
                continue
            formatted_row[column] = _format_detail_value(
                formatted_row[column],
                format_key=format_key,
                format_spec=format_spec,
            )
        formatted_rows.append(formatted_row)
    return formatted_rows


def _normalize_display_field_specs(field_specs: list[object]) -> list[dict[str, str]]:
    """Normalize shared display-field metadata into one reusable shape."""
    normalized_fields: list[dict[str, str]] = []
    for field_spec in field_specs:
        field_key = str(getattr(field_spec, "get", lambda *_args: "")("key", "")).strip()
        if not field_key:
            continue
        label = str(getattr(field_spec, "get", lambda *_args: "")("label", field_key)).strip() or field_key
        normalized_fields.append(
            {
                "key": field_key,
                "label": label,
                "format_key": str(getattr(field_spec, "get", lambda *_args: "")("format_key", "")).strip(),
                "prefix": str(getattr(field_spec, "get", lambda *_args: "")("prefix", "")).strip(),
            }
        )
    return normalized_fields


def _resolve_table_column_specs(spec: dict[str, object]) -> list[dict[str, str]]:
    """Resolve table-column metadata into one normalized, replaceable shape."""
    display_fields = _normalize_display_field_specs(list(spec.get("display_fields", [])))
    if display_fields:
        return display_fields

    table_columns = list(spec.get("table_columns", []))
    if table_columns:
        return _normalize_display_field_specs(table_columns)

    column_formats = dict(spec.get("table_column_formats", {}))
    return [
        {
            "key": str(column),
            "label": str(column),
            "format_key": str(column_formats.get(str(column), "")).strip(),
        }
        for column in list(spec.get("columns", []))
    ]


def _build_table_rows_for_display(
    rows: list[dict[str, object]],
    *,
    spec: dict[str, object],
    format_spec: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    """Build display-ready table rows from replaceable column metadata."""
    column_specs = _resolve_table_column_specs(spec)
    if column_specs:
        display_rows: list[dict[str, object]] = []
        for row in rows:
            display_row: dict[str, object] = {}
            for column_spec in column_specs:
                column_key = column_spec["key"]
                column_label = column_spec["label"]
                column_value = row.get(column_key)
                format_key = column_spec["format_key"]
                if format_key:
                    display_row[column_label] = _format_detail_value(
                        column_value,
                        format_key=format_key,
                        format_spec=format_spec,
                    )
                    continue
                display_row[column_label] = column_value
            display_rows.append(display_row)
        return display_rows

    return rows


def _resolve_detail_layout(spec: dict[str, object]) -> dict[str, object]:
    """Resolve replaceable detail-row layout metadata with legacy fallback."""
    detail_layout = dict(spec.get("detail_layout", {}))
    detail_fields = _normalize_display_field_specs(list(detail_layout.get("fields", [])))
    if detail_fields:
        return {
            "item_prefix": str(detail_layout.get("item_prefix", "- ")),
            "separator": str(detail_layout.get("separator", " | ")),
            "fields": detail_fields,
        }

    display_fields = _normalize_display_field_specs(list(spec.get("display_fields", [])))
    if display_fields:
        return {
            "item_prefix": str(detail_layout.get("item_prefix", "- ")),
            "separator": str(detail_layout.get("separator", " | ")),
            "fields": display_fields,
        }

    columns = list(spec.get("columns", []))
    detail_column_formats = dict(spec.get("detail_column_formats", {}))
    return {
        "item_prefix": "- ",
        "separator": " | ",
        "fields": [
            {
                "key": str(column),
                "label": str(column),
                "format_key": str(detail_column_formats.get(str(column), "")).strip(),
            }
            for column in columns
        ],
    }


def _build_grouped_summary_rows_from_items(
    items: list[dict[str, object]],
    *,
    spec: dict[str, object],
    format_spec: dict[str, dict[str, object]],
) -> list[str]:
    """Build grouped-summary text rows from replaceable field-layout metadata."""
    detail_layout = _resolve_detail_layout(spec)
    item_prefix = str(detail_layout.get("item_prefix", "- "))
    separator = str(detail_layout.get("separator", " | "))
    field_specs = list(detail_layout.get("fields", []))
    summary_rows: list[str] = []
    for item in items:
        parts: list[str] = []
        for field_spec in field_specs:
            field_key = str(field_spec.get("key", "")).strip()
            if not field_key:
                continue
            raw_value = item.get(field_key, "")
            if not str(raw_value):
                continue
            format_key = str(field_spec.get("format_key", "")).strip()
            field_prefix = str(field_spec.get("prefix", ""))
            if format_key:
                formatted_value = _format_detail_value(
                        raw_value,
                        format_key=format_key,
                        format_spec=format_spec,
                    )
                parts.append(field_prefix + formatted_value)
                continue
            parts.append(field_prefix + str(raw_value))
        if parts:
            summary_rows.append(item_prefix + separator.join(parts))
    return summary_rows


def _build_chart_panel_markdown(
    spec: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared card wrapper for chart sections."""
    return _build_chart_intro_markdown(
        spec,
        panel_density=panel_density,
        style_spec=style_spec,
    )


def _build_chart_axes_markdown(
    spec: dict[str, object],
    *,
    panel_density: str,
    style_spec: dict[str, object],
) -> str:
    """Build a shared axis-description wrapper for chart blocks."""
    x_axis_label = str(spec.get("x_axis_label", spec.get("x_key", ""))).strip()
    y_axis_label = str(spec.get("y_axis_label", spec.get("y_key", ""))).strip()
    if not x_axis_label and not y_axis_label:
        return ""
    axis_parts: list[str] = []
    if x_axis_label:
        axis_parts.append(f"{str(style_spec.get('x_axis_prefix', 'X')).strip()}: {x_axis_label}")
    if y_axis_label:
        axis_parts.append(f"{str(style_spec.get('y_axis_prefix', 'Y')).strip()}: {y_axis_label}")
    return _build_info_panel_markdown(
        tone=str(spec.get("tone", style_spec.get("default_tone", "neutral"))).strip(),
        label=str(style_spec.get("axes_label", "axes")),
        body=" | ".join(axis_parts),
        panel_density=panel_density,
    )


def _build_section_title_markdown(
    title: str,
    *,
    tone: str = "neutral",
    style_spec: dict[str, object] | None = None,
) -> str:
    """Build a shared section-title wrapper to reduce raw subheaders."""
    effective_style_spec = style_spec or build_content_panel_style_spec()
    return _build_info_panel_markdown(
        tone=tone,
        label=str(effective_style_spec.get("section_title_label", "section")),
        body=str(title).strip(),
        panel_density="comfortable",
    )


def _build_info_panel_markdown(
    *,
    tone: str,
    label: str,
    body: str,
    panel_density: str,
    apply_density: bool = True,
    supporting_title: str | None = None,
    supporting_body: str | None = None,
) -> str:
    """Build one reusable panel block, optionally followed by a support block."""
    panel_markdown = _build_panel_block_markdown(
        _build_tone_panel_title(tone, label),
        (
            _build_panel_body_text(body, panel_density=panel_density)
            if apply_density
            else str(body).strip()
        ),
        tone=tone,
    )
    if supporting_title and supporting_body:
        return panel_markdown + _build_panel_block_markdown(
            str(supporting_title).strip(),
            str(supporting_body).strip(),
            tone="neutral",
        )
    return panel_markdown


def _build_tone_panel_title(tone: str, label: str) -> str:
    """Build a consistent ASCII panel title from tone metadata."""
    tone_key = str(tone).strip().lower()
    tone_icon = _resolve_tone_icon(tone_key)
    return f"{tone_icon} {tone_key.upper()} {str(label).strip().upper()}"


def _build_panel_block_markdown(title: str, body: str, *, tone: str = "neutral") -> str:
    """Build one HTML card panel block for section framing."""
    clean_title = str(title).strip()
    clean_body = str(body).strip()
    tone_class = _resolve_panel_tone_class(tone)
    return (
        f'<div class="dashboard-panel {tone_class}">'
        f'<div class="dashboard-panel__title">{clean_title}</div>'
        f'<div class="dashboard-panel__body">{clean_body}</div>'
        "</div>"
    )


def _build_panel_body_text(body: str, *, panel_density: str) -> str:
    """Build panel body copy that can tighten up in compact mode."""
    clean_body = str(body).strip()
    if panel_density == "compact" and len(clean_body) > 15:
        return clean_body[:15] + "..."
    return clean_body


def _build_dashboard_panel_css(style_spec: dict[str, object]) -> str:
    """Build shared CSS for HTML panel containers."""
    return (
        "<style>"
        ".dashboard-panel {"
        f"background: {style_spec['background']};"
        f"border: 2px solid {style_spec['border']};"
        f"color: {style_spec['text_color']};"
        f"border-radius: {style_spec['radius']};"
        f"padding: {style_spec['padding']};"
        f"box-shadow: {style_spec['shadow']};"
        "margin: 0 0 0.65rem 0;"
        "}"
        ".dashboard-panel--accent {"
        f"border-color: {style_spec['tone_accent_border']};"
        "}"
        ".dashboard-panel--warning {"
        f"border-color: {style_spec['tone_warning_border']};"
        "}"
        ".dashboard-panel--success {"
        f"border-color: {style_spec['tone_success_border']};"
        "}"
        ".dashboard-panel--error {"
        f"border-color: {style_spec['tone_error_border']};"
        "}"
        ".dashboard-panel--info {"
        f"border-color: {style_spec['tone_info_border']};"
        "}"
        ".dashboard-panel--neutral {"
        f"border-color: {style_spec['tone_neutral_border']};"
        "}"
        ".dashboard-panel__title {"
        "font-size: 0.78rem;"
        "font-weight: 700;"
        "letter-spacing: 0.08em;"
        "text-transform: uppercase;"
        "margin-bottom: 0.4rem;"
        "}"
        ".dashboard-panel--accent .dashboard-panel__title {"
        f"color: {style_spec['tone_accent_border']};"
        "}"
        ".dashboard-panel--warning .dashboard-panel__title {"
        f"color: {style_spec['tone_warning_border']};"
        "}"
        ".dashboard-panel--success .dashboard-panel__title {"
        f"color: {style_spec['tone_success_border']};"
        "}"
        ".dashboard-panel--error .dashboard-panel__title {"
        f"color: {style_spec['tone_error_border']};"
        "}"
        ".dashboard-panel--info .dashboard-panel__title {"
        f"color: {style_spec['tone_info_border']};"
        "}"
        ".dashboard-panel__body {"
        f"color: {style_spec['muted_text_color']};"
        "font-size: 0.96rem;"
        "line-height: 1.45;"
        "white-space: pre-wrap;"
        "}"
        "</style>"
    )


def _resolve_tone_icon(tone: str) -> str:
    """Resolve a small ASCII icon for the shared tone vocabulary."""
    return {
        "accent": "+",
        "warning": "!",
        "success": "+",
        "error": "x",
        "info": "i",
        "neutral": "=",
    }.get(str(tone).strip().lower(), "=")


def _resolve_panel_tone_class(tone: str) -> str:
    """Resolve one CSS class name for panel surface tone styling."""
    return f"dashboard-panel--{str(tone).strip().lower() or 'neutral'}"


def _build_health_summary_view_model(
    value: dict[str, object],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build replaceable copy rows for the stock-pool health block."""
    resolved_spec = _resolve_spec_copy_variant(
        spec,
        merge_keys=("labels", "status_variants", "risk_variants", "health_groups"),
    )
    labels = dict(resolved_spec.get("labels", {}))
    status = str(value.get("status", "unknown"))
    status_variants = dict(resolved_spec.get("status_variants", {}))
    variant = dict(status_variants.get(status, status_variants.get("unknown", {})))
    risk_level = str(value.get("risk_level", "unknown"))
    risk_variants = dict(resolved_spec.get("risk_variants", {}))
    risk_variant = dict(risk_variants.get(risk_level, risk_variants.get("unknown", {})))

    duplicate_codes = list(value.get("duplicate_codes", []))
    unknown_sectors = list(value.get("unknown_sectors", []))
    unknown_chain_groups = list(value.get("unknown_chain_groups", []))
    unknown_markets = list(value.get("unknown_markets", []))
    unknown_pool_types = list(value.get("unknown_pool_types", []))
    health_hints = list(value.get("health_hints", []))
    none_text = str(labels.get("none", "none"))
    duplicate_text = ", ".join(duplicate_codes) if duplicate_codes else none_text
    duplicate_count = len(duplicate_codes)
    resolved_status_label = str(variant.get("status_label", status.title()))
    resolved_risk_label = str(risk_variant.get("label", risk_level.upper()))
    health_group_specs = dict(resolved_spec.get("health_groups", {}))
    health_meta_specs = list(resolved_spec.get("health_meta", []))
    health_info_block_specs = list(resolved_spec.get("health_info_blocks", []))
    group_titles = dict(health_group_specs.get("group_titles", {}))
    suggested_matches = _build_validation_suggestion_rows(
        value,
        group_specs=list(health_group_specs.get("suggestion_groups", [])),
    )
    issue_rows = _build_validation_issue_rows(
        value,
        labels,
        none_text,
        group_specs=list(health_group_specs.get("issue_groups", [])),
    )
    comparison_rows = _build_health_comparison_rows(value, labels)

    hint_rows = (
        [f"- {hint}" for hint in health_hints]
        if health_hints
        else [f"- {variant.get('hint_empty_text', none_text)}"]
    )
    structure_rows = _build_count_summary_rows(value, labels)
    meta_rows = _build_health_meta_rows(
        value,
        labels,
        meta_specs=health_meta_specs,
        derived_values={
            "risk_label": resolved_risk_label,
        },
    )
    row_sources = _build_health_row_sources(
        duplicate_text=duplicate_text,
        issue_rows=issue_rows,
        suggested_matches=suggested_matches,
        structure_rows=structure_rows,
        comparison_rows=comparison_rows,
        hint_rows=hint_rows,
        none_text=none_text,
    )
    section_titles = _build_health_section_titles(labels, group_titles)
    detail_sections = _build_health_detail_sections(
        health_group_specs,
        row_sources,
        title_values=section_titles,
    )

    summary_metrics = _build_summary_metrics(
        resolved_spec,
        labels,
        value_resolver=lambda value_key: (
            duplicate_count if value_key == "duplicate_count" else value.get(value_key, 0)
        ),
    )

    status_copy = _build_health_status_copy(
        status=status,
        status_label=resolved_status_label,
        risk_label=resolved_risk_label,
        templates={
            "status_line_template": labels.get("status_line_template", ""),
            "badge_text_template": labels.get("badge_text_template", ""),
        },
    )

    return {
        "tone": str(risk_variant.get("tone", variant.get("tone", "info"))),
        "risk_level": risk_level,
        "risk_label": resolved_risk_label,
        "risk_text": str(value.get("risk_text", "")).strip(),
        "structure_summary": str(value.get("structure_summary", "")).strip(),
        "extension_summary": str(value.get("extension_summary", "")).strip(),
        "status_line": status_copy["status_line"],
        "badge_text": status_copy["badge_text"],
        "summary_metrics": summary_metrics,
        "info_blocks": _build_health_info_blocks(
            meta_rows,
            detail_sections,
            info_block_specs=health_info_block_specs,
        ),
    }


def _build_validation_issue_rows(
    value: dict[str, object],
    labels: dict[str, object],
    none_text: str,
    *,
    group_specs: list[object],
) -> list[str]:
    """Build flat issue rows from stock-pool validation issue buckets."""
    issue_rows: list[str] = []
    for group_spec in group_specs:
        value_key = str(getattr(group_spec, "get", lambda *_args: "")("value_key", "")).strip()
        fallback_label = str(
            getattr(group_spec, "get", lambda *_args: "")("fallback_label", value_key)
        ).strip()
        label_key = str(
            getattr(group_spec, "get", lambda *_args: "")("label_key", value_key)
        ).strip() or value_key
        if not value_key:
            continue
        values = list(value.get(value_key, []))
        label = str(labels.get(label_key, fallback_label))
        issue_rows.append(f"- {label}: {', '.join(values) if values else none_text}")
    return issue_rows


def _build_validation_suggestion_rows(
    value: dict[str, object],
    *,
    group_specs: list[object],
) -> list[str]:
    """Build flat suggestion rows from stock-pool validation suggestion maps."""
    suggestion_rows: list[str] = []
    for group_spec in group_specs:
        value_key = str(getattr(group_spec, "get", lambda *_args: "")("value_key", "")).strip()
        label = str(getattr(group_spec, "get", lambda *_args: "")("item_label", value_key)).strip()
        if not value_key:
            continue
        suggestions = dict(value.get(value_key, {}))
        for unknown_value, suggested_value in suggestions.items():
            suggestion_rows.append(f"{label}: {unknown_value} -> {suggested_value}")
    return suggestion_rows


def _build_spotlight_summary_view_model(
    value: dict[str, object],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build grouped summary copy for the strongest-sector block."""
    resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels", "display_fields"))
    sector = str(value.get("sector", "No data yet"))
    format_spec = build_kpi_value_format_spec()
    labels = dict(resolved_spec.get("labels", {}))
    summary_metrics = _build_summary_metrics(
        resolved_spec,
        labels,
        value_resolver=lambda value_key: value.get(value_key, 0),
    )
    detail_payload = _build_grouped_summary_detail_payload(
        [value],
        spec=resolved_spec,
        format_spec=format_spec,
    )

    return {
        "tone": str(resolved_spec.get("tone", "accent")),
        "badge_text": sector,
        "summary_metrics": summary_metrics,
        "info_blocks": list(detail_payload["info_blocks"]),
    }


def _build_leader_grouped_view_model(
    value: dict[str, object],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build grouped summary copy for the leader-summary block."""
    resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels",))
    labels = dict(resolved_spec.get("labels", {}))
    leader_items = list(value.items())
    summary_metrics = _build_summary_metrics(
        resolved_spec,
        labels,
        value_resolver=lambda value_key: (
            len(leader_items) if value_key == "leader_count" else value.get(value_key, 0)
        ),
    )

    detail_payload = _build_grouped_summary_detail_payload(
        [
            {
                "leader_type": leader_type,
                "name": name,
            }
            for leader_type, name in leader_items
        ],
        spec=resolved_spec,
        format_spec=build_kpi_value_format_spec(),
    )

    return {
        "tone": str(resolved_spec.get("tone", "neutral")),
        "badge_text": _build_grouped_count_badge(
            len(leader_items),
            str(labels.get("badge_unit", "leader slot(s)")),
        ),
        "summary_metrics": summary_metrics,
        "info_blocks": list(detail_payload["info_blocks"]),
    }


def _build_alerts_grouped_view_model(
    value: list[dict[str, object]],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build grouped summary copy for latest alerts."""
    resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels", "display_fields"))
    labels = dict(resolved_spec.get("labels", {}))
    format_spec = build_kpi_value_format_spec()
    summary_metrics = _build_summary_metrics(
        resolved_spec,
        labels,
        value_resolver=lambda value_key: len(value) if value_key == "alert_count" else 0,
    )

    detail_payload = _build_grouped_summary_detail_payload(
        value,
        spec=resolved_spec,
        format_spec=format_spec,
    )

    return {
        "tone": str(resolved_spec.get("tone", "warning")),
        "badge_text": _build_grouped_count_badge(
            len(value),
            str(labels.get("badge_unit", "alert row(s)")),
        ),
        "summary_metrics": summary_metrics,
        "info_blocks": list(detail_payload["info_blocks"]),
    }


def _build_batch_list_grouped_view_model(
    value: list[object],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build grouped summary copy for saved snapshot batches."""
    resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels", "display_fields"))
    labels = dict(resolved_spec.get("labels", {}))
    format_spec = build_kpi_value_format_spec()
    summary_metrics = _build_summary_metrics(
        resolved_spec,
        labels,
        value_resolver=lambda value_key: len(value) if value_key == "batch_count" else 0,
    )

    detail_payload = _build_grouped_summary_detail_payload(
        [{"timestamp": item} for item in value],
        spec=resolved_spec,
        format_spec=format_spec,
    )

    return {
        "tone": str(resolved_spec.get("tone", "neutral")),
        "badge_text": _build_grouped_count_badge(
            len(value),
            str(labels.get("badge_unit", "saved batch(es)")),
        ),
        "summary_metrics": summary_metrics,
        "info_blocks": list(detail_payload["info_blocks"]),
    }


def _build_next_session_action_grouped_view_model(
    value: dict[str, object],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build grouped summary copy for the next-session action summary block."""
    labels = _resolve_next_session_action_labels(spec)
    core_count = int(value.get("core_count", 0) or 0)
    candidate_count = int(value.get("candidate_count", 0) or 0)
    avoid_count = int(value.get("avoid_count", 0) or 0)
    total_count = core_count + candidate_count + avoid_count
    summary_metrics = _build_summary_metrics(
        spec,
        labels,
        value_resolver=lambda value_key: value.get(value_key, 0),
    )
    rule_summary_lines = [
        str(line).strip()
        for line in list(value.get("rule_summary_lines", ()))
        if str(line).strip()
    ]
    core = dict(value.get("core", {}))
    candidate = dict(value.get("candidate", {}))
    avoid = dict(value.get("avoid", {}))
    detail_sections = _build_grouped_text_section_view_models(
        [
            {
                "title": str(labels.get("rule_section_title", "Weight Summary")).strip()
                + ":",
                "rows_key": "rule_rows",
            },
            {
                "title": str(labels.get("core_section_title", "Core Watchlist")).strip()
                + f" ({core_count}):",
                "rows_key": "core_rows",
            },
            {
                "title": str(
                    labels.get("candidate_section_title", "Candidate Watchlist")
                ).strip()
                + f" ({candidate_count}):",
                "rows_key": "candidate_rows",
            },
            {
                "title": str(labels.get("avoid_section_title", "Avoid List")).strip()
                + f" ({avoid_count}):",
                "rows_key": "avoid_rows",
            },
        ],
        {
            "rule_rows": _build_next_session_action_rule_summary_rows(rule_summary_lines),
            "core_rows": _build_next_session_action_section_rows("Core", core, labels=labels),
            "candidate_rows": _build_next_session_action_section_rows(
                "Candidate",
                candidate,
                labels=labels,
            ),
            "avoid_rows": _build_next_session_action_section_rows("Avoid", avoid, labels=labels),
        },
    )
    info_blocks = _build_grouped_summary_info_blocks_from_sections(detail_sections, spec)
    return {
        "tone": str(spec.get("tone", "accent")),
        "badge_text": str(
            labels.get(
                "badge_template",
                "{total} action slot(s) | Core {core} / Candidate {candidate} / Avoid {avoid}",
            )
        ).format(
            total=total_count,
            core=core_count,
            candidate=candidate_count,
            avoid=avoid_count,
        ),
        "summary_metrics": summary_metrics,
        "info_blocks": info_blocks,
    }


def _build_today_priority_grouped_view_model(
    value: dict[str, object],
    spec: dict[str, object],
) -> dict[str, object]:
    """Build grouped summary copy for the saved daily priority-summary block."""
    resolved_spec = _resolve_spec_copy_variant(spec, merge_keys=("labels",))
    labels = dict(resolved_spec.get("labels", {}))
    shown_items = int(value.get("shown_items", 0) or 0)
    total_items = int(value.get("total_items", 0) or 0)
    summary_metrics = _build_summary_metrics(
        resolved_spec,
        labels,
        value_resolver=lambda value_key: value.get(value_key, 0),
    )
    detail_sections = _build_grouped_text_section_view_models(
        [
            {
                "title": str(labels.get("core_section_title", "Core Summary")).strip() + ":",
                "rows_key": "core_rows",
            },
            {
                "title": str(labels.get("advice_section_title", "One-line Advice")).strip() + ":",
                "rows_key": "advice_rows",
            },
            {
                "title": str(labels.get("conclusion_section_title", "Daily Conclusion")).strip() + ":",
                "rows_key": "conclusion_rows",
            },
            {
                "title": str(labels.get("tips_section_title", "Action Tips")).strip() + ":",
                "rows_key": "tips_rows",
            },
            {
                "title": str(labels.get("read_order_section_title", "Reading Order")).strip() + ":",
                "rows_key": "read_order_rows",
            },
            {
                "title": str(labels.get("watch_section_title", "Watchlist")).strip() + ":",
                "rows_key": "watch_rows",
            },
            {
                "title": str(labels.get("action_section_title", "Suggested Actions")).strip() + ":",
                "rows_key": "action_rows",
            },
            {
                "title": str(labels.get("channel_section_title", "Priority Channel")).strip() + ":",
                "rows_key": "channel_rows",
            },
        ],
        {
            "core_rows": _to_grouped_rows(value.get("core_summary")),
            "advice_rows": _to_grouped_rows(value.get("one_line_advice")),
            "conclusion_rows": _to_grouped_rows(value.get("daily_conclusion")),
            "tips_rows": _to_grouped_rows(value.get("operation_tips")),
            "read_order_rows": _to_bulleted_rows(value.get("read_order")),
            "watch_rows": _to_bulleted_rows(value.get("watch_rows")),
            "action_rows": _to_bulleted_rows(value.get("action_rows")),
            "channel_rows": _build_priority_channel_rows(value, labels=labels),
        },
    )
    info_blocks = _build_grouped_summary_info_blocks_from_sections(detail_sections, resolved_spec)
    return {
        "tone": str(resolved_spec.get("tone", "accent")),
        "badge_text": str(
            labels.get(
                "badge_template",
                "{date} | {shown}/{total} priority items",
            )
        ).format(
            date=str(value.get("summary_date", "")).strip() or "today",
            shown=shown_items,
            total=total_items,
        ),
        "summary_metrics": summary_metrics,
        "info_blocks": info_blocks,
    }


def _resolve_next_session_action_labels(spec: dict[str, object]) -> dict[str, object]:
    """Resolve next-session action labels from the default set plus one optional copy variant."""
    return dict(_resolve_spec_copy_variant(spec, merge_keys=("labels",)).get("labels", {}))


def _build_next_session_action_section_rows(
    label: str,
    value: dict[str, object],
    *,
    labels: dict[str, object] | None = None,
) -> list[str]:
    """Build stable detail rows for one next-session action tier."""
    resolved_labels = labels or {}
    watchlist = list(value.get("watchlist", []))
    tags = dict(value.get("tags", {}))
    scores = dict(value.get("scores", {}))
    reason = str(value.get("reason", "")).strip() or "none"
    names_row_label = str(resolved_labels.get("names_row_label", "names")).strip() or "names"
    tags_row_label = str(resolved_labels.get("tags_row_label", "tags")).strip() or "tags"
    scores_row_label = str(resolved_labels.get("scores_row_label", "scores")).strip() or "scores"
    focus_row_label = str(resolved_labels.get("focus_row_label", "focus")).strip() or "focus"
    focus_templates = dict(resolved_labels.get("focus_templates", {}))
    return [
        f"- {label} {names_row_label}: {', '.join(str(name) for name in watchlist) if watchlist else 'none'}",
        (
            f"- {label} {tags_row_label}: "
            + (
                "; ".join(
                    f"{name} ({'/'.join(str(tag) for tag in list(name_tags))})"
                    for name, name_tags in tags.items()
                )
                if tags
                else "none"
            )
        ),
        (
            f"- {label} {scores_row_label}: "
            + (
                "; ".join(f"{name} ({score})" for name, score in scores.items())
                if scores
                else "none"
            )
        ),
        f"- {label} {focus_row_label}: {_build_compact_next_session_reason(reason, templates=focus_templates)}",
    ]


def _build_compact_next_session_reason(
    reason: str,
    *,
    templates: dict[str, object] | None = None,
) -> str:
    """Compress dashboard-only strategy copy into quicker scan-friendly focus text."""
    clean_reason = str(reason).strip()
    if not clean_reason or clean_reason == "none":
        return "none"

    resolved_templates = templates or {}
    normalized_reason = clean_reason.rstrip(".")
    lowered_reason = normalized_reason.lower()
    if lowered_reason.startswith("stay with ") and lowered_reason.endswith(" first"):
        focus_target = normalized_reason[10:-6].strip()
        return str(
            resolved_templates.get(
                "stay_with_first",
                "Stay with {target} leaders first.",
            )
        ).format(target=focus_target)
    if lowered_reason.startswith("use ") and lowered_reason.endswith(" as confirmation"):
        focus_target = normalized_reason[4:-16].strip()
        return str(
            resolved_templates.get(
                "use_as_confirmation",
                "Use {target} as first confirmation.",
            )
        ).format(target=focus_target)
    if lowered_reason.startswith("reduce names tied to "):
        focus_target = normalized_reason[21:].strip()
        return str(
            resolved_templates.get(
                "reduce_names_tied_to",
                "Reduce {target} names.",
            )
        ).format(target=focus_target)
    return clean_reason[0].upper() + clean_reason[1:]


def _build_next_session_action_rule_summary_rows(
    rule_summary_lines: list[str],
) -> list[str]:
    """Build a compact dashboard-only rule-summary block for the next-session panel."""
    clean_lines = [str(line).strip() for line in rule_summary_lines if str(line).strip()]
    if not clean_lines:
        return ["- none"]
    normalized_lines = []
    for line in clean_lines:
        normalized_line = line
        for prefix in (
            "Score rules: ",
            "Fallback rules: ",
            "评分规则：",
            "兜底规则：",
        ):
            if normalized_line.startswith(prefix):
                normalized_line = normalized_line[len(prefix) :]
                break
        normalized_line = normalized_line.replace(" | Avoid rules: ", " | ")
        normalized_line = normalized_line.replace(" | 规避规则：", " | ")
        normalized_lines.append(normalized_line)
    return ["- " + " | ".join(normalized_lines)]


def _render_page_layout(
    st: object,
    payload: dict[str, object],
    page_layout: list[dict[str, str]],
    *,
    kpi_summary_layout: dict[str, object] | None = None,
    kpi_copy_variant: str,
    surface_copy_variant: str,
    content_variant_overrides: dict[str, str],
    priority_action_sections: list[str] | None = None,
    panel_density: str,
) -> None:
    """Render the dashboard from replaceable page-layout specs."""
    chart_specs = build_chart_specs()
    content_specs = build_content_section_specs()
    focus_labels = _build_priority_focus_labels(
        list(priority_action_sections or []),
        copy_variant=surface_copy_variant,
    )
    focus_tones = _build_priority_focus_tones(list(priority_action_sections or []))
    active_segment_key = ""
    active_group_key = ""
    for section in page_layout:
        section_type = str(section["section_type"])
        section_key = str(section["section_key"])
        segment_key = str(section.get("segment_key", "")).strip()
        if (
            segment_key
            and segment_key != active_segment_key
            and segment_key != "header_segment"
        ):
            active_segment_key = segment_key
            _render_page_segment_intro(
                st,
                section,
                panel_density=panel_density,
                surface_copy_variant=surface_copy_variant,
            )
        group_key = str(section.get("group_key", "")).strip()
        if group_key and group_key != active_group_key:
            active_group_key = group_key
            _render_content_group_intro(
                st,
                section,
                panel_density=panel_density,
                surface_copy_variant=surface_copy_variant,
            )
        if section_type == "kpi":
            _render_kpi_cards(
                st,
                payload,
                copy_variant=kpi_copy_variant,
                panel_density=panel_density,
                kpi_summary_layout=kpi_summary_layout,
            )
            continue
        if section_type == "chart":
            chart_spec = dict(chart_specs[section_key])
            chart_spec["copy_variant"] = surface_copy_variant
            _render_chart_block(
                st,
                payload,
                chart_spec,
                panel_density=panel_density,
                surface_copy_variant=surface_copy_variant,
            )
            continue
        if section_type == "content":
            content_spec = dict(content_specs[section_key])
            requested_copy_variant = str(
                content_variant_overrides.get(
                    section_key,
                    content_spec.get("copy_variant", "default"),
                )
            ).strip()
            if requested_copy_variant:
                content_spec["copy_variant"] = requested_copy_variant
            _render_content_block_with_density(
                st,
                payload,
                content_spec,
                panel_density=panel_density,
                surface_copy_variant=surface_copy_variant,
                focus_label=focus_labels.get(section_key, ""),
                focus_tone=focus_tones.get(section_key, ""),
                section_key=section_key,
            )


def _render_page_segment_intro(
    st: object,
    section: dict[str, object],
    *,
    panel_density: str,
    surface_copy_variant: str,
) -> None:
    """Render a lightweight intro panel when the homepage enters a new page segment."""
    segment_title = str(section.get("segment_title", "")).strip()
    if not segment_title:
        return
    content_style_spec = build_content_panel_style_spec(surface_copy_variant)
    support_key = (
        "compact_segment_supporting_copy"
        if panel_density == "compact"
        else "segment_supporting_copy"
    )
    role_support = _build_business_role_support_text(
        str(section.get("segment_role_key", "")).strip(),
        copy_variant=surface_copy_variant,
        style_spec=content_style_spec,
    )
    supporting_body = role_support
    base_supporting_body = str(content_style_spec.get(support_key, "")).strip()
    if base_supporting_body:
        supporting_body = (
            f"{role_support}\n{base_supporting_body}" if role_support else base_supporting_body
        )
    st.markdown(
        _build_intro_panel_markdown(
            tone=str(
                section.get("segment_tone", content_style_spec.get("default_tone", "neutral"))
            ),
            label=str(content_style_spec.get("segment_label", "page segment")),
            body=segment_title,
            panel_density=panel_density,
            detail_label=str(content_style_spec.get("detail_label", "content details")),
            supporting_body=supporting_body,
        ),
        unsafe_allow_html=True,
    )


def _render_content_group_intro(
    st: object,
    section: dict[str, object],
    *,
    panel_density: str,
    surface_copy_variant: str,
) -> None:
    """Render a lightweight intro panel when the homepage enters a new content group."""
    group_title = str(section.get("group_title", "")).strip()
    if not group_title:
        return
    content_style_spec = build_content_panel_style_spec(surface_copy_variant)
    support_key = (
        "compact_group_supporting_copy"
        if panel_density == "compact"
        else "group_supporting_copy"
    )
    role_support = _build_business_role_support_text(
        str(section.get("group_role_key", "")).strip(),
        copy_variant=surface_copy_variant,
        style_spec=content_style_spec,
    )
    supporting_body = role_support
    base_supporting_body = str(content_style_spec.get(support_key, "")).strip()
    if base_supporting_body:
        supporting_body = (
            f"{role_support}\n{base_supporting_body}" if role_support else base_supporting_body
        )
    st.markdown(
        _build_intro_panel_markdown(
            tone=str(section.get("group_tone", content_style_spec.get("default_tone", "neutral"))),
            label=str(content_style_spec.get("group_label", "content group")),
            body=group_title,
            panel_density=panel_density,
            detail_label=str(content_style_spec.get("detail_label", "content details")),
            supporting_body=supporting_body,
            style_spec=build_intro_panel_style_spec(surface_copy_variant),
        ),
        unsafe_allow_html=True,
    )


def _build_business_role_support_text(
    role_key: str,
    *,
    copy_variant: str,
    style_spec: dict[str, object],
) -> str:
    """Build a small role cue so homepage intro panels reflect business intent."""
    normalized_role_key = str(role_key).strip()
    if not normalized_role_key:
        return ""
    role_specs = build_business_role_specs()
    localized_key = (
        f"{copy_variant}:{normalized_role_key}" if copy_variant == "business_cn" else normalized_role_key
    )
    role_spec = dict(role_specs.get(localized_key, role_specs.get(normalized_role_key, {})))
    role_label = str(role_spec.get("label", normalized_role_key)).strip()
    role_supporting_copy = str(role_spec.get("supporting_copy", "")).strip()
    prefix = str(style_spec.get("role_prefix", "Role")).strip() or "Role"
    if role_supporting_copy:
        return f"{prefix}: {role_label} | {role_supporting_copy}"
    return f"{prefix}: {role_label}"


def _build_task_template_summary_text(
    task_template: dict[str, object],
    *,
    copy_variant: str,
) -> str:
    """Build a compact summary of the current business task template."""
    summary_label = str(
        task_template.get(
            "summary_label",
            "\u4efb\u52a1\u6a21\u677f" if copy_variant == "business_cn" else "task template",
        )
    ).strip()
    label = str(task_template.get("label", "")).strip()
    body = str(task_template.get("body", "")).strip()
    focus_points = [
        str(item).strip()
        for item in list(task_template.get("focus_points", []))
        if str(item).strip()
    ]
    body_parts: list[str] = []
    if label:
        body_parts.append(label)
    if body:
        body_parts.append(body)
    if focus_points:
        focus_prefix = "\u5173\u6ce8\u70b9" if copy_variant == "business_cn" else "Focus"
        body_parts.append(f"{focus_prefix}: {' / '.join(focus_points)}")
    summary_body = " | ".join(body_parts)
    if not summary_body:
        return ""
    return f"{summary_label}: {summary_body}"


def _build_time_phase_summary_text(
    time_phase: dict[str, object],
    *,
    copy_variant: str,
    phase_override_key: str = "auto",
) -> str:
    """Build a compact summary of the current market-time phase template."""
    control_spec = build_control_band_specs(copy_variant)
    summary_label = str(
        time_phase.get(
            "summary_label",
            "\u65f6\u6bb5\u6a21\u677f" if copy_variant == "business_cn" else "time phase",
        )
    ).strip()
    label = str(time_phase.get("label", "")).strip()
    body = str(time_phase.get("body", "")).strip()
    focus_points = [
        str(item).strip()
        for item in list(time_phase.get("focus_points", []))
        if str(item).strip()
    ]
    pinned_sections = [
        str(item).strip()
        for item in list(time_phase.get("pinned_sections", []))
        if str(item).strip()
    ]
    deferred_sections = [
        str(item).strip()
        for item in list(time_phase.get("deferred_sections", []))
        if str(item).strip()
    ]
    hidden_sections = [
        str(item).strip()
        for item in list(time_phase.get("hidden_sections", []))
        if str(item).strip()
    ]
    body_parts: list[str] = []
    normalized_override_key = _resolve_time_phase_override_key(phase_override_key)
    if normalized_override_key == "auto":
        source_line = str(
            control_spec.get("time_phase_source_auto_template", "Phase source: {source_label}")
        ).format(
            source_label=str(
                control_spec.get("time_phase_source_auto", "Automatic")
            ).strip()
        )
    else:
        source_line = str(
            control_spec.get(
                "time_phase_source_manual_template",
                "Phase source: {source_label} | Active mode: {phase_label}",
            )
        ).format(
            source_label=str(
                control_spec.get("time_phase_source_manual", "Manual override")
            ).strip(),
            phase_label=label or normalized_override_key,
        )
    source_line = source_line.strip()
    if source_line:
        body_parts.append(source_line)
    if label:
        body_parts.append(label)
    if body:
        body_parts.append(body)
    if focus_points:
        focus_prefix = "\u5173\u6ce8\u70b9" if copy_variant == "business_cn" else "Focus"
        body_parts.append(f"{focus_prefix}: {' / '.join(focus_points)}")
    if copy_variant == "business_cn":
        if pinned_sections:
            body_parts.append(f"\u7f6e\u9876\u6a21\u5757\uff1a{' / '.join(pinned_sections)}")
        if deferred_sections:
            body_parts.append(f"\u540e\u7f6e\u6a21\u5757\uff1a{' / '.join(deferred_sections)}")
        if hidden_sections:
            body_parts.append(f"\u9690\u85cf\u6a21\u5757\uff1a{' / '.join(hidden_sections)}")
    else:
        if pinned_sections:
            body_parts.append(f"Pinned sections: {' / '.join(pinned_sections)}")
        if deferred_sections:
            body_parts.append(f"Deferred sections: {' / '.join(deferred_sections)}")
        if hidden_sections:
            body_parts.append(f"Hidden sections: {' / '.join(hidden_sections)}")
    summary_body = " | ".join(body_parts)
    if not summary_body:
        return ""
    return f"{summary_label}: {summary_body}"


def _build_role_strategy_summary_text(
    role_strategy: dict[str, object],
    *,
    copy_variant: str,
) -> str:
    """Build a compact summary of which business roles a dashboard mode emphasizes."""
    role_specs = build_business_role_specs()
    primary_roles = [
        str(role_key).strip()
        for role_key in list(role_strategy.get("primary_roles", []))
        if str(role_key).strip()
    ]
    secondary_roles = [
        str(role_key).strip()
        for role_key in list(role_strategy.get("secondary_roles", []))
        if str(role_key).strip()
    ]
    deferred_roles = [
        str(role_key).strip()
        for role_key in list(role_strategy.get("deferred_roles", []))
        if str(role_key).strip()
    ]
    hidden_roles = [
        str(role_key).strip()
        for role_key in list(role_strategy.get("hidden_roles", []))
        if str(role_key).strip()
    ]
    pinned_sections = [
        str(section_key).strip()
        for section_key in list(role_strategy.get("pinned_sections", []))
        if str(section_key).strip()
    ]
    deferred_sections = [
        str(section_key).strip()
        for section_key in list(role_strategy.get("deferred_sections", []))
        if str(section_key).strip()
    ]
    hidden_sections = [
        str(section_key).strip()
        for section_key in list(role_strategy.get("hidden_sections", []))
        if str(section_key).strip()
    ]
    summary_label = str(
        role_strategy.get(
            "summary_label",
            "\u89d2\u8272\u7b56\u7565" if copy_variant == "business_cn" else "role strategy",
        )
    ).strip()
    body = str(role_strategy.get("body", "")).strip()

    def resolve_role_label(role_key: str) -> str:
        localized_key = f"{copy_variant}:{role_key}" if copy_variant == "business_cn" else role_key
        role_spec = dict(role_specs.get(localized_key, role_specs.get(role_key, {})))
        return str(role_spec.get("label", role_key)).strip()

    primary_labels = [resolve_role_label(role_key) for role_key in primary_roles]
    secondary_labels = [resolve_role_label(role_key) for role_key in secondary_roles]
    deferred_labels = [resolve_role_label(role_key) for role_key in deferred_roles]
    hidden_labels = [resolve_role_label(role_key) for role_key in hidden_roles]
    if copy_variant == "business_cn":
        pinned_section_summary = "\u7f6e\u9876\u6a21\u5757"
        deferred_section_summary = "\u540e\u7f6e\u6a21\u5757"
        hidden_section_summary = "\u9690\u85cf\u6a21\u5757"
    else:
        pinned_section_summary = "Pinned sections"
        deferred_section_summary = "Deferred sections"
        hidden_section_summary = "Hidden sections"
    if copy_variant == "business_cn":
        parts: list[str] = []
        if primary_labels:
            parts.append(f"\u4e3b\u8981\uff1a{' / '.join(primary_labels)}")
        if secondary_labels:
            parts.append(f"\u5176\u6b21\uff1a{' / '.join(secondary_labels)}")
        if deferred_labels:
            parts.append(f"\u540e\u7f6e\uff1a{' / '.join(deferred_labels)}")
        if hidden_labels:
            parts.append(f"\u9690\u85cf\uff1a{' / '.join(hidden_labels)}")
        if pinned_sections:
            parts.append(f"{pinned_section_summary}：{' / '.join(pinned_sections)}")
        if deferred_sections:
            parts.append(f"{deferred_section_summary}：{' / '.join(deferred_sections)}")
        if hidden_sections:
            parts.append(f"{hidden_section_summary}：{' / '.join(hidden_sections)}")
        summary_body = " | ".join(parts)
        if body and summary_body:
            summary_body = f"{body} | {summary_body}"
        elif body:
            summary_body = body
    else:
        parts = []
        if primary_labels:
            parts.append(f"Primary: {' / '.join(primary_labels)}")
        if secondary_labels:
            parts.append(f"Secondary: {' / '.join(secondary_labels)}")
        if deferred_labels:
            parts.append(f"Deferred: {' / '.join(deferred_labels)}")
        if hidden_labels:
            parts.append(f"Hidden: {' / '.join(hidden_labels)}")
        if pinned_sections:
            parts.append(f"{pinned_section_summary}: {' / '.join(pinned_sections)}")
        if deferred_sections:
            parts.append(f"{deferred_section_summary}: {' / '.join(deferred_sections)}")
        if hidden_sections:
            parts.append(f"{hidden_section_summary}: {' / '.join(hidden_sections)}")
        summary_body = " | ".join(parts)
        if body and summary_body:
            summary_body = f"{body} | {summary_body}"
        elif body:
            summary_body = body
    if not summary_body:
        return ""
    return f"{summary_label}: {summary_body}"


def _render_content_block_with_density(
    st: object,
    payload: dict[str, object],
    spec: dict[str, object],
    *,
    panel_density: str,
    surface_copy_variant: str = "default",
    focus_label: str = "",
    focus_tone: str = "",
    section_key: str = "",
) -> None:
    """Render content blocks while passing panel-density rhythm hints onward."""
    resolved_spec = _resolve_spec_copy_variant(
        spec,
        merge_keys=("title", "empty_message", "labels", "display_fields"),
    )
    content_style_spec = build_content_panel_style_spec(surface_copy_variant)
    anchor_id = _build_section_anchor_id(section_key)
    if anchor_id:
        st.markdown(
            f'<div id="{anchor_id}"></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        _build_content_section_header_markdown(
            str(resolved_spec["title"]),
            tone=str(resolved_spec.get("tone", "neutral")),
            panel_density=panel_density,
            focus_label=focus_label,
            focus_tone=focus_tone,
            style_spec=content_style_spec,
        )
        ,
        unsafe_allow_html=True,
    )
    value = payload.get(str(resolved_spec["data_key"]))
    if value in (None, "", [], {}):
        st.markdown(
            _build_empty_state_markdown(
                str(resolved_spec["empty_message"]),
                panel_density=panel_density,
                style_spec=content_style_spec,
            ),
            unsafe_allow_html=True,
        )
        return

    render_type = str(resolved_spec["render_type"])
    if render_type == "text":
        st.write(value)
        return
    if render_type == "health_summary":
        _render_health_summary_block(
            st,
            value,
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
        )
        return
    if render_type == "spotlight_summary":
        _render_grouped_summary_block(
            st,
            _build_spotlight_summary_view_model(value, resolved_spec),
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
            focus_tone=focus_tone,
            first_group_anchor_id=_build_primary_group_anchor_id(section_key),
        )
        return
    if render_type == "leader_grouped":
        _render_grouped_summary_block(
            st,
            _build_leader_grouped_view_model(value, resolved_spec),
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
            focus_tone=focus_tone,
            first_group_anchor_id=_build_primary_group_anchor_id(section_key),
        )
        return
    if render_type == "next_session_action_grouped":
        _render_grouped_summary_block(
            st,
            _build_next_session_action_grouped_view_model(value, resolved_spec),
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
            focus_tone=focus_tone,
            first_group_anchor_id=_build_primary_group_anchor_id(section_key),
        )
        return
    if render_type == "today_priority_grouped":
        _render_grouped_summary_block(
            st,
            _build_today_priority_grouped_view_model(value, resolved_spec),
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
            focus_tone=focus_tone,
            first_group_anchor_id=_build_primary_group_anchor_id(section_key),
        )
        return
    if render_type == "alerts_grouped":
        _render_grouped_summary_block(
            st,
            _build_alerts_grouped_view_model(value, resolved_spec),
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
            focus_tone=focus_tone,
            first_group_anchor_id=_build_primary_group_anchor_id(section_key),
        )
        return
    if render_type == "batch_list_grouped":
        _render_grouped_summary_block(
            st,
            _build_batch_list_grouped_view_model(value, resolved_spec),
            resolved_spec,
            panel_density=panel_density,
            surface_copy_variant=surface_copy_variant,
            focus_tone=focus_tone,
            first_group_anchor_id=_build_primary_group_anchor_id(section_key),
        )
        return
    if render_type == "key_value":
        st.json(value)
        return
    if render_type == "table":
        st.markdown(
            _build_content_detail_markdown(
                tone=str(resolved_spec.get("tone", "neutral")),
                body=str(content_style_spec.get("table_detail_body", "Formatted content table")),
                panel_density=panel_density,
                style_spec=content_style_spec,
            ),
            unsafe_allow_html=True,
        )
        rows = _build_table_rows_for_display(
            value,
            spec=resolved_spec,
            format_spec=build_kpi_value_format_spec(),
        )
        st.dataframe(
            rows,
            use_container_width=True,
        )
        return
    if render_type == "list":
        st.write(value)
        return

    st.markdown(
        _build_empty_state_markdown(
            str(resolved_spec["empty_message"]),
            panel_density=panel_density,
            style_spec=content_style_spec,
        ),
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
