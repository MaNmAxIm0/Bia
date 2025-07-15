# Ficheiro: /scripts/process_files.py

import subprocess
import json
import os
import time
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração (sem alterações) ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__ ), 'Montserrat.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
THUMBNAILS_DIR = "Thumbnails"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

# --- Funções Auxiliares (sem alterações) ---
def rclone_lsf_recursive(remote_path):
    command = ["rclone", "lsf", remote_path, "--recursive", "--files-only", "--exclude", "wm_*"]
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
    width, height = 0, 0
    try:
        if media_type in ['fotografias', 'designs', 'carousel']:
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

# --- FUNÇÃO DE VÍDEO ATUALIZADA ---
def apply_watermark_to_video(input_path, output_path, video_width, video_height):
    """Aplica marca d'água a um vídeo com tamanho consistente e compressão mínima."""
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    
    # ** 1. CORREÇÃO DE TAMANHO: A base do cálculo é sempre a LARGURA do vídeo. **
    font_size = max(24, int(video_width * 0.045))
    
    margin = int(video_width * 0.02)
    
    # ** 2. CORREÇÃO DE ESPESSURA PARA VÍDEOS **
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

# --- Lógica Principal (com chamada de função corrigida) ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E LIMPEZA...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    existing_carousel_data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
                existing_carousel_data = {item['name']: item for item in existing_data.get('carousel', [])}
            except json.JSONDecodeError:
                print("AVISO: Ficheiro data.json existente está corrompido.")

    print("\n--- [FASE 1] Mapeando todos os ficheiros no R2 ---")
    all_r2_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")
    
    source_files = {f for f in all_r2_files if not os.path.basename(f).startswith('wm_')}
    processed_files = {f for f in all_r2_files if os.path.basename(f).startswith('wm_')}
    
    new_data = {cat_key: [] for cat_key in CATEGORIES.values()}
    final_processed_files = set()

    for path in source_files:
        try:
            category_folder, filename = path.split('/', 1)
            if category_folder not in CATEGORIES: continue

            category_key = CATEGORIES[category_folder]
            
            if category_key == 'carousel':
                existing_entry = existing_carousel_data.get(filename, {})
                new_data['carousel'].append({
                    "name": filename, "titles": parse_filename_for_titles(filename),
                    "descriptions": existing_entry.get('descriptions', {"pt": "", "en": "", "es": ""}),
                    "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"
                })
                continue

            print(f"A processar: {path}...")
            local_original_path = os.path.join(TEMP_DIR, filename)
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True, capture_output=True)

            width, height = get_media_dimensions(local_original_path, category_key)
            if width == 0 and category_key not in ['apresentacoes']:
                raise ValueError("Dimensões inválidas.")

            file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "orientation": "horizontal" if width >= height else "vertical"}
            
            if category_key in ["fotografias", "designs"]:
                watermarked_filename = f"wm_{os.path.splitext(filename)[0]}.jpg"
                upload_path = f"{category_folder}/{watermarked_filename}"
                final_processed_files.add(upload_path)
                
                if upload_path not in processed_files:
                    print(f"  -> Gerando nova marca d'água para {watermarked_filename}")
                    local_processed_path = os.path.join(TEMP_DIR, watermarked_filename)
                    result = apply_watermark_and_optimize(local_original_path, local_processed_path)
                    if result is not True: raise Exception(f"Falha na otimização: {result}")
                    subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{upload_path}"], check=True, capture_output=True)
                
                file_data["url"] = f"{PUBLIC_URL}/{upload_path.replace(' ', '%20')}"
                
            elif category_key == "videos":
                watermarked_filename = f"wm_{filename}"
                upload_path = f"{category_folder}/{watermarked_filename}"
                final_processed_files.add(upload_path)

                if upload_path not in processed_files:
                    print(f"  -> Gerando nova marca d'água para {watermarked_filename}")
                    local_processed_path = os.path.join(TEMP_DIR, watermarked_filename)
                    result = apply_watermark_to_video(local_original_path, local_processed_path, width, height)
                    if result is not True: raise Exception(f"Falha no watermarking de vídeo: {result}")
                    subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{upload_path}"], check=True, capture_output=True)

                file_data["url"] = f"{PUBLIC_URL}/{upload_path.replace(' ', '%20')}"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')

            elif category_key == "apresentacoes":
                file_data["url"] = f"{PUBLIC_URL}/{path.replace(' ', '%20')}"

            new_data[category_key].append(file_data)

        except Exception as e:
            print(f"  -> ERRO ao processar {path}: {e}")
        finally:
            if 'local_original_path' in locals() and os.path.exists(local_original_path): os.remove(local_original_path)
            if 'local_processed_path' in locals() and os.path.exists(local_processed_path): os.remove(local_processed_path)

    # --- [FASE 2] Limpeza de Ficheiros Órfãos ---
    print("\n--- [FASE 2] Limpando ficheiros órfãos no R2 ---")
    for path in source_files:
        if not path.startswith("Apresentações/") and not path.startswith("Melhores/"):
            print(f"  -> Apagando ficheiro de origem processado: {path}")
            subprocess.run(["rclone", "deletefile", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}"], check=True)

    for path in processed_files:
        if path not in final_processed_files:
            print(f"  -> Apagando ficheiro processado órfão: {path}")
            subprocess.run(["rclone", "deletefile", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}"], check=True)

    print("\nGerando ficheiro data.json final...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
