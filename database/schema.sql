-- Smart Attendance System - database schema
-- Works on MySQL 8.0+ and MariaDB 10.6+.
--
-- Design: one row per student per lecture (table `attendance`), so a subject
-- can have any number of lectures and adding a subject is a single row.

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
  id            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  role          ENUM('student','faculty') NOT NULL,
  roll_no       VARCHAR(20)  NULL,            -- students only; also the label used for face recognition
  first_name    VARCHAR(60)  NOT NULL,
  last_name     VARCHAR(60)  NOT NULL,
  email         VARCHAR(190) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,        -- password_hash() / bcrypt
  photo         VARCHAR(255) NULL,            -- profile picture file name in web/uploads/
  department    VARCHAR(40)  NOT NULL DEFAULT 'EXTC',
  class_name    VARCHAR(20)  NOT NULL DEFAULT 'TE',
  is_online     TINYINT(1)   NOT NULL DEFAULT 0,
  created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email),
  UNIQUE KEY uq_users_roll (roll_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS subjects (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  code        VARCHAR(20)  NOT NULL,          -- short name, e.g. 'maths'
  name        VARCHAR(80)  NOT NULL,
  faculty_id  INT UNSIGNED NULL,              -- teacher of this subject
  finger_id   SMALLINT UNSIGNED NULL,         -- fingerprint sensor slot that starts this subject's lecture
  PRIMARY KEY (id),
  UNIQUE KEY uq_subjects_code (code),
  UNIQUE KEY uq_subjects_finger (finger_id),
  CONSTRAINT fk_subjects_faculty FOREIGN KEY (faculty_id) REFERENCES users (id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS lectures (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  subject_id  INT UNSIGNED NOT NULL,
  started_at  DATETIME     NOT NULL,
  ended_at    DATETIME     NULL,
  photos      TINYINT UNSIGNED NOT NULL DEFAULT 0,   -- how many classroom photos were taken and analysed
  PRIMARY KEY (id),
  KEY ix_lectures_subject (subject_id, started_at),
  CONSTRAINT fk_lectures_subject FOREIGN KEY (subject_id) REFERENCES subjects (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS attendance (
  lecture_id  INT UNSIGNED NOT NULL,
  student_id  INT UNSIGNED NOT NULL,
  status      ENUM('present','absent','leave') NOT NULL DEFAULT 'absent',
  source      ENUM('face','faculty') NOT NULL DEFAULT 'face',  -- camera, or changed by the teacher
  seen        TINYINT UNSIGNED NOT NULL DEFAULT 0,  -- in how many of the lecture's photos the student was recognised
  distance    DECIMAL(4,3) NULL,             -- face distance of the best match (lower = closer)
  updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (lecture_id, student_id),
  KEY ix_attendance_student (student_id),
  CONSTRAINT fk_attendance_lecture FOREIGN KEY (lecture_id) REFERENCES lectures (id) ON DELETE CASCADE,
  CONSTRAINT fk_attendance_student FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Leave applications and questions between students and faculty.
CREATE TABLE IF NOT EXISTS messages (
  id           INT UNSIGNED NOT NULL AUTO_INCREMENT,
  sender_id    INT UNSIGNED NOT NULL,
  receiver_id  INT UNSIGNED NOT NULL,
  title        VARCHAR(150) NOT NULL DEFAULT '',
  body         VARCHAR(1000) NOT NULL,
  created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY ix_messages_pair (sender_id, receiver_id, id),
  CONSTRAINT fk_messages_sender   FOREIGN KEY (sender_id)   REFERENCES users (id) ON DELETE CASCADE,
  CONSTRAINT fk_messages_receiver FOREIGN KEY (receiver_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Announcements from faculty, shown to students as alerts.
CREATE TABLE IF NOT EXISTS announcements (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  faculty_id  INT UNSIGNED NOT NULL,
  body        VARCHAR(1000) NOT NULL,
  created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_announcements_faculty FOREIGN KEY (faculty_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
