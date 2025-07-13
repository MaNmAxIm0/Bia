import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { applyTranslations } from './linguagem.js';

// --- FUNÇÕES GLOBAIS PARA O INJETOR DE HTML ---

/**
 * Inicializa o menu de navegação, incluindo o botão "hamburger" e os dropdowns.
 */
window.initializeMenu = function() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    // Lógica para o botão "hamburger"
    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
        });
    }
  
    // Lógica para os dropdowns do menu principal (Fotografias, Vídeos)
    document.querySelectorAll('.main-nav .dropdown').forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        
        toggle.addEventListener('click', function(event) {
            // Em mobile, previne a navegação e abre/fecha o submenu
            if (window.innerWidth <= 768) {
                event.preventDefault();
                // Fecha outros dropdowns abertos para uma melhor experiência
                document.querySelectorAll('.main-nav .dropdown.active').forEach(openDropdown => {
                    if (openDropdown !== dropdown) {
                        openDropdown.classList.remove('active');
                    }
                });
                dropdown.classList.toggle('active');
            }
        });
    });

    // Lógica para destacar o link ativo (simplificada)
    const currentPath = window.location.pathname;
    document.querySelectorAll('.main-nav a').forEach(link => {
        if (link.href.endsWith(currentPath)) {
            link.classList.add('active');
            // Se o link ativo estiver dentro de um dropdown, ativa o dropdown pai
            if (link.closest('.dropdown')) {
                link.closest('.dropdown').classList.add('active');
            }
        }
    });
};

/**
 * Controla a abertura e fecho do novo dropdown de idiomas.
 */
function initializeLanguageDropdown() {
    const dropdown = document.querySelector('.language-dropdown');
    if (!dropdown) return;

    const selected = dropdown.querySelector('.language-selected');

    selected.addEventListener('click', (event) => {
        event.stopPropagation(); // Impede que o clique no botão feche o menu imediatamente
        dropdown.classList.toggle('open');
    });

    // Fecha o menu se o utilizador clicar em qualquer outro lugar na página
    document.addEventListener('click', () => {
        if (dropdown.classList.contains('open')) {
            dropdown.classList.remove('open');
        }
    });
}

/**
 * Configura os links de navegação entre os diferentes idiomas (PT, EN, ES).
 * @param {string} currentLang - O idioma da página atual ('pt', 'en', ou 'es').
 */
window.setupLanguageSwitcher = function(currentLang) {
    // Mapeamento de nomes de ficheiros entre idiomas
    const pageMap = {
        // PT -> EN
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

    // Função para encontrar a página de origem com base na página atual
    const findSourceFile = (targetLang) => {
        for (const ptFile in pageMap) {
            if (pageMap[ptFile][targetLang] === currentPageFile) {
                return ptFile;
            }
        }
        return 'index.html'; // Fallback
    };

    let sourceFile = 'index.html';
    if (currentLang === 'pt') {
        sourceFile = currentPageFile;
    } else {
        sourceFile = findSourceFile(currentLang);
    }

    // Configurar links
    const linkPt = document.querySelector('.lang-pt-link');
    if (linkPt) linkPt.href = `../pt/${sourceFile}`;

    const linkEn = document.querySelector('.lang-en-link');
    if (linkEn) linkEn.href = `../en/${pageMap[sourceFile]?.en || 'index.html'}`;

    const linkEs = document.querySelector('.lang-es-link');
    if (linkEs) linkEs.href = `../es/${pageMap[sourceFile]?.es || 'index.html'}`;

    // Inicializa o comportamento de clique do dropdown de idiomas
    initializeLanguageDropdown();
};


// --- FUNÇÃO PRINCIPAL PARA O CONTEÚDO DA PÁGINA ---
function initializePageContent() {
    // Inicializa o carrossel na página inicial
    const carouselElement = document.querySelector('.hero-carousel');
    if (carouselElement) {
        initCarousel(carouselElement);
    }

    // Carrega o conteúdo dinâmico da galeria com base na página atual
    const currentPathname = window.location.pathname;

    if (currentPathname.includes('fotos-horizontais') || currentPathname.includes('photos-horizontal') || currentPathname.includes('fotos-horizontales')) {
        loadGalleryContent('fotografias', 'photo-h-gallery', 'horizontal');
    } else if (currentPathname.includes('fotos-verticais') || currentPathname.includes('photos-vertical') || currentPathname.includes('fotos-verticales')) {
        loadGalleryContent('fotografias', 'photo-v-gallery', 'vertical');
    } else if (currentPathname.includes('videos-horizontais') || currentPathname.includes('videos-horizontal') || currentPathname.includes('videos-horizontales')) {
        loadGalleryContent('videos', 'video-h-gallery', 'horizontal');
    } else if (currentPathname.includes('videos-verticais') || currentPathname.includes('videos-vertical') || currentPathname.includes('videos-verticales')) {
        loadGalleryContent('videos', 'video-v-gallery', 'vertical');
    } else if (currentPathname.includes('designs') || currentPathname.includes('disenos')) {
        loadGalleryContent('designs', 'design-gallery');
    } else if (currentPathname.includes('apresentacoes') || currentPathname.includes('presentations') || currentPathname.includes('presentaciones')) {
        loadPresentations();
    }

    // Aplica as traduções a todos os elementos da página
    applyTranslations();
}

// Event listener que executa quando o DOM inicial está carregado
document.addEventListener('DOMContentLoaded', initializePageContent);
