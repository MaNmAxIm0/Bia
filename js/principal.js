// js/principal.js

import { loadGalleryContent, loadPresentations } from './galeria.js';
import { createWatermarkElement } from './ferramentas.js';
import { applyTranslations } from './linguagem.js';

function initializePageContent() {
  console.log("principal.js: A inicializar conteúdo da página.");

  // Código do menu (incluindo a nova lógica para dropdowns móveis)
  const menuToggle = document.querySelector('.menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (menuToggle && navLinks) {
    menuToggle.addEventListener('click', () => {
      navLinks.classList.toggle('active');
      const icon = menuToggle.querySelector('i');
      icon.classList.toggle('fa-bars');
      icon.classList.toggle('fa-times');
    });
  }
  
  document.querySelectorAll('.main-nav .dropdown-toggle').forEach(toggle => {
    toggle.addEventListener('click', function(e) {
      e.preventDefault(); 
      if (window.innerWidth <= 768) {
        const dropdown = this.parentElement;
        dropdown.classList.toggle('active');
      }
    });
  });

  // Lógica para destacar o link ativo na navegação
  const navItems = document.querySelectorAll('.main-nav .nav-links li a');
  const currentPathname = window.location.pathname;
  navItems.forEach(item => {
    const itemHref = item.getAttribute('href');
    if (currentPathname.endsWith(itemHref)) {
      // Adiciona a classe 'active' ao link direto
      item.classList.add('active');
      
      // Se o link ativo estiver dentro de um dropdown, ativa também o link principal do dropdown
      const parentDropdown = item.closest('.dropdown');
      if (parentDropdown) {
        parentDropdown.querySelector('.dropdown-toggle').classList.add('active');
      }
    }
  });

  // Adiciona marca d'água a imagens estáticas
  document.querySelectorAll('.work-item img, .preview-item img').forEach(img => {
      const imageWrapper = document.createElement('div');
      imageWrapper.classList.add('image-container');
      img.parentNode.insertBefore(imageWrapper, img);
      imageWrapper.appendChild(img);
      imageWrapper.appendChild(createWatermarkElement());
      img.oncontextmenu = () => false;
  });

  // --- LÓGICA DE CARREGAMENTO DE GALERIA ATUALIZADA ---
  const pageName = currentPathname.split('/').pop();

  if (pageName.includes('fotos-horizontais') || pageName.includes('photos-horizontal')) {
    loadGalleryContent('fotografias', 'photo-h-gallery', 'horizontal');
  } else if (pageName.includes('fotos-verticais') || pageName.includes('photos-vertical')) {
    loadGalleryContent('fotografias', 'photo-v-gallery', 'vertical');
  } else if (pageName.includes('videos-horizontais') || pageName.includes('videos-horizontal')) {
    loadGalleryContent('videos', 'video-h-gallery', 'horizontal');
  } else if (pageName.includes('videos-verticais') || pageName.includes('videos-vertical')) {
    loadGalleryContent('videos', 'video-v-gallery', 'vertical');
  } else if (pageName.includes('designs')) {
    loadGalleryContent('designs', 'design-gallery');
  } else if (pageName.includes('apresentacoes') || pageName.includes('presentations')) {
    loadPresentations();
  }

  // Aplica as traduções
  applyTranslations();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializePageContent);
} else {
  initializePageContent();
}
