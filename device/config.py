"""Settings for the attendance station, read from the repository's .env file.

Values already set in the environment win over the file, so tests and
one-off runs can override anything (e.g. DB_NAME=... python -m device.main).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_env_file(path: Path) -> dict[str, str]:
    """Parse simple KEY=VALUE lines. Blank lines and # comments are ignored."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def _get(env: dict[str, str], key: str, default: str) -> str:
    return os.environ.get(key, env.get(key, default))


@dataclass
class Settings:
    db_host: str = "127.0.0.1"
    db_port: int = 3306
    db_name: str = "smart_attendance"
    db_user: str = "attendance_app"
    db_password: str = ""
    timezone: str = "Asia/Kolkata"

    fingerprint_port: str = "/dev/ttyUSB0"
    fingerprint_baud: int = 57600
    lcd_address: int = 0x27
    camera_index: int = 0
    camera_width: int = 1920
    camera_height: int = 1080
    capture_count: int = 6
    min_presence: float = 0.6
    face_tolerance: float = 0.5
    face_model: str = "hog"
    face_upsample: int = 1
    encodings_file: Path = field(default_factory=lambda: REPO_ROOT / "device" / "data" / "encodings.npz")
    lecture_minutes: float = 60.0
    save_captures: bool = True
    captures_dir: Path = field(default_factory=lambda: REPO_ROOT / "device" / "captures")


def load_settings(env_path: Path | None = None) -> Settings:
    env = load_env_file(env_path or REPO_ROOT / ".env")
    enc = Path(_get(env, "ENCODINGS_FILE", "device/data/encodings.npz"))
    return Settings(
        db_host=_get(env, "DB_HOST", "127.0.0.1"),
        db_port=int(_get(env, "DB_PORT", "3306")),
        db_name=_get(env, "DB_NAME", "smart_attendance"),
        db_user=_get(env, "DB_USER", "attendance_app"),
        db_password=_get(env, "DB_PASSWORD", ""),
        timezone=_get(env, "APP_TIMEZONE", "Asia/Kolkata"),
        fingerprint_port=_get(env, "FINGERPRINT_PORT", "/dev/ttyUSB0"),
        fingerprint_baud=int(_get(env, "FINGERPRINT_BAUD", "57600")),
        lcd_address=int(_get(env, "LCD_I2C_ADDRESS", "0x27"), 0),
        camera_index=int(_get(env, "CAMERA_INDEX", "0")),
        camera_width=int(_get(env, "CAMERA_WIDTH", "1920")),
        camera_height=int(_get(env, "CAMERA_HEIGHT", "1080")),
        capture_count=max(1, int(_get(env, "CAPTURE_COUNT", "6"))),
        min_presence=min(1.0, max(0.0, float(_get(env, "MIN_PRESENCE", "0.6")))),
        face_tolerance=float(_get(env, "FACE_TOLERANCE", "0.5")),
        face_model=_get(env, "FACE_MODEL", "hog"),
        face_upsample=int(_get(env, "FACE_UPSAMPLE", "1")),
        encodings_file=enc if enc.is_absolute() else REPO_ROOT / enc,
        lecture_minutes=float(_get(env, "LECTURE_MINUTES", "60")),
        save_captures=_get(env, "SAVE_CAPTURES", "1") not in ("0", "false", "no", ""),
    )
