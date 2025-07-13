import subprocess
import json
import os
import time
from PIL import Image, ImageDraw, ImageFont, ExifTags

# --- Configuração ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = { "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs", "Apresentações": "apresentacoes" }
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
ERROR_LOG_FILE = "error_log.txt"
# A pasta de thumbnails permanece separada
THUMBNAILS_DIR = "Thumbnails"

EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)

# --- Funções Auxiliares (sem alterações) ---
def rclone_lsf(remote_path):
    command = ["rclone", "lsf", remote_path, "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return {line for line in result.stdout.strip().split('\n') if line}
    except subprocess.CalledProcessError:
        return set()

def rclone_delete_file(remote_path):
    print(f"  - Apagando thumbnail obsoleto: {remote_path}")
    command = ["rclone", "deletefile", remote_path]
    subprocess.run(command, check=True, capture_output=True)

def add_watermark_to_image(input_path, output_path):
    try:
        with Image.open(input_path).convert("RGBA") as base:
            draw = ImageDraw.Draw(base)
            font_size = max(20, int(base.width * 0.04))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
                font.set_variation_by_name('SemiBold')
            except (IOError, AttributeError):
                font = ImageFont.load_default()
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font); textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(base.width * 0.02); x, y = base.width - textwidth - margin, base.height - textheight - margin
            draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220)); base.save(output_path, "PNG")
        return True
    except Exception as e: return f"PIL Error: {e}"

def add_watermark_to_video(input_path, output_path, video_width):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", "")
    font_size = max(24, int(video_width * 0.035)); margin = int(video_width * 0.02)
    command = ["ffmpeg", "-i", input_path, "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.9:x=main_w-text_w-{margin}:y=main_h-text_h-{margin}:borderw=2:bordercolor=black@0.6", "-c:a", "copy", "-y", output_path]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300)
        return True
    except subprocess.CalledProcessError as e: return f"FFmpeg Error: {e.stderr}"
    except subprocess.TimeoutExpired: return "FFmpeg Error: O processamento demorou demasiado tempo (timeout)."

def get_dimensions(local_path, file_type):
    width, height = 0, 0
    try:
        if file_type in ['fotografias', 'designs']:
            with Image.open(local_path) as img:
                width, height = img.size
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif();
                    if exif and EXIF_ORIENTATION_TAG in exif and exif[EXIF_ORIENTATION_TAG] in [5, 6, 7, 8]: width, height = height, width
        elif file_type == 'videos':
            result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path], capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]; width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e: print(f"AVISO Dimensões: {e}")
    return width, height

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]; parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2: return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else: return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}


# --- Lógica Principal Final ---
def main():
    start_time = time.time(); print(">>> INICIANDO SCRIPT DE PROCESSAMENTO INTELIGENTE...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    errors = []

    # 1. Carregar o data.json antigo para usar como cache
    old_data_map = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f: old_data = json.load(f)
        for category, items in old_data.items():
            for item in items: old_data_map[item['name']] = item
        print(f"Ficheiro data.json anterior carregado com {len(old_data_map)} itens em cache.")

    # 2. Obter a lista atual de ficheiros de origem no R2
    source_files_r2 = {}
    for category_name, category_key in CATEGORIES.items():
        if category_key == 'apresentacoes': continue # Apresentações não são processadas
        path = f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{category_name}"
        files = rclone_lsf(path)
        for f in files: source_files_r2[f] = {'category_key': category_key, 'category_name': category_name}
    print(f"Encontrados {len(source_files_r2)} ficheiros de imagem/vídeo no R2 para verificar.")

    # 3. Limpar thumbnails obsoletas
    print("\n--- A limpar thumbnails obsoletas ---")
    expected_thumbnails = {f"{os.path.splitext(f)[0]}.jpg" for f, data in source_files_r2.items() if data['category_key'] == 'videos'}
    thumbnails_r2 = rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{THUMBNAILS_DIR}")
    for thumb_to_check in thumbnails_r2 - expected_thumbnails:
        rclone_delete_file(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{THUMBNAILS_DIR}/{thumb_to_check}")
    print("Limpeza de thumbnails concluída.")

    # 4. Processar ficheiros e construir o novo data.json
    print("\n--- A gerar data.json e a processar ficheiros novos ---")
    new_data = {cat: [] for cat in CATEGORIES.values()}
    for filename, data in source_files_r2.items():
        category_key = data['category_key']
        category_name = data['category_name']
        
        # Se o ficheiro já está na cache, reutiliza a informação e continua
        if filename in old_data_map:
            new_data[category_key].append(old_data_map[filename])
            continue

        print(f"NOVO FICHEIRO DETECTADO: {filename}. A processar...")
        local_original_path = os.path.join(TEMP_DIR, filename)
        
        try:
            # Descarrega o original
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{category_name}/{filename}", local_original_path], check=True)
            width, height = get_dimensions(local_original_path, category_key)
            if width == 0: raise ValueError("Não foi possível obter as dimensões do ficheiro.")

            file_data = {"name": filename, "titles": parse_filename(filename), "orientation": "horizontal" if width >= height else "vertical"}
            
            # Aplica marca de água e define URL
            processing_result = True
            if category_key in ["fotografias", "designs"]:
                processing_result = add_watermark_to_image(local_original_path, local_original_path) # Substitui o ficheiro local
                file_data["url"] = f"{PUBLIC_URL}/{category_name}/{filename.replace(' ', '%20')}"

            elif category_key == "videos":
                local_watermarked_path = os.path.join(TEMP_DIR, f"wm_{filename}")
                processing_result = add_watermark_to_video(local_original_path, local_watermarked_path, width)
                if processing_result is True: os.rename(local_watermarked_path, local_original_path) # Renomeia para o nome original
                file_data["url"] = f"{PUBLIC_URL}/{category_name}/{filename.replace(' ', '%20')}"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')

            # Faz o upload do ficheiro modificado, substituindo o original no R2
            if processing_result is True:
                subprocess.run(["rclone", "copyto", local_original_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{category_name}/{filename}"], check=True)
                new_data[category_key].append(file_data)
                print(f"  -> Sucesso: {filename} processado e atualizado no R2.")
            else:
                raise Exception(processing_result)

        except Exception as e:
            error_message = f"FALHA AO PROCESSAR '{filename}': {e}"
            print(error_message); errors.append(error_message)
        finally:
            if os.path.exists(local_original_path): os.remove(local_original_path)
            
    # Adicionar as apresentações, que não são processadas
    apresentacoes_files = rclone_lsf(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/Apresentações")
    for f in apresentacoes_files:
        new_data['apresentacoes'].append({ "name": f, "titles": parse_filename(f), "url": f"{PUBLIC_URL}/Apresentações/{f.replace(' ', '%20')}", "orientation": "square" })

    # Escrever os ficheiros de saída
    print("\nA gerar ficheiro data.json final...")
    with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump(new_data, f, indent=2, ensure_ascii=False)

    if errors:
        print(f"\nAVISO: Ocorreram {len(errors)} erros. A verificar '{ERROR_LOG_FILE}'.")
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"Relatório de Erros do Workflow - {time.ctime(start_time)}\n\n"); f.writelines([f"- {error}\n" for error in errors])
    
    end_time = time.time()
    print(f"\n>>> SCRIPT CONCLUÍDO em {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()