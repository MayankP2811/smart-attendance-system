<?php
// Faculty: download a subject's attendance as CSV (opens in Excel).
// One row per student per lecture: roll no, name, date, day, time, photos seen in, status.
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('faculty');

$subject = subject_by_code((string) ($_GET['subject'] ?? ''));
if (!$subject) {
    http_response_code(404);
    exit('Subject not found');
}
$rows = q(
    "SELECT u.roll_no, u.first_name, u.last_name, l.started_at, l.photos, a.seen, a.status
       FROM attendance a JOIN lectures l ON l.id = a.lecture_id JOIN users u ON u.id = a.student_id
      WHERE l.subject_id = ? ORDER BY l.started_at, u.roll_no",
    [$subject['id']]
)->fetchAll();

$file = 'attendance_' . preg_replace('/[^a-z0-9_-]/i', '', $subject['code']) . '_' . date('Y-m-d') . '.csv';
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $file . '"');
$out = fopen('php://output', 'w');
fwrite($out, "\xEF\xBB\xBF"); // UTF-8 marker so Excel shows names correctly
fputcsv($out, ['Roll No', 'Name', 'Subject', 'Date', 'Day', 'Time', 'Seen in photos', 'Status'], ',', '"', '');
foreach ($rows as $r) {
    $d = new DateTime($r['started_at']);
    $name = full_name($r);
    // A leading = + - @ would make Excel run the cell as a formula.
    if ($name !== '' && strpbrk($name[0], '=+-@') !== false) {
        $name = "'" . $name;
    }
    fputcsv($out, [$r['roll_no'], $name, $subject['name'], $d->format('Y-m-d'), $d->format('l'), $d->format('H:i'), $r['seen'] . '/' . $r['photos'], $r['status']], ',', '"', '');
}
fclose($out);
