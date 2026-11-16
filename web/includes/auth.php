<?php
// Sessions, login, roles and CSRF protection.
declare(strict_types=1);

function start_session(): void
{
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    session_name('sas_session');
    session_set_cookie_params([
        'lifetime' => 0,
        'path' => base_path() . '/',
        'httponly' => true,
        'samesite' => 'Lax',
        'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off'),
    ]);
    session_start();
}

function current_user(): ?array
{
    static $user = false;
    if ($user !== false) {
        return $user;
    }
    $id = $_SESSION['user_id'] ?? null;
    $user = $id ? (q('SELECT * FROM users WHERE id = ?', [$id])->fetch() ?: null) : null;
    return $user;
}

function require_login(): array
{
    $user = current_user();
    if (!$user) {
        redirect('login.php');
    }
    return $user;
}

/** Stop with 403 unless the logged-in user has this role. */
function require_role(string $role): array
{
    $user = require_login();
    if ($user['role'] !== $role) {
        http_response_code(403);
        $home = home_for($user);
        exit('<!DOCTYPE html><meta charset="utf-8"><title>Not allowed</title>'
            . '<p style="font-family:sans-serif;padding:2rem">This page is only for ' . e($role)
            . ' accounts. <a href="' . e(url($home)) . '">Back to your dashboard</a></p>');
    }
    return $user;
}

function home_for(array $user): string
{
    return $user['role'] === 'faculty' ? 'faculty.php' : 'student.php';
}

/** Check a password against its bcrypt hash (re-hashed if PHP's default algorithm changes). */
function verify_password(array $user, string $password): bool
{
    $hash = (string) $user['password_hash'];
    if (!password_verify($password, $hash)) {
        return false;
    }
    if (password_needs_rehash($hash, PASSWORD_DEFAULT)) {
        q('UPDATE users SET password_hash = ? WHERE id = ?', [password_hash($password, PASSWORD_DEFAULT), $user['id']]);
    }
    return true;
}

function log_in(array $user): void
{
    session_regenerate_id(true);
    $_SESSION['user_id'] = (int) $user['id'];
    q('UPDATE users SET is_online = 1 WHERE id = ?', [$user['id']]);
}

function log_out(): void
{
    if ($u = current_user()) {
        q('UPDATE users SET is_online = 0 WHERE id = ?', [$u['id']]);
    }
    $_SESSION = [];
    session_destroy();
}

function csrf_token(): string
{
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrf_field(): string
{
    return '<input type="hidden" name="csrf" value="' . e(csrf_token()) . '">';
}

/** Every POST must carry the session's token (form field or X-CSRF-Token header). */
function require_post_with_csrf(): void
{
    if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
        http_response_code(405);
        exit('Method not allowed');
    }
    $sent = $_POST['csrf'] ?? ($_SERVER['HTTP_X_CSRF_TOKEN'] ?? '');
    if (!is_string($sent) || empty($_SESSION['csrf']) || !hash_equals($_SESSION['csrf'], $sent)) {
        http_response_code(400);
        exit('Your session expired. Go back, reload the page and try again.');
    }
}
