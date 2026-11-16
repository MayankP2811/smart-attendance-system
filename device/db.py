"""Database access for the attendance station (MySQL / MariaDB).

Every write is committed straight away, so a power cut or a crash never
loses a lecture that has already started.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable

import mysql.connector

from .config import Settings


@dataclass(frozen=True)
class Subject:
    id: int
    code: str
    name: str
    faculty_name: str


def required_sightings(photos: int, min_presence: float) -> int:
    """How many photos a student must appear in, e.g. 4 of 6 photos at 0.6."""
    if photos <= 0:
        return 1
    return max(1, math.ceil(round(photos * min_presence, 6)))


def utc_offset(tz_name: str, when: datetime | None = None) -> str:
    """'+05:30' style offset for MySQL's session time_zone."""
    from zoneinfo import ZoneInfo

    off = (when or datetime.now(ZoneInfo(tz_name))).astimezone(ZoneInfo(tz_name)).utcoffset() or timedelta(0)
    minutes = int(off.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"{sign}{minutes // 60:02d}:{minutes % 60:02d}"


class AttendanceDB:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.conn = mysql.connector.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name,
            charset="utf8mb4",
            autocommit=False,
        )
        self._set_timezone()

    def _set_timezone(self) -> None:
        cur = self.conn.cursor()
        cur.execute("SET time_zone = %s", (utc_offset(self.settings.timezone),))
        cur.close()

    def _cursor(self):
        # A lecture lasts an hour; reconnect if MySQL closed an idle connection.
        if not self.conn.is_connected():
            self.conn.reconnect(attempts=3, delay=2)
            self._set_timezone()
        return self.conn.cursor()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:  # pragma: no cover - closing is best effort
            pass

    # ---- reads -----------------------------------------------------------
    def subject_for_finger(self, finger_id: int) -> Subject | None:
        cur = self._cursor()
        cur.execute(
            "SELECT s.id, s.code, s.name, COALESCE(CONCAT(u.first_name, ' ', u.last_name), '') "
            "FROM subjects s LEFT JOIN users u ON u.id = s.faculty_id WHERE s.finger_id = %s",
            (finger_id,),
        )
        row = cur.fetchone()
        cur.close()
        self.conn.commit()  # end the read transaction so later reads see fresh data
        return Subject(*row) if row else None

    def student_roll_numbers(self) -> list[str]:
        cur = self._cursor()
        cur.execute("SELECT roll_no FROM users WHERE role = 'student' AND roll_no IS NOT NULL ORDER BY roll_no")
        rolls = [r[0] for r in cur.fetchall()]
        cur.close()
        self.conn.commit()
        return rolls

    # ---- writes ----------------------------------------------------------
    def start_lecture(self, subject_id: int, started_at: datetime) -> int:
        """Create the lecture and mark every student absent until they are seen."""
        cur = self._cursor()
        try:
            cur.execute(
                "INSERT INTO lectures (subject_id, started_at) VALUES (%s, %s)",
                (subject_id, started_at.replace(tzinfo=None, microsecond=0)),
            )
            lecture_id = cur.lastrowid
            cur.execute(
                "INSERT INTO attendance (lecture_id, student_id, status, source) "
                "SELECT %s, id, 'absent', 'face' FROM users WHERE role = 'student'",
                (lecture_id,),
            )
            self.conn.commit()
            return int(lecture_id)
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def record_photo(self, lecture_id: int, matches: dict[str, float], min_presence: float) -> int:
        """Save one classroom photo's result and update everyone's status.

        `matches` maps the roll numbers recognised in this photo to their face distance.
        After the photo, a student is 'present' if recognised in at least `min_presence`
        of the photos taken so far, otherwise 'absent'. A status set by the teacher
        (leave, or a correction) is never changed. Returns how many are present now.
        """
        cur = self._cursor()
        try:
            for roll_no, distance in matches.items():
                cur.execute(
                    "UPDATE attendance a JOIN users u ON u.id = a.student_id "
                    "SET a.seen = a.seen + 1, a.distance = LEAST(COALESCE(a.distance, 9.999), %s) "
                    "WHERE a.lecture_id = %s AND u.roll_no = %s",
                    (round(float(distance), 3), lecture_id, roll_no),
                )
            cur.execute("UPDATE lectures SET photos = photos + 1 WHERE id = %s", (lecture_id,))
            cur.execute("SELECT photos FROM lectures WHERE id = %s", (lecture_id,))
            photos = int(cur.fetchone()[0])
            needed = required_sightings(photos, min_presence)
            cur.execute(
                "UPDATE attendance SET status = IF(seen >= %s, 'present', 'absent') "
                "WHERE lecture_id = %s AND status <> 'leave' AND source = 'face'",
                (needed, lecture_id),
            )
            cur.execute("SELECT COUNT(*) FROM attendance WHERE lecture_id = %s AND status = 'present'", (lecture_id,))
            present = int(cur.fetchone()[0])
            self.conn.commit()
            return present
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def end_lecture(self, lecture_id: int, ended_at: datetime) -> None:
        cur = self._cursor()
        cur.execute(
            "UPDATE lectures SET ended_at = %s WHERE id = %s",
            (ended_at.replace(tzinfo=None, microsecond=0), lecture_id),
        )
        self.conn.commit()
        cur.close()

    def set_finger_for_subject(self, finger_id: int, subject_code: str) -> bool:
        cur = self._cursor()
        cur.execute("UPDATE subjects SET finger_id = NULL WHERE finger_id = %s", (finger_id,))
        cur.execute("UPDATE subjects SET finger_id = %s WHERE code = %s", (finger_id, subject_code))
        ok = cur.rowcount == 1
        self.conn.commit()
        cur.close()
        return ok

    def attendance_for_day(self, day: datetime) -> Iterable[tuple]:
        """Rows for the Excel export: subject, start time, roll no, name, photos seen in, photos, status."""
        cur = self._cursor()
        cur.execute(
            "SELECT s.code, s.name, l.started_at, u.roll_no, CONCAT(u.first_name, ' ', u.last_name), a.seen, l.photos, a.status "
            "FROM attendance a JOIN lectures l ON l.id = a.lecture_id "
            "JOIN subjects s ON s.id = l.subject_id JOIN users u ON u.id = a.student_id "
            "WHERE l.started_at >= %s AND l.started_at < %s "
            "ORDER BY s.id, l.started_at, u.roll_no",
            (day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None),
             day.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None) + timedelta(days=1)),
        )
        rows = cur.fetchall()
        cur.close()
        self.conn.commit()
        return rows
