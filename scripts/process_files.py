import subprocess
import json
import os
import time
from PIL import Image, ImageDraw, ImageFont, ExifTags, ImageOps

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
THUMBNAILS_DIR = "Thumbnails"

# --- Funções Auxiliares ---
def rclone_lsf_recursive(remote_path):
    command = ["rclone", "lsf", remote_path, "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return {line for line in result.stdout.strip().split('\n') if line}
    except subprocess.CalledProcessError:
        return set()

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]; parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2: return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else: return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}

def get_dimensions(local_path, file_type):
    width, height = 0, 0
    try:
        if file_type in ['fotografias', 'designs']:
            with Image.open(local_path) as img:
                img_corrected = ImageOps.exif_transpose(img)
                width, height = img_corrected.size
        elif file_type == 'videos':
            result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path], capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]; width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e: print(f"AVISO Dimensões: {e}")
    return width, height

# --- Funções de Processamento Corrigidas ---

def apply_watermark_to_image(input_path, output_path):
    try:
        with Image.open(input_path) as base_img:
            img_corrected = ImageOps.exif_transpose(base_img)
            final_img = img_corrected.convert("RGBA")
            draw = ImageDraw.Draw(final_img)
            font_size = max(20, int(min(final_img.width, final_img.height) * 0.065))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size); font.set_variation_by_name('SemiBold')
            except (IOError, AttributeError): font = ImageFont.load_default()
            _, top, _, bottom = font.getbbox(WATERMARK_TEXT)
            text_width = font.getlength(WATERMARK_TEXT)
            text_height = bottom - top
            margin = int(final_img.width * 0.02)
            x = final_img.width - text_width - margin
            y = final_img.height - text_height - margin - int(font_size * 0.1)
            draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220)); final_img.save(output_path, "PNG")
        return True
    except Exception as e: return f"PIL Error: {e}"

def apply_watermark_to_video(input_path, output_path, video_width, video_height):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", ""); 
    font_size = max(24, int(min(video_width, video_height) * 0.065))
    margin = int(video_width * 0.02)
    command = ["ffmpeg", "-i", input_path, "-vf", f"drawtext=text='{escaped_text}':fontfile='{FONT_PATH}':fontsize={font_size}:fontcolor=white@0.9:x=main_w-text_w-{margin}:y=main_h-text_h-{margin}:borderw=2:bordercolor=black@0.6", "-c:a", "copy", "-y", output_path]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, timeout=300); return True
    except subprocess.CalledProcessError as e: return f"FFmpeg Error: {e.stderr}"
    except subprocess.TimeoutExpired: return "FFmpeg Error: O processamento demorou demasiado tempo (timeout)."

# --- Lógica Principal Final ---
def main():
    start_time = time.time(); print(">>> INICIANDO SCRIPT DE PROCESSAMENTO...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    errors = []

    old_data_map = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            for category, items in old_data.items():
                for item in items:
                    if item.get('name'): old_data_map[item['name']] = item
        print(f"Ficheiro data.json anterior carregado com {len(old_data_map)} itens em cache.")

    print("\n--- A mapear todos os ficheiros de origem no R2 de uma só vez ---")
    all_source_files = rclone_lsf_recursive(f"R2:{BUCKET_NAME}")
    
    source_files_r2 = {}
    reverse_categories = {v: k for k, v in CATEGORIES.items()}
    for path in all_source_files:
        try:
            category_folder, filename = path.split('/', 1)
            if category_folder in reverse_categories:
                source_files_r2[filename] = {'category_key': category_folder, 'category_name': reverse_categories[category_folder]}
        except ValueError: continue
    print(f"MAPEAMENTO CONCLUÍDO: Encontrados {len(source_files_r2)} ficheiros de origem no R2.")

    new_data = {cat: [] for cat in CATEGORIES.values()}
    for filename, data in source_files_r2.items():
        category_key = data['category_key']
        category_name = data['category_name']
        base_name, ext = os.path.splitext(filename)

        # Constrói o URL final esperado para verificar a cache
        expected_url = f"{PUBLIC_URL}/{category_name}/{filename if category_key == 'videos' else f'{base_name}.png'}".replace(' ', '%20')
        cached_entry = old_data_map.get(filename)
        
        # Se a cache existir E o URL for o esperado, salta o processamento
        if cached_entry and cached_entry.get('url') == expected_url:
            new_data[category_key].append(cached_entry)
            continue

        print(f"A processar: {filename}...")
        local_original_path = os.path.join(TEMP_DIR, filename)
        
        try:
            subprocess.run(["rclone", "copyto", f"R2:{BUCKET_NAME}/{category_name}/{filename}", local_original_path], check=True, capture_output=True)
            width, height = get_dimensions(local_original_path, category_key)
            if width == 0: raise ValueError("Dimensões inválidas.")

            file_data = {"name": filename, "titles": parse_filename(filename), "orientation": "horizontal" if width >= height else "vertical"}
            
            processing_result = True
            final_filename = filename
            
            if category_key in ["fotografias", "designs"]:
                final_filename = f"{base_name}.png"
                local_processed_path = os.path.join(TEMP_DIR, final_filename)
                remote_path = f"{category_name}/{final_filename}"
                processing_result = apply_watermark_to_image(local_original_path, local_processed_path)
                file_data["url"] = f"{PUBLIC_URL}/{remote_path.replace(' ', '%20')}"

            elif category_key == "videos":
                local_processed_path = os.path.join(TEMP_DIR, f"wm_{filename}")
                remote_path = f"{category_name}/{final_filename}"
                processing_result = apply_watermark_to_video(local_original_path, local_processed_path, width, height)
                file_data["url"] = f"{PUBLIC_URL}/{remote_path.replace(' ', '%20')}"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{base_name}.jpg".replace(' ', '%20')
                if processing_result is True: os.rename(local_processed_path, local_original_path)

            if processing_result is True:
                final_local_path = local_original_path if category_key == "videos" else local_processed_path
                subprocess.run(["rclone", "copyto", final_local_path, f"R2:{BUCKET_NAME}/{remote_path}"], check=True, capture_output=True)
                if filename != final_filename:
                    subprocess.run(["rclone", "deletefile", f"R2:{BUCKET_NAME}/{category_name}/{filename}"], check=True, capture_output=True)
                new_data[category_key].append(file_data)
                print(f"  -> Sucesso.")
            else:
                raise Exception(processing_result)

        except Exception as e: errors.append(f"FALHA AO PROCESSAR '{filename}': {e}")
        finally:
            if os.path.exists(local_original_path): os.remove(local_original_path)
            if 'local_processed_path' in locals() and os.path.exists(local_processed_path): os.remove(local_processed_path)
            
    apresentacoes_files = rclone_lsf_recursive(f"R2:{BUCKET_NAME}/Apresentações")
    for path in apresentacoes_files:
        if path.startswith("Apresentações/"):
            f = os.path.basename(path)
            new_data['apresentacoes'].append({ "name": f, "titles": parse_filename(f), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}", "orientation": "square" })

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