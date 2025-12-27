function getPreferredTheme() {
  const stored = localStorage.getItem("theme");
  if (stored === "light" || stored === "dark") return stored;

  const prefersDark =
    window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  return prefersDark ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
}

function setTheme(theme) {
  localStorage.setItem("theme", theme);
  applyTheme(theme);
  updateThemeToggle();
}

function updateThemeToggle() {
  const button = document.getElementById("theme-toggle");
  if (!button) return;

  const theme = document.documentElement.dataset.theme || getPreferredTheme();
  const isDark = theme === "dark";
  button.setAttribute(
    "aria-label",
    isDark ? "Switch to light mode" : "Switch to dark mode",
  );
  button.setAttribute("title", isDark ? "Light mode" : "Dark mode");
  button.dataset.theme = theme;
  const icon = button.querySelector("[data-theme-icon]");
  if (icon) icon.textContent = isDark ? "☾" : "☀";
}

document.addEventListener("DOMContentLoaded", () => {
  applyTheme(getPreferredTheme());
  updateThemeToggle();

  const button = document.getElementById("theme-toggle");
  if (!button) return;

  button.addEventListener("click", () => {
    const current =
      document.documentElement.dataset.theme || getPreferredTheme();
    setTheme(current === "dark" ? "light" : "dark");
  });
});

