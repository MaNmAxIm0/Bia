import { WEB_APP_URL } from './configuracoes.js';
import { getDirectGoogleDriveUrl, createWatermarkElement } from 'ferramentas';
import { openLightbox } from 'lightbox';

export async function loadGalleryContent(type, containerId) {
    const galleryContainer = document.getElementById(containerId);
    if (!galleryContainer) return;

    // Determine loading message based on current page language
    const currentLang = window.location.pathname.includes('/en/') ? 'en' : 'pt';
    const loadingMessage = currentLang === 'en' ? 'Loading content...' : 'A carregar conteúdo...';
    
    galleryContainer.innerHTML = `<p id="loadingMessage" style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;
    const loadingMessageEl = galleryContainer.querySelector('#loadingMessage');

    try {
        const response = await fetch(WEB_APP_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        let items = [];

        if (type === 'photos') {
            items = data.fotografias || []; 
        } else if (type === 'designs') {
            items = data.designs || [];
        } else if (type === 'videos') {
            items = data.videos || [];
        }

        if (loadingMessageEl) loadingMessageEl.style.display = 'none';

        if (items.length === 0) {
            const noContentMessage = currentLang === 'en' ? `No content for '${type}' found.` : `Nenhum conteúdo para '${type}' encontrado.`;
            galleryContainer.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${noContentMessage}</p>`;
            return;
        }

        galleryContainer.innerHTML = ''; 

        items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.classList.add(`${type.slice(0, -1)}-item`);

            const url = item.url;
            const isVideo = url.toLowerCase().endsWith('.mp4') || 
                           url.toLowerCase().endsWith('.mov') || 
                           url.toLowerCase().endsWith('.avi') || 
                           url.toLowerCase().endsWith('.webm') ||
                           url.toLowerCase().endsWith('.mkv') ||
                           url.includes('youtube.com') || 
                           url.includes('youtu.be') || 
                           (item.mime && item.mime.startsWith('video/')) ||
                           (url.includes('drive.google.com/file/d/') && (item.name?.toLowerCase().endsWith('.mp4') || item.name?.toLowerCase().endsWith('.mov') || item.name?.toLowerCase().endsWith('.mkv')));
            const mediaItemType = isVideo ? 'video' : 'image';

            if (mediaItemType === 'image') {
                const img = document.createElement('img');
                img.src = getDirectGoogleDriveUrl(url);
                const fallbackTitle = currentLang === 'en' ? `${type.slice(0, -1)} Title` : `Título do ${type.slice(0, -1)}`;
                img.alt = item.title || item.name || fallbackTitle;
                img.loading = "lazy";
                img.oncontextmenu = () => false; // Disable right-click for image
                itemDiv.appendChild(img);
                itemDiv.appendChild(createWatermarkElement()); // Add watermark to image items

                // Apply overlay design for both photos and designs
                const overlay = document.createElement('div');
                overlay.classList.add(`${type.slice(0, -1)}-overlay`);

                const h3 = document.createElement('h3');
                h3.textContent = item.title || item.name || fallbackTitle;

                const p = document.createElement('p');
                const fallbackDescription = currentLang === 'en' ? `${type.slice(0, -1)} Description.` : `Descrição do ${type.slice(0, -1)}.`;
                p.textContent = item.description || fallbackDescription;

                overlay.appendChild(h3);
                overlay.appendChild(p);
                itemDiv.appendChild(overlay);

                itemDiv.addEventListener('click', () => openLightbox(url, 'image', item.title || item.name, item.description));

            } else if (mediaItemType === 'video') {
                const iframe = document.createElement('iframe');
                let embedUrl = url;
                if (url.includes('youtube.com/watch?v=')) {
                    embedUrl = url.replace('watch?v=', 'embed/');
                } else if (url.includes('youtu.be/')) {
                    embedUrl = url.replace('youtu.be/', 'youtube.com/embed/');
                }
                if (embedUrl.includes('drive.google.com/file/d/')) {
                    const driveIdMatch = embedUrl.match(/(?:id=|file\/d\/)([a-zA-Z0-9_-]+)/);
                    if (driveIdMatch && driveIdMatch[1]) {
                        embedUrl = `https://drive.google.com/file/d/${driveIdMatch[1]}/preview`;
                    }
                }
                iframe.src = embedUrl;
                iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                iframe.allowFullscreen = true;
                iframe.frameBorder = "0";
                const videoFallbackTitle = currentLang === 'en' ? 'Video Title' : 'Título do Vídeo';
                iframe.title = item.name || videoFallbackTitle;
                iframe.loading = "lazy"; 
                iframe.oncontextmenu = () => false; // Disable right-click for iframe (limited effectiveness)

                itemDiv.appendChild(iframe);

                const title = document.createElement('h3');
                title.textContent = item.name || videoFallbackTitle;
                itemDiv.appendChild(title);

                itemDiv.addEventListener('click', (e) => {
                    if (e.target !== iframe) {
                        openLightbox(url, 'video', item.name, '');
                    }
                });
            }
            galleryContainer.appendChild(itemDiv);
        });

    } catch (error) {
        console.error(`Erro ao carregar ${type}:`, error);
        const errorMessage = currentLang === 'en' ? `Error loading ${type}. Please try again later.` : `Erro ao carregar ${type}. Por favor, tente novamente mais tarde.`;
        if (loadingMessageEl) {
            loadingMessageEl.textContent = errorMessage;
            loadingMessageEl.style.color = 'red';
            loadingMessageEl.style.display = 'block';
        } else {
            galleryContainer.innerHTML = `<p style="text-align: center; color: red;">${errorMessage}</p>`;
        }
    }
}

export async function loadPresentations() {
    const gallery = document.getElementById("presentation-gallery");
    if (!gallery) return;

    const currentLang = window.location.pathname.includes('/en/') ? 'en' : 'pt';
    const loadingMessage = currentLang === 'en' ? 'Loading presentations...' : 'A carregar apresentações...';
    
    gallery.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;

    try {
        const response = await fetch(WEB_APP_URL);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const presentations = data.apresentacoes || [];

        if (presentations.length === 0) {
            const noContentMessage = currentLang === 'en' ? 'No presentations found.' : 'Não foram encontradas apresentações.';
            gallery.innerHTML = `<p style='text-align: center; color: var(--light-text-color);'>${noContentMessage}</p>`;
            return;
        }

        gallery.innerHTML = ''; 

        presentations.forEach(presentation => {
            const div = document.createElement("div");
            div.className = "presentation-item";

            const title = document.createElement("h3");
            title.textContent = presentation.name;

            const iframe = document.createElement("iframe");

            let embedUrl = presentation.url;

            if (embedUrl.includes('/presentation/d/')) {
                if (embedUrl.includes('/edit')) {
                    embedUrl = embedUrl.split('/edit')[0] + '/embed?start=false&loop=false&delayms=3000';
                } else if (embedUrl.includes('/pub?')) {
                    embedUrl = embedUrl.replace('/pub?', '/embed?');
                }
            } else if (embedUrl.includes('/file/d/')) {
                const match = embedUrl.match(/file\/d\/([a-zA-Z0-9_-]+)/);
                if (match && match[1]) {
                    embedUrl = `https://drive.google.com/file/d/${match[1]}/preview`;
                }
            }
            
            iframe.src = embedUrl;
            iframe.allowFullscreen = true;
            iframe.title = presentation.name;
            iframe.loading = "lazy"; 
            iframe.oncontextmenu = () => false; // Disable right-click for iframe (limited effectiveness)

            div.appendChild(title);
            div.appendChild(iframe);

            gallery.appendChild(div);
        });
    } catch (err) {
        console.error("Erro a carregar apresentações:", err);
        const errorMessage = currentLang === 'en' ? 'Error loading presentations. Please try again later.' : 'Erro ao carregar apresentações. Por favor, tente novamente mais tarde.';
        gallery.innerHTML = `<p style='text-align: center; color: red;'>${errorMessage}</p>`;
    }
}