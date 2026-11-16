"""Generate database/demo_data.sql: made-up people and attendance for demos and tests.

All names and e-mail addresses are invented. Every demo account uses the
password  Demo@123  (see README). Run from the repository root:

    python scripts/make_demo_data.py
"""
import random
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "database" / "demo_data.sql"
PASSWORD = "Demo@123"
PHOTOS = 6  # classroom photos per lecture (CAPTURE_COUNT)

FACULTY = [  # first, last, email
    ("Priya", "Deshmukh", "priya.deshmukh@example.com"),
    ("Rahul", "Menon", "rahul.menon@example.com"),
    ("Sneha", "Kulkarni", "sneha.kulkarni@example.com"),
    ("Vikram", "Rao", "vikram.rao@example.com"),
    ("Anita", "Joshi", "anita.joshi@example.com"),
]
# code, name, faculty index, fingerprint slot
SUBJECTS = [
    ("maths", "Engineering Mathematics", 0, 4),
    ("physics", "Engineering Physics", 1, 5),
    ("chemistry", "Engineering Chemistry", 2, 2),
    ("ema", "EMA", 3, 3),
    ("bee", "Basic Electrical Engineering", 4, 1),
]
# roll no, first, last, how often this student attends (0..1)
STUDENTS = [
    ("TE01", "Aarav", "Sharma", 0.99),
    ("TE02", "Isha", "Patel", 0.95),
    ("TE03", "Rohan", "Kulkarni", 0.42),
    ("TE04", "Meera", "Iyer", 0.79),
    ("TE05", "Kabir", "Singh", 0.66),
    ("TE06", "Ananya", "Nair", 0.91),
    ("TE07", "Dev", "Chavan", 0.58),
    ("TE08", "Sara", "Fernandes", 0.84),
    ("TE09", "Yash", "Gupta", 0.73),
    ("TE10", "Tanvi", "More", 0.97),
]


def php_hash(password: str) -> str:
    """Use PHP itself so the hash is exactly what password_verify() expects."""
    return subprocess.check_output(
        ["php", "-r", "echo password_hash($argv[1], PASSWORD_DEFAULT);", password], text=True
    )


def q(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


def main() -> None:
    rnd = random.Random(42)
    pw = php_hash(PASSWORD)
    lines = [
        "-- Demo data for the Smart Attendance System. All people are made up.",
        f"-- Every account's password: {PASSWORD}",
        "SET NAMES utf8mb4;",
        "SET time_zone = '+05:30';  -- times below are India time (APP_TIMEZONE)",
        "SET FOREIGN_KEY_CHECKS = 0;",
        "TRUNCATE attendance; TRUNCATE lectures; TRUNCATE messages; TRUNCATE announcements;",
        "TRUNCATE subjects; TRUNCATE users;",
        "SET FOREIGN_KEY_CHECKS = 1;",
        "",
    ]
    uid = 0
    faculty_ids = []
    for first, last, email in FACULTY:
        uid += 1
        faculty_ids.append(uid)
        lines.append(
            "INSERT INTO users (id, role, roll_no, first_name, last_name, email, password_hash) VALUES "
            f"({uid}, 'faculty', NULL, {q(first)}, {q(last)}, {q(email)}, {q(pw)});"
        )
    student_ids = []
    for roll, first, last, _ in STUDENTS:
        uid += 1
        student_ids.append(uid)
        email = f"{first.lower()}.{last.lower()}@example.com"
        lines.append(
            "INSERT INTO users (id, role, roll_no, first_name, last_name, email, password_hash) VALUES "
            f"({uid}, 'student', {q(roll)}, {q(first)}, {q(last)}, {q(email)}, {q(pw)});"
        )
    lines.append("")
    for sid, (code, name, fidx, finger) in enumerate(SUBJECTS, start=1):
        lines.append(
            "INSERT INTO subjects (id, code, name, faculty_id, finger_id) VALUES "
            f"({sid}, {q(code)}, {q(name)}, {faculty_ids[fidx]}, {finger});"
        )
    lines.append("")

    # Four weeks of lectures: each subject twice a week, at a fixed time slot.
    start = datetime(2026, 10, 19, 9, 0)  # a Monday
    slots = {1: (0, 3, 9), 2: (0, 2, 10), 3: (1, 3, 11), 4: (1, 4, 13), 5: (2, 4, 14)}
    lecture_id = 0
    for week in range(4):
        for sid, (day_a, day_b, hour) in slots.items():
            for day in (day_a, day_b):
                lecture_id += 1
                begin = start + timedelta(weeks=week, days=day) - timedelta(hours=9) + timedelta(hours=hour)
                end = begin + timedelta(hours=1)
                lines.append(
                    "INSERT INTO lectures (id, subject_id, started_at, ended_at, photos) VALUES "
                    f"({lecture_id}, {sid}, '{begin:%Y-%m-%d %H:%M:%S}', '{end:%Y-%m-%d %H:%M:%S}', {PHOTOS});"
                )
                rows = []
                for stu_id, (_, _, _, rate) in zip(student_ids, STUDENTS):
                    roll = rnd.random()
                    if roll < rate * 0.94:           # stayed for the lecture: seen in most photos
                        status, seen, dist = "present", rnd.choice([4, 5, 5, 6, 6, 6]), f"{rnd.uniform(0.28, 0.46):.3f}"
                    elif roll < rate:                # came, was seen at the start, then left
                        status, seen, dist = "absent", rnd.choice([1, 2, 2, 3]), f"{rnd.uniform(0.30, 0.46):.3f}"
                    elif roll < rate + 0.04:         # leave approved by the teacher
                        status, seen, dist = "leave", 0, None
                    else:
                        status, seen, dist = "absent", 0, None
                    source = "faculty" if status == "leave" else "face"
                    rows.append(f"({lecture_id}, {stu_id}, '{status}', '{source}', {seen}, {dist or 'NULL'})")
                lines.append(
                    "INSERT INTO attendance (lecture_id, student_id, status, source, seen, distance) VALUES "
                    + ", ".join(rows) + ";"
                )
    lines.append("")
    msgs = [
        (student_ids[2], faculty_ids[0], "Leave application",
         "Respected Ma'am, I was unwell and could not attend Thursday's lecture. Kindly grant leave."),
        (faculty_ids[0], student_ids[2], "Re: Leave application",
         "Leave noted. Please collect the notes from a classmate."),
        (student_ids[0], faculty_ids[1], "Doubt in tutorial 3", "Sir, can we discuss question 4 after the lecture?"),
    ]
    for i, (s, r, title, body) in enumerate(msgs):
        when = datetime(2026, 11, 12, 18, 0) + timedelta(minutes=17 * i)
        lines.append(
            "INSERT INTO messages (sender_id, receiver_id, title, body, created_at) VALUES "
            f"({s}, {r}, {q(title)}, {q(body)}, '{when:%Y-%m-%d %H:%M:%S}');"
        )
    notes = [
        (faculty_ids[0], "Unit test 2 for Engineering Mathematics is on Monday, 10 a.m., Room 304."),
        (faculty_ids[1], "Physics practical submissions are due this Friday."),
    ]
    for i, (f, body) in enumerate(notes):
        when = datetime(2026, 11, 13, 9, 30) + timedelta(hours=i)
        lines.append(
            "INSERT INTO announcements (faculty_id, body, created_at) VALUES "
            f"({f}, {q(body)}, '{when:%Y-%m-%d %H:%M:%S}');"
        )
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({lecture_id} lectures, {len(student_ids)} students)")


if __name__ == "__main__":
    main()
