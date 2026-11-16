# The team's paper and presentation

## Paper: *Smart Attendance System using Face Recognition Method*

Mayank Patil, Chandan Thakur, Omkar Joshi, Manthan Patil — Department of Electronics and Telecommunication Engineering, VCET (University of Mumbai). 1st place at the Oscillations'23 technical paper presentation.

**Problem.** Calling names wastes lecture time; RFID cards can be lost or lent for proxy attendance; fingerprint, iris and voice systems have their own flaws. Face recognition is contactless and passive: the student doesn't have to do anything.

**Method.**

- *Face detection* with the histogram of oriented gradients (HOG).
- *Face matching* with deep metric learning: each face becomes a 128-dimensional embedding, and `compare_faces` measures the Euclidean distance to every face in the dataset. A match within the threshold leads to attendance marking.
- The result is an attendance table with name, roll number, date, day, time and subject, which can be exported to an Excel sheet per subject.
- Front end in PHP, back end in Python, MySQL in between.

**Literature reviewed.**

1. Y. Bharat Chandra, G. Karthikeya Reddy, "A Comparative Analysis of Face Recognition Models on Masked Faces", *IJSTR* 9(10), October 2020 — compares VGGFace, FaceNet, OpenFace and DeepFace on the RMFRD masked-face dataset.
2. D. Kengalagutti, Chethana G, "Comparing Database Management Systems: MySQL, PostgreSQL, SQLite", *IRJET* 7(6), June 2020.
3. R. Jain, A. Sen, K. Paliwal, "A Comparative Analysis of New Cow Concept of Node.js with PHP", *IJERT*, 2020.

**Results and conclusion.** Training set of 6 students. The system worked across different poses and variations, but sometimes failed to recognise students far from the camera, and was limited by processing power.

## Presentation (Tech-A-Thon'23)

- **Vision:** a contactless, centralised and dynamic attendance system that saves time and supports analysis of student data.
- **Mission:** reduce human error, proxy attendance and paperwork.
- **Flowchart:** biometric authentication (faculty) → subject identified → pictures captured at specific intervals → face recognition → attendance recorded in the subject's database.
- **Interface chart:** students get subject-wise attendance, analytics, leave application and notifications; faculty get the attendance record, announcements and leave requests.
- **Hardware:** Raspberry Pi 4B (ARM Cortex-A72 at 1.5 GHz, up to 8 GB RAM, 40 GPIO pins), camera module (8 MP Sony IMX219, 1080p30 / 720p60), fingerprint sensor (508 DPI, 200 templates, 192×192 array).
- **Software:** MySQL Workbench, Python, VS Code, XAMPP.

## How this repository follows them

| Paper / presentation | In this repository |
| --- | --- |
| Faculty fingerprint identifies the subject | `subjects.finger_id`, `device/tools/fingerprint_admin.py` |
| Pictures captured at intervals during the lecture | `CAPTURE_COUNT` photos at random moments, present if seen in `MIN_PRESENCE` of them |
| HOG detection + 128-d embeddings + distance threshold | `device/face.py` (`FACE_MODEL=hog`, `FACE_TOLERANCE`) |
| Attendance recorded per subject | `lectures` + `attendance` tables |
| Present, absent and leave | `attendance.status` |
| Name, roll no, date, day, time, subject → Excel | `device/tools/export_excel.py`, CSV download on the website |
| Student: attendance, analytics, leave application, alerts | `student.php`, `subject.php`, `analytics.php`, `leave.php`, `alerts.php` |
| Faculty: attendance record, announcements, leave requests | `faculty.php`, `records.php`, `announce.php`, `leave.php` |

The original PDFs are kept by the team and are not published here, because they contain photos of students and stock images.

[Back to README](../README.md)
