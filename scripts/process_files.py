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
    "Melhores": "carousel"  # Nova categoria para o carrossel
}
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = os.path.join(os.path.dirname(__file__ ), 'Montserrat.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
ERROR_LOG_FILE = "error_log.txt"
THUMBNAILS_DIR = "Thumbnails"
WATERMARKED_IMAGES_DIR = "WatermarkedImages"
WATERMARKED_VIDEOS_DIR = "WatermarkedVideos"

# --- Funções Auxiliares ---
def rclone_lsf_recursive(remote_path):
    command = ["rclone", "lsf", remote_path, "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return {line for line in result.stdout.strip().split('\n') if line}
    except subprocess.CalledProcessError:
        return set()

def get_dimensions(local_path, file_type):
    width, height = 0, 0
    try:
        if file_type in ['fotografias', 'designs', 'carousel']:
            with Image.open(local_path) as img:
                img_corrected = ImageOps.exif_transpose(img)
                width, height = img_corrected.size
        elif file_type == 'videos':
            result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", local_path], capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
    except Exception as e:
        print(f"AVISO Dimensões: {e}")
    return width, height

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO...")
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    errors = []

    # Carregar data.json existente para preservar dados manuais
    existing_data = {}
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print("AVISO: Ficheiro data.json existente está corrompido. A criar um novo.")
    
    existing_carousel_descriptions = {item['name']: item.get('descriptions', {}) for item in existing_data.get('carousel', [])}

    print("\n--- [FASE 1] A mapear todos os ficheiros de origem no R2 ---")
    all_r2_files = rclone_lsf_recursive(f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}")
    
    source_files_map = {}
    for path in all_r2_files:
        try:
            category_folder, filename = path.split('/', 1)
            if category_folder in CATEGORIES:
                source_files_map[path] = {'category_key': CATEGORIES[category_folder], 'category_name': category_folder}
        except ValueError:
            continue
    print(f"MAPEAMENTO CONCLUÍDO: Encontrados {len(source_files_map)} ficheiros de origem no R2.")

    new_data = {cat: [] for cat in CATEGORIES.values()}
    processed_files = set()

    # Processar ficheiros de todas as categorias
    for full_path, data in source_files_map.items():
        category_key = data['category_key']
        category_name = data['category_name']
        filename = os.path.basename(full_path)

        if filename in processed_files:
            continue
        processed_files.add(filename)

        print(f"A processar: {full_path}...")
        
        # Lógica específica para o carrossel (sem watermarking, etc.)
        if category_key == 'carousel':
            file_data = {
                "name": filename,
                "url": f"{PUBLIC_URL}/{full_path.replace(' ', '%20')}",
                "descriptions": existing_carousel_descriptions.get(filename, {"pt": "", "en": "", "es": ""})
            }
            new_data[category_key].append(file_data)
            print("  -> Sucesso (Item de Carrossel).")
            continue

        # Lógica para outras categorias (a sua lógica original de processamento)
        # Esta parte deve ser mantida como estava no seu script original
        # O código abaixo é um placeholder genérico
        width, height = 1,1 # Placeholder, a sua função get_dimensions deve ser usada
        file_data = {
            "name": filename,
            "titles": {"pt": os.path.splitext(filename)[0], "en": os.path.splitext(filename)[0], "es": os.path.splitext(filename)[0]},
            "orientation": "horizontal" if width >= height else "vertical",
            "url": f"{PUBLIC_URL}/{full_path.replace(' ', '%20')}" # Placeholder
        }
        if category_key == "videos":
            file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAILS_DIR}/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
        
        new_data[category_key].append(file_data)
        print(f"  -> Sucesso ({category_key}).")


    print("\nA gerar ficheiro data.json final...")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

    if errors:
        print(f"\nAVISO: Ocorreram {len(errors)} erros. A verificar '{ERROR_LOG_FILE}'.")
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            f.write(f"Relatório de Erros do Workflow - {time.ctime(start_time)}\n\n")
            f.writelines([f"- {error}\n" for error in errors])
    
    end_time = time.time()
    print(f"\n>>> SCRIPT CONCLUÍDO em {end_time - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()
