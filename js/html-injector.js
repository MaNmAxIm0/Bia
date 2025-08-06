document.addEventListener("DOMContentLoaded", function() {
  const headerPlaceholder = document.getElementById('header-placeholder');
  const footerPlaceholder = document.getElementById('footer-placeholder');
  if (!headerPlaceholder && !footerPlaceholder) {
    return;
  }

  // Determinar o caminho relativo baseado na localização atual
  const currentPath = window.location.pathname;
  let relativePath = '';
  
  // Contar quantas pastas precisamos subir baseado no caminho atual
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
  
  const headerPath = `${relativePath}cabecalho.html`;
  const footerPath = `${relativePath}rodape.html`;

  console.log('Current path:', currentPath);
  console.log('Calculated depth:', depth);
  console.log('Relative path:', relativePath);
  console.log('Header path:', headerPath);
  console.log('Footer path:', footerPath);

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
});      .catch(error => reject(error));
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

