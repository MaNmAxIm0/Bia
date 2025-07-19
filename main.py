# main.py (Versão Final com Correção Definitiva de FFmpeg e Sincronização)

import os
import subprocess
import json
import logging
import shutil
from pathlib import Path
from tqdm import tqdm
from PIL import Image, ImageOps, ImageDraw, ImageFont
from datetime import datetime
import pytz
import config

# --- 1. CONFIGURAÇÃO DE LOGGING COM FUSO HORÁRIO DE LISBOA ---
def setup_logging():
    """Configura o logging para usar o fuso horário 'Europe/Lisbon'."""
    log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    root_logger = logging.getLogger()
    if root_logger.hasHandlers(): root_logger.handlers.clear()
    lisbon_tz = pytz.timezone('Europe/Lisbon')
    logging.Formatter.converter = lambda *args: datetime.now(lisbon_tz).timetuple()
    handler = logging.StreamHandler()
    handler.setFormatter(log_formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

# --- 2. FUNÇÕES DE APOIO ---
def run_command(command: list, operation_name: str) -> bool:
    """Executa um comando de terminal de forma segura."""
    logging.info(f"Iniciando: {operation_name}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', timeout=900)
        logging.info(f"Sucesso: {operation_name} concluída.")
        return True
    except Exception as e:
        stderr = getattr(e, 'stderr', str(e))
        logging.error(f"FALHA em '{operation_name}': {stderr.strip()}")
        return False

def get_media_orientation(file_path: Path) -> str:
    """Obtém a orientação de imagens e vídeos."""
    ext = file_path.suffix.lower()
    try:
        if ext in config.IMAGE_EXTENSIONS:
            with Image.open(file_path) as img:
                return "vertical" if img.height > img.width else "horizontal"
        elif ext in config.VIDEO_EXTENSIONS:
            cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=s=x:p=0", str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            width, height = map(int, result.stdout.strip().split('x'))
            return "vertical" if height > width else "horizontal"
    except Exception:
        return "horizontal"
    return "horizontal"

# --- 3. FUNÇÕES DE PROCESSAMENTO ---
def process_image(input_path: Path, output_path: Path, apply_watermark_flag: bool):
    """Processa uma imagem: otimiza, comprime e aplica marca de água se necessário."""
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        if max(img.size) > 2048:
            img.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
        
        if apply_watermark_flag:
            image_rgba = img.convert("RGBA")
            draw = ImageDraw.Draw(image_rgba)
            font_size = int(max(image_rgba.size) * config.IMG_WATERMARK_FONT_RATIO)
            try:
                font = ImageFont.truetype(str(config.WATERMARK_FONT_PATH), font_size)
            except IOError:
                font = ImageFont.load_default()
            
            bbox = draw.textbbox((0, 0), config.WATERMARK_TEXT, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            margin = int(max(image_rgba.size) * config.MARGIN_RATIO)
            x, y = image_rgba.width - text_width - margin, image_rgba.height - text_height - margin
            shadow_offset = int(font_size * 0.05)
            
            draw.text((x + shadow_offset, y + shadow_offset), config.WATERMARK_TEXT, font=font, fill=(0, 0, 0, 100))
            draw.text((x, y), config.WATERMARK_TEXT, font=font, fill=(*config.WATERMARK_COLOR_RGB, config.WATERMARK_OPACITY))
            img = image_rgba.convert("RGB")
        
        img.save(output_path, "JPEG", quality=65, optimize=True, progressive=True)

def process_video(input_path: Path, output_path: Path, apply_watermark_flag: bool):
    """Processa um vídeo com uma sintaxe de filtro FFmpeg robusta e corrigida."""
    
    # A cadeia de filtros é construída de forma mais limpa, sem aspas internas desnecessárias.
    filter_complex = "scale=min(1920\\,iw):-2" # Escapar a vírgula para o scale
    
    if apply_watermark_flag:
        # Escapar caracteres especiais para o FFmpeg
        # O FFmpeg requer que os dois pontos ':' e as barras invertidas '\' no caminho do Windows sejam escapados.
        font_path = str(config.WATERMARK_FONT_PATH).replace('\\', '\\\\').replace(':', '\\:')
        watermark_text = config.WATERMARK_TEXT.replace("'", "’") # Substituir aspas para evitar conflitos

        # Construção do filtro de marca de água (sombra primeiro, depois o texto principal)
        # A sintaxe foi simplificada para maior compatibilidade.
        watermark_filter = (
            f",drawtext=fontfile='{font_path}':text='{watermark_text}':"
            f"fontsize=min(w\\,h)*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=black@0.5:"
            f"x=(w-text_w-(min(w\\,h)*{config.MARGIN_RATIO}))+2:y=(h-text_h-(min(w\\,h)*{config.MARGIN_RATIO}))+2,"
            f"drawtext=fontfile='{font_path}':text='{watermark_text}':"
            f"fontsize=min(w\\,h)*{config.VID_WATERMARK_FONT_RATIO}:fontcolor=white@0.8:"
            f"x=w-text_w-(min(w\\,h)*{config.MARGIN_RATIO}):y=h-text_h-(min(w\\,h)*{config.MARGIN_RATIO})"
        )
        filter_complex += watermark_filter

    video_cmd = [
        "ffmpeg", "-i", str(input_path),
        "-vf", filter_complex,
        "-c:v", "libx264", "-preset", "medium", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k",
        "-y", # Sobrescrever o ficheiro de saída se já existir
        str(output_path)
    ]
    
    if not run_command(video_cmd, f"Processar vídeo {input_path.name}"):
        return False

    # A lógica para gerar a thumbnail permanece a mesma
    try:
        duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(input_path)]
        result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
        duration = float(result.stdout.strip())
        # Garante que o timestamp para a thumbnail está dentro da duração do vídeo
        ts = min(max(1.0, duration * 0.15), duration - 1)
        thumb_path = config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR / f"{output_path.stem}_thumb.jpg"
        thumb_cmd = ["ffmpeg", "-i", str(input_path), "-ss", str(ts), "-vframes", "1", "-q:v", "2", "-y", str(thumb_path)]
        run_command(thumb_cmd, f"Gerar thumbnail para {output_path.name}")
    except Exception as e:
        logging.error(f"FALHA ao gerar thumbnail para {input_path.name}: {e}")
        return False
        
    return True
# --- 4. FLUXO PRINCIPAL ---
def main():
    setup_logging()
    logging.info("--- INÍCIO DO WORKFLOW DE SINCRONIZAÇÃO ---")

    for path in [config.LOCAL_ASSETS_DIR, config.PROCESSED_ASSETS_DIR, config.PROCESSED_ASSETS_DIR / config.THUMBNAIL_DIR]:
        path.mkdir(exist_ok=True)

    if not run_command(["rclone", "sync", config.DRIVE_REMOTE_PATH, str(config.LOCAL_ASSETS_DIR), "--progress", "-v"], "Sincronizar Google Drive"):
        return
    
    # Adiciona --use-server-modtime para preservar as datas originais e evitar reprocessamento desnecessário
    if not run_command(["rclone", "sync", config.R2_REMOTE_PATH, str(config.PROCESSED_ASSETS_DIR), "--progress", "-v", "--use-server-modtime"], "Sincronizar R2 para local"):
        return

    drive_stems = {p.stem for p in config.LOCAL_ASSETS_DIR.rglob("*.*")}
    for proc_file in list(config.PROCESSED_ASSETS_DIR.rglob("*.*")):
        if config.THUMBNAIL_DIR.name in proc_file.parts:
            if proc_file.stem.replace("_thumb", "") not in drive_stems:
                proc_file.unlink(); logging.info(f"Apagado thumbnail órfão: {proc_file.name}")
        elif proc_file.stem not in drive_stems:
            proc_file.unlink(); logging.info(f"Apagado ficheiro órfão: {proc_file.name}")

    manifest_entries = []
    failed_files = []
    for input_path in tqdm(list(config.LOCAL_ASSETS_DIR.rglob("*.*")), desc="Processando Ficheiros"):
        relative_path = input_path.relative_to(config.LOCAL_ASSETS_DIR)
        output_path = config.PROCESSED_ASSETS_DIR / relative_path
        ext = input_path.suffix.lower()

        if output_path.exists() and input_path.stat().st_mtime <= output_path.stat().st_mtime:
            continue
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        parent_folder = relative_path.parts[0] if len(relative_path.parts) > 1 else ""
        should_apply_watermark = parent_folder not in ["Melhores", "Capas", "Apresentações", config.THUMBNAIL_DIR.name]
        
        processed_successfully = True
        if ext in config.PDF_EXTENSIONS or ext in ['.gdoc', '.gsheet', '.gslides']:
            if ext not in ['.gdoc', '.gsheet', '.gslides']: shutil.copy2(input_path, output_path)
        elif ext in config.IMAGE_EXTENSIONS:
            process_image(input_path, output_path, apply_watermark_flag=should_apply_watermark)
        elif ext in config.VIDEO_EXTENSIONS:
            if not process_video(input_path, output_path, apply_watermark_flag=should_apply_watermark):
                processed_successfully = False
                failed_files.append(str(relative_path))
        else:
            continue
        
        if processed_successfully:
            manifest_entries.append(f"{relative_path.as_posix()} - {datetime.now().isoformat()}")

    final_data = {}
    for source_path in list(config.LOCAL_ASSETS_DIR.rglob("*.*")):
        relative_path = source_path.relative_to(config.LOCAL_ASSETS_DIR)
        ext = source_path.suffix.lower()
        if ext in ['.gdoc', '.gsheet', '.gslides']:
            try:
                with open(source_path, 'r', encoding='utf-8') as f: url = json.load(f)['url']
                if "presentation" in url: url = url.replace("/edit", "/embed?start=false&loop=false&delayms=3000")
                final_data[source_path.stem] = {"titles": {"pt": source_path.stem, "en": source_path.stem, "es": source_path.stem}, "orientation": "horizontal", "url": url, "is_external": True}
            except Exception: continue
        else:
            output_path = config.PROCESSED_ASSETS_DIR / relative_path
            if output_path.exists():
                stem = output_path.stem
                titles = stem.split('_'); title_pt, title_en, title_es = (titles[0] if titles else stem, titles[1] if len(titles) > 1 else titles[0], titles[2] if len(titles) > 2 else titles[0])
                entry = {"titles": {"pt": title_pt, "en": title_en, "es": title_es}, "orientation": get_media_orientation(output_path), "url": f"{config.R2_PUBLIC_URL}/{relative_path.as_posix()}"}
                if ext in config.VIDEO_EXTENSIONS:
                    entry["thumbnail_url"] = f"{config.R2_PUBLIC_URL}/{config.THUMBNAIL_DIR.name}/{stem}_thumb.jpg"
                final_data[output_path.name] = entry

    with open(config.JSON_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    with open(config.R2_FILE_MANIFEST, 'w', encoding='utf-8') as f:
        f.write(f"Última sincronização: {datetime.now(pytz.timezone('Europe/Lisbon')).strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
        if manifest_entries:
            f.write("Ficheiros processados nesta execução:\n")
            f.write("\n".join(manifest_entries))
        else:
            f.write("Nenhum ficheiro novo ou alterado foi processado.\n")
            
    with open(config.FAILED_FILES_LOG, 'w', encoding='utf-8') as f:
        if failed_files:
            f.write("Ficheiros que falharam o processamento:\n")
            f.write("\n".join(failed_files))
        else:
            f.write("Nenhum ficheiro falhou o processamento.\n")

    run_command(["rclone", "sync", str(config.PROCESSED_ASSETS_DIR), config.R2_REMOTE_PATH, "--progress", "-v"], "Sincronizar para R2")
    logging.info("--- WORKFLOW CONCLUÍDO ---")

if __name__ == "__main__":
    main()