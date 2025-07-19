# main.py (Versão Final com Processamento Condicional)

import os
import subprocess
import json
import logging
from PIL import Image, ImageOps, ImageDraw, ImageFont
import shutil
from pathlib import Path
from tqdm import tqdm
import config

# --- Configuração do Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s')

# --- Funções de Comando e Utilitários ---

def run_command(command: list, operation_name: str) -> bool:
    """Executa um comando de terminal e regista o resultado."""
    logging.info(f"Iniciando: {operation_name}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"Sucesso: {operation_name} concluída.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"FALHA em '{operation_name}': {e.stderr.strip()}")
        return False

def get_media_orientation(file_path: Path) -> str:
    """Determina a orientação ('vertical' ou 'horizontal') de um ficheiro de imagem."""
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            return "vertical" if height > width else "horizontal"
    except Exception:
        return "horizontal"

# --- Funções de Processamento de Média ---

def apply_watermark(base_image: Image.Image) -> Image.Image:
    """Aplica uma marca de água de texto com sombra a uma imagem."""
    image = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(image)
    
    font_size = int(image.width * config.IMG_WATERMARK_FONT_RATIO)
    try:
        font = ImageFont.truetype(config.WATERMARK_FONT_PATH, font_size)
    except IOError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    margin = int(image.width * config.MARGIN_RATIO)
    x = image.width - text_width - margin
    y = image.height - text_height - margin

    shadow_offset = int(font_size * 0.05)
    draw.text((x + shadow_offset, y + shadow_offset), config.WATERMARK_TEXT, font=font, fill=(0, 0, 0, 100))
    draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=(*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY))
    
    return image.convert("RGB")

def process_image(input_path: Path, output_path: Path, apply_watermark_flag: bool = True):
    """
    Processa uma imagem: corrige orientação, redimensiona, comprime e, opcionalmente,
    aplica uma marca de água.
    """
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        
        if max(img.size) > 2048:
            img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        
        # --- LÓGICA CONDICIONAL DA MARCA DE ÁGUA ---
        if apply_watermark_flag:
            img_to_save = apply_watermark(img)
        else:
            img_to_save = img.convert("RGB") # Apenas converte para RGB se não houver marca de água
        
        img_to_save.save(output_path, "JPEG", quality=75, optimize=True, progressive=True)

def process_video(input_path: Path, output_path: Path):
    """Aplica marca de água a um vídeo e gera o seu thumbnail (sem marca de água)."""
    # Aplica marca de água ao vídeo principal
    font_path_ffmpeg = str(config.WATERMARK_FONT_PATH).replace("\\", "/").replace(":", "\\\\:")
    watermark_filter = (
        f"drawtext=fontfile='{font_path_ffmpeg}':text='{config.WATERMARK_TEXT}':"
        f"fontsize=h*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=black@0.5:"
        f"x=(w-text_w-w*{config.MARGIN_RATIO})+2:y=(h-text_h-h*{config.MARGIN_RATIO})+2,"
        f"drawtext=fontfile='{font_path_ffmpeg}':text='{config.WATERMARK_TEXT}':"
        f"fontsize=h*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=white@0.8:"
        f"x=w-text_w-w*{config.MARGIN_RATIO}:y=h-text_h-h*{config.MARGIN_RATIO}"
    )
    video_cmd = [
        "ffmpeg", "-i", str(input_path), "-vf", watermark_filter,
        "-codec:v", "libx264", "-preset", "medium", "-crf", "23",
        "-codec:a", "copy", "-y", str(output_path)
    ]
    if not run_command(video_cmd, f"Processar vídeo {input_path.name}"):
        return

    # Gera thumbnail a partir do VÍDEO ORIGINAL (sem marca de água)
    thumb_output_path = config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR / f"{output_path.stem}_thumb.jpg"
    thumb_cmd = ["ffmpeg", "-i", str(input_path), "-ss", config.THUMBNAIL_TIMESTAMP, "-vframes", "1", "-q:v", "2", "-y", str(thumb_output_path)]
    run_command(thumb_cmd, f"Gerar thumbnail para {output_path.name}")

def process_google_drive_link(link_file: Path, data_dict: dict):
    """Extrai o URL de um ficheiro de link do Google e adiciona aos dados."""
    try:
        with open(link_file, 'r', encoding='utf-8') as f:
            link_data = json.load(f)
        url = link_data.get("url")
        if not url: return

        if "docs.google.com/presentation" in url:
            url = url.replace("/edit", "/embed?start=false&loop=false&delayms=3000")
        
        filename = link_file.stem
        data_dict[filename] = {
            "titles": {"pt": filename, "en": filename, "es": filename},
            "orientation": "horizontal", "url": url, "is_external": True
        }
        logging.info(f"Adicionada apresentação externa: '{filename}'")
    except Exception as e:
        logging.error(f"FALHA ao processar ficheiro de link '{link_file.name}': {e}")

# --- Fluxo Principal ---

def main():
    logging.info("--- INÍCIO DO WORKFLOW DE PROCESSAMENTO DE ATIVOS ---")

    # 1. Preparar diretórios
    for dir_path in [config.LOCAL_ASSETS_DIR, config.PROCESSED_ASSETS_DIR]:
        if dir_path.exists(): shutil.rmtree(dir_path)
        dir_path.mkdir(exist_ok=True)
    (config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR).mkdir(exist_ok=True)

    # 2. Copiar todos os ficheiros do Google Drive
    if not run_command(["rclone", "copy", config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "--progress"], "Copiar ativos do Google Drive"):
        logging.critical("Cópia do Drive falhou. Workflow abortado."); return

    # 3. Processar ficheiros e construir o dicionário de dados
    all_files = list(config.LOCAL_ASSETS_DIR.rglob("*.*"))
    final_data = {}
    with tqdm(all_files, desc="Processando Ficheiros") as pbar:
        for input_path in pbar:
            relative_path = input_path.relative_to(config.LOCAL_ASSETS_DIR)
            pbar.set_description(f"Processando {relative_path}")
            
            output_path = config.PROCESSED_ASSETS_DIR / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ext = input_path.suffix.lower()

            # --- LÓGICA DE PROCESSAMENTO CONDICIONAL ---
            if ext in ['.gdoc', '.gsheet', '.gslides']:
                process_google_drive_link(input_path, final_data)
                continue
            
            elif ext in config.PDF_EXTENSIONS:
                shutil.copy2(input_path, output_path)
            
            elif ext in config.IMAGE_EXTENSIONS:
                # Verifica se a imagem está numa pasta que não deve ter marca de água
                parent_folder_name = relative_path.parts[0]
                should_apply_watermark = parent_folder_name not in ["Melhores", "Capas"]
                process_image(input_path, output_path, apply_watermark_flag=should_apply_watermark)
            
            elif ext in config.VIDEO_EXTENSIONS:
                process_video(input_path, output_path)
            
            else:
                logging.warning(f"Extensão desconhecida '{ext}' ignorada para {input_path.name}")
                continue

            # Adicionar metadados ao dicionário se o ficheiro foi processado/copiado
            if output_path.exists():
                filename = output_path.name
                stem = output_path.stem
                titles = stem.split('_')
                title_pt, title_en, title_es = (titles[0] if titles else stem, titles[1] if len(titles) > 1 else titles[0], titles[2] if len(titles) > 2 else titles[0])

                entry = {
                    "titles": {"pt": title_pt, "en": title_en, "es": title_es},
                    "orientation": get_media_orientation(output_path),
                    "url": f"{config.R2_PUBLIC_URL}/{relative_path.as_posix()}"
                }
                if ext in config.VIDEO_EXTENSIONS:
                    entry["thumbnail_url"] = f"{config.R2_PUBLIC_URL}/{config.THUMBNAIL_DIR.name}/{stem}_thumb.jpg"
                
                final_data[filename] = entry

    # 4. Gerar o ficheiro data.json
    with open(config.JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Ficheiro '{config.JSON_OUTPUT_FILE.name}' gerado com sucesso.")

    # 5. Sincronizar tudo para o R2
    run_command(["rclone", "sync", str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH, "--progress", "-v"], "Sincronizar para R2")

    logging.info("--- WORKFLOW CONCLUÍDO ---")

if __name__ == "__main__":
    main()
