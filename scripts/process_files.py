# Ficheiro: scripts/process_files.py (VERSÃO FINAL COM IMPORT RELATIVO)

import subprocess
import json
import os
import time
import sys
from datetime import datetime, timezone
# CORREÇÃO: Adicionado um ponto (.) antes de 'apply_watermark' para indicar importação relativa
from .apply_watermark import apply_image_watermark, apply_video_watermark

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel", "Capas": "covers"
}
PROCESSABLE_CATEGORIES = ["fotografias", "videos", "designs"]
SUPPORTED_IMAGE_EXT = ['.jpeg', '.jpg', '.png', '.webp']
SUPPORTED_VIDEO_EXT = ['.mp4', '.mov', '.avi']

THUMBNAIL_DIR_R2 = "Thumbnails"
FONT_PATH = os.path.join(os.path.dirname(__file__), 'Montserrat-SemiBold.ttf')
TEMP_DIR = "temp_files"
DATA_FILE = "data.json"
MANIFEST_FILE = "r2_file_manifest.txt"
ERROR_LOG_FILE = "upload_errors.log"

# --- Funções Auxiliares ---
def run_command(cmd, check=True):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        print(f"ERRO ao executar: {' '.join(cmd)}\n{e.stderr}")
        return None

def get_rclone_json_list(path, flags=None):
    if flags is None:
        flags = []
    cmd = ["rclone", "lsjson", path] + flags
    result = run_command(cmd)
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
        print(f"AVISO: Manifesto não encontrado ou inválido. A processar todos os ficheiros.")
    return datetime.fromtimestamp(0, tz=timezone.utc)

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def generate_thumbnail(video_path, thumb_path):
    print(f"  -> A gerar thumbnail para: {os.path.basename(video_path)}")
    try:
        command = ["ffmpeg", "-i", video_path, "-ss", "00:00:01.000", "-vframes", "1", "-q:v", "2", "-y", thumb_path]
        run_command(command, check=True)
        return True
    except Exception as e:
        print(f"  ERRO ao gerar thumbnail: {e}", file=sys.stderr)
        return False

# --- Lógica Principal ---
def main():
    start_time = time.time()
    upload_errors = []
    print(">>> INICIANDO SCRIPT DE PROCESSAMENTO E GERAÇÃO DE DADOS...")
    os.makedirs(TEMP_DIR, exist_ok=True)

    print("\n--- [FASE 1] Verificando ficheiros novos ou modificados ---")
    all_files_data = get_rclone_json_list(RCLONE_REMOTE, ["--recursive"])
    
    if not all_files_data:
        print("AVISO: Nenhum ficheiro encontrado no bucket R2. A sair.")
        with open(DATA_FILE, "w", encoding="utf-8") as f: json.dump({key: [] for key in CATEGORIES.values()}, f)
        with open(MANIFEST_FILE, "w", encoding="utf-8") as f: f.write("Manifesto vazio.")
        sys.exit(0)

    existing_thumbnails = {os.path.splitext(f["Name"])[0] for f in get_rclone_json_list(f"{RCLONE_REMOTE}/{THUMBNAIL_DIR_R2}")}
    last_run_time = get_last_manifest_time()

    for item in all_files_data:
        try:
            path = item["Path"]
            filename = os.path.basename(path)
            basename, ext = os.path.splitext(filename)
            category_folder = os.path.dirname(path)
            category_key = CATEGORIES.get(category_folder)
            
            if not category_key or category_key not in PROCESSABLE_CATEGORIES:
                continue
            
            is_video = ext.lower() in SUPPORTED_VIDEO_EXT
            is_image = ext.lower() in SUPPORTED_IMAGE_EXT
            if not is_video and not is_image:
                continue

            mod_time = datetime.fromisoformat(item["ModTime"].replace("Z", "+00:00"))
            if mod_time < last_run_time:
                continue

            print(f"-> Processando ficheiro modificado: {path}")
            
            local_path = os.path.join(TEMP_DIR, filename)
            run_command(["rclone", "copyto", f"{RCLONE_REMOTE}/{path}", local_path])
            
            if is_video and basename not in existing_thumbnails:
                local_thumb_path = os.path.join(TEMP_DIR, f"{basename}.jpg")
                if generate_thumbnail(local_path, local_thumb_path):
                    upload_result = run_command(["rclone", "copyto", local_thumb_path, f"{RCLONE_REMOTE}/{THUMBNAIL_DIR_R2}/{basename}.jpg"])
                    if not upload_result or upload_result.returncode != 0:
                        upload_errors.append(f"Falha no upload da thumbnail: {basename}.jpg")
                    os.remove(local_thumb_path)
            
            print(f"  -> A aplicar marca de água...")
            output_basename = os.path.splitext(filename)[0]
            output_ext = ".jpg" if is_image else ext
            local_processed_path = os.path.join(TEMP_DIR, f"wm_{output_basename}{output_ext}")
            
            success = False
            if is_image:
                success = apply_image_watermark(local_path, local_processed_path, FONT_PATH)
            elif is_video:
                success = apply_video_watermark(local_path, local_processed_path, FONT_PATH)

            if success:
                final_r2_path = os.path.join(category_folder, f"{output_basename}{output_ext}")
                print(f"  -> A enviar ficheiro com marca de água para: {final_r2_path}")
                upload_result = run_command(["rclone", "copyto", local_processed_path, f"{RCLONE_REMOTE}/{final_r2_path}"])
                if not upload_result or upload_result.returncode != 0:
                    upload_errors.append(f"Falha no upload do ficheiro com marca de água: {final_r2_path}")
                
                if is_image and path != final_r2_path:
                    print(f"  -> A apagar original não-JPG: {path}")
                    run_command(["rclone", "deletefile", f"{RCLONE_REMOTE}/{path}"])

            if os.path.exists(local_path): os.remove(local_path)
            if os.path.exists(local_processed_path): os.remove(local_processed_path)

        except Exception as e:
             print(f"  -> ERRO CRÍTICO ao processar {item.get('Path', 'item desconhecido')}: {e}")
             upload_errors.append(f"CRITICAL ERROR on file: {item.get('Path', 'unknown')}")
            
    print("\n--- [FASE 2] Gerando o ficheiro data.json e o manifesto final ---")
    final_r2_files = get_rclone_json_list(RCLONE_REMOTE, ["--recursive"])
    new_data = {v: [] for v in CATEGORIES.values()}
    
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        f.write(f"Manifesto de Ficheiros do Bucket '{os.path.basename(RCLONE_REMOTE)}'\n")
        f.write(f"Gerado em: {datetime.now().strftime('%a %b %d %H:%M:%S WEST %Y')}\n")
        f.write("----------------------------------------------------\n")
        
        for item in sorted(final_r2_files, key=lambda x: x["ModTime"], reverse=True):
            path, mod_time_str, size = item["Path"], item["ModTime"], item["Size"]
            mod_time = datetime.fromisoformat(mod_time_str.replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{mod_time}\t{size:>10}\t{path}\n")

            category_folder = os.path.dirname(path)
            if category_folder in CATEGORIES:
                category_key = CATEGORIES[category_folder]
                file_data = {"name": os.path.basename(path), "titles": parse_filename_for_titles(item["Name"]), "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"}
                if category_key == 'videos':
                    thumb_name = os.path.splitext(item["Name"])[0]
                    file_data["thumbnail_url"] = f"{PUBLIC_URL}/{THUMBNAIL_DIR_R2}/{thumb_name.replace(' ', '%20')}.jpg"
                new_data[category_key].append(file_data)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    print("Ficheiro data.json e manifesto gerados com sucesso.")

    if upload_errors:
        print("\n--- [ERROS DE UPLOAD] ---")
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
            for error in upload_errors:
                print(error)
                f.write(error + "\n")
        print(f"Um log com {len(upload_errors)} erros foi guardado em '{ERROR_LOG_FILE}'")

    print(f"\n>>> SCRIPT CONCLUÍDO em {time.time() - start_time:.2f} segundos.")

if __name__ == "__main__":
    main()