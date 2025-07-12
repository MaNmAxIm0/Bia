# scripts/process_files.py
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

def run_rclone_command(command ):
    """Executa um comando rclone e retorna a saída."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding="utf-8")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar rclone: {e.stderr}")
        return None

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
    
    # 1. Listar todos os ficheiros no bucket
    all_files_json = run_rclone_command(["rclone", "lsjson", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive"])
    if not all_files_json:
        print("Não foi possível listar ficheiros do R2. A sair.")
        return
        
    all_files = json.loads(all_files_json)
    
    # 2. Listar thumbnails existentes
    existing_thumbs_str = run_rclone_command(["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/thumbs/"])
    existing_thumbs = set(existing_thumbs_str.splitlines()) if existing_thumbs_str else set()
    print(f"Encontradas {len(existing_thumbs)} thumbnails existentes.")

    output_data = {category: [] for category in FOLDER_TO_CATEGORY_MAP.values()}
    
    # 3. Processar cada ficheiro
    for file_info in all_files:
        path = file_info.get("Path", "")
        if not path or "/" not in path or path.lower().endswith('desktop.ini'):
            continue

        folder_name = path.split('/')[0]
        category = FOLDER_TO_CATEGORY_MAP.get(folder_name)
        if not category:
            continue

        filename = os.path.basename(path)
        
        # Se for um vídeo, tenta gerar a thumbnail
        if category == "videos":
            thumb_basename = filename.rsplit('.', 1)[0]
            thumb_filename = f"{thumb_basename}.jpg"

            if thumb_filename not in existing_thumbs:
                print(f"A gerar thumbnail para: {filename}")
                local_video_path = "temp_video_file"
                
                # Descarrega o vídeo
                run_rclone_command(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_video_path])
                
                if os.path.exists(local_video_path):
                    local_thumb_path = "temp_thumb.jpg"
                    # Gera a thumbnail
                    subprocess.run([
                        "ffmpeg", "-i", local_video_path, "-ss", "00:00:01", 
                        "-vframes", "1", local_thumb_path, "-y"
                    ], capture_output=True)
                    
                    if os.path.exists(local_thumb_path):
                        # Faz o upload da thumbnail
                        run_rclone_command(["rclone", "copyto", local_thumb_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/thumbs/{thumb_filename}"])
                        print(f"Thumbnail '{thumb_filename}' gerada e enviada com sucesso.")
                        existing_thumbs.add(thumb_filename) # Adiciona à lista para não reprocessar
                        os.remove(local_thumb_path)
                    
                    os.remove(local_video_path)
                else:
                    print(f"AVISO: Falha ao descarregar {filename}. A ignorar thumbnail.")

    # 4. Gerar o data.json final (agora com conhecimento de todas as thumbnails)
    print("\nA gerar o ficheiro data.json final...")
    for file_info in all_files:
        path = file_info.get("Path", "")
        if not path or "/" not in path or path.lower().endswith('desktop.ini'):
            continue

        folder_name = path.split('/')[0]
        category = FOLDER_TO_CATEGORY_MAP.get(folder_name)
        if not category:
            continue

        filename = os.path.basename(path)
        titles = parse_filename(filename)
        encoded_path = urllib.parse.quote(path)
        
        item_data = {
            "name": filename,
            "titles": titles,
            "url": f"{PUBLIC_URL}/{encoded_path}"
        }

        if category == "videos":
            thumb_basename = filename.rsplit('.', 1)[0]
            thumb_filename = f"{thumb_basename}.jpg"
            if thumb_filename in existing_thumbs:
                encoded_thumb = urllib.parse.quote(thumb_filename)
                item_data["thumbnail_url"] = f"{PUBLIC_URL}/thumbs/{encoded_thumb}"
            else:
                item_data["thumbnail_url"] = "https://manmaxim0.github.io/Bia/imagens/work_thumb_video.png"
        
        output_data[category].append(item_data )

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print("Processo concluído. Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    main()