document.addEventListener("DOMContentLoaded", function() {
  // Deteta o idioma da página atual com base no URL
  const path = window.location.pathname;
  const lang = path.includes('/en/') ? 'en' : 'pt';

  // Define os nomes dos ficheiros com base no idioma
  const headerFile = lang === 'en' ? 'header.html' : 'cabecalho.html';
  const footerFile = lang === 'en' ? 'footer.html' : 'rodape.html';

  // Define os caminhos completos para os ficheiros de include
  const headerPath = `../../includes/${headerFile}`;
  const footerPath = `../../includes/${footerFile}`;

  // Função para carregar e injetar o HTML
  const loadHTML = (filePath, placeholderId) => {
    fetch(filePath)
      .then(response => {
        if (!response.ok) throw new Error(`Ficheiro não encontrado: ${filePath}`);
        return response.text();
      })
      .then(data => {
        const placeholder = document.getElementById(placeholderId);
        if (placeholder) {
          placeholder.innerHTML = data;
          // Após injetar o cabeçalho, configura o link de troca de idioma
          if (placeholderId === 'header-placeholder') {
            setupLanguageSwitcher();
          }
        } else {
          console.error(`Erro: Placeholder com ID "${placeholderId}" não foi encontrado.`);
        }
      })
      .catch(error => console.error(`Erro ao carregar ${placeholderId}:`, error));
  };

  // Função para fazer o seletor de idioma funcionar corretamente
  const setupLanguageSwitcher = () => {
    const currentPath = window.location.pathname; // ex: /html/pt/fotos.html
    
    // Mapeamento de nomes de ficheiros entre idiomas
    const pageMap = {
      'index.html': 'index.html',
      'apresentacoes.html': 'presentations.html',
      'contactos.html': 'contacts.html',
      'designs.html': 'designs.html',
      'fotos.html': 'photos.html',
      'sobre-mim.html': 'about-me.html',
      'videos.html': 'videos.html'
    };

    const linkEn = document.querySelector('.lang-en-link');
    const linkPt = document.querySelector('.lang-pt-link');

    if (lang === 'pt' && linkEn) {
      const currentPageFile = currentPath.split('/').pop();
      const equivalentEnFile = pageMap[currentPageFile] || 'index.html';
      linkEn.href = `../en/${equivalentEnFile}`;
    } else if (lang === 'en' && linkPt) {
      const currentPageFile = currentPath.split('/').pop();
      // Inverte o mapeamento para encontrar o ficheiro em português
      const equivalentPtFile = Object.keys(pageMap).find(key => pageMap[key] === currentPageFile) || 'index.html';
      linkPt.href = `../pt/${equivalentPtFile}`;
    }
  };

  // Carrega o cabeçalho e o rodapé corretos
  loadHTML(headerPath, 'header-placeholder');
  loadHTML(footerPath, 'footer-placeholder');
});
