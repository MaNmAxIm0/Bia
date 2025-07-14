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
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes",
    "Melhores": "carousel"
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__ ), 'Montserrat.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
ERROR_LOG_FILE = "error_log.txt"
THUMBNAILS_DIR = "Thumbnails"
WATERMARKED_IMAGES_DIR = "Imagens"
WATERMARKED_VIDEOS_DIR = "Vídeos"

# --- Funções Auxiliares ---

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

def apply_watermark_to_image(input_path, output_path):
    try:
        with Image.open(input_path) as base_img:
            img_corrected = ImageOps.exif_transpose(base_img)
            final_img = img_corrected.convert("RGBA")
            draw = ImageDraw.Draw(final_img)
            font_size = max(20, int(min(final_img.width, final_img.height) * 0.035))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
                font.set_variation_by_name('SemiBold')
            except (IOError, AttributeError):
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(final_img.width * 0.02)
            x, y = final_img.width - text_width - margin, final_img.height - text_height - margin
            
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 200))
            final_img.save(output_path, "PNG")
        return True
    except Exception as e:
        return f"PIL Error: {e}"

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO...")
    if not os.path.exists(TEMP_DIR): os.makedirs(TEMP_DIR)
    
    existing_carousel_data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
                existing_carousel_data = {item['name']: item for item in existing_data.get('carousel', [])}
            except json.JSONDecodeError:
                print("AVISO: Ficheiro data.json existente está corrompido.")

    print("\n--- [FASE 1] Mapeando ficheiros no R2 ---")
    all_r2_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")
    
    new_data = {cat_key: [] for cat_key in CATEGORIES.values()}
    
    for path in all_r2_files:
        try:
            category_folder, filename = path.split('/', 1)
            if category_folder not in CATEGORIES: continue

            category_key = CATEGORIES[category_folder]
            print(f"A processar: {path}...")
            
            local_original_path = os.path.join(TEMP_DIR, filename)
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True, capture_output=True)

            width, height = get_media_dimensions(local_original_path, category_key)
            if width == 0 and category_key not in ['apresentacoes']:
                raise ValueError("Dimensões inválidas, a ignorar processamento.")

            # Lógica para o carrossel (com títulos e descrições)
            if category_key == 'carousel':
                existing_entry = existing_carousel_data.get(filename, {})
                new_data['carousel'].append({
                    "name": filename,
                    "titles": parse_filename_for_titles(filename),
                    "descriptions": existing_entry.get('descriptions', {"pt": "", "en": "", "es": ""}),
                    "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"
                })
                continue

            # Lógica para outras categorias (apenas com títulos)
            file_data = {
                "name": filename,
                "titles": parse_filename_for_titles(filename),
                "orientation": "horizontal" if width >= height else "vertical"
            }
            
            if category_key in ["fotografias", "designs"]:
                watermarked_filename = f"wm_{os.path.splitext(filename)[0]}.png"
                local_processed_path = os.path.join(TEMP_DIR, watermarked_filename)
                upload_path = f"{WATERMARKED_IMAGES_DIR}/{watermarked_filename}"
                
                result = apply_watermark_to_image(local_original_path, local_processed_path)
                if result is not True: raise Exception(f"Falha no watermarking: {result}")
                
                subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{upload_path}"], check=True, capture_output=True)
                file_data["url"] = f"{PUBLIC_URL}/{upload_path.replace(' ', '%20')}"
            
            elif category_key == "apresentacoes":
                file_data["url"] = f"{PUBLIC_URL}/{path.replace(' ', '%20')}"
            
            # Adicione aqui a sua lógica para vídeos, se for diferente
            elif category_key == "videos":
                # Placeholder para a sua lógica de watermarking de vídeo
                file_data["url"] = f"{PUBLIC_URL}/{path.replace(' ', '%20')}" # Deveria apontar para o vídeo com marca d'água
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')

            new_data[category_key].append(file_data)

        except Exception as e:
            print(f"  -> ERRO ao processar {path}: {e}")
        finally:
            if 'local_original_path' in locals() and os.path.exists(local_original_path): os.remove(local_original_path)
            if 'local_processed_path' in locals() and os.path.exists(local_processed_path): os.remove(local_processed_path)

    print("\nGerando ficheiro data.json final...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
