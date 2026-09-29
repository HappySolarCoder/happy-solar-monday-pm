#!/usr/bin/env python3
"""Cancel-join fixtures: Quincy July 5/17, August 0/3, EV->PB first."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from build_project_management_hub import (  # noqa: E402
    cancellation_month_stats,
    extract_relation_ids,
    join_process_to_essential,
    latest_nonzero_month,
    load_fixture,
    normalize_name,
)

FIXTURE = ROOT / "tests" / "fixtures" / "quincy_cancel_join.json"
TEMPLATE = ROOT / "templates" / "project-management-hub.html"

JULY_CANCELLED = {
    "12421502532",  # Raftery
    "12421502541",  # Breaux
    "12656539533",  # Farmer
    "12678199341",  # Washington
    "12683621049",  # Both
}
JULY_OPEN = {
    "12457917606",  # Wray
    "12457908751",  # Bianchi
    "12457908756",  # Letterman
    "12468713975",  # Twersky
    "12553307294",  # McDowell
    "12553357497",  # Richard
    "12556157066",  # Palella
    "12589859765",  # Cuylear
    "12605727169",  # Green
    "12616208929",  # Hood
    "12628908700",  # Andol
    "12687264463",  # Gilbert
}
AUGUST_CREATED = {
    "12805983578",  # Curtis
    "12867539270",  # Tinney
    "12884246719",  # Mcniffe
}


class CancelJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.process_items, cls.ev_items = load_fixture(str(FIXTURE))
        cls.rows = join_process_to_essential(cls.process_items, cls.ev_items)
        cls.by_id = {row["project_id"]: row for row in cls.rows}
        cls.quincy = cancellation_month_stats(cls.rows, assigned_rep="Quincy Sermons")

    def test_normalize_name_last_first(self) -> None:
        self.assertEqual(normalize_name("Wray,  Sheilla"), "wray, sheilla")

    def test_july_is_five_of_seventeen(self) -> None:
        july = self.quincy["2026-07"]
        self.assertEqual(july["cancelled"], 5)
        self.assertEqual(july["created"], 17)
        cancelled_ids = {
            row["project_id"]
            for row in self.rows
            if row["assigned_rep"] == "Quincy Sermons"
            and row["created_at_iso"][:7] == "2026-07"
            and row["pm_bucket"].strip().lower() == "cancelled"
        }
        created_ids = {
            row["project_id"]
            for row in self.rows
            if row["assigned_rep"] == "Quincy Sermons"
            and row["created_at_iso"][:7] == "2026-07"
        }
        self.assertEqual(cancelled_ids, JULY_CANCELLED)
        self.assertEqual(created_ids, JULY_CANCELLED | JULY_OPEN)
        for pid in JULY_OPEN:
            self.assertNotEqual(self.by_id[pid]["pm_bucket"].lower(), "cancelled")

    def test_august_is_zero_of_three(self) -> None:
        august = self.quincy["2026-08"]
        self.assertEqual(august["cancelled"], 0)
        self.assertEqual(august["created"], 3)
        created_ids = {
            row["project_id"]
            for row in self.rows
            if row["assigned_rep"] == "Quincy Sermons"
            and row["created_at_iso"][:7] == "2026-08"
        }
        self.assertEqual(created_ids, AUGUST_CREATED)

    def test_ev_to_pb_relation_assigns_quincy_when_pb_relation_is_null(self) -> None:
        wray = self.by_id["12457917606"]
        self.assertEqual(wray["assigned_rep"], "Quincy Sermons")
        self.assertEqual(wray["join_method"], "relation")
        # Fixture PB relation columns are null — join came from EV -> PB.
        pb = next(item for item in self.process_items if item["id"] == "12457917606")
        for col in pb["column_values"]:
            if col["id"] in {"connect_boards2__1", "board_relation_mm52zx30"}:
                self.assertFalse(extract_relation_ids(col))

    def test_pb_to_ev_only_join_would_miss_wray(self) -> None:
        """Reproduce the live hub bug: reading only PB->EV drops Jul/Aug Quincy jobs."""
        stripped_ev = []
        for ev in self.ev_items:
            clone = dict(ev)
            clone["column_values"] = [
                col
                if col["id"] not in {"board_relation_mm1yysc4", "board_relation_mm52vqdj"}
                else {**col, "value": None, "text": ""}
                for col in ev.get("column_values") or []
            ]
            stripped_ev.append(clone)
        rows = join_process_to_essential(self.process_items, stripped_ev, use_fallbacks=False)
        wray = next(row for row in rows if row["project_id"] == "12457917606")
        self.assertNotEqual(wray["join_method"], "relation")
        stats = cancellation_month_stats(rows, assigned_rep="Quincy Sermons")
        self.assertLess(stats.get("2026-07", {}).get("created", 0), 17)

    def test_unique_name_fallback_assigns_quincy(self) -> None:
        row = self.by_id["90000000001"]
        self.assertEqual(row["assigned_rep"], "Quincy Sermons")
        self.assertEqual(row["join_method"], "name")
        self.assertEqual(row["created_at_iso"][:7], "2026-06")

    def test_ambiguous_name_does_not_assign(self) -> None:
        row = self.by_id["90000000011"]
        self.assertEqual(row["assigned_rep"], "Unassigned")
        self.assertIsNone(row["join_method"])

    def test_epc_filter_drops_other_dealer(self) -> None:
        self.assertNotIn("90000000021", self.by_id)

    def test_does_not_join_on_item_id_equality(self) -> None:
        row = self.by_id["77700000001"]
        self.assertNotEqual(row["assigned_rep"], "Zachary Maecker")
        self.assertNotEqual(row["join_method"], "relation")
        self.assertEqual(row["display_name"], "Collision, Process")

    def test_created_at_is_process_board_not_ev(self) -> None:
        wray = self.by_id["12457917606"]
        self.assertTrue(wray["created_at_iso"].startswith("2026-07-06"))
        ev = next(item for item in self.ev_items if str(item["id"]) == wray["essential_view_project_id"])
        self.assertTrue(str(ev["created_at"]).startswith("2025-"))

    def test_latest_nonzero_skips_empty_month(self) -> None:
        stats = {
            "2026-07": {"created": 17, "cancelled": 5, "rate": 5 / 17 * 100},
            "2026-08": {"created": 0, "cancelled": 0, "rate": 0.0},
        }
        month, bucket = latest_nonzero_month(stats)
        self.assertEqual(month, "2026-07")
        self.assertEqual(bucket["cancelled"], 5)
        # Real Quincy series: August has created>0 so latest is August 0/3.
        real = latest_nonzero_month(self.quincy)
        self.assertIsNotNone(real)
        self.assertEqual(real[0], "2026-08")
        self.assertEqual(real[1]["created"], 3)
        self.assertEqual(real[1]["cancelled"], 0)

    def test_address_fallback(self) -> None:
        row = self.by_id["90000000031"]
        self.assertEqual(row["assigned_rep"], "Ross Williamson")
        self.assertEqual(row["join_method"], "address")


class TemplateSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = TEMPLATE.read_text(encoding="utf-8")
        js = (TEMPLATE.parent / "hub-app.js")
        if js.exists():
            cls.html = cls.html + js.read_text(encoding="utf-8")

    def test_type_to_filter_inputs(self) -> None:
        self.assertIn('id="cancellationRepSearch"', self.html)
        self.assertIn('id="assignedRepSearch"', self.html)
        self.assertIn("multi-select-search", self.html)
        self.assertIn('id="cancellationRepMenu"', self.html)
        self.assertIn('id="assignedRepMenu"', self.html)
        # Sales Rep stays a custom multi-select, not a native select.
        self.assertNotRegex(self.html, r'<select[^>]+id="cancellationRepFilter"')
        self.assertNotRegex(self.html, r'<select[^>]+id="assignedRepFilter"')

    def test_latest_month_uses_created_gt_zero(self) -> None:
        self.assertTrue(
            "created > 0" in self.html or "created>0" in self.html,
            "latest cards must pick the last month with created > 0",
        )

    def test_stage_list_scrolls(self) -> None:
        self.assertIn("overflow-y: auto", self.html)
        self.assertIn("cancel-stage-list", self.html)
        self.assertIn("min-width: 0", self.html)

    def test_formula_copy(self) -> None:
        self.assertIn("created month", self.html.lower())
        self.assertIn("Cancelled", self.html)
        self.assertIn("created in that month", self.html.lower())


if __name__ == "__main__":
    unittest.main()
