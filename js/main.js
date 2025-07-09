import { initCarousel } from 'carousel';

document.addEventListener('DOMContentLoaded', () => {
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
    const currentPath = window.location.pathname.split('/').pop();
    const navItems = document.querySelectorAll('.main-nav .nav-links li a');

    navItems.forEach(item => {
        const linkPath = item.getAttribute('href').split('/').pop();
        if (currentPath === linkPath || (currentPath === '' && linkPath === 'index.html')) {
            item.classList.add('active');
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
});

