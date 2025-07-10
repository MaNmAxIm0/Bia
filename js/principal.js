import { initCarousel } from 'carrossel';
import { loadGalleryContent, loadPresentations } from 'gallery';
import { createWatermarkElement } from 'ferramentas';
import { applyTranslations } from 'linguagem'; // Only applyTranslations is exported from linguagem.js now

console.log("principal.js: Module loaded."); // Added for debugging

// Function to handle all page-specific initializations after common elements are loaded
function initializePageContent() {
    console.log("principal.js: initializePageContent called."); // Added for debugging
    
    // Initialize carousel on the home page
    const carouselElement = document.querySelector('.carousel-container');
    if (carouselElement) {
        initCarousel(carouselElement);
        console.log("principal.js: Carousel initialized."); // Added for debugging
    }

    // Mobile Navigation Toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            // Toggle icon between bars and times
            const icon = menuToggle.querySelector('i');
            if (navLinks.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // Close menu when a link is clicked (for single page navigation or smooth scrolling)
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
    console.log("principal.js: Current pathname:", currentPathname); // Added for debugging

    navItems.forEach(item => {
        const linkPath = item.getAttribute('href'); 
        // A more robust check for the active link
        if (currentPathname.endsWith('/' + linkPath)) {
            item.classList.add('active');
        } else if (linkPath === 'index.html' && (currentPathname.endsWith('/') || currentPathname.endsWith('/index.html'))) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    // Smooth scroll for internal links (optional, if desired for same-page anchors)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Disable right-click and add watermark for static images on the home page
    const homePageImageContainers = document.querySelectorAll('.work-item, .preview-item');
    homePageImageContainers.forEach(container => {
        const img = container.querySelector('img');
        if (img) {
            img.oncontextmenu = () => false; // Disable right-click
            // Add watermark
            container.appendChild(createWatermarkElement());
        }
    });

    // Load content for gallery pages
    const pathSegments = currentPathname.split('/');
    const currentFilename = pathSegments[pathSegments.length - 1]; // Get the actual filename (e.g., fotos.html or photos.html)

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

// Function to load and inject common header/footer (simplified since we're not using dynamic loading anymore)
function loadCommonElements() {
    // For the new structure, we don't need to dynamically load header/footer
    // They're directly embedded in each page
    console.log("principal.js: loadCommonElements called. Proceeding to initializePageContent.");
    initializePageContent();
}

// Call the initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', loadCommonElements);
console.log("principal.js: DOMContentLoaded listener set.");
