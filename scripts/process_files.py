# Ficheiro: scripts/process_files.py (Versão Orquestradora)

import subprocess
import json
import os
import time
from datetime import datetime, timezone

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel", "Capas": "covers"
}
DATA_FILE = "data.json"
MANIFEST_FILE = "r2_file_manifest.txt"
TEMP_DIR = "temp_files"

# --- Funções Auxiliares ---
def run_command(cmd, check=True):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_lsl_json(path):
    result = run_command(["rclone", "lsl", "--json", path, "--recursive"])
    return json.loads(result.stdout) if result and result.stdout else []

def get_last_manifest_time():
    try:
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith("Gerado em:"):
                    parts = line.split()
                    date_str = " ".join(parts[2:5] + [parts[6]])
                    return datetime.strptime(date_str, "%b %d %H:%M:%S %Y").replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else: return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

# --- Lógica Principal ---
def main():
    start_time = time.time()
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("\n--- [FASE 1] Mapeando ficheiros e determinando o que processar ---")
    all_files_data = get_rclone_lsl_json(RCLONE_REMOTE)
    last_run_time = get_last_manifest_time()
    
    files_to_process = [
        item for item in all_files_data
        if datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00")) > last_run_time
    ]
    
    print(f"Encontrados {len(files_to_process)} ficheiros novos ou modificados para processar.")

    for item in files_to_process:
        path = item["Path"]
        filename = os.path.basename(path)
        category_folder = os.path.dirname(path)

        if category_folder not in CATEGORIES or CATEGORIES[category_folder] not in ["fotografias", "designs", "videos"]:
            continue
            
        print(f"-> A processar: {path}")
        local_path = os.path.join(TEMP_DIR, filename)
        
        # 1. Baixar o ficheiro original
        run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])

        # 2. Chamar o script especialista em marcas de água
        result = run_command(["python3", "scripts/apply_watermark.py", local_path], check=False)

        if result and result.returncode == 0:
            print(f"  -> Marca de água aplicada com sucesso a {filename}")
            
            is_image = CATEGORIES[category_folder] in ["fotografias", "designs"]
            if is_image:
                processed_filename = f"{os.path.splitext(filename)[0]}.jpg"
                final_path = os.path.join(category_folder, processed_filename)
                local_processed_path = os.path.join(TEMP_DIR, processed_filename)
            else: # Vídeo
                local_processed_path = os.path.join(TEMP_DIR, f"processed_{filename}")
                final_path = path

            # 3. Fazer upload do ficheiro processado, sobrescrevendo no R2
            print(f"  -> Upload para: {final_path}")
            run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_path}"])

            # 4. Se a extensão mudou (ex: PNG -> JPG), apaga o original
            if path.lower() != final_path.lower():
                print(f"  -> Apagando original obsoleto: {path}")
                run_command(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])
        else:
            print(f"  -> ERRO ou falha ao aplicar marca de água em {filename}. A ignorar.")

        # 5. Limpar ficheiros temporários
        if os.path.exists(local_path): os.remove(local_path)
        if 'local_processed_path' in locals() and os.path.exists(local_processed_path): os.remove(local_processed_path)

    print("\n--- [FASE 2] Gerando o ficheiro data.json final ---")
    final_r2_files = get_rclone_lsl_json(RCLONE_REMOTE)
    new_data = {key: [] for key in CATEGORIES.values()}
    
    for item in final_r2_files:
        path = item["Path"]
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
    print("Ficheiro data.json gerado com sucesso.")

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()