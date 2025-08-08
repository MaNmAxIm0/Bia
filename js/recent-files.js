import * as Tools from './ferramentas.js';
import * as Config from './configuracoes.js';
import * as Lightbox from './pop-up.js';
import { getCurrentLanguage } from './linguagem.js';

document.addEventListener('DOMContentLoaded', async () => {
    const recentHorizontalFilesContainer = document.getElementById('recent-horizontal-files');
    const recentVerticalFilesContainer = document.getElementById('recent-vertical-files');

    if (!recentHorizontalFilesContainer || !recentVerticalFilesContainer) {
        console.error('Containers for recent files not found.');
        return;
    }

    try {
        const manifestResponse = await fetch('../../r2_file_manifest.txt');
        const manifestText = await manifestResponse.text();
        const dataResponse = await fetch('../../data.json');
        const dataJson = await dataResponse.json();

        const files = manifestText.split('\n').filter(line => line.trim() !== '').map(line => {
            const parts = line.split(' ');
            const dateString = parts[0];
            const timeString = parts[1];
            const filePath = parts.slice(2).join(' ').trim();
            const timestamp = new Date(`${dateString}T${timeString}`).getTime();
            const fileName = filePath.split('/').pop().trim();
            return { timestamp, filePath, fileName };
        });

        const filteredFiles = files.filter(file => {
            const pathLower = file.filePath.toLowerCase().trim();
            
            return !pathLower.includes('powerpoints') &&
                   !pathLower.includes('melhores') &&
                   !pathLower.includes('capas') &&
                   !pathLower.endsWith('.pdf') &&
                   !pathLower.includes('thumbnails') &&
                   !pathLower.includes('apresentacoes') &&
                   !pathLower.includes('presentations');
        });

        filteredFiles.sort((a, b) => b.timestamp - a.timestamp);

        const recentHorizontalFiles = [];
        const recentVerticalFiles = [];

        for (const file of filteredFiles) {
            const fileData = dataJson[file.fileName];
            if (fileData) {
                if (fileData.orientation === 'horizontal' && recentHorizontalFiles.length < 6) {
                    recentHorizontalFiles.push({ ...file, ...fileData });
                } else if (fileData.orientation === 'vertical' && recentVerticalFiles.length < 6) {
                    recentVerticalFiles.push({ ...file, ...fileData });
                }
            }
            if (recentHorizontalFiles.length >= 6 && recentVerticalFiles.length >= 6) {
                break;
            }
        }

        const createGalleryItem = (file, isVideo) => {
            const itemDiv = document.createElement('div');
            itemDiv.classList.add(isVideo ? 'video-item' : 'photo-item');
            itemDiv.classList.add(file.orientation === 'horizontal' ? 'horizontal-gallery' : 'vertical-gallery');

            const imageContainer = document.createElement('div');
            imageContainer.classList.add('image-container');
            if (file.orientation === 'horizontal') {
                imageContainer.classList.add('horizontal-gallery');
            } else {
                imageContainer.classList.add('vertical-gallery');
            }

            const mediaElement = document.createElement('img');
            mediaElement.src = isVideo ? file.thumbnail_url : file.url;
            mediaElement.alt = file.titles[getCurrentLanguage()] || file.fileName;
            mediaElement.loading = "lazy";
            mediaElement.onerror = () => {
                mediaElement.src = `${Tools.getBasePath()}/imagens/placeholder.png`;
            };
            imageContainer.appendChild(mediaElement);

            let playIcon; // Declared here
            if (isVideo) {
                playIcon = document.createElement('i'); // Assigned here
                playIcon.className = 'fas fa-play video-play-icon';
                imageContainer.appendChild(playIcon);
            }

            const overlayDiv = document.createElement('div');
            overlayDiv.classList.add(isVideo ? 'video-overlay' : 'photo-overlay');
            const titleElement = document.createElement('h3');
            titleElement.textContent = file.titles[getCurrentLanguage()] || file.fileName; // Use getCurrentLanguage()
            overlayDiv.appendChild(titleElement);
            imageContainer.appendChild(overlayDiv);

            itemDiv.addEventListener('click', () => {
                if (isVideo) {
                    if (imageContainer.querySelector('video')) {
                        return;
                    }
                    const videoElement = document.createElement('video');
                    videoElement.src = file.url;
                    videoElement.controls = true;
                    videoElement.autoplay = true;
                    videoElement.setAttribute('playsinline', '');
                    videoElement.setAttribute('webkit-playsinline', '');
                    videoElement.setAttribute('x5-playsinline', '');
                    videoElement.addEventListener('loadedmetadata', () => {
                        const isVertical = videoElement.videoHeight > videoElement.videoWidth;
                        if (isVertical) {
                            imageContainer.classList.add('vertical-video');
                        } else {
                            imageContainer.classList.add('horizontal-video');
                        }
                    });
                    videoElement.addEventListener('ended', () => {
                        imageContainer.innerHTML = '';
                        imageContainer.appendChild(mediaElement);
                        if (playIcon) { // Check if playIcon exists before appending
                            imageContainer.appendChild(playIcon);
                        }
                        itemDiv.classList.remove('playing');
                    });
                    imageContainer.innerHTML = '';
                    imageContainer.appendChild(videoElement);
                    videoElement.focus();
                } else {
                    Lightbox.openLightbox(file.url, 'image', file.titles[getCurrentLanguage()] || file.fileName); // Use getCurrentLanguage()
                }
            });

            itemDiv.appendChild(imageContainer);

            const titleElementBottom = document.createElement('h3');
            titleElementBottom.textContent = file.titles[getCurrentLanguage()] || file.fileName; // Use getCurrentLanguage()
            itemDiv.appendChild(titleElementBottom);

            return itemDiv;
        };

        recentHorizontalFiles.forEach(file => {
            const isVideo = file.url.endsWith('.mp4');
            recentHorizontalFilesContainer.appendChild(createGalleryItem(file, isVideo));
        });

        recentVerticalFiles.forEach(file => {
            const isVideo = file.url.endsWith('.mp4');
            recentVerticalFilesContainer.appendChild(createGalleryItem(file, isVideo));
        });

    } catch (error) {
        console.error('Error loading recent files:', error);
    }
});