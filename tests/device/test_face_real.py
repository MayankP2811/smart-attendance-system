"""Real face recognition (dlib), on your own photos. Skipped unless you set FACE_TEST_DIR.

No face photos are stored in this repository. To run this test, make a folder:

    my_faces/
      known/TE01/photo1.jpg       enrollment photos, one folder per roll number
      probes.json                 {"other_photo_of_te01.jpg": ["TE01"], "stranger.jpg": []}
      other_photo_of_te01.jpg
      stranger.jpg

    FACE_TEST_DIR=my_faces python -m pytest tests/device/test_face_real.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

FACE_DIR = os.environ.get("FACE_TEST_DIR")
pytestmark = [pytest.mark.face, pytest.mark.skipif(not FACE_DIR, reason="set FACE_TEST_DIR to run")]


def test_real_photos_are_recognised(tmp_path):
    pytest.importorskip("face_recognition")
    import cv2

    from device.face import FaceRecognizer
    from device.tools.build_encodings import build

    root = Path(FACE_DIR)
    enc = tmp_path / "enc.npz"
    count, _ = build(root / "known", enc)
    assert count >= 1
    rec = FaceRecognizer(enc, tolerance=float(os.environ.get("FACE_TOLERANCE", "0.5")))
    probes = json.loads((root / "probes.json").read_text())
    for name, expected in probes.items():
        frame = cv2.imread(str(root / name))
        assert frame is not None, name
        found = sorted({m.label for m in rec.identify(frame) if m.label != "Unknown"})
        assert found == sorted(expected), f"{name}: expected {expected}, got {found}"
