// Ficheiro: /js/principal.js (VERSÃO FINAL COMBINADA E ROBUSTA)

import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { applyTranslations, setLanguage, getCurrentLanguage, getTranslation } from './linguagem.js';

/**
 * Retorna o caminho base do repositório para funcionar no GitHub Pages.
 * @returns {string} O caminho base.
 */
function getBasePath() {
    return window.location.hostname.includes('github.io') ? '/Bia' : '';
}

/**
 * Mapeamento central de todas as páginas para navegação multilingue.
 * A chave é o nome do ficheiro em português.
 */
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
            const title = item.titles[lang] || item.titles.pt;
            const description = item.descriptions[lang] || item.descriptions.pt || '';
            slideDiv.innerHTML = `
                <img src="${item.url}" alt="${title}">
                <div class="carousel-caption">
                    <h2>${title}</h2>
                    <p>${description}</p>
                </div>
            `;
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
            const coverKey = cover.name.split('.')[0].toLowerCase().replace('ç', 'c').replace('õ', 'o');
            coverUrls[coverKey] = cover.url;
        });

        const workCardsData = [
            { pageKey: 'fotos-horizontais.html', titleKey: 'horizontal_photos_title', descKey: 'horizontal_photos_desc', coverKey: 'fotografias' },
            { pageKey: 'fotos-verticais.html', titleKey: 'vertical_photos_title', descKey: 'vertical_photos_desc', coverKey: 'fotografias' },
            { pageKey: 'videos-horizontais.html', titleKey: 'horizontal_videos_title', descKey: 'horizontal_videos_desc', coverKey: 'videos' },
            { pageKey: 'videos-verticais.html', titleKey: 'vertical_videos_title', descKey: 'vertical_videos_desc', coverKey: 'videos' },
            { pageKey: 'designs.html', titleKey: 'designs_title', descKey: 'designs_desc', coverKey: 'designs' },
            { pageKey: 'apresentacoes.html', titleKey: 'presentations_title', descKey: 'presentations_desc', coverKey: 'apresentacoes' }
        ];

        gridContainer.innerHTML = '';

        workCardsData.forEach(cardData => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'work-item';
            
            // Determina o ficheiro de destino correto com base no idioma
            const targetFile = pageMap[cardData.pageKey]?.[lang] || cardData.pageKey;
            
            // Constrói o link do cartão com o href correto
            cardDiv.innerHTML = `
                <img src="${coverUrls[cardData.coverKey] || `${getBasePath()}/imagens/placeholder.png`}" alt="${getTranslation(cardData.titleKey)}">
                <h3 data-lang-key="${cardData.titleKey}">${getTranslation(cardData.titleKey)}</h3>
                <p data-lang-key="${cardData.descKey}">${getTranslation(cardData.descKey)}</p>
                <a href="${targetFile}" class="btn" data-lang-key="view_gallery">
                    ${getTranslation('view_gallery')} <i class="fas fa-arrow-right"></i>
                </a>
            `;
            gridContainer.appendChild(cardDiv);
        });

    } catch (error) {
        console.error('Erro ao carregar os cartões de trabalho:', error);
        gridContainer.innerHTML = `<p style="color: red;">Erro ao carregar secção.</p>`;
    }
}


/**
 * Encontra o nome do ficheiro base em português, independentemente da página atual.
 * @returns {string} O nome do ficheiro em português (ex: "fotos-horizontais.html").
 */
function getSourcePageFile() {
    const currentPageFile = window.location.pathname.split('/').pop();
    if (window.location.pathname.includes('/pt/')) {
        return currentPageFile;
    }
    for (const ptFile in pageMap) {
        if (Object.values(pageMap[ptFile]).includes(currentPageFile)) {
            return ptFile;
        }
    }
    return 'index.html'; // Fallback seguro
}

/**
 * Atualiza todos os links (navegação e seletor de idioma) para o idioma atual.
 */
function updateAllLinks() {
    const lang = getCurrentLanguage();
    const sourceFile = getSourcePageFile();
    const basePath = '..'; // Caminho relativo para a pasta /html/

    // Atualiza links da navegação principal que usam data-page-key
    document.querySelectorAll('a[data-page-key]').forEach(link => {
        const pageKey = link.dataset.pageKey;
        const targetFile = pageMap[pageKey]?.[lang] || pageKey;
        link.href = `${basePath}/${lang}/${targetFile}`;
    });

    // Atualiza links do seletor de idiomas
    const ptLink = document.querySelector('.lang-pt-link');
    const enLink = document.querySelector('.lang-en-link');
    const esLink = document.querySelector('.lang-es-link');

    if (ptLink) ptLink.href = `${basePath}/pt/${sourceFile}`;
    if (enLink) enLink.href = `${basePath}/en/${pageMap[sourceFile]?.en || 'index.html'}`;
    if (esLink) esLink.href = `${basePath}/es/${pageMap[sourceFile]?.es || 'index.html'}`;
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
                document.querySelectorAll('.main-nav .dropdown.active').forEach(openDropdown => {
                    if (openDropdown !== dropdown) openDropdown.classList.remove('active');
                });
                dropdown.classList.toggle('active');
            }
        });
    });

    const sourcePageFile = getSourcePageFile();
    document.querySelectorAll('a[data-page-key]').forEach(link => {
        if (link.dataset.pageKey === sourcePageFile) {
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
    dropdown.querySelector(`.lang-option[data-lang="${currentLang}"]`)?.classList.add('active');

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
    
    const pageKey = getSourcePageFile().replace('.html', '');
    const galleryIdMap = {
        'fotos-horizontais': { id: 'photo-h-gallery', type: 'fotografias', orientation: 'horizontal' },
        'fotos-verticais':   { id: 'photo-v-gallery', type: 'fotografias', orientation: 'vertical' },
        'videos-horizontais': { id: 'video-h-gallery', type: 'videos', orientation: 'horizontal' },
        'videos-verticais':   { id: 'video-v-gallery', type: 'videos', orientation: 'vertical' },
        'designs':           { id: 'design-gallery', type: 'designs' },
        'apresentacoes':     { id: 'presentation-gallery', type: 'apresentacoes' }
    };

    const galleryInfo = galleryIdMap[pageKey];
    if (galleryInfo) {
        if (galleryInfo.type === 'apresentacoes') {
            loadPresentations();
        } else {
            loadGalleryContent(galleryInfo.type, galleryInfo.id, galleryInfo.orientation || null);
        }
    }
}

// --- EVENT LISTENERS ---
document.addEventListener('DOMContentLoaded', onPageLoad);

// Corre APENAS depois de o cabecalho.html ser injetado na página
document.addEventListener('headerLoaded', () => {
    initializeMenu();
    setupLanguageSwitcher();
    updateAllLinks(); // Agora esta função reescreve todos os links para serem corretos.
    applyTranslations(); // Aplica traduções ao cabeçalho/rodapé carregados.
});