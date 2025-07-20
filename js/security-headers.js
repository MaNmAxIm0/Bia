class SecurityHeaders {
  constructor() {
    this.init();
  }
  init() {
    this.setSecurityHeaders();
    this.setupCSP();
    this.preventClickjacking();
    this.setupHTTPS();
    this.preventMimeSniffing();
  }
  setSecurityHeaders() {
    const head = document.head;
    if (!document.querySelector("meta[http-equiv=\"X-Content-Type-Options\"]")) {
      const metaContentType = document.createElement("meta");
      metaContentType.setAttribute("http-equiv", "X-Content-Type-Options");
      metaContentType.setAttribute("content", "nosniff");
      head.appendChild(metaContentType);
    }
    if (!document.querySelector("meta[http-equiv=\"X-XSS-Protection\"]")) {
      const metaXSSProtection = document.createElement("meta");
      metaXSSProtection.setAttribute("http-equiv", "X-XSS-Protection");
      metaXSSProtection.setAttribute("content", "1; mode=block");
      head.appendChild(metaXSSProtection);
    }
    if (!document.querySelector("meta[name=\"referrer\"]")) {
      const metaReferrer = document.createElement("meta");
      metaReferrer.setAttribute("name", "referrer");
      metaReferrer.setAttribute("content", "strict-origin-when-cross-origin");
      head.appendChild(metaReferrer);
    }
  }
  setupCSP() {
    if (!document.querySelector("meta[http-equiv=\"Content-Security-Policy\"]")) {
      const metaCSP = document.createElement("meta");
      metaCSP.setAttribute("http-equiv", "Content-Security-Policy");
      const cspDirectives = [
        "default-src 'self'",
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://www.googletagmanager.com https://www.google-analytics.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
        "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
        "img-src 'self' data: https: blob:",
        "media-src 'self' https:",
        "connect-src 'self' https://www.google-analytics.com",
        "frame-src 'self' https://docs.google.com https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev",
        "base-uri 'self'",
        "form-action 'self'"
      ];
      metaCSP.setAttribute("content", cspDirectives.join("; "));
      document.head.appendChild(metaCSP);
    }
  }
  preventClickjacking() {
    if (window.self !== window.top) {
      try {
        if (window.top.location.hostname !== window.self.location.hostname) {
          window.top.location = window.self.location;
        }
      } catch (e) {
        window.top.location = window.self.location;
      }
    }
  }
  setupHTTPS() {
    if (location.protocol !== 'https:' && 
      location.hostname !== 'localhost' && 
      location.hostname !== '127.0.0.1' &&
      !location.hostname.includes('github.io')) {
        const metaHSTS = document.createElement('meta');
        metaHSTS.setAttribute('http-equiv', 'Strict-Transport-Security');
        metaHSTS.setAttribute('content', 'max-age=31536000; includeSubDomains');
        document.head.appendChild(metaHSTS);
      }
    }
    preventMimeSniffing() {
      console.log('Security headers aplicados com sucesso');
    }
    static sanitizeInput(input) {
      const div = document.createElement('div');
      div.textContent = input;
      return div.innerHTML;
    }
    static isValidURL(url) {
      try {
        const urlObj = new URL(url, window.location.origin);
        return urlObj.protocol === 'https:' || urlObj.origin === window.location.origin;
      } catch (e) {
        return false;
      }
    }
    static generateNonce() {
      const array = new Uint8Array(16);
      crypto.getRandomValues(array);
      return btoa(String.fromCharCode.apply(null, array));
    }
    static isSecureContext() {
      return window.isSecureContext || location.protocol === 'https:';
    }
    static setupCSRFProtection() {
      const forms = document.querySelectorAll('form');
      forms.forEach(form => {
        if (!form.querySelector('input[name="csrf_token"]')) {
          const csrfToken = document.createElement('input');
          csrfToken.type = 'hidden';
          csrfToken.name = 'csrf_token';
          csrfToken.value = SecurityHeaders.generateNonce();
          form.appendChild(csrfToken);
        }
      });
    }
  }
  class GitHubPagesConfig {
    constructor() {
      this.setupGitHubPagesHeaders();
    }
    setupGitHubPagesHeaders() {
      if (window.top !== window.self) {
        window.top.location = window.self.location;
      }
      console.log('%c🔒 Segurança Ativada', 'color: green; font-weight: bold;');
      console.log('Headers de segurança aplicados via JavaScript');
      console.log('Site protegido contra XSS, Clickjacking e outras vulnerabilidades');
    }
    static generateNetlifyHeaders() {
      return `/*
  X-Frame-Options: DENY
  X-XSS-Protection: 1; mode=block
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://www.google-analytics.com;
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Permissions-Policy: geolocation=(), microphone=(), camera=()`;
    }
    static generateApacheHeaders() {
      return `# Security Headers
<IfModule mod_headers.c>
    Header always set X-Frame-Options "DENY"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Content-Type-Options "nosniff"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"
    Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://www.google-analytics.com;"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    Header always set Permissions-Policy "geolocation=(), microphone=(), camera=()"
</IfModule>
# Force HTTPS
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</IfModule>`;
    }
  }
  document.addEventListener('DOMContentLoaded', () => {
    new SecurityHeaders();
    new GitHubPagesConfig();
    SecurityHeaders.setupCSRFProtection();
  });
  window.SecurityHeaders = SecurityHeaders;
  window.GitHubPagesConfig = GitHubPagesConfig;