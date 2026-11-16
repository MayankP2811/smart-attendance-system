<?php
// Students: choose a teacher to send a leave application or question to.
// Faculty: see the students who have written to them.
require __DIR__ . '/includes/bootstrap.php';
require __DIR__ . '/includes/messages.php';
$user = require_login();

$contacts = chat_contacts($user);
$isStudent = $user['role'] === 'student';

page_start($isStudent ? 'Leave application' : 'Leave requests', $user, 'leave.php');
?>
<h1><?= $isStudent ? 'Choose the Faculty Member' : 'Student Leave Applications' ?></h1>
<div class="table-card contacts">
  <p class="muted"><?= $isStudent ? 'Send an application to your teacher or class in-charge.' : 'Students who have written to you.' ?></p>
  <input type="search" class="contact-filter" placeholder="Search by name..." aria-label="Search by name">
  <?php if (!$contacts): ?><p class="muted">No messages yet.</p><?php endif; ?>
  <?php foreach ($contacts as $c): ?>
    <a class="contact" href="<?= e(url('chat.php?with=' . (int) $c['id'])) ?>" data-name="<?= e(strtolower(full_name($c))) ?>">
      <img src="<?= e(photo_url($c['photo'])) ?>" alt="">
      <div class="details">
        <span><?= e(full_name($c)) ?><?= $c['roll_no'] ? ' · ' . e($c['roll_no']) : '' ?></span>
        <p><?= $c['last_body'] === null ? 'No messages yet' : ($c['last_is_mine'] ? 'You: ' : '') . e(mb_strimwidth($c['last_body'], 0, 60, '…')) ?></p>
      </div>
      <i class="dot <?= $c['is_online'] ? 'online' : '' ?>" title="<?= $c['is_online'] ? 'Online' : 'Offline' ?>"></i>
    </a>
  <?php endforeach; ?>
</div>
<?php page_end($user, ['js/app.js']);
