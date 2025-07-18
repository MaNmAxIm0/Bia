# config.py

# --- Configurações Gerais de Diretórios ---
# Caminho correto para a sua pasta no Google Drive
SOURCE_RCLONE_PATH = "Drive:Portfólio Bia"
# O nome do bucket de destino no R2
DEST_RCLONE_PATH = "R2:bia-portfolio-assets"
# Pastas locais temporárias usadas pelo workflow
LOCAL_DOWNLOAD_DIR = "local_assets"
LOCAL_PROCESSED_DIR = "processed_assets"

# --- Configurações da Marca de Água ---
WATERMARK_TEXT = "© Beatriz Rodrigues"
WATERMARK_OPACITY = 255 # 100% opaco
WATERMARK_FONT_PATH = "fonts/Montserrat-Medium.ttf"
WATERMARK_COLOR_RGB = (255, 255, 255) # Branco

# --- Configurações Avançadas de Posicionamento e Tamanho ---
FONT_SIZE_RATIO = 0.03
POSITION_HORIZONTAL = 'right'
POSITION_VERTICAL = 'bottom'
MARGIN_RATIO = 0.02

# --- Configurações de Filtros ---
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mp4', '.mov']
EXCLUDE_PATTERNS = []