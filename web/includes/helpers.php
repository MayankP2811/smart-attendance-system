<?php
declare(strict_types=1);

/** Escape text for HTML. Use for every value that comes from the database or the user. */
function e(mixed $value): string
{
    return htmlspecialchars((string) ($value ?? ''), ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

/** Path of the web root relative to the server root, e.g. '' or '/smart-attendance/web'. */
function base_path(): string
{
    static $base = null;
    if ($base === null) {
        $webRoot = str_replace('\\', '/', realpath(dirname(__DIR__)) ?: dirname(__DIR__));
        $docRoot = str_replace('\\', '/', realpath($_SERVER['DOCUMENT_ROOT'] ?? '') ?: '');
        $base = ($docRoot !== '' && str_starts_with($webRoot, $docRoot)) ? substr($webRoot, strlen($docRoot)) : '';
        $base = rtrim($base, '/');
    }
    return $base;
}

function url(string $path = ''): string
{
    return base_path() . '/' . ltrim($path, '/');
}

function redirect(string $path): never
{
    header('Location: ' . url($path));
    exit;
}

function asset(string $path): string
{
    return url('assets/' . ltrim($path, '/'));
}

function photo_url(?string $photo): string
{
    if ($photo && preg_match('/^[A-Za-z0-9._-]+$/', $photo) && is_file(dirname(__DIR__) . '/uploads/' . $photo)) {
        return url('uploads/' . $photo);
    }
    return asset('img/avatar.svg');
}

function full_name(array $u): string
{
    return trim(($u['first_name'] ?? '') . ' ' . ($u['last_name'] ?? ''));
}

function flash(?string $message = null, string $type = 'ok'): ?array
{
    if ($message !== null) {
        $_SESSION['flash'] = ['msg' => $message, 'type' => $type];
        return null;
    }
    $f = $_SESSION['flash'] ?? null;
    unset($_SESSION['flash']);
    return $f;
}

function fmt_date(string $dt, string $format = 'd M Y, H:i'): string
{
    return (new DateTime($dt))->format($format);
}

function json_out(mixed $data, int $status = 200): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}
