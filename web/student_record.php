<?php
// Faculty: one student's lecture-by-lecture record. The subject's teacher can correct a status
// (for example, mark an approved leave). Changes are saved with source = 'faculty'.
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('faculty');

$student = q("SELECT * FROM users WHERE id = ? AND role = 'student'", [(int) ($_GET['student'] ?? 0)])->fetch();
$subject = subject_by_code((string) ($_GET['subject'] ?? ''));
if (!$student || !$subject) {
    flash('Student or subject not found.', 'error');
    redirect('records.php');
}
$canEdit = (int) $subject['faculty_id'] === (int) $user['id'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_with_csrf();
    if (!$canEdit) {
        http_response_code(403);
        exit('Only the teacher of this subject can change its attendance.');
    }
    $status = (string) ($_POST['status'] ?? '');
    $lectureId = (int) ($_POST['lecture_id'] ?? 0);
    if (in_array($status, ['present', 'absent', 'leave'], true)) {
        $n = q(
            "UPDATE attendance a JOIN lectures l ON l.id = a.lecture_id
                SET a.status = ?, a.source = 'faculty'
              WHERE a.lecture_id = ? AND a.student_id = ? AND l.subject_id = ?",
            [$status, $lectureId, $student['id'], $subject['id']]
        )->rowCount();
        flash($n ? 'Attendance updated.' : 'Nothing changed.');
    }
    redirect('student_record.php?student=' . (int) $student['id'] . '&subject=' . urlencode($subject['code']));
}

$records = student_records((int) $student['id'], (int) $subject['id']);
$present = count(array_filter($records, fn ($r) => $r['status'] === 'present'));

page_start('Student record', $user, 'records.php');
?>
<h1><?= e(full_name($student)) ?> <small class="muted">· <?= e($student['roll_no'] ?? '') ?> · <?= e($subject['name']) ?></small></h1>
<p class="muted"><?= $present ?> of <?= count($records) ?> lectures present (<?= e(pct_label(percent($present, count($records)))) ?>).
  <a href="<?= e(url('records.php?subject=' . urlencode($subject['code']))) ?>">Back to the class list</a></p>
<div class="table-card">
  <table>
    <thead><tr><th>Date</th><th>Time</th><th>Seen by the camera</th><th>Status</th><th>Marked by</th><?= $canEdit ? '<th>Change</th>' : '' ?></tr></thead>
    <tbody>
    <?php foreach ($records as $r): ?>
      <tr>
        <td><?= e(fmt_date($r['started_at'], 'D, d M Y')) ?></td>
        <td><?= e(fmt_date($r['started_at'], 'H:i')) ?></td>
        <td><?= e(seen_label($r)) ?></td>
        <td><span class="status <?= e($r['status']) ?>"><?= e($r['status']) ?></span></td>
        <td><?= e($r['source'] === 'face' ? 'camera' : $r['source']) ?></td>
        <?php if ($canEdit): ?>
        <td>
          <form method="post" class="inline">
            <?= csrf_field() ?>
            <input type="hidden" name="lecture_id" value="<?= (int) $r['lecture_id'] ?>">
            <select name="status" aria-label="New status">
              <?php foreach (['present', 'absent', 'leave'] as $st): ?>
                <option value="<?= $st ?>" <?= $st === $r['status'] ? 'selected' : '' ?>><?= $st ?></option>
              <?php endforeach; ?>
            </select>
            <button type="submit">Save</button>
          </form>
        </td>
        <?php endif; ?>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php page_end($user);
