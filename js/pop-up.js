let currentGalleryItems = [];
let currentIndex = -1;

export function openLightbox(items, index) {
  currentGalleryItems = items;
  currentIndex = index;
  const item = currentGalleryItems[currentIndex];
  if (!item) return;

  const lightbox = document.getElementById("lightbox");
  if (!lightbox) {
    console.error("Elemento #lightbox não encontrado no DOM.");
    return;
  }

  lightbox.innerHTML = "";
  const contentWrapper = document.createElement("div");
  contentWrapper.className = "lightbox-content";

  // Only handle images
  if (item.type === "image") {
    const img = new Image();
    img.onload = function() {
      contentWrapper.appendChild(img);
      addControls(lightbox, contentWrapper, item.title);
      lightbox.appendChild(contentWrapper);
      lightbox.classList.add("active");
    };
    img.src = item.src;
    img.alt = item.title;
    img.oncontextmenu = () => false; // Disable right-click
  } else {
    console.warn("Lightbox received unsupported item type:", item.type);
    return;
  }
  document.body.style.overflow = "hidden";
}
function addControls(lightbox, container, title) {
  const closeBtn = document.createElement("button");
  closeBtn.className = "lightbox-close";
  closeBtn.innerHTML = "&times;";
  closeBtn.title = "Fechar (Esc)";
  closeBtn.onclick = (e) => { e.stopPropagation(); closeLightbox(); };

  const caption = document.createElement("div");
  caption.className = "lightbox-caption";
  const captionText = document.createElement("span");
  captionText.textContent = title;
  caption.appendChild(captionText);

  const prevBtn = document.createElement("button");
  prevBtn.className = "lightbox-nav lightbox-prev";
  prevBtn.innerHTML = "&#10094;";
  prevBtn.title = "Anterior";
  prevBtn.onclick = (e) => { e.stopPropagation(); showPrev(); };

  const nextBtn = document.createElement("button");
  nextBtn.className = "lightbox-nav lightbox-next";
  nextBtn.innerHTML = "&#10095;";
  nextBtn.title = "Seguinte";
  nextBtn.onclick = (e) => { e.stopPropagation(); showNext(); };

  lightbox.appendChild(closeBtn);
  lightbox.appendChild(prevBtn);
  lightbox.appendChild(nextBtn);
  container.appendChild(caption);
}

function showNext() {
  currentIndex = (currentIndex + 1) % currentGalleryItems.length;
  openLightbox(currentGalleryItems, currentIndex);
}

function showPrev() {
  currentIndex = (currentIndex - 1 + currentGalleryItems.length) % currentGalleryItems.length;
  openLightbox(currentGalleryItems, currentIndex);
}

function closeLightbox() {
  const lightbox = document.getElementById("lightbox");
  if (!lightbox) return;
  // Removed video player destruction logic
  lightbox.classList.remove("active");
  document.body.style.overflow = "auto";
  setTimeout(() => {
    lightbox.innerHTML = "";
  }, 300);
}

function setupLightboxEventListeners() {
  document.body.addEventListener("click", function(e) {
    if (e.target.matches("#lightbox")) {
      e.preventDefault();
      e.stopPropagation();
      closeLightbox();
    }
  });

  document.addEventListener("keydown", function(e) {
    const lightbox = document.getElementById("lightbox");
    if (!lightbox?.classList.contains("active")) return;

    if (e.key === "Escape") {
      closeLightbox();
    } else if (e.key === "ArrowRight") {
      showNext();
    } else if (e.key === "ArrowLeft") {
      showPrev();
    }
  });
}

document.addEventListener("DOMContentLoaded", setupLightboxEventListeners);
