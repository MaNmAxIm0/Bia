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
# URL de uma imagem de fallback caso a geração da thumbnail falhe
FALLBACK_THUMBNAIL_URL = "https://manmaxim0.github.io/Bia/imagens/work_thumb_video.png"

def get_all_files_with_metadata( ):
    """
    *** A NOVA ABORDAGEM ***
    Executa 'rclone lsjson' com a flag '--metadata' uma única vez para obter
    todos os ficheiros e os seus metadados (incluindo dimensões) numa só chamada de rede.
    Isto é muito mais rápido do que fazer um pedido para cada ficheiro.
    """
    print("A obter a lista de todos os ficheiros e metadados do R2...")
    command = [
        "rclone", "lsjson",
        f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}",
        "--metadata",         # Pede os metadados (inclui altura e largura)
        "--recursive",        # Garante que lemos dentro de todas as subpastas
        "--no-mimetype"       # Não precisamos do mimetype, poupa processamento
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
    """
    Extrai os títulos multilingues do nome do ficheiro.
    Exemplo: "Título PT_Título EN_Título ES.jpg"
    """
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    
    # Garante que temos sempre 3 partes, repetindo a primeira se necessário
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

    output_data = {
        "fotografias": [],
        "videos": [],
        "designs": [],
        "apresentacoes": []
    }

    for item in all_files:
        path = item.get("Path", "")
        
        # Ignora ficheiros indesejados
        if "desktop.ini" in path or not path:
            continue

        # Determina a categoria e o nome do ficheiro
        try:
            category_name, filename = path.split('/', 1)
        except ValueError:
            continue # Ignora ficheiros na raiz do bucket

        if category_name in CATEGORIES:
            category_key = CATEGORIES[category_name]
            
            # Obtém as dimensões dos metadados (muito mais rápido)
            width = int(item.get("Mdi", {}).get("width", 0))
            height = int(item.get("Mdi", {}).get("height", 0))

            orientation = "horizontal" if width >= height else "vertical"
            if width == 0 or height == 0:
                orientation = "square" # Fallback para ficheiros sem dimensões (PDFs, etc.)

            file_data = {
                "name": filename,
                "titles": parse_filename(filename),
                "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}",
                "orientation": orientation
            }

            # Adiciona URL da thumbnail apenas para vídeos
            if category_key == "videos":
                thumb_filename = os.path.splitext(filename)[0] + ".jpg"
                file_data["thumbnail_url"] = f"{PUBLIC_URL}/_thumbnails/{thumb_filename.replace(' ', '%20')}"

            output_data[category_key].append(file_data)

    # Escreve o ficheiro data.json final
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    process_files()
