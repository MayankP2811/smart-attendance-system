// Bar chart of attendance per subject, and the typed advice message.
(function () {
  var data = JSON.parse(document.getElementById('chart-data').textContent);
  var ctx = document.getElementById('barChart');
  if (window.Chart && ctx) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [{
          label: 'Attendance %',
          data: data.values,
          backgroundColor: data.values.map(function (v) { return v < 50 ? '#e5484d' : v < 75 ? '#f2b33d' : '#6bc733'; }),
          borderRadius: 4,
          maxBarThickness: 56
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { min: 0, max: 100, ticks: { callback: function (v) { return v + '%'; } }, grid: { color: '#ececf3' } },
          x: { grid: { display: false } }
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: {
            title: function (items) { return data.names[items[0].dataIndex]; },
            label: function (item) { return ' ' + item.parsed.y + '% attended'; }
          } }
        }
      }
    });
  }
  // Typing effect for the advice message (the text itself is already on the page).
  var box = document.getElementById('advice');
  if (box && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    var p = box.querySelector('p'), text = box.dataset.text, i = 0;
    p.textContent = '';
    var timer = setInterval(function () {
      p.textContent = text.slice(0, ++i);
      if (i >= text.length) clearInterval(timer);
    }, 18);
  }
})();
