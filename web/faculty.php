<?php
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('faculty');

$mine = faculty_subjects((int) $user['id']);
$lectures = array_sum(array_column($mine, 'lectures'));
$recent = q(
    "SELECT l.id, l.started_at, l.photos, s.name, s.code,
            SUM(a.status = 'present') AS present, COUNT(a.student_id) AS total
       FROM lectures l JOIN subjects s ON s.id = l.subject_id
       LEFT JOIN attendance a ON a.lecture_id = l.id
      WHERE s.faculty_id = ?
      GROUP BY l.id, l.started_at, l.photos, s.name, s.code
      ORDER BY l.started_at DESC LIMIT 5",
    [$user['id']]
)->fetchAll();
$announcements = q(
    "SELECT a.body, a.created_at, u.first_name, u.last_name
       FROM announcements a JOIN users u ON u.id = a.faculty_id ORDER BY a.id DESC LIMIT 3"
)->fetchAll();

page_start('Faculty dashboard', $user, 'faculty.php');
?>
<h1>Dashboard</h1>
<div class="insights">
  <div class="card c-green">
    <span class="material-icons-sharp">analytics</span>
    <div class="middle"><div class="left">
      <h3>Class</h3>
      <p><b>Branch:</b> <?= e($user['department']) ?> · <b>Class:</b> <?= e($user['class_name']) ?></p>
      <p><b>Class strength:</b> <?= student_count() ?></p>
      <p><b>Your lectures recorded:</b> <?= (int) $lectures ?></p>
    </div></div>
  </div>
  <div class="card c-purple">
    <span class="material-icons-sharp">person</span>
    <div class="middle"><div class="left">
      <h3>Profile</h3>
      <p><b>Name:</b> <?= e(full_name($user)) ?></p>
      <p><b>Subjects:</b> <?= e($mine ? implode(', ', array_column($mine, 'name')) : 'none assigned') ?></p>
      <p class="email"><b>Email:</b> <?= e($user['email']) ?></p>
    </div></div>
  </div>
  <div class="card c-teal">
    <span class="material-icons-sharp">fingerprint</span>
    <div class="middle"><div class="left">
      <h3>Start a lecture</h3>
      <p>Scan your finger at the classroom door. The camera inside then takes photos at random moments during the lecture of
        <?= e($mine ? $mine[0]['name'] : 'your subject') ?>.</p>
    </div></div>
  </div>
</div>

<div class="two-col">
  <div class="table-card">
    <h2>Recent lectures</h2>
    <?php if (!$recent): ?><p class="muted">No lectures recorded yet.</p><?php else: ?>
    <table>
      <thead><tr><th>Date</th><th>Subject</th><th>Photos</th><th>Present</th><th></th></tr></thead>
      <tbody>
      <?php foreach ($recent as $r): ?>
        <tr><td><?= e(fmt_date($r['started_at'])) ?></td><td><?= e($r['name']) ?></td><td><?= (int) $r['photos'] ?></td>
          <td><?= (int) $r['present'] ?> / <?= (int) $r['total'] ?></td>
          <td class="primary"><a href="<?= e(url('records.php?subject=' . urlencode($r['code']))) ?>">View</a></td></tr>
      <?php endforeach; ?>
      </tbody>
    </table>
    <?php endif; ?>
  </div>
  <div class="table-card">
    <h2>Student Announcements</h2>
    <?php if (!$announcements): ?><p class="muted">No announcements yet.</p><?php endif; ?>
    <?php foreach ($announcements as $a): ?>
      <div class="feed-item"><b><?= e(full_name($a)) ?></b><p><?= e($a['body']) ?></p>
        <small class="muted"><?= e(fmt_date($a['created_at'])) ?></small></div>
    <?php endforeach; ?>
  </div>
</div>
<?php page_end($user);
