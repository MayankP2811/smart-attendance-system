"""Website tests: logins, roles, common web attacks, and the numbers on each page."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import mysql.connector

from tests.web.conftest import Client, csrf_of

ROOT = Path(__file__).resolve().parents[2]
ROHAN = 8          # demo student TE03 (low attendance)
PRIYA = 1          # demo faculty, teaches maths


def sql(site, query, params=()):
    s = site["settings"]
    conn = mysql.connector.connect(host=s.db_host, port=s.db_port, user=s.db_user, password=s.db_password,
                                   database=site["db"])
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall() if cur.with_rows else None
    conn.commit()
    conn.close()
    return rows


# ------------------------------------------------------------------ login & sessions
def test_pages_need_login_and_send_no_content(client):
    for page in ["student.php", "faculty.php", "records.php", "analytics.php", "subject.php?code=maths",
                 "leave.php", "chat.php?with=1", "announce.php", "export.php?subject=maths"]:
        r = client.page(page)
        assert r.status_code == 302 and r.headers["Location"].endswith("/login.php"), page
        assert len(r.content) == 0, page        # nothing of the page is sent before the redirect


def test_login_errors_do_not_reveal_which_part_was_wrong(client):
    wrong_pw = client.login("aarav.sharma@example.com", "student", "nope")
    wrong_role = client.login("aarav.sharma@example.com", "faculty")
    for r in (wrong_pw, wrong_role):
        assert r.status_code == 200 and "E-mail, password or role is not correct." in r.text


def test_login_and_logout(student):
    assert student.page("student.php").status_code == 200
    assert student.page("logout.php").status_code == 405           # logout by link is refused
    assert student.page("student.php").status_code == 200
    r = student.post_form("logout.php", {}, token_from="student.php")
    assert r.status_code == 302
    assert student.page("student.php").status_code == 302


def test_session_cookie_flags(site):
    c = Client(site["base"])
    c.page("login.php")
    assert "sas_session" in c.cookies
    jar = next(x for x in c.cookies if x.name == "sas_session")
    assert jar.has_nonstandard_attr("HttpOnly")


def test_security_headers(client):
    h = client.page("login.php").headers
    assert h["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert h["X-Content-Type-Options"] == "nosniff"


def test_passwords_are_bcrypt(site):
    hashes = [h for (h,) in sql(site, "SELECT password_hash FROM users")]
    assert all(h.startswith("$2y$") for h in hashes)


def test_private_files_are_not_served(client):
    for path in ["includes/db.php", "includes/config.php", "cli/create_user.php", ".htaccess", "router.php",
                 "uploads/.htaccess"]:
        assert client.page(path).status_code == 404, path


# ------------------------------------------------------------------ roles
def test_signup_creates_students_only(site, client):
    data = {"first_name": "New", "last_name": "Person", "email": "new.person@example.com", "roll_no": "te11",
            "password": "longenough1", "role": "faculty", "select1": "Faculty"}
    r = client.post_form("signup.php", data, token_from="signup.php")
    assert r.status_code == 302
    assert sql(site, "SELECT role, roll_no FROM users WHERE email='new.person@example.com'") == [("student", "TE11")]


def test_signup_validation(client):
    base = {"first_name": "A", "last_name": "B", "email": "x@example.com", "roll_no": "TE01", "password": "longenough1"}
    r = client.post_form("signup.php", base, token_from="signup.php")
    assert "already registered" in r.text                                # TE01 is taken
    r = client.post_form("signup.php", {**base, "roll_no": "TE99", "password": "short"}, token_from="signup.php")
    assert "at least 8 characters" in r.text
    r = client.post_form("signup.php", {**base, "roll_no": "TE99", "email": "not-an-email"}, token_from="signup.php")
    assert "valid e-mail" in r.text


def _upload(client, filename, content, mime, email):
    token = csrf_of(client.get(client.base + "signup.php").text)
    data = {"csrf": token, "first_name": "Up", "last_name": "Load", "email": email,
            "roll_no": "U" + str(abs(hash(email)) % 10000), "password": "longenough1"}
    return client.post(client.base + "signup.php", data=data, files={"photo": (filename, content, mime)},
                       allow_redirects=False)


def test_upload_checks_the_real_file_content(site, client):
    import numpy as np
    import cv2
    ok, jpg = cv2.imencode(".jpg", np.zeros((20, 20, 3), np.uint8))
    assert _upload(client, "ME.JPG", jpg.tobytes(), "image/jpeg", "up1@example.com").status_code == 302  # capital .JPG ok
    photo = sql(site, "SELECT photo FROM users WHERE email='up1@example.com'")[0][0]
    assert re.fullmatch(r"[0-9a-f]{24}\.jpg", photo)                    # random name, not the user's file name
    bad = _upload(client, "shell.php.png", b"<?php echo 'pwned'; ?>", "image/png", "up2@example.com")
    assert bad.status_code == 200 and "must be a JPG or PNG" in bad.text
    assert sql(site, "SELECT COUNT(*) FROM users WHERE email='up2@example.com'")[0][0] == 0
    (ROOT / "web" / "uploads" / photo).unlink()


def test_student_cannot_open_faculty_pages(student):
    for page in ["faculty.php", "records.php", "announce.php", "export.php?subject=maths",
                 f"student_record.php?student={ROHAN}&subject=maths"]:
        r = student.page(page)
        assert r.status_code == 403, page
        assert "Attendance List" not in r.text


def test_faculty_cannot_open_student_pages(faculty):
    for page in ["student.php", "analytics.php", "subject.php?code=maths", "alerts.php"]:
        assert faculty.page(page).status_code == 403, page


def test_only_the_subjects_teacher_can_change_attendance(site, faculty):
    page = f"student_record.php?student={ROHAN}&subject=physics"   # Priya doesn't teach physics
    html = faculty.page(page).text
    assert "<th>Change</th>" not in html
    lecture = sql(site, "SELECT MIN(id) FROM lectures WHERE subject_id=2")[0][0]
    r = faculty.post_form(page, {"lecture_id": lecture, "status": "present"}, token_from=page)
    assert r.status_code == 403


def test_teacher_marks_leave(site, faculty):
    page = f"student_record.php?student={ROHAN}&subject=maths"
    lecture = sql(site, "SELECT MAX(id) FROM lectures WHERE subject_id=1")[0][0]
    r = faculty.post_form(page, {"lecture_id": lecture, "status": "leave"}, token_from=page)
    assert r.status_code == 302
    assert sql(site, "SELECT status, source FROM attendance WHERE lecture_id=%s AND student_id=%s",
               (lecture, ROHAN)) == [("leave", "faculty")]


# ------------------------------------------------------------------ common attacks
def test_sql_injection_attempts_are_harmless(student, faculty):
    r = faculty.page("records.php", params={"subject": "maths' OR '1'='1"})
    assert r.status_code == 200 and "Rohan" not in r.text             # unknown subject -> no rows
    r = faculty.page("student_record.php", params={"student": "8 OR 1=1", "subject": "maths"})
    assert r.status_code in (200, 302)
    r = student.page("chat.php", params={"with": "1 OR 1=1"})
    assert r.status_code in (200, 302)
    r = student.page("api/messages.php", params={"with": "0 OR 1=1"})
    assert r.status_code == 403
    r = student.page("subject.php", params={"code": "' UNION SELECT password_hash FROM users -- "})
    assert "$2y$" not in r.text


def test_messages_and_announcements_are_escaped(site, student, faculty):
    evil = '<img src=x onerror=alert(document.cookie)>'
    token = csrf_of(student.page("chat.php?with=1").text)
    r = student.post(student.base + "api/messages.php", data={"with": PRIYA, "title": evil, "body": evil},
                     headers={"X-CSRF-Token": token})
    assert r.status_code == 201
    # The API returns JSON and the page inserts it with textContent, never as HTML.
    api = faculty.page("api/messages.php", params={"with": 6})
    assert api.headers["Content-Type"].startswith("application/json")
    assert api.json()["messages"][-1]["body"] == evil
    assert evil not in faculty.page("leave.php").text                    # last-message preview is escaped
    assert "&lt;img src=x onerror" in faculty.page("leave.php").text
    r = faculty.post_form("announce.php", {"body": evil}, token_from="announce.php")
    assert r.status_code == 302
    alerts = student.page("alerts.php").text
    assert evil not in alerts and "&lt;img src=x onerror=alert(document.cookie)&gt;" in alerts
    sql(site, "DELETE FROM announcements WHERE body=%s", (evil,))


def test_post_without_csrf_token_is_rejected(faculty, student):
    assert faculty.post(faculty.base + "announce.php", data={"body": "hi"}, allow_redirects=False).status_code == 400
    r = student.post(student.base + "api/messages.php", data={"with": PRIYA, "body": "hi"})
    assert r.status_code == 400


def test_chat_only_between_students_and_faculty(student):
    assert student.page("api/messages.php", params={"with": 7}).status_code == 403    # another student
    r = student.page("chat.php", params={"with": 7})
    assert r.status_code == 302 and r.headers["Location"].endswith("/leave.php")


def test_logout_cannot_touch_other_users(site, student):
    sql(site, "UPDATE users SET is_online=1 WHERE id=%s", (PRIYA,))
    student.get(student.base + f"logout.php?logout_id={PRIYA}")
    assert sql(site, "SELECT is_online FROM users WHERE id=%s", (PRIYA,))[0][0] == 1


# ------------------------------------------------------------------ the numbers
def _percent_after(label, html):
    m = re.search(re.escape(label) + r".*?(\d+(?:\.\d)?)%", html, re.S)
    return m.group(1) if m else None


def test_same_percentage_on_every_page(site):
    rohan = Client(site["base"])
    assert rohan.login("rohan.kulkarni@example.com", "student").status_code == 302
    present, held = sql(site, "SELECT SUM(a.status='present'), COUNT(*) FROM attendance a "
                              "JOIN lectures l ON l.id=a.lecture_id WHERE l.subject_id=1 AND a.student_id=%s", (ROHAN,))[0]
    expected = f"{round(100 * float(present) / held, 1):g}"
    dash = rohan.page("student.php").text
    assert _percent_after("Engineering Mathematics", dash) == expected
    subject = rohan.page("subject.php?code=maths").text
    assert f"{int(present)}/{held}" in subject and f"<p>{expected}%</p>" in subject
    analytics = rohan.page("analytics.php").text
    assert f'"values":[{float(expected):g}' in analytics.replace(".0,", ",") or expected in analytics
    prof = Client(site["base"])
    prof.login("priya.deshmukh@example.com", "faculty")
    rec = prof.page("records.php?subject=maths").text
    row = re.search(r"TE03</td>.*?</tr>", rec, re.S).group(0)
    assert f">{expected}%<" in row


def test_analytics_advice_uses_the_average(site):
    """The message depends on the average of the subject percentages."""
    rohan = Client(site["base"])
    rohan.login("rohan.kulkarni@example.com", "student")
    html = rohan.page("analytics.php").text
    assert 'class="advice poor"' in html and "very poor" in html
    tanvi = Client(site["base"])
    tanvi.login("tanvi.more@example.com", "student")
    assert 'class="advice good"' in tanvi.page("analytics.php").text


def test_csv_export(faculty, site):
    r = faculty.page("export.php?subject=maths")
    assert r.status_code == 200 and r.headers["Content-Type"].startswith("text/csv")
    lines = r.content.decode("utf-8-sig").strip().splitlines()
    assert lines[0] == '"Roll No",Name,Subject,Date,Day,Time,"Seen in photos",Status'
    lectures = sql(site, "SELECT COUNT(*) FROM lectures WHERE subject_id=1")[0][0]
    assert len(lines) == 1 + lectures * 10


def test_csv_export_blocks_spreadsheet_formulas(site, faculty):
    sql(site, "UPDATE users SET first_name='=HYPERLINK(\"http://x\")' WHERE id=%s", (ROHAN,))
    body = faculty.page("export.php?subject=maths").content.decode("utf-8-sig")
    assert ",'=HYPERLINK" in body.replace('"', "")
    sql(site, "UPDATE users SET first_name='Rohan' WHERE id=%s", (ROHAN,))


def test_photo_counts_and_early_leavers_are_shown(site, student, faculty):
    sub = student.page("subject.php?code=maths").text
    assert "Seen by the camera" in sub and re.search(r"\d of 6 photos", sub)
    rec = faculty.page("records.php?subject=maths").text
    assert "Left early" in rec
    expected = sql(site, "SELECT COUNT(*) FROM attendance a JOIN lectures l ON l.id=a.lecture_id "
                         "WHERE l.subject_id=1 AND a.student_id=%s AND a.status='absent' AND a.seen>0", (ROHAN,))[0][0]
    row = re.search(r"TE03</td>.*?</tr>", rec, re.S).group(0)
    cells = re.findall(r"<td[^>]*>([^<]*)</td>", row)
    assert cells[3].strip() == str(expected)          # after the roll no: name, dept, present, left early
    detail = faculty.page(f"student_record.php?student={ROHAN}&subject=maths").text
    assert "of 6 photos" in detail


def test_unknown_subject_page(student):
    r = student.page("subject.php?code=nope")
    assert r.status_code == 302


def test_cli_creates_faculty_and_assigns_subject(site):
    env = {"APP_ENV_FILE": str(site["env_file"]), "PATH": "/usr/bin:/bin:/usr/local/bin"}
    out = subprocess.run(["php", "web/cli/create_user.php", "--role=faculty", "--first=New", "--last=Teacher",
                          "--email=new.teacher@example.com", "--subjects=ema", "--password=StrongPass1"],
                         cwd=ROOT, env=env, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert "teaches ema" in out.stdout
    assert sql(site, "SELECT u.email FROM subjects s JOIN users u ON u.id=s.faculty_id WHERE s.code='ema'") == \
        [("new.teacher@example.com",)]
    teacher = Client(site["base"])
    assert teacher.login("new.teacher@example.com", "faculty", "StrongPass1").status_code == 302
