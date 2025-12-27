function normalizeTag(tag) {
  return String(tag || "")
    .trim()
    .toLowerCase();
}

function applyPublicationFilter(tag) {
  const target = normalizeTag(tag);
  const items = document.querySelectorAll("[data-pub-tags]");
  items.forEach((item) => {
    const tags = String(item.getAttribute("data-pub-tags") || "")
      .split(",")
      .map(normalizeTag)
      .filter(Boolean);
    const matches = target === "all" || tags.includes(target);
    item.style.display = matches ? "" : "none";
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const buttons = document.querySelectorAll("[data-pub-filter]");
  if (!buttons.length) return;

  const setActive = (button) => {
    buttons.forEach((b) => b.setAttribute("aria-pressed", "false"));
    button.setAttribute("aria-pressed", "true");
  };

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      const tag = button.getAttribute("data-pub-filter") || "all";
      setActive(button);
      applyPublicationFilter(tag);
    });
  });

  const defaultBtn = document.querySelector('[data-pub-filter="all"]');
  if (defaultBtn) defaultBtn.click();
});

