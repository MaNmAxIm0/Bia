function initThemeSwitcher() {
  const themeToggleButton = document.getElementById("theme-toggle");
  const currentTheme = localStorage.getItem("theme");
  if (currentTheme) {
    document.documentElement.setAttribute("data-tema", currentTheme);
  }
  if (themeToggleButton) {
    themeToggleButton.removeEventListener("click", handleThemeToggle);
    themeToggleButton.addEventListener("click", handleThemeToggle);
  }
}
function handleThemeToggle() {
  let theme = document.documentElement.getAttribute("data-tema");
  if (theme === "escuro") {
    document.documentElement.setAttribute("data-tema", "claro");
    localStorage.setItem("theme", "claro");
  } else {
    document.documentElement.setAttribute("data-tema", "escuro");
    localStorage.setItem("theme", "escuro");
  }
}
document.addEventListener("headerLoaded", initThemeSwitcher);
if (document.readyState === "complete") {
  setTimeout(() => {
    if (!document.getElementById("theme-toggle")) {
      initThemeSwitcher();
    }
  }, 100);
}
