# config.py

# --- Configurações Gerais de Diretórios ---
SOURCE_RCLONE_PATH = "R2:bia-portfolio-assets"
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

# --- CORREÇÃO --- Adicionar padrões de exclusão para o Rclone aqui
# Cada item nesta lista será passado para o rclone com a flag --exclude
RCLONE_EXCLUDE_PATTERNS = [
    "Thumbnails/**",
    ".DS_Store",       # Exemplo: ignorar ficheiros do macOS
    "*.tmp",           # Exemplo: ignorar ficheiros temporários
]

# Padrões de exclusão para o processamento local (opcional, pode ser útil)
LOCAL_EXCLUDE_FILENAMES = []
