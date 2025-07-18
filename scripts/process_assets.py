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
SOURCE_DIR = Path("./portfolio_source")
OUTPUT_DIR = Path("./processed_assets")
FAILED_DIR = Path("./failed_images")
MANIFEST_FILE = Path("./r2_manifest.json")
FONT_FILE = Path("./scripts/Montserrat-Medium.ttf")

# Configurações da Marca de Água de Texto
WATERMARK_TEXT = "Portfólio da Bia"
WATERMARK_OPACITY = 1.0
FONT_SIZE_RATIO = 0.05

# Configurações de Imagem
THUMBNAIL_SIZE = (400, 400)
IMAGE_QUALITY = 85
SUPPORTED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi']

def setup_directories():
    """Cria os diretórios de saída e de falhas se não existirem."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    FAILED_DIR.mkdir(exist_ok=True)

def load_manifest():
    """Carrega o manifesto de ficheiros existentes no R2."""
    if not MANIFEST_FILE.exists():
        print(f"AVISO: Ficheiro de manifesto '{MANIFEST_FILE.name}' não encontrado. A processar todos os ficheiros.")
        return {}
    try:
        with open(MANIFEST_FILE, 'r') as f:
            manifest_data = json.load(f)
            return {item['Path']: item for item in manifest_data}
    except (json.JSONDecodeError, TypeError):
        print(f"AVISO: O ficheiro de manifesto '{MANIFEST_FILE.name}' não é um JSON válido. Será ignorado.")
        return {}

# --- FUNÇÃO ADICIONADA ---
def open_image_safely(file_path: Path):
    """Abre uma imagem de forma segura, retornando None se falhar."""
    try:
        img = Image.open(file_path)
        img.load()  # Força a leitura dos dados da imagem para detetar corrupção
        return img
    except (IOError, UnidentifiedImageError):
        return None

def apply_text_watermark(base_image: Image, text: str):
    """Aplica uma marca de água de texto na imagem."""
    if base_image.mode != 'RGBA':
        base_image = base_image.convert('RGBA')

    txt_layer = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    font_size = int(base_image.width * FONT_SIZE_RATIO)
    try:
        font = ImageFont.truetype(str(FONT_FILE), font_size)
    except IOError:
        print(f"AVISO: Fonte '{FONT_FILE.name}' não encontrada. A usar fonte padrão.")
        font = ImageFont.load_default()

    # Correção no cálculo da bounding box do texto
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    margin = int(base_image.width * 0.05)
    position = (base_image.width - text_width - margin, base_image.height - text_height - margin)

    fill_color = (255, 255, 255, int(255 * WATERMARK_OPACITY))
    draw.text(position, text, font=font, fill=fill_color)

    return Image.alpha_composite(base_image, txt_layer)

def process_single_file(file_path: Path, r2_manifest: dict):
    """Processa um único ficheiro: verifica, aplica marca de água e cria thumbnail."""
    relative_path = file_path.relative_to(SOURCE_DIR)
    output_path = OUTPUT_DIR / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    local_size = file_path.stat().st_size
    remote_file_info = r2_manifest.get(str(relative_path))

    if remote_file_info and local_size == remote_file_info.get('Size'):
        return (str(relative_path), "SKIPPED", None)

    try:
        file_ext = file_path.suffix.lower()

        if file_ext in SUPPORTED_IMAGE_EXTENSIONS:
            base_image = open_image_safely(file_path)
            if not base_image:
                raise UnidentifiedImageError("Formato de imagem não identificado ou ficheiro corrompido")

            final_image_rgba = apply_text_watermark(base_image, WATERMARK_TEXT)
            
            final_image_rgb = final_image_rgba.convert("RGB")

            final_image_rgb.save(output_path, format='JPEG', quality=IMAGE_QUALITY, optimize=True, progressive=True)

            thumbnail_path = OUTPUT_DIR / "Thumbnails" / relative_path
            thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
            thumbnail_image = final_image_rgb.copy()
            thumbnail_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            thumbnail_image.save(thumbnail_path, format='JPEG', quality=80)

            return (str(relative_path), "SUCCESS", None)

        elif file_ext in VIDEO_EXTENSIONS or file_ext == '.pdf':
            # Em vez de os.link, usamos os.symlink para compatibilidade ou shutil.copy2 para uma cópia real
            # shutil.copy2(file_path, output_path) # Descomente se preferir copiar
            if output_path.exists():
                output_path.unlink()
            os.link(file_path, output_path) # Hard link é mais eficiente se estiver no mesmo sistema de ficheiros
            return (str(relative_path), "COPIED", None)
        else:
            return (str(relative_path), "IGNORED_TYPE", None)

    except Exception as e:
        return (str(relative_path), "FAILURE", str(e))

def main():
    """Função principal que orquestra todo o processo."""
    setup_directories()
    print("--- Iniciando o Processamento de Ativos ---")

    r2_manifest = load_manifest()
    
    # --- CORREÇÃO ---
    # Inicializa as variáveis com os valores corretos
    all_files = [p for p in SOURCE_DIR.rglob('*') if p.is_file()]
    success_log = []
    failure_log = []
    skipped_count = 0

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_single_file, file_path, r2_manifest): file_path for file_path in all_files}
        progress_bar = tqdm(as_completed(futures), total=len(all_files), desc="Processando Ativos", unit="file")

        for future in progress_bar:
            try:
                relative_path, status, error_msg = future.result()
                if status == "SUCCESS" or status == "COPIED":
                    success_log.append(f"{relative_path}: {status}")
                elif status == "SKIPPED":
                    skipped_count += 1
                else: # FAILURE ou IGNORED_TYPE
                    error_details = f"{relative_path}: {status}"
                    if error_msg:
                        error_details += f" (Detalhe: {error_msg})"
                    failure_log.append(error_details)
                    
                    original_failed_path = SOURCE_DIR / Path(relative_path)
                    if original_failed_path.exists():
                        # Garante que o destino não existe antes de mover
                        failed_dest = FAILED_DIR / original_failed_path.name
                        if failed_dest.exists():
                            os.remove(failed_dest)
                        os.rename(original_failed_path, failed_dest)
            except Exception as exc:
                # Captura exceções inesperadas do próprio future
                file_path = futures[future]
                failure_log.append(f"{file_path.relative_to(SOURCE_DIR)}: FATAL_ERROR ({exc})")


    print("\n--- Processamento Concluído ---")
    print(f"Total de ficheiros processados com sucesso: {len(success_log)}")
    print(f"Total de ficheiros ignorados (inalterados): {skipped_count}")
    print(f"Total de falhas: {len(failure_log)}")
    
    with open(OUTPUT_DIR / "success.log", "w") as f:
        f.write("\n".join(success_log))
    
    if failure_log:
        print("\nVerifique o artefacto 'failed-images' para os ficheiros com falha.")
        with open(OUTPUT_DIR / "failure.log", "w") as f:
            f.write("\n".join(failure_log))

if __name__ == "__main__":
    main()
