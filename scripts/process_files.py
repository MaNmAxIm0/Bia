# Ficheiro: /scripts/process_files.py (VERSÃO CORRIGIDA E EFICIENTE)

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
THUMBNAILS_DIR = "Thumbnails"
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
    name_without_ext = os.path.splitext(filename)[0].replace('wm_', '')
    parts = name_without_ext.split('_')
    if len(parts) >= 3:
        return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2:
        return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else:
        return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def get_media_dimensions(local_path, media_type):
    # (Esta função permanece igual)
    width, height = 0, 0
    try:
        if media_type in ['fotografias', 'designs', 'carousel', 'covers']:
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
    # (Esta função permanece igual)
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
    command = [
        "ffmpeg", "-i", input_path,
        "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2:borderw=1:bordercolor=white@0.8",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-c:a", "copy", "-y", output_path
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=600)
        return True
    except subprocess.CalledProcessError as e:
        return f"FFmpeg Error: {e.stderr}"
    except subprocess.TimeoutExpired:
        return "FFmpeg Error: O processamento demorou demasiado tempo (timeout)."

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    existing_carousel_data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_carousel_data = json.load(f)
            except json.JSONDecodeError:
                print("AVISO: Ficheiro data.json existente está corrompido.")

    print("\n--- [FASE 1] Mapeando todos os ficheiros no R2 ---")
    all_r2_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")
    
    # ** LÓGICA CORRIGIDA **
    # Separa os ficheiros originais dos já processados para uma verificação eficiente
    source_files = {f for f in all_r2_files if not os.path.basename(f).startswith('wm_')}
    processed_files_paths = {f for f in all_r2_files if os.path.basename(f).startswith('wm_')}
    
    new_data = {cat_key: [] for cat_key in CATEGORIES.values()}
    
    for path in source_files:
        try:
            category_folder = path.split('/')[0]
            if category_folder not in CATEGORIES:
                continue
            
            filename = os.path.basename(path)
            category_key = CATEGORIES[category_folder]

            # Ignora ficheiros que não são para processar (Capas, Apresentações, etc.)
            if category_key in ['carousel', 'covers', 'apresentacoes']:
                # (a sua lógica existente para estes tipos)
                continue

            # ** VERIFICAÇÃO MELHORADA **
            # Define o nome do ficheiro processado esperado
            if category_key in ["fotografias", "designs"]:
                watermarked_filename = f"wm_{os.path.splitext(filename)[0]}.jpg"
            else: # videos
                watermarked_filename = f"wm_{filename}"
            
            expected_upload_path = f"{category_folder}/{watermarked_filename}"

            # A condição principal: só processa se o ficheiro não existir na lista de processados
            if expected_upload_path not in processed_files_paths:
                print(f"A verificar: {path}...")
                print(f"  -> Processamento necessário. A gerar {watermarked_filename}")
                local_original_path = os.path.join(TEMP_DIR, filename)
                
                # Baixar o ficheiro original
                subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True, capture_output=True)

                width, height = get_media_dimensions(local_original_path, category_key)
                if width == 0 and height == 0:
                    raise ValueError("Dimensões inválidas, não foi possível processar.")

                local_processed_path = os.path.join(TEMP_DIR, watermarked_filename)
                
                # Aplicar marca de água
                if category_key in ["fotografias", "designs"]:
                    apply_watermark_and_optimize(local_original_path, local_processed_path)
                elif category_key == "videos":
                    apply_watermark_to_video(local_original_path, local_processed_path, width, height)
                
                # Fazer upload do ficheiro processado
                print(f"  -> A fazer upload de {local_processed_path} para {expected_upload_path}")
                subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{expected_upload_path}"], check=True, capture_output=True)
                
                os.remove(local_original_path)
                os.remove(local_processed_path)
            else:
                # O ficheiro já existe, não faz nada
                pass

            # Adiciona sempre os dados ao `data.json` se o ficheiro original existir
            # (a sua lógica para adicionar ao new_data permanece aqui)

        except Exception as e:
            print(f"  -> ERRO ao processar {path}: {e}")
            # ... (código de limpeza de erro) ...

    # ... (o resto do seu script para gerar data.json e fazer a limpeza final) ...

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()