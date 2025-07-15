// Ficheiro: /js/principal.js (VERSÃO COMPLETA E VERIFICADA)

import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { applyTranslations, setLanguage, getCurrentLanguage } from './linguagem.js';

/**
 * Retorna o caminho base do repositório para funcionar no GitHub Pages.
 * @returns {string} '/Bia' ou uma string vazia.
 */
function getBasePath() {
    return window.location.hostname.includes('github.io') ? '/Bia' : '';
}

/**
 * Carrega e constrói o carrossel dinâmico a partir do data.json.
 */
async function loadDynamicCarousel() {
    const slidesContainer = document.getElementById('dynamic-carousel-slides');
    const carouselSection = document.querySelector('.hero-carousel');
    if (!slidesContainer || !carouselSection) return;

    try {
        const response = await fetch(`${getBasePath()}/data.json`);
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

/**
 * Carrega e constrói os cartões de trabalho na página inicial a partir do data.json.
 */
async function loadWorkCards() {
    const gridContainer = document.getElementById('my-works-grid');
    if (!gridContainer) return;

    try {
        const response = await fetch(`${getBasePath()}/data.json`);
        const data = await response.json();
        const covers = data.covers || [];
        const lang = getCurrentLanguage();

        const coverUrls = {};
        covers.forEach(cover => {
            const coverKey = cover.name.split('.')[0].toLowerCase();
            coverUrls[coverKey] = cover.url;
        });

        const workCards = [
            { key: 'horizontal_photos', coverKey: 'fotografias', link: 'fotos-horizontais.html' },
            { key: 'vertical_photos', coverKey: 'fotografias', link: 'fotos-verticais.html' },
            { key: 'horizontal_videos', coverKey: 'videos', link: 'videos-horizontais.html' },
            { key: 'vertical_videos', coverKey: 'videos', link: 'videos-verticais.html' },
            { key: 'designs', coverKey: 'designs', link: 'designs.html' },
            { key: 'presentations', coverKey: 'apresentacoes', link: 'apresentacoes.html' }
        ];

        gridContainer.innerHTML = '';

        workCards.forEach(card => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'work-item';

            const img = document.createElement('img');
            img.src = coverUrls[card.coverKey] || `${getBasePath()}/imagens/placeholder.png`;
            img.alt = getTranslation(`${card.key}_title`);

            const title = document.createElement('h3');
            title.dataset.langKey = `${card.key}_title`;
            title.textContent = getTranslation(`${card.key}_title`);

            const description = document.createElement('p');
            description.dataset.langKey = `${card.key}_desc`;
            description.textContent = getTranslation(`${card.key}_desc`);

            const link = document.createElement('a');
            link.href = card.link;
            link.className = 'btn';
            link.dataset.langKey = 'view_gallery';
            link.innerHTML = `${getTranslation('view_gallery')} <i class="fas fa-arrow-right"></i>`;

            cardDiv.appendChild(img);
            cardDiv.appendChild(title);
            cardDiv.appendChild(description);
            cardDiv.appendChild(link);
            gridContainer.appendChild(cardDiv);
        });

    } catch (error) {
        console.error('Erro ao carregar os cartões de trabalho:', error);
        gridContainer.innerHTML = `<p style="color: red;">Erro ao carregar secção.</p>`;
    }
}

/**
 * Inicializa a navegação, incluindo menus e links ativos.
 */
function initializeMenu() {
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

/**
 * Configura o seletor de idiomas, atualizando links e a bandeira/texto visível.
 */
function setupLanguageSwitcher() {
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

/**
 * Função principal que orquestra o carregamento da página.
 */
function onPageLoad() {
    const pathLang = window.location.pathname.split('/')[2] || 'pt';
    setLanguage(pathLang);
    applyTranslations();

    if (window.location.pathname.endsWith('index.html')) {
        loadDynamicCarousel();
        loadWorkCards();
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

// --- EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', onPageLoad);

document.addEventListener('headerLoaded', () => {
    initializeMenu();
    setupLanguageSwitcher();
    applyTranslations();
});
