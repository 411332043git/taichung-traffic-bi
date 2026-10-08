"""ETL: data/11503.csv -> work/traffic_115_03.csv (UTF-8 with BOM), with sum checks.

Standard library only. The source file is opened read-only and never modified.
"""
import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "11503.csv"
DST = ROOT / "work" / "traffic_115_03.csv"

# source column -> output column (order = output order)
COLUMNS = {
    "序號": "序號",
    "年": "年",
    "月": "月",
    "日": "日",
    "時": "發生時段",
    "區": "行政區",
    "事故類型及型態": "事故類型及型態",
    "肇事因素主要": "肇事因素主要",
    "當事者區分_類別": "當事者區分_類別",
    "受傷數量": "受傷數量",
    "死亡數量": "死亡數量",
    "事故類別": "事故類別",
    "GPS座標X": "GPS座標X",
    "GPS座標Y": "GPS座標Y",
}
INT_COLS = ["受傷數量", "死亡數量", "發生時段"]


def clean(s: str) -> str:
    """Strip BOMs, NBSP, full-width space and surrounding whitespace."""
    return s.replace("﻿", "").replace(" ", " ").replace("　", " ").strip()


def read_source():
    # utf-8-sig removes one BOM; clean() removes the extra stacked BOMs.
    with open(SRC, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [clean(h) for h in next(reader)]
        rows = [[clean(v) for v in r] for r in reader if any(v.strip() for v in r)]
    return header, rows


def transform(header, rows):
    missing = [c for c in COLUMNS if c not in header]
    if missing:
        sys.exit(f"來源缺少欄位: {missing}")
    idx = {c: header.index(c) for c in COLUMNS}
    out = []
    for r in rows:
        rec = {new: r[idx[old]] for old, new in COLUMNS.items()}
        for c in INT_COLS:
            rec[c] = int(rec[c])  # raises on bad data, intentionally
        rec["發生日期"] = date(int(rec["年"]), int(rec["月"]), int(rec["日"])).isoformat()
        out.append(rec)
    return out


def write_output(out):
    fields = ["序號", "發生日期", "發生時段"] + [
        v for v in COLUMNS.values() if v not in ("序號", "發生時段", "年", "月", "日")
    ]
    DST.parent.mkdir(exist_ok=True)
    with open(DST, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out)
    return fields


def validate(src_rows, header):
    # Source totals come straight from the raw rows (independent of transform).
    i_inj, i_dead, i_id = header.index("受傷數量"), header.index("死亡數量"), header.index("序號")
    src = (
        len(src_rows),
        sum(int(r[i_inj]) for r in src_rows),
        sum(int(r[i_dead]) for r in src_rows),
    )
    # Output totals come from re-reading the written file.
    with open(DST, "r", encoding="utf-8-sig", newline="") as f:
        back = list(csv.DictReader(f))
    dst = (len(back), sum(int(r["受傷數量"]) for r in back), sum(int(r["死亡數量"]) for r in back))

    print("=== 驗證 (來源 vs 輸出) ===")
    ok = True
    for name, a, b in zip(("總件數", "總受傷人數", "總死亡人數"), src, dst):
        flag = "OK" if a == b else "不一致"
        ok &= a == b
        print(f"{name}: 來源={a:,}  輸出={b:,}  {flag}")
    ids = [r[i_id] for r in src_rows]
    print(f"序號重複數: {len(ids) - len(set(ids))}")
    print(f"月份範圍: {min(r['發生日期'] for r in back)} ~ {max(r['發生日期'] for r in back)}")
    print(f"發生時段範圍: {min(int(r['發生時段']) for r in back)} ~ {max(int(r['發生時段']) for r in back)}")
    with open(DST, "rb") as f:
        print("輸出含 UTF-8 BOM:", f.read(3) == b"\xef\xbb\xbf")
    print("行政區數:", len({r["行政區"] for r in back}))
    return ok


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    header, rows = read_source()
    print(f"讀入 {len(rows):,} 筆, {len(header)} 欄 (來源: {SRC.name})")
    out = transform(header, rows)
    fields = write_output(out)
    print(f"已輸出 {DST.relative_to(ROOT)} ({len(fields)} 欄: {', '.join(fields)})")
    if not validate(rows, header):
        sys.exit("驗證失敗")


if __name__ == "__main__":
    main()
