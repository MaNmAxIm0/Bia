import { translations } from './traducao.js';

let currentLanguage = 'pt';

export function setLanguage(lang) {
  if (['pt', 'en', 'es'].includes(lang)) {
    currentLanguage = lang;
    localStorage.setItem('preferredLanguage', lang);
    document.documentElement.lang = lang;
  }
}

export function getCurrentLanguage() {
  return currentLanguage;
}

export function getTranslation(key) {
  return translations[currentLanguage]?.[key] || translations.pt?.[key] || key;
}

export function applyTranslations() {
  const pageTitleKey = document.body.getAttribute('data-page-title-key');
  if (pageTitleKey) {
    document.title = getTranslation(pageTitleKey);
  }
  document.querySelectorAll('[data-lang-key]').forEach(element => {
    const key = element.dataset.langKey;
    const translation = getTranslation(key);
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