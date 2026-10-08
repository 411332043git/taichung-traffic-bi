"""Build docs/data.js (window.TRAFFIC_DATA) from work/traffic_115_03.csv.

Standard library only. Output is a plain <script>-loadable file so docs/index.html
works from file:// with no server.
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "work" / "traffic_115_03.csv"
DST = ROOT / "docs" / "data.js"
ALL = "全區"
TOP_N = 8
EXPECT = (11974, 7663, 12)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    with open(SRC, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    districts = sorted({r["行政區"] for r in rows})
    days = sorted({r["發生日期"] for r in rows})

    summary = {d: {"count": 0, "injured": 0, "dead": 0} for d in districts}
    hourly = {k: [0] * 24 for k in [ALL] + districts}
    daily = {k: {d: 0 for d in days} for k in [ALL] + districts}
    BLANK = "(空白)"  # type field is empty on ~15% of rows; keep it as its own group
    for r in rows:
        r["事故類型及型態"] = r["事故類型及型態"] or BLANK
    type_all = Counter(r["事故類型及型態"] for r in rows)
    top = [t for t, _ in type_all.most_common(TOP_N)]
    types = {k: Counter() for k in [ALL] + districts}

    for r in rows:
        d = r["行政區"]
        s = summary[d]
        s["count"] += 1
        s["injured"] += int(r["受傷數量"])
        s["dead"] += int(r["死亡數量"])
        h = int(r["發生時段"])
        t = r["事故類型及型態"] if r["事故類型及型態"] in top else "其他"
        for k in (ALL, d):
            hourly[k][h] += 1
            daily[k][r["發生日期"]] += 1
            types[k][t] += 1

    total = {
        "count": sum(s["count"] for s in summary.values()),
        "injured": sum(s["injured"] for s in summary.values()),
        "dead": sum(s["dead"] for s in summary.values()),
    }
    summary[ALL] = total

    type_order = top + ["其他"]  # ranked by overall count, 其他 last
    data = {
        "meta": {"period": "2026-03", "source": "traffic_115_03.csv", "all": ALL},
        "districts": districts,
        "summary": summary,
        "hourly": hourly,  # {區: [24 counts]}
        "typeOrder": type_order,  # codes of 事故類型及型態 (no code table available)
        "types": {k: [c[t] for t in type_order] for k, c in types.items()},
        "days": days,
        "daily": {k: [v[d] for d in days] for k, v in daily.items()},
    }

    DST.parent.mkdir(exist_ok=True)
    js = "window.TRAFFIC_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    DST.write_text(js, encoding="utf-8")

    # --- checks ---
    got = (total["count"], total["injured"], total["dead"])
    print(f"已輸出 {DST.relative_to(ROOT)}  {DST.stat().st_size / 1024:.1f} KB")
    print(f"行政區 {len(districts)} 個, 日期 {days[0]}~{days[-1]} ({len(days)} 天), 類型 Top{TOP_N}: {top}")
    print(f"總件數/受傷/死亡: {got}  預期 {EXPECT}  {'OK' if got == EXPECT else '不一致'}")
    checks = {
        "時段加總": sum(hourly[ALL]) == total["count"],
        "每日加總": sum(data["daily"][ALL]) == total["count"],
        "類型加總": sum(data["types"][ALL]) == total["count"],
        "各區時段加總=各區件數": all(sum(hourly[d]) == summary[d]["count"] for d in districts),
        "各區每日加總=各區件數": all(sum(data["daily"][d]) == summary[d]["count"] for d in districts),
        "各區類型加總=各區件數": all(sum(data["types"][d]) == summary[d]["count"] for d in districts),
    }
    for k, v in checks.items():
        print(f"{k}: {'OK' if v else '失敗'}")
    if got != EXPECT or not all(checks.values()):
        sys.exit("驗證失敗")


if __name__ == "__main__":
    main()
