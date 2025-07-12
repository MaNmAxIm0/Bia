// js/configuracoes.js

// O caminho para o nosso ficheiro de dados local.
// Este caminho é relativo à raiz do site.
export const DATA_JSON_URL = './data.json'; // Ajustado para ser relativo à raiz

// Helper function para criar um elemento de marca d'água.
// Mantemos esta função aqui porque é uma configuração/ferramenta útil.
export function createWatermarkElement() {
    const watermarkDiv = document.createElement('div');
    watermarkDiv.classList.add('image-watermark');
    watermarkDiv.textContent = '© Beatriz Rodrigues';
    return watermarkDiv;
}
