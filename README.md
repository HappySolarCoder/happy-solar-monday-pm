# happy-solar-monday-pm

Static Project Management Hub for Happy Solar. Live preview historically at
https://happy-solar-monday-pm.vercel.app/project-management-hub.html

Process Board NY (`6700296573`) is the grain for cancel / hold / install.
Assigned sales rep is enriched from Essential View (`6691791537`) only.

## Cancel formula

- **Created month:** Process Board item `created_at`, UTC `YYYY-MM` (`iso.slice(0, 7)`). Do not use Essential View `created_at` or `date__1`.
- **Denominator:** EPC `dropdown_mkpp9kz7` is one of `Happy Slr` / `Happy Solar` / `EPC-new`.
- **Numerator:** current group title is `Cancelled` (group id `new_group`).
- **Rate:** currently Cancelled created that month / all created that month.
- **S-Rep:** Essential View `people_mkm6c7vb` is enrichment only.
- **Join:** start from EV S-Rep and follow EV to PB (`board_relation_mm1yysc4`, `board_relation_mm52vqdj`). Also accept PB to EV (`connect_boards2__1`, `board_relation_mm52zx30`) when filled. If both relation directions are empty, fall back to a unique normalized name (`Last, First`), then a unique address (EV location). Do not join on Item ID. Do not read EV `text__1`.

The live hub only walked PB to EV. Those columns are null on the Jul/Aug Happy Slr rows, so Quincy showed 2/2 in July and 0/0 in August. Monday math with EV to PB is **5/17** (Jul) and **0/3** (Aug).

Latest-month cards use the last month with `created > 0`. Empty `0/0` months are not presented as `0.0%` latest.

Sales Rep in the cancellation popup (and the page Assigned Sales Rep filter) is a type-to-filter checkbox menu, not a plain select.

## Build

From a Monday token (never committed):

    MONDAY_API_TOKEN=... python3 build_project_management_hub.py

Offline / CI, from the Quincy lock fixture:

    python3 build_project_management_hub.py --rows-json tests/fixtures/quincy_cancel_join.json

Output: `public/project-management-hub.html`.

## Test

    python3 -m unittest tests.test_cancel_join -v

## Deploy notes

This is a framework-less static site (`vercel.json` serves `public/`). Do **not** run `vercel --prod` from this README. Preview / static only. Vercel git linking can be added later; this repo is the source.

No Firestore. Do not copy this into HappySolarCoder/happy-solar-reporting dashboard routes.
