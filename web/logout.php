<?php
// Logging out needs a POST with the CSRF token, and always logs out the
// current session's own user.
require __DIR__ . '/includes/bootstrap.php';

require_post_with_csrf();
log_out();
redirect('login.php');
