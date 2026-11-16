<?php
// Leave applications / questions: students write to faculty and faculty reply.
declare(strict_types=1);

/** Students may talk to faculty, and faculty to students. Returns the other person or null. */
function chat_partner(array $me, int $otherId): ?array
{
    $want = $me['role'] === 'student' ? 'faculty' : 'student';
    return q('SELECT id, role, first_name, last_name, photo, is_online, roll_no FROM users WHERE id = ? AND role = ?',
        [$otherId, $want])->fetch() ?: null;
}

/** People shown on the leave page, with the last message of each conversation. */
function chat_contacts(array $me): array
{
    $id = (int) $me['id'];
    $sql = "SELECT u.id, u.first_name, u.last_name, u.photo, u.is_online, u.roll_no,
                   m.body AS last_body, (m.sender_id = :me1) AS last_is_mine
              FROM users u
              LEFT JOIN messages m ON m.id = (
                   SELECT MAX(x.id) FROM messages x
                    WHERE (x.sender_id = u.id AND x.receiver_id = :me2)
                       OR (x.sender_id = :me3 AND x.receiver_id = u.id))
             WHERE u.role = :role";
    $params = ['me1' => $id, 'me2' => $id, 'me3' => $id];
    if ($me['role'] === 'student') {
        $params['role'] = 'faculty';
    } else {
        // faculty see the students who have written to them
        $params['role'] = 'student';
        $sql .= ' AND m.id IS NOT NULL';
    }
    $sql .= ' ORDER BY m.id IS NULL, m.id DESC, u.first_name';
    return q($sql, $params)->fetchAll();
}

function chat_messages(int $me, int $other, int $afterId = 0): array
{
    return q(
        'SELECT id, sender_id, title, body, created_at FROM messages
          WHERE id > ? AND ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
          ORDER BY id LIMIT 200',
        [$afterId, $me, $other, $other, $me]
    )->fetchAll();
}
