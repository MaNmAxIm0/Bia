// js/principal.js

import { initCarousel } from './carrossel.js';
import { loadGalleryContent, loadPresentations } from './galeria.js';
import { createWatermarkElement } from './ferramentas.js';
import { applyTranslations } from './linguagem.js';

console.log("principal.js: Módulo carregado.");

// Função para lidar com todas as inicializações de página
function initializePageContent() {
  console.log("principal.js: initializePageContent chamada.");
  
  // Inicializa o carrossel na página inicial
  const carouselElement = document.querySelector('.carousel-container');
  if (carouselElement) {
    initCarousel(carouselElement);
    console.log("principal.js: Carrossel inicializado.");
  }

  // Mobile Navigation Toggle
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
      const icon = menuToggle.querySelector('i');
      if (navLinks.classList.contains('active')) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-times');
      } else {
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
      }
    });

    navLinks.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        if (navLinks.classList.contains('active')) {
          navLinks.classList.remove('active');
          menuToggle.querySelector('i').classList.remove('fa-times');
          menuToggle.querySelector('i').classList.add('fa-bars');
        }
      });
    });
  }

  // Set active class for navigation link based on current page
  const navItems = document.querySelectorAll('.main-nav .nav-links li a');
  const currentPathname = window.location.pathname;
  console.log("principal.js: Current pathname:", currentPathname);

  navItems.forEach(item => {
    const linkPath = item.getAttribute('href');
    if (currentPathname.endsWith('/' + linkPath)) {
      item.classList.add('active');
    } else if (linkPath === 'index.html' && (currentPathname.endsWith('/') || currentPathname.endsWith('/index.html'))) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Smooth scroll for internal links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      document.querySelector(this.getAttribute('href')).scrollIntoView({
        behavior: 'smooth'
      });
    });
  });

  // Adiciona marca d'água às imagens estáticas da página inicial
  const staticImageContainers = document.querySelectorAll('.work-item, .preview-item');
  staticImageContainers.forEach(container => {
    const img = container.querySelector('img');
    if (img) {
      const imageWrapper = document.createElement('div');
      imageWrapper.classList.add('image-container');
      container.insertBefore(imageWrapper, img);
      imageWrapper.appendChild(img);
      imageWrapper.appendChild(createWatermarkElement());
      img.oncontextmenu = () => false;
    }
  });

  // --- CORREÇÃO PRINCIPAL AQUI ---
  // Carrega o conteúdo para as páginas de galeria usando as chaves corretas do data.json
  const pathSegments = currentPathname.split('/');
  const currentFilename = pathSegments[pathSegments.length - 1];

  if (currentFilename === 'fotos.html' || currentFilename === 'photos.html') {
    console.log("principal.js: A chamar loadGalleryContent para 'fotografias'.");
    loadGalleryContent('fotografias', 'photoGalleryContainer');
  } else if (currentFilename === 'designs.html') {
    console.log("principal.js: A chamar loadGalleryContent para 'designs'.");
    loadGalleryContent('designs', 'design-gallery');
  } else if (currentFilename === 'videos.html') {
    console.log("principal.js: A chamar loadGalleryContent para 'videos'.");
    loadGalleryContent('videos', 'video-gallery');
  } else if (currentFilename === 'apresentacoes.html' || currentFilename === 'presentations.html') {
    console.log("principal.js: A chamar loadPresentations.");
    loadPresentations();
  } else {
    console.log("principal.js: Nenhum conteúdo de galeria específico para carregar nesta página.");
  }

  // Aplica as traduções depois de todo o conteúdo ser carregado/inicializado
  applyTranslations();
  console.log("principal.js: Traduções aplicadas.");
}

// Garante que o código só é executado depois de o HTML ser carregado
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePageContent);
} else {
  initializePageContent();
}
