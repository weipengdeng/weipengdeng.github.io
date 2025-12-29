function installMarkdownImageInteractions() {
  const figures = document.querySelectorAll("[data-md-figure]");
  figures.forEach((figure) => {
    figure.addEventListener("dblclick", () => {
      figure.classList.toggle("is-full");
    });
  });
}

function getActiveGalleryIndex(track, items) {
  const left = track.scrollLeft;
  let bestIdx = 0;
  let bestDist = Number.POSITIVE_INFINITY;
  items.forEach((el, idx) => {
    const dist = Math.abs(left - el.offsetLeft);
    if (dist < bestDist) {
      bestDist = dist;
      bestIdx = idx;
    }
  });
  return bestIdx;
}

function installGalleryNav() {
  const buttons = document.querySelectorAll("[data-gallery-nav]");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = Number(btn.getAttribute("data-gallery-nav") || "0");
      const gallery = btn.closest(".gallery");
      const track = gallery && gallery.querySelector(".gallery__track");
      if (!track) return;

      const items = Array.from(track.querySelectorAll(".gallery__item"));
      if (items.length < 2) return;

      const active = getActiveGalleryIndex(track, items);
      const next = (active + dir + items.length) % items.length;
      const target = items[next];
      track.scrollTo({ left: target.offsetLeft, behavior: "smooth" });
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  installMarkdownImageInteractions();
  installGalleryNav();
});
