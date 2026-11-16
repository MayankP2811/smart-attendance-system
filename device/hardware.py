"""Fingerprint sensor, LCD and camera - the real parts and stand-ins for testing.

The real classes import their hardware libraries only when created, so the
rest of the code (and the tests) run on any computer.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Iterable, Iterator

import numpy as np

LCD_WIDTH = 16


def fit_line(text: str, width: int = LCD_WIDTH) -> str:
    """Cut or pad text to exactly one LCD line."""
    return str(text)[:width].ljust(width)


# --------------------------------------------------------------------------
# Fingerprint sensor (faculty authentication)
# --------------------------------------------------------------------------
class FingerprintSensor:
    """R30x-family optical sensor through Adafruit's driver, on a USB-serial adapter."""

    def __init__(self, port: str, baudrate: int = 57600):
        import adafruit_fingerprint  # type: ignore
        import serial  # type: ignore

        self._af = adafruit_fingerprint
        self._uart = serial.Serial(port, baudrate=baudrate, timeout=1)
        self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self._uart)

    def wait_for_finger(self, timeout: float | None = None, poll: float = 0.1) -> int | None:
        """Wait for a finger and return its stored slot number, or None if not recognised."""
        af = self._af
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.finger.get_image() != af.OK:
            if deadline is not None and time.monotonic() > deadline:
                return None
            time.sleep(poll)  # short pause so the loop does not use a whole CPU core
        if self.finger.image_2_tz(1) != af.OK:
            return None
        if self.finger.finger_search() != af.OK:
            return None
        return int(self.finger.finger_id)


class MockFingerprint:
    """Stands in for the sensor: a fixed list of finger IDs, or typed at the keyboard."""

    def __init__(self, script: Iterable[int] | None = None, ask: Callable[[str], str] = input):
        self._script: Iterator[int] | None = iter(script) if script is not None else None
        self._ask = ask

    def wait_for_finger(self, timeout: float | None = None, poll: float = 0.1) -> int | None:
        if self._script is not None:
            try:
                return next(self._script)
            except StopIteration:
                raise KeyboardInterrupt  # script finished: stop the station
        answer = self._ask("[mock fingerprint] finger ID to scan (q = quit): ").strip()
        if answer.lower() in ("q", "quit", "exit"):
            raise KeyboardInterrupt
        return int(answer) if answer.isdigit() else None


# --------------------------------------------------------------------------
# 16x2 LCD
# --------------------------------------------------------------------------
class LcdDisplay:
    """16x2 character LCD with a PCF8574 I2C backpack.

    Uses RPLCD if installed, otherwise the raspberry-pi-guy 'drivers' module.
    """

    def __init__(self, address: int = 0x27):
        try:
            from RPLCD.i2c import CharLCD  # type: ignore

            self._lcd = CharLCD("PCF8574", address, cols=16, rows=2)
            self._mode = "rplcd"
        except ImportError:
            import drivers  # type: ignore

            self._lcd = drivers.Lcd()
            self._mode = "drivers"

    def show(self, line1: str, line2: str = "") -> None:
        if self._mode == "rplcd":
            self._lcd.cursor_pos = (0, 0)
            self._lcd.write_string(fit_line(line1))
            self._lcd.cursor_pos = (1, 0)
            self._lcd.write_string(fit_line(line2))
        else:
            self._lcd.lcd_display_string(fit_line(line1), 1)
            self._lcd.lcd_display_string(fit_line(line2), 2)

    def clear(self) -> None:
        if self._mode == "rplcd":
            self._lcd.clear()
        else:
            self._lcd.lcd_clear()


class ConsoleDisplay:
    """Prints what the LCD would show. Keeps a history for tests."""

    def __init__(self, echo: bool = True):
        self.echo = echo
        self.history: list[tuple[str, str]] = []
        self._last: tuple[str, str] | None = None

    def show(self, line1: str, line2: str = "") -> None:
        screen = (fit_line(line1), fit_line(line2))
        self.history.append(screen)
        if self.echo and screen != self._last:
            print(f"[LCD] |{screen[0]}|  |{screen[1]}|", flush=True)
        self._last = screen

    def clear(self) -> None:
        self.show("", "")


# --------------------------------------------------------------------------
# Camera
# --------------------------------------------------------------------------
class Camera:
    """USB camera or Pi camera seen by OpenCV (V4L2)."""

    def __init__(self, index: int = 0, width: int = 1920, height: int = 1080):
        import cv2

        self._cv2 = cv2
        self.index, self.width, self.height = index, width, height
        self.cap = None

    def open(self) -> None:
        cv2 = self._cv2
        self.cap = cv2.VideoCapture(self.index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        for _ in range(5):  # let auto-exposure settle
            self.cap.read()

    def capture(self) -> np.ndarray | None:
        """One BGR frame, or None if the camera gave nothing."""
        if self.cap is None:
            self.open()
        ok, frame = self.cap.read()
        return frame if ok and frame is not None else None

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class MockCamera:
    """Returns pictures from a folder in turn, or a plain grey frame."""

    def __init__(self, images_dir: Path | None = None):
        self.files: list[Path] = []
        if images_dir:
            self.files = sorted(p for p in Path(images_dir).iterdir()
                                if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        self._i = 0

    def open(self) -> None:
        pass

    def capture(self) -> np.ndarray | None:
        if not self.files:
            return np.full((480, 640, 3), 200, dtype=np.uint8)
        import cv2

        path = self.files[self._i % len(self.files)]
        self._i += 1
        return cv2.imread(str(path))

    def close(self) -> None:
        pass
