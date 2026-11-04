// Shared behaviour for the inner pages: nav background on scroll, quiet reveals, mobile menu.
(function () {
  var nav = document.getElementById('nav');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('is-scrolled', window.scrollY > 24); };
    window.addEventListener('scroll', onScroll, { passive: true }); onScroll();
  }

  // Stagger siblings that reveal together
  document.querySelectorAll('.reveal').forEach(function (el) {
    var sibs = Array.prototype.filter.call(el.parentElement.children, function (c) { return c.classList.contains('reveal'); });
    if (sibs.length > 1) el.style.setProperty('--d', (sibs.indexOf(el) * 90) + 'ms');
  });
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -10% 0px' });
  document.querySelectorAll('.reveal').forEach(function (el) { io.observe(el); });

  var menu = document.getElementById('mobile-menu'), openBtn = document.getElementById('menu-open');
  if (menu && openBtn) {
    var closeBtn = menu.querySelector('button');
    openBtn.addEventListener('click', function () { menu.classList.add('is-open'); closeBtn.focus(); });
    closeBtn.addEventListener('click', function () { menu.classList.remove('is-open'); openBtn.focus(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') menu.classList.remove('is-open'); });
    menu.querySelectorAll('a').forEach(function (l) { l.addEventListener('click', function () { menu.classList.remove('is-open'); }); });
  }
})();
