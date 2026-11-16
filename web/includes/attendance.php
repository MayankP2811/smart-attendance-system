<?php
// Attendance numbers. Every page uses these functions, so the same student
// always gets the same percentage everywhere.
//
// Percentage = lectures marked 'present' / lectures the student was enrolled for x 100.
// 'present' means recognised in enough of the lecture's photos (MIN_PRESENCE on the station),
// so a student who leaves early is 'absent'. 'leave' counts as not present, but is shown separately.
declare(strict_types=1);

function percent(int $present, int $held): ?float
{
    return $held > 0 ? round($present * 100 / $held, 1) : null;
}

function pct_label(?float $p): string
{
    return $p === null ? '–' : rtrim(rtrim(number_format($p, 1), '0'), '.') . '%';
}

/** Per-subject summary for one student. */
function student_subjects(int $studentId): array
{
    $rows = q(
        "SELECT s.id, s.code, s.name, CONCAT(f.first_name, ' ', f.last_name) AS faculty,
                COUNT(a.lecture_id) AS held,
                COALESCE(SUM(a.status = 'present'), 0) AS present,
                COALESCE(SUM(a.status = 'leave'), 0) AS on_leave
           FROM subjects s
           LEFT JOIN users f ON f.id = s.faculty_id
           LEFT JOIN lectures l ON l.subject_id = s.id
           LEFT JOIN attendance a ON a.lecture_id = l.id AND a.student_id = ?
          GROUP BY s.id, s.code, s.name, f.first_name, f.last_name
          ORDER BY s.id",
        [$studentId]
    )->fetchAll();
    foreach ($rows as &$r) {
        $r['held'] = (int) $r['held'];
        $r['present'] = (int) $r['present'];
        $r['on_leave'] = (int) $r['on_leave'];
        $r['percent'] = percent($r['present'], $r['held']);
    }
    return $rows;
}

/** Average of the subject percentages (subjects with no lectures yet are left out). */
function overall_percent(array $subjects): ?float
{
    $values = array_values(array_filter(array_column($subjects, 'percent'), fn ($p) => $p !== null));
    return $values ? round(array_sum($values) / count($values), 1) : null;
}

/** The advice message shown on the analytics page, based on the average attendance. */
function attendance_advice(?float $avg): array
{
    if ($avg === null) {
        return ['info', 'No lectures have been recorded yet.'];
    }
    $a = pct_label($avg);
    if ($avg < 50) {
        return ['poor', "Dear Student, your average attendance is $a, which is very poor. It may affect your "
            . 'academic performance. Please contact your class in-charge within 2 working days and improve your attendance.'];
    }
    if ($avg < 75) {
        return ['moderate', "Dear Student, your average attendance is $a, which is moderate. Please treat this "
            . 'as an early warning and improve attendance in the subjects where it is low.'];
    }
    return ['good', "Dear Student, your average attendance is $a, which is good. Keep it up!"];
}

/** Lecture-by-lecture record of one student in one subject. */
function student_records(int $studentId, int $subjectId): array
{
    return q(
        "SELECT l.id AS lecture_id, l.started_at, l.photos, a.status, a.source, a.seen
           FROM lectures l
           JOIN attendance a ON a.lecture_id = l.id AND a.student_id = ?
          WHERE l.subject_id = ?
          ORDER BY l.started_at DESC",
        [$studentId, $subjectId]
    )->fetchAll();
}

/** Every student's numbers for one subject (faculty view). */
function class_summary(int $subjectId): array
{
    $rows = q(
        "SELECT u.id, u.roll_no, u.first_name, u.last_name, u.department,
                COUNT(a.lecture_id) AS held,
                COALESCE(SUM(a.status = 'present'), 0) AS present,
                COALESCE(SUM(a.status = 'leave'), 0) AS on_leave,
                COALESCE(SUM(a.status = 'absent' AND a.seen > 0), 0) AS left_early
           FROM users u
           LEFT JOIN attendance a ON a.student_id = u.id
                AND a.lecture_id IN (SELECT id FROM lectures WHERE subject_id = ?)
          WHERE u.role = 'student'
          GROUP BY u.id, u.roll_no, u.first_name, u.last_name, u.department
          ORDER BY u.roll_no IS NULL, u.roll_no, u.first_name",
        [$subjectId]
    )->fetchAll();
    foreach ($rows as &$r) {
        $r['held'] = (int) $r['held'];
        $r['present'] = (int) $r['present'];
        $r['on_leave'] = (int) $r['on_leave'];
        $r['left_early'] = (int) $r['left_early'];
        $r['percent'] = percent($r['present'], $r['held']);
    }
    return $rows;
}

/** "4 of 6 photos" - how often the camera saw the student in that lecture. */
function seen_label(array $r): string
{
    if ($r['source'] === 'faculty' && (int) $r['seen'] === 0) {
        return '–';
    }
    return (int) $r['seen'] . ' of ' . (int) $r['photos'] . ' photos';
}

function subject_by_code(string $code): ?array
{
    return q('SELECT * FROM subjects WHERE code = ?', [$code])->fetch() ?: null;
}

function faculty_subjects(int $facultyId): array
{
    return q(
        'SELECT s.*, (SELECT COUNT(*) FROM lectures l WHERE l.subject_id = s.id) AS lectures
           FROM subjects s WHERE s.faculty_id = ? ORDER BY s.id',
        [$facultyId]
    )->fetchAll();
}

function lecture_count(int $subjectId): int
{
    return (int) q('SELECT COUNT(*) FROM lectures WHERE subject_id = ?', [$subjectId])->fetchColumn();
}

function student_count(): int
{
    return (int) q("SELECT COUNT(*) FROM users WHERE role = 'student'")->fetchColumn();
}

/** Subject icon file for a subject code (falls back to a generic book). */
function subject_icon(string $code): string
{
    $known = ['maths', 'physics', 'chemistry', 'ema', 'bee'];
    return asset('img/subjects/' . (in_array($code, $known, true) ? $code : 'generic') . '.svg');
}
