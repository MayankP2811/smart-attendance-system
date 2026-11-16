<?php
require __DIR__ . '/includes/bootstrap.php';
require __DIR__ . '/includes/messages.php';
$user = require_login();

$other = chat_partner($user, (int) ($_GET['with'] ?? 0));
if (!$other) {
    flash('You can only write to ' . ($user['role'] === 'student' ? 'faculty members.' : 'students.'), 'error');
    redirect('leave.php');
}
$isStudent = $user['role'] === 'student';

page_start('Conversation', $user, 'leave.php', ['css/chat.css']);
?>
<h1><?= $isStudent ? 'Leave Application' : 'Leave Requests' ?></h1>
<section class="chat-area" data-with="<?= (int) $other['id'] ?>" data-me="<?= (int) $user['id'] ?>"
         data-api="<?= e(url('api/messages.php')) ?>">
  <header>
    <a href="<?= e(url('leave.php')) ?>" class="back" aria-label="Back"><span class="material-icons-sharp">arrow_back</span></a>
    <img src="<?= e(photo_url($other['photo'])) ?>" alt="">
    <div class="details"><span><?= e(full_name($other)) ?></span><p><?= $other['is_online'] ? 'Online' : 'Offline' ?></p></div>
  </header>
  <div class="chat-box" aria-live="polite"><p class="text">Loading…</p></div>
  <form class="typing-area" autocomplete="off">
    <input type="text" name="title" class="title-field" maxlength="150"
           placeholder="<?= $isStudent ? 'Subject, e.g. Leave application for 14 Nov' : 'Title (optional)' ?>">
    <div class="row">
      <textarea name="body" class="input-field" maxlength="1000" rows="2" placeholder="Type a message here..." required></textarea>
      <button type="submit" aria-label="Send"><span class="material-icons-sharp">send</span></button>
    </div>
  </form>
</section>
<?php page_end($user, ['js/chat.js']);
