// Ficheiro: js/linguagem.js (Versão Final e Centralizada)

import { translations } from './traducao.js';

let currentLanguage = 'pt'; // Idioma padrão

/**
 * Define o idioma atual do site.
 * @param {string} lang - O código do idioma ('pt', 'en', 'es').
 */
export function setLanguage(lang) {
    if (['pt', 'en', 'es'].includes(lang)) {
        currentLanguage = lang;
        // Guarda a preferência do utilizador no armazenamento local
        localStorage.setItem('preferredLanguage', lang);
        // Atualiza o atributo 'lang' na tag <html> para acessibilidade e SEO
        document.documentElement.lang = lang;
    }
}

/**
 * Obtém o idioma atualmente definido.
 * @returns {string} O código do idioma atual.
 */
export function getCurrentLanguage() {
    return currentLanguage;
}

/**
 * Obtém a tradução para uma chave específica no idioma atual.
 * @param {string} key - A chave de tradução (ex: 'home', 'about_me').
 * @returns {string} A string traduzida ou a própria chave se não for encontrada.
 */
export function getTranslation(key) {
    return translations[currentLanguage]?.[key] || translations.pt?.[key] || key;
}

/**
 * Aplica todas as traduções aos elementos da página que têm o atributo `data-lang-key`.
 */
export function applyTranslations() {
    // Traduz o título da página
    const pageTitleKey = document.body.getAttribute('data-page-title-key');
    if (pageTitleKey) {
        document.title = getTranslation(pageTitleKey);
    }

    // Traduz todos os outros elementos
    document.querySelectorAll('[data-lang-key]').forEach(element => {
        const key = element.dataset.langKey;
        const translation = getTranslation(key);
        
        // Trata de diferentes tipos de elementos
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.type === 'submit') {
                element.value = translation;
            } else {
                element.placeholder = translation;
            }
        } else if (element.hasAttribute('aria-label')) {
            element.setAttribute('aria-label', translation);
        } else {
            element.innerHTML = translation;
        }
    });
}
