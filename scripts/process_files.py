# Ficheiro: /scripts/process_files.py (VERSÃO FINAL E CORRIGIDA)

import subprocess
import json
import os
import time
from datetime import datetime, timezone, timedelta # <--- LINHA CORRIGIDA
from PIL import Image, ImageDraw, ImageFont, ImageOps # <--- LINHA ADICIONADA

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
def get_rclone_lsl_json(path):
    command = ["rclone", "lsl", "--json", path, "--recursive"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Erro ao obter lista de ficheiros de {path}: {e}")
        return []

def get_last_manifest_time():
    try:
        # Lê a data da última linha do manifesto para ser mais preciso
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) > 2: # Garante que o ficheiro tem conteúdo
                # Exemplo de linha: 2025-07-16 21:36:00 WEST       123456 Fotografias/foto.jpg
                last_line = lines[-1]
                date_str = " ".join(last_line.split("\t")[0].split()[:2])
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (FileNotFoundError, IndexError):
        # Se o ficheiro não existe ou está vazio, retorna o início dos tempos
        pass
    return datetime.fromtimestamp(0, tz=timezone.utc)

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
            
            font_size = max(24, int(img_corrected.height * 0.05))
            font = ImageFont.truetype(FONT_PATH, font_size)
            
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(img_corrected.width * 0.025)
            x, y = img_corrected.width - text_width - margin, img_corrected.height - text_height - margin
            
            draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
            
            img_corrected.save(output_path, "JPEG", quality=JPEG_QUALITY, optimize=True, subsampling=0)
        return True
    except Exception as e:
        return f"PIL Error: {e}"

def apply_watermark_to_video(input_path, output_path, video_width, video_height):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    font_size = max(30, int(video_width * 0.055))
    margin = int(video_width * 0.025)
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

    print("\n--- [FASE 1] Lendo o estado atual do R2 ---")
    all_r2_files_data = get_rclone_lsl_json(RCLONE_REMOTE)
    last_run_time = get_last_manifest_time()

    new_data = {key: [] for key in CATEGORIES.values()}
    
    files_to_process = []
    # Converte a data de modificação do ficheiro para um objeto ciente do fuso horário
    for item in all_r2_files_data:
        mod_time = datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00"))
        if mod_time > last_run_time:
            path = item["Path"]
            category_folder = os.path.dirname(path)
            if category_folder in CATEGORIES and CATEGORIES[category_folder] in ["fotografias", "designs", "videos"]:
                files_to_process.append(item)

    if not files_to_process:
        print("Nenhum ficheiro novo ou modificado para processar.")
    else:
        print(f"Encontrados {len(files_to_process)} ficheiros novos ou modificados para processar.")

    for item in files_to_process:
        try:
            path = item["Path"]
            filename = os.path.basename(path)
            category_folder = os.path.dirname(path)
            category_key = CATEGORIES[category_folder]

            print(f"-> Processando: {path}")

            local_original_path = os.path.join(TEMP_DIR, filename)
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_original_path], check=True)
            
            width, height = get_media_dimensions(local_original_path, category_key)
            
            if category_key in ["fotografias", "designs"]:
                processed_filename = f"{os.path.splitext(filename)[0]}.jpg"
                final_path = os.path.join(category_folder, processed_filename)
                local_processed_path = os.path.join(TEMP_DIR, processed_filename)
                apply_watermark_and_optimize(local_original_path, local_processed_path)
            else: # videos
                local_processed_path = os.path.join(TEMP_DIR, f"proc_{filename}")
                apply_watermark_to_video(local_original_path, local_processed_path, width, height)
                final_path = path

            print(f"  -> A fazer upload e a sobrescrever: {final_path}")
            subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_path}"], check=True)

            if path != final_path:
                print(f"  -> Apagando ficheiro de origem obsoleto: {path}")
                subprocess.run(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])

            os.remove(local_original_path)
            os.remove(local_processed_path)

        except Exception as e:
            print(f"  -> ERRO ao processar {item['Path']}: {e}")
    
    # Reconstrói o data.json com todos os ficheiros do R2 (estado final)
    print("\n--- [FASE 2] Gerando o ficheiro data.json final ---")
    final_r2_files_data = get_rclone_lsl_json(RCLONE_REMOTE)
    for item in final_r2_files_data:
        path = item["Path"]
        category_folder = os.path.dirname(path)
        if category_folder in CATEGORIES:
            filename = os.path.basename(path)
            category_key = CATEGORIES[category_folder]
            file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"}
            if category_key == 'videos': file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
            if category_key in ["fotografias", "designs"]:
                 # A orientação precisa de ser determinada ou assumida
                 # Para simplificar, podemos omiti-la por agora ou necessitar de uma lógica mais complexa
                 pass
            new_data[category_key].append(file_data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()