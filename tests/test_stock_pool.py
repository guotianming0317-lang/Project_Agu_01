"""Tests for the stock observation universe."""

from __future__ import annotations

from pathlib import Path
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

from app.universe.stock_pool import (
    build_stock_pool_health_comparison,
    build_stock_pool_health_summary,
    get_all_stocks,
    get_high_priority_stocks,
    get_stocks_by_sector,
    save_stock_pool_health_snapshot,
    validate_stock_pool,
)


class StockPoolTests(unittest.TestCase):
    """Verify the observation universe shape and file-backed loading."""

    def test_get_all_stocks_returns_expected_core_sectors(self) -> None:
        stocks = get_all_stocks()

        self.assertGreaterEqual(len(stocks), 40)
        sectors = {stock["sector"] for stock in stocks}

        self.assertIn("AI\u5149\u6a21\u5757/CPO", sectors)
        self.assertIn("\u534a\u5bfc\u4f53\u6750\u6599", sectors)
        self.assertIn("\u534a\u5bfc\u4f53\u6c14\u4f53", sectors)
        self.assertIn("\u5148\u8fdb\u5c01\u88c5/Chiplet", sectors)

    def test_get_all_stocks_exposes_new_metadata_fields_for_default_rows(self) -> None:
        stocks = get_all_stocks()
        industrial_fulian = next(
            stock for stock in stocks if stock["code"] == "601138"
        )

        self.assertEqual("\u6caaA", industrial_fulian["market"])
        self.assertEqual("AI\u670d\u52a1\u5668/\u7b97\u529b\u786c\u4ef6", industrial_fulian["monitor_sector"])
        self.assertEqual("\u670d\u52a1\u5668/\u7cfb\u7edf\u96c6\u6210", industrial_fulian["chain_group"])
        self.assertEqual("core", industrial_fulian["pool_type"])

    def test_get_stocks_by_sector_filters_correctly(self) -> None:
        stocks = get_stocks_by_sector("\u534a\u5bfc\u4f53\u6c14\u4f53")

        self.assertEqual(3, len(stocks))
        self.assertTrue(all(stock["sector"] == "\u534a\u5bfc\u4f53\u6c14\u4f53" for stock in stocks))
        self.assertIn("688549", {stock["code"] for stock in stocks})

    def test_get_stocks_by_sector_returns_split_material_bucket(self) -> None:
        stocks = get_stocks_by_sector("\u534a\u5bfc\u4f53\u6750\u6599")

        self.assertEqual(11, len(stocks))
        self.assertTrue(all(stock["sector"] == "\u534a\u5bfc\u4f53\u6750\u6599" for stock in stocks))
        self.assertIn("688126", {stock["code"] for stock in stocks})

    def test_get_high_priority_stocks_only_returns_priority_one(self) -> None:
        stocks = get_high_priority_stocks()

        self.assertTrue(stocks)
        self.assertTrue(all(stock["priority"] == 1 for stock in stocks))

    def test_get_all_stocks_can_load_from_custom_json_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "custom_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600000",
                            "name": "Alpha",
                            "sector": "Custom-Sector",
                            "sub_sector": "Branch-A",
                            "priority": 1,
                            "notes": "json override",
                        },
                        {
                            "code": "600001",
                            "name": "Beta",
                            "sector": "Custom-Sector",
                            "sub_sector": "Branch-B",
                            "priority": 2,
                            "notes": "",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                stocks = get_all_stocks()

            self.assertEqual(2, len(stocks))
            self.assertEqual("600000", stocks[0]["code"])
            self.assertEqual("Custom-Sector", stocks[0]["sector"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_all_stocks_can_load_new_monitor_fields(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "custom_stock_pool_with_monitor_fields.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600020",
                            "name": "Alpha",
                            "monitor_sector": "AI鏈嶅姟鍣?绠楀姏纭欢",
                            "sub_sector": "鏈嶅姟鍣∣DM",
                            "priority": 1,
                            "market": "娌狝",
                            "chain_group": "鏈嶅姟鍣?绯荤粺闆嗘垚",
                            "pool_type": "extended",
                            "notes": "json override",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                stocks = get_all_stocks()

            self.assertEqual(1, len(stocks))
            self.assertEqual("AI鏈嶅姟鍣?绠楀姏纭欢", stocks[0]["sector"])
            self.assertEqual("AI鏈嶅姟鍣?绠楀姏纭欢", stocks[0]["monitor_sector"])
            self.assertEqual("娌狝", stocks[0]["market"])
            self.assertEqual("鏈嶅姟鍣?绯荤粺闆嗘垚", stocks[0]["chain_group"])
            self.assertEqual("extended", stocks[0]["pool_type"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_all_stocks_can_load_from_custom_csv_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "custom_stock_pool.csv"
        try:
            stock_pool_path.write_text(
                "\n".join(
                    [
                        "code,name,sector,sub_sector,priority,notes",
                        "600010,Alpha,CSV-Sector,Branch-A,1,csv override",
                        "600011,Beta,CSV-Sector,Branch-B,2,",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                stocks = get_all_stocks()
                filtered = get_stocks_by_sector("CSV-Sector")
                priority_stocks = get_high_priority_stocks()

            self.assertEqual(2, len(stocks))
            self.assertEqual(2, len(filtered))
            self.assertEqual(["600010"], [stock["code"] for stock in priority_stocks])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_reports_valid_custom_json_file(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "valid_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600100",
                            "name": "Alpha",
                            "sector": "Validation-Sector",
                            "sub_sector": "Branch-A",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertTrue(result["is_valid"])
            self.assertEqual(1, result["record_count"])
            self.assertEqual([], result["duplicate_codes"])
            self.assertEqual(["Validation-Sector"], result["unknown_sectors"])
            self.assertIn("\u534a\u5bfc\u4f53\u6750\u6599", result["registered_sectors"])
            self.assertIn("\u534a\u5bfc\u4f53\u6c14\u4f53", result["registered_sectors"])
            self.assertEqual({"Validation-Sector": 1}, result["sector_counts"])
            self.assertEqual({}, result["chain_group_counts"])
            self.assertEqual({1: 1}, result["priority_counts"])
            self.assertTrue(
                any(
                    "Sector coverage is narrow" in hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_accepts_monitor_sector_without_legacy_sector(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "valid_monitor_sector_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600101",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "priority": 1,
                            "market": "\u6caaA",
                            "pool_type": "core",
                            "chain_group": "\u6750\u6599",
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()
                stocks = get_all_stocks()

            self.assertTrue(result["is_valid"])
            self.assertEqual({"\u534a\u5bfc\u4f53\u6750\u6599": 1}, result["sector_counts"])
            self.assertEqual("\u534a\u5bfc\u4f53\u6750\u6599", stocks[0]["monitor_sector"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_get_all_stocks_defaults_new_fields_for_legacy_rows(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "legacy_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600021",
                            "name": "Alpha",
                            "sector": "\u534a\u5bfc\u4f53\u6750\u6599\u6c14\u4f53",
                            "sub_sector": "鐢靛瓙鐗规皵",
                            "priority": 1,
                            "notes": "",
                        },
                        {
                            "code": "600022",
                            "name": "Beta",
                            "sector": "PCB/楂橀€熸澘",
                            "sub_sector": "PCB",
                            "priority": 2,
                            "notes": "",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                stocks = get_all_stocks()

            self.assertEqual("\u534a\u5bfc\u4f53\u6750\u6599\u6c14\u4f53", stocks[0]["monitor_sector"])
            self.assertEqual("\u6750\u6599", stocks[0]["chain_group"])
            self.assertEqual("core", stocks[0]["pool_type"])
            self.assertEqual("", stocks[0]["market"])
            self.assertEqual("PCB", stocks[1]["chain_group"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_reports_duplicate_codes(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "duplicate_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600200",
                            "name": "Alpha",
                            "sector": "Validation-Sector",
                            "sub_sector": "Branch-B",
                            "priority": 1,
                            "notes": "",
                        },
                        {
                            "code": "600200",
                            "name": "Beta",
                            "sector": "Validation-Sector",
                            "sub_sector": "Branch-C",
                            "priority": 2,
                            "notes": "",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertFalse(result["is_valid"])
            self.assertEqual(["600200"], result["duplicate_codes"])
            self.assertEqual(["Validation-Sector"], result["unknown_sectors"])
            self.assertEqual({"Validation-Sector": 2}, result["sector_counts"])
            self.assertEqual({}, result["chain_group_counts"])
            self.assertEqual({1: 1, 2: 1}, result["priority_counts"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_warns_when_no_priority_one_names_exist(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "no_priority_one.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600301",
                            "name": "Alpha",
                            "sector": "Sector-A",
                            "sub_sector": "Branch-1",
                            "priority": 2,
                            "notes": "",
                        },
                        {
                            "code": "600302",
                            "name": "Beta",
                            "sector": "Sector-B",
                            "sub_sector": "Branch-2",
                            "priority": 3,
                            "notes": "",
                        },
                        {
                            "code": "600303",
                            "name": "Gamma",
                            "sector": "Sector-C",
                            "sub_sector": "Branch-3",
                            "priority": 2,
                            "notes": "",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertIn(
                "No priority-1 stocks are configured.",
                result["health_hints"],
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_reports_chain_group_counts(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "chain_group_counts_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600401",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "chain_group": "\u6750\u6599",
                            "priority": 1,
                            "notes": "",
                        },
                        {
                            "code": "600402",
                            "name": "Beta",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u524d\u9a71\u4f53",
                            "chain_group": "\u6750\u6599",
                            "priority": 2,
                            "notes": "",
                        },
                        {
                            "code": "600403",
                            "name": "Gamma",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6c14\u4f53",
                            "sub_sector": "\u7535\u5b50\u7279\u6c14",
                            "chain_group": "\u6c14\u4f53",
                            "priority": 1,
                            "notes": "",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual({"\u6750\u6599": 2, "\u6c14\u4f53": 1}, result["chain_group_counts"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_build_stock_pool_health_summary_reuses_validation_structure(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "health_summary_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600410",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "chain_group": "\u6750\u6599",
                            "pool_type": "core",
                            "priority": 1,
                            "notes": "",
                        },
                        {
                            "code": "600411",
                            "name": "Beta",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6c14\u4f53",
                            "sub_sector": "\u7535\u5b50\u7279\u6c14",
                            "chain_group": "\u6c14\u4f53",
                            "pool_type": "extended",
                            "priority": 2,
                            "notes": "",
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                summary = build_stock_pool_health_summary()

            self.assertEqual("valid", summary["status"])
            self.assertIn(summary["risk_level"], {"clean", "warning"})
            self.assertIn("\u5f53\u524d\u76d1\u63a7\u6c60\u504f\u5411\u6750\u6599\u94fe", summary["structure_summary"])
            self.assertIn("core\u6c60\u5360\u6bd4\u7ea6\u4e3a1/2", summary["structure_summary"])
            self.assertEqual({"\u534a\u5bfc\u4f53\u6750\u6599": 1, "\u534a\u5bfc\u4f53\u6c14\u4f53": 1}, summary["sector_counts"])
            self.assertEqual({"\u6750\u6599": 1, "\u6c14\u4f53": 1}, summary["chain_group_counts"])
            self.assertEqual({"core": 1, "extended": 1}, summary["pool_type_counts"])
            self.assertEqual({1: 1, 2: 1}, summary["priority_counts"])
            self.assertEqual(str(stock_pool_path), summary["source_path"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_stock_pool_health_comparison_reports_structure_changes(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "health_comparison_stock_pool.json"
        snapshot_path = temp_dir / "stock_pool_health_snapshot.json"
        try:
            baseline_records = [
                {
                    "code": "600420",
                    "name": "Alpha",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": "\u7845\u7247",
                    "chain_group": "\u6750\u6599",
                    "pool_type": "core",
                    "priority": 1,
                    "notes": "",
                },
                {
                    "code": "600421",
                    "name": "Beta",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6c14\u4f53",
                    "sub_sector": "\u7535\u5b50\u7279\u6c14",
                    "chain_group": "\u6c14\u4f53",
                    "pool_type": "extended",
                    "priority": 2,
                    "notes": "",
                },
            ]
            changed_records = [
                {
                    "code": "600420",
                    "name": "Alpha",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": "\u7845\u7247",
                    "chain_group": "\u6750\u6599",
                    "pool_type": "core",
                    "priority": 1,
                    "notes": "",
                },
                {
                    "code": "600422",
                    "name": "Gamma",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": "\u524d\u9a71\u4f53",
                    "chain_group": "\u6750\u6599",
                    "pool_type": "extended",
                    "priority": 2,
                    "notes": "",
                },
            ]
            stock_pool_path.write_text(
                json.dumps(baseline_records, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                    "MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                },
                clear=False,
            ):
                baseline_summary = build_stock_pool_health_summary()
                saved_path = save_stock_pool_health_snapshot(baseline_summary)

            self.assertEqual(snapshot_path, saved_path)
            self.assertTrue(snapshot_path.exists())

            stock_pool_path.write_text(
                json.dumps(changed_records, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {
                    "MONITOR_STOCK_POOL_PATH": str(stock_pool_path),
                    "MONITOR_STOCK_POOL_HEALTH_SNAPSHOT_PATH": str(snapshot_path),
                },
                clear=False,
            ):
                changed_summary = build_stock_pool_health_summary()
                comparison = build_stock_pool_health_comparison(changed_summary)

            self.assertTrue(comparison["baseline_exists"])
            self.assertEqual(str(snapshot_path), comparison["snapshot_path"])
            self.assertIn(
                "\u80a1\u7968\u6c60\u7ed3\u6784\u53d1\u751f\u53d8\u5316",
                comparison["comparison_summary"],
            )
            self.assertIn(
                "\u91cd\u70b9\u53d8\u5316\uff1a",
                comparison["highlight_summary"],
            )
            self.assertIn(
                "\u4ea7\u4e1a\u94fe\u5206\u7ec4",
                comparison["highlight_summary"],
            )
            self.assertIn("Priority-1 Focus Down", comparison["comparison_tags"])
            self.assertNotIn("Structure Stable", comparison["comparison_tags"])
            self.assertIn("\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d", comparison["comparison_tag_labels"])
            self.assertTrue(
                any(
                    group["group_key"] == "priority_focus"
                    and group["group_label"] == "\u4f18\u5148\u7ea7\u7126\u70b9"
                    and "\u4e00\u7ea7\u4f18\u5148\u5173\u6ce8\u4e0b\u964d" in group["tag_labels"]
                    for group in comparison["comparison_tag_groups"]
                )
            )
            self.assertTrue(comparison["baseline_saved_at"])
            self.assertIn("- \u677f\u5757 \u534a\u5bfc\u4f53\u6750\u6599: +1", comparison["change_rows"])
            self.assertIn("- \u677f\u5757 \u534a\u5bfc\u4f53\u6c14\u4f53: -1", comparison["change_rows"])
            self.assertIn("- \u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6750\u6599: +1", comparison["change_rows"])
            self.assertIn("- \u4ea7\u4e1a\u94fe\u5206\u7ec4 \u6c14\u4f53: -1", comparison["change_rows"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_warns_when_one_sector_is_too_concentrated(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "concentrated_stock_pool.json"
        try:
            records = [
                {
                    "code": f"6004{i:02d}",
                    "name": f"Name-{i}",
                    "sector": "Dominant",
                    "sub_sector": f"Branch-{i}",
                    "priority": 1 if i == 0 else 2,
                    "notes": "",
                }
                for i in range(7)
            ]
            records.extend(
                [
                    {
                        "code": "600480",
                        "name": "Edge-1",
                        "sector": "Other-A",
                        "sub_sector": "Branch-X",
                        "priority": 2,
                        "notes": "",
                    },
                    {
                        "code": "600481",
                        "name": "Edge-2",
                        "sector": "Other-B",
                        "sub_sector": "Branch-Y",
                        "priority": 3,
                        "notes": "",
                    },
                ]
            )
            stock_pool_path.write_text(
                json.dumps(records, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertTrue(
                any(
                    "Sector concentration is high" in hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_warns_when_one_chain_group_is_too_concentrated(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "concentrated_chain_group_stock_pool.json"
        try:
            records = [
                {
                    "code": f"6014{i:02d}",
                    "name": f"Name-{i}",
                    "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                    "sub_sector": f"Branch-{i}",
                    "chain_group": "\u6750\u6599",
                    "priority": 1 if i == 0 else 2,
                    "notes": "",
                }
                for i in range(7)
            ]
            records.extend(
                [
                    {
                        "code": "601480",
                        "name": "Edge-1",
                        "monitor_sector": "\u534a\u5bfc\u4f53\u6c14\u4f53",
                        "sub_sector": "\u7535\u5b50\u7279\u6c14",
                        "chain_group": "\u6c14\u4f53",
                        "priority": 2,
                        "notes": "",
                    },
                    {
                        "code": "601481",
                        "name": "Edge-2",
                        "monitor_sector": "\u534a\u5bfc\u4f53\u8bbe\u5907",
                        "sub_sector": "\u523b\u8680",
                        "chain_group": "\u8bbe\u5907",
                        "priority": 3,
                        "notes": "",
                    },
                ]
            )
            stock_pool_path.write_text(
                json.dumps(records, ensure_ascii=False),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertTrue(
                any(
                    "Chain-group concentration is high" in hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_keeps_registered_monitor_sector_clean(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "registered_sector_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600901",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual([], result["unknown_sectors"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_warns_when_sector_is_unregistered(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "unknown_sector_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600902",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u79d1",
                            "sub_sector": "\u7845\u7247",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual(["\u534a\u5bfc\u4f53\u6750\u79d1"], result["unknown_sectors"])
            self.assertTrue(
                any(
                    "Unknown monitor sectors detected" in hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_suggests_registered_sector_for_typo(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "unknown_sector_with_suggestion.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600903",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u79d1",
                            "sub_sector": "\u7845\u7247",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual(
                "\u534a\u5bfc\u4f53\u6750\u6599",
                result["unknown_sector_suggestions"]["\u534a\u5bfc\u4f53\u6750\u79d1"],
            )
            self.assertTrue(
                any(
                    "Possible sector match for \u534a\u5bfc\u4f53\u6750\u79d1: \u534a\u5bfc\u4f53\u6750\u6599"
                    == hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_keeps_registered_chain_group_clean(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "registered_chain_group_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600904",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "chain_group": "\u6750\u6599",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual([], result["unknown_chain_groups"])
            self.assertIn("\u6750\u6599", result["registered_chain_groups"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_suggests_registered_chain_group_for_typo(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "unknown_chain_group_with_suggestion.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600905",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "chain_group": "\u6750\u79d1",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual(["\u6750\u79d1"], result["unknown_chain_groups"])
            self.assertEqual("\u6750\u6599", result["unknown_chain_group_suggestions"]["\u6750\u79d1"])
            self.assertTrue(
                any(
                    "Possible chain-group match for \u6750\u79d1: \u6750\u6599" in hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_keeps_registered_market_and_pool_type_clean(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "registered_market_pool_type_stock_pool.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600906",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "market": "\u6caaA",
                            "pool_type": "core",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual([], result["unknown_markets"])
            self.assertEqual([], result["unknown_pool_types"])
            self.assertIn("\u6caaA", result["registered_markets"])
            self.assertIn("core", result["registered_pool_types"])
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_validate_stock_pool_suggests_registered_market_and_pool_type_for_typo(self) -> None:
        temp_dir = Path(tempfile.mkdtemp())
        stock_pool_path = temp_dir / "unknown_market_pool_type_with_suggestion.json"
        try:
            stock_pool_path.write_text(
                json.dumps(
                    [
                        {
                            "code": "600907",
                            "name": "Alpha",
                            "monitor_sector": "\u534a\u5bfc\u4f53\u6750\u6599",
                            "sub_sector": "\u7845\u7247",
                            "market": "\u6caaB",
                            "pool_type": "cores",
                            "priority": 1,
                            "notes": "",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with patch.dict(
                "os.environ",
                {"MONITOR_STOCK_POOL_PATH": str(stock_pool_path)},
                clear=False,
            ):
                result = validate_stock_pool()

            self.assertEqual(["\u6caaB"], result["unknown_markets"])
            self.assertEqual("\u6caaA", result["unknown_market_suggestions"]["\u6caaB"])
            self.assertEqual(["cores"], result["unknown_pool_types"])
            self.assertEqual("core", result["unknown_pool_type_suggestions"]["cores"])
            self.assertTrue(
                any(
                    "Possible market match for \u6caaB: \u6caaA" in hint
                    for hint in result["health_hints"]
                )
            )
            self.assertTrue(
                any(
                    "Possible pool-type match for cores: core" in hint
                    for hint in result["health_hints"]
                )
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

