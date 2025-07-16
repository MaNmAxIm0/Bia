# Ficheiro: /scripts/process_files.py (VERSÃO FINAL COM REGISTO DE PROCESSAMENTO)

import subprocess
import json
import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel", "Capas": "covers"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
LOG_FILE_NAME = "processed_log.txt" # O nosso novo ficheiro de registo
LOG_FILE_PATH_LOCAL = os.path.join(TEMP_DIR, LOG_FILE_NAME)
LOG_FILE_PATH_REMOTE = f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{LOG_FILE_NAME}"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

# --- Funções Auxiliares (sem alterações) ---
def rclone_lsf_recursive(remote_path):
    command = ["rclone", "lsf", remote_path, "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return {line for line in result.stdout.strip().split('\n') if line}
    except subprocess.CalledProcessError:
        return set()

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3:
        return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2:
        return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else:
        return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def get_media_dimensions(local_path, media_type):
    width, height = 0, 0
    try:
        if media_type in ['fotografias', 'designs']:
            with Image.open(local_path) as img:
                img_corrected = ImageOps.exif_transpose(img)
                width, height = img_corrected.size
        elif media_type == 'videos':
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e:
        print(f"  AVISO: Não foi possível obter dimensões para '{local_path}'. Erro: {e}")
    return width, height

def apply_watermark_and_optimize(input_path, output_path):
    # Converte para JPG e aplica marca de água
    try:
        with Image.open(input_path) as img:
            img_corrected = ImageOps.exif_transpose(img)
            if img_corrected.mode == 'RGBA':
                background = Image.new("RGB", img_corrected.size, (255, 255, 255))
                background.paste(img_corrected, mask=img_corrected.split()[3])
                img_corrected = background
            if img_corrected.width > MAX_IMAGE_WIDTH:
                new_height = int(MAX_IMAGE_WIDTH * img_corrected.height / img_corrected.width)
                img_corrected = img_corrected.resize((MAX_IMAGE_WIDTH, new_height), Image.Resampling.LANCZOS)
            draw = ImageDraw.Draw(img_corrected)
            font_size = max(20, int(img_corrected.height * 0.04))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
                font.set_variation_by_name('SemiBold')
            except (IOError, AttributeError):
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(img_corrected.width * 0.02)
            x, y = img_corrected.width - text_width - margin, img_corrected.height - text_height - margin
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 200))
            img_corrected.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True, subsampling=0)
        return True
    except Exception as e:
        return f"PIL Error: {e}"

def apply_watermark_to_video(input_path, output_path, video_width, video_height):
    # (Esta função permanece igual)
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    font_size = max(24, int(video_width * 0.045))
    margin = int(video_width * 0.02)
    command = [ "ffmpeg", "-i", input_path, "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2:borderw=1:bordercolor=white@0.8", "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", "-y", output_path ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=600)
        return True
    except Exception as e:
        return f"FFmpeg Error: {e}"

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    # 1. Carregar o registo de ficheiros já processados
    processed_files_log = set()
    try:
        subprocess.run(["rclone", "copyto", LOG_FILE_PATH_REMOTE, LOG_FILE_PATH_LOCAL], check=False)
        with open(LOG_FILE_PATH_LOCAL, "r", encoding="utf-8") as f:
            processed_files_log = {line.strip() for line in f}
        print(f"Encontrado registo com {len(processed_files_log)} ficheiros já processados.")
    except FileNotFoundError:
        print("Registo de processamento não encontrado. A criar um novo.")

    all_source_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")
    new_data = {key: [] for key in CATEGORIES.values()}

    for path in all_source_files:
        if LOG_FILE_NAME in path: continue # Ignora o próprio ficheiro de registo

        try:
            category_folder = os.path.dirname(path)
            if category_folder not in CATEGORIES: continue
            
            filename = os.path.basename(path)
            category_key = CATEGORIES[category_folder]

            # Adiciona sempre ao data.json, pois ele representa o estado final
            if category_key in ['fotografias', 'designs']:
                # O URL final será sempre .jpg
                final_url = f"{PUBLIC_URL}/{os.path.splitext(path)[0]}.jpg".replace(' ', '%20')
            else:
                final_url = f"{PUBLIC_URL}/{path.replace(' ', '%20')}"

            file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": final_url}
            
            if category_key == 'videos':
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
            
            # Adiciona ao new_data
            new_data[category_key].append(file_data)
            
            # ** A VERIFICAÇÃO PRINCIPAL **
            # Se o ficheiro já está no registo, ignora-o.
            if path in processed_files_log:
                continue

            # Se chegámos aqui, o ficheiro precisa de ser processado
            print(f"-> Processamento necessário para: {path}")

            local_original_path = os.path.join(TEMP_DIR, filename)
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True)

            width, height = get_media_dimensions(local_original_path, category_key)
            # Adiciona orientação ao data.json se for relevante
            if 'orientation' in file_data:
                file_data['orientation'] = "vertical" if height > width else "horizontal"

            if category_key in ["fotografias", "designs"]:
                processed_filename = f"{os.path.splitext(filename)[0]}.jpg"
                local_processed_path = os.path.join(TEMP_DIR, processed_filename)
                apply_watermark_and_optimize(local_original_path, local_processed_path)
                # O caminho de upload é o mesmo que o original, mas com .jpg
                upload_path = f"{os.path.splitext(path)[0]}.jpg"
            elif category_key == "videos":
                local_processed_path = os.path.join(TEMP_DIR, f"wm_{filename}")
                apply_watermark_to_video(local_original_path, local_processed_path, width, height)
                # O caminho de upload é o mesmo que o original
                upload_path = path
            
            # Sobrescreve o ficheiro no R2
            print(f"  -> A fazer upload e a sobrescrever: {upload_path}")
            subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{upload_path}"], check=True)

            # Adiciona ao registo e limpa ficheiros temporários
            processed_files_log.add(path)
            os.remove(local_original_path)
            os.remove(local_processed_path)

        except Exception as e:
            print(f"  -> ERRO ao processar {path}: {e}")

    print("\n--- [FASE 2] Limpeza e Finalização ---")
    print("Gerando ficheiro data.json final...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print("Guardando registo de processamento no R2...")
    with open(LOG_FILE_PATH_LOCAL, "w", encoding="utf-8") as f:
        for item in sorted(list(processed_files_log)):
            f.write(f"{item}\n")
    subprocess.run(["rclone", "copyto", LOG_FILE_PATH_LOCAL, LOG_FILE_PATH_REMOTE], check=True)
    
    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()