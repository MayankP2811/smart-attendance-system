<?php
// JSON API for the chat page.
//   GET  ?with=ID&after=LAST_ID   -> new messages in this conversation
//   POST with=ID, title, body     -> send (needs the X-CSRF-Token header)
// The browser inserts messages as plain text, so HTML in a message is never run.
require dirname(__DIR__) . '/includes/bootstrap.php';
require dirname(__DIR__) . '/includes/messages.php';

$me = current_user();
if (!$me) {
    json_out(['error' => 'not logged in'], 401);
}
$other = chat_partner($me, (int) ($_REQUEST['with'] ?? 0));
if (!$other) {
    json_out(['error' => 'not allowed'], 403);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_with_csrf();
    $title = trim((string) ($_POST['title'] ?? ''));
    $body = trim((string) ($_POST['body'] ?? ''));
    if ($body === '' || mb_strlen($body) > 1000 || mb_strlen($title) > 150) {
        json_out(['error' => 'Write a message of up to 1000 characters.'], 422);
    }
    q('INSERT INTO messages (sender_id, receiver_id, title, body) VALUES (?, ?, ?, ?)',
        [$me['id'], $other['id'], $title, $body]);
    json_out(['ok' => true, 'id' => (int) db()->lastInsertId()], 201);
}

$rows = chat_messages((int) $me['id'], (int) $other['id'], max(0, (int) ($_GET['after'] ?? 0)));
json_out(['messages' => array_map(fn ($m) => [
    'id' => (int) $m['id'],
    'mine' => (int) $m['sender_id'] === (int) $me['id'],
    'title' => $m['title'],
    'body' => $m['body'],
    'time' => fmt_date($m['created_at'], 'd M, H:i'),
], $rows)]);
