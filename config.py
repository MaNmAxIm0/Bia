# config.py

from pathlib import Path

# --- Caminhos e Remotes ---
DRIVE_REMOTE_PATH = "Drive:Portfólio Bia"
R2_REMOTE_PATH = "R2:bia-portfolio-assets"
R2_PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
LOCAL_ASSETS_DIR = Path("local_assets")
PROCESSED_ASSETS_DIR = Path("processed_assets")

# --- Geração de Ficheiros ---
JSON_OUTPUT_FILE = Path("data.json")
MANIFEST_OUTPUT_FILE = Path("r2_file_manifest.txt")
FAILED_FILES_LOG = Path("failed_files.log")

# --- Configurações da Marca de Água ---
WATERMARK_TEXT = "© Beatriz Rodrigues"
WATERMARK_FONT_PATH = "fonts/Montserrat-Medium.ttf"
WATERMARK_COLOR_RGB = (255, 255, 255)  # Branco
WATERMARK_OPACITY = 200  # Opacidade de 0 (transparente) a 255 (opaco)

# --- Parâmetros de Processamento ---
# Proporção da LARGURA da imagem para o tamanho da fonte
IMG_WATERMARK_FONT_RATIO = 0.04
# Proporção da ALTURA do vídeo para o tamanho da fonte (mantendo consistência com o original)
VID_WATERMARK_FONT_RATIO = 0.03
# Margem para a marca de água como proporção da dimensão correspondente
MARGIN_RATIO = 0.02
# Qualidade do JPEG para imagens processadas e thumbnails
IMAGE_QUALITY = 90

# --- Configurações de Thumbnail de Vídeo ---
THUMBNAIL_WIDTH = 1280  # Largura alvo em pixels
THUMBNAIL_TIMESTAMP = "00:00:02"  # Ponto no vídeo para extrair o frame

# --- Filtros de Ficheiros ---
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi']
