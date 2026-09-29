# happy-solar-monday-pm

Static Project Management Hub for Happy Solar. Live at
https://happy-solar-monday-pm.vercel.app/project-management-hub.html

## Data source (Evan option 3 — 2026-09-29)

The **Essential Power Happy Slr installer spreadsheet** is the sole/primary
database (morning + EOD refresh):

https://docs.google.com/spreadsheets/d/12axTA4pt3s_yEkANHd-2soPvPZZTR9JOyypuf-FwlNs

Hub funnel / stages come from **Essential View Pipeline Phase** plus sheet
cancel/hold statuses. Process Board NY groups are **not** the stage grain.

### Stage lanes

| Lane | Pipeline Phase / status |
| --- | --- |
| Onboarding | Project Verification, Site Evaluation, Site Review |
| EP Ops | ENG/FIN/PERM, ESOW / Final Approval (Depricated), Install Ready |
| EP Installation | Being Installed, Build Inspection, Elec. Inspection, Post Install Evaluation, PTO, Finalized |
| Hold / Cancel | Validation Hold, HOLD, HOLD 2026, Cancelled |

**Cancelled** is derived when Intake NTP = `HO Cancelled`, Site Eval =
`Cancelled at door`, or Interconnection = `Cancel` / `CDG Cancellation`.
Prior Pipeline Phase (if any) is kept as `cancel_source_stage`.

Sheet has no Assigned Sales Rep and no created_at. Cancel-month charts use
sheet **Last updated** as a month proxy. Days-in-bucket / SLA are blank.

Monday Process Board join path remains in the builder for unit tests and
optional enrichment only (`--rows-json` / `MONDAY_API_TOKEN`). Never read EV
`text__1`.

## Build

From the installer sheet CSV (preferred):

    python3 build_project_management_hub.py --sheet-csv /path/to/HappySlr.csv

Or sheet JSON rows:

    python3 build_project_management_hub.py --sheet-json /path/to/rows.json

Offline Monday cancel-join fixture:

    python3 build_project_management_hub.py --rows-json tests/fixtures/quincy_cancel_join.json

Output: `public/project-management-hub.html` (+ companion `public/hub-data.js`).

## Test

    python3 -m unittest tests.test_cancel_join tests.test_sheet_pipeline -v

## Deploy notes

Framework-less static site (`vercel.json` serves `public/`). File-deploy only.
Do **not** run `vercel --prod` from this README — Charles is the prod gate
(preview deploy, then promote). No cloud agent required for this static hub.

No Firestore. Do not copy this into HappySolarCoder/happy-solar-reporting
dashboard routes.
