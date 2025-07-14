document.addEventListener("DOMContentLoaded", function() {
    const headerPlaceholder = document.getElementById('header-placeholder');
    const footerPlaceholder = document.getElementById('footer-placeholder');

    if (!headerPlaceholder && !footerPlaceholder) {
        return; // Sai se não houver placeholders na página
    }

    // Caminhos atualizados para buscar os ficheiros a partir da pasta /html/
    // Sobe um nível a partir da pasta do idioma (ex: /pt/) para a pasta /html/
    const headerPath = `../cabecalho.html`;
    const footerPath = `../rodape.html`;

    const loadHTML = (filePath, placeholder) => {
        return new Promise((resolve, reject) => {
            if (!placeholder) {
                resolve();
                return;
            }
            fetch(filePath)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Ficheiro não encontrado: ${filePath}. Verifique o caminho e o nome do ficheiro.`);
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

    // Carrega o cabeçalho e dispara um evento para notificar outros scripts
    if (headerPlaceholder) {
        loadHTML(headerPath, headerPlaceholder)
            .then(() => {
                document.dispatchEvent(new CustomEvent('headerLoaded'));
            })
            .catch(error => console.error(`Erro ao carregar cabeçalho:`, error));
    }
});
