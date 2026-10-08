# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Current state

Early-stage project (`taichung-traffic-bi`, a BI project on Taichung traffic accidents). The repo has one commit and no source code, build system, tests, or linter yet. `README.md` is just the title. `docs/` and `work/` are empty placeholders. Do not invent build/test commands; add them here once tooling exists.

## Data

`data/11503.csv` is the only dataset. It is untracked in git (`data/` shows as `??`), so decide with the user before committing it (about 3.4 MB).

- Taichung City (臺中市) traffic accident records for March 2026 (`年`=2026, `月`=03). The filename `11503` looks like a ROC-calendar year-month (115 = 2026, 03).
- 11,974 rows, 1 header row, 53 columns. `序號` is unique per row.
- Encoding quirks:
  - The file starts with **four stacked UTF-8 BOMs**. Read with `encoding="utf-8-sig"`, which strips only one, so also strip leftover `﻿` from the first column name.
  - Every data field is double-quoted, and the header is not.
- All columns except the geo and location text fields are **numeric category codes** (weather, road type, speed limit, accident type, party type, and so on). The CSV has no code tables, so decoding them needs the official Taiwan road-accident data dictionary. Do not guess code meanings.
- Notable columns:
  - Time: `年, 月, 日, 時, 分`
  - Location: `區` (district), `GPS座標X`/`GPS座標Y` (WGS84 lon/lat, e.g. 120.66, 24.07)
  - Severity: `死亡數量`, `受傷數量`
  - Classification: `事故類別` (last column)
- The `2-30` column is a published field (30-day deaths in the official schema). Keep its name as it is.
- Columns `機關代碼, 市話, 傳真, 縣市別代碼` are constant reporting-agency metadata with no analytic value.
