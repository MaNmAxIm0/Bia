// js/galeria.js (Versão Corrigida - Sem Duplicação)

import { DATA_JSON_URL } from './configuracoes.js';
import { createWatermarkElement } from './ferramentas.js';
import { openLightbox } from './pop-up.js';
import { getTranslation, getCurrentLanguage } from './gestor-de-linguagem.js';

// --- FUNÇÃO PRINCIPAL PARA GALERIAS (FOTOS, VÍDEOS, DESIGNS) ---
export async function loadGalleryContent(type, containerId) {
  console.log(`galeria.js: A carregar conteúdo para tipo: ${type}`);
  const galleryContainer = document.getElementById(containerId);
  if (!galleryContainer) {
    console.error(`galeria.js: Contentor com ID '${containerId}' não encontrado.`);
    return;
  }

  const loadingMessage = getTranslation('loading_content');
  galleryContainer.innerHTML = `<p id="loadingMessage" style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;
  
  try {
    // O caminho para o data.json é relativo à página HTML, por isso usamos ../../
    const response = await fetch(`../../data.json`); 
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    const items = data[type] || [];
    const lang = getCurrentLanguage();

    galleryContainer.innerHTML = '';

    if (items.length === 0) {
      const noContentMessage = getTranslation('no_content_found', { type: getTranslation(type) });
      galleryContainer.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${noContentMessage}</p>`;
      return;
    }

    items.forEach(item => {
      const itemDiv = document.createElement('div');
      
      const classMap = {
        'fotografias': 'photo',
        'designs': 'design',
        'videos': 'video'
      };
      const baseClass = classMap[type];
      itemDiv.classList.add(`${baseClass}-item`);

      const mediaUrl = item.url;
      const title = item.titles[lang] || item.titles['pt'];
      const description = '';

      const isVideo = type === 'videos';

      let mediaElement;
      if (!isVideo) {
        mediaElement = document.createElement('img');
        mediaElement.src = mediaUrl;
      } else {
        mediaElement = document.createElement('img');
        mediaElement.src = item.thumbnail_url;
        mediaElement.classList.add('video-thumbnail');
      }
      mediaElement.alt = title;
      mediaElement.loading = "lazy";
      mediaElement.oncontextmenu = () => false;
      
      const imageContainer = document.createElement('div');
      imageContainer.classList.add('image-container');
      imageContainer.appendChild(mediaElement);
      imageContainer.appendChild(createWatermarkElement());

      if (isVideo) {
        const playIcon = document.createElement('i');
        playIcon.className = 'fas fa-play video-play-icon';
        imageContainer.appendChild(playIcon);
      }

      const overlayDiv = document.createElement('div');
      overlayDiv.classList.add(`${baseClass}-overlay`);
      
      const titleElement = document.createElement('h3');
      titleElement.textContent = title;
      overlayDiv.appendChild(titleElement);

      itemDiv.appendChild(imageContainer);
      itemDiv.appendChild(overlayDiv);

      itemDiv.addEventListener('click', () => {
        const mediaType = isVideo ? 'video' : 'image';
        openLightbox(mediaUrl, mediaType, title, description);
      });

      galleryContainer.appendChild(itemDiv);
    });

  } catch (error) {
    console.error(`galeria.js: Erro ao carregar ${type}:`, error);
    const errorMessage = getTranslation('error_loading_content', { type: getTranslation(type) });
    galleryContainer.innerHTML = `<p style="text-align: center; color: red;">${errorMessage}</p>`;
  }
}


// --- FUNÇÃO APENAS PARA A PÁGINA DE APRESENTAÇÕES ---
// (Esta era a função que estava duplicada)
export async function loadPresentations() {
  console.log("galeria.js: A carregar apresentações.");
  const gallery = document.getElementById("presentation-gallery");
  if (!gallery) return;

  const loadingMessage = getTranslation('loading_presentations');
  gallery.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;

  try {
    const response = await fetch(`../../data.json`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const presentations = data['apresentacoes'] || [];
    const lang = getCurrentLanguage();

    gallery.innerHTML = '';

    if (presentations.length === 0) {
      const noContentMessage = getTranslation('no_presentations_found');
      gallery.innerHTML = `<p style='text-align: center; color: var(--light-text-color);'>${noContentMessage}</p>`;
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
      iframe.oncontextmenu = () => false;
      
      div.appendChild(titleElement);
      div.appendChild(iframe);
      gallery.appendChild(div);
    });
  } catch (err) {
    console.error("galeria.js: Erro ao carregar apresentações:", err);
    const errorMessage = getTranslation('error_loading_content', { type: getTranslation('presentations') });
    gallery.innerHTML = `<p style='text-align: center; color: red;'>${errorMessage}</p>`;
  }
}
