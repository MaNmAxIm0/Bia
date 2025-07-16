// Ficheiro: /js/principal.js (VERSÃO CORRIGIDA E COMPLETA)

import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { applyTranslations, setLanguage, getCurrentLanguage, getTranslation } from './linguagem.js';

/**
 * Retorna o caminho base do repositório para funcionar no GitHub Pages.
 * @returns {string} O caminho base.
 */
function getBasePath() {
    // A verificação 'Bia' torna o site funcional tanto localmente como no GitHub Pages.
    return window.location.pathname.startsWith('/Bia/') ? '/Bia' : '';
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

        const workCardsData = [
            { ptFile: 'fotos-horizontais.html', titleKey: 'horizontal_photos_title', descKey: 'horizontal_photos_desc', coverKey: 'fotografias' },
            { ptFile: 'fotos-verticais.html', titleKey: 'vertical_photos_title', descKey: 'vertical_photos_desc', coverKey: 'fotografias' },
            { ptFile: 'videos-horizontais.html', titleKey: 'horizontal_videos_title', descKey: 'horizontal_videos_desc', coverKey: 'videos' },
            { ptFile: 'videos-verticais.html', titleKey: 'vertical_videos_title', descKey: 'vertical_videos_desc', coverKey: 'videos' },
            { ptFile: 'designs.html', titleKey: 'designs_title', descKey: 'designs_desc', coverKey: 'designs' },
            { ptFile: 'apresentacoes.html', titleKey: 'presentations_title', descKey: 'presentations_desc', coverKey: 'apresentacoes' }
        ];

        gridContainer.innerHTML = '';

        workCardsData.forEach(cardData => {
            const cardDiv = document.createElement('div');
            cardDiv.className = 'work-item';
            
            const targetFile = pageMap[cardData.ptFile]?.[lang] || cardData.ptFile;

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
    // Se já estamos numa página 'pt', o nome do ficheiro é a fonte
    if (window.location.pathname.includes('/pt/')) {
        return currentPageFile;
    }
    // Caso contrário, procura no pageMap para encontrar a chave (ficheiro 'pt')
    for (const ptFile in pageMap) {
        if (Object.values(pageMap[ptFile]).includes(currentPageFile)) {
            return ptFile;
        }
    }
    return 'index.html'; // Fallback seguro
}


/**
 * Atualiza todos os links de navegação para o idioma atual.
 */
function updateAllNavLinks() {
    const lang = getCurrentLanguage();
    const basePath = `..`; // Navega para a raiz de /html/ a partir de /pt/, /en/, etc.

    document.querySelectorAll('.main-nav a[href]').forEach(link => {
        // Encontra o ficheiro de destino original em português
        const originalHref = link.getAttribute('href').split('/').pop();
        const sourceFile = getSourcePageFileFromLink(originalHref);
        
        // Encontra o nome do ficheiro traduzido
        const targetFile = pageMap[sourceFile]?.[lang] || sourceFile;
        
        // Constrói o novo URL completo e atualiza o link
        link.href = `${basePath}/${lang}/${targetFile}`;
    });
}

/**
 * Função auxiliar para encontrar o ficheiro PT de um link.
 * @param {string} linkFile - O nome do ficheiro do link (e.g., "photos-horizontal.html")
 * @returns {string} - O nome do ficheiro base em PT.
 */
function getSourcePageFileFromLink(linkFile) {
    for (const ptFile in pageMap) {
        if (ptFile === linkFile || Object.values(pageMap[ptFile]).includes(linkFile)) {
            return ptFile;
        }
    }
    return linkFile; // Retorna o original se não encontrar
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
                // Fecha outros dropdowns abertos para uma melhor experiência mobile
                document.querySelectorAll('.main-nav .dropdown.active').forEach(openDropdown => {
                    if (openDropdown !== dropdown) {
                        openDropdown.classList.remove('active');
                    }
                });
                dropdown.classList.toggle('active');
            }
        });
    });

    // Destaca o link da página atual
    const sourcePageFile = getSourcePageFile();
    document.querySelectorAll('.main-nav a').forEach(link => {
        const linkSourceFile = getSourcePageFileFromLink(link.href.split('/').pop());
        if (linkSourceFile === sourcePageFile) {
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

    // Atualiza o botão do seletor
    const selectedButton = dropdown.querySelector('.language-selected');
    const langData = {
        pt: { flag: 'fi-pt', text: 'PT' },
        en: { flag: 'fi-gb', text: 'EN' },
        es: { flag: 'fi-es', text: 'ES' }
    };
    selectedButton.querySelector('.fi').className = `fi ${langData[currentLang].flag}`;
    selectedButton.querySelector('span:not(.fi)').textContent = langData[currentLang].text;

    // Marca a opção ativa no menu dropdown
    dropdown.querySelectorAll('.lang-option').forEach(opt => opt.classList.remove('active'));
    const activeOption = dropdown.querySelector(`.lang-option[data-lang="${currentLang}"]`);
    if (activeOption) activeOption.classList.add('active');

    // ** LÓGICA CORRIGIDA PARA OS LINKS DO SELETOR **
    const sourceFile = getSourcePageFile();
    const basePath = `..`; // Caminho relativo para a pasta /html/

    document.querySelector('.lang-pt-link').href = `${basePath}/pt/${sourceFile}`;
    document.querySelector('.lang-en-link').href = `${basePath}/en/${pageMap[sourceFile]?.en || 'index.html'}`;
    document.querySelector('.lang-es-link').href = `${basePath}/es/${pageMap[sourceFile]?.es || 'index.html'}`;

    // Lógica para abrir/fechar o dropdown
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
    // Determina o idioma com base no URL
    const pathLang = window.location.pathname.split('/')[2] || 'pt';
    setLanguage(pathLang);
    
    // Aplica as traduções a todo o texto estático
    applyTranslations();

    // Carrega conteúdo dinâmico específico da página
    if (window.location.pathname.endsWith('index.html')) {
        loadDynamicCarousel();
        loadWorkCards();
    }
    
    // Mapeamento de ficheiros para galerias
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

// Corre quando o DOM inicial está pronto
document.addEventListener('DOMContentLoaded', onPageLoad);

// Corre APENAS depois de o cabecalho.html ser injetado na página
document.addEventListener('headerLoaded', () => {
    updateAllNavLinks(); // **NOVO: Atualiza os links da navegação principal**
    initializeMenu();
    setupLanguageSwitcher();
    applyTranslations(); // Aplica traduções ao cabeçalho/rodapé carregados
});