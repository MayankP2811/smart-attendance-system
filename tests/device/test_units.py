"""Unit tests for the station code. No database, camera or sensor needed."""
from __future__ import annotations

import sys
import types
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from device.config import Settings, load_env_file, load_settings
from device.face import (FaceRecognizer, Match, SimulatedRecognizer, best_matches, load_encodings,
                         save_encodings)
from device.hardware import ConsoleDisplay, MockCamera, MockFingerprint, fit_line
from device.station import Station, capture_times
from device.db import Subject, required_sightings, utc_offset


# ---------------------------------------------------------------- config
def test_env_file_parsing(tmp_path):
    f = tmp_path / ".env"
    f.write_text("# comment\nDB_HOST=db.local\nDB_PASSWORD='p@ss=word'\n\nBROKEN LINE\nLCD_I2C_ADDRESS=0x3F\n")
    env = load_env_file(f)
    assert env == {"DB_HOST": "db.local", "DB_PASSWORD": "p@ss=word", "LCD_I2C_ADDRESS": "0x3F"}


def test_settings_environment_overrides_file(tmp_path, monkeypatch):
    f = tmp_path / ".env"
    f.write_text("DB_NAME=from_file\nCAPTURE_COUNT=4\nLCD_I2C_ADDRESS=0x3F\n")
    monkeypatch.setenv("DB_NAME", "from_env")
    s = load_settings(f)
    assert s.db_name == "from_env"
    assert s.capture_count == 4
    assert s.lcd_address == 0x3F


def test_no_password_in_default_settings():
    assert Settings().db_password == ""


def test_utc_offset_india():
    assert utc_offset("Asia/Kolkata") == "+05:30"


# ---------------------------------------------------------------- LCD
def test_station_messages_fit_the_lcd():
    import re
    src = (Path(__file__).resolve().parents[2] / "device" / "station.py").read_text()
    for text in re.findall(r'display\.show\("([^"{]*)"', src):
        assert len(text) <= 16, text


def test_lcd_lines_are_exactly_16_characters():
    assert fit_line("Welcome chemistry lecture") == "Welcome chemistr"
    assert len(fit_line("Hi")) == 16


def test_console_display_keeps_history():
    d = ConsoleDisplay(echo=False)
    d.show("Smart Attendance", "Place finger")
    assert d.history[-1] == ("Smart Attendance", "Place finger    ")


# ---------------------------------------------------------------- fingerprint
def test_mock_fingerprint_script_then_stops():
    fp = MockFingerprint([4, 2])
    assert fp.wait_for_finger() == 4
    assert fp.wait_for_finger() == 2
    with pytest.raises(KeyboardInterrupt):
        fp.wait_for_finger()


def test_mock_fingerprint_keyboard():
    answers = iter(["5", "x", "q"])
    fp = MockFingerprint(ask=lambda _: next(answers))
    assert fp.wait_for_finger() == 5
    assert fp.wait_for_finger() is None
    with pytest.raises(KeyboardInterrupt):
        fp.wait_for_finger()


def _fake_adafruit(monkeypatch, images_before_finger: int, found: bool = True):
    af = types.SimpleNamespace(OK=0, NOFINGER=2)

    class Finger:
        def __init__(self, uart):
            self.calls = 0
            self.finger_id = 4
            self.confidence = 90

        def get_image(self):
            self.calls += 1
            return af.OK if self.calls > images_before_finger else af.NOFINGER

        def image_2_tz(self, slot):
            return af.OK

        def finger_search(self):
            return af.OK if found else 9

    af.Adafruit_Fingerprint = Finger
    monkeypatch.setitem(sys.modules, "adafruit_fingerprint", af)
    monkeypatch.setitem(sys.modules, "serial", types.SimpleNamespace(Serial=lambda *a, **k: object()))


def test_fingerprint_sensor_waits_politely_and_returns_slot(monkeypatch):
    from device import hardware

    _fake_adafruit(monkeypatch, images_before_finger=3)
    sleeps = []
    monkeypatch.setattr(hardware.time, "sleep", lambda s: sleeps.append(s))
    sensor = hardware.FingerprintSensor("/dev/null")
    assert sensor.wait_for_finger() == 4
    assert len(sleeps) == 3 and all(s > 0 for s in sleeps)   # no busy loop


def test_fingerprint_sensor_unknown_finger(monkeypatch):
    from device import hardware

    _fake_adafruit(monkeypatch, images_before_finger=0, found=False)
    assert hardware.FingerprintSensor("/dev/null").wait_for_finger() is None


# ---------------------------------------------------------------- camera
def test_mock_camera_blank_and_folder(tmp_path):
    import cv2

    assert MockCamera().capture().shape == (480, 640, 3)
    cv2.imwrite(str(tmp_path / "b.png"), np.zeros((10, 20, 3), np.uint8))
    cv2.imwrite(str(tmp_path / "a.png"), np.ones((10, 30, 3), np.uint8))
    cam = MockCamera(tmp_path)
    assert cam.capture().shape[1] == 30   # sorted: a.png first
    assert cam.capture().shape[1] == 20
    assert cam.capture().shape[1] == 30   # then wraps around


# ---------------------------------------------------------------- face matching
def _vec(i, scale=1.0):
    v = np.zeros(128)
    v[i] = scale
    return v


def test_best_matches_tolerance_and_unknown():
    labels = ["TE01", "TE02"]
    known = np.array([_vec(0), _vec(1)])
    faces = [_vec(0) + 0.01, _vec(5)]            # close to TE01, far from everyone
    out = best_matches(labels, known, faces, tolerance=0.5)
    assert out[0][0] == "TE01" and out[0][1] < 0.2
    assert out[1][0] == "Unknown"


def test_one_student_is_given_to_only_one_face_per_photo():
    labels = ["TE01"]
    known = np.array([_vec(0)])
    faces = [_vec(0) + 0.2, _vec(0) + 0.01]       # two faces both look like TE01
    out = best_matches(labels, known, faces, tolerance=0.9)
    assert [l for l, _ in out] == ["Unknown", "TE01"]   # the closer face wins


def test_several_photos_per_student():
    labels = ["TE01", "TE01", "TE02"]
    known = np.array([_vec(0), _vec(2), _vec(1)])
    out = best_matches(labels, known, [_vec(2) + 0.02], tolerance=0.5)
    assert out[0][0] == "TE01"


def test_encodings_file_round_trip_without_pickle(tmp_path):
    path = tmp_path / "enc.npz"
    save_encodings(path, ["TE01", "TE02"], [_vec(0), _vec(1)])
    labels, enc = load_encodings(path)
    assert labels == ["TE01", "TE02"] and enc.shape == (2, 128)
    with np.load(path, allow_pickle=False) as data:     # loads with pickling switched off
        assert set(data.files) == {"labels", "encodings"}


def _fake_face_lib(monkeypatch, faces_per_image):
    """faces_per_image: list of lists of 128-d vectors, one entry per call."""
    calls = iter(faces_per_image)
    state = {}

    def face_locations(img, number_of_times_to_upsample=1, model="hog"):
        state["faces"] = next(calls)
        return [(10 * i, 50 + 10 * i, 50 + 10 * i, 10 * i) for i in range(len(state["faces"]))]

    def face_encodings(img, boxes=None):
        return list(state["faces"])

    lib = types.SimpleNamespace(face_locations=face_locations, face_encodings=face_encodings,
                                load_image_file=lambda p: np.zeros((60, 60, 3), np.uint8))
    monkeypatch.setitem(sys.modules, "face_recognition", lib)
    return lib


def test_face_recognizer_converts_bgr_and_labels_faces(tmp_path, monkeypatch):
    path = tmp_path / "enc.npz"
    save_encodings(path, ["TE01", "TE02"], [_vec(0), _vec(1)])
    _fake_face_lib(monkeypatch, [[_vec(1) + 0.01, _vec(7)]])
    rec = FaceRecognizer(path, tolerance=0.5)
    matches = rec.identify(np.zeros((60, 60, 3), np.uint8))
    assert [m.label for m in matches] == ["TE02", "Unknown"]
    assert matches[0].box == (0, 50, 50, 0)


def test_build_encodings_skips_bad_photos(tmp_path, monkeypatch):
    from device.tools import build_encodings

    ds = tmp_path / "dataset"
    (ds / "TE02").mkdir(parents=True)
    for p in (ds / "TE01.jpg", ds / "TE02" / "a.jpg", ds / "TE02" / "b.png", ds / "TE03.jpg", ds / "notes.txt"):
        p.write_bytes(b"x")
    # sorted order: TE01.jpg, TE02/a.jpg, TE02/b.png, TE03.jpg
    lib = _fake_face_lib(monkeypatch, [[_vec(0)], [_vec(1)], [], [_vec(2), _vec(3)]])
    out = tmp_path / "enc.npz"
    count, warnings = build_encodings.build(ds, out, fr=lib)
    assert count == 2
    assert len(warnings) == 2 and "0 faces" in warnings[0] and "2 faces" in warnings[1]
    assert load_encodings(out)[0] == ["TE01", "TE02"]


def test_simulated_recognizer_fixed_list_and_early_leaver():
    rec = SimulatedRecognizer(["TE01", "TE02", "TE03"], present=["TE02"], leave_early=["TE03"], photos=6, seed=1)
    seen = [sorted(m.label for m in rec.identify(None)) for _ in range(6)]
    assert seen[0] == ["TE02", "TE03"] and seen[1] == ["TE02", "TE03"]   # first third: both
    assert all(s == ["TE02"] for s in seen[2:])                            # then TE03 is gone


# ---------------------------------------------------------------- photo moments
def test_capture_times_cover_the_whole_lecture_at_random():
    import random

    times = capture_times(3600, 6, random.Random(7))
    assert len(times) == 6 and times == sorted(times)
    for i, t in enumerate(times):                      # one photo inside each 10-minute part
        assert 600 * i < t < 600 * (i + 1)
    other = capture_times(3600, 6, random.Random(8))
    assert times != other                              # not predictable from one lecture to the next


def test_required_sightings():
    assert required_sightings(6, 0.6) == 4
    assert required_sightings(5, 0.6) == 3
    assert required_sightings(1, 0.6) == 1
    assert required_sightings(10, 0.5) == 5


# ---------------------------------------------------------------- station flow
class FakeDB:
    """Keeps the same counts as the real database, in memory."""

    def __init__(self, min_presence=0.6):
        self.lectures = []
        self.seen = {}
        self.photos = {}
        self.ended = []

    def subject_for_finger(self, finger_id):
        return Subject(1, "maths", "Engineering Mathematics", "Priya Deshmukh") if finger_id == 4 else None

    def start_lecture(self, subject_id, started_at):
        self.lectures.append((subject_id, started_at))
        lid = len(self.lectures)
        self.seen[lid], self.photos[lid] = {}, 0
        return lid

    def record_photo(self, lecture_id, matches, min_presence):
        self.photos[lecture_id] += 1
        for roll in matches:
            self.seen[lecture_id][roll] = self.seen[lecture_id].get(roll, 0) + 1
        need = required_sightings(self.photos[lecture_id], min_presence)
        return sum(1 for n in self.seen[lecture_id].values() if n >= need)

    def end_lecture(self, lecture_id, ended_at):
        self.ended.append(lecture_id)


class ScriptedRecognizer:
    def __init__(self, per_photo):
        self.per_photo = iter(per_photo)

    def identify(self, frame):
        return [Match(label, dist, (0, 0, 0, 0)) for label, dist in next(self.per_photo, [])]


class FakeClock:
    def __init__(self):
        self.t = datetime(2024, 1, 15, 9, 0)

    def __call__(self):
        return self.t

    def sleep(self, seconds):
        self.t += timedelta(seconds=seconds)


def make_station(fingers, per_photo, camera=None, **overrides):
    import random

    s = Settings(capture_count=6, min_presence=0.6, lecture_minutes=60, save_captures=False)
    for k, v in overrides.items():
        setattr(s, k, v)
    clock = FakeClock()
    st = Station(s, FakeDB(), MockFingerprint(fingers), camera or MockCamera(), ScriptedRecognizer(per_photo),
                 ConsoleDisplay(echo=False), sleep=clock.sleep, clock=clock, rng=random.Random(3))
    return st, clock


STAYS = ("TE01", 0.35)
LEAVES = ("TE02", 0.33)
COMES_LATE = ("TE03", 0.40)
SIX_PHOTOS = [
    [STAYS, LEAVES], [STAYS, LEAVES], [STAYS],
    [STAYS, COMES_LATE], [STAYS, COMES_LATE, ("Unknown", 0.8)], [COMES_LATE],
]


def test_student_who_leaves_early_is_absent():
    st, _ = make_station([4], SIX_PHOTOS)
    result = st.run_once()
    assert result.photos == 6
    assert result.seen == {"TE01": 5, "TE02": 2, "TE03": 3}
    assert result.present == ["TE01"]           # needs 4 of 6: leaving early or coming late isn't enough
    assert result.unknown_faces == 1
    assert st.db.ended == [1]


def test_photos_are_spread_over_the_whole_lecture():
    st, clock = make_station([4], SIX_PHOTOS)
    taken = []
    original = st.take_photo
    st.take_photo = lambda r: (taken.append(clock.t), original(r))
    st.run_once()
    start = st.db.lectures[0][1]
    minutes = [(t - start).total_seconds() / 60 for t in taken]
    assert len(minutes) == 6 and minutes[-1] > 50 and minutes[0] < 10   # first early, last near the end
    assert all(b - a > 0 for a, b in zip(minutes, minutes[1:]))


def test_lower_threshold_counts_more_students():
    st, _ = make_station([4], SIX_PHOTOS, min_presence=0.5)
    assert st.run_once().present == ["TE01", "TE03"]


def test_lecture_time_is_read_for_each_lecture():
    st, clock = make_station([4, 4], [[]] * 12)
    st.run_once()
    st.run_once()
    (_, t1), (_, t2) = st.db.lectures
    assert (t2 - t1).total_seconds() >= 3600


def test_countdown_and_photo_progress_on_lcd():
    st, _ = make_station([4], SIX_PHOTOS)
    st.run_once()
    lines = [l2 for _, l2 in st.display.history]
    assert any(l.startswith("Ends in 00:5") for l in lines)
    assert ("Lec: maths      ", "Present: 1      ") in st.display.history
    assert st.display.history[-1] == ("                ", "                ")


def test_camera_failure_does_not_crash():
    class DeadCamera(MockCamera):
        def capture(self):
            return None

    st, _ = make_station([4], [], camera=DeadCamera())
    result = st.run_once()
    assert result.photos == 0 and result.present == []
    assert st.db.photos[1] == 0


def test_unknown_finger_and_unlinked_finger():
    st, _ = make_station([None, 9], [])
    assert st.run_once() is None
    assert st.display.history[-1][0].startswith("Not recognised")
    assert st.run_once() is None
    assert st.display.history[-1] == ("No subject for  ", "finger 9        ")
    assert st.db.lectures == []


def test_main_module_has_no_shadowed_time_module():
    import device.station as station_mod

    assert isinstance(station_mod.time, types.ModuleType)   # `time` must stay the module, never a string


def test_no_secrets_in_python_sources():
    root = Path(__file__).resolve().parents[2]
    for py in (root / "device").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        assert "db4free" not in text and "Mp@" not in text, py
