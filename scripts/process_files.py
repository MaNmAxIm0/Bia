import subprocess
import json
import os
import time
from PIL import Image, ImageDraw, ImageFont, ExifTags

# --- Configuração Simplificada ---
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
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat.ttf')
TEMP_DIR = "temp_files"

# Pastas no R2
WATERMARKED_DIR_IMG = "WatermarkedImages"
WATERMARKED_DIR_VID = "WatermarkedVideos"
THUMBNAILS_DIR = "Thumbnails"

EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)

# --- Funções Rclone Auxiliares ---
def rclone_lsf(remote_path):
    command = ["rclone", "lsf", remote_path, "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return [line for line in result.stdout.strip().split('\n') if line]
    except subprocess.CalledProcessError:
        return []

def rclone_delete_file(remote_path):
    print(f"  - Apagando ficheiro obsoleto: {remote_path}")
    command = ["rclone", "deletefile", remote_path]
    subprocess.run(command, check=True, capture_output=True)

# --- Funções de Processamento ---
# (As funções add_watermark_to_image, add_watermark_to_video, get_dimensions e parse_filename mantêm-se iguais)
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
    try:
        if file_type in ['fotografias', 'designs']:
            with Image.open(local_path) as img:
                width, height = img.size
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif and EXIF_ORIENTATION_TAG in exif and exif[EXIF_ORIENTATION_TAG] in [5, 6, 7, 8]: width, height = height, width
        elif file_type == 'videos':
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e:
        print(f"  AVISO: Não foi possível obter dimensões para {local_path}. Erro: {e}")
    return width, height

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2: return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else: return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}


# --- Lógica Principal Reestruturada para usar R2 como fonte da verdade ---

def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)

    # 1. Obter a lista de ficheiros de ORIGEM que já estão no R2
    print("\n--- [FASE 1 de 4] A mapear ficheiros de origem no R2 ---")
    source_files_r2 = {}
    for category_name, category_key in CATEGORIES.items():
        print(f"A listar ficheiros R2 da categoria: {category_name}...")
        path = f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{category_name}"
        files = rclone_lsf(path)
        for f in files:
            source_files_r2[f] = {'category_key': category_key, 'category_name': category_name}
    print(f"MAPEAMENTO CONCLUÍDO: Encontrados {len(source_files_r2)} ficheiros de origem no R2.")

    # 2. Obter listas de ficheiros já processados no R2
    print("\n--- [FASE 2 de 4] A verificar ficheiros já existentes no R2 ---")
    watermarked_images_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_IMG}"))
    watermarked_videos_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}"))
    thumbnails_r2 = set(rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{THUMBNAILS_DIR}"))
    
    # 3. Limpar ficheiros obsoletos no R2
    print("\n--- [FASE 3 de 4] A limpar ficheiros obsoletos no R2 ---")
    expected_images = {f"{os.path.splitext(f)[0]}.png" for f, data in source_files_r2.items() if data['category_key'] in ['fotografias', 'designs']}
    expected_videos = {f"{os.path.splitext(f)[0]}_wm{os.path.splitext(f)[1]}" for f, data in source_files_r2.items() if data['category_key'] == 'videos'}
    expected_thumbnails = {f"{os.path.splitext(f)[0]}.jpg" for f, data in source_files_r2.items() if data['category_key'] == 'videos'}

    for file_to_check in watermarked_images_r2 - expected_images:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_IMG}/{file_to_check}")
    for file_to_check in watermarked_videos_r2 - expected_videos:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{WATERMARKED_DIR_VID}/{file_to_check}")
    for file_to_check in thumbnails_r2 - expected_thumbnails:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{THUMBNAILS_DIR}/{file_to_check}")
    print("Limpeza concluída.")

    # 4. Processar novos ficheiros e gerar data.json
    print("\n--- [FASE 4 de 4] A gerar data.json e a processar ficheiros novos ---")
    output_data = {cat: [] for cat in CATEGORIES.values()}
    all_processed_files = watermarked_images_r2.union(watermarked_videos_r2)

    for i, (filename, data) in enumerate(source_files_r2.items()):
        print(f"A verificar ficheiro {i+1}/{len(source_files_r2)}: {filename}")
        category_key = data['category_key']
        category_name = data['category_name']
        base_name, ext = os.path.splitext(filename)
        
        file_data = {"name": filename, "titles": parse_filename(filename)}
        
        # Define nomes e URLs
        process_this_file = False
        if category_key in ["fotografias", "designs"]:
            watermarked_filename = f"{base_name}.png"
            remote_path = f"{WATERMARKED_DIR_IMG}/{watermarked_filename}"
            if watermarked_filename not in all_processed_files:
                process_this_file = True
            file_data["url"] = f"{PUBLIC_URL}/{remote_path.replace(' ', '%20')}"
        elif category_key == "videos":
            watermarked_filename = f"{base_name}_wm{ext}"
            remote_path = f"{WATERMARKED_DIR_VID}/{watermarked_filename}"
            if watermarked_filename not in all_processed_files:
                process_this_file = True
            file_data["url"] = f"{PUBLIC_URL}/{remote_path.replace(' ', '%20')}"
            file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{base_name}.jpg".replace(' ', '%20')
        
        # Descarrega e processa APENAS se for um ficheiro novo
        local_original_path = os.path.join(TEMP_DIR, filename)
        subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{category_name}/{filename}", local_original_path], check=True)
        width, height = get_dimensions(local_original_path, category_key)
        file_data["orientation"] = "horizontal" if width >= height else "vertical"

        if process_this_file:
            print(f"  - Ficheiro novo detectado. A processar...")
            local_watermarked_path = os.path.join(TEMP_DIR, watermarked_filename)
            if category_key in ["fotografias", "designs"]:
                if add_watermark_to_image(local_original_path, local_watermarked_path):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_path}"], check=True)
            elif category_key == "videos":
                if add_watermark_to_video(local_original_path, local_watermarked_path, width):
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_path}"], check=True)
            if os.path.exists(local_watermarked_path): os.remove(local_watermarked_path)
            print("  - Processamento e upload concluídos.")
        
        os.remove(local_original_path)
        output_data[category_key].append(file_data)
    
    # Adicionar as apresentações, que não são processadas mas são sincronizadas
    apresentacoes_files = rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/Apresentações")
    for f in apresentacoes_files:
        if f:
             output_data['apresentacoes'].append({
                 "name": f,
                 "titles": parse_filename(f),
                 "url": f"{PUBLIC_URL}/Apresentações/{f.replace(' ', '%20')}",
                 "orientation": "square"
             })

    print("\nA gerar ficheiro data.json final...")
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    end_time = time.time()
    print(f"\n>>> SCRIPT CONCLUÍDO em {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()