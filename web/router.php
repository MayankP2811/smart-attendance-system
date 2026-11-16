<?php
// Router for PHP's built-in server (php -S), used for local development:
//   php -S 127.0.0.1:8000 -t web web/router.php
// It applies the same rules as .htaccess does on Apache.
$path = rawurldecode(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH) ?? '/');
if (preg_match('#^/(includes|cli)(/|$)#', $path) || preg_match('#^/uploads/.*\.(php\d?|phtml|phar)$#i', $path)
    || preg_match('#/\.#', $path) || $path === '/router.php') {
    http_response_code(404);
    exit('Not found');
}
return false; // let the built-in server handle the file
