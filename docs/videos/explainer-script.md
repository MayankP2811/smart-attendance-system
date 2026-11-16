# Explainer video: narration script

`smart-attendance-explainer.mp4` · 1280×720 · 30 fps · 2 min 41 s · computer-generated voice (Kokoro TTS, voice af_heart). Captions are burnt in; the same text is in `smart-attendance-explainer.srt`.

| Time | Scene | On screen | Narration |
| --- | --- | --- | --- |
| 0:00 | Title | Project name, team, illustration | This is the Smart Attendance System, a B.E. project by team Innovative_Heads at VCET, Mumbai University. It takes classroom attendance using face recognition. |
| 0:14 | The problem | Three cards: minutes lost, proxy attendance, a student marked present who walks out | Calling names takes several minutes of every lecture. Friends can answer for students who are not there. And a student can be marked present, then quietly leave a few minutes later. |
| 0:26 | The setup | The classroom picture: fingerprint sensor outside the door, camera on the wall, Raspberry Pi in between, each highlighted in turn | A fingerprint sensor sits outside the classroom door, and every teacher scans a finger while entering. Inside, a camera on the wall faces the whole class, and a Raspberry Pi between them does the processing. |
| 0:41 | At the classroom door | Fingerprint scan → slot 4 → Engineering Mathematics → LCD "Welcome maths" | Each enrolled finger belongs to a subject, so the system knows which lecture has started, and the LCD greets the teacher. |
| 0:50 | Throughout the lecture | A 60-minute timeline with six random photo moments, and five students' sightings filling in; Rohan leaves early and Kabir comes late, both absent | During the lecture, the camera takes six photos of the class at random moments, so nobody can predict the next one. A student counts as present only if seen in at least 60 % of the photos. Someone who is marked at the start and then leaves ends up absent. |
| 1:10 | Face recognition | A classroom photo (3 of 6), a face turned into 128 numbers, the distance bar, green boxes with roll numbers | In each photo, faces are found with HOG detection and turned into 128 numbers. If those numbers are close enough to a known student, the photo counts for that student. |
| 1:25 | Saved at once | The attendance table with the photos each student was seen in; the LCD countdown | After every photo, the result is saved in MySQL. Meanwhile, the LCD counts down the lecture. |
| 1:33 | For students | Real screens: student dashboard, then analytics with the warning | Students log in to see their attendance in every subject, lecture by lecture. The analytics page warns them early when their average falls below 75 % or 50 %. |
| 1:47 | For faculty | Real screens: attendance list with the Left early column, then a leave application and reply | Faculty see the whole class, including who left early, correct a status or mark a leave, and download the record for Excel. Students send leave applications, and teachers reply. |
| 2:01 | Recognition | Four cards: 1st Oscillations'23, 2nd Tech-A-Thon'23, 2nd VNPS'23, 2nd Electrowiz 2023 | The project won first place at the Oscillations technical paper presentation, and second prizes at Tech-A-Thon, the VNPS project showcase, and Electrowiz. |
| 2:15 | Future scope | The future-scope diagram: several rooms on one central server, and features for students, faculty and the college | In future, every classroom can connect to one central server, saving time in every lecture across the college. Students could get an app and alerts for parents, and faculty automatic defaulter lists and timetable integration. |
| 2:32 | Team | Team names and the repository link | Built by Mayank Patil, Omkar Joshi, Chandan Thakur and Parth Mhatre. |

The website scenes are screenshots of the website running on localhost with the made-up demo data. The other scenes are animations drawn for this video from the team's presentation and paper.
