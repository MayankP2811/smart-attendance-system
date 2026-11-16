<?php
// Shared page frame: left sidebar, main area and the top-right profile strip.
declare(strict_types=1);

function nav_items(array $user): array
{
    if ($user['role'] === 'faculty') {
        return [
            ['faculty.php', 'grid_view', 'Dashboard'],
            ['records.php', 'people', 'Attendance Record'],
            ['announce.php', 'campaign', 'Announcements'],
            ['leave.php', 'contact_mail', 'Leave Requests'],
        ];
    }
    return [
        ['student.php', 'grid_view', 'Dashboard'],
        ['analytics.php', 'bar_chart', 'Analytics'],
        ['leave.php', 'contact_mail', 'Leave Application'],
        ['alerts.php', 'notifications', 'Alerts'],
    ];
}

function page_start(string $title, array $user, string $active, array $extraCss = []): void
{
    $role = $user['role'] === 'faculty' ? 'Faculty' : 'Student';
    ?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><?= e($title) ?> · Smart Attendance</title>
  <link rel="icon" href="<?= e(asset('img/logo.svg')) ?>" type="image/svg+xml">
  <link rel="stylesheet" href="<?= e(asset('css/fonts.css')) ?>">
  <link rel="stylesheet" href="<?= e(asset('css/app.css')) ?>">
  <?php foreach ($extraCss as $css): ?><link rel="stylesheet" href="<?= e(asset($css)) ?>"><?php endforeach; ?>
</head>
<body data-csrf="<?= e(csrf_token()) ?>">
<div class="container">
  <aside>
    <div class="brand">
      <img src="<?= e(photo_url($user['photo'])) ?>" alt="">
      <div><h2><?= e($user['first_name']) ?></h2><small><?= e($role) ?></small></div>
    </div>
    <nav class="sidebar">
      <?php foreach (nav_items($user) as [$href, $icon, $label]): ?>
        <a href="<?= e(url($href)) ?>" class="<?= $href === $active ? 'active' : '' ?>">
          <span class="material-icons-sharp" aria-hidden="true"><?= e($icon) ?></span><h3><?= e($label) ?></h3>
        </a>
      <?php endforeach; ?>
      <form method="post" action="<?= e(url('logout.php')) ?>" class="logout">
        <?= csrf_field() ?>
        <button type="submit"><span class="material-icons-sharp" aria-hidden="true">logout</span><h3>Logout</h3></button>
      </form>
    </nav>
  </aside>
  <main>
    <?php if ($f = flash()): ?><div class="flash <?= e($f['type']) ?>"><?= e($f['msg']) ?></div><?php endif; ?>
    <?php
}

function page_end(array $user, array $scripts = []): void
{
    $bell = $user['role'] === 'faculty' ? ['announce.php', 'campaign'] : ['alerts.php', 'notifications'];
    ?>
  </main>
  <div class="right">
    <div class="top">
      <a href="<?= e(url($bell[0])) ?>" class="bell" title="<?= $user['role'] === 'faculty' ? 'Announcements' : 'Alerts' ?>">
        <span class="material-icons-sharp"><?= e($bell[1]) ?></span></a>
      <h2><?= e(full_name($user)) ?></h2>
      <img class="avatar" src="<?= e(photo_url($user['photo'])) ?>" alt="">
    </div>
  </div>
</div>
<?php foreach ($scripts as $js): ?><script src="<?= e(asset($js)) ?>"></script><?php endforeach; ?>
</body>
</html>
    <?php
}

/** The round progress ring used on dashboard cards. */
function ring(?float $percent, string $class = ''): string
{
    $p = $percent ?? 0;
    $circ = 226.2; // 2 * pi * r (r = 36)
    $offset = $circ - ($circ * max(0, min(100, $p)) / 100);
    return '<div class="progress ' . e($class) . '"><svg viewBox="0 0 92 92"><circle class="track" cx="46" cy="46" r="36"></circle>'
        . '<circle class="bar" cx="46" cy="46" r="36" style="stroke-dashoffset:' . round($offset, 1) . '"></circle></svg>'
        . '<div class="number"><p>' . e(pct_label($percent)) . '</p></div></div>';
}
