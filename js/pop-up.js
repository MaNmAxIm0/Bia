import { getDirectGoogleDriveUrl, createWatermarkElement } from 'ferramentas';
import { getTranslation } from 'gestor-de-linguagem'; // Import getTranslation and getCurrentLanguage from language-manager

// Lightbox variables
let currentLightbox = null;

function closeLightbox() {
    if (currentLightbox) {
        currentLightbox.classList.remove('active');
        currentLightbox.addEventListener('transitionend', function handler() {
            if (currentLightbox && currentLightbox.parentNode) { // Check if it still exists before removing
                currentLightbox.parentNode.removeChild(currentLightbox);
                currentLightbox = null;
            }
            document.removeEventListener('keydown', handleEscapeKey);
            document.body.style.overflow = ''; // Restore scrolling
            currentLightbox.removeEventListener('transitionend', handler); // Clean up self
        });
    }
}

function handleEscapeKey(e) {
    if (e.key === 'Escape') {
        closeLightbox();
    }
}

export function openLightbox(mediaUrl, mediaType, title = '', description = '') {
    // If a lightbox is already open, close it first
    if (currentLightbox) {
        closeLightbox();
    }

    const overlay = document.createElement('div');
    overlay.classList.add('lightbox-overlay');
    overlay.classList.add('active'); // Start active for transition

    const content = document.createElement('div');
    content.classList.add('lightbox-content');

    const closeBtn = document.createElement('button');
    closeBtn.classList.add('lightbox-close');
    closeBtn.innerHTML = '&times;'; // 'X' character
    
    // Determine close button label based on current page language
    const closeLabel = getTranslation('close');
    closeBtn.setAttribute('aria-label', closeLabel);
    closeBtn.addEventListener('click', closeLightbox);

    let mediaElement;
    if (mediaType === 'image') {
        mediaElement = document.createElement('img');
        mediaElement.src = getDirectGoogleDriveUrl(mediaUrl); // Apply conversion here
        const fallbackTitle = getTranslation('photo_title');
        mediaElement.alt = title || fallbackTitle;
        mediaElement.oncontextmenu = () => false; // Disable right-click for image
    } else if (mediaType === 'video') {
        mediaElement = document.createElement('iframe');
        // Ensure the URL is embedded correctly for YouTube/Vimeo
        let embedUrl = mediaUrl;
        if (mediaUrl.includes('youtube.com/watch?v=')) {
            embedUrl = mediaUrl.replace('watch?v=', 'embed/');
        } else if (mediaUrl.includes('youtu.be/')) {
            embedUrl = mediaUrl.replace('youtu.be/', 'youtube.com/embed/');
        }
        // For Google Drive videos in iframes, converting to 'preview' link is generally more reliable
        if (embedUrl.includes('drive.google.com/file/d/')) {
            const driveIdMatch = embedUrl.match(/(?:id=|file\/d\/)([a-zA-Z0-9_-]+)/);
            if (driveIdMatch && driveIdMatch[1]) {
                embedUrl = `https://drive.google.com/file/d/${driveIdMatch[1]}/preview`;
            }
        }
        mediaElement.src = embedUrl;
        mediaElement.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
        mediaElement.allowFullscreen = true;
        mediaElement.frameBorder = "0";
        const videoFallbackTitle = getTranslation('video_title');
        mediaElement.title = title || videoFallbackTitle;
        mediaElement.classList.add('lightbox-video');
        mediaElement.oncontextmenu = () => false; // Disable right-click for iframe content (may not work on all browsers/embeds)
    }

    content.appendChild(closeBtn);
    if (mediaElement) {
        content.appendChild(mediaElement);
        if (mediaType === 'image') { // Only add watermark to images
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
    document.body.style.overflow = 'hidden'; // Prevent scrolling background

    currentLightbox = overlay;

    // Close on click outside content
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closeLightbox();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', handleEscapeKey);
}