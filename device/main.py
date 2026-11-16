"""Start the attendance station.

On the Raspberry Pi:
    python -m device.main

On any computer, without the sensor, LCD or camera:
    python -m device.main --mock                       # type a finger ID (1-5)
    python -m device.main --mock --finger 4 --lecture-seconds 30
    python -m device.main --mock --finger 4 --lecture-seconds 30 --leave-early TE03
    python -m device.main --mock --images path/to/classroom/photos   # real face matching
"""
from __future__ import annotations

import argparse
import logging
import random
import sys

from .config import load_settings


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Smart Attendance station (fingerprint at the door, camera in the classroom)")
    p.add_argument("--mock", action="store_true", help="no hardware: keyboard fingerprint, console LCD")
    p.add_argument("--finger", type=int, action="append",
                   help="mock: finger ID(s) to scan, then stop (repeat the option for more)")
    p.add_argument("--images", help="mock: folder of classroom photos to run real face matching on")
    p.add_argument("--present", help="mock without --images: roll numbers seen in every photo (comma-separated)")
    p.add_argument("--leave-early", help="mock without --images: roll numbers seen only at the start of the lecture")
    p.add_argument("--lecture-seconds", type=float, help="override the lecture length (for demos)")
    p.add_argument("--photos", type=int, help="override CAPTURE_COUNT")
    p.add_argument("--seed", type=int, help="fix the random photo moments (for repeatable demos)")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def split(value: str | None) -> list[str] | None:
    return [x.strip().upper() for x in value.split(",") if x.strip()] if value else None


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    s = load_settings()
    if args.lecture_seconds is not None:
        s.lecture_minutes = args.lecture_seconds / 60
    if args.photos:
        s.capture_count = args.photos

    from .db import AttendanceDB
    from .station import Station

    db = AttendanceDB(s)

    if args.mock:
        from .face import SimulatedRecognizer
        from .hardware import ConsoleDisplay, MockCamera, MockFingerprint

        fingerprint = MockFingerprint(args.finger)
        display = ConsoleDisplay()
        camera = MockCamera(args.images)
        if args.images:
            from .face import FaceRecognizer
            recognizer = FaceRecognizer(s.encodings_file, s.face_tolerance, s.face_model, s.face_upsample)
        else:
            recognizer = SimulatedRecognizer(db.student_roll_numbers(), split(args.present), split(args.leave_early),
                                             photos=s.capture_count, seed=args.seed)
    else:
        from .face import FaceRecognizer
        from .hardware import Camera, FingerprintSensor, LcdDisplay

        display = LcdDisplay(s.lcd_address)
        display.show("Smart Attendance", "Starting...")
        fingerprint = FingerprintSensor(s.fingerprint_port, s.fingerprint_baud)
        camera = Camera(s.camera_index, s.camera_width, s.camera_height)
        recognizer = FaceRecognizer(s.encodings_file, s.face_tolerance, s.face_model, s.face_upsample)

    rng = random.Random(args.seed) if args.seed is not None else None
    try:
        Station(s, db, fingerprint, camera, recognizer, display, rng=rng).run_forever()
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
