import subprocess
import json
import urllib.parse

# --- CONFIGURAÇÃO PRINCIPAL ---
# Altere estes valores para corresponderem à sua configuração
RCLONE_REMOTE_NAME = "R2"
BUCKET_NAME = "bia-portfolio-assets"
PUBLIC_URL = "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev"

# Mapeia os nomes das pastas no R2 para as categorias no JSON
# Use os nomes exatos das suas pastas, com maiúsculas e acentos.
FOLDER_TO_CATEGORY_MAP = {
    "Fotografias": "fotografias",
    "Vídeos": "videos",
    "Designs": "designs",
    "Apresentações": "apresentacoes"
}
# --- FIM DA CONFIGURAÇÃO ---

def parse_filename(filename ):
    """
    Analisa o nome do ficheiro para extrair títulos de forma robusta.
    Formato esperado para multilingue: TituloPT_TituloEN_TituloES.extensao
    """
    name_part = filename.rsplit('.', 1)[0]
    titles_parts = name_part.split('_')
    
    # Se o nome do ficheiro tiver exatamente 3 partes separadas por '_', assume que são os títulos.
    if len(titles_parts) == 3:
        return {
            "pt": titles_parts[0].strip(),
            "en": titles_parts[1].strip(),
            "es": titles_parts[2].strip()
        }
    else:
        # Caso contrário, usa o nome completo (sem os '_') como título para todos os idiomas.
        clean_title = name_part.replace('_', ' ').strip()
        return {
            "pt": clean_title,
            "en": clean_title,
            "es": clean_title
        }

def main():
    """Função principal para gerar o data.json"""
    remote_path = f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}"
    command = ["rclone", "lsjson", remote_path, "--recursive"]

    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding="utf-8")
        files = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"Erro ao executar rclone ou ao analisar o JSON: {e}")
        return

    output_data = {
        "fotografias": [],
        "videos": [],
        "designs": [],
        "apresentacoes": []
    }

    # Lista as thumbnails disponíveis uma única vez para eficiência
    try:
        thumb_list_result = subprocess.run(["rclone", "lsf", f"{remote_path}/thumbs/"], capture_output=True, text=True, encoding="utf-8")
        available_thumbs = set(thumb_list_result.stdout.splitlines())
    except subprocess.CalledProcessError:
        available_thumbs = set()
        print("Aviso: Não foi possível listar as thumbnails. A pasta 'thumbs' pode não existir.")

    for file_info in files:
        path = file_info.get("Path", "")

        # Ignora ficheiros 'desktop.ini'
        if path.lower().endswith('desktop.ini'):
            continue

        # Ignora ficheiros na raiz do bucket (só processa ficheiros dentro de pastas)
        if "/" not in path:
            print(f"A ignorar ficheiro na raiz do bucket: {path}")
            continue

        folder_name = path.split('/')[0]
        category = FOLDER_TO_CATEGORY_MAP.get(folder_name)

        if not category:
            continue

        filename = file_info.get("Name", "")
        titles = parse_filename(filename)
        
        # Codifica o caminho para URLs seguros (lida com espaços, acentos, etc.)
        encoded_path = urllib.parse.quote(path)

        item_data = {
            "name": filename,
            "titles": titles,
            "url": f"{PUBLIC_URL}/{encoded_path}"
        }

        # Se for um vídeo, procura pela sua thumbnail
        if category == "videos":
            base_name = filename.rsplit('.', 1)[0]
            thumb_name = f"{base_name}.jpg"
            
            if thumb_name in available_thumbs:
                encoded_thumb_name = urllib.parse.quote(thumb_name)
                item_data["thumbnail_url"] = f"{PUBLIC_URL}/thumbs/{encoded_thumb_name}"
            else:
                # Fallback para uma imagem genérica se a thumbnail não for encontrada
                item_data["thumbnail_url"] = "https://manmaxim0.github.io/Bia/imagens/work_thumb_video.png" # URL absoluto para o fallback

        output_data[category].append(item_data )

    # Escreve o ficheiro JSON final
    try:
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print("Ficheiro data.json gerado com sucesso.")
    except IOError as e:
        print(f"Erro ao escrever o ficheiro data.json: {e}")

if __name__ == "__main__":
    main()
