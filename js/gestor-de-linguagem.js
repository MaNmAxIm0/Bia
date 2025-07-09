import { translations } from './traducao.js';

let currentLanguage = 'pt'; // Default language

/**
 * Sets the current language and stores it in localStorage.
 * @param {string} lang - The language code (e.g., 'pt', 'en').
 */
export function setLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        localStorage.setItem('preferredLanguage', lang);
    } else {
        console.warn(`Language '${lang}' not supported.`);
    }
}

/**
 * Retrieves a translation for a given key in the current language.
 * Falls back to English if not found, then the key itself.
 * @param {string} key - The translation key.
 * @param {object} [replacements={}] - An object with placeholders and their values.
 * @returns {string} The translated string.
 */
export function getTranslation(key, replacements = {}) {
    let translation = translations[currentLanguage]?.[key] || translations['en']?.[key] || key; // Fallback to English, then key itself
    for (const placeholder in replacements) {
        translation = translation.replace(`{${placeholder}}`, replacements[placeholder]);
    }
    return translation;
}

/**
 * Returns the currently active language.
 * @returns {string} The current language code.
 */
export function getCurrentLanguage() {
    return currentLanguage;
}