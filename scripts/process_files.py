import subprocess
import json
import os
import re

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

def get_all_files( ):
    """Obtém a lista de todos os ficheiros do R2 de forma eficiente."""
    print("A obter a lista de todos os ficheiros do R2...")
    command = [
        "rclone", "lsjson",
        f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}",
        "--recursive",
        "--no-mimetype"
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("Lista de ficheiros obtida com sucesso.")
        return json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}")
        if hasattr(e, 'stderr'):
            print(f"Stderr: {e.stderr}")
        return []

def get_dimensions(file_path_on_remote):
    """
    Obtém as dimensões de um único ficheiro (imagem ou vídeo) usando ffprobe.
    O rclone cat transmite o ficheiro para o ffprobe sem o guardar em disco.
    """
    print(f"A obter dimensões para: {file_path_on_remote}")
    ffprobe_command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        "-" # O hífen indica que a entrada vem do stdin
    ]
    rclone_command = ["rclone", "cat", f"{RCLONE_REMOTE_NAME}:{file_path_on_remote}"]
    
    try:
        # Executa o rclone e envia a sua saída (o ficheiro) para o stdin do ffprobe
        rclone_process = subprocess.Popen(rclone_command, stdout=subprocess.PIPE)
        ffprobe_process = subprocess.run(ffprobe_command, stdin=rclone_process.stdout, capture_output=True, text=True, check=True)
        
        # Garante que o processo rclone terminou
        rclone_process.wait()

        dimensions_data = json.loads(ffprobe_process.stdout)
        width = dimensions_data["streams"][0].get("width", 0)
        height = dimensions_data["streams"][0].get("height", 0)
        print(f"Dimensões encontradas: {width}x{height}")
        return width, height
    except Exception as e:
        print(f"AVISO: Não foi possível obter dimensões para '{file_path_on_remote}'. Erro: {e}")
        return 0, 0

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
    all_files = get_all_files()
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
            
            width, height = get_dimensions(f"{BUCKET_NAME}/{path}")

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
