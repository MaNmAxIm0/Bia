export function getDirectGoogleDriveUrl(url) {
  if (url.includes('drive.google.com/uc?') ||
  url.includes('lh3.googleusercontent.com/d/') ||
  url.includes('drive.google.com/thumbnail?')) {
    return url;
  }
  const driveIdMatch = url.match(/(?:id=|file\/d\/|document\/d\/|presentation\/d\/)([a-zA-Z0-9_-]+)/);
  if (driveIdMatch && driveIdMatch[1]) {
    const fileId = driveIdMatch[1];
    return `https://drive.google.com/uc?id=${fileId}&export=view`;
  }
  return url;
}

export function createWatermarkElement() {
  const watermarkDiv = document.createElement('div');
  watermarkDiv.classList.add('image-watermark');
  watermarkDiv.textContent = '© Beatriz Rodrigues';
  return watermarkDiv;
}