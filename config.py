# config.py

# --- Configurações Gerais de Diretórios ---
# A origem dos ficheiros é a pasta "Portfólio Bia" no seu Google Drive.
# Certifique-se de que o nome da pasta está exatamente correto.
SOURCE_RCLONE_PATH = "Drive:Portfólio Bia"

# O destino dos ficheiros processados é um bucket no Cloudflare R2.
DEST_RCLONE_PATH = "R2:bia-portfolio-assets-watermarked"

# Nomes dos diretórios locais que serão usados durante a execução.
LOCAL_DOWNLOAD_DIR = "local_assets"
LOCAL_PROCESSED_DIR = "processed_assets"


# --- Configurações da Marca de Água ---
WATERMARK_TEXT = "© Beatriz Rodrigues."
# Opacidade: 255 é 100% opaco. Um valor como 200 (aprox. 80%) é mais subtil.
WATERMARK_OPACITY = 200
WATERMARK_FONT_PATH = "fonts/Montserrat-Medium.ttf"
WATERMARK_COLOR_RGB = (255, 255, 255) # Cor da fonte: Branco


# --- Configurações Avançadas de Posicionamento e Tamanho ---
FONT_SIZE_RATIO = 0.03    # Tamanho da fonte como 3% da altura do vídeo/imagem.
POSITION_HORIZONTAL = 'right'  # Posição horizontal: 'left', 'center', ou 'right'.
POSITION_VERTICAL = 'bottom'   # Posição vertical: 'top', 'middle', ou 'bottom'.
MARGIN_RATIO = 0.02       # Margem de 2% em relação às bordas.


# --- Configurações de Filtros de Ficheiros ---
# Extensões de ficheiros que serão processados.
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mp4', '.mov']

# Lista de padrões de ficheiros a ignorar durante o processamento.
# Exemplo: ['*thumb.jpg', 'preview.*']
EXCLUDE_PATTERNS = []
