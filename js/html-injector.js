document.addEventListener("DOMContentLoaded", function() {
  const headerPlaceholder = document.getElementById('header-placeholder');
  const footerPlaceholder = document.getElementById('footer-placeholder');
  if (!headerPlaceholder && !footerPlaceholder) {
    return;
  }

  // Determinar o caminho relativo baseado na localização atual - GitHub Pages
  const currentPath = window.location.pathname;
  let relativePath = '';
  
  // Para GitHub Pages, o site está em /Bia/, então precisamos considerar isso
  const isGitHubPages = window.location.hostname.includes('github.io');
  const repoName = '/Bia/';
  
  if (isGitHubPages) {
    // No GitHub Pages, determinar caminho baseado na estrutura /Bia/...
    if (currentPath === repoName || currentPath === repoName + 'index.html') {
      // Estamos na raiz do repositório
      relativePath = '';
    } else if (currentPath.includes(repoName + 'pt/') || currentPath.includes(repoName + 'en/') || currentPath.includes(repoName + 'es/')) {
      // Estamos numa pasta de idioma
      const pathAfterRepo = currentPath.replace(repoName, '');
      const pathParts = pathAfterRepo.split('/').filter(part => part !== '');
      
      if (pathParts.length >= 2) {
        // Estamos numa subpasta dentro do idioma (ex: /Bia/pt/apresentacoes/)
        relativePath = '../../';
      } else {
        // Estamos diretamente na pasta do idioma (ex: /Bia/pt/)
        relativePath = '../';
      }
    } else {
      // Fallback para raiz
      relativePath = '';
    }
  } else {
    // Para desenvolvimento local, usar lógica anterior
    const pathParts = currentPath.split('/').filter(part => part !== '');
    
    // Remover o nome do ficheiro se existir (ex: index.html)
    let depth = pathParts.length;
    if (pathParts[pathParts.length - 1] && pathParts[pathParts.length - 1].includes('.html')) {
      depth = depth - 1;
    }
    
    // Se estamos numa subpasta, precisamos de voltar atrás
    if (depth > 0) {
      relativePath = '../'.repeat(depth);
    }
  }
  
  const headerPath = `${relativePath}cabecalho.html`;
  const footerPath = `${relativePath}rodape.html`;

  console.log('GitHub Pages mode (injector):', isGitHubPages);
  console.log('Current path (injector):', currentPath);
  console.log('Calculated relative path (injector):', relativePath);
  console.log('Header path (injector):', headerPath);
  console.log('Footer path (injector):', footerPath);

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
