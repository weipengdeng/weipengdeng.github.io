function installMarkdownImageInteractions() {
  const figures = document.querySelectorAll("[data-md-figure]");
  figures.forEach((figure) => {
    figure.addEventListener("dblclick", () => {
      figure.classList.toggle("is-full");
    });
  });
}

document.addEventListener("DOMContentLoaded", installMarkdownImageInteractions);

