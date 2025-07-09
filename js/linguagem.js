import { setLanguage, getTranslation, getCurrentLanguage } from './gestor-de-linguagem.js';

/**
 * Applies translations to all elements with `data-lang-key` attributes on the page.
 */
export function applyTranslations() {
    // Set page title
    const pageTitleElement = document.querySelector('title[data-lang-key]');
    if (pageTitleElement) {
        pageTitleElement.textContent = getTranslation(pageTitleElement.dataset.langKey);
    } else {
        // Fallback for pages without data-lang-key on title tag or root index.html
        const path = window.location.pathname;
        if (path.includes('/html/pt/index.html') || path.endsWith('/html/pt/') || path === '/index.html') {
            document.title = getTranslation('home') + ' - Beatriz Rodrigues';
        } else if (path.includes('/html/en/index.html') || path.endsWith('/html/en/')) {
            document.title = getTranslation('home') + ' - Beatriz Rodrigues';
        }
    }

    document.querySelectorAll('[data-lang-key]').forEach(element => {
        const key = element.dataset.langKey;
        const translation = getTranslation(key);

        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.placeholder) {
                element.placeholder = translation;
            }
            if (key === 'form_name_label' || key === 'form_email_label' || key === 'form_message_label') {
                element.textContent = translation; // For <label> elements
            }
        } else if (element.tagName === 'BUTTON') {
            if (key === 'send_message_button') {
                element.innerHTML = `${translation} <i class="fas fa-paper-plane"></i>`;
            } else if (key === 'toggle_navigation') {
                element.setAttribute('aria-label', translation);
            } else if (key === 'close') {
                element.setAttribute('aria-label', translation);
            } else if (!element.classList.contains('lang-btn')) { // Avoid changing lang-btn text content
                element.textContent = translation;
            }
        } else if (element.tagName === 'A' && element.classList.contains('lang-btn')) {
            // Handled by hardcoded PT/EN text and active class
        } else if (key === 'all_rights_reserved') {
            element.innerHTML = translation; // Preserve HTML for 
        } else if (key.startsWith('view_')) { // Special handling for "Ver/View" buttons
             element.innerHTML = `${translation} <i class="fas fa-arrow-right"></i>`;
        }
        else {
            element.textContent = translation;
        }
    });

    // Handle language switcher buttons active state
    document.querySelectorAll('.language-switcher .lang-btn').forEach(btn => {
        const targetLang = btn.getAttribute('href').split('/')[2]; // 'pt' or 'en'
        if (targetLang === getCurrentLanguage()) { // Use getCurrentLanguage from manager
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Initialize language and apply translations on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    // Determine the current language based on the URL path, e.g., /html/pt/somepage.html -> 'pt'
    const pathSegments = window.location.pathname.split('/');
    let langFromPath = 'pt'; // Default
    if (pathSegments.includes('html')) {
        const htmlIndex = pathSegments.indexOf('html');
        if (htmlIndex > -1 && pathSegments.length > htmlIndex + 1) {
            const langSegment = pathSegments[htmlIndex + 1];
            if (langSegment === 'en' || langSegment === 'pt') {
                langFromPath = langSegment;
            }
        }
    }

    // Initialize the language manager with the language from the URL.
    // This will also load the stored preferredLanguage if it exists and matches.
    setLanguage(langFromPath); 

    // Apply translations to the loaded page content
    applyTranslations();

    // Set up event listeners for language switcher buttons
    document.querySelectorAll('.language-switcher .lang-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            
            // The href of the button already points to the correct language version of the current page.
            const targetHref = button.getAttribute('href');
            
            // Extract the target language from the href to set it in the manager
            const targetLangMatch = targetHref.match(/\/html\/(pt|en)\//);
            if (targetLangMatch && targetLangMatch[1]) {
                const targetLang = targetLangMatch[1];
                setLanguage(targetLang); // Update preferred language in localStorage via manager
            }
            
            window.location.href = targetHref; // Redirect to the new language page
        });
    });
});