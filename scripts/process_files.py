import subprocess
import json
import os
from PIL import Image, ImageDraw, ImageFont, ExifTags

# --- Configuração ATUALIZADA ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__ ), 'Montserrat-Medium.ttf')
TEMP_DIR = "temp_files"

# Novos nomes para as pastas no R2 (sem underscore, com letra maiúscula)
WATERMARKED_DIR_IMG = "WatermarkedImages"
WATERMARKED_DIR_VID = "WatermarkedVideos"
THUMBNAILS_DIR = "Thumbnails" # Usado para construir a URL da thumbnail

# Mapeia a orientação EXIF
EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)

# --- Funções de Marca de Água ATUALIZADAS ---

def add_watermark_to_image(input_path, output_path):
    """Aplica uma marca de água de texto a uma imagem com tamanho proporcional."""
    try:
        with Image.open(input_path).convert("RGBA") as base:
            draw = ImageDraw.Draw(base)
            
            # --- LÓGICA DE TAMANHO DINÂMICO ---
            # O tamanho da fonte será 5% da largura da imagem (o dobro dos 2.5% anteriores).
            # Com um tamanho mínimo de 20px para imagens muito pequenas.
            font_size = max(20, int(base.width * 0.05))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except IOError:
                print(f"AVISO: Fonte não encontrada em '{FONT_PATH}'. Usando fonte padrão.")
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            textwidth = bbox[2] - bbox[0]
            textheight = bbox[3] - bbox[1]

            margin = int(base.width * 0.015) # Margem também proporcional
            x = base.width - textwidth - margin
            y = base.height - textheight - margin
            
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill="black")
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))
            
            base.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"ERRO ao aplicar marca de água na imagem '{input_path}': {e}")
        return False

def add_watermark_to_video(input_path, output_path, video_width):
    """Aplica uma marca de água de texto a um vídeo com tamanho proporcional."""
    print(f"A aplicar marca de água no vídeo: {input_path}")
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    
    # --- LÓGICA DE TAMANHO DINÂMICO PARA VÍDEOS ---
    # O tamanho da fonte será ~4% da largura do vídeo (o dobro do tamanho fixo anterior de 24px para um vídeo 1080p).
    font_size = max(24, int(video_width * 0.04))
    margin = int(video_width * 0.015) # Margem proporcional

    command = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.7:x=main_w-text_w-{margin}:y=main_h-text_h-{margin}:shadowcolor=black:shadowx=1:shadowy=1",
        "-c:a", "copy",
        "-y",
        output_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Marca de água aplicada com sucesso em '{output_path}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao aplicar marca de água no vídeo '{input_path}':")
        print(f"FFmpeg Stderr: {e.stderr}")
        return False

# --- Funções Auxiliares (sem alterações) ---
def get_file_list():
    print("A obter a lista de todos os ficheiros do R2...")
    command = ["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}\nStderr: {e.stderr}")
        return []

def get_dimensions(local_path, file_type):
    width, height = 0, 0
    if file_type in ['fotografias', 'designs']:
        try:
            with Image.open(local_path) as img:
                width, height = img.size
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif and EXIF_ORIENTATION_TAG in exif and exif[EXIF_ORIENTATION_TAG] in [5, 6, 7, 8]:
                        width, height = height, width
        except Exception as e:
            print(f"AVISO: Pillow não conseguiu processar a imagem '{local_path}'. Erro: {e}")
    elif file_type == 'videos':
        try:
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
        except Exception as e:
            print(f"AVISO: ffprobe não conseguiu obter dimensões para o vídeo '{local_path}'. Erro: {e}")
    return width, height

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2: return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else: return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}

# --- Função Principal ATUALIZADA ---
def process_files():
    all_files = get_file_list()
    if not all_files:
        print("Nenhum ficheiro encontrado no R2. A sair.")
        return

    for dir_path in [TEMP_DIR, os.path.join(TEMP_DIR, WATERMARKED_DIR_IMG), os.path.join(TEMP_DIR, WATERMARKED_DIR_VID)]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    output_data = {cat: [] for cat in CATEGORIES.values()}

    for path in all_files:
        # Ignora as novas pastas e ficheiros de sistema
        if any(x in path for x in ["desktop.ini", f"/{THUMBNAILS_DIR}/", f"/{WATERMARKED_DIR_IMG}/", f"/{WATERMARKED_DIR_VID}/"]) or not path:
            continue

        try:
            category_name, filename = path.split('/', 1)
        except ValueError:
            continue

        if category_name in CATEGORIES:
            category_key = CATEGORIES[category_name]
            local_original_path = os.path.join(TEMP_DIR, filename)
            
            try:
                subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(f"AVISO: Falha ao descarregar '{path}'. A ignorar. Erro: {e.stderr.decode()}")
                continue

            width, height = get_dimensions(local_original_path, category_key)
            orientation = "horizontal" if width >= height else "vertical"
            file_data = {"name": filename, "titles": parse_filename(filename), "orientation": orientation}

            if category_key in ["fotografias", "designs"]:
                base_name, _ = os.path.splitext(filename)
                watermarked_filename = f"{base_name}.png"
                local_watermarked_path = os.path.join(TEMP_DIR, WATERMARKED_DIR_IMG, watermarked_filename)
                
                if add_watermark_to_image(local_original_path, local_watermarked_path):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_IMG}/{watermarked_filename}"], check=True)
                    file_data["url"] = f"{PUBLIC_URL}/{WATERMARKED_DIR_IMG}/{watermarked_filename.replace(' ', '%20')}"
                    output_data[category_key].append(file_data)

            elif category_key == "videos":
                base_name, ext = os.path.splitext(filename)
                watermarked_filename = f"{base_name}_wm{ext}"
                local_watermarked_path = os.path.join(TEMP_DIR, WATERMARKED_DIR_VID, watermarked_filename)

                if add_watermark_to_video(local_original_path, local_watermarked_path, width):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}/{watermarked_filename}"], check=True)
                    file_data["url"] = f"{PUBLIC_URL}/{WATERMARKED_DIR_VID}/{watermarked_filename.replace(' ', '%20')}"
                    file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{base_name}.jpg".replace(' ', '%20')
                    output_data[category_key].append(file_data)
            
            os.remove(local_original_path)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    process_files()
