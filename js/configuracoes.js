export const DATA_JSON_URL = './data.json';
export function createWatermarkElement() {
  const watermarkDiv = document.createElement('div');
  watermarkDiv.classList.add('image-watermark');
  watermarkDiv.textContent = '© Beatriz Rodrigues';
  return watermarkDiv;
}