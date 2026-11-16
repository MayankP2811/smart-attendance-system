<?php
// Student registration. Faculty accounts are created by the admin:
//   php web/cli/create_user.php --role=faculty ...
require __DIR__ . '/includes/bootstrap.php';

if ($u = current_user()) {
    redirect(home_for($u));
}

const MAX_PHOTO_BYTES = 2 * 1024 * 1024;

/** Save an uploaded profile photo. Returns [filename|null, error|null]. */
function save_photo(array $file): array
{
    if (($file['error'] ?? UPLOAD_ERR_NO_FILE) === UPLOAD_ERR_NO_FILE) {
        return [null, null]; // a photo is optional
    }
    if ($file['error'] !== UPLOAD_ERR_OK || $file['size'] > MAX_PHOTO_BYTES) {
        return [null, 'The photo must be a JPG or PNG under 2 MB.'];
    }
    // Check the real file content, not the name or the type the browser claims.
    $info = @getimagesize($file['tmp_name']);
    $types = [IMAGETYPE_JPEG => 'jpg', IMAGETYPE_PNG => 'png'];
    if (!$info || !isset($types[$info[2]])) {
        return [null, 'The photo must be a JPG or PNG under 2 MB.'];
    }
    $name = bin2hex(random_bytes(12)) . '.' . $types[$info[2]];
    if (!move_uploaded_file($file['tmp_name'], __DIR__ . '/uploads/' . $name)) {
        return [null, 'Could not save the photo. Try again.'];
    }
    return [$name, null];
}

$errors = [];
$v = ['first_name' => '', 'last_name' => '', 'email' => '', 'roll_no' => ''];
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    require_post_with_csrf();
    foreach ($v as $k => $_) {
        $v[$k] = trim((string) ($_POST[$k] ?? ''));
    }
    $v['roll_no'] = strtoupper($v['roll_no']);
    $password = (string) ($_POST['password'] ?? '');
    if ($v['first_name'] === '' || $v['last_name'] === '') {
        $errors[] = 'Please enter your first and last name.';
    }
    if (!filter_var($v['email'], FILTER_VALIDATE_EMAIL)) {
        $errors[] = 'Please enter a valid e-mail address.';
    }
    if (!preg_match('/^[A-Z0-9-]{1,20}$/', $v['roll_no'])) {
        $errors[] = 'Roll number: letters, digits and "-" only (for example TE01).';
    }
    if (strlen($password) < 8) {
        $errors[] = 'The password needs at least 8 characters.';
    }
    if (!$errors) {
        if (q('SELECT 1 FROM users WHERE email = ?', [$v['email']])->fetch()) {
            $errors[] = 'An account with this e-mail already exists.';
        }
        if (q('SELECT 1 FROM users WHERE roll_no = ?', [$v['roll_no']])->fetch()) {
            $errors[] = 'This roll number is already registered. Ask your class in-charge if this is wrong.';
        }
    }
    if (!$errors) {
        [$photo, $err] = save_photo($_FILES['photo'] ?? []);
        if ($err) {
            $errors[] = $err;
        } else {
            q(
                "INSERT INTO users (role, roll_no, first_name, last_name, email, password_hash, photo)
                 VALUES ('student', ?, ?, ?, ?, ?, ?)",
                [$v['roll_no'], $v['first_name'], $v['last_name'], $v['email'], password_hash($password, PASSWORD_DEFAULT), $photo]
            );
            redirect('login.php?registered=1');
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Student registration · Smart Attendance</title>
  <link rel="icon" href="<?= e(asset('img/logo.svg')) ?>" type="image/svg+xml">
  <link rel="stylesheet" href="<?= e(asset('css/fonts.css')) ?>">
  <link rel="stylesheet" href="<?= e(asset('css/login.css')) ?>">
</head>
<body>
  <img class="wave" src="<?= e(asset('img/wave.svg')) ?>" alt="">
  <div class="container">
    <div class="img"><img src="<?= e(asset('img/login-illustration.svg')) ?>" alt=""></div>
    <section class="login-content">
      <form method="post" enctype="multipart/form-data" autocomplete="off" novalidate class="signup">
        <?= csrf_field() ?>
        <h2 class="title">Registration</h2>
        <p class="sub">Students only · faculty accounts are created by the admin</p>
        <?php foreach ($errors as $err): ?><div class="error-text"><?= e($err) ?></div><?php endforeach; ?>
        <div class="two">
          <div><label for="fn">First Name</label><input id="fn" name="first_name" value="<?= e($v['first_name']) ?>" required></div>
          <div><label for="ln">Last Name</label><input id="ln" name="last_name" value="<?= e($v['last_name']) ?>" required></div>
        </div>
        <label for="roll">Roll Number</label>
        <input id="roll" name="roll_no" value="<?= e($v['roll_no']) ?>" placeholder="e.g. TE11" required>
        <label for="email">Email Address</label>
        <input id="email" type="email" name="email" value="<?= e($v['email']) ?>" placeholder="Enter your email" required>
        <label for="password">Password</label>
        <div class="pw"><input id="password" type="password" name="password" placeholder="At least 8 characters" required>
          <button type="button" class="show-pw" aria-label="Show password">show</button></div>
        <label for="photo">Profile photo (optional, JPG/PNG)</label>
        <input id="photo" type="file" name="photo" accept="image/jpeg,image/png">
        <button type="submit" class="btn">Sign up</button>
        <p class="link">Already registered? <a href="<?= e(url('login.php')) ?>">Login now</a></p>
      </form>
    </section>
  </div>
  <script src="<?= e(asset('js/password.js')) ?>"></script>
</body>
</html>
