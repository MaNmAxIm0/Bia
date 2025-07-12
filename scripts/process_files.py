# scripts/process_files.py (Versão com Deteção de Orientação)
import subprocess
import json
import os
import urllib.parse

# --- CONFIGURAÇÃO PRINCIPAL ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
FOLDER_TO_CATEGORY_MAP = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
# --- FIM DA CONFIGURAÇÃO ---

def run_command(command, check=True ):
    """Executa um comando e retorna a saída."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=check, encoding="utf-8")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando {' '.join(command)}: {e.stderr}")
        return None

def get_orientation(local_file_path):
    """Usa ffprobe para obter a orientação de um ficheiro de media."""
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height", "-of", "json", local_file_path
    ]
    output = run_command(command)
    if not output:
        return "unknown"
    
    try:
        data = json.loads(output)
        width = data["streams"][0]["width"]
        height = data["streams"][0]["height"]
        
        if width > height:
            return "horizontal"
        elif height > width:
            return "vertical"
        else:
            return "square"
    except (KeyError, IndexError, json.JSONDecodeError):
        return "unknown"

def parse_filename(filename):
    name_part = filename.rsplit('.', 1)[0]
    titles_parts = name_part.split('_')
    if len(titles_parts) == 3:
        return {"pt": titles_parts[0].strip(), "en": titles_parts[1].strip(), "es": titles_parts[2].strip()}
    else:
        clean_title = name_part.replace('_', ' ').strip()
        return {"pt": clean_title, "en": clean_title, "es": clean_title}

def main():
    print("A iniciar o processamento de ficheiros...")
    
    all_files_json = run_command(["rclone", "lsjson", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive"])
    if not all_files_json: return
    all_files = json.loads(all_files_json)
    
    existing_thumbs_str = run_command(["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/thumbs/"])
    existing_thumbs = set(existing_thumbs_str.splitlines()) if existing_thumbs_str else set()

    output_data = {category: [] for category in FOLDER_TO_CATEGORY_MAP.values()}
    
    for file_info in all_files:
        path = file_info.get("Path", "")
        if not path or "/" not in path or path.lower().endswith('desktop.ini'):
            continue

        folder_name = path.split('/')[0]
        category = FOLDER_TO_CATEGORY_MAP.get(folder_name)
        if not category: continue

        filename = os.path.basename(path)
        titles = parse_filename(filename)
        encoded_path = urllib.parse.quote(path)
        
        item_data = {
            "name": filename,
            "titles": titles,
            "url": f"{PUBLIC_URL}/{encoded_path}",
            "orientation": "unknown" # Valor padrão
        }

        # Só precisamos de detetar a orientação para fotos e vídeos
        if category in ["fotografias", "videos"]:
            print(f"A processar: {filename}")
            local_file = "temp_media_file"
            run_command(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_file])
            
            if os.path.exists(local_file):
                item_data["orientation"] = get_orientation(local_file)
                print(f"--> Orientação detetada: {item_data['orientation']}")
                
                if category == "videos":
                    thumb_basename = filename.rsplit('.', 1)[0]
                    thumb_filename = f"{thumb_basename}.jpg"
                    if thumb_filename not in existing_thumbs:
                        print(f"--> A gerar thumbnail...")
                        local_thumb_path = "temp_thumb.jpg"
                        subprocess.run(["ffmpeg", "-i", local_file, "-ss", "00:00:01", "-vframes", "1", local_thumb_path, "-y"], capture_output=True)
                        if os.path.exists(local_thumb_path):
                            run_command(["rclone", "copyto", local_thumb_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/thumbs/{thumb_filename}"])
                            existing_thumbs.add(thumb_filename)
                            os.remove(local_thumb_path)
                
                os.remove(local_file)

        # Adiciona a thumbnail URL se for um vídeo
        if category == "videos":
            thumb_basename = filename.rsplit('.', 1)[0]
            thumb_filename = f"{thumb_basename}.jpg"
            if thumb_filename in existing_thumbs:
                item_data["thumbnail_url"] = f"{PUBLIC_URL}/thumbs/{urllib.parse.quote(thumb_filename)}"
            else:
                item_data["thumbnail_url"] = "https://manmaxim0.github.io/Bia/imagens/work_thumb_video.png"
        
        output_data[category].append(item_data )

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("Processo concluído. Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    main()
