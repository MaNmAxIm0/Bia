# Ficheiro: /scripts/process_files.py (VERSÃO FINAL E CORRIGIDA)

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
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf') # Usar a fonte correta
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

# --- Funções Auxiliares ---
def rclone_lsf_recursive(remote_path):
    command = ["rclone", "lsf", remote_path, "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return {line.strip() for line in result.stdout.strip().split('\n') if line.strip()}
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
            
            # **MARCA DE ÁGUA MELHORADA**
            font_size = max(24, int(img_corrected.height * 0.05)) # Tamanho aumentado
            font = ImageFont.truetype(FONT_PATH, font_size)
            
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(img_corrected.width * 0.025)
            x, y = img_corrected.width - text_width - margin, img_corrected.height - text_height - margin
            
            draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128)) # Sombra
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220)) # Texto principal
            
            img_corrected.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True, subsampling=0)
        return True
    except Exception as e:
        return f"PIL Error: {e}"

def apply_watermark_to_video(input_path, output_path, video_width, video_height):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    # **MARCA DE ÁGUA MELHORADA**
    font_size = max(30, int(video_width * 0.055)) # Tamanho aumentado
    margin = int(video_width * 0.025)
    # Comando FFmpeg para usar a fonte bold
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

    print("\n--- [FASE 1] Mapeando todos os ficheiros no R2 ---")
    all_r2_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")

    source_files = {f for f in all_r2_files if not f.startswith("wm_")} # Simplificado
    
    new_data = {key: [] for key in CATEGORIES.values()}

    for path in source_files:
        try:
            category_folder = os.path.dirname(path)
            if category_folder not in CATEGORIES: continue

            filename = os.path.basename(path)
            basename = os.path.splitext(filename)[0]
            category_key = CATEGORIES[category_folder]

            # Ignora ficheiros que não são para processar
            if category_key not in ["fotografias", "designs", "videos"]:
                final_url = f"{PUBLIC_URL}/{path.replace(' ', '%20')}"
                file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": final_url}
                new_data[category_key].append(file_data)
                continue

            # Determina o nome final do ficheiro processado (sempre .jpg para imagens)
            if category_key in ['fotografias', 'designs']:
                final_filename = f"{basename}.jpg"
                final_path = os.path.join(category_folder, final_filename)
            else: # Vídeos mantêm o nome original
                final_filename = filename
                final_path = path

            # Verifica se a versão final já existe no R2
            if final_path in all_r2_files:
                # Adiciona ao data.json e continua para o próximo
                file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": f"{PUBLIC_URL}/{final_path.replace(' ', '%20')}"}
                if category_key == 'videos': file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{basename}.jpg".replace(' ', '%20')
                new_data[category_key].append(file_data)
                continue

            # Se chegámos aqui, o ficheiro precisa de ser processado
            print(f"-> Processamento necessário para: {path}")

            local_original_path = os.path.join(TEMP_DIR, filename)
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True)

            width, height = get_media_dimensions(local_original_path, category_key)
            
            local_processed_path = os.path.join(TEMP_DIR, final_filename)

            if category_key in ["fotografias", "designs"]:
                apply_watermark_and_optimize(local_original_path, local_processed_path)
            else: # Vídeos
                apply_watermark_to_video(local_original_path, local_processed_path, width, height)

            print(f"  -> A fazer upload e a sobrescrever: {final_path}")
            subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{final_path}"], check=True)

            # Se o ficheiro original era diferente do final (ex: .png -> .jpg), apaga o original
            if path != final_path:
                print(f"  -> Apagando ficheiro de origem obsoleto: {path}")
                subprocess.run(["rclone", "deletefile", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}"])
            
            # Adiciona ao data.json
            file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": f"{PUBLIC_URL}/{final_path.replace(' ', '%20')}", "orientation": "vertical" if height > width else "horizontal"}
            if category_key == 'videos': file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{basename}.jpg".replace(' ', '%20')
            new_data[category_key].append(file_data)
            
            os.remove(local_original_path)
            os.remove(local_processed_path)

        except Exception as e:
            print(f"  -> ERRO ao processar {path}: {e}")

    print("\nGerando ficheiro data.json final...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
        
    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()