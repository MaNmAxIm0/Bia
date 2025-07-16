# Ficheiro: /scripts/process_files.py (VERSÃO FINAL E DEFINITIVA)

import subprocess
import json
import os
import time
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
MAX_IMAGE_WIDTH = 1920
JPEG_QUALITY = 85

# --- Funções Auxiliares ---
def run_command(cmd, check=True):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check, encoding='utf-8')
        return result
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_files(path, extension_filter=None):
    """Obtém a lista de ficheiros, opcionalmente filtrando por extensão."""
    print(f"A obter lista de ficheiros de: {path}")
    result = run_command(["rclone", "lsf", path, "--recursive", "--files-only"])
    if not result: return set()
    
    files = {line.strip() for line in result.stdout.split('\n') if line.strip()}
    if extension_filter:
        return {f for f in files if f.lower().endswith(extension_filter)}
    return files

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else: return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def apply_watermark_and_compress(input_path, output_path):
    try:
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
        return True
    except Exception as e:
        print(f"  ERRO ao aplicar marca de água: {e}")
        return False

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("\n--- [FASE 1] Mapeando ficheiros existentes no R2 ---")
    all_r2_files = get_rclone_files(RCLONE_REMOTE)
    
    # Cria um conjunto de nomes base de ficheiros já processados (JPGs)
    processed_jpg_basenames = {os.path.splitext(f)[0] for f in all_r2_files if f.lower().endswith('.jpg')}

    files_to_process = []
    for path in all_r2_files:
        basename = os.path.splitext(path)[0]
        # Adiciona à lista de processamento se o nome base ainda não existir como JPG
        if not path.lower().endswith('.jpg') and basename not in processed_jpg_basenames:
            category_folder = os.path.dirname(path)
            if category_folder in CATEGORIES and CATEGORIES[category_folder] in ["fotografias", "designs"]:
                files_to_process.append(path)

    if not files_to_process:
        print("Nenhuma imagem nova para processar.")
    else:
        print(f"Encontradas {len(files_to_process)} imagens para processar.")

    for path in files_to_process:
        try:
            print(f"-> Processando: {path}")
            filename = os.path.basename(path)
            
            # **CORREÇÃO CRÍTICA**: Garante que o diretório local existe
            local_path = os.path.join(TEMP_DIR, filename)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
            
            processed_filename = f"{os.path.splitext(filename)[0]}.jpg"
            local_processed_path = os.path.join(TEMP_DIR, processed_filename)

            if apply_watermark_and_compress(local_path, local_processed_path):
                final_path = os.path.join(os.path.dirname(path), processed_filename)
                print(f"  -> Upload para: {final_path}")
                run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_path}"])

                print(f"  -> Apagando original obsoleto: {path}")
                run_command(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])
            
            os.remove(local_path)
            if os.path.exists(local_processed_path):
                os.remove(local_processed_path)

        except Exception as e:
            print(f"  -> ERRO CRÍTICO ao processar {path}: {e}")
            
    print("\n--- [FASE 2] Gerando o ficheiro data.json final ---")
    final_r2_files = get_rclone_files(RCLONE_REMOTE)
    new_data = {key: [] for key in CATEGORIES.values()}
    
    for path in final_r2_files:
        category_folder = os.path.dirname(path)
        if category_folder in CATEGORIES:
            filename = os.path.basename(path)
            category_key = CATEGORIES[category_folder]
            
            if category_key in ['apresentacoes', 'carousel', 'capas', 'videos'] or \
               (category_key in ['fotografias', 'designs'] and path.lower().endswith('.jpg')):
                
                file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"}
                if category_key == 'videos':
                    file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
                new_data[category_key].append(file_data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print("Ficheiro data.json gerado com sucesso.")

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()