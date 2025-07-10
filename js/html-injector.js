document.addEventListener("DOMContentLoaded", function() {
  // Função para carregar um ficheiro e inseri-lo num placeholder
  const loadHTML = (filePath, placeholderId) => {
    fetch(filePath)
      .then(response => {
        if (!response.ok) {
          // Lança um erro para ser apanhado pelo .catch()
          throw new Error(`Ficheiro não encontrado: ${filePath}`);
        }
        return response.text();
      })
      .then(data => {
        const placeholder = document.getElementById(placeholderId);
        if (placeholder) {
          placeholder.innerHTML = data;
        } else {
          // Erro se o placeholder não existir na página
          console.error(`Erro: Placeholder com ID "${placeholderId}" não foi encontrado.`);
        }
      })
      .catch(error => {
        // Mostra o erro na consola do navegador
        console.error(`Erro ao carregar ${placeholderId}:`, error);
      });
  };

  // Carrega o cabeçalho e o rodapé
  // O caminho '../../' funciona porque todas as suas páginas estão 2 níveis abaixo da raiz
  loadHTML('../../includes/cabecalho.html', 'header-placeholder');
  loadHTML('../../includes/rodape.html', 'footer-placeholder');
});
