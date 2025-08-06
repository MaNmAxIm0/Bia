document.addEventListener("DOMContentLoaded", function() {
  const headerPlaceholder = document.getElementById('header-placeholder');
  const footerPlaceholder = document.getElementById('footer-placeholder');
  if (!headerPlaceholder && !footerPlaceholder) {
    return;
  }

  // Determinar o caminho relativo baseado na localização atual
  const currentPath = window.location.pathname;
  let relativePath = '';
  
  // Se estivermos numa subpasta (pt/, en/, es/), precisamos de voltar atrás
  if (currentPath.includes('/pt/') || currentPath.includes('/en/') || currentPath.includes('/es/')) {
    relativePath = '../';
  }
  
  const headerPath = `${relativePath}cabecalho.html`;
  const footerPath = `${relativePath}rodape.html`;

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

  if (footerPlaceholder) {
    loadHTML(footerPath, footerPlaceholder)
    .catch(error => console.error(`Erro ao carregar rodapé:`, error));
  }

  if (headerPlaceholder) {
    loadHTML(headerPath, headerPlaceholder)
    .then(() => {
      document.dispatchEvent(new CustomEvent('headerLoaded'));
    })
    .catch(error => console.error(`Erro ao carregar cabeçalho:`, error));
  }
});

