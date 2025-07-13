import subprocess
import json
import os
from PIL import Image, ImageDraw, ImageFont, ExifTags

# --- Configuração ---
RCLONE_REMOTE_NAME = "R2"
GDRIVE_REMOTE_NAME = "Drive" # Assumindo que o seu remote do GDrive se chama 'Drive'
BUCKET_NAME = "bia-portfolio-assets"
GDRIVE_SOURCE_PATH = "Portfólio Bia"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat.ttf')
TEMP_DIR = "temp_files"

# Pastas no R2
WATERMARKED_DIR_IMG = "WatermarkedImages"
WATERMARKED_DIR_VID = "WatermarkedVideos"
THUMBNAILS_DIR = "Thumbnails"

EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)


# --- Funções Rclone ---

def rclone_lsf(remote_path):
    """Lista ficheiros num remote rclone, retorna uma lista vazia em caso de erro."""
    command = ["rclone", "lsf", remote_path]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def rclone_delete_file(remote_path):
    """Apaga um único ficheiro de um remote rclone."""
    print(f"A apagar ficheiro obsoleto: {remote_path}")
    command = ["rclone", "deletefile", remote_path]
    subprocess.run(command, check=True, capture_output=True)

# --- Funções de Processamento (sem alterações na lógica interna) ---

def add_watermark_to_image(input_path, output_path):
    try:
        with Image.open(input_path).convert("RGBA") as base:
            draw = ImageDraw.Draw(base)
            font_size = max(20, int(base.width * 0.05))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except IOError:
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(base.width * 0.015)
            x, y = base.width - textwidth - margin, base.height - textheight - margin
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill="black")
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))
            base.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"ERRO ao aplicar marca de água na imagem '{input_path}': {e}")
        return False

def add_watermark_to_video(input_path, output_path, video_width):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    font_size = max(24, int(video_width * 0.04))
    margin = int(video_width * 0.015)
    command = ["ffmpeg", "-i", input_path, "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.7:x=main_w-text_w-{margin}:y=main_h-text_h-{margin}:shadowcolor=black:shadowx=1:shadowy=1", "-c:a", "copy", "-y", output_path]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERRO FFmpeg: {e.stderr}")
        return False

def get_dimensions(local_path, file_type):
    width, height = 0, 0
    if file_type in ['fotografias', 'designs']:
        try:
            with Image.open(local_path) as img:
                width, height = img.size
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif and EXIF_ORIENTATION_TAG in exif and exif[EXIF_ORIENTATION_TAG] in [5, 6, 7, 8]: width, height = height, width
        except Exception: pass
    elif file_type == 'videos':
        try:
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
        except Exception: pass
    return width, height

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2: return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else: return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}


# --- Lógica Principal (Totalmente Reestruturada) ---

def main():
    print("Iniciando o processo de sincronização e processamento.")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

    # 1. Obter a lista de ficheiros de origem do Google Drive
    source_files = {}
    for category_name, category_key in CATEGORIES.items():
        files = rclone_lsf(f"{GDRIVE_REMOTE_NAME}:{GDRIVE_SOURCE_PATH}/{category_name}")
        for f in files:
            if f: source_files[f] = {'category_key': category_key, 'category_name': category_name}
    
    print(f"Encontrados {len(source_files)} ficheiros de origem no Google Drive.")

    # 2. Construir um set de ficheiros processados esperados
    expected_processed_files = set()
    for filename, data in source_files.items():
        base_name, ext = os.path.splitext(filename)
        if data['category_key'] in ["fotografias", "designs"]:
            expected_processed_files.add(f"{WATERMARKED_DIR_IMG}/{base_name}.png")
        elif data['category_key'] == "videos":
            expected_processed_files.add(f"{WATERMARKED_DIR_VID}/{base_name}_wm{ext}")
            expected_processed_files.add(f"{THUMBNAILS_DIR}/{base_name}.jpg")

    # 3. Limpar ficheiros obsoletos no R2
    print("\n--- Fase de Limpeza ---")
    r2_folders_to_check = [WATERMARKED_DIR_IMG, WATERMARKED_DIR_VID, THUMBNAILS_DIR]
    for folder in r2_folders_to_check:
        print(f"A verificar a pasta R2: {folder}")
        r2_files = rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{folder}")
        for r2_file in r2_files:
            if not r2_file: continue
            full_r2_path = f"{folder}/{r2_file}"
            if full_r2_path not in expected_processed_files:
                rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{full_r2_path}")

    # 4. Processar novos ficheiros e gerar data.json
    print("\n--- Fase de Processamento e Geração do JSON ---")
    output_data = {cat: [] for cat in CATEGORIES.values()}
    processed_files_on_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_IMG}") +
                                rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}"))

    for filename, data in source_files.items():
        category_key = data['category_key']
        category_name = data['category_name']
        base_name, ext = os.path.splitext(filename)
        
        file_data = {"name": filename, "titles": parse_filename(filename)}
        
        # Define nomes e URLs
        remote_watermarked_path = ""
        watermarked_filename_only = ""
        if category_key in ["fotografias", "designs"]:
            watermarked_filename_only = f"{base_name}.png"
            remote_watermarked_path = f"{WATERMARKED_DIR_IMG}/{watermarked_filename_only}"
            file_data["url"] = f"{PUBLIC_URL}/{remote_watermarked_path.replace(' ', '%20')}"
        elif category_key == "videos":
            watermarked_filename_only = f"{base_name}_wm{ext}"
            remote_watermarked_path = f"{WATERMARKED_DIR_VID}/{watermarked_filename_only}"
            file_data["url"] = f"{PUBLIC_URL}/{remote_watermarked_path.replace(' ', '%20')}"
            file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{base_name}.jpg".replace(' ', '%20')

        # Descarrega para obter dimensões (necessário para o data.json)
        local_original_path = os.path.join(TEMP_DIR, filename)
        subprocess.run(["rclone", "copyto", f"{GDRIVE_REMOTE_NAME}:{GDRIVE_SOURCE_PATH}/{category_name}/{filename}", local_original_path], check=True)
        width, height = get_dimensions(local_original_path, category_key)
        file_data["orientation"] = "horizontal" if width >= height else "vertical"
        
        output_data[category_key].append(file_data)
        
        # Processa apenas se o ficheiro ainda não existir no R2
        if watermarked_filename_only not in processed_files_on_r2:
            print(f"A processar novo ficheiro: {filename}")
            if category_key in ["fotografias", "designs"]:
                local_watermarked_path = os.path.join(TEMP_DIR, watermarked_filename_only)
                if add_watermark_to_image(local_original_path, local_watermarked_path):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_watermarked_path}"], check=True)
                    os.remove(local_watermarked_path)
            elif category_key == "videos":
                local_watermarked_path = os.path.join(TEMP_DIR, watermarked_filename_only)
                if add_watermark_to_video(local_original_path, local_watermarked_path, width):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_watermarked_path}"], check=True)
                    os.remove(local_watermarked_path)
        
        os.remove(local_original_path)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("\nFicheiro data.json gerado com sucesso.")
    print("Processo concluído.")

if __name__ == "__main__":
    main()