import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageFile, UnidentifiedImageError, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Permite que o Pillow tente carregar imagens mesmo que estejam truncadas
ImageFile.LOAD_TRUNCATED_IMAGES = True

# --- Constantes de Configuração ---
DRIVE_DIR = Path("./local_drive")
OUTPUT_DIR = Path("./output")
THUMBNAILS_DIR = OUTPUT_DIR / "Thumbnails"
MANIFEST_FILE = Path("./r2_manifest.json")
FONT_FILE = Path("./scripts/Montserrat-Medium.ttf")

# Configurações da Marca de Água de Texto
WATERMARK_TEXT = "Portfólio da Bia"
WATERMARK_OPACITY = 0.15
FONT_SIZE_RATIO = 0.05

# Configurações de Imagem
THUMBNAIL_SIZE = (400, 400)
IMAGE_QUALITY = 85
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi']

def load_manifest():
    """Carrega o manifesto de ficheiros existentes no R2."""
    if not MANIFEST_FILE.exists():
        print("AVISO: Ficheiro de manifesto não encontrado. A processar todos os ficheiros.")
        return {}
    with open(MANIFEST_FILE, 'r') as f:
        manifest_data = json.load(f)
        return {item['Path']: item for item in manifest_data}

def open_image_safely(image_path: Path):
    """Abre uma imagem de forma segura, convertendo perfis de cor problemáticos."""
    try:
        img = Image.open(image_path)
        if img.mode in ('CMYK', 'P'):
            img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
        return img
    except UnidentifiedImageError:
        return None
    except Exception as e:
        print(f"ERRO inesperado ao abrir {image_path.name}: {e}")
        return None

def apply_text_watermark(base_image: Image, text: str):
    """Aplica uma marca de água de texto na imagem."""
    if base_image.mode!= 'RGBA':
        base_image = base_image.convert('RGBA')

    txt_layer = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    font_size = int(base_image.width * FONT_SIZE_RATIO)
    try:
        font = ImageFont.truetype(str(FONT_FILE), font_size)
    except IOError:
        print(f"AVISO: Fonte '{FONT_FILE.name}' não encontrada. A usar fonte padrão.")
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[1] - text_bbox
    text_height = text_bbox[2] - text_bbox[3]
    margin = int(base_image.width * 0.05)
    position = (base_image.width - text_width - margin, base_image.height - text_height - margin)

    fill_color = (255, 255, 255, int(255 * WATERMARK_OPACITY))
    draw.text(position, text, font=font, fill=fill_color)

    return Image.alpha_composite(base_image, txt_layer)

def process_single_file(file_path: Path, r2_manifest: dict):
    """Processa um único ficheiro: verifica, aplica marca de água e cria thumbnail."""
    relative_path = file_path.relative_to(DRIVE_DIR)
    output_path = OUTPUT_DIR / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    local_size = file_path.stat().st_size
    remote_file_info = r2_manifest.get(str(relative_path))

    if remote_file_info and local_size == remote_file_info.get('Size'):
        return (str(relative_path), "SKIPPED")

    file_ext = file_path.suffix.lower()

    if file_ext in SUPPORTED_IMAGE_EXTENSIONS:
        base_image = open_image_safely(file_path)
        if not base_image:
            return (str(relative_path), "FAILURE: Formato de imagem não identificado")

        final_image = apply_text_watermark(base_image, WATERMARK_TEXT)
        
        if final_image.mode == 'RGBA':
            final_image.save(output_path, format='WEBP', quality=IMAGE_QUALITY, method=6)
        else:
            final_image.save(output_path, format='JPEG', quality=IMAGE_QUALITY, optimize=True, progressive=True)

        thumbnail_path = THUMBNAILS_DIR / relative_path
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        final_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        final_image.save(thumbnail_path, format='JPEG', quality=80)

        return (str(relative_path), "SUCCESS")

    elif file_ext in VIDEO_EXTENSIONS or file_ext == '.pdf':
        os.link(file_path, output_path)
        return (str(relative_path), "COPIED")
    else:
        return (str(relative_path), "IGNORED_TYPE")

def main():
    """Função principal que orquestra todo o processo."""
    print("--- Iniciando o Processamento de Ativos com Marca de Água de Texto ---")

    if not DRIVE_DIR.is_dir():
        print(f"ERRO: Diretório de origem '{DRIVE_DIR}' não encontrado.")
        sys.exit(1)
    if not FONT_FILE.exists():
        print(f"AVISO: Ficheiro da fonte '{FONT_FILE.name}' não encontrado. A usar fonte padrão.")

    OUTPUT_DIR.mkdir(exist_ok=True)
    THUMBNAILS_DIR.mkdir(exist_ok=True)

    r2_manifest = load_manifest()
    # Inicializa as variáveis com as suas expressões corretas.
    all_files = [p for p in DRIVE_DIR.rglob('*') if p.is_file()]
    success_log = []
    failure_log = []

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_single_file, file_path, r2_manifest): file_path for file_path in all_files}
        progress_bar = tqdm(as_completed(futures), total=len(all_files), desc="Processando Ativos", unit="file")

        for future in progress_bar:
            file_path = futures[future]
            try:
                relative_path, status = future.result()
                if status in ("SUCCESS", "COPIED"):
                    success_log.append(f"{relative_path}: {status}")
                elif status.startswith("FAILURE"):
                    failure_log.append(f"{relative_path}: {status}")
            except Exception as e:
                failure_log.append(f"{file_path.relative_to(DRIVE_DIR)}: FAILURE: Exceção inesperada - {e}")

    print("\n--- Relatório de Processamento ---")
    print(f"Total de ficheiros processados com sucesso: {len(success_log)}")
    print(f"Total de falhas: {len(failure_log)}")

    with open(OUTPUT_DIR / "success.log", "w") as f:
        f.write("\n".join(success_log))
    with open(OUTPUT_DIR / "failure.log", "w") as f:
        f.write("\n".join(failure_log))
    
    if failure_log:
        print("\n--- Detalhes das Falhas ---")
        for entry in failure_log:
            print(entry)
        print("\nWorkflow terminado com erros.")
        sys.exit(1)

    print("\nWorkflow concluído com sucesso.")

if __name__ == "__main__":
    main()