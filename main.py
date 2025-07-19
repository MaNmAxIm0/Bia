import os
import subprocess
import json
import logging
import shutil
from datetime import datetime
from tqdm import tqdm
from PIL import Image, ImageOps, ImageDraw, ImageFont
import pytz
from pathlib import Path

# --- CONFIGURAÇÃO ---
DRIVE_REMOTE_PATH = os.getenv("DRIVE_REMOTE_FULL_PATH", "Drive:Portfólio Bia")
R2_BUCKET_PATH = os.getenv("R2_REMOTE_FULL_PATH", "R2:bia-portfolio-assets")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://pub-ff3d4811ffc342b7800d644cf981e731.r2.dev" )

LOCAL_ASSETS_DIR = Path("local_assets")
PROCESSED_ASSETS_DIR = Path("processed_assets")
THUMBNAILS_DIR = PROCESSED_ASSETS_DIR / "Thumbnails"
CACHE_FILE = Path("processed_cache.json") # Cache baseada em ficheiro
WATERMARK_TEXT = "© Beatriz Rodrigues"
FONT_PATH = Path("fonts/Montserrat-Medium.ttf")

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi']

# --- CONFIGURAÇÃO DE LOGGING ---
def setup_logging():
    log_formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    def custom_time(*args):
        return datetime.now(pytz.timezone('Europe/Lisbon')).timetuple()
    logging.Formatter.converter = custom_time
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    if not root_logger.handlers:
        root_logger.addHandler(console_handler)
setup_logging()

# --- FUNÇÕES DE CACHE E MANIFESTO ---
def load_cache():
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.warning("Ficheiro de cache corrompido. A criar um novo.")
    return {}

def save_cache(cache_data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=4)

def generate_r2_manifest():
    # Esta função será chamada pelo format_manifest.py, mas a deixamos aqui para referência
    pass

# --- FUNÇÕES DE PROCESSAMENTO ---
def run_rclone_command(command: list, operation_name: str) -> bool:
    logging.info(f"Iniciando operação rclone: {operation_name}")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"Operação rclone '{operation_name}' concluída com sucesso.")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Falha na operação rclone '{operation_name}': {e.stderr.strip()}")
        return False

def get_media_dimensions(file_path: Path) -> tuple:
    try:
        if file_path.suffix.lower() in IMAGE_EXTENSIONS:
            with Image.open(file_path) as img: return img.size
        elif file_path.suffix.lower() in VIDEO_EXTENSIONS:
            cmd = ['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', str(file_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            video_data = json.loads(result.stdout)['streams'][0]
            return video_data['width'], video_data['height']
    except Exception as e:
        logging.warning(f"Não foi possível obter as dimensões para {file_path.name}: {e}")
    return None, None

def correct_image_orientation(img: Image.Image) -> Image.Image:
    try:
        return ImageOps.exif_transpose(img)
    except Exception:
        return img

def apply_watermark_to_image(base_image: Image.Image) -> Image.Image:
    image_with_watermark = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(image_with_watermark)
    font_size = int(image_with_watermark.width * 0.035)
    try:
        font = ImageFont.truetype(str(FONT_PATH), font_size)
    except IOError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    margin = int(image_with_watermark.width * 0.02)
    x = image_with_watermark.width - text_width - margin
    y = image_with_watermark.height - text_height - margin
    shadow_offset = int(font_size * 0.05)
    draw.text((x + shadow_offset, y + shadow_offset), WATERMARK_TEXT, font=font, fill=(0, 0, 0, 100))
    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(255, 255, 255, 180))
    return image_with_watermark.convert("RGB")

def process_video(input_path: Path, output_path: Path) -> bool:
    font_path_ffmpeg = str(FONT_PATH).replace("\\", "/").replace(":", "\\\\:")
    watermark_cmd = [
        "ffmpeg", "-i", str(input_path),
        "-vf", f"drawtext=fontfile='{font_path_ffmpeg}':text='{WATERMARK_TEXT}':fontsize=h*0.03:fontcolor=black@0.5:x=(w-text_w-w*0.02)+2:y=(h-text_h-h*0.02)+2,drawtext=fontfile='{font_path_ffmpeg}':text='{WATERMARK_TEXT}':fontsize=h*0.03:fontcolor=white@0.8:x=w-text_w-w*0.02:y=h-text_h-h*0.02",
        "-codec:v", "libx264", "-preset", "medium", "-crf", "23", "-codec:a", "copy", "-y", str(output_path)
    ]
    try:
        subprocess.run(watermark_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao aplicar marca de água ao vídeo '{input_path.name}': {e.stderr.strip()}")
        return False
    thumbnail_path = THUMBNAILS_DIR / f"{input_path.stem}_thumb.jpg"
    thumbnail_cmd = ["ffmpeg", "-i", str(output_path), "-ss", "00:00:01.000", "-vframes", "1", "-q:v", "2", "-y", str(thumbnail_path)]
    try:
        subprocess.run(thumbnail_cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"FFmpeg falhou ao gerar thumbnail para '{input_path.name}': {e.stderr.strip()}")
        return True

def generate_data_json(output_file: str):
    logging.info("Gerando ficheiro de metadados data.json com a nova estrutura...")
    if not R2_PUBLIC_URL or "xxxx" in R2_PUBLIC_URL:
        logging.warning("A variável de ambiente R2_PUBLIC_URL não foi definida!")
    final_data_structure = {}
    all_processed_files = [p for p in PROCESSED_ASSETS_DIR.rglob("*") if p.is_file()]
    for file_path_local in all_processed_files:
        if file_path_local.parent.name == "Thumbnails": continue
        filename, stem = file_path_local.name, file_path_local.stem
        parts = stem.split('_')
        title_pt, title_es, title_en = (parts[0] if len(parts) > 0 else stem, parts[1] if len(parts) > 1 else parts[0], parts[2] if len(parts) > 2 else parts[0])
        width, height = get_media_dimensions(file_path_local)
        orientation = "vertical" if width is not None and height is not None and height > width else "horizontal"
        relative_path = file_path_local.relative_to(PROCESSED_ASSETS_DIR)
        url_path = relative_path.as_posix()
        full_url = f"{R2_PUBLIC_URL.rstrip('/')}/{url_path}"
        asset_info = {"pt": title_pt, "es": title_es, "en": title_en, "orientation": orientation, "url": full_url}
        if file_path_local.suffix.lower() in VIDEO_EXTENSIONS:
            asset_info["thumbnail_url"] = f"{R2_PUBLIC_URL.rstrip('/')}/Thumbnails/{stem}_thumb.jpg"
        final_data_structure[filename] = asset_info
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data_structure, f, indent=4, ensure_ascii=False)
    logging.info(f"'{output_file}' gerado com sucesso com a estrutura final.")

# --- FLUXO DE TRABALHO PRINCIPAL ---
def main():
    logging.info("--- INÍCIO DO PIPELINE DE PROCESSAMENTO ---")
    if not DRIVE_REMOTE_PATH or not R2_BUCKET_PATH:
        logging.error("As variáveis de ambiente dos remotes não estão definidas.")
        exit(1)

    LOCAL_ASSETS_DIR.mkdir(exist_ok=True)
    PROCESSED_ASSETS_DIR.mkdir(exist_ok=True)
    THUMBNAILS_DIR.mkdir(exist_ok=True)

    download_cmd = ["rclone", "copy", DRIVE_REMOTE_PATH, str(LOCAL_ASSETS_DIR), "--progress"]
    if not run_rclone_command(download_cmd, "Download de ativos do Drive"):
        logging.error("Pipeline interrompido devido a falha no download.")
        return

    cache_data = load_cache()
    updated_cache = cache_data.copy()
    files_to_process = []
    
    all_local_files = [p for p in LOCAL_ASSETS_DIR.rglob("*") if p.is_file() and not p.name.startswith('.')]
    logging.info(f"Encontrados {len(all_local_files)} ficheiros na origem. Verificando contra a cache de ficheiro...")

    for file_path in all_local_files:
        relative_path_str = str(file_path.relative_to(LOCAL_ASSETS_DIR))
        mod_time = str(file_path.stat().st_mtime)
        
        if cache_data.get(relative_path_str) != mod_time:
            files_to_process.append(file_path)

    processed_count = len(all_local_files) - len(files_to_process)
    if processed_count > 0:
        logging.info(f"{processed_count} ficheiros encontrados na cache e serão ignorados.")
    logging.info(f"{len(files_to_process)} ficheiros novos ou modificados para processar.")

    failure_count = 0
    with tqdm(total=len(files_to_process), desc="Processando novos ativos") as pbar:
        for input_path in files_to_process:
            relative_path = input_path.relative_to(LOCAL_ASSETS_DIR)
            output_path = PROCESSED_ASSETS_DIR / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            processed_successfully = False
            try:
                if input_path.suffix.lower() in IMAGE_EXTENSIONS:
                    with Image.open(input_path) as img:
                        img = correct_image_orientation(img)
                        img = apply_watermark_to_image(img)
                        img.save(output_path, "JPEG", quality=90, optimize=True, progressive=True)
                    processed_successfully = True
                elif input_path.suffix.lower() in VIDEO_EXTENSIONS:
                    if process_video(input_path, output_path):
                        processed_successfully = True
                else:
                    shutil.copy2(input_path, output_path)
                    processed_successfully = True
                
                if processed_successfully:
                    updated_cache[str(relative_path)] = str(input_path.stat().st_mtime)
            except Exception as e:
                logging.error(f"Erro inesperado ao processar {input_path.name}: {e}")
                failure_count += 1
            pbar.update(1)

    save_cache(updated_cache)
    generate_data_json("data.json")
    # A geração do manifesto r2 é agora feita no workflow para usar o script format_manifest.py

    if failure_count > 0:
        logging.warning(f"{failure_count} ficheiros falharam ao processar.")
    logging.info("--- FIM DO PIPELINE ---")

if __name__ == "__main__":
    main()
