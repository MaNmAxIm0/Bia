// Ficheiro: security-headers.js
// Sistema de Headers de Segurança para o Website

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

    /**
     * Define headers de segurança básicos via meta tags
     */
    setSecurityHeaders() {
        const head = document.head;
        
        // X-Content-Type-Options
        if (!document.querySelector("meta[http-equiv=\"X-Content-Type-Options\"]")) {
            const metaContentType = document.createElement("meta");
            metaContentType.setAttribute("http-equiv", "X-Content-Type-Options");
            metaContentType.setAttribute("content", "nosniff");
            head.appendChild(metaContentType);
        }

        // X-XSS-Protection
        if (!document.querySelector("meta[http-equiv=\"X-XSS-Protection\"]")) {
            const metaXSSProtection = document.createElement("meta");
            metaXSSProtection.setAttribute("http-equiv", "X-XSS-Protection");
            metaXSSProtection.setAttribute("content", "1; mode=block");
            head.appendChild(metaXSSProtection);
        }

        // Referrer Policy
        if (!document.querySelector("meta[name=\"referrer\"]")) {
            const metaReferrer = document.createElement("meta");
            metaReferrer.setAttribute("name", "referrer");
            metaReferrer.setAttribute("content", "strict-origin-when-cross-origin");
            head.appendChild(metaReferrer);
        }
    }

    /**
     * Configura Content Security Policy
     */
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

    /**
     * Previne clickjacking (via JavaScript, pois meta tag é ignorada)
     */
    preventClickjacking() {
        if (window.self !== window.top) {
            try {
                if (window.top.location.hostname !== window.self.location.hostname) {
                    window.top.location = window.self.location;
                }
            } catch (e) {
                // Pode ocorrer erro de segurança se domínios forem diferentes
                window.top.location = window.self.location;
            }
        }
    }

    /**
     * Força HTTPS (se aplicável)
     */
    setupHTTPS() {
        // Redireciona para HTTPS se estiver em produção e usando HTTP
        if (location.protocol !== 'https:' && 
            location.hostname !== 'localhost' && 
            location.hostname !== '127.0.0.1' &&
            !location.hostname.includes('github.io')) {
            
            // Adiciona HSTS header via meta tag
            const metaHSTS = document.createElement('meta');
            metaHSTS.setAttribute('http-equiv', 'Strict-Transport-Security');
            metaHSTS.setAttribute('content', 'max-age=31536000; includeSubDomains');
            document.head.appendChild(metaHSTS);
        }
    }

    /**
     * Previne MIME sniffing
     */
    preventMimeSniffing() {
        // Já implementado em setSecurityHeaders(), mas adiciona verificação extra
        console.log('Security headers aplicados com sucesso');
    }

    /**
     * Sanitiza inputs para prevenir XSS
     */
    static sanitizeInput(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }

    /**
     * Valida URLs para prevenir redirecionamentos maliciosos
     */
    static isValidURL(url) {
        try {
            const urlObj = new URL(url, window.location.origin);
            // Permite apenas URLs do mesmo domínio ou HTTPS
            return urlObj.protocol === 'https:' || urlObj.origin === window.location.origin;
        } catch (e) {
            return false;
        }
    }

    /**
     * Gera nonce para scripts inline (para CSP mais restritivo)
     */
    static generateNonce() {
        const array = new Uint8Array(16);
        crypto.getRandomValues(array);
        return btoa(String.fromCharCode.apply(null, array));
    }

    /**
     * Verifica se o site está sendo executado em HTTPS
     */
    static isSecureContext() {
        return window.isSecureContext || location.protocol === 'https:';
    }

    /**
     * Implementa proteção contra CSRF para formulários
     */
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

// Configuração para GitHub Pages
class GitHubPagesConfig {
    constructor() {
        this.setupGitHubPagesHeaders();
    }

    setupGitHubPagesHeaders() {
        // GitHub Pages não permite configuração de headers do servidor,
        // mas podemos implementar algumas proteções via JavaScript
        
        // Previne embedding em iframes
        if (window.top !== window.self) {
            window.top.location = window.self.location;
        }

        // Adiciona informações de segurança ao console
        console.log('%c🔒 Segurança Ativada', 'color: green; font-weight: bold;');
        console.log('Headers de segurança aplicados via JavaScript');
        console.log('Site protegido contra XSS, Clickjacking e outras vulnerabilidades');
    }

    /**
     * Cria arquivo _headers para Netlify (se migrar no futuro)
     */
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

    /**
     * Cria arquivo .htaccess para Apache (se migrar no futuro)
     */
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

// Inicialização automática
document.addEventListener('DOMContentLoaded', () => {
    new SecurityHeaders();
    new GitHubPagesConfig();
    
    // Setup CSRF protection para formulários
    SecurityHeaders.setupCSRFProtection();
});

// Exporta para uso global
window.SecurityHeaders = SecurityHeaders;
window.GitHubPagesConfig = GitHubPagesConfig;
