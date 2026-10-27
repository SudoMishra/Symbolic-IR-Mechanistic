const stageOne = {
  5: {
    handleTokens: "235",
    uuidTokens: "386",
    handleLatency: "1.7s",
    uuidLatency: "4.4s",
    handleBinding: "96%",
    uuidBinding: "63%",
  },
  20: {
    handleTokens: "639",
    uuidTokens: "1,237",
    handleLatency: "5.3s",
    uuidLatency: "12.0s",
    handleBinding: "66%",
    uuidBinding: "37%",
  },
};

const switchButtons = document.querySelectorAll("[data-sources]");
const valueNodes = document.querySelectorAll("[data-value]");

function showSourceCount(sourceCount) {
  const values = stageOne[sourceCount];

  switchButtons.forEach((button) => {
    const active = button.dataset.sources === sourceCount;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  valueNodes.forEach((node) => {
    const anim = node.animate(
      [
        { opacity: 1, transform: "translateY(0)" },
        { opacity: 0, transform: "translateY(-0.25rem)" },
      ],
      { duration: 120, easing: "ease-out" },
    );
    anim.onfinish = () => {
      node.textContent = values[node.dataset.value];
      node.animate(
        [
          { opacity: 0, transform: "translateY(0.25rem)" },
          { opacity: 1, transform: "translateY(0)" },
        ],
        { duration: 160, easing: "ease-out" },
      );
    };
  });
}

switchButtons.forEach((button) => {
  button.addEventListener("click", () => showSourceCount(button.dataset.sources));
});

const revealNodes = document.querySelectorAll(
  ".reveal-up, .reveal-side, .reveal-count, .reveal-word, .reveal-image, .reveal-row",
);

if ("IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      });
    },
    { rootMargin: "0px 0px -10%", threshold: 0.08 },
  );

  revealNodes.forEach((node) => observer.observe(node));
} else {
  revealNodes.forEach((node) => node.classList.add("is-visible"));
}

function renderMath() {
  if (typeof renderMathInElement === "function") {
    renderMathInElement(document.body, {
      delimiters: [
        { left: "$$", right: "$$", display: true },
        { left: "\\[", right: "\\]", display: true },
        { left: "$", right: "$", display: false },
        { left: "\\(", right: "\\)", display: false },
      ],
      throwOnError: false,
    });
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderMath);
} else {
  renderMath();
}
window.addEventListener("load", renderMath);
