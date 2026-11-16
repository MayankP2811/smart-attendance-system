<?php
// Faculty: post an announcement. Students see it under Alerts.
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('faculty');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_with_csrf();
    $body = trim((string) ($_POST['body'] ?? ''));
    if ($body === '' || mb_strlen($body) > 1000) {
        flash('Write a message of up to 1000 characters.', 'error');
    } else {
        q('INSERT INTO announcements (faculty_id, body) VALUES (?, ?)', [$user['id'], $body]);
        flash('Announcement posted.');
    }
    redirect('announce.php');   // Post/Redirect/Get: refreshing won't post it twice
}

$items = q(
    "SELECT a.body, a.created_at, u.first_name, u.last_name, a.faculty_id
       FROM announcements a JOIN users u ON u.id = a.faculty_id ORDER BY a.id DESC LIMIT 50"
)->fetchAll();

page_start('Announcements', $user, 'announce.php');
?>
<h1>Announcement</h1>
<form method="post" class="compose table-card">
  <?= csrf_field() ?>
  <label for="body"><b>New announcement for students</b></label>
  <textarea id="body" name="body" maxlength="1000" rows="3" placeholder="Type a message here..." required></textarea>
  <button type="submit"><span class="material-icons-sharp">send</span> Post</button>
</form>
<div class="table-card feed">
  <?php if (!$items): ?><p class="muted">No announcements yet.</p><?php endif; ?>
  <?php foreach ($items as $a): ?>
    <div class="feed-item <?= (int) $a['faculty_id'] === (int) $user['id'] ? 'mine' : '' ?>">
      <b><?= e(full_name($a)) ?></b><p><?= nl2br(e($a['body'])) ?></p>
      <small class="muted"><?= e(fmt_date($a['created_at'])) ?></small>
    </div>
  <?php endforeach; ?>
</div>
<?php page_end($user);
