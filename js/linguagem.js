import { setLanguage, getTranslation, getCurrentLanguage } from './gestor-de-linguagem.js';

/**
 * Aplica as traduções a todos os elementos da página que possuem o atributo `data-lang-key`.
 */
export function applyTranslations() {
    // Traduz o título da página usando a chave definida no body
    const pageTitleKey = document.body.getAttribute('data-page-title-key');
    if (pageTitleKey) {
        document.title = getTranslation(pageTitleKey);
    }

    // Itera sobre todos os elementos que precisam de tradução
    document.querySelectorAll('[data-lang-key]').forEach(element => {
        const key = element.dataset.langKey;
        const translation = getTranslation(key);

        // Não traduz os links do menu de idiomas, pois eles já têm o texto correto
        if (element.classList.contains('lang-option')) {
            return;
        }

        // Trata de placeholders em inputs e textareas
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            if (element.placeholder) {
                element.placeholder = translation;
            }
        } 
        // Trata de atributos 'aria-label' para acessibilidade
        else if (key === 'toggle_navigation' || key === 'close') {
            element.setAttribute('aria-label', translation);
        }
        // Usa innerHTML para preservar tags como &copy; ou <i>
        else {
            element.innerHTML = translation;
        }
    });
}

/**
 * Função principal que é executada quando o DOM da página é carregado.
 * Deteta o idioma, define-o e aplica as traduções.
 */
document.addEventListener('DOMContentLoaded', () => {
    // --- LÓGICA DE DETEÇÃO DE IDIOMA A PARTIR DO URL (ROBUSTA) ---
    let langFromPath = 'pt'; // Define 'pt' como idioma padrão
    const pathSegments = window.location.pathname.split('/');

    // Procura por 'pt', 'en', ou 'es' na parte correta do URL (ex: /html/es/...)
    const langCodes = ['pt', 'en', 'es'];
    for (const code of langCodes) {
        if (pathSegments.includes(code)) {
            langFromPath = code;
            break; // Para assim que encontrar o primeiro código de idioma
        }
    }

    // 1. Define o idioma detetado no gestor de linguagem
    setLanguage(langFromPath); 

    // 2. Aplica as traduções a todo o conteúdo estático da página
    applyTranslations();

    // 3. Adiciona os listeners de clique aos links de idioma no cabeçalho.
    //    Isto é feito após o evento 'headerLoaded' ser disparado pelo html-injector.js,
    //    garantindo que o cabeçalho já foi injetado na página.
    document.addEventListener('headerLoaded', () => {
        document.querySelectorAll('.language-options .lang-option').forEach(button => {
            // Remove listeners antigos para evitar duplicação, se houver
            button.replaceWith(button.cloneNode(true));
        });

        // Adiciona novos listeners
        document.querySelectorAll('.language-options .lang-option').forEach(button => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                
                const targetLang = button.dataset.lang;
                
                // Define o novo idioma preferido no localStorage
                setLanguage(targetLang); 
                
                // Redireciona para a página no idioma selecionado
                window.location.href = button.href; 
            });
        });
    });
});
