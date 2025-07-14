// Ficheiro: /js/linguagem.js (Versão Final Recomendada)

import { translations } from './traducao.js';

// --- GESTÃO DO IDIOMA ---

let currentLanguage = 'pt'; // Idioma padrão

/**
 * Define o idioma atual e guarda a preferência.
 * @param {string} lang - O código do idioma ('pt', 'en', 'es').
 */
export function setLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        localStorage.setItem('preferredLanguage', lang);
    }
}

/**
 * Obtém a tradução para uma chave específica.
 * @param {string} key - A chave de tradução.
 * @returns {string} O texto traduzido.
 */
export function getTranslation(key) {
    const langTranslations = translations[currentLanguage] || translations.pt; // Usa PT como fallback
    return langTranslations[key] || key; // Retorna a própria chave se não encontrar tradução
}

/**

 * Retorna o código do idioma atualmente ativo.
 * @returns {string}
 */
export function getCurrentLanguage() {
    return currentLanguage;
}


// --- APLICAÇÃO DAS TRADUÇÕES NO DOM ---

/**
 * Aplica as traduções a todos os elementos da página com o atributo `data-lang-key`.
 */
export function applyTranslations() {
    // Traduz o título da página
    const pageTitleKey = document.body.getAttribute('data-page-title-key');
    if (pageTitleKey) {
        document.title = getTranslation(pageTitleKey);
    }

    // Itera sobre todos os elementos que precisam de tradução
    document.querySelectorAll('[data-lang-key]').forEach(element => {
        const key = element.dataset.langKey;
        const translation = getTranslation(key);

        // Trata de placeholders em inputs e textareas
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.placeholder) {
                element.placeholder = translation;
            }
        } 
        // Trata de atributos 'aria-label' para acessibilidade
        else if (element.hasAttribute('aria-label')) {
            element.setAttribute('aria-label', translation);
        }
        // Usa innerHTML para preservar tags como &copy; ou <i>
        else {
            element.innerHTML = translation;
        }
    });
}
