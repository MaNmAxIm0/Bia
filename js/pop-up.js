// js/pop-up.js (Versão Final com Integração Plyr.io)

import { createWatermarkElement } from './ferramentas.js';
import { getTranslation } from './linguagem.js';

let currentLightbox = null;

function closeLightbox() {
    if (currentLightbox) {
        const lightboxToRemove = currentLightbox; // Guarda a referência ao elemento atual

        lightboxToRemove.classList.remove('active');

        const handler = () => {
            // Remove o próprio listener para garantir que só corre uma vez
            lightboxToRemove.removeEventListener('transitionend', handler);

            if (lightboxToRemove.parentNode) {
                lightboxToRemove.parentNode.removeChild(lightboxToRemove);
            }
            
            // Anula a variável global apenas no final
            if (currentLightbox === lightboxToRemove) {
                currentLightbox = null;
            }
        };

        lightboxToRemove.addEventListener('transitionend', handler);
        
        // Remove o listener da tecla Escape imediatamente
        document.removeEventListener('keydown', handleEscapeKey);
        document.body.style.overflow = '';
    }
}

function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        closeLightbox();
    }
}

export function openLightbox(mediaUrl, mediaType, title = '', description = '') {
    if (currentLightbox) {
        closeLightbox();
    }

    const overlay = document.createElement('div');
    overlay.classList.add('lightbox-overlay');
    overlay.classList.add('active');

    const content = document.createElement('div');
    content.classList.add('lightbox-content');

    const closeBtn = document.createElement('button');
    closeBtn.classList.add('lightbox-close');
    closeBtn.innerHTML = '&times;';
    const closeLabel = getTranslation('close');
    closeBtn.setAttribute('aria-label', closeLabel);
    closeBtn.addEventListener('click', closeLightbox);

    let mediaElement;
    if (mediaType === 'image') {
        mediaElement = document.createElement('img');
        mediaElement.src = mediaUrl;
        mediaElement.alt = title;
        mediaElement.oncontextmenu = () => false;
    } else if (mediaType === 'video') {
        // --- LÓGICA ATUALIZADA PARA CRIAR O PLAYER PLYR ---
        // Cria um elemento <video> que o Plyr irá detetar
        mediaElement = document.createElement('video');
        mediaElement.controls = true;
        mediaElement.autoplay = true; // Faz o vídeo começar a tocar assim que o lightbox abre
        mediaElement.playsInline = true;

        const source = document.createElement('source');
        source.src = mediaUrl;
        source.type = `video/${mediaUrl.split('.').pop()}`; // Deteta o tipo (mp4, webm, etc.)
        
        mediaElement.appendChild(source);
    }

    content.appendChild(closeBtn);
    if (mediaElement) {
        content.appendChild(mediaElement);
        if (mediaType === 'image') {
            content.appendChild(createWatermarkElement());
        }
    }

    const titleEl = document.createElement('h3');
    titleEl.textContent = title;
    content.appendChild(titleEl);

    const descEl = document.createElement('p');
    descEl.textContent = description;
    content.appendChild(descEl);

    overlay.appendChild(content);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    // Se for um vídeo, inicializa o Plyr DEPOIS de o elemento estar na página
    if (mediaType === 'video') {
        // Verifica se a biblioteca Plyr foi carregada nesta página
        if (typeof Plyr !== 'undefined') {
            new Plyr(mediaElement);
        } else {
            console.warn("A biblioteca Plyr.io não foi encontrada nesta página.");
        }
    }

    currentLightbox = overlay;

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeLightbox();
        }
    });

    document.addEventListener('keydown', handleEscapeKey);
}
