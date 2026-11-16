<?php
// Settings come from environment variables or the repository's .env file.
// Nothing secret is written in the code.
declare(strict_types=1);

function config(string $key, ?string $default = null): ?string
{
    static $file = null;
    $env = getenv($key);
    if ($env !== false && $env !== '') {
        return $env;
    }
    if ($file === null) {
        $file = [];
        $path = getenv('APP_ENV_FILE') ?: dirname(__DIR__, 2) . '/.env';
        if (is_readable($path)) {
            foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
                $line = trim($line);
                if ($line === '' || $line[0] === '#' || !str_contains($line, '=')) {
                    continue;
                }
                [$k, $v] = array_map('trim', explode('=', $line, 2));
                if (strlen($v) >= 2 && ($v[0] === '"' || $v[0] === "'") && $v[-1] === $v[0]) {
                    $v = substr($v, 1, -1);
                }
                $file[$k] = $v;
            }
        }
    }
    return $file[$key] ?? $default;
}
