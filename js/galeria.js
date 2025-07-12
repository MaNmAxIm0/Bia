// js/galeria.js

// Importa a nova fonte de dados e as ferramentas necessárias
import { DATA_JSON_URL } from './configuracoes.js';
import { createWatermarkElement } from './ferramentas.js'; // Assumindo que a função está em ferramentas.js
import { openLightbox } from './pop-up.js';
import { getTranslation, getCurrentLanguage } from './gestor-de-linguagem.js';

// Função para carregar o conteúdo das galerias (fotos, designs, vídeos)
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
    // 1. ALTERAÇÃO PRINCIPAL: Buscar o data.json local
    const response = await fetch(`../../${DATA_JSON_URL}`); // O ../../ sobe de /js/pt/ para a raiz
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    
    // O 'type' corresponde às chaves no nosso data.json (fotografias, videos, etc.)
    const items = data[type] || [];
    const lang = getCurrentLanguage(); // Obtém o idioma atual (ex: 'pt')

    galleryContainer.innerHTML = ''; // Limpa a mensagem de "a carregar"

    if (items.length === 0) {
      const noContentMessage = getTranslation('no_content_found', { type: getTranslation(type) });
      galleryContainer.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${noContentMessage}</p>`;
      return;
    }

    items.forEach(item => {
      const itemDiv = document.createElement('div');
      itemDiv.classList.add(`${type.slice(0, -1)}-item`);

      // 2. ALTERAÇÃO PRINCIPAL: Usar os dados do novo JSON
      const mediaUrl = item.url; // URL direto do R2
      const title = item.titles[lang] || item.titles['pt']; // Título no idioma correto, com fallback para PT
      const description = item.description || ''; // Descrição (se existir no futuro)

      const isVideo = mediaUrl.toLowerCase().endsWith('.mp4') || mediaUrl.toLowerCase().endsWith('.mov') || mediaUrl.toLowerCase().endsWith('.webm');

      if (!isVideo) { // Lógica para Imagens (fotos, designs)
        const imageContainer = document.createElement('div');
        imageContainer.classList.add('image-container');

        const img = document.createElement('img');
        img.src = mediaUrl; // URL direto do R2
        img.alt = title;
        img.loading = "lazy";
        img.oncontextmenu = () => false;

        imageContainer.appendChild(img);
        imageContainer.appendChild(createWatermarkElement());
        itemDiv.appendChild(imageContainer);

        const overlay = document.createElement('div');
        overlay.classList.add(`${type.slice(0, -1)}-overlay`);
        const h3 = document.createElement('h3');
        h3.textContent = title;
        overlay.appendChild(h3);
        itemDiv.appendChild(overlay);

        itemDiv.addEventListener('click', () => openLightbox(mediaUrl, 'image', title, description));

      } else { // Lógica para Vídeos
        const iframe = document.createElement('iframe');
        iframe.src = mediaUrl; // O URL do R2 pode ser usado diretamente se o bucket for público
        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
        iframe.allowFullscreen = true;
        iframe.frameBorder = "0";
        iframe.title = title;
        iframe.loading = "lazy";
        iframe.oncontextmenu = () => false;

        itemDiv.appendChild(iframe);

        const titleElement = document.createElement('h3');
        titleElement.textContent = title;
        itemDiv.appendChild(titleElement);

        itemDiv.addEventListener('click', (e) => {
          if (e.target !== iframe) {
            openLightbox(mediaUrl, 'video', title, description);
          }
        });
      }
      galleryContainer.appendChild(itemDiv);
    });

  } catch (error) {
    console.error(`galeria.js: Erro ao carregar ${type}:`, error);
    const errorMessage = getTranslation('error_loading_content', { type: getTranslation(type) });
    galleryContainer.innerHTML = `<p style="text-align: center; color: red;">${errorMessage}</p>`;
  }
}

// Função para carregar as apresentações
export async function loadPresentations() {
  console.log("galeria.js: A carregar apresentações.");
  const gallery = document.getElementById("presentation-gallery");
  if (!gallery) return;

  const loadingMessage = getTranslation('loading_presentations');
  gallery.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;

  try {
    // 3. ALTERAÇÃO PRINCIPAL: Buscar o data.json local
    const response = await fetch(`../../${DATA_JSON_URL}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    const presentations = data.apresentacoes || [];
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
      // 4. ALTERAÇÃO PRINCIPAL: Usar o título multilingue
      titleElement.textContent = presentation.titles[lang] || presentation.titles['pt'];
      
      const iframe = document.createElement("iframe");
      // O URL do R2 pode ser usado diretamente se for um link público para um PDF, por exemplo.
      // Se for um link do Google Slides, a lógica de conversão pode ser necessária.
      // Assumindo que o URL no JSON já é o link de 'embed' correto.
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
