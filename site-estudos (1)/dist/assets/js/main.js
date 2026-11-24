(function () {
  'use strict';
  var b = document.body, r = document.documentElement;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function $(s, c) { return (c || document).querySelector(s); }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function shuffle(a) { a = a.slice(); for (var i = a.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = a[i]; a[i] = a[j]; a[j] = t; } return a; }
  function json(id) { var el = document.getElementById(id); if (!el) return null; try { return JSON.parse(el.textContent); } catch (e) { return null; } }

  /* ---------- acessibilidade ---------- */
  if (get('hc') === '1') b.classList.add('hc');
  var fs = parseInt(get('fs') || '17', 10); r.style.setProperty('--fs', fs + 'px');
  document.addEventListener('click', function (e) {
    var t = e.target.closest('[data-act]'); if (!t) return; var a = t.dataset.act;
    if (a === 'hc') { b.classList.toggle('hc'); set('hc', b.classList.contains('hc') ? '1' : '0'); }
    if (a === 'fp' || a === 'fm') { fs = Math.max(14, Math.min(24, fs + (a === 'fp' ? 1 : -1))); r.style.setProperty('--fs', fs + 'px'); set('fs', fs); }
    if (a === 'menu') { var n = document.getElementById('nav'); var o = n.classList.toggle('open'); t.setAttribute('aria-expanded', o); }
  });

  /* ---------- data da prova ---------- */
  document.querySelectorAll('[data-date]').forEach(function (el) {
    var p = el.dataset.date.split('-'); var d = new Date(+p[0], +p[1] - 1, +p[2]);
    var h = new Date(); h = new Date(h.getFullYear(), h.getMonth(), h.getDate());
    var diff = Math.round((d - h) / 86400000);
    var txt = diff === 0 ? 'Hoje' : diff === 1 ? 'Amanhã' : diff === -1 ? 'Ontem' : (('0' + p[2]).slice(-2) + '/' + ('0' + p[1]).slice(-2));
    el.textContent = txt;
  });

  /* ---------- quiz ---------- */
  function Quiz(root, perguntas, key) {
    var i = 0, acertos = 0, erradas = [], lista = perguntas.slice();
    function start(qs) { lista = qs; i = 0; acertos = 0; erradas = []; show(); }
    function show() {
      if (i >= lista.length) return fim();
      var q = lista[i];
      var ops = shuffle(q.o.map(function (t, k) { return { t: t, c: k === q.c }; }));
      root.innerHTML =
        '<div class="q-top"><span>Questão ' + (i + 1) + ' de ' + lista.length + '</span><span>Acertos: ' + acertos + '</span></div>' +
        '<div class="q-bar"><i style="width:' + (i / lista.length * 100) + '%"></i></div>' +
        '<p class="q-q">' + esc(q.q) + '</p><div class="q-opts" role="group" aria-label="Alternativas"></div><div class="q-exp"></div><div class="q-act"></div>';
      var box = $('.q-opts', root);
      ops.forEach(function (o) {
        var bt = document.createElement('button'); bt.type = 'button'; bt.className = 'q-opt'; bt.textContent = o.t;
        bt.addEventListener('click', function () {
          var bs = box.querySelectorAll('button');
          bs.forEach(function (x, k) { x.disabled = true; if (ops[k].c) x.classList.add('ok'); });
          if (o.c) { acertos++; } else { bt.classList.add('no'); erradas.push(q); }
          $('.q-exp', root).innerHTML = '<div class="alert ' + (o.c ? 'i' : '') + '"><strong>' + (o.c ? 'Certo!' : 'Não foi dessa vez.') + '</strong> ' + esc(q.e) + '</div>';
          var nx = document.createElement('button'); nx.type = 'button'; nx.className = 'btn b';
          nx.textContent = i + 1 === lista.length ? 'Ver resultado' : 'Próxima'; nx.addEventListener('click', function () { i++; show(); });
          $('.q-act', root).appendChild(nx); nx.focus();
        });
        box.appendChild(bt);
      });
    }
    function fim() {
      var pct = Math.round(acertos / lista.length * 100);
      var best = parseInt(get('best:' + key) || '0', 10); if (pct > best) { best = pct; set('best:' + key, best); }
      var msg = pct === 100 ? 'Perfeito! Você está pronto(a).' : pct >= 70 ? 'Muito bem! Falta pouco.' : pct >= 50 ? 'Está no caminho. Reveja o resumo e tente de novo.' : 'Leia o resumo com calma e tente outra vez.';
      root.innerHTML = '<div class="q-top"><span>Resultado</span><span>Melhor: ' + best + '%</span></div><div class="q-bar"><i style="width:100%"></i></div>' +
        '<div class="q-score">' + acertos + ' / ' + lista.length + '</div><p>' + msg + '</p><div class="q-act"></div>';
      var act = $('.q-act', root);
      function add(t, cls, fn) { var x = document.createElement('button'); x.type = 'button'; x.className = 'btn ' + cls; x.textContent = t; x.addEventListener('click', fn); act.appendChild(x); }
      if (erradas.length) add('Refazer só as que errei (' + erradas.length + ')', 'b', function () { start(shuffle(erradas)); });
      add('Recomeçar', 'ghost', function () { start(shuffle(perguntas)); });
    }
    start(shuffle(perguntas));
  }
  var qr = $('#quiz');
  if (qr) {
    var data = json('quiz-data') || [];
    var n = parseInt(qr.dataset.n || '0', 10);
    var qs = n && n < data.length ? shuffle(data).slice(0, n) : data;
    Quiz(qr, qs, qr.dataset.key || 'quiz');
    var redo = $('#quiz-new'); if (redo) redo.addEventListener('click', function () { Quiz(qr, n ? shuffle(data).slice(0, n) : data, qr.dataset.key); });
  }

  /* ---------- cartas ---------- */
  var dk = $('#deck');
  if (dk) {
    var cards = json('deck-data') || [], idx = 0, order = cards.slice();
    function draw() {
      var c = order[idx];
      dk.innerHTML = '<div class="dk-top"><span>Carta ' + (idx + 1) + ' de ' + order.length + '</span><span>Clique na carta para virar</span></div>' +
        '<button type="button" class="flip" aria-label="Virar a carta"><div class="flip-in"><div class="face front"><small>' + esc(c.t || 'Pergunta') + '</small><b>' + esc(c.f) + '</b></div><div class="face back"><small>Resposta</small><p>' + esc(c.v) + '</p></div></div></button>' +
        '<div class="dk-act"><button class="btn ghost" data-d="prev" type="button">Anterior</button><button class="btn b" data-d="flip" type="button">Virar</button><button class="btn ghost" data-d="next" type="button">Próxima</button><button class="btn ghost" data-d="mix" type="button">Embaralhar</button></div>';
    }
    dk.addEventListener('click', function (e) {
      var t = e.target.closest('.flip,[data-d]'); if (!t) return;
      var d = t.dataset.d;
      if (!d || d === 'flip') { $('.flip', dk).classList.toggle('on'); return; }
      if (d === 'next') idx = (idx + 1) % order.length;
      if (d === 'prev') idx = (idx - 1 + order.length) % order.length;
      if (d === 'mix') { order = shuffle(order); idx = 0; }
      draw();
    });
    if (cards.length) draw();
  }

  /* ---------- chat com IA ---------- */
  var ch = $('#chat');
  if (ch) {
    var log = $('.chat-log', ch), form = $('form', ch), inp = $('input', ch), hist = [];
    function bubble(t, who) { var d = document.createElement('div'); d.className = 'msg ' + who; d.textContent = t; log.appendChild(d); log.scrollTop = log.scrollHeight; return d; }
    bubble('Oi! Pergunte o que quiser sobre Expressionismo, Renascimento, Commedia dell\'Arte e Mímica.', 'a');
    function send(text) {
      text = (text || '').trim(); if (!text) return;
      bubble(text, 'u'); hist.push({ role: 'user', content: text }); inp.value = '';
      var w = bubble('Pensando...', 'a'); var btn = $('button', form); btn.disabled = true;
      fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ materia: 'artes', mensagens: hist }) })
        .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.erro || 'Erro'); return d; }); })
        .then(function (d) { w.textContent = d.resposta.replace(/\*\*/g, '').replace(/^#+\s*/gm, ''); hist.push({ role: 'assistant', content: d.resposta }); })
        .catch(function (e) { w.textContent = e.message || 'Não consegui falar com a IA agora.'; hist.pop(); })
        .then(function () { btn.disabled = false; log.scrollTop = log.scrollHeight; inp.focus(); });
    }
    form.addEventListener('submit', function (e) { e.preventDefault(); send(inp.value); });
    document.querySelectorAll('.sugs button').forEach(function (s) { s.addEventListener('click', function () { send(s.textContent); }); });
  }

  /* ---------- busca ---------- */
  var sr = $('#sres');
  if (sr && window.SITE_INDEX) {
    var q = (new URLSearchParams(location.search).get('q') || '').trim();
    var bi = $('#bq'); if (bi) bi.value = q;
    var nm = function (s) { return s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase(); };
    var qq = nm(q).split(/\s+/).filter(Boolean);
    var hits = window.SITE_INDEX.filter(function (p) { var h = nm(p.t + ' ' + p.d); return qq.every(function (w) { return h.indexOf(w) > -1; }); });
    var c = $('#scount');
    c.textContent = !q ? 'Digite algo para pesquisar nas páginas do site.' : hits.length ? hits.length + ' resultado(s) para "' + q + '".' : 'Nenhum resultado para "' + q + '". Tente outra palavra.';
    if (q) hits.forEach(function (p) { var li = document.createElement('li'); var a = document.createElement('a'); a.href = p.u; a.textContent = p.t; var d = document.createElement('div'); d.textContent = p.d; li.appendChild(a); li.appendChild(d); sr.appendChild(li); });
  }
})();
