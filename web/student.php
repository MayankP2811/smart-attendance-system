<?php
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('student');

$subjects = student_subjects((int) $user['id']);
$overall = overall_percent($subjects);
$latest = q(
    "SELECT a.body, a.created_at, u.first_name, u.last_name
       FROM announcements a JOIN users u ON u.id = a.faculty_id ORDER BY a.id DESC LIMIT 1"
)->fetch();

page_start('Student dashboard', $user, 'student.php');
?>
<h1>Dashboard</h1>
<div class="insights">
  <div class="card c-green">
    <span class="material-icons-sharp">analytics</span>
    <div class="middle">
      <div class="left">
        <h3>Overall attendance</h3>
        <h1><?= e(pct_label($overall)) ?></h1>
        <p class="muted">Branch <?= e($user['department']) ?> · Class <?= e($user['class_name']) ?> · <?= student_count() ?> students</p>
      </div>
      <?= ring($overall) ?>
    </div>
  </div>
  <div class="card c-purple">
    <span class="material-icons-sharp">person</span>
    <div class="middle"><div class="left">
      <h3>Profile</h3>
      <p><b>Roll No.:</b> <?= e($user['roll_no'] ?? '–') ?></p>
      <p><b>Dept.:</b> <?= e($user['department']) ?></p>
      <p class="email"><b>Email:</b> <?= e($user['email']) ?></p>
    </div></div>
  </div>
  <div class="card c-teal">
    <span class="material-icons-sharp">campaign</span>
    <div class="middle"><div class="left">
      <h3>Latest announcement</h3>
      <?php if ($latest): ?>
        <p class="quote"><?= e($latest['body']) ?></p>
        <small class="muted"><?= e(full_name($latest)) ?> · <?= e(fmt_date($latest['created_at'])) ?></small>
      <?php else: ?><p class="muted">No announcements yet.</p><?php endif; ?>
    </div></div>
  </div>
</div>

<div class="table-card">
  <h2>Subject Attendance</h2>
  <table>
    <thead><tr><th>Sr No</th><th>Subject</th><th>Faculty</th><th>Attended</th><th>Attendance</th><th>Details</th></tr></thead>
    <tbody>
    <?php foreach ($subjects as $i => $s): ?>
      <tr>
        <td><?= sprintf('%02d', $i + 1) ?></td>
        <td><?= e($s['name']) ?></td>
        <td><?= e($s['faculty'] ?? '–') ?></td>
        <td><?= $s['present'] ?> / <?= $s['held'] ?></td>
        <td class="<?= $s['percent'] !== null && $s['percent'] < 75 ? 'warning' : 'success' ?>"><?= e(pct_label($s['percent'])) ?></td>
        <td class="primary"><a href="<?= e(url('subject.php?code=' . urlencode($s['code']))) ?>">Details</a></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
</div>
<?php page_end($user);
