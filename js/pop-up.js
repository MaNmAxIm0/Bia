// Ficheiro: js/pop-up.js (Versão Reforçada e Corrigida)

import { createWatermarkElement } from './ferramentas.js';
import { getTranslation } from './linguagem.js';

let currentLightbox = null;
let currentPlayer = null; // Variável global para a instância do Plyr

/**
 * Fecha o lightbox ativo e destrói qualquer player de vídeo.
 */
function closeLightbox() {
    if (currentLightbox) {
        // 1. Destrói a instância do player de vídeo para libertar recursos
        if (currentPlayer) {
            try {
                currentPlayer.destroy();
            } catch (e) {
                console.error("Erro ao destruir o player Plyr:", e);
            }
            currentPlayer = null;
        }

        // 2. Inicia a animação de fecho
        const lightboxToRemove = currentLightbox;
        lightboxToRemove.classList.remove('active');

        // 3. Remove o elemento do DOM apenas após a transição terminar
        const handler = () => {
            lightboxToRemove.removeEventListener('transitionend', handler);
            if (lightboxToRemove.parentNode) {
                lightboxToRemove.parentNode.removeChild(lightboxToRemove);
            }
            // Garante que a variável global é limpa corretamente
            if (currentLightbox === lightboxToRemove) {
                currentLightbox = null;
            }
        };
        lightboxToRemove.addEventListener('transitionend', handler);
        
        // 4. Remove imediatamente os listeners de eventos e restaura o scroll
        document.removeEventListener('keydown', handleEscapeKey);
        document.body.style.overflow = '';
    }
}

/**
 * Lida com o pressionar da tecla 'Escape' para fechar o lightbox.
 * @param {KeyboardEvent} e - O evento do teclado.
 */
function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        closeLightbox();
    }
}

/**
 * Abre um lightbox para exibir uma imagem ou um vídeo.
 * @param {string} mediaUrl - O URL da imagem ou do vídeo.
 * @param {string} mediaType - O tipo de média ('image' ou 'video').
 * @param {string} title - O título da média.
 */
export function openLightbox(mediaUrl, mediaType, title = '') {
    // Se já houver um lightbox, fecha-o primeiro para evitar sobreposições
    if (currentLightbox) {
        closeLightbox();
    }

    const overlay = document.createElement('div');
    overlay.classList.add('lightbox-overlay');
    
    const content = document.createElement('div');
    content.classList.add('lightbox-content');

    const closeBtn = document.createElement('button');
    closeBtn.classList.add('lightbox-close');
    closeBtn.innerHTML = '&times;';
    closeBtn.setAttribute('aria-label', getTranslation('close'));
    closeBtn.addEventListener('click', closeLightbox);

    let mediaElement;

    if (mediaType === 'image') {
        mediaElement = document.createElement('img');
        mediaElement.src = mediaUrl;
        mediaElement.alt = title;
        mediaElement.oncontextmenu = () => false; // Desativa o menu de contexto
        content.appendChild(mediaElement);
        content.appendChild(createWatermarkElement());
    } else if (mediaType === 'video') {
        // Cria o contentor para o vídeo que o Plyr irá usar
        mediaElement = document.createElement('video');
        mediaElement.playsInline = true;
        mediaElement.autoplay = true;
        mediaElement.controls = true;

        const source = document.createElement('source');
        source.src = mediaUrl;
        // Deteta o tipo de ficheiro a partir da extensão para maior precisão
        const fileExtension = mediaUrl.split('.').pop().toLowerCase();
        source.type = `video/${fileExtension}`;
        
        mediaElement.appendChild(source);
        content.appendChild(mediaElement);
    }

    content.appendChild(closeBtn);
    overlay.appendChild(content);
    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    // Força o navegador a processar a inserção do elemento antes de continuar
    requestAnimationFrame(() => {
        overlay.classList.add('active');

        // Inicializa o Plyr DEPOIS de o elemento estar visível e no DOM
        if (mediaType === 'video') {
            if (typeof Plyr !== 'undefined') {
                try {
                    // Guarda a instância do player na variável global
                    currentPlayer = new Plyr(mediaElement, {
                        // Opções do Plyr, se necessário
                        autoplay: true,
                        muted: false,
                    });
                } catch (e) {
                    console.error("Falha ao inicializar o Plyr.io:", e);
                }
            } else {
                console.warn("Biblioteca Plyr.io não encontrada. Usando leitor de vídeo nativo.");
            }
        }
    });

    currentLightbox = overlay;

    // Adiciona listeners para fechar o lightbox
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeLightbox();
        }
    });
    document.addEventListener('keydown', handleEscapeKey);
}
