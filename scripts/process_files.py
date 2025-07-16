# Ficheiro: scripts/process_files.py (VERSÃO FINAL E DEFINITIVA)

import subprocess
import json
import os
import time
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel", "Capas": "covers"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
MANIFEST_FILE = "r2_file_manifest.txt"
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

# --- Funções Auxiliares ---
def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, encoding='utf-8')
        return result
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_lsl_json(path):
    result = run_command(["rclone", "lsl", "--json", path, "--recursive"])
    return json.loads(result.stdout) if result and result.stdout else []

def get_last_manifest_time():
    try:
        with open(MANIFEST_FILE, 'r') as f:
            for line in f:
                if line.startswith("Gerado em:"):
                    parts = line.split()
                    date_str = " ".join(parts[2:5] + [parts[6]])
                    return datetime.strptime(date_str, "%b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)
    except (FileNotFoundError, IndexError, ValueError):
        print("AVISO: Manifesto não encontrado ou inválido. A processar todos os ficheiros que necessitem.")
    return datetime.fromtimestamp(0, tz=timezone.utc)

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else: return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def get_media_dimensions(local_path, is_video):
    width, height = 0, 0
    try:
        if not is_video:
            with Image.open(local_path) as img:
                img_corrected = ImageOps.exif_transpose(img)
                width, height = img_corrected.size
        else:
            result = run_command(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path])
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e:
        print(f"  AVISO: Não foi possível obter dimensões para '{local_path}'. Erro: {e}")
    return width, height

def apply_watermark(input_path, output_path, is_video):
    width, height = get_media_dimensions(input_path, is_video)
    if width == 0: return False

    if not is_video:
        with Image.open(input_path) as img:
            img = ImageOps.exif_transpose(img)
            if img.mode == 'RGBA':
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            if img.width > MAX_IMAGE_WIDTH:
                h = int((MAX_IMAGE_WIDTH / img.width) * img.height)
                img = img.resize((MAX_IMAGE_WIDTH, h), Image.Resampling.LANCZOS)
            
            draw = ImageDraw.Draw(img)
            font_size = max(24, int(img.height * 0.05))
            font = ImageFont.truetype(FONT_PATH, font_size)
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(img.width * 0.025)
            position = (img.width - text_width - margin, img.height - text_height - margin)
            draw.text((position[0] + 2, position[1] + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text(position, WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
            img.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True)
    else:
        font_size = max(30, int(width * 0.055))
        margin = int(width * 0.025)
        escaped_text = WATERMARK_TEXT.replace("'", "\\'").replace(":", "\\:")
        vf_command = f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.8:x=w-text_w-{margin}:y=h-text_h-{margin}:shadowcolor=black@0.6:shadowx=2:shadowy=2"
        command = ["ffmpeg", "-i", input_path, "-vf", vf_command, "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-c:a", "copy", "-y", output_path]
        run_command(command)
    return True

# --- LÓGICA PRINCIPAL ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("\n--- [FASE 1] Mapeando ficheiros e determinando o que processar ---")
    all_files_data = get_rclone_lsl_json(RCLONE_REMOTE)
    last_run_time = get_last_manifest_time()
    
    # Mapeia os nomes base (.jpg) que já existem para verificação rápida
    existing_jpg_basenames = {os.path.splitext(item["Path"])[0] for item in all_files_data if item["Path"].lower().endswith('.jpg')}

    for item in all_files_data:
        try:
            path = item["Path"]
            filename = os.path.basename(path)
            basename, ext = os.path.splitext(filename)
            category_folder = os.path.dirname(path)
            
            if category_folder not in CATEGORIES: continue
            
            category_key = CATEGORIES[category_folder]

            # Define o que precisa de ser processado
            is_new_video = category_key == "videos" and datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00")) > last_run_time
            is_new_image = category_key in ["fotografias", "designs"] and not path.lower().endswith('.jpg') and os.path.join(category_folder, basename) not in existing_jpg_basenames
            
            if not is_new_video and not is_new_image:
                continue

            print(f"-> Processamento necessário para: {path}")
            
            local_path = os.path.join(TEMP_DIR, filename)
            run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
            
            if is_new_image:
                processed_filename = f"{basename}.jpg"
                final_path = os.path.join(category_folder, processed_filename)
                local_processed_path = os.path.join(TEMP_DIR, processed_filename)
            else: # é vídeo
                local_processed_path = os.path.join(TEMP_DIR, f"proc_{filename}")
                final_path = path

            if apply_watermark(local_path, local_processed_path, is_new_video):
                print(f"  -> Upload para: {final_path}")
                run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_path}"])
                if path.lower() != final_path.lower():
                    print(f"  -> Apagando original obsoleto: {path}")
                    run_command(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])
            
            os.remove(local_path)
            if os.path.exists(local_processed_path):
                os.remove(local_processed_path)

        except Exception as e: print(f"  -> ERRO CRÍTICO ao processar {item['Path']}: {e}")
            
    print("\n--- [FASE 2] Gerando o ficheiro data.json final ---")
    final_r2_files = get_rclone_lsl_json(RCLONE_REMOTE)
    new_data = {key: [] for key in CATEGORIES.values()}
    
    for item in final_r2_files:
        path = item["Path"]
        filename = os.path.basename(path)
        category_folder = os.path.dirname(path)
        if category_folder in CATEGORIES:
            category_key = CATEGORIES[category_folder]
            
            if category_key in ['fotografias', 'designs'] and not path.lower().endswith('.jpg'):
                continue
            
            file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"}
            if category_key == 'videos':
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
            
            # Adicionar orientação aqui se necessário no futuro
            new_data[category_key].append(file_data)
            
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print("Ficheiro data.json gerado com sucesso.")

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()