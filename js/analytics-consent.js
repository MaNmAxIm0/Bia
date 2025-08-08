class AnalyticsConsent {
  constructor(measurementId = 'G-ZW5DLGF7RF') {
    this.measurementId = measurementId;
    this.isLoaded = false;
    this.consentGiven = false;
    this.init();
  }
  init() {
    document.addEventListener('cookieConsentChanged', (event) => {
      this.handleConsentChange(event.detail);
    });
    this.checkExistingConsent();
  }
  checkExistingConsent() {
    if (window.cookieConsent) {
      const preferences = window.cookieConsent.getPreferences();
      if (preferences && preferences.analytics) {
        this.loadAnalytics();
      }
    }
  }
  handleConsentChange(detail) {
    const { preferences } = detail;
    if (preferences.analytics && !this.isLoaded) {
      this.loadAnalytics();
    } else if (!preferences.analytics && this.isLoaded) {
      this.disableAnalytics();
    }
  }
  loadAnalytics() {
    if (this.isLoaded) return;
    this.loadGoogleAnalytics();
    this.setupCustomEvents();
    this.isLoaded = true;
    this.consentGiven = true;
    console.log('Google Analytics carregado com consentimento');
  }
  loadGoogleAnalytics() {
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${this.measurementId}`;
    document.head.appendChild(script);
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    window.gtag = gtag;
    gtag('js', new Date());
    gtag('consent', 'default', {
      'analytics_storage': 'granted',
      'ad_storage': 'denied'
    });
    gtag('config', this.measurementId, {
      'anonymize_ip': true,
      'respect_dnt': true,
      'allow_google_signals': false,
      'allow_ad_personalization_signals': false
    });
  }
  disableAnalytics() {
    if (!this.isLoaded) return;
    if (window.gtag) {
      gtag('consent', 'update', {
        'analytics_storage': 'denied'
      });
    }
    this.removeAnalyticsCookies();
    this.consentGiven = false;
    console.log('Google Analytics desativado');
  }
  removeAnalyticsCookies() {
    const analyticsCookies = [
      '_ga',
      '_ga_' + this.measurementId.replace('G-', ''),
      '_gid',
      '_gat',
      '_gat_gtag_' + this.measurementId,
      '__utma',
      '__utmb',
      '__utmc',
      '__utmt',
      '__utmz'
    ];
    analyticsCookies.forEach(cookieName => {
      document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
      document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`;
      document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${window.location.hostname};`;
    });
  }
  setupCustomEvents() {
    if (!this.consentGiven || !window.gtag) return;
    document.addEventListener('click', (event) => {
      const link = event.target.closest('a');
      if (link && this.isExternalLink(link.href)) {
        gtag('event', 'click', {
          'event_category': 'external_link',
          'event_label': link.href,
          'transport_type': 'beacon'
        });
      }
    });
    document.addEventListener('click', (event) => {
      const link = event.target.closest('a');
      if (link && this.isDownloadLink(link.href)) {
        gtag('event', 'file_download', {
          'event_category': 'download',
          'event_label': link.href,
          'transport_type': 'beacon'
        });
      }
    });
    this.setupTimeTracking();
    this.setupScrollTracking();
  }
  isExternalLink(url) {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname !== window.location.hostname;
    } catch (e) {
      return false;
    }
  }
  isDownloadLink(url) {
    const downloadExtensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.zip', '.rar'];
    return downloadExtensions.some(ext => url.toLowerCase().includes(ext));
  }
  setupTimeTracking() {
    let startTime = Date.now();
    let timeThresholds = [30, 60, 120, 300];
    let thresholdsPassed = [];
    setInterval(() => {
      if (!this.consentGiven || !window.gtag) return;
      const timeSpent = Math.floor((Date.now() - startTime) / 1000);
      timeThresholds.forEach(threshold => {
        if (timeSpent >= threshold && !thresholdsPassed.includes(threshold)) {
          thresholdsPassed.push(threshold);
          gtag('event', 'timing_complete', {
            'event_category': 'engagement',
            'name': 'time_on_page',
            'value': threshold
          });
        }
      });
    }, 10000);
  }
  setupScrollTracking() {
    let maxScroll = 0;
    let scrollThresholds = [25, 50, 75, 90];
    let thresholdsPassed = [];
    window.addEventListener('scroll', () => {
      if (!this.consentGiven || !window.gtag) return;
      const scrollPercent = Math.round(
        (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100
      );
      if (scrollPercent > maxScroll) {
        maxScroll = scrollPercent;
        scrollThresholds.forEach(threshold => {
          if (scrollPercent >= threshold && !thresholdsPassed.includes(threshold)) {
            thresholdsPassed.push(threshold);
            gtag('event', 'scroll', {
              'event_category': 'engagement',
              'event_label': `${threshold}%`,
              'value': threshold
            });
          }
        });
      }
    });
  }
  trackEvent(eventName, parameters = {}) {
    if (!this.consentGiven || !window.gtag) return;
    gtag('event', eventName, {
      'event_category': parameters.category || 'custom',
      'event_label': parameters.label || '',
      'value': parameters.value || 0,
      ...parameters
    });
  }
  trackPageView(pagePath = null) {
    if (!this.consentGiven || !window.gtag) return;
    gtag('config', this.measurementId, {
      'page_path': pagePath || window.location.pathname
    });
  }
  trackConversion(conversionId, conversionLabel = '') {
    if (!this.consentGiven || !window.gtag) return;
    gtag('event', 'conversion', {
      'send_to': `${conversionId}/${conversionLabel}`
    });
  }
  trackPurchase(transactionId, items, value, currency = 'EUR') {
    if (!this.consentGiven || !window.gtag) return;
    gtag('event', 'purchase', {
      'transaction_id': transactionId,
      'value': value,
      'currency': currency,
      'items': items
    });
  }
  getAnalyticsStatus() {
    return {
      isLoaded: this.isLoaded,
      consentGiven: this.consentGiven,
      measurementId: this.measurementId,
      gtagAvailable: typeof window.gtag !== 'undefined'
    };
  }
}
class BeatrizAnalytics extends AnalyticsConsent {
  constructor() {
    super('G-ZW5DLGF7RF');
    this.setupPortfolioTracking();
  }
  setupPortfolioTracking() {
    this.trackPortfolioViews();
    this.trackGalleryInteractions();
    this.trackContactFormSubmissions();
  }
  trackPortfolioViews() {
    const sections = ['presentations', 'designs', 'photos', 'videos'];
    sections.forEach(section => {
      if (window.location.pathname.includes(section)) {
        this.trackEvent('portfolio_view', {
          category: 'portfolio',
          label: section
        });
      }
    });
  }
  trackGalleryInteractions() {
    document.addEventListener('click', (event) => {
      if (!this.consentGiven) return;
      const galleryItem = event.target.closest('.gallery-item, .work-item');
      if (galleryItem) {
        this.trackEvent('gallery_interaction', {
          category: 'engagement',
          label: 'gallery_item_click'
        });
      }
      const carouselBtn = event.target.closest('.carousel-btn');
      if (carouselBtn) {
        this.trackEvent('carousel_interaction', {
          category: 'engagement',
          label: carouselBtn.classList.contains('next') ? 'next' : 'prev'
        });
      }
    });
  }
  trackContactFormSubmissions() {
    document.addEventListener('submit', (event) => {
      if (!this.consentGiven) return;
      const form = event.target;
      if (form.id === 'contact-form' || form.classList.contains('contact-form')) {
        this.trackEvent('form_submit', {
          category: 'contact',
          label: 'contact_form'
        });
      }
    });
  }
}
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => {
    window.beatrizAnalytics = new BeatrizAnalytics();
  }, 1000);
});
window.AnalyticsConsent = AnalyticsConsent;
window.BeatrizAnalytics = BeatrizAnalytics;

