import { initCarousel } from 'carousel';
import { loadGalleryContent, loadPresentations } from 'gallery';
import { createWatermarkElement } from 'ferramentas';

// Function to handle all page-specific initializations after common elements are loaded
function initializePageContent() {
    // Initialize carousel on the home page
    const carouselElement = document.querySelector('.carousel-container');
    if (carouselElement) {
        initCarousel(carouselElement);
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

    navItems.forEach(item => {
        const linkPath = item.getAttribute('href'); 
        let normalizedCurrentPath = currentPathname;

        // Check if current page matches the link
        if (normalizedCurrentPath.includes(linkPath) || 
            (linkPath.includes('index.html') && (normalizedCurrentPath.endsWith('/') || normalizedCurrentPath.includes('index.html')))) {
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
    if (currentPathname.includes('/html/fotos.html')) { 
        loadGalleryContent('photos', 'photoGalleryContainer');
    } else if (currentPathname.includes('/html/designs.html')) { 
        loadGalleryContent('designs', 'design-gallery');
    } else if (currentPathname.includes('/html/videos.html')) {
        loadGalleryContent('videos', 'video-gallery');
    } else if (currentPathname.includes('/html/apresentacoes.html')) {
        loadPresentations();
    }
}

// Function to load and inject common header/footer (simplified since we're not using dynamic loading anymore)
function loadCommonElements() {
    // For the new structure, we don't need to dynamically load header/footer
    // They're directly embedded in each page
    initializePageContent();
}

// Call the initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', loadCommonElements);