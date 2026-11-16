<?php
// Create a faculty (or student) account from the command line. Only the admin
// can do this: faculty accounts can't be created from the website.
//
//   php web/cli/create_user.php --role=faculty --first=Priya --last=Deshmukh \
//       --email=priya@college.edu --subjects=maths,physics
//   php web/cli/create_user.php --role=student --first=Aarav --last=Sharma --email=a@x.com --roll=TE01
//
// The password is asked for on the keyboard (or pass --password=... in scripts).
declare(strict_types=1);

if (PHP_SAPI !== 'cli') {
    http_response_code(404);
    exit;
}
require dirname(__DIR__) . '/includes/config.php';
require dirname(__DIR__) . '/includes/db.php';
date_default_timezone_set(config('APP_TIMEZONE', 'Asia/Kolkata'));

$o = getopt('', ['role:', 'first:', 'last:', 'email:', 'roll::', 'subjects::', 'password::']);
$role = $o['role'] ?? '';
if (!in_array($role, ['faculty', 'student'], true) || empty($o['first']) || empty($o['last']) || empty($o['email'])) {
    fwrite(STDERR, "Usage: php web/cli/create_user.php --role=faculty|student --first=NAME --last=NAME --email=EMAIL"
        . " [--roll=TE01] [--subjects=maths,bee] [--password=...]\n");
    exit(2);
}
if (!filter_var($o['email'], FILTER_VALIDATE_EMAIL)) {
    fwrite(STDERR, "Not a valid e-mail address.\n");
    exit(2);
}
if ($role === 'student' && empty($o['roll'])) {
    fwrite(STDERR, "Students need --roll (the same roll number used for their face photos).\n");
    exit(2);
}
$password = $o['password'] ?? null;
if ($password === null) {
    echo 'Password (min. 8 characters): ';
    if (DIRECTORY_SEPARATOR === '/') {
        system('stty -echo');
    }
    $password = trim((string) fgets(STDIN));
    if (DIRECTORY_SEPARATOR === '/') {
        system('stty echo');
    }
    echo "\n";
}
if (strlen($password) < 8) {
    fwrite(STDERR, "The password needs at least 8 characters.\n");
    exit(2);
}
try {
    q('INSERT INTO users (role, roll_no, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?, ?)', [
        $role, $role === 'student' ? strtoupper($o['roll']) : null, $o['first'], $o['last'], $o['email'],
        password_hash($password, PASSWORD_DEFAULT),
    ]);
} catch (PDOException $e) {
    fwrite(STDERR, "Could not create the account (is the e-mail or roll number already used?)\n");
    exit(1);
}
$id = (int) db()->lastInsertId();
echo "Created $role account #$id for {$o['email']}\n";

if ($role === 'faculty' && !empty($o['subjects'])) {
    foreach (array_filter(array_map('trim', explode(',', $o['subjects']))) as $code) {
        $n = q('UPDATE subjects SET faculty_id = ? WHERE code = ?', [$id, $code])->rowCount();
        echo $n ? "  teaches $code\n" : "  no subject with code '$code' (add it to the subjects table first)\n";
    }
}
