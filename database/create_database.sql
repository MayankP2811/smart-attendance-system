-- Run once as the MySQL root user (XAMPP: phpMyAdmin > SQL, or `mysql -u root -p < database/create_database.sql`).
-- Change both passwords to your own, then put the same password in .env as DB_PASSWORD.
CREATE DATABASE IF NOT EXISTS smart_attendance CHARACTER SET utf8mb4;
CREATE USER IF NOT EXISTS 'attendance_app'@'localhost' IDENTIFIED BY 'change-me';
CREATE USER IF NOT EXISTS 'attendance_app'@'127.0.0.1' IDENTIFIED BY 'change-me';
GRANT SELECT, INSERT, UPDATE, DELETE ON smart_attendance.* TO 'attendance_app'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON smart_attendance.* TO 'attendance_app'@'127.0.0.1';
FLUSH PRIVILEGES;
