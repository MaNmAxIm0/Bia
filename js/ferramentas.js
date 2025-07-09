// Helper function to get direct Google Drive URL for embedding
export function getDirectGoogleDriveUrl(url) {
    // If it's already a direct 'uc' link or lh3 link, use it directly
    if (url.includes('drive.google.com/uc?') ||
        url.includes('lh3.googleusercontent.com/d/') ||
        url.includes('drive.google.com/thumbnail?')) {
        return url;
    }

    // Try to extract file ID from various Google Drive sharing/view/edit URLs
    // Covers: drive.google.com/file/d/FILE_ID/view, drive.google.com/file/d/FILE_ID/edit, etc.
    const driveIdMatch = url.match(/(?:id=|file\/d\/|document\/d\/|presentation\/d\/)([a-zA-Z0-9_-]+)/);

    if (driveIdMatch && driveIdMatch[1]) {
        const fileId = driveIdMatch[1];
        // This format is generally the most reliable for direct display in <img> tags
        return `https://drive.google.com/uc?id=${fileId}&export=view`;
    }

    // If no recognizable Google Drive ID pattern, return original URL (might be a direct image URL from elsewhere)
    return url;
}

// Helper function to create a watermark element
export function createWatermarkElement() {
    const watermarkDiv = document.createElement('div');
    watermarkDiv.classList.add('image-watermark');
    watermarkDiv.textContent = '© Beatriz Rodrigues';
    return watermarkDiv;
}