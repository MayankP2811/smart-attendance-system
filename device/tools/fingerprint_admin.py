"""Enroll, list, test and delete teacher fingerprints, and link a finger to a subject.

    python -m device.tools.fingerprint_admin list
    python -m device.tools.fingerprint_admin enroll 4 --subject maths
    python -m device.tools.fingerprint_admin test
    python -m device.tools.fingerprint_admin delete 4
    python -m device.tools.fingerprint_admin link 4 maths     # link only, no scanning

Each sensor slot (1-127) belongs to one subject.
A teacher with two subjects enrolls one finger for each.
"""
from __future__ import annotations

import argparse
import sys
import time


def enroll(finger, af, slot: int) -> bool:
    """Two scans of the same finger -> one template in `slot`."""
    for attempt in (1, 2):
        print("Place finger on the sensor..." if attempt == 1 else "Place the same finger again...")
        while (r := finger.get_image()) != af.OK:
            if r not in (af.NOFINGER,):
                print("Imaging error, try again")
                return False
            time.sleep(0.1)
        if finger.image_2_tz(attempt) != af.OK:
            print("Could not read the finger clearly")
            return False
        if attempt == 1:
            print("Remove finger")
            time.sleep(1)
            while finger.get_image() != af.NOFINGER:
                time.sleep(0.1)
    if finger.create_model() != af.OK:
        print("The two scans did not match")
        return False
    if finger.store_model(slot) != af.OK:
        print("Could not store the template")
        return False
    print(f"Stored in slot {slot}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("test")
    e = sub.add_parser("enroll")
    e.add_argument("slot", type=int)
    e.add_argument("--subject", help="subject code to link, e.g. maths")
    d = sub.add_parser("delete")
    d.add_argument("slot", type=int)
    link = sub.add_parser("link")
    link.add_argument("slot", type=int)
    link.add_argument("subject")
    args = ap.parse_args(argv)

    if getattr(args, "slot", 1) not in range(1, 128):
        ap.error("slot must be 1-127")

    from ..config import load_settings

    s = load_settings()

    if args.cmd == "link":
        from ..db import AttendanceDB
        ok = AttendanceDB(s).set_finger_for_subject(args.slot, args.subject)
        print("Linked." if ok else f"No subject with code '{args.subject}'.")
        return 0 if ok else 1

    import adafruit_fingerprint as af  # type: ignore

    from ..hardware import FingerprintSensor

    sensor = FingerprintSensor(s.fingerprint_port, s.fingerprint_baud)
    finger = sensor.finger
    if finger.read_templates() != af.OK:
        print("Could not talk to the fingerprint sensor")
        return 1

    if args.cmd == "list":
        print("Stored slots:", sorted(finger.templates))
    elif args.cmd == "test":
        print("Scan a finger...")
        slot = sensor.wait_for_finger(timeout=15)
        print(f"Matched slot {slot} (confidence {finger.confidence})" if slot else "No match")
    elif args.cmd == "delete":
        print("Deleted" if finger.delete_model(args.slot) == af.OK else "Delete failed")
    elif args.cmd == "enroll":
        if not enroll(finger, af, args.slot):
            return 1
        if args.subject:
            from ..db import AttendanceDB
            ok = AttendanceDB(s).set_finger_for_subject(args.slot, args.subject)
            print("Linked to", args.subject if ok else f"(no subject '{args.subject}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
