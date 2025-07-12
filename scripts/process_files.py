import subprocess
import json
import os

# --- Configuração ---
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"
CATEGORIES = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
FALLBACK_THUMBNAIL_URL = "https://manmaxim0.github.io/Bia/imagens/work_thumb_video.png"

def get_all_files_with_metadata( ):
    """Obtém todos os ficheiros e os seus metadados numa só chamada."""
    print("A obter a lista de todos os ficheiros e metadados do R2...")
    command = [
        "rclone", "lsjson",
        f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}",
        "--metadata",
        "--recursive",
        "--no-mimetype"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Lista de ficheiros e metadados obtida com sucesso.")
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}")
        if hasattr(e, 'stderr'):
            print(f"Stderr: {e.stderr}")
        return []

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) == 1:
        titles = {'pt': parts[0], 'en': parts[0], 'es': parts[0]}
    elif len(parts) == 2:
        titles = {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else:
        titles = {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    return titles

def process_files():
    all_files = get_all_files_with_metadata()
    if not all_files:
        print("Nenhum ficheiro encontrado no R2. A sair.")
        return

    output_data = {cat: [] for cat in CATEGORIES.values()}

    for item in all_files:
        path = item.get("Path", "")
        if "desktop.ini" in path or "/_thumbnails/" in path or not path:
            continue

        try:
            category_name, filename = path.split('/', 1)
        except ValueError:
            continue

        if category_name in CATEGORIES:
            category_key = CATEGORIES[category_name]
            
            # Lê as dimensões dos metadados guardados pelo workflow
            metadata = item.get("Metadata", {})
            width = int(metadata.get("width", 0))
            height = int(metadata.get("height", 0))

            orientation = "square"
            if width > 0 and height > 0:
                orientation = "horizontal" if width >= height else "vertical"

            file_data = {
                "name": filename,
                "titles": parse_filename(filename),
                "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}",
                "orientation": orientation
            }

            if category_key == "videos":
                thumb_filename = os.path.splitext(filename)[0] + ".jpg"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/_thumbnails/{thumb_filename.replace(' ', '%20')}"

            output_data[category_key].append(file_data)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    process_files()
