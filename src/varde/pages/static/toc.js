// Contents nav: scroll-spy sets aria-current="location" on the link of the section nearest
// above the top of the page; a contents link to a tab names its panel, so a hidden panel is
// never current. The <details> stays open from 64rem (the rail); below it, it closes on leaving
// the rail and when a link is followed. ES module loaded by app.js; without it the links are
// plain anchors.
// `mountToc(root)` works on the document or a shadow root and returns a function that stops it.
// In a shadow root the browser cannot follow "#h-..." into the tree, so a click on any in-page
// link scrolls its target into view there (the nearest scroller, which the host page chooses).
const RAIL_MIN_WIDTH = 64 * 16;
// The observed area runs from far above the page down to a line 25% below the viewport top, so a
// section is "above" exactly when its start is over that line, even after a jump past it.
const ABOVE_PAGE = 10_000_000;

export function mountToc(root = document) {
  const stops = [jumpInside(root)];
  const nav = root.querySelector('nav.doc-toc');
  if (nav) stops.push(spy(root, nav), keepOpenOnRail(nav), closeOnFollow(nav));
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

// The element a contents link marks: the panel of a tab heading (its heading is hidden while
// tabs show), else the heading.
function sectionOf(root, link) {
  const heading = root.getElementById(link.getAttribute('href').slice(1));
  return heading && (heading.closest('.vd-ctabs-panel') || heading);
}

function spy(root, nav) {
  if (!('IntersectionObserver' in window)) return () => {};
  const links = Array.from(nav.querySelectorAll('a[href^="#"]'));
  let sections = [];
  const above = new Set();
  const mark = () => {
    let active = -1;
    sections.forEach((h, i) => { if (h && above.has(h)) active = i; });
    links.forEach((a, i) => {
      if (i === active) a.setAttribute('aria-current', 'location');
      else a.removeAttribute('aria-current');
    });
    if (active >= 0) showInRail(nav, links[active]);
  };
  const observer = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) above.add(e.target);
      else above.delete(e.target);
    }
    mark();
  }, { rootMargin: `${ABOVE_PAGE}px 0px -75% 0px` });
  // A live update replaces blocks, so the sections are looked up again after each one.
  const watch = () => {
    observer.disconnect();
    above.clear();
    sections = links.map((a) => sectionOf(root, a));
    sections.forEach((h) => { if (h) observer.observe(h); });
  };
  const replaced = new MutationObserver(watch);
  const main = nav.closest('main');
  if (main) replaced.observe(main, { childList: true });
  watch();
  return () => { observer.disconnect(); replaced.disconnect(); };
}

// A long rail scrolls inside itself: keep the current link in its view.
function showInRail(nav, link) {
  if (nav.scrollHeight <= nav.clientHeight) return;
  const top = link.offsetTop;
  if (top < nav.scrollTop || top + link.offsetHeight > nav.scrollTop + nav.clientHeight) {
    nav.scrollTop = top - (nav.clientHeight - link.offsetHeight) / 2;
  }
}

// The CSS container query measures main's content box, so padding is left out here too.
function onRail(main) {
  const style = getComputedStyle(main);
  const padding = parseFloat(style.paddingInlineStart) + parseFloat(style.paddingInlineEnd);
  return main.clientWidth - padding >= RAIL_MIN_WIDTH;
}

// Below the rail the bar closes once a link is followed, so the page is not left covered.
function closeOnFollow(nav) {
  const details = nav.querySelector('details');
  const main = nav.closest('main');
  if (!details || !main) return () => {};
  const onClick = (event) => {
    const followed = event.target instanceof Element && event.target.closest('a[href^="#"]');
    if (followed && !onRail(main)) details.open = false;
  };
  nav.addEventListener('click', onClick);
  return () => nav.removeEventListener('click', onClick);
}

function keepOpenOnRail(nav) {
  const details = nav.querySelector('details');
  const main = nav.closest('main');
  if (!details || !main || !('ResizeObserver' in window)) return () => {};
  let wasRail = false;
  const observer = new ResizeObserver(() => {
    const rail = onRail(main);
    if (rail) details.open = true;
    else if (wasRail) details.open = false; // leaving the rail: the bar starts closed
    wasRail = rail;
  });
  observer.observe(main);
  return () => observer.disconnect();
}
