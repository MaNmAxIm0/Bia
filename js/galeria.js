import { WEB_APP_URL } from './configuracoes.js';
import { getDirectGoogleDriveUrl, createWatermarkElement } from 'ferramentas';
import { openLightbox } from 'lightbox';
import { getTranslation } from 'gestor-de-linguagem';

export async function loadGalleryContent(type, containerId) {
    console.log(`galeria.js: loadGalleryContent called for type: ${type}, containerId: ${containerId}`);
    const galleryContainer = document.getElementById(containerId);
    if (!galleryContainer) {
        console.error(`galeria.js: Gallery container with ID '${containerId}' not found on this page.`);
        return;
    }

    const loadingMessage = getTranslation('loading_content');
    
    galleryContainer.innerHTML = `<p id="loadingMessage" style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;
    const loadingMessageEl = galleryContainer.querySelector('#loadingMessage');

    try {
        console.log(`galeria.js: Fetching data from ${WEB_APP_URL}`);
        const response = await fetch(WEB_APP_URL);
        if (!response.ok) {
            console.error(`galeria.js: HTTP error! status: ${response.status} for ${WEB_APP_URL}`);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log(`galeria.js: Data received for ${type}:`, data);
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
            const noContentMessage = getTranslation('no_content_found', {type: getTranslation(type)});
            galleryContainer.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${noContentMessage}</p>`;
            console.warn(`galeria.js: No items found for type: ${type}.`);
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
                const fallbackTitle = getTranslation(`${type.slice(0, -1)}_title`);
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
                const fallbackDescription = getTranslation(`${type.slice(0, -1)}_description`);
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
                const videoFallbackTitle = getTranslation('video_title');
                iframe.title = item.name || videoFallbackTitle;
                iframe.loading = "lazy"; 
                iframe.oncontextmenu = () => false; // Disable right-click for iframe (limited effectiveness)

                itemDiv.appendChild(iframe);

                const title = document.createElement('h3');
                title.textContent = item.name || videoFallbackTitle;
                itemDiv.appendChild(title);

                itemDiv.addEventListener('click', (e) => {
                    // Prevent lightbox opening if the click originated from within the iframe (which is hard to reliably detect cross-origin)
                    // The main goal is to open lightbox on itemDiv click, but if the iframe is clicked, its default behavior should take precedence.
                    // However, due to security restrictions, clicking an iframe's content often doesn't bubble up.
                    // A simple check if the click target is the iframe itself might be sufficient for preventing double action.
                    if (e.target !== iframe) {
                        openLightbox(url, 'video', item.name, '');
                    }
                });
            }
            galleryContainer.appendChild(itemDiv);
        });

    } catch (error) {
        console.error(`galeria.js: Error loading ${type}:`, error);
        const errorMessage = getTranslation('error_loading_content', {type: getTranslation(type)});
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
    console.log("galeria.js: loadPresentations called.");
    const gallery = document.getElementById("presentation-gallery");
    if (!gallery) {
        console.error("galeria.js: Presentation gallery container not found on this page.");
        return;
    }

    const loadingMessage = getTranslation('loading_presentations');
    
    gallery.innerHTML = `<p style="text-align: center; color: var(--light-text-color);">${loadingMessage}</p>`;

    try {
        console.log(`galeria.js: Fetching presentations from ${WEB_APP_URL}`);
        const response = await fetch(WEB_APP_URL);
        if (!response.ok) {
            console.error(`galeria.js: HTTP error! status: ${response.status} for ${WEB_APP_URL}`);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("galeria.js: Data received for presentations:", data);
        const presentations = data.apresentacoes || [];

        if (presentations.length === 0) {
            const noContentMessage = getTranslation('no_presentations_found');
            gallery.innerHTML = `<p style='text-align: center; color: var(--light-text-color);'>${noContentMessage}</p>`;
            console.warn("galeria.js: No presentations found.");
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
        console.error("galeria.js: Error loading presentations:", err);
        const errorMessage = getTranslation('error_loading_content', {type: getTranslation('presentations')});
        gallery.innerHTML = `<p style='text-align: center; color: red;'>${errorMessage}</p>`;
    }
}