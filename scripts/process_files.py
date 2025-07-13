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

EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)

# --- Funções Auxiliares ---
def rclone_lsf(remote_path):
    command = ["rclone", "lsf", remote_path, "--files-only"]
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

# --- Funções de Processamento Corrigidas ---

def add_watermark_to_image(input_path, output_path):
    """Aplica uma marca de água a uma imagem, corrigindo a rotação EXIF."""
    try:
        with Image.open(input_path) as base_img:
            # CORREÇÃO: Aplica a rotação com base nos dados EXIF
            img_corrected = ImageOps.exif_transpose(base_img)
            
            # Converte para RGBA para suportar transparência na marca de água
            final_img = img_corrected.convert("RGBA")
            draw = ImageDraw.Draw(final_img)
            
            font_size = max(20, int(final_img.width * 0.04))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
                font.set_variation_by_name('SemiBold')
            except (IOError, AttributeError):
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font); textwidth, textheight = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(final_img.width * 0.02); x, y = final_img.width - textwidth - margin, final_img.height - textheight - margin
            
            draw.text((x + 2, y + 2), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 220))
            
            final_img.save(output_path, "PNG")
        return True
    except Exception as e:
        return f"PIL Error: {e}"

def add_watermark_to_video(input_path, output_path, video_width):
    escaped_text = WATERMARK_TEXT.replace(":", "\\:").replace("'", ""); font_size = max(24, int(video_width * 0.035)); margin = int(video_width * 0.02)
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
                img_corrected = ImageOps.exif_transpose(img)
                width, height = img_corrected.size
        elif file_type == 'videos':
            result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path], capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]; width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e: print(f"AVISO Dimensões: {e}")
    return width, height

# --- Lógica Principal Final ---
def main():
    start_time = time.time(); print(">>> INICIANDO SCRIPT DE PROCESSAMENTO...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    errors = []

    old_data_map = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f: old_data = json.load(f)
        for category, items in old_data.items():
            for item in items: old_data_map[item.get('name')] = item
        print(f"Ficheiro data.json anterior carregado com {len(old_data_map)} itens em cache.")

    source_files_r2 = {}
    for category_name, category_key in CATEGORIES.items():
        if category_key == 'apresentacoes': continue
        path = f"R2:{BUCKET_NAME}/{category_name}"
        files = rclone_lsf(path)
        for f in files: source_files_r2[f] = {'category_key': category_key, 'category_name': category_name}
    print(f"Encontrados {len(source_files_r2)} ficheiros de origem no R2.")

    new_data = {cat: [] for cat in CATEGORIES.values()}
    for filename, data in source_files_r2.items():
        category_key = data['category_key']
        category_name = data['category_name']
        
        cached_entry = old_data_map.get(filename)
        if cached_entry:
            new_data[category_key].append(cached_entry)
            continue

        print(f"NOVO/ALTERADO: {filename}. A processar...")
        local_original_path = os.path.join(TEMP_DIR, filename)
        
        try:
            subprocess.run(["rclone", "copyto", f"R2:{BUCKET_NAME}/{category_name}/{filename}", local_original_path], check=True)
            width, height = get_dimensions(local_original_path, category_key)
            if width == 0: raise ValueError("Dimensões inválidas.")

            file_data = {"name": filename, "titles": parse_filename(filename), "orientation": "horizontal" if width >= height else "vertical"}
            
            processing_result = True
            base_name, ext = os.path.splitext(filename)
            
            if category_key in ["fotografias", "designs"]:
                final_filename = f"{base_name}.png"
                local_processed_path = os.path.join(TEMP_DIR, final_filename)
                processing_result = add_watermark_to_image(local_original_path, local_processed_path)
                remote_path = f"{category_name}/{final_filename}"
                file_data["url"] = f"{PUBLIC_URL}/{remote_path.replace(' ', '%20')}"

            elif category_key == "videos":
                final_filename = filename # O nome do ficheiro de vídeo não muda
                local_processed_path = os.path.join(TEMP_DIR, f"wm_{filename}")
                processing_result = add_watermark_to_video(local_original_path, local_processed_path, width)
                remote_path = f"{category_name}/{final_filename}"
                file_data["url"] = f"{PUBLIC_URL}/{remote_path.replace(' ', '%20')}"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{base_name}.jpg".replace(' ', '%20')
            
            if processing_result is True:
                # Renomeia o ficheiro processado para o nome final antes de fazer o upload
                if category_key == "videos": os.rename(local_processed_path, local_original_path)
                else: os.rename(local_processed_path, os.path.join(TEMP_DIR, final_filename))

                final_local_path = os.path.join(TEMP_DIR, final_filename)
                subprocess.run(["rclone", "copyto", final_local_path, f"R2:{BUCKET_NAME}/{remote_path}"], check=True)
                
                # Se o nome mudou (ex: .jpeg para .png), apaga o ficheiro antigo
                if filename != final_filename: subprocess.run(["rclone", "deletefile", f"R2:{BUCKET_NAME}/{category_name}/{filename}"], check=True)

                new_data[category_key].append(file_data)
                print(f"  -> Sucesso: {filename} processado e atualizado.")
            else:
                raise Exception(processing_result)

        except Exception as e:
            errors.append(f"FALHA AO PROCESSAR '{filename}': {e}")
        finally:
            for f in os.listdir(TEMP_DIR): os.remove(os.path.join(TEMP_DIR, f))
            
    # Adicionar as apresentações
    apresentacoes_files = rclone_lsf(f"R2:{BUCKET_NAME}/Apresentações")
    for f in apresentacoes_files:
        new_data['apresentacoes'].append({ "name": f, "titles": parse_filename(f), "url": f"{PUBLIC_URL}/Apresentações/{f.replace(' ', '%20')}", "orientation": "square" })

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