"""Station <-> database tests. Need MySQL or MariaDB (skipped otherwise)."""
from __future__ import annotations

from datetime import datetime, timedelta

import mysql.connector

from device.db import AttendanceDB


def fresh_connection(settings):
    return mysql.connector.connect(host=settings.db_host, port=settings.db_port, user=settings.db_user,
                                   password=settings.db_password, database=settings.db_name)


def count(settings, sql, params=()):
    conn = fresh_connection(settings)
    cur = conn.cursor()
    cur.execute(sql, params)
    value = cur.fetchone()[0]
    conn.close()
    return value


def test_finger_maps_to_subject(demo_db):
    db = AttendanceDB(demo_db)
    s = db.subject_for_finger(4)
    assert (s.code, s.faculty_name) == ("maths", "Priya Deshmukh")
    assert db.subject_for_finger(99) is None
    assert db.student_roll_numbers()[:2] == ["TE01", "TE02"]
    db.close()


def test_each_photo_is_saved_even_if_the_station_stops(demo_db):
    """Every photo's result is committed at once, so a crash mid-lecture keeps what was seen."""
    db = AttendanceDB(demo_db)
    bee = db.subject_for_finger(1)
    lecture = db.start_lecture(bee.id, datetime(2024, 1, 15, 10, 0))
    db.record_photo(lecture, {"TE01": 0.31, "TE04": 0.402}, 0.6)
    db.record_photo(lecture, {"TE01": 0.29}, 0.6)
    db.conn.close()            # simulate a crash: no clean shutdown
    assert count(demo_db, "SELECT started_at FROM lectures WHERE id=%s", (lecture,)) == datetime(2024, 1, 15, 10, 0)
    assert count(demo_db, "SELECT photos FROM lectures WHERE id=%s", (lecture,)) == 2
    assert count(demo_db, "SELECT COUNT(*) FROM attendance WHERE lecture_id=%s", (lecture,)) == 10
    rows = dict(((r, (st, seen, float(d) if d is not None else None)) for r, st, seen, d in rows_of(demo_db, lecture)))
    assert rows["TE01"] == ("present", 2, 0.29)       # best distance kept
    assert rows["TE04"] == ("absent", 1, 0.402)       # 1 of 2 photos is below 60 %
    assert rows["TE02"] == ("absent", 0, None)


def rows_of(settings, lecture):
    conn = fresh_connection(settings)
    cur = conn.cursor()
    cur.execute("SELECT u.roll_no, a.status, a.seen, a.distance FROM attendance a JOIN users u ON u.id=a.student_id "
                "WHERE a.lecture_id=%s ORDER BY u.roll_no", (lecture,))
    out = cur.fetchall()
    conn.close()
    return out


def test_leaving_early_ends_as_absent(demo_db):
    db = AttendanceDB(demo_db)
    lecture = db.start_lecture(1, datetime(2024, 1, 15, 11, 0))
    photos = [{"TE01": .3, "TE05": .3}, {"TE01": .3, "TE05": .3}, {"TE01": .3}, {"TE01": .3}, {"TE01": .3}, {}]
    present = [db.record_photo(lecture, p, 0.6) for p in photos]
    assert present == [2, 2, 2, 1, 1, 1]              # TE05 counts at first (2 of 3), then drops out
    rows = {r: (st, seen) for r, st, seen, _ in rows_of(demo_db, lecture)}
    assert rows["TE01"] == ("present", 5) and rows["TE05"] == ("absent", 2)
    db.close()


def test_teacher_changes_are_not_overwritten_by_the_camera(demo_db):
    db = AttendanceDB(demo_db)
    lecture = db.start_lecture(1, datetime(2024, 1, 15, 12, 0))
    conn = fresh_connection(demo_db)
    cur = conn.cursor()
    cur.execute("UPDATE attendance a JOIN users u ON u.id=a.student_id SET a.status='leave', a.source='faculty' "
                "WHERE a.lecture_id=%s AND u.roll_no='TE03'", (lecture,))
    cur.execute("UPDATE attendance a JOIN users u ON u.id=a.student_id SET a.status='present', a.source='faculty' "
                "WHERE a.lecture_id=%s AND u.roll_no='TE07'", (lecture,))
    conn.commit()
    conn.close()
    db.record_photo(lecture, {"TE03": 0.3, "TE01": 0.3}, 0.6)
    rows = {r: st for r, st, _, _ in rows_of(demo_db, lecture)}
    assert rows["TE03"] == "leave" and rows["TE07"] == "present" and rows["TE01"] == "present"
    db.close()


def test_unknown_roll_numbers_are_ignored(demo_db):
    db = AttendanceDB(demo_db)
    lecture = db.start_lecture(1, datetime(2024, 1, 15, 13, 0))
    assert db.record_photo(lecture, {"NOPE": 0.2}, 0.6) == 0
    db.close()


def test_no_limit_on_lectures_per_subject(demo_db):
    """A subject can have any number of lectures."""
    db = AttendanceDB(demo_db)
    start = datetime(2027, 1, 1, 9, 0)
    for i in range(120):
        db.start_lecture(1, start + timedelta(days=i))
    assert count(demo_db, "SELECT COUNT(*) FROM lectures WHERE subject_id=1") == 128
    db.close()


def test_relink_finger_moves_it(demo_db):
    db = AttendanceDB(demo_db)
    assert db.set_finger_for_subject(4, "physics")
    assert db.subject_for_finger(4).code == "physics"
    assert count(demo_db, "SELECT finger_id FROM subjects WHERE code='maths'") is None
    assert not db.set_finger_for_subject(7, "nonexistent")
    db.close()


def test_excel_export_one_sheet_per_subject(demo_db, tmp_path):
    from openpyxl import load_workbook

    from device.tools.export_excel import HEADERS, write_workbook

    db = AttendanceDB(demo_db)
    rows = db.attendance_for_day(datetime(2026, 10, 19))   # Monday: maths + physics in the demo data
    db.close()
    path = tmp_path / "out.xlsx"
    assert write_workbook(rows, path) == 2
    wb = load_workbook(path)
    assert wb.sheetnames == ["maths", "physics"]
    ws = wb["maths"]
    assert [c.value for c in ws[1]] == HEADERS
    assert ws.max_row == 11                     # header + 10 students
    assert ws["E2"].value == "Monday" and ws["F2"].value == "09:00"
    assert ws["G2"].value.endswith("/6")


def test_excel_export_empty_day(tmp_path):
    from openpyxl import load_workbook

    from device.tools.export_excel import write_workbook

    path = tmp_path / "none.xlsx"
    assert write_workbook([], path) == 0
    assert load_workbook(path).sheetnames == ["No lectures"]


def test_mock_station_end_to_end(demo_db, capsys):
    """python -m device.main --mock ... writes a real lecture to the database."""
    from device import main as main_mod

    rc = main_mod.main(["--mock", "--finger", "4", "--present", "TE01,TE05,TE09", "--leave-early", "TE02",
                        "--lecture-seconds", "3", "--photos", "6", "--seed", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "|Welcome maths   |" in out
    lecture = count(demo_db, "SELECT MAX(id) FROM lectures")
    rows = {r: (st, seen) for r, st, seen, _ in rows_of(demo_db, lecture)}
    assert [r for r, (st, _) in rows.items() if st == "present"] == ["TE01", "TE05", "TE09"]
    assert rows["TE02"] == ("absent", 2)               # seen in the first 2 of 6 photos, then left
    assert count(demo_db, "SELECT photos FROM lectures WHERE id=%s", (lecture,)) == 6
    assert count(demo_db, "SELECT ended_at IS NOT NULL FROM lectures WHERE id=%s", (lecture,)) == 1
