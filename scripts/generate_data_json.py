# scripts/generate_data_json.py
import subprocess
import json
import os

# --- CONFIGURAÇÕES ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets" # O nome do seu bucket no R2
R2_PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev" # SUBSTITUA PELO SEU URL PÚBLICO
# DEPOIS DA CORREÇÃO
FOLDER_TO_CATEGORY_MAP = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
# --------------------

def parse_filename(filename ):
    name_part = filename.rsplit('.', 1)[0]
    titles = name_part.split('_')
    return {
        "pt": titles[0].strip() if len(titles) > 0 else name_part,
        "en": titles[1].strip() if len(titles) > 1 else (titles[0].strip() if len(titles) > 0 else name_part),
        "es": titles[2].strip() if len(titles) > 2 else (titles[0].strip() if len(titles) > 0 else name_part)
    }

def list_all_files_in_bucket():
    remote_path = f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}"
    command = ["rclone", "lsjson", remote_path, "--recursive"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print("Erro ao listar ficheiros do R2:", result.stderr)
        return []
    return json.loads(result.stdout)

def main():
    print("A listar todos os ficheiros do bucket R2...")
    files = list_all_files_in_bucket()
    
    output_data = {key: [] for key in FOLDER_TO_CATEGORY_MAP.values()}

    for file_info in files:
        path = file_info.get("Path", "")
        if "/" not in path:
            continue

        folder_name, file_name = path.split('/', 1)
        category = FOLDER_TO_CATEGORY_MAP.get(folder_name)
        
        if not category:
            continue
            
        titles = parse_filename(file_name)
        item = {
            "name": file_name,
            "titles": titles,
            "url": f"{R2_PUBLIC_URL}/{path.replace(' ', '%20')}" # Codifica espaços no URL
        }
        output_data[category].append(item)
    
    print("Resumo dos ficheiros encontrados:")
    for category, items in output_data.items():
        print(f"- {category.capitalize()}: {len(items)} ficheiros")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        
    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    main()
