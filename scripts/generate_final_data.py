# Ficheiro: scripts/generate_final_data.py

import subprocess, json, os

# --- Configuração ---
RCLONE_REMOTE = "R2:bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias", "Vídeos": "videos", "Designs": "designs",
    "Apresentações": "apresentacoes", "Melhores": "carousel", "Capas": "covers"
}
DATA_FILE = "data.json"

def get_rclone_files(path):
    result = subprocess.run(["rclone", "lsf", path, "--recursive", "--files-only"], capture_output=True, text=True, check=True, encoding='utf-8')
    return {line.strip() for line in result.stdout.split('\n') if line.strip()}

def parse_filename_for_titles(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[2].replace('-', ' ')}
    elif len(parts) == 2: return {'pt': parts[0].replace('-', ' '), 'en': parts[1].replace('-', ' '), 'es': parts[1].replace('-', ' ')}
    else: return {'pt': name_without_ext.replace('-', ' '), 'en': name_without_ext.replace('-', ' '), 'es': name_without_ext.replace('-', ' ')}

def main():
    print("Gerando data.json a partir do estado final do R2...")
    all_final_files = get_rclone_files(RCLONE_REMOTE)
    new_data = {key: [] for key in CATEGORIES.values()}

    for path in all_final_files:
        category_folder = os.path.dirname(path)
        if category_folder in CATEGORIES:
            filename = os.path.basename(path)
            category_key = CATEGORIES[category_folder]
            
            file_data = {
                "name": filename,
                "titles": parse_filename_for_titles(filename),
                "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}"
            }
            if category_key == 'videos':
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/Thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
            
            # Nota: a orientação terá de ser determinada por outra via se for necessária no data.json
            
            new_data[category_key].append(file_data)
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    main()