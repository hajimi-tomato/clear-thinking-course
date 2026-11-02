(() => {
  'use strict';
  const memory = {};
  const storage = {
    get(key, fallback = null) { try { const value = localStorage.getItem(key); return value === null ? fallback : JSON.parse(value); } catch { return key in memory ? memory[key] : fallback; } },
    set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch { memory[key] = value; } }
  };
  const dayId = document.body.dataset.day || '01';
  const prefix = `course-day-${dayId}-`;
  const total = document.querySelectorAll('.quiz,.short-task,.case').length || 9;
  const completed = new Set(storage.get(prefix + 'interactions', []));
  const progressText = document.querySelector('#progress-text');
  const progressFill = document.querySelector('#progress-fill');
  function updateProgress() {
    if (progressText) progressText.textContent = `${completed.size} / ${total}`;
    if (progressFill) progressFill.style.width = `${Math.min(100, completed.size / total * 100)}%`;
  }
  function markDone(key) { completed.add(key); storage.set(prefix + 'interactions', [...completed]); updateProgress(); }
  updateProgress();

  const terms = Object.assign({
    '主张': ['说话者希望你接受的判断或行动要求。', '例：“你应该现在辞职。”这里的“应该辞职”就是主张。'],
    '理由': ['说话者用来支持主张的信息、经验或判断。', '例：“公司可能裁员”是支持“应该辞职”的一个理由，但还需要进一步判断。'],
    '隐含前提': ['没有被说出，却必须依靠它才能从理由走到结论的条件。', '例：“没秒回＝不重视”依赖“重视就一定秒回”。找到它，不等于已经证明它错。'],
    '论证': ['用理由支持一个主张的过程。', '例：“因为下周有重要交付，所以今天先完成测试。”'],
    '限定词': ['说明一个结论适用范围有多大的词。', '例：“所有人”“通常”“在这个项目中”。范围越大，越需要充分证据。'],
    '反例': ['与一个一般判断不一致的真实例子。', '例：一个认真工作却未升职的人，可以推翻“认真工作的人一定升职”。']
  }, window.courseTerms || {});
  const popover = document.querySelector('#term-popover');
  if (popover) {
    const title = popover.querySelector('#term-title');
    const definition = popover.querySelector('#term-definition');
    const example = popover.querySelector('#term-example');
    let trigger = null;
    let suppressFocus = false;
    let closeTimer;
    function placePopover(el) {
      const box = el.getBoundingClientRect();
      const width = popover.offsetWidth;
      const height = popover.offsetHeight;
      const left = Math.max(12, Math.min(box.left, window.innerWidth - width - 12));
      const below = box.bottom + height + 12 < window.innerHeight;
      const top = below ? box.bottom + 8 : Math.max(8, box.top - height - 8);
      popover.style.left = `${left}px`;
      popover.style.top = `${top}px`;
    }
    function open(el) {
      clearTimeout(closeTimer);
      const info = terms[el.dataset.term];
      if (!info) return;
      if (trigger && trigger !== el) trigger.setAttribute('aria-expanded', 'false');
      trigger = el;
      title.textContent = el.dataset.term;
      definition.textContent = info[0];
      example.textContent = info[1];
      popover.hidden = false;
      el.setAttribute('aria-expanded', 'true');
      el.setAttribute('aria-describedby', 'term-popover');
      placePopover(el);
    }
    function close() {
      clearTimeout(closeTimer);
      popover.hidden = true;
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
      trigger = null;
    }
    function delayedClose() { clearTimeout(closeTimer); closeTimer = setTimeout(close, 180); }
    document.querySelectorAll('.term').forEach(el => {
      el.setAttribute('aria-haspopup', 'true');
      el.setAttribute('aria-expanded', 'false');
      el.addEventListener('pointerenter', () => open(el));
      el.addEventListener('pointerleave', delayedClose);
      el.addEventListener('focus', () => { if (!suppressFocus) open(el); });
      el.addEventListener('blur', delayedClose);
      el.addEventListener('click', event => { event.preventDefault(); open(el); });
    });
    popover.addEventListener('pointerenter', () => clearTimeout(closeTimer));
    popover.addEventListener('pointerleave', delayedClose);
    popover.addEventListener('focusin', () => clearTimeout(closeTimer));
    popover.querySelector('.popover-close').addEventListener('click', () => { const previous = trigger; close(); suppressFocus = true; previous?.focus(); suppressFocus = false; });
    document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
    document.addEventListener('pointerdown', event => { if (!popover.contains(event.target) && !event.target.closest('.term')) close(); });
    window.addEventListener('resize', () => { if (trigger) placePopover(trigger); });
    window.addEventListener('scroll', () => { if (trigger) placePopover(trigger); }, { passive: true });
  }

  document.querySelectorAll('.quiz').forEach(quiz => {
    const id = quiz.dataset.quiz;
    const feedback = quiz.querySelector('.quiz-feedback');
    const saved = storage.get(prefix + id, null);
    if (saved) {
      const input = quiz.querySelector(`input[value="${saved}"]`);
      if (input) input.checked = true;
      feedback.textContent = saved === quiz.dataset.answer ? feedback.dataset.correct : feedback.dataset.wrong;
      feedback.classList.toggle('wrong', saved !== quiz.dataset.answer);
    }
    quiz.querySelector('.quiz-submit').addEventListener('click', () => {
      const choice = quiz.querySelector('input:checked');
      if (!choice) { feedback.textContent = '先选择一个答案。'; feedback.classList.add('wrong'); return; }
      storage.set(prefix + id, choice.value);
      feedback.textContent = choice.value === quiz.dataset.answer ? feedback.dataset.correct : feedback.dataset.wrong;
      feedback.classList.toggle('wrong', choice.value !== quiz.dataset.answer);
      markDone(id);
    });
  });

  document.querySelectorAll('.short-task').forEach(task => {
    const key = 'task-' + task.dataset.task;
    const area = task.querySelector('textarea');
    const result = task.querySelector('.task-feedback');
    area.value = storage.get(prefix + key + '-text', '');
    area.addEventListener('input', () => storage.set(prefix + key + '-text', area.value));
    if (completed.has(key)) result.hidden = false;
    task.querySelector('.task-reveal').addEventListener('click', () => {
      if (area.value.trim().length < 20) { area.focus(); area.placeholder = '先写至少 20 个字，试着提出你的回应。'; return; }
      result.hidden = false; markDone(key);
    });
  });

  document.querySelectorAll('.case').forEach(card => {
    const key = 'case-' + card.dataset.case;
    const area = card.querySelector('textarea');
    const result = card.querySelector('.case-answer');
    area.value = storage.get(prefix + key + '-text', '');
    area.addEventListener('input', () => storage.set(prefix + key + '-text', area.value));
    if (completed.has(key)) result.hidden = false;
    card.querySelector('.case-reveal').addEventListener('click', () => {
      if (area.value.trim().length < 35) { area.focus(); area.placeholder = '请先写下至少 35 个字，包含结论、理由、前提和回应。'; return; }
      result.hidden = false; markDone(key);
    });
  });

  document.querySelectorAll('.copy-prompt').forEach(button => {
    button.addEventListener('click', async () => {
      const prompt = document.getElementById(button.dataset.target)?.textContent;
      if (!prompt) return;
      try { await navigator.clipboard.writeText(prompt); button.textContent = '已复制，可以开始对话'; }
      catch {
        const details = button.nextElementSibling;
        if (details?.tagName === 'DETAILS') details.open = true;
        button.textContent = '请从下方手动复制';
      }
      setTimeout(() => { button.textContent = '复制角色设定'; }, 3500);
    });
  });

  const roleplayDone = document.querySelector('#roleplay-done');
  if (roleplayDone) {
    roleplayDone.checked = storage.get(prefix + 'roleplay-done', false);
    roleplayDone.addEventListener('change', () => storage.set(prefix + 'roleplay-done', roleplayDone.checked));
  }

  const completeButton = document.querySelector('#complete-day');
  if (completeButton) {
    const completeStatus = document.querySelector('#complete-status');
    if (storage.get(prefix + 'complete', false)) { completeStatus.textContent = '已完成 · 可以随时回来复习'; completeButton.textContent = '已标记完成'; }
    completeButton.addEventListener('click', () => {
      if (completed.size < total) { completeStatus.textContent = `还差 ${total - completed.size} 项页面练习。完成后再回来标记。`; return; }
      if (!document.querySelector('#roleplay-done')?.checked) { completeStatus.textContent = '请先完成至少一场对话练习，并勾选上方的完成框。'; return; }
      storage.set(prefix + 'complete', true);
      completeStatus.textContent = '已完成 · 可以随时回来复习';
      completeButton.textContent = '已标记完成';
    });
  }

  const navLinks = [...document.querySelectorAll('.lesson-aside nav a')];
  if (navLinks.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) { navLinks.forEach(link => link.classList.toggle('active', link.getAttribute('href') === `#${entry.target.id}`)); } });
    }, { rootMargin: '-10% 0px -75% 0px' });
    navLinks.forEach(link => { const section = document.querySelector(link.getAttribute('href')); if (section) observer.observe(section); });
  }
})();
