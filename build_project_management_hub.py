#!/usr/bin/env python3
"""Rebuild public/project-management-hub.html from Monday or a local fixture.

Join starts at Essential View S-Rep and follows EV -> Process Board
(board_relation_mm1yysc4 / board_relation_mm52vqdj). PB -> EV columns are
often null (the live hub bug). Then unique name, then unique address.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROCESS_BOARD_ID = "6700296573"
ESSENTIAL_VIEW_BOARD_ID = "6691791537"
CANCELLED_GROUP_ID = "new_group"
MONDAY_API = "https://api.monday.com/v2"

EPC_COLUMN = "dropdown_mkpp9kz7"
EPC_ALIASES = {"happy slr", "happy solar", "epc-new"}

PB_RELATION_COLUMNS = ("connect_boards2__1", "board_relation_mm52zx30")
EV_RELATION_COLUMNS = ("board_relation_mm1yysc4", "board_relation_mm52vqdj")
S_REP_COLUMN = "people_mkm6c7vb"
# Never query or read EV text__1 (Customer DOB Account Password).
FORBIDDEN_COLUMNS = frozenset({"text__1"})

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = REPO_ROOT / "templates" / "project-management-hub.html"
DEFAULT_OUT = REPO_ROOT / "public" / "project-management-hub.html"


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_name(name: str) -> str:
    """Lowercase, collapse spaces, keep 'last, first' order."""
    text = unicodedata.normalize("NFKC", _as_text(name)).lower()
    text = text.replace(".", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*", ", ", text)
    return text


def normalize_address(value: str) -> str:
    """Lowercase, collapse spaces, strip punctuation that is not alphanumeric."""
    text = unicodedata.normalize("NFKC", _as_text(value)).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_jsonish(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8", "replace")
    if isinstance(value, str):
        raw = value.strip()
        if not raw or raw in {"null", "None"}:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return value


def extract_relation_ids(column_value: Any) -> list[str]:
    """Parse Monday relation column JSON / dict / linked_item_ids."""
    if column_value is None or column_value == "" or column_value is False:
        return []
    if isinstance(column_value, dict) and "value" in column_value and len(column_value) <= 4:
        # column_values entry: prefer value, then text of ids
        nested = extract_relation_ids(column_value.get("value"))
        if nested:
            return nested
        column_value = column_value.get("linked_item_ids") or column_value.get("linkedPulseIds")
    parsed = _parse_jsonish(column_value)
    if parsed is None or parsed == "" or parsed is False:
        return []
    ids: list[str] = []

    def add(item: Any) -> None:
        if item is None or item is False:
            return
        if isinstance(item, dict):
            for key in ("linkedPulseId", "linked_item_id", "item_id", "id"):
                if item.get(key) not in (None, ""):
                    add(item[key])
                    return
            return
        text = str(item).strip()
        if text.isdigit() or (text and text.replace("-", "").isalnum()):
            if text not in ids:
                ids.append(text)

    if isinstance(parsed, list):
        for entry in parsed:
            add(entry)
        return ids
    if isinstance(parsed, dict):
        for key in ("linked_item_ids", "linkedPulseIds", "item_ids", "linkedItems"):
            if key in parsed and parsed[key] is not None:
                for entry in parsed[key] if isinstance(parsed[key], list) else [parsed[key]]:
                    add(entry)
        if not ids:
            add(parsed)
        return ids
    add(parsed)
    return ids


def _column_map(item: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in item.get("column_values") or []:
        if not isinstance(col, dict):
            continue
        col_id = _as_text(col.get("id"))
        if not col_id or col_id in FORBIDDEN_COLUMNS:
            continue
        out[col_id] = col
    return out


def _column_text(col: Any) -> str:
    if col is None:
        return ""
    if isinstance(col, dict):
        for key in ("text", "display_value", "name"):
            if col.get(key):
                return _as_text(col[key])
        val = _parse_jsonish(col.get("value"))
        if isinstance(val, dict):
            if val.get("label"):
                return _as_text(val["label"])
            labels = val.get("labels") or val.get("personsAndTeams") or []
            if isinstance(labels, list) and labels:
                names = []
                for entry in labels:
                    if isinstance(entry, dict):
                        names.append(_as_text(entry.get("name") or entry.get("text") or entry.get("email")))
                    else:
                        names.append(_as_text(entry))
                return ", ".join(n for n in names if n)
        return _as_text(col.get("value"))
    return _as_text(col)


def is_happy_epc(column_value: Any) -> bool:
    text = _column_text(column_value).lower()
    if text in EPC_ALIASES:
        return True
    parsed = _parse_jsonish(column_value if not isinstance(column_value, dict) else column_value.get("value"))
    if isinstance(parsed, dict):
        label = _as_text(parsed.get("label") or (parsed.get("text"))).lower()
        if label in EPC_ALIASES:
            return True
    return False


def _item_address(item: dict[str, Any]) -> str:
    if item.get("address"):
        return _as_text(item["address"])
    cols = _column_map(item)
    for key in ("location", "text6", "address", "location__1"):
        if key in cols:
            text = _column_text(cols[key])
            if text:
                return text
    return ""


def _item_created_at(item: dict[str, Any]) -> str:
    raw = item.get("created_at") or item.get("created_at_iso") or ""
    return _as_text(raw)


def _group_title(item: dict[str, Any]) -> str:
    group = item.get("group") or {}
    if isinstance(group, dict):
        return _as_text(group.get("title") or group.get("name"))
    return _as_text(group)


def _group_id(item: dict[str, Any]) -> str:
    group = item.get("group") or {}
    if isinstance(group, dict):
        return _as_text(group.get("id"))
    return ""


def _assigned_rep_from_ev(ev: dict[str, Any] | None) -> str:
    if not ev:
        return "Unassigned"
    cols = _column_map(ev)
    text = _column_text(cols.get(S_REP_COLUMN))
    if ev.get("assigned_rep"):
        text = text or _as_text(ev.get("assigned_rep"))
    return text or "Unassigned"


def _unique_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("id") or id(item))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def join_process_to_essential(
    process_items: list[dict[str, Any]],
    ev_items: list[dict[str, Any]],
    use_fallbacks: bool = True,
) -> list[dict[str, Any]]:
    """One hub row per Happy-EPC Process Board item.

    Join order:
    1. EV -> PB relations (board_relation_mm1yysc4 / board_relation_mm52vqdj)
    2. PB -> EV relations (connect_boards2__1 / board_relation_mm52zx30)
    3. Unique normalized name (Last, First)
    4. Unique normalized address
    Never join on raw item-id equality.
    """
    ev_by_id = {str(item.get("id")): item for item in ev_items if item.get("id") not in (None, "")}

    pb_to_ev: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # START from EV, follow EV -> PB.
    for ev in ev_items:
        cols = _column_map(ev)
        for col_id in EV_RELATION_COLUMNS:
            for pb_id in extract_relation_ids(cols.get(col_id)):
                pb_to_ev[str(pb_id)].append(ev)

    # Also accept PB -> EV when those columns are populated.
    for pb in process_items:
        cols = _column_map(pb)
        pb_id = str(pb.get("id") or "")
        for col_id in PB_RELATION_COLUMNS:
            for ev_id in extract_relation_ids(cols.get(col_id)):
                ev = ev_by_id.get(str(ev_id))
                if ev:
                    pb_to_ev[pb_id].append(ev)

    name_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    addr_index: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in ev_items:
        name_key = normalize_name(ev.get("name") or "")
        if name_key:
            name_index[name_key].append(ev)
        addr_key = normalize_address(_item_address(ev))
        if addr_key:
            addr_index[addr_key].append(ev)

    rows: list[dict[str, Any]] = []
    for pb in process_items:
        cols = _column_map(pb)
        if not is_happy_epc(cols.get(EPC_COLUMN) or pb.get("epc")):
            continue
        pb_id = str(pb.get("id") or "")
        ev = None
        method = None

        related = _unique_items(pb_to_ev.get(pb_id, []))
        if len(related) == 1:
            ev, method = related[0], "relation"

        if ev is None and use_fallbacks:
            name_key = normalize_name(pb.get("name") or "")
            candidates = _unique_items(name_index.get(name_key, []))
            if len(candidates) == 1:
                ev, method = candidates[0], "name"

        if ev is None and use_fallbacks:
            addr_key = normalize_address(_item_address(pb))
            candidates = _unique_items(addr_index.get(addr_key, []))
            if len(candidates) == 1:
                ev, method = candidates[0], "address"

        created = _item_created_at(pb)
        group_title = _group_title(pb)
        if _group_id(pb) == CANCELLED_GROUP_ID and not group_title:
            group_title = "Cancelled"
        rows.append(
            {
                "project_id": pb_id,
                "essential_view_project_id": str(ev.get("id")) if ev else "",
                "display_name": _as_text(pb.get("name")),
                "pm_bucket": group_title,
                "pm_bucket_slug": _slugify(group_title),
                "section": _section_for(group_title),
                "process_bucket": group_title,
                "process_bucket_slug": _slugify(group_title),
                "source_process_bucket": group_title,
                "assigned_rep": _assigned_rep_from_ev(ev),
                "address": _item_address(pb) or (_item_address(ev) if ev else ""),
                "zip_code": "",
                "permit_ahj": "",
                "permit_phone": "",
                "permit_tat": "",
                "permit_zip_sla_days": "",
                "site_survey_date": "",
                "site_eval_scheduling": "",
                "electrical_review": "",
                "permit_status": "",
                "interconnection_status": "",
                "installation_dates": "",
                "first_installed_on": "",
                "install_cycle_days": "",
                "task_status": "",
                "calc_status": "",
                "finance_status": "",
                "monitoring_approval": "",
                "monitoring_status": "",
                "process_board_note": "",
                "essential_view_note": "",
                "process_board_note_date": "",
                "created_at_display": _display_created(created),
                "created_at_iso": created,
                "bucket_entered_at_iso": "",
                "bucket_entered_at_display": "",
                "days_in_bucket": pb.get("days_in_bucket") or 0,
                "board_url": f"https://nysessentialpower.monday.com/boards/{PROCESS_BOARD_ID}/pulses/{pb_id}" if pb_id else "",
                "cancel_source_stage": _as_text(pb.get("cancel_source_stage")),
                "sla_days": "",
                "uses_default_permit_sla": False,
                "sla_label": "",
                "is_over_sla": False,
                "join_method": method,
            }
        )
    return rows


def _slugify(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", _as_text(value).lower()).strip("-")
    return text


def _section_for(bucket: str) -> str:
    key = bucket.strip().lower()
    if key in {"cancelled", "on hold", "on hold 2026"} or "hold" in key or key.startswith("cancel"):
        return "hold_cancel"
    if any(token in key for token in ("post install", "pto", "electrical inspection", "monitoring", "needs return")):
        return "ep_installation"
    if any(token in key for token in ("stamp", "permit", "install", "pending", "job at risk", "qa / ntp", "esow qa")):
        return "ep_ops"
    return "onboarding"


def _display_created(iso: str) -> str:
    raw = _as_text(iso)
    if not raw:
        return ""
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return raw[:16].replace("T", " ")


def cancellation_month_stats(
    rows: list[dict[str, Any]],
    assigned_rep: str | None = None,
) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    needle = normalize_name(assigned_rep) if assigned_rep else ""
    for row in rows:
        if needle and normalize_name(row.get("assigned_rep") or "") != needle:
            continue
        month = _as_text(row.get("created_at_iso"))[:7]
        if not month:
            continue
        bucket = stats.setdefault(month, {"created": 0, "cancelled": 0, "rate": 0.0})
        bucket["created"] += 1
        if _as_text(row.get("pm_bucket")).lower() == "cancelled":
            bucket["cancelled"] += 1
    for bucket in stats.values():
        bucket["rate"] = (bucket["cancelled"] / bucket["created"] * 100) if bucket["created"] else 0.0
    return stats


def latest_nonzero_month(stats: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]] | None:
    for month in sorted((key for key, value in stats.items() if value.get("created", 0) > 0), reverse=True):
        return month, stats[month]
    return None


def load_fixture(path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "process_items" in data:
        return list(data.get("process_items") or []), list(data.get("ev_items") or [])
    raise ValueError(f"Fixture {path} must be an object with process_items and ev_items")


def _stage_card(stage: str, count: int, section: str) -> dict[str, Any]:
    return {
        "stage": stage,
        "full_name": stage,
        "display_label": stage,
        "short_label": stage[:18],
        "stage_slug": _slugify(stage),
        "count": count,
        "lane": "secondary" if section == "hold_cancel" else "primary",
        "section": section,
        "sla_days": None,
        "sla_mode": "bucket",
        "sla_label": "",
        "overdue_count": 0,
    }


def build_stage_cards(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    counts: dict[str, int] = {}
    sections: dict[str, str] = {}
    for row in rows:
        stage = _as_text(row.get("pm_bucket")) or "Unknown"
        counts[stage] = counts.get(stage, 0) + 1
        sections[stage] = row.get("section") or _section_for(stage)
    cards = [_stage_card(stage, counts[stage], sections[stage]) for stage in sorted(counts)]
    return {
        "all": cards,
        "onboarding": [c for c in cards if c["section"] == "onboarding"],
        "ep_ops": [c for c in cards if c["section"] == "ep_ops"],
        "ep_installation": [c for c in cards if c["section"] == "ep_installation"],
        "secondary": [c for c in cards if c["section"] == "hold_cancel"],
    }


def _rep_option_html(names: list[str]) -> str:
    parts = []
    for name in names:
        safe = escape(name, quote=True)
        parts.append(f'<label class="multi-select-option"><input type="checkbox" value="{safe}" /><span>{safe}</span></label>')
    return "".join(parts)


def render_hub(rows: list[dict[str, Any]], template_path: str, out_path: str) -> None:
    template = Path(template_path).read_text(encoding="utf-8")
    cards = build_stage_cards(rows)
    reps = sorted({_as_text(row.get("assigned_rep")) or "Unassigned" for row in rows}, key=str.lower)
    generated = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %I:%M %p %Z")
    replacements = {
        "/*__ROWS__*/": json.dumps(rows, ensure_ascii=False),
        "/*__STAGE_CARDS__*/": json.dumps(cards["all"], ensure_ascii=False),
        "/*__ONBOARDING_STAGE_CARDS__*/": json.dumps(cards["onboarding"], ensure_ascii=False),
        "/*__EP_OPS_STAGE_CARDS__*/": json.dumps(cards["ep_ops"], ensure_ascii=False),
        "/*__EP_INSTALLATION_STAGE_CARDS__*/": json.dumps(cards["ep_installation"], ensure_ascii=False),
        "/*__SECONDARY_STAGE_CARDS__*/": json.dumps(cards["secondary"], ensure_ascii=False),
        "/*__ASSIGNED_REP_OPTIONS__*/": _rep_option_html(reps),
        "/*__CANCELLATION_REP_OPTIONS__*/": _rep_option_html(reps),
        "/*__GENERATED_AT__*/": generated,
    }
    html = template
    for needle, value in replacements.items():
        html = html.replace(needle, value)
    dest = Path(out_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")


def _monday_graphql(token: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
    req = Request(
        MONDAY_API,
        data=payload,
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
            "API-Version": "2024-10",
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        raise SystemExit(f"Monday API HTTP {exc.code}") from exc
    except URLError as exc:
        raise SystemExit(f"Monday API error: {exc}") from exc
    if body.get("errors"):
        raise SystemExit(f"Monday API errors: {body['errors']}")
    return body["data"]


def fetch_board_items(token: str, board_id: str, column_ids: list[str]) -> list[dict[str, Any]]:
    safe_cols = [cid for cid in column_ids if cid not in FORBIDDEN_COLUMNS]
    query = """
    query ($boardId: [ID!]!, $cursor: String, $limit: Int!, $cols: [String!]) {
      boards(ids: $boardId) {
        items_page(limit: $limit, cursor: $cursor) {
          cursor
          items {
            id
            name
            created_at
            group { id title }
            column_values(ids: $cols) {
              id
              text
              value
            }
          }
        }
      }
    }
    """
    items: list[dict[str, Any]] = []
    cursor = None
    while True:
        data = _monday_graphql(
            token,
            query,
            {"boardId": [board_id], "cursor": cursor, "limit": 100, "cols": safe_cols},
        )
        page = (data.get("boards") or [{}])[0].get("items_page") or {}
        items.extend(page.get("items") or [])
        cursor = page.get("cursor")
        if not cursor:
            break
    return items


def fetch_monday_boards(token: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    process_cols = [EPC_COLUMN, *PB_RELATION_COLUMNS, "location"]
    ev_cols = [S_REP_COLUMN, *EV_RELATION_COLUMNS, "location"]
    process_items = fetch_board_items(token, PROCESS_BOARD_ID, process_cols)
    ev_items = fetch_board_items(token, ESSENTIAL_VIEW_BOARD_ID, ev_cols)
    return process_items, ev_items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Project Management Hub static page.")
    parser.add_argument("--rows-json", help="Fixture path with process_items + ev_items")
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--template", default=str(DEFAULT_TEMPLATE))
    args = parser.parse_args(argv)

    token = os.environ.get("MONDAY_API_TOKEN", "").strip()
    if args.rows_json:
        process_items, ev_items = load_fixture(args.rows_json)
    elif token:
        process_items, ev_items = fetch_monday_boards(token)
    else:
        print("MONDAY_API_TOKEN is missing. Pass --rows-json PATH to build from a fixture.", file=sys.stderr)
        return 2

    rows = join_process_to_essential(process_items, ev_items)
    if "MONDAY_API_TOKEN" in json.dumps(rows):
        raise SystemExit("refusing to write rows that embed a token")
    render_hub(rows, args.template, args.out)
    print(f"Wrote {args.out} with {len(rows)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
