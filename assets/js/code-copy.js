function copyTextToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }

  return new Promise((resolve, reject) => {
    try {
      const textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.position = "fixed";
      textarea.style.top = "-9999px";
      textarea.style.left = "-9999px";
      document.body.appendChild(textarea);
      textarea.select();
      const ok = document.execCommand("copy");
      document.body.removeChild(textarea);
      ok ? resolve() : reject(new Error("copy failed"));
    } catch (err) {
      reject(err);
    }
  });
}

function installBibtexCopyButtons() {
  const codeBlocks = document.querySelectorAll("pre > code");
  codeBlocks.forEach((code) => {
    const cls = String(code.className || "");
    const isBibtex =
      cls.includes("language-bibtex") ||
      cls.includes("lang-bibtex") ||
      cls.includes("bibtex");
    if (!isBibtex) return;

    const pre = code.parentElement;
    if (!pre || pre.dataset.copyEnhanced === "true") return;
    pre.dataset.copyEnhanced = "true";

    const wrapper = document.createElement("div");
    wrapper.className = "code-block";

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    const button = document.createElement("button");
    button.type = "button";
    button.className = "code-copy-btn";
    button.textContent = "Copy";
    button.setAttribute("aria-label", "Copy BibTeX to clipboard");

    let resetTimer = 0;
    button.addEventListener("click", async () => {
      try {
        window.clearTimeout(resetTimer);
        button.disabled = true;
        await copyTextToClipboard(code.textContent || "");
        button.textContent = "Copied";
        resetTimer = window.setTimeout(() => {
          button.textContent = "Copy";
        }, 1400);
      } catch (e) {
        button.textContent = "Failed";
        resetTimer = window.setTimeout(() => {
          button.textContent = "Copy";
        }, 1400);
      } finally {
        button.disabled = false;
      }
    });

    wrapper.appendChild(button);
  });
}

document.addEventListener("DOMContentLoaded", installBibtexCopyButtons);

