# Implementation status

## What works and how it was tested

**67 automated tests: 66 pass and 1 is skipped by default** (Python 3.13, PHP 8.3, MariaDB 10.11). The skipped one runs real face recognition and needs your own photos (`FACE_TEST_DIR`); it was run on private photos of one team member and passed. The website was also walked through in a real browser (Chromium) with the demo data, on every student and faculty page, with no script errors. The station was run end to end in mock mode, and with real face matching on photos, writing real lectures to the database.

| Area | Covered by tests |
| --- | --- |
| Photo moments | One random moment in each part of the lecture, different every lecture, first photo early and last near the end |
| Presence rule | 4 of 6 photos needed by default; a student who leaves early or arrives very late is absent; a lower `MIN_PRESENCE` counts more students; the threshold for any number of photos |
| Lecture loop | Photos combined with the best distance kept, the clock read for each lecture, LCD countdown and messages never longer than 16 characters, camera failure, unknown or unlinked finger |
| Face matching | Tolerance, unknown faces, one student per face per photo, several photos per student, BGR→RGB, `.npz` encodings load with pickling off, photos with 0 or 2 faces skipped when building encodings |
| Fingerprint | Waits with a short pause instead of a busy loop, returns the slot, unknown finger |
| Database | Each photo committed at once (survives a crash), status updated after every photo, teacher's leave and corrections kept, unknown roll numbers ignored, 128 lectures in one subject, finger relinking |
| Exports | Excel workbook with one sheet per subject and the photos each student was seen in; empty day; CSV download with header, all rows, and protection against spreadsheet formulas |
| Login | Pages need login and send no content when redirecting, same error for wrong password or role, logout only by POST, all hashes bcrypt, cookie HttpOnly, security headers |
| Roles | Signup creates students only (even if "faculty" is posted), students get 403 on faculty pages and the reverse, only a subject's teacher can change its attendance, the admin CLI creates faculty |
| Common attacks | SQL injection attempts on five pages, stored XSS in chat, previews and announcements, missing CSRF token, chat between two students, logging out another user, fake image upload, private files (`includes/`, `cli/`, `.htaccess`) not served |
| Numbers | The same percentage on the dashboard, subject page, analytics and the faculty list; the analytics advice uses the average; photo counts and early departures shown to students and faculty |

Run them with `python -m pytest`. GitHub Actions runs the same tests on MySQL 8 for every push.

## Not tested

- **The real hardware.** The fingerprint sensor, LCD and camera were tested with stand-ins that behave like the libraries the code calls. The first run on the Raspberry Pi should follow the [Pi test checklist](pi-test-checklist.md).
- **Face recognition accuracy in a real classroom.** The matching was checked on a few photos of one person and one stranger (correct match at distance 0.32–0.42, stranger rejected at 0.91). How many students are recognised from the back of a room depends on the camera, the light and the distance; the team's paper noted that faces far from the camera were sometimes missed.
- **Apache/XAMPP.** The website was tested with PHP's built-in server and the `router.php` rules. The `.htaccess` files apply the same rules on Apache.
- **Docker.** `docker-compose.yml` hasn't been run yet.
- **Load.** One class of ten demo students. Not tested with hundreds of students or many classrooms.

## Known limitations

- **Photo spoofing.** Holding up a printed photo of a student would be recognised as that student. There is no liveness check yet (see future scope); the teacher being in the room limits this in practice.
- **One class.** Every lecture includes every student account. Several classes or divisions would need a link between students and subjects.
- **Students register themselves** and choose their roll number. A roll number is blocked only if it is already taken; the class in-charge should check new accounts.
- **No password reset** on the website. The admin can set a new password with SQL or by recreating the account.
- **Faces at a distance.** HOG with `FACE_UPSAMPLE=1` finds faces down to roughly 40×40 pixels. For a large room use a higher-resolution camera, `FACE_UPSAMPLE=2` (slower), or more photos.
- **Borderline cases.** A student seen in exactly half the photos is absent with the default 60 %. The faculty page shows how many photos each student was in, and the teacher can correct the status.

## Privacy

Face photos and the encodings made from them are biometric data. Under India's Digital Personal Data Protection Act, people must be told why their data is collected and must agree to it.

- No face photos, encodings or real student records are in this repository. The demo data is made up.
- `dataset/`, `device/data/`, `device/captures/`, `*.npz` and uploaded profile pictures are git-ignored.
- Enroll only students who have agreed. Keep the encodings and captures on the station or the college server, and delete a student's photos and encodings when they leave (`build_encodings` again without them).
- Set `SAVE_CAPTURES=0` if annotated classroom photos shouldn't be kept.

[Back to README](../README.md)
