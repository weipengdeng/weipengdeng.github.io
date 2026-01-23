function installLanguageTabs() {
  const containers = document.querySelectorAll("[data-langtabs]");
  let groupIndex = 0;

  containers.forEach((container) => {
    const panels = Array.from(container.querySelectorAll(".lang-tabs__panel"));
    const nav = container.querySelector(".lang-tabs__nav");
    if (!nav || panels.length < 2) return;

    groupIndex += 1;
    const storageKey = container.getAttribute("data-storage") || "langtabs:lang";
    const defaultId = container.getAttribute("data-default") || "";

    const url = new URL(window.location.href);
    const queryLang = url.searchParams.get("lang") || "";

    const tabs = panels
      .map((panel) => {
        const id = panel.getAttribute("data-langtab-id") || "";
        const label = panel.getAttribute("data-langtab-label") || id;
        if (!id) return null;

        const safeId = String(id).replace(/[^a-z0-9_-]/gi, "-");
        const panelDomId =
          panel.id || `langtab-panel-${groupIndex}-${safeId}`;

        panel.id = panelDomId;
        panel.setAttribute("role", "tabpanel");

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "lang-tabs__btn";
        btn.setAttribute("role", "tab");
        btn.setAttribute(
          "id",
          `langtab-tab-${groupIndex}-${safeId}`,
        );
        btn.setAttribute("aria-controls", panelDomId);
        btn.dataset.langtabTarget = id;
        btn.textContent = label;

        panel.setAttribute("aria-labelledby", btn.id);
        nav.appendChild(btn);

        return { id, btn, panel };
      })
      .filter(Boolean);

    if (tabs.length < 2) return;

    function getStoredLang() {
      try {
        return localStorage.getItem(storageKey) || "";
      } catch (e) {
        return "";
      }
    }

    function setStoredLang(value) {
      try {
        localStorage.setItem(storageKey, value);
      } catch (e) {}
    }

    function activate(targetId, { focus = false } = {}) {
      const target = tabs.find((t) => t.id === targetId) || tabs[0];
      tabs.forEach((t) => {
        const isActive = t.id === target.id;
        t.btn.setAttribute("aria-selected", isActive ? "true" : "false");
        t.btn.tabIndex = isActive ? 0 : -1;
        t.panel.hidden = !isActive;
        t.panel.classList.toggle("is-active", isActive);
        t.btn.classList.toggle("is-active", isActive);
      });
      setStoredLang(target.id);
      if (focus) target.btn.focus();
    }

    function resolveInitialId() {
      const allowed = new Set(tabs.map((t) => t.id));
      if (queryLang && allowed.has(queryLang)) return queryLang;
      const stored = getStoredLang();
      if (stored && allowed.has(stored)) return stored;
      if (defaultId && allowed.has(defaultId)) return defaultId;
      return tabs[0].id;
    }

    tabs.forEach((t) => {
      t.btn.addEventListener("click", () => activate(t.id));
      t.btn.addEventListener("keydown", (e) => {
        const keys = ["ArrowLeft", "ArrowRight", "Home", "End"];
        if (!keys.includes(e.key)) return;
        e.preventDefault();

        const idx = tabs.findIndex((x) => x.btn === e.currentTarget);
        let nextIdx = idx;
        if (e.key === "ArrowRight") nextIdx = (idx + 1) % tabs.length;
        if (e.key === "ArrowLeft") nextIdx = (idx - 1 + tabs.length) % tabs.length;
        if (e.key === "Home") nextIdx = 0;
        if (e.key === "End") nextIdx = tabs.length - 1;

        activate(tabs[nextIdx].id, { focus: true });
      });
    });

    container.setAttribute("data-ready", "1");
    activate(resolveInitialId());
  });
}

document.addEventListener("DOMContentLoaded", () => {
  installLanguageTabs();
});

