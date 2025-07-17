// ==========================================================================
// FICHEIRO PRINCIPAL (VERSÃO FINAL COM BASE NO SEU FICHEIRO)
// Corrige os links do cabeçalho e mantém as funções de carregamento de conteúdo.
// ==========================================================================

import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { setLanguage, getCurrentLanguage, getTranslation, applyTranslations } from './linguagem.js';

// --- FUNÇÕES AUXILIARES E DE NAVEGAÇÃO ---

function getBasePath() {
    return window.location.hostname.includes('github.io') ? '/Bia' : '';
}

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

function getSourcePageFile() {
    const currentPageFile = window.location.pathname.split('/').pop();
    if (window.location.pathname.includes('/pt/')) return currentPageFile;
    for (const ptFile in pageMap) {
        if (Object.values(pageMap[ptFile]).includes(currentPageFile)) return ptFile;
    }
    return 'index.html';
}

// --- FUNÇÕES DE CARREGAMENTO DE CONTEÚDO DINÂMICO (DO SEU FICHEIRO) ---

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

        slidesContainer.innerHTML = '';
        carouselItems.forEach(item => {
            const slideDiv = document.createElement('div');
            slideDiv.className = 'carousel-slide';
            const title = item.titles[getCurrentLanguage()] || item.titles.pt;
            const description = item.descriptions?.[getCurrentLanguage()] || item.descriptions?.pt || '';
            slideDiv.innerHTML = `
                <img src="${item.url}" alt="${title}" loading="lazy">
                <div class="carousel-caption"><h2>${title}</h2><p>${description}</p></div>`;
            slidesContainer.appendChild(slideDiv);
        });
        initCarousel(carouselSection);
    } catch (error) {
        console.error('Erro ao carregar dados do carrossel:', error);
        carouselSection.style.display = 'none';
    }
}

async function loadWorkCards() {
    const gridContainer = document.getElementById('my-works-grid');
    if (!gridContainer) return;
    gridContainer.innerHTML = `<p style="text-align: center;">${getTranslation('loading_content')}</p>`;

    try {
        const response = await fetch(`${getBasePath()}/data.json`);
        const data = await response.json();
        const covers = data.covers || [];

        const workCardsData = [
            { pageKey: 'fotos-horizontais.html', titleKey: 'horizontal_photos_title', descKey: 'horizontal_photos_desc', coverKey: 'fotografias' },
            { pageKey: 'fotos-verticais.html', titleKey: 'vertical_photos_title', descKey: 'vertical_photos_desc', coverKey: 'fotografias' },
            { pageKey: 'videos-horizontais.html', titleKey: 'horizontal_videos_title', descKey: 'horizontal_videos_desc', coverKey: 'vídeos' },
            { pageKey: 'videos-verticais.html', titleKey: 'vertical_videos_title', descKey: 'vertical_videos_desc', coverKey: 'vídeos' },
            { pageKey: 'designs.html', titleKey: 'designs_title', descKey: 'designs_desc', coverKey: 'designs' },
            { pageKey: 'apresentacoes.html', titleKey: 'presentations_title', descKey: 'presentations_desc', coverKey: 'apresentações' }
        ];

        gridContainer.innerHTML = '';
        workCardsData.forEach(cardData => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'work-item';
            const cover = covers.find(c => c.name.toLowerCase().includes(cardData.coverKey));
            const coverUrl = cover ? cover.url : `${getBasePath()}/imagens/placeholder.png`;
            const targetFile = pageMap[cardData.pageKey]?.[getCurrentLanguage()] || cardData.pageKey;

            cardDiv.innerHTML = `
                <img src="${coverUrl}" alt="${getTranslation(cardData.titleKey)}">
                <h3>${getTranslation(cardData.titleKey)}</h3>
                <p>${getTranslation(cardData.descKey)}</p>
                <a href="${targetFile}" class="btn">${getTranslation('view_gallery')} <i class="fas fa-arrow-right"></i></a>`;
            gridContainer.appendChild(cardDiv);
        });
    } catch (error) {
        console.error('Erro ao carregar os cartões de trabalho:', error);
    }
}

async function loadPagePreviews() {
    const previewContainer = document.querySelector('.section-preview-grid');
    if (!previewContainer) return;
    try {
        const response = await fetch(`${getBasePath()}/data.json`);
        const data = await response.json();
        const covers = data.covers || [];

        const aboutMeImg = previewContainer.querySelector('a[href="sobre-mim.html"] img');
        const contactImg = previewContainer.querySelector('a[href="contactos.html"] img');
        
        const aboutCover = covers.find(c => c.name.toLowerCase().includes('sobre mim'));
        const contactCover = covers.find(c => c.name.toLowerCase().includes('contactos'));

        if (aboutMeImg && aboutCover) aboutMeImg.src = aboutCover.url;
        if (contactImg && contactCover) contactImg.src = contactCover.url;
    } catch (error) {
        console.error("Erro ao carregar imagens de preview:", error);
    }
}


// --- FUNÇÕES DE INICIALIZAÇÃO DE PÁGINA E EVENTOS ---

function setupHeader() {
    // --- Lógica do Menu ---
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    if (menuToggle) menuToggle.addEventListener('click', () => navLinks.classList.toggle('active'));

    document.querySelectorAll('.main-nav .dropdown > a').forEach(toggle => {
        toggle.addEventListener('click', (event) => {
            if (window.innerWidth <= 768) {
                event.preventDefault();
                toggle.parentElement.classList.toggle('active');
            }
        });
    });

    // --- Lógica do Seletor de Idioma ---
    const dropdown = document.querySelector('.language-dropdown');
    if (!dropdown) return;

    const selectedButton = dropdown.querySelector('.language-selected');
    const lang = getCurrentLanguage();
    const langData = { pt: { flag: 'pt', text: 'PT' }, en: { flag: 'gb', text: 'EN' }, es: { flag: 'es', text: 'ES' } };

    selectedButton.querySelector('.fi').className = `fi fi-${langData[lang].flag}`;
    selectedButton.querySelector('span:not(.fi)').textContent = langData[lang].text;

    selectedButton.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('open');
    });
    document.addEventListener('click', () => dropdown.classList.remove('open'));

    // --- CORREÇÃO DOS LINKS ---
    const sourceFile = getSourcePageFile();

    // 1. Atualiza os links de navegação principais (ex: Sobre Mim, Designs)
    document.querySelectorAll('a[data-page-key]').forEach(link => {
        const pageKey = link.dataset.pageKey;
        const targetFile = pageMap[pageKey]?.[lang] || pageKey;
        link.href = `../${lang}/${targetFile}`; // Constrói o link correto
    });
    
    // 2. Atualiza os links dentro do seletor de idiomas
    document.querySelectorAll('.lang-option').forEach(link => {
        const linkLang = link.dataset.lang;
        const targetFile = pageMap[sourceFile]?.[linkLang] || sourceFile;
        link.href = `../${linkLang}/${targetFile}`;
        if (linkLang === lang) link.classList.add('active');
    });

    // 3. Destaca o link da página atual no menu
    document.querySelectorAll('a[data-page-key]').forEach(link => {
        if (link.dataset.pageKey === sourceFile) {
            link.classList.add('active');
            const parentDropdown = link.closest('.dropdown');
            if (parentDropdown) parentDropdown.classList.add('active');
        }
    });
}

function onPageLoad() {
    const pathLang = window.location.pathname.split('/')[2] || 'pt';
    setLanguage(pathLang);
    applyTranslations();

    // Condicional para só executar na página inicial
    if (document.querySelector('.hero-carousel')) {
        loadDynamicCarousel();
        loadWorkCards();
        loadPagePreviews();
    }

    const galleryIdMap = {
        'fotos-horizontais': { id: 'photo-h-gallery', type: 'fotografias', orientation: 'horizontal' },
        'fotos-verticais': { id: 'photo-v-gallery', type: 'fotografias', orientation: 'vertical' },
        'videos-horizontais': { id: 'video-h-gallery', type: 'videos', orientation: 'horizontal' },
        'videos-verticais': { id: 'video-v-gallery', type: 'videos', orientation: 'vertical' },
        'designs': { id: 'design-gallery', type: 'designs' },
        'apresentacoes': { id: 'presentation-gallery', type: 'apresentacoes' }
    };
    const pageKey = getSourcePageFile().replace('.html', '');
    const galleryInfo = galleryIdMap[pageKey];
    if (galleryInfo) {
        if (galleryInfo.type === 'apresentacoes') loadPresentations();
        else loadGalleryContent(galleryInfo.type, galleryInfo.id, galleryInfo.orientation || null);
    }
}

// --- INICIALIZAÇÃO GERAL ---
document.addEventListener('DOMContentLoaded', onPageLoad);

// Observador para configurar o cabeçalho assim que ele for injetado
const observer = new MutationObserver((mutations, obs) => {
    const header = document.querySelector('.main-header');
    if (header) {
        setupHeader(); // Chama a função única que configura tudo no cabeçalho
        applyTranslations(); // Garante que o conteúdo injetado também é traduzido
        obs.disconnect(); // Para de observar depois de o trabalho estar feito
    }
});
observer.observe(document.body, { childList: true, subtree: true });