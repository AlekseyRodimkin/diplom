const htmlEl = document.documentElement;
const btn = document.getElementById("themeToggleBtn");
const icon = document.getElementById("themeIcon");

const savedTheme = localStorage.getItem("theme") || "light";
htmlEl.setAttribute("data-bs-theme", savedTheme);

function updateIcon(theme) {
    icon.textContent = theme === "light" ? "🌒" : "🌖";
}

updateIcon(savedTheme);

btn.addEventListener("click", () => {
    const current = htmlEl.getAttribute("data-bs-theme");
    const next = current === "light" ? "dark" : "light";

    htmlEl.setAttribute("data-bs-theme", next);
    localStorage.setItem("theme", next);

    updateIcon(next);
});
