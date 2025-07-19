# main.py (Versão Final com Sincronização Incremental)

import os
import subprocess
import json
import logging
from PIL import Image, ImageOps, ImageDraw, ImageFont
import shutil
from pathlib import Path
from tqdm import tqdm
import config
from datetime import datetime
import pytz

# --- CONFIGURAÇÃO DE LOGGING COM FUSO HORÁRIO DE LISBOA ---
def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    lisbon_tz = pytz.timezone('Europe/Lisbon')
    logging.Formatter.converter = lambda *args: datetime.now(lisbon_tz).timetuple()
    handler = logging.StreamHandler()
    handler.setFormatter(log_formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

# --- Funções de Comando e Utilitários ---
def run_command(command: list, operation_name: str) -> bool:
    logging.info(f"Iniciando: {operation_name}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', timeout=900) # Timeout de 15 mins
        logging.info(f"Sucesso: {operation_name} concluída.")
        return True
    except subprocess.TimeoutExpired:
        logging.error(f"FALHA DE TIMEOUT em '{operation_name}'.")
        return False
    except subprocess.CalledProcessError as e:
        logging.error(f"FALHA em '{operation_name}': {e.stderr.strip()}")
        return False

def get_media_orientation(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in config.IMAGE_EXTENSIONS:
        try:
            with Image.open(file_path) as img:
                return "vertical" if img.height > img.width else "horizontal"
        except Exception: return "horizontal"
    elif ext in config.VIDEO_EXTENSIONS:
        try:
            command = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(file_path)]
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split('x'))
            return "vertical" if height > width else "horizontal"
        except Exception: return "horizontal"
    return "horizontal"

# --- Funções de Processamento de Média ---
def apply_watermark(base_image: Image.Image) -> Image.Image:
    image = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(image)
    font_size = int(max(image.size) * config.IMG_WATERMARK_FONT_RATIO)
    try:
        font = ImageFont.truetype(str(config.WATERMARK_FONT_PATH), font_size)
    except IOError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = int(max(image.size) * config.MARGIN_RATIO)
    x = image.width - text_width - margin
    y = image.height - text_height - margin
    shadow_offset = int(font_size * 0.05)
    draw.text((x + shadow_offset, y + shadow_offset), config.WATERMARK_TEXT, font=font, fill=(0, 0, 0, 100))
    draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=(*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY))
    return image.convert("RGB")

def process_image(input_path: Path, output_path: Path, apply_watermark_flag: bool = True):
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if max(img.size) > 2048:
            img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        img_to_save = apply_watermark(img) if apply_watermark_flag else img.convert("RGB")
        img_to_save.save(output_path, "JPEG", quality=65, optimize=True, progressive=True)

def process_video(input_path: Path, output_path: Path):
    font_path_ffmpeg = str(config.WATERMARK_FONT_PATH).replace("\\", "/").replace(":", "\\\\:")
    watermark_filter = (f"drawtext=fontfile='{font_path_ffmpeg}':text='{config.WATERMARK_TEXT}':fontsize=min(w,h)*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=black@0.5:x=(w-text_w-(min(w,h)*{config.MARGIN_RATIO}))+2:y=(h-text_h-(min(w,h)*{config.MARGIN_RATIO}))+2,"
                        f"drawtext=fontfile='{font_path_ffmpeg}':text='{config.WATERMARK_TEXT}':fontsize=min(w,h)*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=white@0.8:x=w-text_w-(min(w,h)*{config.MARGIN_RATIO}):y=h-text_h-(min(w,h)*{config.MARGIN_RATIO})")
    video_cmd = ["ffmpeg", "-i", str(input_path), "-vf", f"scale=-2:1080,{watermark_filter}", "-codec:v", "libx264", "-preset", "medium", "-crf", "28", "-codec:a", "aac", "-b:a", "128k", "-y", str(output_path)]
    if not run_command(video_cmd, f"Processar vídeo {input_path.name}"): return False
    try:
        duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(input_path)]
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout)
        thumbnail_timestamp = max(1.0, duration * 0.15)
        thumb_output_path = config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR / f"{output_path.stem}_thumb.jpg"
        thumb_cmd = ["ffmpeg", "-i", str(input_path), "-ss", str(thumbnail_timestamp), "-vframes", "1", "-q:v", "2", "-y", str(thumb_output_path)]
        run_command(thumb_cmd, f"Gerar thumbnail inteligente para {output_path.name}")
    except Exception as e:
        logging.error(f"FALHA ao gerar thumbnail inteligente para {input_path.name}: {e}")
        return False
    return True

def process_google_drive_link(link_file: Path, data_dict: dict):
    try:
        with open(link_file, 'r', encoding='utf-8') as f:
            link_data = json.load(f)
        url = link_data.get("url")
        if not url: return
        if "docs.google.com/presentation" in url:
            url = url.replace("/edit", "/embed?start=false&loop=false&delayms=3000")
        filename = link_file.stem
        data_dict[filename] = {"titles": {"pt": filename, "en": filename, "es": filename}, "orientation": "horizontal", "url": url, "is_external": True}
        logging.info(f"Adicionada APRESENTAÇÃO EXTERNA (link): '{filename}'")
    except Exception as e:
        logging.error(f"FALHA ao processar ficheiro de link '{link_file.name}': {e}")

# --- Fluxo Principal ---
def main():
    setup_logging()
    logging.info("--- INÍCIO DO WORKFLOW DE PROCESSAMENTO INCREMENTAL ---")

    # 1. Limpa apenas a pasta de processamento final. A pasta local será gerida pelo rclone.
    if config.PROCESSED_ASSETS_DIR.exists():
        shutil.rmtree(config.PROCESSED_ASSETS_DIR)
    config.PROCESSED_ASSETS_DIR.mkdir(exist_ok=True)
    (config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR).mkdir(exist_ok=True)
    config.LOCAL_ASSETS_DIR.mkdir(exist_ok=True)

    # 2. SINCRONIZA o Drive para a pasta local. Apenas ficheiros novos/alterados serão transferidos.
    #    Isto é a chave para a otimização de tempo.
    sync_from_drive_cmd = ["rclone", "sync", config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "--progress", "-v"]
    if not run_command(sync_from_drive_cmd, "Sincronizar ativos do Google Drive para local"):
        logging.critical("Sincronização do Drive falhou. Workflow abortado."); return

    # 3. Processa APENAS os ficheiros que foram sincronizados para a pasta local
    all_files = list(config.LOCAL_ASSETS_DIR.rglob("*.*"))
    final_data = {}
    if not all_files:
        logging.info("Nenhum ficheiro novo ou alterado para processar.")
    
    with tqdm(all_files, desc="Processando Ficheiros") as pbar:
        for input_path in pbar:
            relative_path = input_path.relative_to(config.LOCAL_ASSETS_DIR)
            pbar.set_description(f"Processando {relative_path}")
            output_path = config.PROCESSED_ASSETS_DIR / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ext = input_path.suffix.lower()

            # Lógica de processamento condicional...
            if ext in ['.gdoc', '.gsheet', '.gslides']:
                process_google_drive_link(input_path, final_data)
                continue
            elif ext in config.PDF_EXTENSIONS:
                shutil.copy2(input_path, output_path)
            elif ext in config.IMAGE_EXTENSIONS:
                parent_folder_name = relative_path.parts[0] if len(relative_path.parts) > 1 else ""
                should_apply_watermark = parent_folder_name not in ["Melhores", "Capas"]
                process_image(input_path, output_path, apply_watermark_flag=should_apply_watermark)
            elif ext in config.VIDEO_EXTENSIONS:
                if not process_video(input_path, output_path): continue
            else:
                logging.warning(f"Extensão desconhecida '{ext}' ignorada para {input_path.name}")
                continue
            
            # Adicionar metadados
            if output_path.exists():
                filename, stem = output_path.name, output_path.stem
                titles = stem.split('_')
                title_pt, title_en, title_es = (titles[0] if titles else stem, titles[1] if len(titles) > 1 else titles[0], titles[2] if len(titles) > 2 else titles[0])
                entry = {"titles": {"pt": title_pt, "en": title_en, "es": title_es}, "orientation": get_media_orientation(output_path), "url": f"{config.R2_PUBLIC_URL}/{relative_path.as_posix()}"}
                if ext in config.VIDEO_EXTENSIONS:
                    entry["thumbnail_url"] = f"{config.R2_PUBLIC_URL}/{config.THUMBNAIL_DIR.name}/{stem}_thumb.jpg"
                final_data[filename] = entry

    # 4. Gerar o ficheiro data.json completo (esta parte precisa de ser inteligente)
    # Primeiro, carrega os dados existentes do R2 (se existirem)
    try:
        if os.path.exists(config.JSON_OUTPUT_FILE):
            with open(config.JSON_OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        else:
            existing_data = {}
    except (json.JSONDecodeError, FileNotFoundError):
        existing_data = {}

    # Atualiza com os ficheiros recém-processados
    existing_data.update(final_data)
    
    # Remove entradas de ficheiros que já não existem no Drive
    drive_files_stems = {p.stem for p in config.LOCAL_ASSETS_DIR.rglob("*.*")}
    final_data_keys = list(existing_data.keys())
    for key in final_data_keys:
        if existing_data[key].get('is_external'): continue # Não apaga links externos
        if key.rsplit('.', 1)[0] not in drive_files_stems:
            del existing_data[key]
            logging.info(f"Removida entrada obsoleta '{key}' do data.json.")
    
    with open(config.JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)
    logging.info(f"Ficheiro '{config.JSON_OUTPUT_FILE.name}' atualizado com sucesso.")

    # 5. SINCRONIZA a pasta processada para o R2. Ficheiros novos/alterados são enviados,
    #    e ficheiros apagados no Drive (e consequentemente na pasta local) são REMOVIDOS do R2.
    sync_to_r2_cmd = ["rclone", "sync", str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH, "--progress", "-v"]
    run_command(sync_to_r2_cmd, "Sincronizar ativos processados para R2")

    logging.info("--- WORKFLOW INCREMENTAL CONCLUÍDO ---")

if __name__ == "__main__":
    main()