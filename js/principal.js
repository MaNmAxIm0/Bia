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

  // --- INÍCIO DA ALTERAÇÃO DA MARCA D'ÁGUA ---
  // Adiciona marca d'água às imagens estáticas da página inicial
  const staticImageContainers = document.querySelectorAll('.work-item, .preview-item');
  staticImageContainers.forEach(container => {
    const img = container.querySelector('img');
    if (img) {
      // Cria o wrapper para a imagem
      const imageWrapper = document.createElement('div');
      imageWrapper.classList.add('image-container');

      // Move a imagem para dentro do wrapper
      // O insertBefore coloca o wrapper no lugar da imagem, e depois a imagem é movida para dentro dele
      container.insertBefore(imageWrapper, img);
      imageWrapper.appendChild(img);

      // Adiciona a marca d'água ao wrapper
      imageWrapper.appendChild(createWatermarkElement());
      
      // Desativa o menu de contexto na imagem
      img.oncontextmenu = () => false;
    }
  });
  // --- FIM DA ALTERAÇÃO DA MARCA D'ÁGUA ---

  // Load content for gallery pages
  const pathSegments = currentPathname.split('/');
  const currentFilename = pathSegments[pathSegments.length - 1];

  if (currentFilename === 'fotos.html' || currentFilename === 'photos.html') {
    console.log("principal.js: Calling loadGalleryContent for photos.");
    loadGalleryContent('photos', 'photoGalleryContainer');
  } else if (currentFilename === 'designs.html') {
    console.log("principal.js: Calling loadGalleryContent for designs.");
    loadGalleryContent('designs', 'design-gallery');
  } else if (currentFilename === 'videos.html') {
    console.log("principal.js: Calling loadGalleryContent for videos.");
    loadGalleryContent('videos', 'video-gallery');
  } else if (currentFilename === 'apresentacoes.html' || currentFilename === 'presentations.html') {
    console.log("principal.js: Calling loadPresentations.");
    loadPresentations();
  } else {
    console.log("principal.js: No specific gallery content loading for this page.");
  }

  // Apply translations after all content is loaded/initialized
  applyTranslations();
  console.log("principal.js: Translations applied.");
}

// Garante que o código só é executado depois de o HTML ser carregado
// (Embora o script seja type="module", que já tem defer, isto é uma segurança extra)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePageContent);
} else {
  initializePageContent();
}
