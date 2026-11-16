"""Face recognition: HOG face detection + 128-number face embeddings (dlib, via face_recognition).

Known faces live in an .npz file made by `python -m device.tools.build_encodings`:
  labels     - one roll number per encoding (a student may have several photos)
  encodings  - array of shape (n, 128)
Using .npz instead of pickle means the file can't run code when it is loaded.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class Match:
    label: str          # roll number, or "Unknown"
    distance: float     # distance to the closest known face (lower = more alike)
    box: tuple[int, int, int, int]  # top, right, bottom, left


def load_encodings(path: Path) -> tuple[list[str], np.ndarray]:
    data = np.load(path, allow_pickle=False)
    labels = [str(x) for x in data["labels"]]
    encodings = np.asarray(data["encodings"], dtype=np.float64)
    if encodings.ndim != 2 or encodings.shape[0] != len(labels):
        raise ValueError(f"{path}: labels and encodings don't line up")
    return labels, encodings


def save_encodings(path: Path, labels: list[str], encodings: list[np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, labels=np.array(labels, dtype=str), encodings=np.array(encodings, dtype=np.float64))


def best_matches(known_labels: list[str], known: np.ndarray, faces: list[np.ndarray],
                 tolerance: float) -> list[tuple[str, float]]:
    """For each face, the closest known label within tolerance (else 'Unknown').

    Each student is given to at most one face per photo: if two faces look
    like the same student, the closer one wins and the other is 'Unknown'.
    """
    if len(known) == 0:
        return [("Unknown", 1.0) for _ in faces]
    best: list[tuple[str, float]] = []
    for face in faces:
        dists = np.linalg.norm(known - np.asarray(face), axis=1)
        i = int(np.argmin(dists))
        best.append((known_labels[i], float(dists[i])))
    results = [("Unknown", d) for _, d in best]
    taken: set[str] = set()
    for idx in sorted(range(len(best)), key=lambda k: best[k][1]):  # closest faces first
        label, d = best[idx]
        if d <= tolerance and label not in taken:
            results[idx] = (label, d)
            taken.add(label)
    return results


class FaceRecognizer:
    def __init__(self, encodings_file: Path, tolerance: float = 0.5, model: str = "hog", upsample: int = 1):
        import face_recognition  # type: ignore  (needs dlib)

        self._fr = face_recognition
        self.labels, self.known = load_encodings(encodings_file)
        self.tolerance = tolerance
        self.model = model
        self.upsample = upsample

    def identify(self, frame_bgr: np.ndarray) -> list[Match]:
        rgb = np.ascontiguousarray(frame_bgr[:, :, ::-1])  # OpenCV gives BGR; dlib wants RGB
        boxes = self._fr.face_locations(rgb, number_of_times_to_upsample=self.upsample, model=self.model)
        encs = self._fr.face_encodings(rgb, boxes)
        pairs = best_matches(self.labels, self.known, encs, self.tolerance)
        return [Match(label, dist, tuple(box)) for (label, dist), box in zip(pairs, boxes)]


class SimulatedRecognizer:
    """For demos without a camera: 'sees' a chosen or random set of students in each photo.

    present      - roll numbers seen in every photo (default: each student is seen
                   in a photo with probability `rate`)
    leave_early  - roll numbers seen only in the first third of the photos, like a
                   student who is marked at the start and then leaves
    """

    def __init__(self, roll_numbers: list[str], present: list[str] | None = None,
                 leave_early: list[str] | None = None, photos: int = 6,
                 rate: float = 0.85, seed: int | None = None):
        self.rolls = roll_numbers
        self.present = present
        self.leave_early = set(leave_early or [])
        self.photos = max(1, photos)
        self.rate = rate
        self.rnd = random.Random(seed)
        self.calls = 0

    def identify(self, frame_bgr: np.ndarray) -> list[Match]:
        self.calls += 1
        if self.present is not None:
            chosen = [r for r in self.present if r not in self.leave_early]
        else:
            chosen = [r for r in self.rolls if r not in self.leave_early and self.rnd.random() < self.rate]
        if self.calls <= max(1, self.photos // 3):
            chosen += sorted(self.leave_early)
        return [Match(r, round(self.rnd.uniform(0.30, 0.45), 3), (0, 0, 0, 0)) for r in chosen]


def draw_matches(frame_bgr: np.ndarray, matches: list[Match], names: dict[str, str] | None = None) -> np.ndarray:
    """Copy of the frame with a box and name on every face (green = known, red = unknown)."""
    import cv2

    out = frame_bgr.copy()
    for m in matches:
        top, right, bottom, left = m.box
        if right <= left:
            continue
        known = m.label != "Unknown"
        color = (60, 180, 75) if known else (60, 60, 220)
        text = (names or {}).get(m.label, m.label)
        cv2.rectangle(out, (left, top), (right, bottom), color, 2)
        cv2.putText(out, text, (left, max(15, top - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return out
