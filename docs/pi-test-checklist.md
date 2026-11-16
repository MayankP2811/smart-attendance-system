# Raspberry Pi test checklist

Use this the first time the station runs on real hardware. Tick each line.

## Before you start

- [ ] Raspberry Pi OS updated, I2C enabled (`sudo raspi-config` → Interface Options → I2C)
- [ ] `requirements-hardware.txt` installed in `.venv` (dlib compiled without errors)
- [ ] `.env` copied from `.env.example`, `DB_HOST` points to the MySQL server
- [ ] From the Pi: `mysql -h DB_HOST -u attendance_app -p smart_attendance -e "SELECT COUNT(*) FROM subjects"` works

## Each part on its own

- [ ] **LCD:** `i2cdetect -y 1` shows `27` (or `3f` → set `LCD_I2C_ADDRESS=0x3F`).
  `.venv/bin/python -c "from device.hardware import LcdDisplay; LcdDisplay().show('Hello', 'LCD works')"` shows both lines. If the text is invisible, turn the contrast screw on the backpack.
- [ ] **Fingerprint sensor:** `ls /dev/ttyUSB*` shows the adapter. `python -m device.tools.fingerprint_admin list` prints the stored slots (an empty list is fine).
- [ ] **Enroll:** `python -m device.tools.fingerprint_admin enroll 4 --subject maths` → "Stored in slot 4" and "Linked to maths".
- [ ] **Match:** `python -m device.tools.fingerprint_admin test` with the same finger → "Matched slot 4"; with another finger → "No match".
- [ ] **Camera:** `python -c "from device.hardware import Camera; import cv2; f=Camera().capture(); print(None if f is None else f.shape); cv2.imwrite('test.jpg', f)"` prints a size like `(1080, 1920, 3)` and `test.jpg` looks right. (CSI camera on Bookworm: put `libcamerify` in front of `python`.)
- [ ] **Encodings:** `python -m device.tools.build_encodings dataset` saves one encoding per usable photo.

## The whole station

- [ ] `python -m device.main` → LCD shows "Smart Attendance / Place finger"
- [ ] Scan the maths finger at the door → "Welcome maths / Lecture started", then the countdown "Lec: maths / Ends in …"
- [ ] For a quick test set `LECTURE_MINUTES=5`: six photos are taken at random moments within those 5 minutes, then "Lec: maths / Present: N"
- [ ] Walk out of the room after the first photo: you end up absent ("seen in 1 of 6 photos" on the faculty page)
- [ ] `device/captures/` has one photo per planned moment (6 per hour), with green boxes and roll numbers on the recognised faces
- [ ] The faculty website shows a new maths lecture with the right students present
- [ ] The LCD counts down; after `LECTURE_MINUTES` it returns to "Place finger"
- [ ] Unknown finger → "Not recognised / Please try again"
- [ ] Pull the network cable during a countdown, plug it back in: the next lecture is still saved (the station reconnects)
- [ ] Reboot with the systemd service enabled: the station starts by itself

## Accuracy check (optional, but worth doing once)

Sit the class as usual, run one lecture, and compare the result with a manual roll call.

| Students in the room | Marked present | Missed | Wrongly marked |
| --- | --- | --- | --- |
| | | | |

If students are missed: more light, the camera higher and closer, `FACE_UPSAMPLE=2`, more enrollment photos per student, or `CAPTURE_COUNT=5`. If wrong people are marked: lower `FACE_TOLERANCE` to 0.45.

[Back to setup](setup.md)
