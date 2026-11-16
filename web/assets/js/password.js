// "show / hide" button next to password fields.
document.querySelectorAll('.show-pw').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var input = btn.parentElement.querySelector('input');
    var show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    btn.textContent = show ? 'hide' : 'show';
  });
});
