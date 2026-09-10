/* Static replacement for navigation, CMS filtering, reading progress and zoom. */
(() => {
  'use strict';
  document.querySelectorAll('#year').forEach(el => { el.textContent = new Date().getFullYear(); });

  const nav = document.querySelector('.w-nav');
  const menu = nav?.querySelector('.w-nav-menu');
  const toggle = nav?.querySelector('.w-nav-button');
  const setMenu = open => {
    nav?.classList.toggle('menu-open', open);
    toggle?.classList.toggle('w--open', open);
    toggle?.setAttribute('aria-expanded', String(open));
    toggle?.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  };
  toggle?.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  menu?.addEventListener('click', event => { if (event.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && nav?.classList.contains('menu-open')) { setMenu(false); toggle.focus(); }
  });
  document.addEventListener('click', event => { if (nav && !nav.contains(event.target)) setMenu(false); });
  window.matchMedia('(min-width: 992px)').addEventListener('change', event => { if (event.matches) setMenu(false); });

  const form = document.querySelector('[fs-cmsfilter-element="filters"]');
  if (form) {
    const search = form.querySelector('.blog-search');
    const checks = [...form.querySelectorAll('input[type="checkbox"]')];
    const list = document.querySelector('[fs-cmsfilter-element="list"]');
    const cards = [...list.children].map(el => ({
      el,
      text: [...el.querySelectorAll('[fs-cmsfilter-field="name"], [fs-cmsfilter-field="description"]')].map(n => n.textContent).join(' ').toLowerCase(),
      tags: [...el.querySelectorAll('[fs-cmsfilter-field="tag"]')].map(n => n.textContent.trim())
    }));
    const empty = document.querySelector('[fs-cmsfilter-element="empty"]');
    const count = document.querySelector('[fs-cmsfilter-element="results-count"]');
    const update = () => {
      const words = search.value.trim().toLowerCase().split(/\s+/).filter(Boolean);
      const selected = checks.filter(n => n.checked).map(n => n.value);
      let total = 0;
      cards.forEach(card => {
        const visible = words.every(word => card.text.includes(word)) && (!selected.length || selected.some(tag => card.tags.includes(tag)));
        card.el.hidden = !visible;
        if (visible) total++;
      });
      checks.forEach(input => input.parentElement.querySelector('.checkbox')?.classList.toggle('w--redirected-checked', input.checked));
      count.textContent = String(total);
      if (empty) { empty.hidden = total !== 0; empty.style.display = total ? 'none' : 'block'; }
    };
    form.addEventListener('submit', event => event.preventDefault());
    form.addEventListener('input', update);
    form.addEventListener('change', update);
    update();
  }

  const article = document.querySelector('.article-text-height');
  if (article) {
    const updateProgress = () => {
      const rect = article.getBoundingClientRect();
      const percent = Math.max(0, Math.min(100, (window.innerHeight - rect.top) / Math.max(rect.height, 1) * 100));
      document.querySelectorAll('.progress').forEach(el => { el.style.width = percent + '%'; });
      document.querySelectorAll('.percent').forEach(el => { el.textContent = Math.round(percent) + '%'; });
    };
    window.addEventListener('scroll', updateProgress, {passive:true});
    window.addEventListener('resize', updateProgress);
    updateProgress();
  }

  document.querySelectorAll('[data-action="zoom"] img').forEach(img => {
    img.tabIndex = 0;
    img.setAttribute('role', 'button');
    img.setAttribute('aria-label', img.alt ? 'Enlarge: ' + img.alt : 'Enlarge tutorial image');
    const open = () => {
      const dialog = document.createElement('dialog');
      dialog.className = 'image-zoom';
      dialog.setAttribute('aria-label', 'Enlarged tutorial image');
      const full = document.createElement('img'); full.src = img.src; full.alt = img.alt;
      const close = document.createElement('button'); close.className = 'zoom-close'; close.textContent = '×'; close.setAttribute('aria-label', 'Close image');
      dialog.append(full, close); document.body.append(dialog);
      dialog.addEventListener('click', () => dialog.close());
      dialog.addEventListener('close', () => { dialog.remove(); img.focus(); });
      dialog.showModal();
    };
    img.addEventListener('click', open);
    img.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(); } });
  });

  // Existing Osmosis Intercom workspace. The public app ID is not a secret.
  window.intercomSettings = {api_base:'https://api-iam.intercom.io', app_id:'uco7rjff'};
  if (typeof window.Intercom !== 'function') {
    const intercom = function () { intercom.q.push(arguments); };
    intercom.q = []; window.Intercom = intercom;
    const script = document.createElement('script'); script.async = true;
    script.src = 'https://widget.intercom.io/widget/uco7rjff';
    document.head.append(script);
  }
  document.querySelectorAll('#my-unique-link, #chat-expert-link').forEach(link => {
    link.addEventListener('click', event => { event.preventDefault(); window.Intercom('show'); });
  });
})();
