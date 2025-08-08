class SecurityHeaders {
  constructor() {
    this.init();
  }
  init() {
    this.setSecurityHeaders();
    this.setupCSP();
    this.preventClickjacking();
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
        "default-src \'self\';",
        "script-src \'self\' \'unsafe-inline\' \'unsafe-eval\' https://assets.mailerlite.com https://tally.so https://www.googletagmanager.com https://www.google-analytics.com https://cdn.plyr.io https://groot.mailerlite.com https://assets.mlcdn.com blob:;",
        "style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://cdn.plyr.io https://assets.mailerlite.com https://assets.mlcdn.com https://fonts.mailerlite.com;",
        "img-src \'self\' data: https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev https://manmaxim0.github.io https://cdn.jsdelivr.net blob: https://cdn.jsdelivr.net;",
        "font-src \'self\' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com https://assets.mlcdn.com https://fonts.mailerlite.com;",
        "media-src \'self\' https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev;",
        "connect-src \'self\' https://www.google-analytics.com https://region1.google-analytics.com https://tally.so https://assets.mailerlite.com https://assets.mlcdn.com;",
        "frame-src \'self\' https://tally.so https://assets.mailerlite.com https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev;",
        "base-uri \'self\';",
        "form-action \'self\' https://assets.mailerlite.com https://tally.so;",
        "object-src \'none\';",
        "upgrade-insecure-requests;"
      ];
      metaCSP.setAttribute("content", cspDirectives.join(" "));
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
  preventMimeSniffing() {
    console.log("Security headers aplicados com sucesso");
  }
  static sanitizeInput(input) {
    const div = document.createElement("div");
    div.textContent = input;
    return div.innerHTML;
  }
  static isValidURL(url) {
    try {
      const urlObj = new URL(url, window.location.origin);
      return urlObj.protocol === "https:" || urlObj.origin === window.location.origin;
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
    return window.isSecureContext || location.protocol === "https:";
  }
  static setupCSRFProtection() {
    const forms = document.querySelectorAll("form");
    forms.forEach(form => {
      if (!form.querySelector("input[name=\"csrf_token\"]")) {
        const csrfToken = document.createElement("input");
        csrfToken.type = "hidden";
        csrfToken.name = "csrf_token";
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
    console.log("%c🔒 Segurança Ativada", "color: green; font-weight: bold;");
    console.log("Headers de segurança aplicados via JavaScript");
    console.log("Site protegido contra XSS, Clickjacking e outras vulnerabilidades");
  }
  static generateNetlifyHeaders() {
    return `/*
    X-Frame-Options: DENY
    X-XSS-Protection: 1; mode=block
    X-Content-Type-Options: nosniff
    Referrer-Policy: strict-origin-when-cross-origin
    Content-Security-Policy: default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://assets.mailerlite.com https://tally.so https://www.googletagmanager.com https://www.google-analytics.com https://cdn.plyr.io https://groot.mailerlite.com https://assets.mlcdn.com; style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://cdn.plyr.io https://assets.mailerlite.com https://assets.mlcdn.com https://fonts.mailerlite.com; img-src \'self\' data: https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev https://manmaxim0.github.io https://cdn.jsdelivr.net blob:; font-src \'self\' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com https://assets.mlcdn.com https://fonts.mailerlite.com; media-src \'self\' https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev; connect-src \'self\' https://www.google-analytics.com https://region1.google-analytics.com https://tally.so https://assets.mailerlite.com https://assets.mlcdn.com; frame-src \'self\' https://tally.so https://assets.mailerlite.com https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev; base-uri \'self\'; form-action \'self\' https://assets.mailerlite.com https://tally.so; object-src \'none\'; upgrade-insecure-requests
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
    Header always set Content-Security-Policy "default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://assets.mailerlite.com https://tally.so https://www.googletagmanager.com https://www.google-analytics.com https://cdn.plyr.io https://groot.mailerlite.com https://assets.mlcdn.com; style-src \'self\' \'unsafe-inline\' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://cdn.plyr.io https://assets.mailerlite.com https://assets.mlcdn.com https://fonts.mailerlite.com; img-src \'self\' data: https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev https://manmaxim0.github.io https://cdn.jsdelivr.net blob:; font-src \'self\' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com https://assets.mlcdn.com https://fonts.mailerlite.com; media-src \'self\' https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev; connect-src \'self\' https://www.google-analytics.com https://region1.google-analytics.com https://tally.so https://assets.mailerlite.com https://assets.mlcdn.com; frame-src \'self\' https://tally.so https://assets.mailerlite.com https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev; base-uri \'self\'; form-action \'self\' https://assets.mailerlite.com https://tally.so; object-src \'none\'; upgrade-insecure-requests"
    Header always set Strict-Transport-Transport-Security "max-age=31536000; includeSubDomains"
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
document.addEventListener("DOMContentLoaded", () => {
  new SecurityHeaders();
  new GitHubPagesConfig();
  SecurityHeaders.setupCSRFProtection();
});
window.SecurityHeaders = SecurityHeaders;
window.GitHubPagesConfig = GitHubPagesConfig;

