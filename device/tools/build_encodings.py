"""Build the known-faces file from a folder of student photos.

Name each photo (or a sub-folder of photos) after the student's roll number,
the same roll number the student uses on the website:

    dataset/
      TE01.jpg              one photo for TE01
      TE02/                 or several photos for TE02 (better accuracy)
        front.jpg
        left.jpg

    python -m device.tools.build_encodings dataset

Photos with no face, or with more than one face, are skipped with a warning.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def collect_photos(dataset: Path) -> list[tuple[str, Path]]:
    photos: list[tuple[str, Path]] = []
    for entry in sorted(dataset.iterdir()):
        if entry.is_dir():
            photos += [(entry.name, p) for p in sorted(entry.iterdir()) if p.suffix.lower() in IMAGE_TYPES]
        elif entry.suffix.lower() in IMAGE_TYPES:
            photos.append((entry.stem, entry))
    return photos


def build(dataset: Path, output: Path, upsample: int = 1, model: str = "hog", fr=None) -> tuple[int, list[str]]:
    """Returns (number of encodings saved, list of warnings)."""
    if fr is None:
        import face_recognition as fr  # type: ignore
    from ..face import save_encodings

    labels, encodings, warnings = [], [], []
    for label, path in collect_photos(dataset):
        image = fr.load_image_file(str(path))
        boxes = fr.face_locations(image, number_of_times_to_upsample=upsample, model=model)
        if len(boxes) != 1:
            warnings.append(f"skipped {path.name}: found {len(boxes)} faces (need exactly 1)")
            continue
        labels.append(label)
        encodings.append(fr.face_encodings(image, boxes)[0])
    if not encodings:
        raise SystemExit("No usable photos found - nothing saved.")
    save_encodings(output, labels, encodings)
    return len(encodings), warnings


def main(argv: list[str] | None = None) -> int:
    from ..config import load_settings

    s = load_settings()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dataset", type=Path, help="folder of student photos")
    ap.add_argument("-o", "--output", type=Path, default=s.encodings_file)
    ap.add_argument("--upsample", type=int, default=s.face_upsample)
    args = ap.parse_args(argv)
    count, warnings = build(args.dataset, args.output, args.upsample, s.face_model)
    for w in warnings:
        print("warning:", w, file=sys.stderr)
    students = len({label for label, _ in collect_photos(args.dataset)})
    print(f"Saved {count} face encodings for up to {students} students to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
