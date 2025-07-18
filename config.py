# config.py

# --- Configurações Gerais de Diretórios ---
# --- CORREÇÃO --- A origem agora é o Google Drive
# Substitua 'caminho/para/a/pasta' pelo caminho real da pasta no seu Google Drive
SOURCE_RCLONE_PATH = "Drive:caminho/para/a/pasta" 
DEST_RCLONE_PATH = "R2:bia-portfolio-assets-watermarked"
LOCAL_DOWNLOAD_DIR = "local_assets"
LOCAL_PROCESSED_DIR = "processed_assets"

# --- Configurações da Marca de Água ---
WATERMARK_TEXT = "© Beatriz Rodrigues."
WATERMARK_OPACITY = 200
WATERMARK_FONT_PATH = "fonts/Montserrat-Medium.ttf"
WATERMARK_COLOR_RGB = (255, 255, 255)

# --- Configurações Avançadas de Posicionamento e Tamanho ---
FONT_SIZE_RATIO = 0.03
POSITION_HORIZONTAL = 'right'
POSITION_VERTICAL = 'bottom'
MARGIN_RATIO = 0.02

# --- Configurações de Filtros de Ficheiros ---
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mp4', '.mov']

# Padrões de exclusão para o Rclone (pode manter ou ajustar)
RCLONE_EXCLUDE_PATTERNS = [
    "*.tmp",
]

# Padrões de exclusão para o processamento local
LOCAL_EXCLUDE_FILENAMES = []
