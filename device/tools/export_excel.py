"""Export one day's attendance to Excel: one worksheet per subject.

This is the "attendance sheet generation and import to Excel" step from the
team's paper. Each row: roll no, name, subject, date, day, time, photos seen in, status.

    python -m device.tools.export_excel                 # today
    python -m device.tools.export_excel 2024-01-15 -o reports/
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

HEADERS = ["Roll No", "Name", "Subject", "Date", "Day", "Time", "Seen in photos", "Status"]


def write_workbook(rows, path: Path) -> int:
    """rows: (subject code, subject name, started_at, roll no, name, seen, photos, status). Returns sheets written."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill

    wb = Workbook()
    wb.remove(wb.active)
    fills = {"present": "E3F4E3", "absent": "FBE4E4", "leave": "FFF4D6"}
    sheets: dict[str, object] = {}
    for code, name, started, roll, student, seen, photos, status in rows:
        title = code[:31]
        ws = sheets.get(title)
        if ws is None:
            ws = wb.create_sheet(title)
            ws.append(HEADERS)
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for col, width in zip("ABCDEFGH", (10, 24, 30, 12, 11, 8, 15, 10)):
                ws.column_dimensions[col].width = width
            ws.freeze_panes = "A2"
            sheets[title] = ws
        ws.append([roll, student, name, started.strftime("%Y-%m-%d"), started.strftime("%A"),
                   started.strftime("%H:%M"), f"{seen}/{photos}", status])
        ws.cell(ws.max_row, 8).fill = PatternFill("solid", fgColor=fills.get(status, "FFFFFF"))
    if not sheets:
        ws = wb.create_sheet("No lectures")
        ws.append(["No lectures were held on this day."])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return len(sheets)


def main(argv: list[str] | None = None) -> int:
    from ..config import load_settings
    from ..db import AttendanceDB

    s = load_settings()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("date", nargs="?", help="YYYY-MM-DD (default: today)")
    ap.add_argument("-o", "--out", type=Path, default=Path("."), help="folder for the .xlsx file")
    args = ap.parse_args(argv)
    day = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now(ZoneInfo(s.timezone))
    db = AttendanceDB(s)
    try:
        rows = db.attendance_for_day(day)
    finally:
        db.close()
    path = args.out / f"attendance_{day:%Y-%m-%d}.xlsx"
    n = write_workbook(rows, path)
    print(f"Wrote {path} ({n} subject sheets, {len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
