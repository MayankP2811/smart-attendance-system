<?php
require __DIR__ . '/includes/bootstrap.php';

if ($u = current_user()) {
    redirect(home_for($u));
}

$error = '';
$email = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_with_csrf();
    $email = trim((string) ($_POST['email'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');
    $role = ($_POST['role'] ?? '') === 'faculty' ? 'faculty' : 'student';
    $user = q('SELECT * FROM users WHERE email = ? AND role = ?', [$email, $role])->fetch();
    if ($email === '' || $password === '') {
        $error = 'Please enter your e-mail and password.';
    } elseif (!$user || !verify_password($user, $password)) {
        $error = 'E-mail, password or role is not correct.';   // same message: don't reveal which
    } else {
        log_in($user);
        redirect(home_for($user));
    }
}
$role = $_POST['role'] ?? 'student';
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Login · Smart Attendance</title>
  <link rel="icon" href="<?= e(asset('img/logo.svg')) ?>" type="image/svg+xml">
  <link rel="stylesheet" href="<?= e(asset('css/fonts.css')) ?>">
  <link rel="stylesheet" href="<?= e(asset('css/login.css')) ?>">
</head>
<body>
  <img class="wave" src="<?= e(asset('img/wave.svg')) ?>" alt="">
  <div class="container">
    <div class="img"><img src="<?= e(asset('img/login-illustration.svg')) ?>" alt="Camera recognising students in a classroom"></div>
    <section class="login-content">
      <form method="post" autocomplete="off" novalidate>
        <?= csrf_field() ?>
        <img class="avatar" src="<?= e(asset('img/avatar.svg')) ?>" alt="">
        <h2 class="title">Login</h2>
        <p class="sub">Smart Attendance System</p>
        <?php if ($error): ?><div class="error-text"><?= e($error) ?></div><?php endif; ?>
        <?php if (isset($_GET['registered'])): ?><div class="ok-text">Account created. Please log in.</div><?php endif; ?>
        <label for="email">Email Address</label>
        <input id="email" type="email" name="email" value="<?= e($email) ?>" placeholder="Enter your email" required>
        <label for="password">Password</label>
        <div class="pw"><input id="password" type="password" name="password" placeholder="Enter your password" required>
          <button type="button" class="show-pw" aria-label="Show password">show</button></div>
        <label for="role">Choose the Role</label>
        <select id="role" name="role">
          <option value="student" <?= $role === 'student' ? 'selected' : '' ?>>Student</option>
          <option value="faculty" <?= $role === 'faculty' ? 'selected' : '' ?>>Faculty</option>
        </select>
        <button type="submit" class="btn">Login</button>
        <p class="link">New student? <a href="<?= e(url('signup.php')) ?>">Create an account</a></p>
      </form>
    </section>
  </div>
  <script src="<?= e(asset('js/password.js')) ?>"></script>
</body>
</html>
