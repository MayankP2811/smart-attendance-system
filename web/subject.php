<?php
// One page for every subject: subject.php?code=maths, subject.php?code=bee, ...
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('student');

$subject = subject_by_code((string) ($_GET['code'] ?? ''));
if (!$subject) {
    http_response_code(404);
    flash('That subject does not exist.', 'error');
    redirect('student.php');
}
$summary = null;
foreach (student_subjects((int) $user['id']) as $s) {
    if ((int) $s['id'] === (int) $subject['id']) {
        $summary = $s;
    }
}
$records = student_records((int) $user['id'], (int) $subject['id']);
$faculty = $subject['faculty_id'] ? q('SELECT first_name, last_name FROM users WHERE id = ?', [$subject['faculty_id']])->fetch() : null;

page_start($subject['name'], $user, 'student.php');
?>
<h1><?= e($subject['name']) ?></h1>
<div class="insights">
  <div class="card c-green">
    <span class="material-icons-sharp">analytics</span>
    <div class="middle">
      <div class="left">
        <h3>Total attendance</h3>
        <h1><?= (int) $summary['present'] ?>/<?= (int) $summary['held'] ?></h1>
        <?php if ($summary['on_leave']): ?><p class="muted"><?= (int) $summary['on_leave'] ?> on leave</p><?php endif; ?>
      </div>
      <?= ring($summary['percent']) ?>
    </div>
    <small class="muted">Till now</small>
  </div>
  <div class="card subject-art"><img src="<?= e(subject_icon($subject['code'])) ?>" alt=""></div>
  <div class="card c-teal">
    <span class="material-icons-sharp">group</span>
    <div class="middle"><div class="left">
      <h3>Subject: <?= e(strtoupper($subject['code'])) ?></h3>
      <p><b>Faculty:</b> <?= e($faculty ? full_name($faculty) : 'not assigned') ?></p>
      <p><b>Lectures held:</b> <?= lecture_count((int) $subject['id']) ?></p>
    </div></div>
    <small class="muted">This year</small>
  </div>
</div>

<div class="table-card">
  <h2>Attendance Record</h2>
  <?php if (!$records): ?>
    <p class="muted">No lectures recorded yet.</p>
  <?php else: ?>
  <table>
    <thead><tr><th>Date</th><th>Day</th><th>Time</th><th>Seen by the camera</th><th>Status</th></tr></thead>
    <tbody>
    <?php foreach ($records as $r): $d = new DateTime($r['started_at']); ?>
      <tr>
        <td><?= e($d->format('d M Y')) ?></td>
        <td><?= e($d->format('l')) ?></td>
        <td><?= e($d->format('H:i')) ?></td>
        <td><?= e(seen_label($r)) ?></td>
        <td><span class="status <?= e($r['status']) ?>"><?= e($r['status']) ?></span></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
  <?php endif; ?>
</div>
<?php page_end($user);
