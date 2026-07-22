"""Tests for shared sector labels and grouping helpers."""

from __future__ import annotations

import unittest

from app.sectors import (
    DEFAULT_FOCUS_SECTORS,
    MATERIAL_CHAIN_LABEL,
    SEMICONDUCTOR_EQUIPMENT_SECTOR,
    SEMICONDUCTOR_GAS_SECTOR,
    SEMICONDUCTOR_MATERIAL_SECTOR,
    build_default_focus_sectors,
    is_material_related_sector,
)


class SectorHelpersTests(unittest.TestCase):
    """Verify shared sector helpers keep report and alert logic aligned."""

    def test_is_material_related_sector_matches_split_material_chain(self) -> None:
        self.assertTrue(is_material_related_sector(SEMICONDUCTOR_MATERIAL_SECTOR))
        self.assertTrue(is_material_related_sector(SEMICONDUCTOR_GAS_SECTOR))
        self.assertFalse(is_material_related_sector(SEMICONDUCTOR_EQUIPMENT_SECTOR))

    def test_build_default_focus_sectors_keeps_chain_and_equipment_as_base(self) -> None:
        self.assertEqual(list(DEFAULT_FOCUS_SECTORS), build_default_focus_sectors())
        self.assertEqual(
            [MATERIAL_CHAIN_LABEL, SEMICONDUCTOR_EQUIPMENT_SECTOR],
            build_default_focus_sectors(SEMICONDUCTOR_MATERIAL_SECTOR),
        )
        self.assertEqual(
            [
                "AI服务器/算力硬件",
                MATERIAL_CHAIN_LABEL,
                SEMICONDUCTOR_EQUIPMENT_SECTOR,
            ],
            build_default_focus_sectors("AI服务器/算力硬件"),
        )


if __name__ == "__main__":
    unittest.main()
