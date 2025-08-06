import { getTranslation, getCurrentLanguage } from './linguagem.js';
import { openLightbox } from './pop-up.js';
const galleryStates = {};
function getBasePath() {
  return window.location.hostname.includes('github.io') ? '/Bia' : '';
}
function renderNextBatch(containerId) {
  const state = galleryStates[containerId];
  if (!state || state.currentIndex >= state.allItems.length) {
    if (state.observer) state.observer.disconnect();
    return;
  }
  const galleryContainer = document.getElementById(containerId);
  if (!galleryContainer) return
  const lang = getCurrentLanguage();
  const itemsToRender = state.allItems.slice(state.currentIndex, state.currentIndex + state.itemsPerLoad);
  itemsToRender.forEach(item => {
    const itemDiv = document.createElement('div');
    const classMap = { 'fotografias': 'photo', 'designs': 'design', 'videos': 'video' };
    const itemClassName = classMap[state.type] || 'gallery';
    itemDiv.classList.add(`${itemClassName}-item`);
    const title = item.titles[lang] || item.titles.pt;
    const isVideo = state.type === 'videos';
    const previewImageUrl = isVideo ? item.thumbnail_url : item.url;
    const imageContainer = document.createElement('div');
    imageContainer.classList.add('image-container');
    const mediaElement = document.createElement('img');
    mediaElement.src = previewImageUrl;
    mediaElement.alt = title;
    mediaElement.loading = "lazy";
    mediaElement.onerror = () => {
      mediaElement.src = `${getBasePath()}/imagens/placeholder.png`;
    };
    imageContainer.appendChild(mediaElement);
    if (isVideo) {
      const playIcon = document.createElement('i');
      playIcon.className = 'fas fa-play video-play-icon';
      imageContainer.appendChild(playIcon);
    }
    const overlayDiv = document.createElement('div');
    overlayDiv.classList.add(`${itemClassName}-overlay`);
    const titleElement = document.createElement('h3');
    titleElement.textContent = title;
    overlayDiv.appendChild(titleElement);
    itemDiv.appendChild(imageContainer);
    itemDiv.appendChild(overlayDiv);
    itemDiv.addEventListener('click', () => {
      if (isVideo) {
        // Verificar se o vídeo já está a ser reproduzido
        if (imageContainer.querySelector('video')) {
          return; // Se já está a reproduzir, não fazer nada
        }

        // Substituir apenas a imagem pelo vídeo, mantendo o overlay
        const videoElement = document.createElement('video');
        videoElement.src = item.url;
        videoElement.controls = true;
        videoElement.autoplay = true;
        videoElement.setAttribute('playsinline', '');
        videoElement.setAttribute('webkit-playsinline', '');
        videoElement.setAttribute('x5-playsinline', '');
        
        // Detectar orientação do vídeo e ajustar container
        videoElement.addEventListener('loadedmetadata', () => {
          const isVertical = videoElement.videoHeight > videoElement.videoWidth;
          if (isVertical) {
            imageContainer.classList.add('vertical-video');
          } else {
            imageContainer.classList.add('horizontal-video');
          }
        });
        
        // Adicionar evento para quando o vídeo terminar
        videoElement.addEventListener('ended', () => {
          // Restaurar o thumbnail quando o vídeo terminar
          imageContainer.innerHTML = '';
          imageContainer.appendChild(mediaElement);
          imageContainer.appendChild(playIcon);
          itemDiv.classList.remove('playing');
        });
        
        // Criar botão de ecrã inteiro
        const fullscreenButton = document.createElement('button');
        fullscreenButton.className = 'fullscreen-button';
        fullscreenButton.innerHTML = '<i class="fas fa-expand"></i>';
        fullscreenButton.title = 'Ecrã Cheio';
        fullscreenButton.addEventListener('click', (e) => {
          e.stopPropagation();
          if (videoElement.requestFullscreen) {
            videoElement.requestFullscreen();
          } else if (videoElement.webkitRequestFullscreen) {
            videoElement.webkitRequestFullscreen();
          } else if (videoElement.msRequestFullscreen) {
            videoElement.msRequestFullscreen();
          }
        });
        
        // Substituir apenas a imagem pelo vídeo
        imageContainer.innerHTML = '';
        imageContainer.appendChild(videoElement);
        imageContainer.appendChild(fullscreenButton);
        
        // Focar no vídeo para melhor experiência do utilizador
        videoElement.focus();
        
      } else {
        openLightbox(item.url, 'image', title);
      }
    });
    galleryContainer.appendChild(itemDiv);
  });
  state.currentIndex += itemsToRender.length;
  if (state.currentIndex < state.allItems.length) {
    const lastElement = galleryContainer.lastElementChild;
    if (lastElement) {
      state.observer.observe(lastElement);
    }
  } else {
    state.observer.disconnect();
  }
}
export async function loadGalleryContent(type, containerId, orientationFilter = null) {
  const galleryContainer = document.getElementById(containerId);
  if (!galleryContainer) return;
  if (galleryStates[containerId] && galleryStates[containerId].observer) {
    galleryStates[containerId].observer.disconnect();
  }
  if (orientationFilter === 'horizontal') {
    galleryContainer.classList.add('horizontal-gallery');
  } else {
    galleryContainer.classList.remove('horizontal-gallery');
  }
  galleryContainer.innerHTML = `<p style="text-align: center;">${getTranslation('loading_content')}</p>`;
  try {
    const response = await fetch(`${getBasePath()}/data.json`);
    if (!response.ok) throw new Error(`Network response was not ok: ${response.statusText}`);
    const data = await response.json();
    let allFilteredItems = Object.values(data).filter(item => {
      if (!item.url) return false;
      if (type === 'fotografias' && item.url.includes('/Fotografias/')) return true;
      if (type === 'videos' && item.url.includes('/Vídeos/')) return true;
      if (type === 'designs' && item.url.includes('/Designs/')) return true;
      return false;
    });
    if (orientationFilter) {
      allFilteredItems = allFilteredItems.filter(item => item.orientation === orientationFilter);
    }
    galleryContainer.innerHTML = '';
    if (allFilteredItems.length === 0) {
      galleryContainer.innerHTML = `<p>${getTranslation('no_content_found').replace('{type}', getTranslation(type))}</p>`;
      return;
    }
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const state = galleryStates[containerId];
          if (state) {
            state.observer.unobserve(entry.target);
            renderNextBatch(containerId);
          }
        }
      });
    }, { rootMargin: "500px" });
    galleryStates[containerId] = {
      allItems: allFilteredItems,
      currentIndex: 0,
      itemsPerLoad: 12,
      type: type,
      observer: observer
    };
    renderNextBatch(containerId);
  } catch (error) {
    console.error(`Erro ao carregar ${type}:`, error);
    galleryContainer.innerHTML = `<p style="color: red;">${getTranslation('error_loading_content').replace('{type}', getTranslation(type))}</p>`;
  }
}
export async function loadPresentations() {
  const gallery = document.getElementById("presentation-gallery");
  if (!gallery) return;
  gallery.innerHTML = `<p style="text-align: center;">${getTranslation('loading_presentations')}</p>`;
  try {
    const response = await fetch(`${getBasePath()}/data.json`);
    const data = await response.json();
    const presentations = Object.values(data).filter(item => {
      const url = item.url.toLowerCase();
      return item.is_external || url.endsWith('.pdf');
    });
    const lang = getCurrentLanguage();
    gallery.innerHTML = '';
    if (presentations.length === 0) {
      gallery.innerHTML = `<p>${getTranslation('no_presentations_found')}</p>`;
      return;
    }
    presentations.forEach(presentation => {
      const div = document.createElement("div");
      div.className = "presentation-item";
      const titleElement = document.createElement("h3");
      titleElement.textContent = presentation.titles[lang] || presentation.titles['pt'];
      const iframe = document.createElement("iframe");
      iframe.src = presentation.url;
      iframe.allowFullscreen = true;
      iframe.title = titleElement.textContent;
      iframe.loading = "lazy";
      div.appendChild(titleElement);
      div.appendChild(iframe);
      gallery.appendChild(div);
    });
  } catch (err) {
    console.error("Erro ao carregar apresentações:", err);
    gallery.innerHTML = `<p style="color: red;">${getTranslation('error_loading_content').replace('{type}', getTranslation('presentations'))}</p>`;
  }
}
