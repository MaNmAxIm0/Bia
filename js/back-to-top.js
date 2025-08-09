document.addEventListener("DOMContentLoaded", function () {
  var backToTopButton = document.getElementById("back-to-top");
  if (backToTopButton) {
    window.onscroll = function () {
      if (
        document.body.scrollTop > 20 ||
        document.documentElement.scrollTop > 20
      ) {
        backToTopButton.style.display = "flex";
        backToTopButton.classList.add("show");
      } else {
        backToTopButton.classList.remove("show");
        setTimeout(function () {
          if (!backToTopButton.classList.contains("show")) {
            backToTopButton.style.display = "none";
          }
        }, 300);
      }
    };
    backToTopButton.onclick = function () {
      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    };
  }
});
