// js/html-injector.js (VERSÃO CORRIGIDA E FINAL)

document.addEventListener("DOMContentLoaded", function() {
    const headerPlaceholder = document.getElementById('header-placeholder');
    const footerPlaceholder = document.getElementById('footer-placeholder');

    if (!headerPlaceholder && !footerPlaceholder) {
        return; // Sai se não houver placeholders na página
    }

    // --- LÓGICA DE DETEÇÃO DE IDIOMA CORRIGIDA ---
    let lang = 'pt'; // Idioma padrão
    const pathname = window.location.pathname;

    if (pathname.includes('/en/')) {
        lang = 'en';
    } else if (pathname.includes('/es/')) {
        lang = 'es';
    }
    // Se não for 'en' nem 'es', assume-se 'pt'.

    // --- MAPEAMENTO DE FICHEIROS ---
    const fileMap = {
        pt: {
            header: 'cabecalho.html',
            footer: 'rodape.html'
        },
        en: {
            header: 'header.html',
            footer: 'footer.html'
        },
        es: {
            // Assumindo que os ficheiros para espanhol se chamarão assim
            header: 'cabecera.html', 
            footer: 'pie-de-pagina.html'
        }
    };

    const headerFile = fileMap[lang].header;
    const footerFile = fileMap[lang].footer;

    // Constrói os caminhos corretos
    const headerPath = `../../includes/${headerFile}`;
    const footerPath = `../../includes/${footerFile}`;

    // Função para carregar e injetar o HTML
    const loadHTML = (filePath, placeholder) => {
        return new Promise((resolve, reject) => {
            if (!placeholder) {
                resolve();
                return;
            }
            fetch(filePath)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Ficheiro não encontrado: ${filePath}. Verifique se o ficheiro existe no caminho correto.`);
                    }
                    return response.text();
                })
                .then(data => {
                    placeholder.innerHTML = data;
                    resolve();
                })
                .catch(error => reject(error));
        });
    };

    // Carrega o rodapé
    if (footerPlaceholder) {
        loadHTML(footerPath, footerPlaceholder)
            .catch(error => console.error(`Erro ao carregar rodapé:`, error));
    }

    // Carrega o cabeçalho e, DEPOIS, executa os scripts que dependem dele
    if (headerPlaceholder) {
        loadHTML(headerPath, headerPlaceholder)
            .then(() => {
                // O cabeçalho está 100% garantido no DOM neste ponto.
                if (typeof window.initializeMenu === 'function') {
                    window.initializeMenu();
                }
                if (typeof window.setupLanguageSwitcher === 'function') {
                    window.setupLanguageSwitcher(lang);
                }
                
                // !! ADICIONE ESTA LINHA !!
                // Avisa outros scripts que o cabeçalho foi carregado
                document.dispatchEvent(new CustomEvent('headerLoaded'));
            })
            .catch(error => console.error(`Erro ao carregar cabeçalho:`, error));
    }
});
