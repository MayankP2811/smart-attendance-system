<?php
// Students see the faculty's announcements here.
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('student');

$items = q(
    "SELECT a.body, a.created_at, u.first_name, u.last_name
       FROM announcements a JOIN users u ON u.id = a.faculty_id ORDER BY a.id DESC LIMIT 100"
)->fetchAll();

page_start('Alerts', $user, 'alerts.php');
?>
<h1>Announcements</h1>
<div class="table-card feed">
  <?php if (!$items): ?><p class="muted">No announcements yet.</p><?php endif; ?>
  <?php foreach ($items as $a): ?>
    <div class="feed-item">
      <b><?= e(full_name($a)) ?></b>
      <p><?= nl2br(e($a['body'])) ?></p>
      <small class="muted"><?= e(fmt_date($a['created_at'])) ?></small>
    </div>
  <?php endforeach; ?>
</div>
<?php page_end($user);
