#!/usr/bin/env python3
"""Option 3: hub stages from Essential View Pipeline Phase + sheet statuses."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from build_project_management_hub import (
    build_stage_cards,
    cancellation_month_stats,
    render_hub,
    rows_from_sheet,
)


SAMPLE = [
    {
        "Monday Item ID": "1",
        "Project Name": "Alpha, A",
        "Customer Address": "1 Main St",
        "EPC NEW": "Happy Slr",
        "Essential View Pipeline Phase": "Project Verification",
        "Intake NTP Check": "NTP / Closed",
        "Site Evaluation Scheduling": "Needs Confirmation",
        "Interconnection Status": "Not Specified",
        "Permit Status": "Ready For Permit",
        "Last updated": "2026-09-29 12:00:00 UTC",
        "Monitoring Status": "TBD",
    },
    {
        "Monday Item ID": "2",
        "Project Name": "Beta, B",
        "Customer Address": "2 Main St",
        "EPC NEW": "Happy Slr",
        "Essential View Pipeline Phase": "Site Review",
        "Intake NTP Check": "HO Cancelled",
        "Site Evaluation Scheduling": "Site Eval Complete",
        "Interconnection Status": "Not Specified",
        "Permit Status": "Ready For Permit",
        "Last updated": "2026-09-15 12:00:00 UTC",
        "Monitoring Status": "TBD",
    },
    {
        "Monday Item ID": "3",
        "Project Name": "Gamma, G",
        "Customer Address": "3 Main St",
        "EPC NEW": "Happy Slr",
        "Essential View Pipeline Phase": "Being Installed",
        "Intake NTP Check": "NTP / Closed",
        "Site Evaluation Scheduling": "Site Eval Complete",
        "Interconnection Status": "PTI Approved",
        "Permit Status": "PERMIT RECEIVED",
        "Last updated": "2026-09-20 12:00:00 UTC",
        "Monitoring Status": "TBD",
        "Installation Date(s)": "2026-09-18",
    },
    {
        "Monday Item ID": "4",
        "Project Name": "Hold, H",
        "Customer Address": "4 Main St",
        "EPC NEW": "Happy Slr",
        "Essential View Pipeline Phase": "HOLD 2026",
        "Intake NTP Check": "Issue Found",
        "Site Evaluation Scheduling": "Needs Confirmation",
        "Interconnection Status": "Not Specified",
        "Permit Status": "Ready For Permit",
        "Last updated": "2026-09-10 12:00:00 UTC",
        "Monitoring Status": "TBD",
    },
]


class SheetPipelineTests(unittest.TestCase):
    def test_pipeline_phase_is_stage_grain(self):
        rows = rows_from_sheet(SAMPLE)
        by_name = {r["display_name"]: r for r in rows}
        self.assertEqual(by_name["Alpha, A"]["pm_bucket"], "Project Verification")
        self.assertEqual(by_name["Alpha, A"]["section"], "onboarding")
        self.assertEqual(by_name["Gamma, G"]["section"], "ep_installation")
        self.assertEqual(by_name["Hold, H"]["section"], "hold_cancel")

    def test_ho_cancelled_becomes_cancelled_bucket(self):
        rows = rows_from_sheet(SAMPLE)
        beta = next(r for r in rows if r["display_name"] == "Beta, B")
        self.assertEqual(beta["pm_bucket"], "Cancelled")
        self.assertEqual(beta["section"], "hold_cancel")
        self.assertEqual(beta["cancel_source_stage"], "Site Review")

    def test_stage_cards_lanes(self):
        cards = build_stage_cards(rows_from_sheet(SAMPLE))
        onboarding = {c["stage"] for c in cards["onboarding"]}
        self.assertIn("Project Verification", onboarding)
        secondary = {c["stage"] for c in cards["secondary"]}
        self.assertIn("Cancelled", secondary)
        self.assertIn("HOLD 2026", secondary)

    def test_cancel_month_uses_last_updated_proxy(self):
        stats = cancellation_month_stats(rows_from_sheet(SAMPLE))
        self.assertEqual(stats["2026-09"]["created"], 4)
        self.assertEqual(stats["2026-09"]["cancelled"], 1)

    def test_non_happy_epc_skipped(self):
        rows = rows_from_sheet(
            SAMPLE
            + [
                {
                    "Monday Item ID": "9",
                    "Project Name": "Other",
                    "EPC NEW": "Other EPC",
                    "Essential View Pipeline Phase": "Site Review",
                    "Last updated": "2026-09-29 12:00:00 UTC",
                }
            ]
        )
        self.assertEqual(len(rows), 4)

    def test_render_smoke(self):
        rows = rows_from_sheet(SAMPLE)
        template = Path(__file__).resolve().parents[1] / "templates" / "project-management-hub.html"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "hub.html"
            render_hub(rows, str(template), str(out))
            html = out.read_text(encoding="utf-8")
            self.assertIn("Project Verification", html)
            self.assertIn("Alpha, A", html)
            self.assertIn("Essential View Pipeline Phase", html)
            self.assertNotIn("/*__ROWS__*/", html)


if __name__ == "__main__":
    unittest.main()
