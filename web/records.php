<?php
// Faculty: every student's attendance in one subject.
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('faculty');

$all = q('SELECT * FROM subjects ORDER BY id')->fetchAll();
$mine = array_values(array_filter($all, fn ($s) => (int) $s['faculty_id'] === (int) $user['id']));
$code = (string) ($_GET['subject'] ?? ($mine[0]['code'] ?? ($all[0]['code'] ?? '')));
$subject = subject_by_code($code);
$rows = $subject ? class_summary((int) $subject['id']) : [];

page_start('Attendance record', $user, 'records.php');
?>
<h1>Attendance List</h1>
<form class="toolbar" method="get">
  <label for="subject">Subject</label>
  <select id="subject" name="subject" class="autosubmit">
    <?php foreach ($all as $s): ?>
      <option value="<?= e($s['code']) ?>" <?= $subject && $s['id'] === $subject['id'] ? 'selected' : '' ?>>
        <?= e($s['name']) ?><?= (int) $s['faculty_id'] === (int) $user['id'] ? ' (yours)' : '' ?></option>
    <?php endforeach; ?>
  </select>
  <noscript><button type="submit">Show</button></noscript>
  <?php if ($subject): ?>
    <a class="btn-small" href="<?= e(url('export.php?subject=' . urlencode($subject['code']))) ?>">
      <span class="material-icons-sharp">download</span> Download CSV (Excel)</a>
  <?php endif; ?>
</form>

<div class="table-card">
  <?php if (!$subject): ?><p class="muted">No subjects yet.</p><?php else: ?>
  <p class="muted"><?= lecture_count((int) $subject['id']) ?> lectures recorded. Below 75% is highlighted. <b>Left early</b> = seen by the camera at the start but not in enough photos, so marked absent.</p>
  <table>
    <thead><tr><th>Roll No</th><th>Name</th><th>Dept.</th><th>Present</th><th title="Seen in some photos, but not enough to count as present">Left early</th><th>Leave</th><th>Attendance</th><th>Details</th></tr></thead>
    <tbody>
    <?php foreach ($rows as $r): ?>
      <tr>
        <td><?= e($r['roll_no'] ?? '–') ?></td>
        <td><?= e(full_name($r)) ?></td>
        <td><?= e($r['department']) ?></td>
        <td><?= $r['present'] ?> / <?= $r['held'] ?></td>
        <td><?= $r['left_early'] ?></td>
        <td><?= $r['on_leave'] ?></td>
        <td class="<?= $r['percent'] !== null && $r['percent'] < 75 ? 'warning' : 'success' ?>"><?= e(pct_label($r['percent'])) ?></td>
        <td class="primary"><a href="<?= e(url('student_record.php?student=' . (int) $r['id'] . '&subject=' . urlencode($subject['code']))) ?>">View</a></td>
      </tr>
    <?php endforeach; ?>
    </tbody>
  </table>
  <?php endif; ?>
</div>
<?php page_end($user, ['js/app.js']);
