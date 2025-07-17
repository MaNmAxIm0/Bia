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
DRIVE_DIR = Path("./portfolio_source") # Alterado de SOURCE_DIR para DRIVE_DIR para consistência
OUTPUT_DIR = Path("./processed_assets")
FAILED_DIR = Path("./failed_images") # Diretório para imagens que falham
WATERMARK_TEXT = "Portfólio da Bia"
FONT_FILE = Path("./scripts/Montserrat-Medium.ttf") # Assumindo que a fonte está em scripts/

# Configurações da Marca de Água de Texto
WATERMARK_OPACITY = 0.15
FONT_SIZE_RATIO = 0.05

# Configurações de Imagem
THUMBNAIL_SIZE = (400, 400)
IMAGE_QUALITY = 85
SUPPORTED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".avi"]

def load_manifest():
    """Carrega o manifesto de ficheiros existentes no R2."""
    # MANIFEST_FILE não está definido aqui, assumindo que é para o r2_manifest.json
    # que é gerado pelo generate_manifest.py
    manifest_path = Path("./r2_manifest.json") # Assumindo o nome do ficheiro gerado
    if not manifest_path.exists():
        print("AVISO: Ficheiro de manifesto não encontrado. A processar todos os ficheiros.")
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            return {item["Path"]: item for item in manifest_data}
    except (json.JSONDecodeError, TypeError):
        print("AVISO: Manifesto corrompido ou vazio. A processar todos os ficheiros.")
        return {}

def setup_directories():
    """Cria os diretórios de saída e de falhas se não existirem."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    FAILED_DIR.mkdir(exist_ok=True)

def open_image_safely(image_path: Path):
    """Abre uma imagem de forma segura, convertendo perfis de cor problemáticos."""
    try:
        img = Image.open(image_path)
        # Converte para RGB para garantir compatibilidade
        if img.mode == 'P': # Paleta
             img = img.convert('RGBA')
        if img.mode == 'CMYK':
            img = img.convert('RGB')
        return img
    except UnidentifiedImageError:
        return None
    except Exception as e:
        print(f"ERRO inesperado ao abrir {image_path.name}: {e}")
        return None

def apply_text_watermark(base_image: Image, text: str):
    """Aplica uma marca de água de texto na imagem."""
    # Converte para RGBA para suportar a camada de texto com transparência
    watermark_image = base_image.convert('RGBA')
    
    txt_layer = Image.new('RGBA', watermark_image.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(txt_layer)

    font_size = int(watermark_image.width * FONT_SIZE_RATIO)
    try:
        font = ImageFont.truetype(str(FONT_FILE), font_size)
    except IOError:
        print(f"AVISO: Fonte \'{FONT_FILE.name}\' não encontrada. A usar fonte padrão.")
        font = ImageFont.load_default(size=font_size)

    # ## CORREÇÃO ##
    # A forma correta de calcular a largura e altura do texto
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0] # Corrigido
    text_height = text_bbox[3] - text_bbox[1] # Corrigido
    
    margin = int(watermark_image.width * 0.05)
    # Posiciona no canto inferior direito
    position = (watermark_image.width - text_width - margin, watermark_image.height - text_height - margin)

    fill_color = (255, 255, 255, int(255 * WATERMARK_OPACITY))
    draw.text(position, text, font=font, fill=fill_color)

    # Combina a imagem original com a camada de texto
    return Image.alpha_composite(watermark_image, txt_layer).convert("RGB")

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
        
        # Converte de volta para RGB antes de salvar em formatos que não suportam alfa (como JPEG)
        final_image_rgb = final_image.convert('RGB')

        # Salva a imagem principal em WEBP ou JPEG
        if final_image.mode == 'RGBA': # Se a imagem original já tinha transparência
            final_image.save(output_path.with_suffix('.webp'), format='WEBP', quality=IMAGE_QUALITY)
        else:
            final_image_rgb.save(output_path.with_suffix('.jpg'), format='JPEG', quality=IMAGE_QUALITY, optimize=True, progressive=True)

        # Cria a thumbnail
        thumbnail_path = FAILED_DIR / relative_path.with_suffix('.jpg') # Alterado para usar FAILED_DIR
        thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
        
        thumbnail_image = final_image_rgb.copy()
        thumbnail_image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        thumbnail_image.save(thumbnail_path, format='JPEG', quality=80)

        return (str(relative_path), "SUCCESS")

    elif file_ext in VIDEO_EXTENSIONS or file_ext == '.pdf':
        # Usa shutil.copy2 para preservar metadados
        import shutil
        shutil.copy2(file_path, output_path)
        return (str(relative_path), "COPIED")
    else:
        return (str(relative_path), "IGNORED_TYPE")

def main():
    """Função principal que orquestra o processamento."""
    setup_directories()
    
    # ## CORREÇÃO ##
    # A linha `files_to_process =` estava incompleta. É necessário preenchê-la.
    # Assumindo que você quer listar todos os ficheiros de imagem no SOURCE_DIR.
    files_to_process = [p for p in DRIVE_DIR.rglob('*') if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS]

    if not files_to_process:
        print("Nenhum ficheiro de imagem encontrado para processar.")
        return

    print(f"Encontrados {len(files_to_process)} ficheiros de imagem para processar.")
    
    success_log = []
    failure_log = []

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_single_file, file_path, load_manifest()): file_path for file_path in files_to_process} # Passa o manifesto
        progress_bar = tqdm(as_completed(futures), total=len(files_to_process), desc="Processando Ativos", unit="file")

        for future in progress_bar:
            file_path = futures[future]
            try:
                relative_path, status = future.result()
                if status in ("SUCCESS", "COPIED", "SKIPPED"): # Adicionado SKIPPED para registar
                    success_log.append(f"{relative_path}: {status}")
                elif status.startswith("FAILURE") or status == "IGNORED_TYPE": # Adicionado IGNORED_TYPE
                    failure_log.append(f"{relative_path}: {status}")
            except Exception as e:
                failure_log.append(f"{file_path.relative_to(DRIVE_DIR)}: FAILURE: Exceção inesperada - {e}")

    print("\n--- Relatório de Processamento ---")
    print(f"Total de ficheiros processados com sucesso: {len(success_log)}")
    print(f"Total de falhas: {len(failure_log)}")

    with open(OUTPUT_DIR / "success.log", "w", encoding='utf-8') as f:
        f.write("\n".join(success_log))
    with open(OUTPUT_DIR / "failure.log", "w", encoding='utf-8') as f:
        f.write("\n".join(failure_log))
    
    if failure_log:
        print(f"\n{len(failure_log)} ficheiro(s) com falha foram movidos para o diretório \'{FAILED_DIR}\' e serão carregados como artefacto.")
        sys.exit(1) # Faz o workflow falhar se houver erros

    print("\nWorkflow concluído com sucesso.")

if __name__ == "__main__":
    main()
