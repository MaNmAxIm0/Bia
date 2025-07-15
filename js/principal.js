// Ficheiro: /js/principal.js

import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { applyTranslations, setLanguage, getCurrentLanguage } from './linguagem.js';

async function loadDynamicCarousel() {
    const slidesContainer = document.getElementById('dynamic-carousel-slides');
    const carouselSection = document.querySelector('.hero-carousel');
    if (!slidesContainer || !carouselSection) return;

    try {
        const basePath = window.location.hostname.includes('github.io') ? '/Bia' : '';
        const response = await fetch(`${basePath}/data.json`);
        const data = await response.json();
        const carouselItems = data.carousel || [];

        if (carouselItems.length === 0) {
            carouselSection.style.display = 'none';
            return;
        }

        const lang = getCurrentLanguage();
        slidesContainer.innerHTML = '';

        carouselItems.forEach(item => {
            const slideDiv = document.createElement('div');
            slideDiv.className = 'carousel-slide';

            const img = document.createElement('img');
            img.src = item.url;
            img.alt = item.titles[lang] || item.titles.pt;

            const captionDiv = document.createElement('div');
            captionDiv.className = 'carousel-caption';
            
            const titleH2 = document.createElement('h2');
            titleH2.textContent = item.titles[lang] || item.titles.pt;
            captionDiv.appendChild(titleH2);

            const descriptionP = document.createElement('p');
            descriptionP.textContent = item.descriptions[lang] || item.descriptions.pt || '';
            captionDiv.appendChild(descriptionP);

            slideDiv.appendChild(img);
            slideDiv.appendChild(captionDiv);
            slidesContainer.appendChild(slideDiv);
        });

        initCarousel(carouselSection);

    } catch (error) {
        console.error('Erro ao carregar dados do carrossel:', error);
        carouselSection.style.display = 'none';
    }
}

function initializeMenu() {
    // ... (função igual à anterior)
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => navLinks.classList.toggle('active'));
    }

    document.querySelectorAll('.main-nav .dropdown').forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        toggle.addEventListener('click', (event) => {
            if (window.innerWidth <= 768) {
                event.preventDefault();
                dropdown.classList.toggle('active');
            }
        });
    });

    const pageFileMap = {
        'home': { pt: 'index.html', en: 'index.html', es: 'index.html' },
        'presentations': { pt: 'apresentacoes.html', en: 'presentations.html', es: 'presentaciones.html' },
        'designs': { pt: 'designs.html', en: 'designs.html', es: 'disenos.html' },
        'horizontal_photos': { pt: 'fotos-horizontais.html', en: 'photos-horizontal.html', es: 'fotos-horizontales.html' },
        'vertical_photos': { pt: 'fotos-verticais.html', en: 'photos-vertical.html', es: 'fotos-verticales.html' },
        'horizontal_videos': { pt: 'videos-horizontais.html', en: 'videos-horizontal.html', es: 'videos-horizontales.html' },
        'vertical_videos': { pt: 'videos-verticais.html', en: 'videos-vertical.html', es: 'videos-verticales.html' },
        'about_me': { pt: 'sobre-mim.html', en: 'about-me.html', es: 'sobre-mi.html' },
        'contact': { pt: 'contactos.html', en: 'contacts.html', es: 'contactos.html' }
    };

    const currentLang = getCurrentLanguage();
    document.querySelectorAll('.main-nav > ul > li > a[data-lang-key]').forEach(link => {
        const key = link.dataset.langKey;
        if (pageFileMap[key]) link.href = pageFileMap[key][currentLang];
    });
    document.querySelectorAll('.dropdown-menu a').forEach(link => {
        const parentKey = link.closest('.dropdown').querySelector('a').dataset.langKey;
        const selfKey = link.dataset.langKey;
        const fullKey = `${selfKey}_${parentKey}`;
        if (pageFileMap[fullKey]) link.href = pageFileMap[fullKey][currentLang];
    });

    const currentPage = window.location.pathname.split('/').pop();
    document.querySelectorAll('.main-nav a').forEach(link => {
        if (link.href.endsWith(currentPage)) {
            link.classList.add('active');
            const parentDropdown = link.closest('.dropdown');
            if (parentDropdown) {
                parentDropdown.classList.add('active');
            }
        }
    });
}

function setupLanguageSwitcher() {
    // ... (função igual à anterior)
    const currentLang = getCurrentLanguage();
    const dropdown = document.querySelector('.language-dropdown');
    if (!dropdown) return;

    const selectedButton = dropdown.querySelector('.language-selected');
    const langData = {
        pt: { flag: 'fi-pt', text: 'PT' },
        en: { flag: 'fi-gb', text: 'EN' },
        es: { flag: 'fi-es', text: 'ES' }
    };
    selectedButton.querySelector('.fi').className = `fi ${langData[currentLang].flag}`;
    selectedButton.querySelector('span:not(.fi)').textContent = langData[currentLang].text;

    dropdown.querySelectorAll('.lang-option').forEach(opt => opt.classList.remove('active'));
    const activeOption = dropdown.querySelector(`.lang-option[data-lang="${currentLang}"]`);
    if (activeOption) activeOption.classList.add('active');

    const pageMap = {
        'index.html': { en: 'index.html', es: 'index.html' },
        'apresentacoes.html': { en: 'presentations.html', es: 'presentaciones.html' },
        'contactos.html': { en: 'contacts.html', es: 'contactos.html' },
        'designs.html': { en: 'designs.html', es: 'disenos.html' },
        'fotos-horizontais.html': { en: 'photos-horizontal.html', es: 'fotos-horizontales.html' },
        'fotos-verticais.html': { en: 'photos-vertical.html', es: 'fotos-verticales.html' },
        'sobre-mim.html': { en: 'about-me.html', es: 'sobre-mi.html' },
        'videos-horizontais.html': { en: 'videos-horizontal.html', es: 'videos-horizontales.html' },
        'videos-verticais.html': { en: 'videos-vertical.html', es: 'videos-verticales.html' }
    };
    const currentPageFile = window.location.pathname.split('/').pop();
    let sourceFile = 'index.html';
    if (currentLang === 'pt') {
        sourceFile = currentPageFile;
    } else {
        for (const ptFile in pageMap) {
            if (Object.values(pageMap[ptFile]).includes(currentPageFile)) {
                sourceFile = ptFile;
                break;
            }
        }
    }
    document.querySelector('.lang-pt-link').href = `../pt/${sourceFile}`;
    document.querySelector('.lang-en-link').href = `../en/${pageMap[sourceFile]?.en || 'index.html'}`;
    document.querySelector('.lang-es-link').href = `../es/${pageMap[sourceFile]?.es || 'index.html'}`;

    selectedButton.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    });
    document.addEventListener('click', () => dropdown.classList.remove('open'));
}

function onPageLoad() {
    // ... (função igual à anterior)
    const pathLang = window.location.pathname.split('/')[2] || 'pt';
    setLanguage(pathLang);
    applyTranslations();

    if (window.location.pathname.endsWith('index.html')) {
        loadDynamicCarousel();
    }

    const pageKey = window.location.pathname.split('/').pop().replace('.html', '');
    const galleryIdMap = {
        'fotos-horizontais': 'photo-h-gallery', 'photos-horizontal': 'photo-h-gallery', 'fotos-horizontales': 'photo-h-gallery',
        'fotos-verticais': 'photo-v-gallery', 'photos-vertical': 'photo-v-gallery', 'fotos-verticales': 'photo-v-gallery',
        'videos-horizontais': 'video-h-gallery', 'videos-horizontal': 'video-h-gallery', 'videos-horizontales': 'video-h-gallery',
        'videos-verticais': 'video-v-gallery', 'videos-vertical': 'video-v-gallery', 'videos-verticales': 'video-v-gallery',
        'designs': 'design-gallery', 'disenos': 'design-gallery',
        'apresentacoes': 'presentation-gallery', 'presentations': 'presentation-gallery', 'presentaciones': 'presentation-gallery'
    };
    const galleryId = galleryIdMap[pageKey];
    if (galleryId) {
        const typeMap = { photo: 'fotografias', video: 'videos', design: 'designs', presentation: 'apresentacoes' };
        const galleryType = typeMap[galleryId.split('-')[0]];
        if (galleryType === 'apresentacoes') {
            loadPresentations();
        } else {
            const orientation = galleryId.includes('-h-') ? 'horizontal' : (galleryId.includes('-v-') ? 'vertical' : null);
            loadGalleryContent(galleryType, galleryId, orientation);
        }
    }
}

document.addEventListener('DOMContentLoaded', onPageLoad);
document.addEventListener('headerLoaded', () => {
    initializeMenu();
    setupLanguageSwitcher();
    applyTranslations();
});
