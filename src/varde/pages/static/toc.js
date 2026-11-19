// Contents nav: scroll-spy sets aria-current="location" on the link of the
// heading nearest above the top of the page, and the <details> stays open from
// 64rem (the rail). ES module loaded by app.js; without it the links are plain anchors.
// `mountToc(root)` works on the document or a shadow root and returns a function that stops it.
// In a shadow root the browser cannot follow "#h-..." into the tree, so a click on any in-page
// link scrolls its target into view there (the nearest scroller, which the host page chooses).
const RAIL_MIN_WIDTH = 64 * 16;

export function mountToc(root = document) {
  const stops = [jumpInside(root)];
  const nav = root.querySelector('nav.doc-toc');
  if (nav) stops.push(spy(root, nav), keepOpenOnRail(nav));
  return () => stops.forEach((stop) => stop());
}

function jumpInside(root) {
  if (root === document) return () => {};
  const onClick = (event) => {
    const link = event.target instanceof Element ? event.target.closest('a[href^="#"]') : null;
    const id = link && decodeURIComponent(link.getAttribute('href').slice(1));
    const target = id && root.getElementById(id);
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView();
  };
  root.addEventListener('click', onClick);
  return () => root.removeEventListener('click', onClick);
}

function spy(root, nav) {
  const links = Array.from(nav.querySelectorAll('a[href^="#h-"]'));
  const heads = links.map((a) => root.getElementById(a.getAttribute('href').slice(1)));
  if (!('IntersectionObserver' in window)) return () => {};
  const above = new Set();
  const mark = () => {
    let active = -1;
    heads.forEach((h, i) => { if (h && above.has(h)) active = i; });
    links.forEach((a, i) => {
      if (i === active) a.setAttribute('aria-current', 'location');
      else a.removeAttribute('aria-current');
    });
  };
  const observer = new IntersectionObserver((entries) => {
    for (const e of entries) {
      const passed = !e.isIntersecting && e.boundingClientRect.top < 0;
      if (e.isIntersecting || passed) above.add(e.target);
      else above.delete(e.target);
    }
    mark();
  }, { rootMargin: '0px 0px -75% 0px' });
  heads.forEach((h) => { if (h) observer.observe(h); });
  return () => observer.disconnect();
}

function keepOpenOnRail(nav) {
  const details = nav.querySelector('details');
  const main = nav.closest('main');
  if (!details || !main || !('ResizeObserver' in window)) return () => {};
  const observer = new ResizeObserver(() => {
    if (main.clientWidth >= RAIL_MIN_WIDTH) details.open = true;
  });
  observer.observe(main);
  return () => observer.disconnect();
}
