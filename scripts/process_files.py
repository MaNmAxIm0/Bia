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

def get_file_list( ):
    """Obtém a lista de todos os ficheiros do R2."""
    print("A obter a lista de todos os ficheiros do R2...")
    command = ["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        print("Lista de ficheiros obtida com sucesso.")
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}")
        print(f"Stderr: {e.stderr}")
        return []

def get_dimensions(remote_path):
    """Descarrega um ficheiro, obtém as suas dimensões com ffprobe e apaga-o."""
    local_filename = os.path.basename(remote_path)
    print(f"A obter dimensões para: {remote_path}")
    
    # Descarregar
    try:
        subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_path}", f"./{local_filename}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"AVISO: Falha ao descarregar '{remote_path}'. A ignorar. Erro: {e.stderr}")
        return 0, 0

    # Obter dimensões
    width, height = 0, 0
    try:
        command = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", f"./{local_filename}"
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        dims = json.loads(result.stdout)["streams"][0]
        width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
        print(f"Dimensões encontradas: {width}x{height}")
    except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError, KeyError) as e:
        print(f"AVISO: Não foi possível obter dimensões para '{local_filename}'. Erro: {e}")
    
    # Apagar ficheiro local
    os.remove(f"./{local_filename}")
    
    return width, height

def parse_filename(filename):
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3:
        return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2:
        return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else:
        return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}

def process_files():
    all_files = get_file_list()
    if not all_files:
        print("Nenhum ficheiro encontrado no R2. A sair.")
        return

    output_data = {cat: [] for cat in CATEGORIES.values()}

    for path in all_files:
        if "desktop.ini" in path or "/_thumbnails/" in path or not path:
            continue

        try:
            category_name, filename = path.split('/', 1)
        except ValueError:
            continue

        if category_name in CATEGORIES:
            category_key = CATEGORIES[category_name]
            
            width, height = 0, 0
            # Só obtemos dimensões para imagens e vídeos
            if category_key in ["fotografias", "videos", "designs"]:
                 width, height = get_dimensions(path)

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
