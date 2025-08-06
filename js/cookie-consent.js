class CookieConsent {
  constructor() {
    this.cookieName = 'cookie-consent';
    this.cookieExpiry = 365;
    this.translations = {
      pt: {
        title: 'Utilizamos Cookies',
        message: 'Este site utiliza cookies para melhorar a sua experiência de navegação, analisar o tráfego e personalizar conteúdo. Pode escolher quais cookies aceitar.',
        acceptAll: 'Aceitar Todos',
        acceptNecessary: 'Apenas Necessários',
        settings: 'Configurações dos Cookies',
        save: 'Guardar Preferências',
        necessary: 'Cookies Necessários',
        analytics: 'Cookies de Análise',
        marketing: 'Cookies de Marketing',
        necessaryDesc: 'Estes cookies são essenciais para o funcionamento básico do site.',
        analyticsDesc: 'Ajudam-nos a entender como os visitantes interagem com o site.',
        marketingDesc: 'Utilizados para mostrar anúncios relevantes aos utilizadores.',
        privacyPolicy: 'Política de Privacidade'
      },
      en: {
        title: 'We Use Cookies',
        message: 'This website uses cookies to improve your browsing experience, analyze traffic and personalize content. You can choose which cookies to accept.',
        acceptAll: 'Accept All',
        acceptNecessary: 'Necessary Only',
        settings: 'Cookies settings',
        save: 'Save Preferences',
        necessary: 'Necessary Cookies',
        analytics: 'Analytics Cookies',
        marketing: 'Marketing Cookies',
        necessaryDesc: 'These cookies are essential for the basic functioning of the website.',
        analyticsDesc: 'Help us understand how visitors interact with the website.',
        marketingDesc: 'Used to show relevant advertisements to users.',
        privacyPolicy: 'Privacy Policy'
      },
      es: {
        title: 'Utilizamos Cookies',
        message: 'Este sitio web utiliza cookies para mejorar su experiencia de navegación, analizar el tráfico y personalizar el contenido. Puede elegir qué cookies aceptar.',
        acceptAll: 'Aceptar Todas',
        acceptNecessary: 'Solo Necesarias',
        settings: 'Configuraciones de cookies',
        save: 'Guardar Preferencias',
        necessary: 'Cookies Necesarias',
        analytics: 'Cookies de Análisis',
        marketing: 'Cookies de Marketing',
        necessaryDesc: 'Estas cookies son esenciales para el funcionamiento básico del sitio web.',
        analyticsDesc: 'Nos ayudan a entender cómo los visitantes interactúan con el sitio web.',
        marketingDesc: 'Utilizadas para mostrar anuncios relevantes a los usuarios.',
        privacyPolicy: 'Política de Privacidad'
      }
    };
    this.init();
  }
  init() {
    if (!this.hasConsent()) {
      this.showBanner();
    }
    this.loadAcceptedCookies();
  }
  getCurrentLanguage() {
    const pathLang = window.location.pathname.split('/')[2] || 'pt';
    return ['pt', 'en', 'es'].includes(pathLang) ? pathLang : 'pt';
  }
  getTranslation(key) {
    const lang = this.getCurrentLanguage();
    return this.translations[lang][key] || this.translations.pt[key];
  }
  hasConsent() {
    return this.getCookie(this.cookieName) !== null;
  }
  getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }
  setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
  }
  showBanner() {
    const banner = this.createBanner();
    document.body.appendChild(banner);
    setTimeout(() => {
      banner.classList.add('show');
    }, 100);
  }
  createBanner() {
    const banner = document.createElement('div');
    banner.className = 'cookie-consent-banner';
    banner.innerHTML = `
    <div class="cookie-consent-content">
    <div class="cookie-consent-text">
    <h3>${this.getTranslation('title')}</h3>
    <p>${this.getTranslation('message')}</p>
    </div>
    <div class="cookie-consent-actions">
    <button class="cookie-btn cookie-btn-settings">
    ${this.getTranslation('settings')}
    </button>
    <button class="cookie-btn cookie-btn-necessary">
    ${this.getTranslation('acceptNecessary')}
    </button>
    <button class="cookie-btn cookie-btn-accept">
    ${this.getTranslation('acceptAll')}
    </button>
    </div>
    </div>
    `;
    banner.querySelector('.cookie-btn-settings').addEventListener('click', () => this.showSettings());
    banner.querySelector('.cookie-btn-necessary').addEventListener('click', () => this.acceptNecessary());
    banner.querySelector('.cookie-btn-accept').addEventListener('click', () => this.acceptAll());
    return banner;
  }
  showSettings() {
    const modal = this.createSettingsModal();
    document.body.appendChild(modal);
    setTimeout(() => {
      modal.classList.add('show');
    }, 100);
  }
  createSettingsModal() {
    const currentPreferences = this.getPreferences() || { analytics: false, marketing: false };
    const analyticsChecked = currentPreferences.analytics ? 'checked' : '';
    const marketingChecked = currentPreferences.marketing ? 'checked' : '';
    const modal = document.createElement('div');
    modal.className = 'cookie-settings-modal';
    modal.innerHTML = `
    <div class="cookie-settings-overlay" onclick="cookieConsent.closeSettings()"></div>
    <div class="cookie-settings-content">
    <div class="cookie-settings-header">
    <h3>${this.getTranslation('settings')}</h3>
    <button class="cookie-settings-close" onclick="cookieConsent.closeSettings()">×</button>
    </div>
    <div class="cookie-settings-body">
    <div class="cookie-category">
    <div class="cookie-category-header">
    <label class="cookie-switch">
    <input type="checkbox" id="necessary-cookies" checked disabled>
    <span class="cookie-slider"></span>
    </label>
    <h4>${this.getTranslation('necessary')}</h4>
    </div>
    <p>${this.getTranslation('necessaryDesc')}</p>
    </div>
    <div class="cookie-category">
    <div class="cookie-category-header">
    <label class="cookie-switch">
    <input type="checkbox" id="analytics-cookies" ${analyticsChecked}>
    <span class="cookie-slider"></span>
    </label>
    <h4>${this.getTranslation('analytics')}</h4>
    </div>
    <p>${this.getTranslation('analyticsDesc')}</p>
    </div>
    <div class="cookie-category">
    <div class="cookie-category-header">
    <label class="cookie-switch">
    <input type="checkbox" id="marketing-cookies" ${marketingChecked}>
    <span class="cookie-slider"></span>
    </label>
    <h4>${this.getTranslation('marketing')}</h4>
    </div>
    <p>${this.getTranslation('marketingDesc')}</p>
    </div>
    </div>
    <div class="cookie-settings-footer">
    <button class="cookie-btn cookie-btn-save" onclick="cookieConsent.savePreferences()">
    ${this.getTranslation('save')}
    </button>
    </div>
    </div>
    `;
    return modal;
  }
  closeSettings() {
    const modal = document.querySelector('.cookie-settings-modal');
    if (modal) {
      modal.remove();
    }
    const overlay = document.querySelector('.cookie-modal-overlay');
    if (overlay) {
      overlay.remove();
    }
    this.modal = null;
  }
  acceptAll() {
    const preferences = {
      necessary: true,
      analytics: true,
      marketing: true,
      timestamp: Date.now()
    };
    this.setCookie(this.cookieName, JSON.stringify(preferences), this.cookieExpiry);
    this.hideBanner();
    this.loadAcceptedCookies();
    this.triggerConsentEvent('all');
  }
  acceptNecessary() {
    const preferences = {
      necessary: true,
      analytics: false,
      marketing: false,
      timestamp: Date.now()
    };
    this.setCookie(this.cookieName, JSON.stringify(preferences), this.cookieExpiry);
    this.hideBanner();
    this.loadAcceptedCookies();
    this.triggerConsentEvent('necessary');
  }
  savePreferences() {
    const necessary = document.getElementById('necessary-cookies').checked;
    const analytics = document.getElementById('analytics-cookies').checked;
    const marketing = document.getElementById('marketing-cookies').checked;
    const preferences = {
      necessary,
      analytics,
      marketing,
      timestamp: Date.now()
    };
    this.setCookie(this.cookieName, JSON.stringify(preferences), this.cookieExpiry);
    this.closeSettings();
    this.hideBanner();
    this.loadAcceptedCookies();
    this.triggerConsentEvent('custom');
  }
  hideBanner() {
    const banner = document.querySelector('.cookie-consent-banner');
    if (banner) {
      banner.classList.remove('show');
      // Aguardar a transição CSS antes de remover o elemento
      setTimeout(() => {
        if (banner.parentNode) {
          banner.remove();
        }
      }, 300); // Tempo da transição CSS
    }
  }
  loadAcceptedCookies() {
    const consent = this.getCookie(this.cookieName);
    if (!consent) return;
    try {
      const preferences = JSON.parse(consent);
      if (preferences.analytics) {
        this.loadAnalyticsCookies();
      }
      if (preferences.marketing) {
        this.loadMarketingCookies();
      }
    } catch (error) {
      console.error('Erro ao carregar preferências de cookies:', error);
    }
  }
  loadAnalyticsCookies() {
    console.log('Carregando cookies de análise...');
  }
  loadMarketingCookies() {
    console.log('Carregando cookies de marketing...');
  }
  triggerConsentEvent(type) {
    const event = new CustomEvent('cookieConsentChanged', {
      detail: { type, preferences: this.getPreferences() }
    });
    document.dispatchEvent(event);
  }
  getPreferences() {
    const consent = this.getCookie(this.cookieName);
    if (!consent) return null;
    try {
      return JSON.parse(consent);
    } catch (error) {
      return null;
    }
  }
  isAccepted(type) {
    const preferences = this.getPreferences();
    return preferences ? preferences[type] === true : false;
  }
  revokeConsent() {
    document.cookie = `${this.cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
    location.reload();
  }
}
let cookieConsent;
document.addEventListener('DOMContentLoaded', () => {
  cookieConsent = new CookieConsent();
  const manageCookiesBtn = document.getElementById('manage-cookies-btn');
  if (manageCookiesBtn) {
    manageCookiesBtn.addEventListener('click', function(event) {
      if (cookieConsent) {
        cookieConsent.showSettings();
      }
    });
  }
});
window.cookieConsent = cookieConsent;
