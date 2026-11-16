// Conversation page: loads new messages every 3 seconds and sends new ones.
// Messages are added with textContent, so any HTML inside them is shown as text, never run.
(function () {
  var area = document.querySelector('.chat-area');
  if (!area) return;
  var api = area.dataset.api, other = area.dataset.with;
  var csrf = document.body.dataset.csrf;
  var box = area.querySelector('.chat-box');
  var form = area.querySelector('.typing-area');
  var lastId = 0, loaded = false;

  function bubble(m) {
    var div = document.createElement('div');
    div.className = 'msg' + (m.mine ? ' mine' : '');
    if (m.title) { var b = document.createElement('b'); b.textContent = m.title; div.appendChild(b); }
    var p = document.createElement('p'); p.textContent = m.body; div.appendChild(p);
    var s = document.createElement('small'); s.textContent = m.time; div.appendChild(s);
    return div;
  }

  function load() {
    fetch(api + '?with=' + encodeURIComponent(other) + '&after=' + lastId, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.messages) return;
        if (!loaded) { box.textContent = ''; loaded = true; }
        if (!data.messages.length && !box.children.length) {
          var t = document.createElement('p'); t.className = 'text';
          t.textContent = 'No messages yet. Your message will appear here.';
          box.appendChild(t);
        }
        var nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 80;
        data.messages.forEach(function (m) {
          var empty = box.querySelector('.text'); if (empty) empty.remove();
          box.appendChild(bubble(m));
          lastId = Math.max(lastId, m.id);
        });
        if (data.messages.length && (nearBottom || data.messages.some(function (m) { return m.mine; }))) {
          box.scrollTop = box.scrollHeight;
        }
      })
      .catch(function () { /* try again on the next tick */ });
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var body = form.body.value.trim();
    if (!body) return;
    var fd = new FormData(form);
    fd.append('with', other);
    fetch(api, { method: 'POST', body: fd, credentials: 'same-origin', headers: { 'X-CSRF-Token': csrf } })
      .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
      .then(function (res) {
        var err = form.querySelector('.error'); if (err) err.remove();
        if (!res.ok) {
          var p = document.createElement('p'); p.className = 'error'; p.textContent = res.j.error || 'Could not send.';
          form.appendChild(p); return;
        }
        form.body.value = ''; form.title.value = '';
        load();
      });
  });
  form.body.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit(); }
  });

  load();
  setInterval(load, 3000);
})();
