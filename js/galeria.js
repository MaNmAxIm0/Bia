// js/galeria.js (Versão Final com Infinite Scroll Corrigido)

import { getTranslation, getCurrentLanguage } from './gestor-de-linguagem.js';
import { createWatermarkElement } from './ferramentas.js';
import { openLightbox } from './pop-up.js';

// Objeto para guardar o estado de cada galeria individualmente
const galleryStates = {};

/**
 * Renderiza o próximo lote de itens para uma galeria específica.
 * @param {string} containerId - O ID do contentor da galeria.
 */
function renderNextBatch(containerId) {
    const state = galleryStates[containerId];
    if (!state || state.currentIndex >= state.allItems.length) {
        if (state.observer) state.observer.disconnect(); // Para de observar se não há mais itens
        return;
    }

    const galleryContainer = document.getElementById(containerId);
    if (!galleryContainer) return;

    const lang = getCurrentLanguage();
    const itemsToRender = state.allItems.slice(state.currentIndex, state.currentIndex + state.itemsPerLoad);

    itemsToRender.forEach(item => {
        const itemDiv = document.createElement('div');
        const classMap = { 'fotografias': 'photo', 'designs': 'design', 'videos': 'video' };
        itemDiv.classList.add(`${classMap[state.type]}-item`);

        const mediaUrl = item.url;
        const title = item.titles[lang] || item.titles['pt'];
        const isVideo = state.type === 'videos';

        const imageContainer = document.createElement('div');
        imageContainer.classList.add('image-container');

        const mediaElement = document.createElement('img');
        mediaElement.src = isVideo ? item.thumbnail_url : mediaUrl;
        mediaElement.alt = title;
        mediaElement.loading = "lazy";
        mediaElement.oncontextmenu = () => false;
        
        imageContainer.appendChild(mediaElement);

        if (isVideo) {
            const playIcon = document.createElement('i');
            playIcon.className = 'fas fa-play video-play-icon';
            imageContainer.appendChild(playIcon);
        }

        const overlayDiv = document.createElement('div');
        overlayDiv.classList.add(`${classMap[state.type]}-overlay`);
        const titleElement = document.createElement('h3');
        titleElement.textContent = title;
        overlayDiv.appendChild(titleElement);

        itemDiv.appendChild(imageContainer);
        itemDiv.appendChild(overlayDiv);

        itemDiv.addEventListener('click', () => {
            openLightbox(mediaUrl, isVideo ? 'video' : 'image', title);
        });

        galleryContainer.appendChild(itemDiv);
    });

    state.currentIndex += itemsToRender.length;

    // Se ainda houver itens, observa o novo último elemento
    if (state.currentIndex < state.allItems.length) {
        const lastElement = galleryContainer.lastElementChild;
        if (lastElement) {
            state.observer.observe(lastElement);
        }
    } else {
        state.observer.disconnect(); // Fim da lista
    }
}

/**
 * Função principal que inicia o carregamento da galeria.
 */
export async function loadGalleryContent(type, containerId, orientationFilter = null) {
    const galleryContainer = document.getElementById(containerId);
    if (!galleryContainer) return;

    // Limpa o estado anterior para esta galeria, se existir
    if (galleryStates[containerId] && galleryStates[containerId].observer) {
        galleryStates[containerId].observer.disconnect();
    }

    // Adiciona a classe para o estilo 16:9 se a orientação for horizontal
    if (orientationFilter === 'horizontal') {
        galleryContainer.classList.add('horizontal-gallery');
    } else {
        galleryContainer.classList.remove('horizontal-gallery'); // Garante que não fica em outras páginas
    }

    galleryContainer.innerHTML = `<p style="text-align: center;">${getTranslation('loading_content')}</p>`;
    
    try {
        const response = await fetch(`../../data.json`);
        const data = await response.json();
        
        let allFilteredItems = data[type] || [];
        if (orientationFilter) {
            allFilteredItems = allFilteredItems.filter(item => item.orientation === orientationFilter);
        }

        galleryContainer.innerHTML = '';

        if (allFilteredItems.length === 0) {
            galleryContainer.innerHTML = `<p>${getTranslation('no_content_found', { type: getTranslation(type) })}</p>`;
            return;
        }

        // Cria um novo observador para esta galeria
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
        }, { rootMargin: "500px" }); // Carrega 500px antes de o elemento ser visível

        // Inicializa o estado para esta galeria específica
        galleryStates[containerId] = {
            allItems: allFilteredItems,
            currentIndex: 0,
            itemsPerLoad: 12, // Pode ajustar este número
            type: type,
            observer: observer
        };

        // Inicia o processo renderizando o primeiro lote
        renderNextBatch(containerId);

    } catch (error) {
        console.error(`Erro ao carregar ${type}:`, error);
        galleryContainer.innerHTML = `<p style="color: red;">${getTranslation('error_loading_content', { type: getTranslation(type) })}</p>`;
    }
}

/**
 * Carrega e exibe as apresentações (sem carregamento progressivo).
 */
export async function loadPresentations() {
  const gallery = document.getElementById("presentation-gallery");
  if (!gallery) return;
  gallery.innerHTML = `<p style="text-align: center;">${getTranslation('loading_presentations')}</p>`;
  try {
    const response = await fetch(`../../data.json`);
    const data = await response.json();
    const presentations = data['apresentacoes'] || [];
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
      iframe.oncontextmenu = () => false;
      div.appendChild(titleElement);
      div.appendChild(iframe);
      gallery.appendChild(div);
    });
  } catch (err) {
    console.error("Erro ao carregar apresentações:", err);
    gallery.innerHTML = `<p style="color: red;">${getTranslation('error_loading_content', { type: getTranslation('presentations') })}</p>`;
  }
}
