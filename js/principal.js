import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { setLanguage, getCurrentLanguage, getTranslation, applyTranslations } from './linguagem.js';
function getBasePath() {
  return window.location.hostname.includes('github.io') ? '/Bia' : '';
}
const pageMap = {
  'inicio': { pt: 'inicio', en: 'home', es: 'inicio' },
  'apresentacoes': { pt: 'apresentacoes', en: 'presentations', es: 'presentaciones' },
  'contactos': { pt: 'contactos', en: 'contacts', es: 'contactos' },
  'designs': { pt: 'designs', en: 'designs', es: 'disenos' },
  'fotos-horizontais': { pt: 'fotos-horizontais', en: 'photos-horizontal', es: 'fotos-horizontales' },
  'fotos-verticais': { pt: 'fotos-verticais', en: 'photos-vertical', es: 'fotos-verticales' },
  'sobre-mim': { pt: 'sobre-mim', en: 'about-me', es: 'sobre-mi' },
  'politica-de-privacidade': { pt: 'politica-de-privacidade', en: 'privacy-policy', es: 'politica-de-privacidad' },
  'videos-horizontais': { pt: 'videos-horizontais', en: 'videos-horizontal', es: 'videos-horizontales' },
  'termos-de-utilizacao': { pt: 'termos-de-utilizacao', en: 'terms-of-use', es: 'terminos-de-uso' },
  'videos-verticais': { pt: 'videos-verticais', en: 'videos-vertical', es: 'videos-verticales' }
};
function getSourcePageFile() {
  const pathSegments = window.location.pathname.split("/").filter(segment => segment !== "");
  const lang = pathSegments.find(seg => ["pt", "en", "es"].includes(seg));
  let pageName = pathSegments[pathSegments.indexOf(lang) + 1];
  if (!pageName) return "inicio"; // Default to 'inicio' if no page name is found
  
  // Find the original pageKey from pageMap based on the current language and pageName
  for (const ptPage in pageMap) {
    if (pageMap[ptPage][lang] === pageName) {
      return ptPage;
    }
  }
  return "inicio"; // Default to 'inicio' if not found in pageMap
}
async function loadDynamicCarousel() {
  const slidesContainer = document.getElementById('dynamic-carousel-slides');
  const carouselSection = document.querySelector('.hero-carousel');
  if (!slidesContainer || !carouselSection) return;
  try {
    const response = await fetch(`${getBasePath()}/data.json`);
    if (!response.ok) throw new Error('Failed to fetch carousel data');
    const data = await response.json();
    const carouselItems = Object.values(data).filter(item => item.url && item.url.includes('/Melhores/'));
    if (carouselItems.length === 0) {
      carouselSection.style.display = 'none';
      return;
    }
    slidesContainer.innerHTML = '';
    const lang = getCurrentLanguage();
    carouselItems.forEach(item => {
      const slideDiv = document.createElement('div');
      slideDiv.className = 'carousel-slide';
      const title = item.titles?.[lang] || item.titles?.pt || '';
      const description = item.descriptions?.[lang] || item.descriptions?.pt || '';
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
    if (!response.ok) throw new Error('Failed to fetch work cards data');
    const data = await response.json();
    const covers = Object.values(data).filter(item => item.url && item.url.includes('/Capas/'));
    const workCardsData = [
    { pageKey: 'fotos-horizontais', titleKey: 'horizontal_photos_title', descKey: 'horizontal_photos_desc', coverKey: 'Fotografias Horizontais' },
    { pageKey: 'fotos-verticais', titleKey: 'vertical_photos_title', descKey: 'vertical_photos_desc', coverKey: 'Fotografias Verticais' },
    { pageKey: 'videos-horizontais', titleKey: 'horizontal_videos_title', descKey: 'horizontal_videos_desc', coverKey: 'Vídeos Horizontais' },
    { pageKey: 'videos-verticais', titleKey: 'vertical_videos_title', descKey: 'vertical_videos_desc', coverKey: 'Vídeos Verticais' },
    { pageKey: 'designs', titleKey: 'designs_title', descKey: 'designs_desc', coverKey: 'designs' },
    { pageKey: 'apresentacoes', titleKey: 'presentations_title', descKey: 'presentations_desc', coverKey: 'apresentações' }
    ];
    gridContainer.innerHTML = '';
        workCardsData.forEach(cardData => {
      const cardDiv = document.createElement('div');
      cardDiv.className = 'work-item';
      const cover = covers.find(c => c.titles.pt.toLowerCase() === cardData.coverKey.toLowerCase());
      const coverUrl = cover ? cover.url : `${getBasePath()}/imagens/placeholder.png`;
      const targetFile = pageMap[cardData.pageKey]?.[getCurrentLanguage()] || cardData.pageKey;
      cardDiv.innerHTML = `
      <img src="${coverUrl}" alt="${getTranslation(cardData.titleKey)}">
      <h3>${getTranslation(cardData.titleKey)}</h3>
      <p>${getTranslation(cardData.descKey)}</p>
      <a href="${getBasePath()}/${getCurrentLanguage()}/${targetFile}/" class="btn">${getTranslation("view_gallery")} <i class="fas fa-arrow-right"></i></a>`;
      gridContainer.appendChild(cardDiv);
    });
  } catch (error) {
    console.error('Erro ao carregar os cartões de trabalho:', error);
    gridContainer.innerHTML = `<p style="color: red;">${getTranslation('error_loading_content').replace('{type}', 'trabalhos')}</p>`;
  }
}
async function loadPagePreviews() {
  const previewContainer = document.querySelector('.section-preview-grid');
  if (!previewContainer) return;
  try {
    const response = await fetch(`${getBasePath()}/data.json`);
    if (!response.ok) throw new Error('Failed to fetch page previews data');
    const data = await response.json();
    const covers = Object.values(data).filter(item => item.url && item.url.includes('/Capas/'));
    const lang = getCurrentLanguage();
    const previewMap = [
    { linkSelector: 'a[href*="sobre-mi"], a[href*="about-me"]', coverTitleKey: 'sobre mim' },
    { linkSelector: 'a[href*="contactos"], a[href*="contacts"]', coverTitleKey: 'contactos' }
    ];
    previewMap.forEach(item => {
      const linkElement = previewContainer.querySelector(item.linkSelector);
      if (linkElement) {
        const coverData = covers.find(c => c.titles.pt.toLowerCase().includes(item.coverTitleKey));
        const imgElement = linkElement.querySelector('img');
        if (coverData) {
          imgElement.src = coverData.url;
          const altTextKey = linkElement.querySelector('h3').dataset.langKey;
          imgElement.alt = getTranslation(altTextKey);
        } else {
          console.warn(`Capa para '${item.coverTitleKey}' não encontrada no data.json`);
          imgElement.src = `${getBasePath()}/imagens/placeholder.png`;
        }
      }
    });
  } catch (error) {
    console.error("Erro ao carregar imagens de preview:", error);
  }
}
function initializeMailerLite() {
  if (document.querySelector('script[src="https://assets.mailerlite.com/js/universal.js"]')) {
  if (window.ml) {
    window.ml('account', '1677717');
  }
  return;
}
(function(w,d,e,u,f,l,n){w[f]=w[f]||function(){(w[f].q=w[f].q||[]).push(arguments);},l=d.createElement(e),l.async=1,l.src=u,n=d.getElementsByTagName(e)[0],n.parentNode.insertBefore(l,n);})(window,document,'script','https://assets.mailerlite.com/js/universal.js','ml');
ml('account', '1677717');
}
function loadNewsletterForm() {
  const container = document.getElementById('newsletter-embed-container');
  if (!container) return;
  const formIds = {
    pt: 'igOq2z',
    en: 'IYWzHx',
    es: 'JgeLNy'
  };
  const lang = getCurrentLanguage();
  const formId = formIds[lang] || formIds.pt;
  const mailerliteDiv = document.createElement('div');
  mailerliteDiv.className = 'ml-embedded';
  mailerliteDiv.dataset.form = formId;
  container.innerHTML = '';
  container.appendChild(mailerliteDiv);
  initializeMailerLite();
}
function setupHeader() {
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => navLinks.classList.toggle('active'));
  }
  document.querySelectorAll('.main-nav .dropdown > a').forEach(toggle => {
    toggle.addEventListener('click', (event) => {
      if (window.innerWidth <= 768) {
        event.preventDefault();
        toggle.parentElement.classList.toggle('active');
      }
    });
  });
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
  
  // Atualizar todos os links com base no idioma atual
  updateNavigationLinks(lang);
  
  const sourceFile = getSourcePageFile();
  document.querySelectorAll('a[data-page-key]').forEach(link => {
    if (link.dataset.pageKey === sourceFile) {
      link.classList.add('active');
      const parentDropdown = link.closest('.dropdown');
      if (parentDropdown) parentDropdown.classList.add('active');
    }
  });
}

function updateNavigationLinks(lang) {
  const sourceFile = getSourcePageFile();
  const basePath = getBasePath(); // Obter o caminho base

  // Atualizar links de navegação
  document.querySelectorAll("a[data-page-key]").forEach(link => {
    const pageKey = link.dataset.pageKey;
    const targetFile = pageMap[pageKey]?.[lang] || pageKey;
    // MODIFICAÇÃO: Adicionar basePath ao início do href
    link.href = `${basePath}/${lang}/${targetFile}/`; 
  });
  
  // Atualizar links de idioma
  const langNames = { pt: 'Português', en: 'English', es: 'Español' };
  document.querySelectorAll(".lang-option").forEach(link => {
    const linkLang = link.dataset.lang;
    const targetFile = pageMap[sourceFile]?.[linkLang] || sourceFile;
    // MODIFICAÇÃO: Adicionar basePath ao início do href
    link.href = `${basePath}/${linkLang}/${targetFile}/`;

    const textSpan = link.querySelector('span[data-lang-key]');
    if (textSpan) {
      textSpan.textContent = langNames[linkLang];
    }

    if (linkLang === lang) {
      link.classList.add("active");
    } else {
      link.classList.remove("active");
    }
  });
}

function onPageLoad() {
  const pathSegments = window.location.pathname.split('/');
  const lang = pathSegments.find(seg => ['pt', 'en', 'es'].includes(seg)) || 'pt';
  setLanguage(lang);
  applyTranslations();
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
  const pageKey = getSourcePageFile();
  const galleryInfo = galleryIdMap[pageKey] || Object.values(galleryIdMap).find(g => window.location.pathname.includes(g.id.split('-gallery')[0]));
  if (galleryInfo) {
    if (galleryInfo.type === 'apresentacoes') {
      loadPresentations();
    } else {
      loadGalleryContent(galleryInfo.type, galleryInfo.id, galleryInfo.orientation || null);
    }
  }
}
document.addEventListener('DOMContentLoaded', onPageLoad);
const observer = new MutationObserver((mutations, obs) => {
  const header = document.querySelector('.main-header');
  if (header && header.innerHTML.trim() !== '') {
    setupHeader();
    applyTranslations();
    initializeMailerLite();
    loadNewsletterForm();
    obs.disconnect();
  }
});
observer.observe(document.body, { childList: true, subtree: true });