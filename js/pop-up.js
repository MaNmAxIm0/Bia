export function openLightbox(src, type, title) {
  const lightbox = document.getElementById('lightbox');
  if (!lightbox) {
    console.error('Elemento #lightbox não encontrado no DOM.');
    return;
  }
  lightbox.innerHTML = '';
  const contentWrapper = document.createElement('div');
  contentWrapper.className = 'lightbox-content';
  if (type === 'image') {
    const img = new Image();
    img.onload = function() {
      contentWrapper.style.width = `${this.width}px`;
      contentWrapper.style.height = `${this.height}px`;
      contentWrapper.appendChild(img);
      addControls(contentWrapper, title);
      lightbox.appendChild(contentWrapper);
      lightbox.classList.add('active');
    };
    img.src = src;
    img.alt = title;
  } else if (type === 'video') {
    const video = document.createElement('video');
    video.src = src;
    contentWrapper.appendChild(video);
    addControls(contentWrapper, title);
    lightbox.appendChild(contentWrapper);
    new Plyr(video, { autoplay: true });
    lightbox.classList.add('active');
  }
  document.body.style.overflow = 'hidden';
}
function addControls(container, title) {
  const closeBtn = document.createElement('span');
  closeBtn.className = 'lightbox-close';
  closeBtn.innerHTML = '&times;';
  closeBtn.title = 'Fechar (Esc)';
  const caption = document.createElement('div');
  caption.className = 'lightbox-caption';
  const captionText = document.createElement('span');
  captionText.textContent = title;
  caption.appendChild(captionText);
  container.appendChild(closeBtn);
  container.appendChild(caption);
}
function closeLightbox() {
  const lightbox = document.getElementById('lightbox');
  if (!lightbox) return;
  const videoPlayer = lightbox.querySelector('.plyr');
  if (videoPlayer && videoPlayer.plyr) {
    videoPlayer.plyr.destroy();
  }
  lightbox.classList.remove('active');
  document.body.style.overflow = 'auto';
  setTimeout(() => {
    lightbox.innerHTML = '';
  }, 300);
}
function setupLightboxEventListeners() {
  document.body.addEventListener('click', function(e) {
    if (e.target.matches('#lightbox') || e.target.matches('.lightbox-close')) {
      e.preventDefault();
      e.stopPropagation();
      closeLightbox();
    }
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === "Escape" && document.getElementById('lightbox')?.classList.contains('active')) {
      closeLightbox();
    }
  });
}
document.addEventListener('DOMContentLoaded', setupLightboxEventListeners);
