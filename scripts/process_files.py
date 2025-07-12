import subprocess
import json
import os
from PIL import Image, ExifTags

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

# Mapeia a orientação EXIF para a rotação necessária
EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items( ) if name == 'Orientation'), None)

def get_file_list():
    """Obtém a lista de todos os ficheiros do R2."""
    print("A obter a lista de todos os ficheiros do R2...")
    command = ["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        print("Lista de ficheiros obtida com sucesso.")
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}\nStderr: {e.stderr}")
        return []

def get_dimensions(remote_path, file_type):
    """Obtém as dimensões de um ficheiro, usando Pillow para imagens e ffprobe para vídeos."""
    local_filename = os.path.basename(remote_path)
    print(f"A obter dimensões para: {remote_path} (Tipo: {file_type})")
    
    # Descarregar o ficheiro
    try:
        subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{remote_path}", f"./{local_filename}"], check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"AVISO: Falha ao descarregar '{remote_path}'. A ignorar. Erro: {e.stderr.decode()}")
        return 0, 0

    width, height = 0, 0
    
    if file_type in ['fotografias', 'designs']:
        # --- LÓGICA PARA IMAGENS USANDO PILLOW ---
        try:
            with Image.open(f"./{local_filename}") as img:
                width, height = img.size
                print(f"Dimensões físicas encontradas: {width}x{height}")
                
                # Verifica os metadados EXIF para rotação
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif and EXIF_ORIENTATION_TAG in exif:
                        orientation = exif[EXIF_ORIENTATION_TAG]
                        # Se a orientação for 5, 6, 7 ou 8, as dimensões devem ser trocadas
                        if orientation in [5, 6, 7, 8]:
                            print(f"Orientação EXIF encontrada: {orientation}. A trocar dimensões.")
                            width, height = height, width
                print(f"Dimensões finais após EXIF: {width}x{height}")
        except Exception as e:
            print(f"AVISO: Pillow não conseguiu processar a imagem '{local_filename}'. Erro: {e}")

    elif file_type == 'videos':
        # --- LÓGICA PARA VÍDEOS USANDO FFPROBE ---
        try:
            command = [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "json", f"./{local_filename}"
            ]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            dims = json.loads(result.stdout)["streams"][0]
            width, height = int(dims.get("width", 0)), int(dims.get("height", 0))
            print(f"Dimensões do vídeo encontradas: {width}x{height}")
        except Exception as e:
            print(f"AVISO: ffprobe não conseguiu obter dimensões para o vídeo '{local_filename}'. Erro: {e}")

    # Apagar ficheiro local
    os.remove(f"./{local_filename}")
    
    return width, height

def parse_filename(filename):
    # ... (esta função permanece igual)
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
            if category_key in ["fotografias", "videos", "designs"]:
                 width, height = get_dimensions(path, category_key)

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
