# Ficheiro: scripts/process_files.py (VERSÃO FINAL E UNIFICADA)

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
def run_command(cmd, check=True):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_lsl_json(path):
    result = run_command(["rclone", "lsljson", path, "--recursive"])
    return json.loads(result.stdout) if result and result.stdout else []

def get_last_manifest_time():
    try:
        with open(MANIFEST_FILE, 'r') as f:
            for line in f:
                if line.startswith("Gerado em:"):
                    parts = line.split()
                    date_str = " ".join(parts[2:5] + [parts[6]])
                    return datetime.strptime(date_str, "%b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)
    except Exception as e:
        print(f"AVISO: Manifesto não encontrado ou inválido ({e}). A processar todos os ficheiros que necessitem.")
    return datetime.fromtimestamp(0, tz=timezone.utc)

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else: return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def apply_watermark(input_path, output_path, is_video):
    # (O corpo desta função permanece igual, é a lógica de manipulação de imagem/vídeo)
    # ... cole aqui a função apply_watermark da versão anterior ...
    pass # Placeholder

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("\n--- [FASE 1] Mapeando ficheiros e determinando o que processar ---")
    all_files_data = get_rclone_lsl_json(RCLONE_REMOTE)
    last_run_time = get_last_manifest_time()
    
    existing_jpg_basenames = {os.path.splitext(item["Path"])[0] for item in all_files_data if item["Path"].lower().endswith('.jpg')}

    for item in all_files_data:
        try:
            path = item["Path"]
            filename = os.path.basename(path)
            basename, ext = os.path.splitext(filename)
            category_folder = os.path.dirname(path)
            
            if category_folder not in CATEGORIES: continue
            
            category_key = CATEGORIES[category_folder]

            is_new_video = category_key == "videos" and datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00")) > last_run_time
            is_new_image = category_key in ["fotografias", "designs"] and not path.lower().endswith('.jpg') and os.path.join(category_folder, basename) not in existing_jpg_basenames
            
            if not is_new_video and not is_new_image:
                continue

            print(f"-> Processamento necessário para: {path}")
            
            local_path = os.path.join(TEMP_DIR, filename)
            run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
            
            local_processed_path = os.path.join(TEMP_DIR, f"proc_{filename}")
            
            if apply_watermark(local_path, local_processed_path, is_new_video):
                if is_new_image:
                    final_path = os.path.join(category_folder, f"{basename}.jpg")
                else:
                    final_path = path

                print(f"  -> Upload para: {final_path}")
                run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_path}"])
                if path.lower() != final_path.lower():
                    print(f"  -> Apagando original obsoleto: {path}")
                    run_command(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])
            
            os.remove(local_path)
            if os.path.exists(local_processed_path): os.remove(local_processed_path)

        except Exception as e: print(f"  -> ERRO CRÍTICO ao processar {item['Path']}: {e}")
            
    print("\n--- [FASE 2] Gerando o ficheiro data.json e o manifesto final ---")
    final_r2_files = get_rclone_lsl_json(RCLONE_REMOTE)
    new_data = {key: [] for key in CATEGORIES.values()}
    
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write("Manifesto de Ficheiros do Bucket 'bia-portfolio-assets'\n")
        f.write(f"Gerado em: {datetime.now().strftime('%a %b %d %H:%M:%S WEST %Y')}\n")
        f.write("----------------------------------------------------\n")
        
        # Ordena por data de modificação, do mais recente para o mais antigo
        for item in sorted(final_r2_files, key=lambda x: x["ModTime"], reverse=True):
            path = item["Path"]
            mod_time = datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{mod_time}\t{item['Size']:>10}\t{path}\n")

            category_folder = os.path.dirname(path)
            if category_folder in CATEGORIES:
                filename = os.path.basename(path)
                category_key = CATEGORIES[category_folder]
                
                if category_key in ['fotografias', 'designs'] and not path.lower().endswith('.jpg'):
                    continue
                
                file_data = {"name": filename, "titles": parse_filename_for_titles(filename), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"}
                if category_key == 'videos':
                    file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
                new_data[category_key].append(file_data)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print("Ficheiro data.json e manifesto gerados com sucesso.")

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()