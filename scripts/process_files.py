import subprocess
import json
import os
from PIL import Image, ImageDraw, ImageFont, ExifTags

# --- Configuração ---
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
TEMP_DIR = "temp_files" # Pasta temporária para todos os ficheiros
WATERMARKED_DIR_IMG = "_watermarked_images"
WATERMARKED_DIR_VID = "_watermarked_videos"

# Mapeia a orientação EXIF
EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)

# --- Funções de Marca de Água ---

def add_watermark_to_image(input_path, output_path):
    """Aplica uma marca de água de texto a uma imagem."""
    try:
        with Image.open(input_path).convert("RGBA") as base:
            draw = ImageDraw.Draw(base)
            font_size = max(16, int(base.width * 0.025))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except IOError:
                print(f"AVISO: Fonte não encontrada em '{FONT_PATH}'. Usando fonte padrão.")
                font = ImageFont.load_default()

            textwidth, textheight = draw.textsize(WATERMARK_TEXT, font)
            margin = 15
            x = base.width - textwidth - margin
            y = base.height - textheight - margin
            
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill="black")
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))
            
            base.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"ERRO ao aplicar marca de água na imagem '{input_path}': {e}")
        return False

def add_watermark_to_video(input_path, output_path):
    """Aplica uma marca de água de texto a um vídeo usando FFmpeg."""
    print(f"A aplicar marca de água no vídeo: {input_path}")
    # Prepara o texto para ser usado no FFmpeg (precisa de escapar caracteres especiais)
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    
    # Comando FFmpeg para adicionar a marca de água
    # 'main_w' e 'main_h' são as larguras e alturas do vídeo
    # 'x' e 'y' posicionam o texto no canto inferior direito com uma margem de 10px
    command = [
        "ffmpeg",
        "-i", input_path,
        "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize=24:fontcolor=white@0.7:x=main_w-text_w-10:y=main_h-text_h-10:shadowcolor=black:shadowx=1:shadowy=1",
        "-c:a", "copy", # Copia o áudio sem re-codificar para ser mais rápido
        "-y", # Sobrescreve o ficheiro de saída se já existir
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

# --- Funções Auxiliares ---

def get_file_list():
    """Obtém a lista de todos os ficheiros do R2."""
    print("A obter a lista de todos os ficheiros do R2...")
    command = ["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}\nStderr: {e.stderr}")
        return []

def get_dimensions(local_path, file_type):
    """Obtém as dimensões de um ficheiro local."""
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
            command = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "json", local_path
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
        except Exception as e:
            print(f"AVISO: ffprobe não conseguiu obter dimensões para o vídeo '{local_path}'. Erro: {e}")
    return width, height

def parse_filename(filename):
    """Extrai títulos do nome do ficheiro."""
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3:
        return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2:
        return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else:
        return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}

# --- Função Principal ---

def process_files():
    """Função principal do workflow."""
    all_files = get_file_list()
    if not all_files:
        print("Nenhum ficheiro encontrado no R2. A sair.")
        return

    # Cria as pastas temporárias, se não existirem
    for dir_path in [TEMP_DIR, os.path.join(TEMP_DIR, WATERMARKED_DIR_IMG), os.path.join(TEMP_DIR, WATERMARKED_DIR_VID)]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    output_data = {cat: [] for cat in CATEGORIES.values()}

    for path in all_files:
        if any(x in path for x in ["desktop.ini", "/_thumbnails/", f"/{WATERMARKED_DIR_IMG}/", f"/{WATERMARKED_DIR_VID}/"]) or not path:
            continue

        try:
            category_name, filename = path.split('/', 1)
        except ValueError:
            continue

        if category_name in CATEGORIES:
            category_key = CATEGORIES[category_name]
            local_original_path = os.path.join(TEMP_DIR, filename)
            
            # 1. Descarregar o ficheiro original
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
                watermarked_filename = f"{base_name}_wm{ext}" # Adiciona _wm para evitar conflitos
                local_watermarked_path = os.path.join(TEMP_DIR, WATERMARKED_DIR_VID, watermarked_filename)

                if add_watermark_to_video(local_original_path, local_watermarked_path):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}/{watermarked_filename}"], check=True)
                    file_data["url"] = f"{PUBLIC_URL}/{WATERMARKED_DIR_VID}/{watermarked_filename.replace(' ', '%20')}"
                    file_data["thumbnail_url"] = f"{PUBLIC_URL}/_thumbnails/{base_name}.jpg".replace(' ', '%20')
                    output_data[category_key].append(file_data)
            
            # Limpar ficheiro original descarregado
            os.remove(local_original_path)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    process_files()
