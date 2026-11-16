// Small helpers used on several pages.
(function () {
  // Subject picker on the attendance record page: reload when changed.
  document.querySelectorAll('select.autosubmit').forEach(function (sel) {
    sel.addEventListener('change', function () { sel.form.submit(); });
  });
  // Name filter on the leave page.
  var filter = document.querySelector('.contact-filter');
  if (filter) {
    filter.addEventListener('input', function () {
      var term = filter.value.trim().toLowerCase();
      document.querySelectorAll('.contact').forEach(function (a) {
        a.style.display = a.dataset.name.indexOf(term) === -1 ? 'none' : '';
      });
    });
  }
})();
