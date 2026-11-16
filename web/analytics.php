<?php
require __DIR__ . '/includes/bootstrap.php';
$user = require_role('student');

$subjects = student_subjects((int) $user['id']);
$avg = overall_percent($subjects);
[$level, $advice] = attendance_advice($avg);
$chart = [
    'labels' => array_map(fn ($s) => strtoupper($s['code']), $subjects),
    'values' => array_map(fn ($s) => $s['percent'] ?? 0, $subjects),
    'names' => array_column($subjects, 'name'),
];

page_start('Analytics', $user, 'analytics.php');
?>
<h1>Analytics</h1>
<div class="analytics">
  <div class="table-card chart-card">
    <h2>Attendance by subject</h2>
    <canvas id="barChart" height="300" aria-label="Bar chart of attendance percentage per subject" role="img"></canvas>
    <script type="application/json" id="chart-data"><?= json_encode($chart, JSON_HEX_TAG | JSON_HEX_AMP) ?></script>
    <details class="table-view"><summary>Show as table</summary>
      <table><thead><tr><th>Subject</th><th>Attended</th><th>Attendance</th></tr></thead><tbody>
      <?php foreach ($subjects as $s): ?>
        <tr><td><?= e($s['name']) ?></td><td><?= $s['present'] ?> / <?= $s['held'] ?></td><td><?= e(pct_label($s['percent'])) ?></td></tr>
      <?php endforeach; ?>
      </tbody></table>
    </details>
  </div>
  <div class="advice <?= e($level) ?>" id="advice" data-text="<?= e($advice) ?>">
    <span class="material-icons-sharp"><?= $level === 'good' ? 'verified' : ($level === 'info' ? 'info' : 'warning') ?></span>
    <p><?= e($advice) ?></p>
  </div>
</div>
<?php page_end($user, ['vendor/chart.umd.min.js', 'js/analytics.js']);
