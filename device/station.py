"""The attendance station.

The fingerprint sensor and LCD are at the classroom door; the camera is inside
the classroom, facing the students.

1. The teacher scans a finger at the door. The finger's slot tells us the subject.
2. The LCD greets the teacher and a lecture is created (everyone 'absent').
3. During the whole lecture the camera takes photos at random moments, so
   students can't know when the next one comes.
4. Faces in each photo are matched against the known students.
5. A student is 'present' only if recognised in enough of the photos
   (MIN_PRESENCE), so marking attendance and leaving early shows as absent.
6. The LCD counts down the lecture, then waits for the next finger.
"""
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from .config import Settings
from .db import required_sightings

log = logging.getLogger("station")


@dataclass
class LectureResult:
    lecture_id: int
    subject_code: str
    photos: int = 0
    seen: dict[str, int] = field(default_factory=dict)       # roll no -> photos the student was in
    best: dict[str, float] = field(default_factory=dict)     # roll no -> smallest face distance
    unknown_faces: int = 0
    present: list[str] = field(default_factory=list)         # final result


def capture_times(lecture_seconds: float, count: int, rng: random.Random) -> list[float]:
    """Random photo moments spread over the lecture.

    The lecture is cut into `count` equal parts and one moment is picked at random
    inside each part. Every part of the lecture is covered, but nobody can predict
    the exact time of the next photo.
    """
    part = lecture_seconds / count
    return [part * i + part * rng.uniform(0.1, 0.9) for i in range(count)]


class Station:
    def __init__(self, settings: Settings, db, fingerprint, camera, recognizer, display,
                 sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], datetime] | None = None,
                 rng: random.Random | None = None):
        self.s = settings
        self.db = db
        self.fingerprint = fingerprint
        self.camera = camera
        self.recognizer = recognizer
        self.display = display
        self.sleep = sleep
        self.rng = rng or random.Random()
        tz = ZoneInfo(settings.timezone)
        self.now = clock or (lambda: datetime.now(tz))  # the clock is read for every lecture

    # ------------------------------------------------------------------
    def run_forever(self) -> None:
        try:
            while True:
                self.run_once()
        except KeyboardInterrupt:
            log.info("Stopping")
        finally:
            self.display.show("Station stopped", "")
            self.camera.close()

    def run_once(self) -> LectureResult | None:
        self.display.show("Smart Attendance", "Place finger")
        finger_id = self.fingerprint.wait_for_finger()
        if finger_id is None:
            self.display.show("Not recognised", "Please try again")
            self.sleep(3)
            return None
        subject = self.db.subject_for_finger(finger_id)
        if subject is None:
            log.warning("Finger %s is not linked to a subject", finger_id)
            self.display.show("No subject for", f"finger {finger_id}")
            self.sleep(3)
            return None

        started = self.now()
        self.display.show(f"Welcome {subject.code}", "Lecture started")
        lecture_id = self.db.start_lecture(subject.id, started)
        log.info("Lecture %s started: %s (%s)", lecture_id, subject.name, subject.faculty_name)
        result = LectureResult(lecture_id, subject.code)
        self.sleep(2)

        self.run_lecture(result, started)
        self.display.show(f"Lec: {subject.code}", f"Present: {len(result.present)}")
        self.db.end_lecture(lecture_id, self.now())
        log.info("Lecture %s ended: %s photos, present: %s", lecture_id, result.photos,
                 ", ".join(result.present) or "nobody")
        self.sleep(3)
        self.display.clear()
        return result

    # ------------------------------------------------------------------
    def run_lecture(self, result: LectureResult, started: datetime) -> None:
        """Count down the lecture on the LCD and take each photo when its moment comes."""
        total = self.s.lecture_minutes * 60
        moments = capture_times(total, self.s.capture_count, self.rng)
        log.debug("Photo moments (s): %s", [round(m) for m in moments])
        while True:
            elapsed = (self.now() - started).total_seconds()
            while moments and elapsed >= moments[0]:
                moments.pop(0)
                self.take_photo(result)
            left = int(total - elapsed)
            if left <= 0:
                break
            h, rem = divmod(left, 3600)
            m, s = divmod(rem, 60)
            self.display.show(f"Lec: {result.subject_code}", f"Ends in {h:02d}:{m:02d}:{s:02d}")
            self.sleep(1)
        for _ in moments:          # e.g. the clock jumped: still take the remaining photos
            self.take_photo(result)
        needed = required_sightings(result.photos, self.s.min_presence)
        result.present = sorted(r for r, n in result.seen.items() if result.photos and n >= needed)

    def take_photo(self, result: LectureResult) -> None:
        shot = result.photos + 1
        frame = self.camera.capture()
        if frame is None:
            log.warning("Photo %s: the camera returned nothing; skipped", shot)
            return
        matches = self.recognizer.identify(frame)
        found: dict[str, float] = {}
        for m in matches:
            if m.label == "Unknown":
                result.unknown_faces += 1
            elif m.label not in found or m.distance < found[m.label]:
                found[m.label] = m.distance
        result.photos = shot
        for roll, dist in found.items():
            result.seen[roll] = result.seen.get(roll, 0) + 1
            result.best[roll] = min(dist, result.best.get(roll, dist))
        present_now = self.db.record_photo(result.lecture_id, found, self.s.min_presence)
        log.info("Photo %s: %s faces, %s known; %s present so far", shot, len(matches), len(found), present_now)
        self._save_photo(frame, matches, result.lecture_id, shot)

    def _save_photo(self, frame, matches, lecture_id: int, shot: int) -> None:
        if not self.s.save_captures:
            return
        try:
            import cv2

            from .face import draw_matches

            folder = Path(self.s.captures_dir)
            folder.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(folder / f"lecture{lecture_id}_photo{shot}.jpg"), draw_matches(frame, matches))
        except Exception as exc:  # a full SD card must not stop attendance
            log.warning("Could not save photo: %s", exc)
