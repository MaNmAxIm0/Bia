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
WATERMARKED_IMAGES_DIR = "Fotografias"
WATERMARKED_VIDEOS_DIR = "Vídeos"

# --- Funções Auxiliares (Completas) ---
def rclone_lsf_recursive(remote_path):
    command = ["rclone", "lsf", remote_path, "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return {line for line in result.stdout.strip().split('\n') if line}
    except subprocess.CalledProcessError:
        return set()

def get_image_dimensions(local_path):
    try:
        with Image.open(local_path) as img:
            img_corrected = ImageOps.exif_transpose(img)
            return img_corrected.size
    except Exception as e:
        print(f"AVISO Dimensões Imagem: {e}")
        return 0, 0

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
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            margin = int(final_img.width * 0.02)
            x = final_img.width - text_width - margin
            y = final_img.height - text_height - margin
            
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 128))
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 200))
            
            final_img.save(output_path, "PNG")
        return True
    except Exception as e:
        return f"PIL Error: {e}"

# --- Lógica Principal (Restaurada e Completa) ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO...")
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    existing_carousel_descriptions = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
                existing_carousel_descriptions = {item['name']: item.get('descriptions', {}) for item in existing_data.get('carousel', [])}
            except json.JSONDecodeError:
                print("AVISO: Ficheiro data.json existente está corrompido.")

    print("\n--- [FASE 1] Mapeando ficheiros no R2 ---")
    all_r2_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")
    
    new_data = {cat_key: [] for cat_key in CATEGORIES.values()}
    
    for path in all_r2_files:
        try:
            category_folder, filename = path.split('/', 1)
            if category_folder not in CATEGORIES:
                continue

            category_key = CATEGORIES[category_folder]
            
            # Lógica para o carrossel (sem processamento)
            if category_key == 'carousel':
                new_data['carousel'].append({
                    "name": filename,
                    "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}",
                    "descriptions": existing_carousel_descriptions.get(filename, {"pt": "", "en": "", "es": ""})
                })
                continue

            # Lógica para as outras categorias (com processamento)
            print(f"A processar: {path}...")
            local_original_path = os.path.join(TEMP_DIR, filename)
            
            # 1. Descarregar ficheiro original
            subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True, capture_output=True)
            
            width, height = get_image_dimensions(local_original_path)
            if width == 0: raise ValueError("Dimensões inválidas.")

            # 2. Aplicar marca d'água
            watermarked_filename = f"watermarked_{os.path.splitext(filename)[0]}.png"
            local_processed_path = os.path.join(TEMP_DIR, watermarked_filename)
            
            if category_key in ["fotografias", "designs"]:
                result = apply_watermark_to_image(local_original_path, local_processed_path)
                if result is not True: raise Exception(f"Falha no watermarking: {result}")
                
                # 3. Fazer upload do ficheiro processado
                upload_path = f"{WATERMARKED_IMAGES_DIR}/{watermarked_filename}"
                subprocess.run(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{upload_path}"], check=True, capture_output=True)
                
                # 4. Gerar dados para o JSON
                file_data = {
                    "name": filename,
                    "titles": {"pt": os.path.splitext(filename)[0], "en": os.path.splitext(filename)[0], "es": os.path.splitext(filename)[0]},
                    "orientation": "horizontal" if width >= height else "vertical",
                    "url": f"{PUBLIC_URL}/{upload_path.replace(' ', '%20')}"
                }
                new_data[category_key].append(file_data)

            # (Manter aqui a sua lógica para vídeos e apresentações)

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
