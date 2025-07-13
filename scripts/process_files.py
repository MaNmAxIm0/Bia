import subprocess
import json
import os
from PIL import Image, ImageDraw, ImageFont, ExifTags

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
WATERMARK_TEXT = "© Beatriz Rodrigues"
# Certifique-se que o ficheiro da fonte está na mesma pasta que o script
FONT_PATH = os.path.join(os.path.dirname(__file__ ), 'Montserrat-Regular.ttf') 
WATERMARKED_DIR = "temp_watermarked" # Pasta temporária para imagens com marca de água

# Mapeia a orientação EXIF para a rotação necessária
EXIF_ORIENTATION_TAG = next((tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'), None)

def add_watermark(input_image_path, output_image_path):
    """Aplica uma marca de água de texto a uma imagem."""
    try:
        with Image.open(input_image_path).convert("RGBA") as base:
            # Cria um objeto para desenhar
            draw = ImageDraw.Draw(base)
            
            # Tenta carregar a fonte. O tamanho é ajustado dinamicamente.
            # O tamanho da fonte será 2.5% da largura da imagem, com um mínimo de 16px.
            font_size = max(16, int(base.width * 0.025))
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except IOError:
                print(f"AVISO: Ficheiro de fonte não encontrado em '{FONT_PATH}'. A usar fonte padrão.")
                font = ImageFont.load_default()

            # Calcula a posição do texto
            textwidth, textheight = draw.textsize(WATERMARK_TEXT, font)
            margin = 15
            x = base.width - textwidth - margin
            y = base.height - textheight - margin

            # Adiciona uma sombra subtil para legibilidade
            shadow_color = "black"
            draw.text((x + 1, y + 1), WATERMARK_TEXT, font=font, fill=shadow_color)

            # Adiciona o texto principal
            text_color = (255, 255, 255, 180) # Branco com 70% de opacidade
            draw.text((x, y), WATERMARK_TEXT, font=font, fill=text_color)

            base.save(output_image_path, "PNG") # Salva como PNG para manter a qualidade e transparência
        return True
    except Exception as e:
        print(f"ERRO: Falha ao aplicar marca de água em '{input_image_path}'. Erro: {e}")
        return False

def get_file_list():
    """Obtém a lista de todos os ficheiros do R2."""
    print("A obter a lista de todos os ficheiros do R2...")
    command = ["rclone", "lsf", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}", "--recursive", "--files-only"]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError as e:
        print(f"Erro ao obter a lista de ficheiros do R2: {e}\nStderr: {e.stderr}")
        return []

def get_dimensions(local_path, file_type):
    """Obtém as dimensões de um ficheiro local."""
    width, height = 0, 0
    if file_type in ['fotografias', 'designs']:
        try:
            with Image.open(local_path) as img:
                width, height = img.size
                if EXIF_ORIENTATION_TAG and hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif and EXIF_ORIENTATION_TAG in exif and exif[EXIF_ORIENTATION_TAG] in [5, 6, 7, 8]:
                        width, height = height, width
        except Exception as e:
            print(f"AVISO: Pillow não conseguiu processar a imagem '{local_path}'. Erro: {e}")
    elif file_type == 'videos':
        # Esta função não será usada para vídeos neste workflow, mas mantém-se por consistência
        pass
    return width, height

def parse_filename(filename):
    """Extrai títulos do nome do ficheiro."""
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 3:
        return {'pt': parts[0], 'en': parts[1], 'es': parts[2]}
    elif len(parts) == 2:
        return {'pt': parts[0], 'en': parts[1], 'es': parts[1]}
    else:
        return {'pt': name_without_ext, 'en': name_without_ext, 'es': name_without_ext}

def process_files():
    """Função principal do workflow."""
    all_files = get_file_list()
    if not all_files:
        print("Nenhum ficheiro encontrado no R2. A sair.")
        return

    # Cria a pasta temporária para as imagens com marca de água, se não existir
    if not os.path.exists(WATERMARKED_DIR):
        os.makedirs(WATERMARKED_DIR)

    output_data = {cat: [] for cat in CATEGORIES.values()}

    for path in all_files:
        if "desktop.ini" in path or "/_thumbnails/" in path or "/_watermarked/" in path or not path:
            continue

        try:
            category_name, filename = path.split('/', 1)
        except ValueError:
            continue

        if category_name in CATEGORIES:
            category_key = CATEGORIES[category_name]
            
            if category_key in ["fotografias", "designs"]:
                print(f"A processar imagem: {path}")
                local_original_path = f"./{filename}"
                
                # 1. Descarregar a imagem original
                try:
                    subprocess.run(["rclone", "copyto", f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/{path}", local_original_path], check=True, capture_output=True)
                except subprocess.CalledProcessError as e:
                    print(f"AVISO: Falha ao descarregar '{path}'. A ignorar. Erro: {e.stderr.decode()}")
                    continue

                # 2. Aplicar a marca de água
                base_name, _ = os.path.splitext(filename)
                watermarked_filename = f"{base_name}.png" # Sempre PNG
                local_watermarked_path = os.path.join(WATERMARKED_DIR, watermarked_filename)
                
                if add_watermark(local_original_path, local_watermarked_path):
                    # 3. Enviar a imagem com marca de água para uma nova pasta no R2
                    print(f"A enviar imagem com marca de água para R2: _watermarked/{watermarked_filename}")
                    subprocess.run(["rclone", "copyto", local_watermarked_path, f"{RCLONE_REMOTE_NAME}:{BUCKET_NAME}/_watermarked/{watermarked_filename}"], check=True)
                    
                    # 4. Obter dimensões e criar entrada no JSON
                    width, height = get_dimensions(local_original_path, category_key)
                    orientation = "horizontal" if width >= height else "vertical"
                    
                    file_data = {
                        "name": filename,
                        "titles": parse_filename(filename),
                        "url": f"{PUBLIC_URL}/_watermarked/{watermarked_filename.replace(' ', '%20')}", # URL aponta para a imagem com marca de água
                        "orientation": orientation
                    }
                    output_data[category_key].append(file_data)

                # Limpar ficheiros locais
                os.remove(local_original_path)
                if os.path.exists(local_watermarked_path):
                    os.remove(local_watermarked_path)

            elif category_key == "videos":
                # Lógica para vídeos permanece a mesma
                file_data = {
                    "name": filename,
                    "titles": parse_filename(filename),
                    "url": f"{PUBLIC_URL}/{path.replace(' ', '%20')}",
                    "orientation": "vertical", # Pode ser melhorado se necessário
                    "thumbnail_url": f"{PUBLIC_URL}/_thumbnails/{os.path.splitext(filename)[0]}.jpg".replace(' ', '%20')
                }
                output_data[category_key].append(file_data)
            
            # Adicionar aqui a lógica para apresentações se necessário

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print("Ficheiro data.json gerado com sucesso.")

if __name__ == "__main__":
    process_files()
